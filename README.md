# Insurance-Quote-Processor

# Risk Validator Service

A Django application for validating and processing quotes with risk assessment features.

## Architecture & Approach


### Core Components

- **Quote Engine**: Main application which handles quote processing and risk validation
  - `models.py`: Data models for quotes and API log 
  - `views.py`: API endpoints for quote submission and quote fetching
  - `serializers.py`: Data serialization/validation 
  - `risk_utils.py`: Risk calculation and validation utilities. Responsible for external API calls to Postcodes.io, Data.Police.uk, environment.data.gov.uk. Postcodes.io external API call is responsible for converting postcode data to longitude,latitude coordinates. Long/Lat coordinates are utilized to retrieve crime and flood data to be used for risk assessment by location. 
  - `riskservice.py`: Contains class which performs calculations and assessments for risk and roi
  - `utils.py`: Utility function that contains functionality for retry logic and exponential backoff
  - quote_queries.sql : SQl queries for: Conversion rates by product type and age bracket, finding the top 3 postcodes by quote volume, Average premium by product type and payment method,  Potential fraud patterns, Broker commission report

### Key Design Decisions

1. **Layered Architecture**
   - API Layer (views) → Serialization → Business Logic (services) → Data Layer
   - All dependencies have been managed using a python virtual environment
   - Clear separation of concerns between components
   - Risk validation logic isolated in dedicated modules
   - Data fetched from external APIs are stored in Redis cache to reduce costs and to account for potential API downtime
   - Serializer-Level Checks: Ensured input data meets required formats and business rules.

2. **Django REST Framework**
   - Utilized for API development and request handling
   - Built-in serialization and validation
   - Utilized for handling authentication/authorization (Not implemented for the purpose of this challenge, but can be extended for future use).
   - Ensures scalability and maintainability for future API enhancements and integrations

3. **Application Design** 
   - Risk calculation logic separated from request handling
   - Reusable utility functions in dedicated modules
   - Easy to add new risk validation rules

## Code Quality Measures

1. **Code Organization**
   - Logical separation of functionality into modules
   - Clear naming conventions
   - Django best practices followed

2. **Error Handling**
   - Consistent error responses
   - Proper validation at serializer level
   - Business logic exceptions handled appropriately
   - Logging strategy implemented for debugging purposes

3. **Documentation**
   - Docstrings for key functions
   - API endpoint documentation
   - Clear code comments where needed

## Testing Approach

### Unit Tests
- Test individual components in isolation
- Coverage for:
  - Serializer validation
  - Risk calculation logic
  - Utility functions
  - Model methods

- The following areas were not addressed due to time constraints:

   --API endpoint tests 
   -- End-to-end request/response validation
   -- Feature for flagging suspicious quotes is not fully functional. While the framework for this logic is setup, refinement is needed for accuracy and edge cases.

### Test Tools
- Django's TestCase framework
- pytest for unit testing

## Assumptions Made 

   - Valid quote data structure
   - Required fields for risk assessment
   - Flood and crime data essential for risk assessment
    - Reasonable request volume
   - Acceptable response times
   - Database scaling needs
   - Business rule constraints
   - Positive value constraint for content_value field


## Production Deployment


### Deployment Process

The application is designed to be deployed on Heroku with the following steps:
Deployment Process

 -- Ensure Procfile is created and included in directory with the following content: web: gunicorn projectname.wsgi

  -- Set necessary environment variables on Heroku (e.g., SECRET_KEY, DEBUG=False, DATABASE_URL, API keys) although no SECRET_KEY is in use for this application.
  -- Push the code to the Heroku remote repository
  -- Setup database : Run database migrations after deployment
  -- Populate static files:
  -- Static Files: static files will be servedusing Whitenoise, which must be included already integrated into the project.



### Scaling Strategy which are utilized 
- Database optimization
- Caching implementation


## Development Setup
Clone the repository 
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
