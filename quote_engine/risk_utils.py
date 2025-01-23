import requests
import logging
from django.core.cache import cache
from django.conf import settings
import logging
from datetime import datetime

"""
The risk_utils.py module contains functions to retrieve and calculate risk data for insurance quotes. 
The functions interact with external APIs to fetch crime and flood data based on a given location (latitude and longitude). 
The data is then used to calculate the risk associated with a given property type (e.g., home, commercial, beauty).

"""



logger = logging.getLogger('django')

CACHE_TIMEOUT = 60 * 60 * 24

def get_long_lat(risk_postcode:str) -> tuple:
    """
    Retrieve latitude and longitude for a given UK postcode.

    The function checks the Django cache for existing coordinates; if not found,
    it queries the Postcodes.io API. If successful, it caches the results.

    :param risk_postcode: The postcode to look up.
    :type risk_postcode: str
    :return: A tuple of (latitude, longitude).
    :raises ValueError: If the API response indicates the postcode could not be found.
    :raises ConnectionError: If there is a network issue or request timeout.
    :raises Exception: For any other unexpected errors.
    """
    try:
        normalized_postcode = risk_postcode.replace(" ", "").upper()
        cache_key = f'postcode_cordinates_{normalized_postcode}'

        cached_coords = cache.get(cache_key)

        if cached_coords:
            logger.debug(f"Cache hit for postcode {normalized_postcode}")
            return cached_coords
        
        logger.debug(f"Cache miss for postcode {normalized_postcode}")
        url = f"https://api.postcodes.io/postcodes/{risk_postcode}"
        
        response = requests.get(url,timeout=5)


        if response.status_code==200:
            data = response.json()
            if data and 'longitude' in data['result'] and 'latitude' in data['result']:
                latitude = data['result']['latitude'] 
                longitude = data['result']['longitude']
                cache.set(cache_key, latitude,longitude, CACHE_TIMEOUT)
                return latitude, longitude

        else:
            raise ValueError(f"Could not get location for postcode {risk_postcode}, response code {response.status_code}")
    except requests.RequestException as e:
        raise ConnectionError(f'Error retrieving location for postcode {risk_postcode}: {e}')
    
    except Exception as e:
        raise 

def get_crimes_for_location(timestamp: str,lat: float,long: float) -> list:

    """
    Fetch crime data from the UK Police API for a given date and location.

    The function uses the timestamp (converted to 'YYYY-MM' format) to
    query the crime data. Results are cached to reduce repeat calls.

    :param timestamp: A date/time string in 'YYYY-MM-DD HH:MM:SS' or similar format.
    :type timestamp: str
    :param lat: The latitude of the location.
    :type lat: float
    :param long: The longitude of the location.
    :type long: float
    :return: A list of crime records in JSON-like dictionary form.
    :rtype: list
    :raises ConnectionError: If a network or request error occurs.
    :raises ValueError: If the date format is invalid or if the API response is not successful.
    :raises Exception: For any other unexpected errors.
    """

    try:
        timestamp = str(timestamp)
        date_part = timestamp.split(' ')[0]
        
        # Parse the date part
        parsed_date = datetime.strptime(date_part, '%Y-%m-%d')
        
        # Format the date to 'YYYY-MM'
        normalized_date = parsed_date.strftime('%Y-%m')
    

        cache_key = f'crimes_{normalized_date}_{long}_{lat}'
        cached_crimes = cache.get(cache_key)

        if cached_crimes:
            return cached_crimes

        url = f"https://data.police.uk/api/crimes-at-location?date={normalized_date}&lat={lat}&lng={long}"
        response = requests.get(url,timeout=5)


        if response.status_code==200:
            data = response.json()
            cache.set(cache_key, data, CACHE_TIMEOUT)
            return data

        else:
            raise ValueError(f"Could not get crimes for date {normalized_date}, location {long},{lat}, response code {response.status_code}")
    
    except requests.RequestException as e:
        raise ConnectionError(f'Error retrieving crime data for location {lat},{long}: {e}')
    
    except ValueError:
        raise ValueError(f"Invalid date format {timestamp}, should be YYYY-MM")
    
    except Exception as e:
        raise ValueError(f"Unexpected error occured when retrieving crimes for location {lat},{long}: {e}")


def get_flood_data_for_location(lat: float,long: float,dist: int = 50) -> dict:

    """
    Fetch flood data from the UK Environment Agency Flood Monitoring API.

    The function retrieves flood alerts or warnings within a specified distance
    in km of the given latitude and longitude. Results are cached for
    performance optimization.
    

    :param lat: The latitude of the location.
    :type lat: float
    :param long: The longitude of the location.
    :type long: float
    :param dist: The distance in km around the coordinates to check for flood data, defaults to 50.
    :type dist: int
    :return: A dictionary containing flood data from the API.
    :rtype: dict
    :raises ConnectionError: If a network issue or request timeout occurs.
    :raises TimeoutError: If the API request times out.
    :raises ValueError: If an unexpected error occurs or if the response is not valid JSON.
    """



    try:

        url = 'https://environment.data.gov.uk/flood-monitoring/id/floods'

        # Prepare query parameters
        params = {'lat': lat, 'long': long, 'dist': dist}

        # Create a unique cache key based on the coordinates and distance
        cache_key = f'flood_risk_{lat}_{long}_{dist}'

        # Check if data is already cached
        cached_coords = cache.get(cache_key)
        if cached_coords:
            logger.debug(f"Cache hit for location: lat={lat}, long={long}, dist={dist}")
            return cached_coords

        # Make the API request with parameters
    
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status() 
        

        data = response.json()

        # Cache the response data
        cache.set(cache_key, data, CACHE_TIMEOUT)
        logger.debug(f"Cached flood data for location")
        return data

    except requests.RequestException as e:
        logger.error(f"Error fetching flood data for lat={lat}, long={long}: {e}")
        raise ConnectionError(f"Error fetching flood data for location {lat},{long}: {e}")
    except requests.exceptions.Timeout as e:
        raise TimeoutError(f'Request timed out while retrieving flood data: {e}')
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f'Connection error occured when retrieving flood data: {e}')
    
    except Exception as e:
        raise ValueError(f'Unexpected error occured when retrieving flood data: {e}')

    



        
def calculate_crime_risk(crime_data: list,product_type: str) -> float:

    """
    Calculate a crime risk score for a given product type based on crime data.

    Uses weighted crime categories and property-specific multipliers to compute
    a normalized risk score (0–100). The higher the score, the higher the risk.

    It is assumed that COMMERCIAL properties are at higher risk from crime than HOME/BEAUTY properties.

    :param crime_data: A list of crime records.
    :type crime_data: list
    :param product_type: The type of product (e.g., 'HOME', 'COMMERCIAL', 'BEAUTY').
    :type product_type: str
    :return: A float representing the normalized crime risk (0 to 100).
    :rtype: float
    :raises ValueError: If any unexpected error occurs during calculation.
    """

    try:
        PROPERTY_TYPE_MULTIPLIERS = {
        'BEAUTY': 1.0,   # Baseline risk
        'HOME': 1.5,   
        'COMMERCIAL': 2,    
    }

        crime_risk = 0
        MAXIMUM_CRIME_RISK = 100

        CRIME_WEIGHTS = {
        "anti-social-behaviour": 1,
        "bicycle-theft" : 1,
        "burglary" : 3, 
        "criminal-damage-arson" : 4, 
        "drugs" : 1.5,
        "other-crime" : 1, 
        "other-theft" : 2,
        "possession-of-weapons" : 4,
        "public-order" : 2,
        "robbery" : 3, 
        "shoplifting" : 2, 
        "theft-from-the-person" : 2, 
        "vehicle-crime" : 2,
        "violent-crime" : 4 
        }

            
        for crime in crime_data:
            category = crime.get('category')
            if category:
                weight = CRIME_WEIGHTS.get(category, 1)
                crime_risk +=  weight
            
        crime_risk *= PROPERTY_TYPE_MULTIPLIERS.get(product_type, 1)
        print(f'crime_risk -- {crime_risk}')
        normalized_crime_risk = min((crime_risk/MAXIMUM_CRIME_RISK), 1) * 100
        return normalized_crime_risk
    
    except Exception as e:
        raise ValueError(f"Error calculating crime risk: {e}")
    



def calculate_flood_risk(flood_data: dict,product_type: str) -> float:
    
    """
    Calculate a flood risk score based on Environment Agency flood data and product type.

    Flood severity level is converted into a score, multiplied by property type
    risk factors, then normalized to a range of 0–100. Tidal flood events add extra risk.

    It is assumed that HOME properties are at higher risk from flood than COMMERCIAL/BEAUTY properties.

    :param flood_data: A dictionary containing flood data with 'items', each item having:
                       'severityLevel': int, 'isTidal': bool, etc.
    :type flood_data: dict
    :param product_type: The product type (e.g., 'HOME', 'COMMERCIAL', 'BEAUTY').
    :type product_type: str
    :return: A float representing the normalized flood risk (0 to 100).
    :rtype: float
    :raises ValueError: If any unexpected error occurs during calculation.
    """

    


    try:
        PROPERTY_TYPE_MULTIPLIERS = {
        'BEAUTY': 1.0,   
        'COMMERCIAL': 1.5,   
        'HOME': 2,   
        }

        MAX_FLOOD_RISK = 200
        flood_risk = 0

        for flood in flood_data.get('items'):
            severityLevel = flood.get('severityLevel', 4)
            isTidal = flood.get('isTidal', False)

            score = 0
            if severityLevel == 1:
                score = 20
            elif severityLevel == 2:
                score = 15
            elif severityLevel == 3:
                score = 10

            if isTidal: 
                score += 10

            flood_risk += score
            print(flood_risk)

        flood_risk *= PROPERTY_TYPE_MULTIPLIERS.get(product_type, 1)
        print(f'flood_risk -- {flood_risk}')
        normalized_flood_risk = min(flood_risk/MAX_FLOOD_RISK, 1) * 100
        return normalized_flood_risk
    
    except Exception as e:
        raise ValueError(f"Error calculating flood risk: {e}")
    


def calculate_roi(
    quote_premium: float, 
    broker_commission: float, 
    operational_cost: float = 15, 
    marketing_cost: float = 25
) -> float:
    """
    Calculates the ROI for a single quote.

    ROI = ((Revenue - Costs) / Costs) * 100
      Revenue = quote_premium
      Costs = broker_commission + operational_cost + marketing_cost
    """

    revenue = quote_premium
    costs = broker_commission + operational_cost + marketing_cost
    net_profit = revenue - costs

    # Avoiding divide-by-zero
    if costs == 0:
        return 0

    roi_percentage = (net_profit / costs) * 100
    return round(roi_percentage, 2)



    




    
