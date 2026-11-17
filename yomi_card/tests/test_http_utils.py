import unittest
from unittest.mock import Mock, patch

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import requests

from src.http_utils import request_with_retries


class TestRequestWithRetries(unittest.TestCase):

    @patch("src.http_utils.time.sleep")
    def test_retries_transient_server_error(self, mock_sleep):
        temporary_error = requests.Response()
        temporary_error.status_code = 503

        success = requests.Response()
        success.status_code = 200

        mock_request = Mock(side_effect=[temporary_error, success])

        result = request_with_retries(
            mock_request,
            "https://example.test",
            retry_safe=True,
        )

        self.assertIs(result, success)
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_once_with(0.5)

    @patch("src.http_utils.time.sleep")
    def test_does_not_retry_unsafe_timeout(self, mock_sleep):
        mock_request = Mock(side_effect=requests.Timeout("timed out"))

        with self.assertRaises(requests.Timeout):
            request_with_retries(
                mock_request,
                "http://anki.test",
                retry_safe=False,
            )

        self.assertEqual(mock_request.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("src.http_utils.time.sleep")
    def test_stops_after_max_attempts(self, mock_sleep):
        temporary_error = requests.Response()
        temporary_error.status_code = 503
        mock_request = Mock(return_value=temporary_error)

        with self.assertRaises(requests.HTTPError):
            request_with_retries(
                mock_request,
                "https://example.test",
                retry_safe=True,
                max_attempts=3,
            )

        self.assertEqual(mock_request.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
    @patch("src.http_utils.time.sleep")
    def test_retries_429_after_retry_after(self, mock_sleep):
        rate_limited = requests.Response()
        rate_limited.status_code = 429
        rate_limited.headers["Retry-After"] = "2"

        success = requests.Response()
        success.status_code = 200
        mock_request = Mock(side_effect=[rate_limited, success])

        request_with_retries(
            mock_request,
            "https://example.test",
            retry_safe=True,
        )

        mock_sleep.assert_called_once_with(2)

    @patch("src.http_utils.time.sleep")
    def test_retries_429_after_http_date(self, mock_sleep):
        rate_limited = requests.Response()
        rate_limited.status_code = 429
        retry_at = datetime.now(timezone.utc) + timedelta(seconds=30)
        rate_limited.headers["Retry-After"] = format_datetime(
            retry_at,
            usegmt=True,
        )

        success = requests.Response()
        success.status_code = 200
        mock_request = Mock(side_effect=[rate_limited, success])

        request_with_retries(
            mock_request,
            "https://example.test",
            retry_safe=True,
            max_retry_after=60.0,
        )

        delay = mock_sleep.call_args.args[0]
        self.assertGreater(delay, 28.0)
        self.assertLessEqual(delay, 30.0)

    @patch("src.http_utils.time.sleep")
    def test_does_not_retry_after_wait_limit(self, mock_sleep):
        rate_limited = requests.Response()
        rate_limited.status_code = 429
        rate_limited.headers["Retry-After"] = "31"
        mock_request = Mock(return_value=rate_limited)

        with self.assertRaises(requests.HTTPError):
            request_with_retries(
                mock_request,
                "https://example.test",
                retry_safe=True,
                max_retry_after=30.0,
            )

        self.assertEqual(mock_request.call_count, 1)
        mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()