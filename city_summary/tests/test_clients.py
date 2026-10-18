import unittest
from unittest.mock import patch

from clients.http import APIResponseError
from clients.rates import CurrencyNotFoundError, get_rate
from clients.weather import CityNotFoundError, get_weather


class TestWeatherClient(unittest.TestCase):
    @patch("clients.weather.get_json")
    def test_valid_weather(self, mock_get_json):
        mock_get_json.side_effect = [
            {"results": [{"latitude": 55.75, "longitude": 37.62}]},
            {
                "current": {
                    "temperature_2m": -3.2,
                    "weather_code": 0,
                }
            },
        ]

        result = get_weather("Moscow")

        self.assertEqual(
            result,
            {"temp_c": -3.2, "description": "clear sky"},
        )
        self.assertEqual(mock_get_json.call_count, 2)

    @patch("clients.weather.get_json")
    def test_missing_results_for_unknown_city(self, mock_get_json):
        mock_get_json.return_value = {"generationtime_ms": 0.8}

        with self.assertRaises(CityNotFoundError):
            get_weather("UnknownCity")

    @patch("clients.weather.get_json")
    def test_malformed_geocoding_response(self, mock_get_json):
        mock_get_json.return_value = {}

        with self.assertRaises(APIResponseError):
            get_weather("Moscow")

    @patch("clients.weather.get_json")
    def test_city_not_found(self, mock_get_json):
        mock_get_json.return_value = {"results": []}

        with self.assertRaises(CityNotFoundError):
            get_weather("UnknownCity")

    @patch("clients.weather.get_json")
    def test_invalid_coordinates(self, mock_get_json):
        mock_get_json.return_value = {
            "results": [{"latitude": 200, "longitude": 37.62}]
        }

        with self.assertRaises(APIResponseError):
            get_weather("Moscow")

    @patch("clients.weather.get_json")
    def test_missing_weather_data(self, mock_get_json):
        mock_get_json.side_effect = [
            {"results": [{"latitude": 55.75, "longitude": 37.62}]},
            {"wrong_field": 123},
        ]

        with self.assertRaises(APIResponseError):
            get_weather("Moscow")

    @patch("clients.weather.get_json")
    def test_invalid_temperature(self, mock_get_json):
        mock_get_json.side_effect = [
            {"results": [{"latitude": 55.75, "longitude": 37.62}]},
            {
                "current": {
                    "temperature_2m": "cold",
                    "weather_code": 0,
                }
            },
        ]

        with self.assertRaises(APIResponseError):
            get_weather("Moscow")


class TestRatesClient(unittest.TestCase):
    @patch("clients.rates.get_json")
    def test_valid_rate(self, mock_get_json):
        mock_get_json.return_value = {
            "date": "2026-10-18",
            "base": "USD",
            "quote": "RUB",
            "rate": 83.72,
        }

        self.assertEqual(get_rate("USD"), 83.72)

    @patch("clients.rates.get_json")
    def test_invalid_currency_format(self, mock_get_json):
        with self.assertRaises(CurrencyNotFoundError):
            get_rate("US123")

        mock_get_json.assert_not_called()

    @patch("clients.rates.get_json")
    def test_unknown_currency(self, mock_get_json):
        mock_get_json.side_effect = APIResponseError(404, "Currency not found")

        with self.assertRaises(CurrencyNotFoundError):
            get_rate("XYZ")

    @patch("clients.rates.get_json")
    def test_invalid_rate(self, mock_get_json):
        mock_get_json.return_value = {
            "date": "2026-10-18",
            "base": "USD",
            "quote": "RUB",
            "rate": float("nan"),
        }

        with self.assertRaises(APIResponseError):
            get_rate("USD")

    @patch("clients.rates.get_json")
    def test_invalid_date(self, mock_get_json):
        mock_get_json.return_value = {
            "date": "not-a-date",
            "base": "USD",
            "quote": "RUB",
            "rate": 83.72,
        }

        with self.assertRaises(APIResponseError):
            get_rate("USD")
