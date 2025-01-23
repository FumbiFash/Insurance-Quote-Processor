from django.db import models


"""
This file defines the models for the quote_engine app.

The Quote model represents a single quote record in the system. It contains fields for the
quote reference, timestamp, product type, customer age, risk postcode, building value, contents value,
quote premium, conversion status, payment type, broker commission.

The APILog model represents a log entry for API requests and responses made by the system. It contains
fields for the timestamp, request method, request URL, request headers, request body, response status,
and response body.

The models are used to store and retrieve data from the database


"""
class Quote(models.Model):
    quote_reference = models.CharField(max_length = 50, unique = True)
    timestamp = models.DateTimeField()
    product_type = models.CharField(max_length = 50,choices=[('HOME', 'HOME'), ('BEAUTY', 'BEAUTY'), ('COMMERCIAL','COMMERCIAL')])
    customer_age = models.IntegerField()
    risk_postcode = models.CharField(max_length = 20)
    building_value = models.DecimalField(max_digits = 12, decimal_places = 2)
    contents_value = models.DecimalField(max_digits = 12, decimal_places = 2)
    quote_premium = models.DecimalField(max_digits = 12, decimal_places = 2)
    conversion_status = models.CharField(max_length = 20,choices=[('QUOTED', 'QUOTED'), ('ACCEPTED', 'ACCEPTED'), ('LAPSED','LAPSED')])
    payment_type = models.CharField(max_length = 20,choices=[('ANNUAL', 'ANNUAL'), ('MONTHLY', 'MONTHLY')])
    broker_commission = models.DecimalField(max_digits = 12, decimal_places = 2)

    date_created = models.DateTimeField(auto_now_add = True)
    date_updated = models.DateTimeField(auto_now = True)
    suspicious = models.BooleanField(default = False)

    def __str__(self):
        return self.quote_reference
    

class APILog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    request_method = models.CharField(max_length=10)
    request_url = models.CharField(max_length=600)
    request_headers = models.TextField()
    request_body = models.TextField()
    response_status = models.IntegerField()
    response_body = models.TextField()

    def __str__(self):
        return f"API Log {self.id} - {self.timestamp} - {self.request_url}"
