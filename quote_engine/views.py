import csv
import io
import logging
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from quote_engine.riskservice import RiskService
from quote_engine.utils import log_api_call
from .models import Quote
from .serializers import QuoteSerializer

logger = logging.getLogger('django')



@log_api_call(max_retries=3, backoff_factor=2)
@api_view(['POST'])
def submit_quote(request):
    """
    Creates and saves a single Quote record based on POST data.

    If valid, returns a 201 response with the new quote's ID and reference.
    Otherwise, responds with validation errors.
    """
    logger.info('Received submit quote request')
    
    quote_data = request.data
    logger.debug(f'Submitted quote data: {quote_data}')
   
    
    serializer = QuoteSerializer(data=quote_data)
    if serializer.is_valid():
        quote = serializer.save()
        logger.info(f'Quote {quote.quote_reference} saved successfully')

        return Response(
            {'status': 'Submitted',
             'quote_reference': quote.quote_reference,
             'quote_id': quote.id},
             status=status.HTTP_201_CREATED
            )
    else:
        logger.warning(f'quote data invalid: {serializer.errors}')
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def submit_quotes_csv(request):
    """
    Retrieves a multiple quote submissions through a CSV file and saves them.

    Responds with a summary of the number of errors encountered during processing.
    
    """
    file = request.FILES.get('file')
    
    if not file:
        logger.error('file not provided')
        return Response(
            {'Error': 'file not provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not file.name.endswith('.csv'):
        logger.error('file type must be csv')
        return Response(
            {'Error': 'file type must be csv'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        decoded_file = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded_file))
    except Exception as e:
        return Response(
            {'error': f'Error reading file: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result_status = {'error_count': 0}  
    for rownum, row in enumerate(csv_reader, start=1):
        logger.debug(f'Processing row {rownum}: {row}')
        serializer = QuoteSerializer(data=row)

        if serializer.is_valid():
            try:
                quote = serializer.save()
                logger.info(f'Quote {quote.quote_reference} saved successfully')
            except Exception as e:
                logger.error(f'Error saving quote: {str(e)}')
                result_status['error_count'] += 1
        else:
            logger.warning(f'quote data invalid for row num {rownum}: {serializer.errors}')
            result_status['error_count'] += 1

    logger.info(f'Processed {rownum} rows, errors: {result_status["error_count"]}')
    return Response(result_status, status=status.HTTP_201_CREATED)



@log_api_call(max_retries=3, backoff_factor=2)
@api_view(['GET'])
def getQuote(request):
    """
    Retrieves a specific Quote by its reference and calculates associated risks.

    Responds with the quote data, including additional fields such as
    location_risk, risk_type, and quote_validity in the context.
    """
    logger.info('Received get quote request')
    requested_quote = request.query_params.get('quote_reference')

    if not requested_quote:
        logger.warning('Quote reference not provided')
        return Response(
            {
                'Error': 'Quote must be provided'},
                 status = status.HTTP_400_BAD_REQUEST
        )          
  
    try:        
        quote = Quote.objects.get(quote_reference=requested_quote)
        logger.info(f'quote reference {requested_quote} successfully retrieved')
    

        logger.info(f'Calculating risks for quote {quote.quote_reference}')
        location_risk = RiskService.calculate_location_risks(
            quote.risk_postcode,
            quote.product_type,
            quote.timestamp
            )
       
        risk_type = RiskService.risk_type(location_risk['flood_risk'],location_risk['crime_risk'])    

        
        quote_validity = RiskService.quote_validity(risk_type)

        logger.info('Quote validity and risks calculated successfully')
        
        
                    
    except Quote.DoesNotExist:
        logger.error(f'Quote {requested_quote} not found')
        return Response({
        'Error':'Quote not found'},
        status = status.HTTP_404_NOT_FOUND
    )

    except Exception as e:
        logger.error(f'Unexpected error occured: {str(e)}')
        return Response({
        'Error':f'Unexpected error occured'},
        status = status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    context={
        'location_risk': location_risk, 
        'risk_type': risk_type, 
        'quote_validity': quote_validity,
        
        }

    serializer = QuoteSerializer(quote, many=False, context=context)

    logger.info('Successfully fetched quote')
    return Response(serializer.data, status=status.HTTP_200_OK)



