import pytest
from unittest.mock import patch, Mock
from quote_engine.riskservice import RiskService
from django.test import TestCase


"""
This file defines the tests for the RiskService class in the quote_engine app.

The RiskService class is responsible for calculating the risks associated with a location
and a product type, as well as determining the validity of a quote based on the total risk
of the location.

The tests in this file will cover the following scenarios:
- Calculating the risks associated with a location
- Determining the validity of a quote based on the total risk
- Determining the risk type based on the total risk threshold

The tests will use the mock library to mock external dependencies such as the flood data API
and the crime data API. This will allow us to test the RiskService class in isolation from
these external services.

The tests will also cover edge cases such as invalid input values and unexpected exceptions
that may occur during the risk calculation process.


"""

class TestRiskService(TestCase):

    @patch('quote_engine.riskservice.get_long_lat')
    @patch('quote_engine.riskservice.get_flood_data_for_location') 
    @patch('quote_engine.riskservice.get_crimes_for_location')
    @patch('quote_engine.riskservice.calculate_flood_risk')
    @patch('quote_engine.riskservice.calculate_crime_risk')
    def test_calculate_location_risks_success(
        self, 
        mock_calc_crime_risk,
        mock_calc_flood_risk,
        mock_get_crimes,
        mock_get_flood_data,
        mock_get_coords
    ):
        # Arrange
        mock_get_coords.return_value = (51.5074, -0.1278)
        mock_get_flood_data.return_value = {"flood_data": "test"}
        mock_get_crimes.return_value = {"crime_data": "test"}
        mock_calc_flood_risk.return_value = "LOW"
        mock_calc_crime_risk.return_value = "MEDIUM"
        
        # Act
        result = RiskService.calculate_location_risks(
            postcode="SW1A 1AA",
            product_type="HOME",
            timestamp="2024-01-25"
        )

        # Assert
        assert result == {
            'flood_risk': 'LOW',
            'crime_risk': 'MEDIUM'
        }
        
        mock_get_coords.assert_called_once_with("SW1A 1AA")
        mock_get_flood_data.assert_called_once_with(lat=51.5074, long=-0.1278)
        mock_get_crimes.assert_called_once_with("2024-01-25", lat=51.5074, long=-0.1278)

    def test_calculate_location_risks_invalid_inputs(self):
        # Add input validation to RiskService.calculate_location_risks first
        with self.assertRaises(ValueError):
            RiskService.calculate_location_risks(
                postcode="",
                product_type="HOME",
                timestamp="2024-01-25"
            )

    def test_quote_validity(self):
        # Test quote validity calculations
        assert RiskService.quote_validity("HIGH_VALUE_RISK") == 7
        assert RiskService.quote_validity("STANDARD_VALUE_RISK") == 14
        assert RiskService.quote_validity("UNKNOWN") is None

    def test_risk_type(self):
        # Test risk type calculations based on total risk thresholds
        assert RiskService.risk_type(40, 30) == "STANDARD_VALUE_RISK"  # Total 70 < 100
        assert RiskService.risk_type(60, 45) == "HIGH_VALUE_RISK"     # Total 105 > 100
        assert RiskService.risk_type(70, 35) == "HIGH_VALUE_RISK"     # Total 105 > 100