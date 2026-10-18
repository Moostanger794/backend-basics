import unittest
from unittest.mock import Mock, call, patch

import requests

from clients.http import APIResponseError, APIUnavailableError, get_json


def make_response(status=200, data=None, headers=None):
    response = Mock()
    response.status_code = status
    response.headers = headers or {}
    response.json.return_value = {"ok": True} if data is None else data
    return response


class TestHTTPClient(unittest.TestCase):
    @patch("clients.http.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = make_response()

        result = get_json("https://example.com")

        self.assertEqual(result, {"ok": True})
        mock_get.assert_called_once_with("https://example.com", params=None, timeout=10)

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_timeout_retry(self, mock_get, mock_sleep):
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            make_response(),
        ]

        result = get_json("https://example.com")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(
            mock_sleep.call_args_list,
            [call(1.0), call(2.0)],
        )

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_connection_error(self, mock_get, mock_sleep):
        mock_get.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(APIUnavailableError):
            get_json("https://example.com")

        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("clients.http.time.sleep")
    def test_server_errors(self, mock_sleep):
        for status in (500, 502, 503, 504):
            with (
                self.subTest(status=status),
                patch("clients.http.requests.get") as mock_get,
            ):
                mock_get.return_value = make_response(status=status)

                with self.assertRaises(APIUnavailableError):
                    get_json("https://example.com")

                self.assertEqual(mock_get.call_count, 3)

    @patch("clients.http.time.sleep")
    @patch("clients.http.requests.get")
    def test_429_retry_after(self, mock_get, mock_sleep):
        mock_get.side_effect = [
            make_response(
                status=429,
                headers={"Retry-After": "7"},
            ),
            make_response(),
        ]

        result = get_json("https://example.com")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(7.0)

    @patch("clients.http.requests.get")
    def test_invalid_json(self, mock_get):
        response = make_response()
        response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = response

        with self.assertRaises(APIResponseError):
            get_json("https://example.com")

    @patch("clients.http.requests.get")
    def test_wrong_json_type(self, mock_get):
        mock_get.return_value = make_response(data=[1, 2, 3])

        with self.assertRaises(APIResponseError):
            get_json("https://example.com")

    @patch("clients.http.requests.get")
    def test_unexpected_status(self, mock_get):
        mock_get.return_value = make_response(status=400)

        with self.assertRaises(APIResponseError):
            get_json("https://example.com")

        self.assertEqual(mock_get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
