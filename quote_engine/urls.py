from django.urls import path
from . import views

"""
This file defines the URL patterns for the quote_engine app.


"""

urlpatterns = [
    path('submitquote/', views.submit_quote, name = 'submit_quote'),
    path('submitcsvfile/', views.submit_quotes_csv, name = 'submit_quotes_csv'),
    path('getquote/', views.getQuote, name = 'getQuotes')
]