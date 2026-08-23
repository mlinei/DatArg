from __future__ import annotations

import io
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from argentina_economic_data.inflation import acquire


class _Headers:
    def get_content_type(self) -> str:
        return "application/json"


class _Response(io.BytesIO):
    headers = _Headers()


class DownloadRetryTests(unittest.TestCase):
    @patch("argentina_economic_data.inflation.time.sleep")
    @patch("argentina_economic_data.inflation.urllib.request.urlopen")
    def test_retries_transient_http_errors(self, urlopen, sleep):
        urlopen.side_effect = [
            urllib.error.HTTPError("https://example.test/data", 502, "Bad Gateway", None, None),
            urllib.error.HTTPError("https://example.test/data", 503, "Unavailable", None, None),
            _Response(b'{"data":"' + b"x" * 128 + b'"}'),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            artifact = acquire(
                "transient_source",
                "https://example.test/data.json",
                Path(tmp),
            )

        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [2, 4])
        self.assertGreater(artifact.size, 100)

    @patch("argentina_economic_data.inflation.time.sleep")
    @patch("argentina_economic_data.inflation.urllib.request.urlopen")
    def test_does_not_retry_permanent_http_errors(self, urlopen, sleep):
        urlopen.side_effect = urllib.error.HTTPError(
            "https://example.test/missing", 404, "Not Found", None, None
        )

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(urllib.error.HTTPError):
                acquire("missing_source", "https://example.test/missing.json", Path(tmp))

        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
