import os
from unittest import TestCase
from unittest.mock import Mock, patch

from popcorn_meter.infrastructure.omdb_client import OmdbClient


class TestOmdbClient(TestCase):
    def test_search_by_title_raises_if_no_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            client = OmdbClient(api_key=None)
            with self.assertRaisesRegex(RuntimeError, "OMDB_API_KEY not set"):
                client.search_by_title("Inception")

    @patch("popcorn_meter.infrastructure.omdb_client.requests.get")
    def test_search_by_title_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"Title": "Inception"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = OmdbClient(api_key="dummy-key")
        result = client.search_by_title("Inception")

        mock_get.assert_called_once()
        self.assertEqual(result["Title"], "Inception")

    @patch("popcorn_meter.infrastructure.omdb_client.requests.get")
    def test_search_by_title_http_error(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP error")
        mock_get.return_value = mock_response

        client = OmdbClient(api_key="dummy-key")

        with self.assertRaises(Exception):
            client.search_by_title("Inception")
