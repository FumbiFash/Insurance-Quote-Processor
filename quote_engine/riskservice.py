import logging

from .risk_utils import (
    calculate_crime_risk,
    calculate_flood_risk,
    get_crimes_for_location,
    get_flood_data_for_location,
    get_long_lat
)

logger = logging.getLogger('django')

class RiskService:

    """
    Service class responsible for computing various risk-related calculations
    based on location details and returning
    calculated results, such as risk levels and quote validity durations.
    """
    @staticmethod

    def calculate_location_risks(
        postcode: str, 
        product_type: str, 
        timestamp: str
    ):
        if not postcode or not product_type or not timestamp:
            raise ValueError('Invalid input data provided')


        try:
            latitude, longitude = get_long_lat(postcode)
            flood_data = get_flood_data_for_location(lat=latitude, long=longitude)
            flood_risk = calculate_flood_risk(flood_data, product_type)
            crime_data = get_crimes_for_location(timestamp, lat=latitude, long=longitude)
            crime_risk = calculate_crime_risk(crime_data, 'HOME')

            return {
                'flood_risk': flood_risk,
                'crime_risk': crime_risk
            }
        except Exception as e:
            logger.error('Error calculating location risks')
            raise ValueError(f'Error calculating location risks for postcode: {e}')
    
    def risk_type(flood_risk,crime_risk):
        try:
            total_risk = flood_risk + crime_risk
            if total_risk > 100:
                risk_value = 'HIGH_VALUE_RISK'
            elif total_risk < 100:
                risk_value = 'STANDARD_VALUE_RISK'
            print(risk_value)
            return risk_value
        except Exception as e:
            logger.error('Error calculating risk type')
            raise ValueError(f'Error calculating risk type: {e}')

    def quote_validity(risk_value : str):
        """
        Return the validity period (in days) for a quote based on its 
        assessed risk category.

        - 'HIGH_VALUE_RISK' -> 7 days
        - 'STANDARD_VALUE_RISK' -> 14 days
        - Any other category -> None

        :param risk_value: The risk category label (e.g., 'HIGH_VALUE_RISK').
        :type risk_value: str
        :return: The number of days the quote is valid, or None if unspecified.
        :rtype: int or None
        :raises ValueError: If an unexpected error occurs when determining validity.
        """
        try: 
            if risk_value == 'HIGH_VALUE_RISK':
                quote_validity = 7
            elif risk_value == 'STANDARD_VALUE_RISK':
                quote_validity = 14
            else:
                return None
            return quote_validity
        except Exception as e:
            logger.error(f'Error calculating quote validity')
            raise ValueError(f'Error calculating quote validity: {e}')
