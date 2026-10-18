import unittest
from unittest.mock import patch

from processing.service import build_city_summary


class TestCitySummary(unittest.TestCase):
    @patch("processing.service.get_rate")
    @patch("processing.service.get_weather")
    def test_cold_weather(self, mock_weather, mock_rate):
        mock_weather.return_value = {
            "temp_c": -5.0,
            "description": "snow",
        }
        mock_rate.return_value = 83.72

        result = build_city_summary("Moscow")

        self.assertEqual(result["city"], "Moscow")
        self.assertTrue(result["weather"]["warm_clothes"])
        self.assertFalse(result["rates"]["expensive"])
        self.assertEqual(result["rates"]["currency"], "USD")

    @patch("processing.service.get_rate")
    @patch("processing.service.get_weather")
    def test_warm_weather_and_expensive_rate(self, mock_weather, mock_rate):
        mock_weather.return_value = {
            "temp_c": 20.0,
            "description": "clear sky",
        }
        mock_rate.return_value = 120.0

        result = build_city_summary("London", "EUR")

        self.assertFalse(result["weather"]["warm_clothes"])
        self.assertTrue(result["rates"]["expensive"])
        self.assertEqual(result["rates"]["currency"], "EUR")
