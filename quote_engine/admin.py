from django.contrib import admin
from . import models
# Register your models here.

"""
This file registers the models with the Django admin interface
"""
admin.site.register(models.Quote)
admin.site.register(models.APILog)