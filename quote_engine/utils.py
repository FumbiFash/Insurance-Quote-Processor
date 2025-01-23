from functools import wraps
import time
import requests
from .models import APILog
import json
import logging


logger = logging.getLogger('django')


def log_api_call(max_retries: int = 3, backoff_factor: int = 2):
    """
    Provides a decorator to log an API request and response, as well as to retry
    the wrapped function if an exception occurs.

    This includes recording request details (method, URL, headers, body) and the
    response status and body in the APILog model. If the function raises an exception, 
    the call is retried up to 3 times,
    with an exponential backoff also accounted for.

    :param max_retries: The maximum number of retry attempts before giving up.
                        
    :type max_retries: int
    :param backoff_factor: The factor by which the wait time is multiplied after every
                           failed attempt.
    :type backoff_factor: int
    :return: A decorator function that is applied to views
    """



    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            attempt = 0
            wait_time = 1

            while attempt < max_retries:
                try:
                   
                    response = func(request, *args, **kwargs)
                    
                    # Log the API call
                    try:
                        # Handle request body
                        request_body = ''
                        if hasattr(request, 'data'):
                            request_body = json.dumps(request.data)
                        
                        # Handle response body
                        if hasattr(response, 'rendered_content'):
                            response_body = response.rendered_content.decode('utf-8')
                        else:
                            response_body = str(response.content)
                        
                        # Create log entry
                        APILog.objects.create(
                            request_method=request.method,
                            request_url=request.build_absolute_uri(),
                            request_headers=json.dumps(dict(request.headers)),
                            request_body=request_body,
                            response_status=response.status_code,
                            response_body=response_body
                        )
                        
                        logger.info(f'API call logged: {request.method} {request.build_absolute_uri()}')
                    
                    except Exception as log_error:
                        logger.error(f"Failed to log API call: {str(log_error)}")
                    
                    return response
                
                except Exception as e:
                    attempt += 1
                    
                    # Log the retry attempt
                    logger.warning(f"Retry attempt {attempt}/{max_retries} for API call. Error: {str(e)}")
                    
                    # If all retries exhausted, raise the last exception
                    if attempt >= max_retries:
                        logger.error(f"Max retries reached for API call. Final error: {str(e)}")
                        raise
                    
                    # Wait before next retry with exponential backoff
                    time.sleep(wait_time)
                    wait_time *= backoff_factor
        
        return wrapper
    return decorator

    

