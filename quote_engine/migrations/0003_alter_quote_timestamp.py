# Generated by Django 4.2.18 on 2025-01-23 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quote_engine", "0002_apilog"),
    ]

    operations = [
        migrations.AlterField(
            model_name="quote",
            name="timestamp",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]