import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch

from clients.http import APIResponseError, APIUnavailableError
from clients.rates import CurrencyNotFoundError
from clients.weather import CityNotFoundError
from main import main

SAMPLE_SUMMARY = {
    "city": "Moscow",
    "weather": {
        "temp_c": -5.0,
        "description": "snow",
        "warm_clothes": True,
    },
    "rates": {
        "currency": "USD",
        "rate_to_rub": 83.72,
        "expensive": False,
    },
}


class TestCLI(unittest.TestCase):
    def run_cli(self, arguments, summary=None, error=None):
        stdout = StringIO()
        stderr = StringIO()

        with (
            patch("sys.argv", ["main.py", *arguments]),
            patch("main.build_city_summary") as mock_build,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            if error is not None:
                mock_build.side_effect = error
            else:
                mock_build.return_value = summary

            try:
                exit_code = main()
            except SystemExit as exc:
                exit_code = exc.code

        return exit_code, stdout.getvalue(), stderr.getvalue(), mock_build

    def test_success(self):
        code, output, errors, mock_build = self.run_cli(
            ["--city", "Moscow"], SAMPLE_SUMMARY
        )

        self.assertEqual(code, 0)
        self.assertIn("Город: Moscow", output)
        self.assertIn("Тёплая одежда: да", output)
        self.assertIn("USD→RUB: 83.72", output)
        self.assertEqual(errors, "")
        mock_build.assert_called_once_with("Moscow", "USD")

    def test_json_output(self):
        code, output, errors, _ = self.run_cli(
            ["--city", "Moscow", "--json"], SAMPLE_SUMMARY
        )

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output), SAMPLE_SUMMARY)
        self.assertEqual(errors, "")

    def test_missing_city(self):
        code, _, errors, mock_build = self.run_cli(["--currency", "EUR"])

        self.assertEqual(code, 2)
        self.assertIn("--city", errors)
        mock_build.assert_not_called()

    def test_empty_city(self):
        code, _, _, mock_build = self.run_cli(["--city", "   "])

        self.assertEqual(code, 2)
        mock_build.assert_not_called()

    def test_city_not_found(self):
        code, output, errors, _ = self.run_cli(
            ["--city", "Unknown"],
            error=CityNotFoundError("Город не найден"),
        )

        self.assertEqual(code, 3)
        self.assertEqual(output, "")
        self.assertIn("Город не найден", errors)

    def test_currency_not_found(self):
        code, _, errors, _ = self.run_cli(
            ["--city", "Moscow", "--currency", "XYZ"],
            error=CurrencyNotFoundError("Валюта не найдена"),
        )

        self.assertEqual(code, 3)
        self.assertIn("Валюта не найдена", errors)

    def test_api_unavailable(self):
        code, _, errors, _ = self.run_cli(
            ["--city", "Moscow"],
            error=APIUnavailableError("Сервис недоступен"),
        )

        self.assertEqual(code, 4)
        self.assertIn("Сервис недоступен", errors)

    def test_invalid_api_response(self):
        code, _, errors, _ = self.run_cli(
            ["--city", "Moscow"],
            error=APIResponseError(None, "Некорректный JSON"),
        )

        self.assertEqual(code, 4)
        self.assertIn("Некорректный JSON", errors)
