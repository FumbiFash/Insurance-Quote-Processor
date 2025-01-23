import logging
from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from .models import Quote
import re

logger = logging.getLogger('django')

class QuoteSerializer(serializers.ModelSerializer):

    """
    Serializer for the Quote model, handling field validation and
    computed fields such as `location_risk`, `risk_type`, `quote_validity`,
    and `roi`.
    
    This serializer also enforces specific business rules for different
    product types (HOME, COMMERCIAL, BEAUTY) and flags suspicious quotes
    based on the frequency of quotes from the same postcode.
    
    Attributes:
        location_risk (SerializerMethodField): Computed field for location-based risk score.
        risk_type (SerializerMethodField): Computed field which indicates risk type category.
        quote_validity (SerializerMethodField): Computed field for how long a quote is valid.
        roi (SerializerMethodField): Computed field for return on investment (ROI).
    """


    location_risk = serializers.SerializerMethodField(read_only=True)
    risk_type = serializers.SerializerMethodField(read_only=True)
    quote_validity = serializers.SerializerMethodField(read_only=True)
    roi = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """
        Meta class defining the model and fields used by this serializer.

        model (Quote): Reference to the Quote model.
        fields (str): Specifies that all model fields will be serialized.
        """
        model = Quote
        fields = '__all__'

    
    def validate_risk_postcode(self, value: str) -> str:

        """
        Validate that the risk_postcode follows a UK postcode format.

        :param value: The postcode string entered by the user.
        :type value: str
        :return: The original `value` if valid.
        :rtype: str
        :raises serializers.ValidationError: If the postcode format is invalid.
        """

        pattern = r"^[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}$"
        if not re.match(pattern, value):
            logger.warning(f"Invalid postcode format {value}")
            raise serializers.ValidationError("Invalid postcode format")
        return value

    def validate_quote_reference(self, value: str) -> str:
        """
        Validate that the quote reference follows the INS-YYYY-XXXXX format.

        :param value: The quote reference string entered by the user.
        :type value: str
        :return: The original `value` if valid.
        :rtype: str
        :raises serializers.ValidationError: If the quote reference format is invalid.
        """


        pattern = r"^INS-\d{4}-\d{5}$"
        if not re.match(pattern, value):
            logger.warning(f"Invalid quote reference format {value}")
            raise serializers.ValidationError("Invalid quote reference format")
        return value
    
    def validate(self, data: dict) -> dict:

        """
        Performs overall validation of the Quote data. Logic rules include:
          - No empty fields.
          - Positive numeric values for building_value, contents_value, quote_premium, and broker_commission.
          - Product-specific rules:
            - HOME: building_value <= £2,000,000, contents_value <= £150,000, age between 18 and 75.
            - COMMERCIAL: building_value between £100,000 and £5,000,000.
            - BEAUTY: Only ANNUAL payments, minimum premium of £150.
          - Suspicious quote detection based on frequency of quotes from the same postcode.

        :param data: A dictionary of validated fields before saving to the database.
        :type data: dict
        :return: The validated data.
        :rtype: dict
        :raises serializers.ValidationError: If any field is invalid or if business rules are violated.
        """

        for field in data:
            if data[field] == '':
                logger.warning(f"field {field} is empty")
                raise serializers.ValidationError(f"{field} cannot be empty")

        product_type = data.get('product_type')
        building_value = data.get('building_value')
        contents_value = data.get('contents_value')
        customer_age = data.get('customer_age')
        payment_type = data.get('payment_type')
        quote_premium = data.get('quote_premium')
        broker_commission = data.get('broker_commission')
        risk_postcode = data.get('risk_postcode')

        if building_value <= 0:
            raise serializers.ValidationError("Building value must be positive")
        if contents_value <= 0:
            raise serializers.ValidationError("Contents value must be positive")
        if quote_premium <= 0:
            raise serializers.ValidationError("Quote premium must be positive")
        if broker_commission <= 0:
            raise serializers.ValidationError("Broker commission must be positive")
        

        if product_type == 'HOME':
            if building_value > 2_000_000:
                logger.warning(f"Building value exceeds limit for HOME product type")
                raise serializers.ValidationError("Building value cannot be more than £2,000,000 for HOME product type")
            if contents_value > 150_000:
                logger.warning(f"Contents value exceeds limit for HOME product type")
                raise serializers.ValidationError("Contents value cannot be more than £150,000 for HOME product type")
            if customer_age < 18 or customer_age > 75:
                logger.warning(f"Customer age {data.get('customer_age')} out of range for HOME product type")
                raise serializers.ValidationError("Customer age must be between 18 and 75 for HOME product type")


        elif product_type == 'COMMERCIAL':
            if building_value < 100_000:
                logger.warning(f"Building value too low for COMMERCIAL product type")
                raise serializers.ValidationError('Building value for Commercial product type must be minimum of £100,000')
            if building_value > 5_000_000:
                logger.warning(f"Building value too high for COMMERCIAL product type")
                raise serializers.ValidationError('Building value for Commercial product type must be maximum of £5,000,000')

    
        elif product_type == 'BEAUTY':
            if payment_type != 'ANNUAL':
                logger.warning("Wrong payment type for BEAUTY product type")
                raise serializers.ValidationError('Beauty product type is only available with annual payment type')
            if quote_premium < 150:
                logger.warning("Quote premium too low for BEAUTY product type")
                raise serializers.ValidationError('Premium for beauty product type must be minimum of £150')


        suspicion_threshold = 3
        one_hour_ago = timezone.now() - timedelta(hours=1)
        quote_count = Quote.objects.filter(risk_postcode = risk_postcode, timestamp__gte = one_hour_ago ).count()

        if quote_count >= suspicion_threshold:
            logger.warning("Multiple quotes from same postcode within the hour")
            data['suspicious'] = True

        return data
    
    def get_location_risk(self, obj: Quote) -> float:
        """
        Retrieve the location risk score from the serializer context.

        :param obj: The Quote instance being serialized.
        :type obj: Quote
        :return: Location risk score if available, otherwise None.
        :rtype: float or None
        """

        return self.context.get('location_risk')
    
    def get_risk_type(self, obj: Quote) -> str:
        """
        Retrieve the risk type from the serializer context.

        :param obj: The Quote instance being serialized.
        :type obj: Quote
        :return: Risk type string if available, otherwise returns None.
        :rtype: str or None
        """
        return self.context.get('risk_type')
    
    def get_quote_validity(self, obj: Quote) -> str:
        """
        Retrieve the quote validity duration from the serializer context.

        :param obj: The Quote instance being serialized.
        :type obj: Quote
        :return: A string representing how long the quote is valid (e.g., '14 days').
        :rtype: str or None
        """
        return self.context.get('quote_validity')
    
    def get_roi(self, obj: Quote) -> float:
        """
        Calculate and return the ROI (Return on Investment) for the specific Quote.

        :param obj: The Quote instance being serialized.
        :type obj: Quote
        :return: ROI value rounded to two decimal places.
        :rtype: float
        """

        from quote_engine.risk_utils import calculate_roi
        quote_premium = obj.quote_premium
        broker_commision = obj.broker_commission

        return calculate_roi(quote_premium, broker_commision)