import pytest
from unittest.mock import patch, Mock

from popcorn_meter.infrastructure.omdb_client import OmdbClient


# ---------- Missing API key ----------

def test_search_by_title_raises_if_no_api_key(monkeypatch):
    monkeypatch.delenv("OMDB_API_KEY", raising=False)

    client = OmdbClient(api_key=None)

    with pytest.raises(RuntimeError, match="OMDB_API_KEY not set"):
        client.search_by_title("Inception")


# ---------- Successful response ----------

@patch("popcorn_meter.infrastructure.omdb_client.requests.get")
def test_search_by_title_success(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {"Title": "Inception"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    client = OmdbClient(api_key="dummy-key")
    result = client.search_by_title("Inception")

    mock_get.assert_called_once()
    assert result["Title"] == "Inception"


# ---------- HTTP error ----------

@patch("popcorn_meter.infrastructure.omdb_client.requests.get")
def test_search_by_title_http_error(mock_get):
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("HTTP error")
    mock_get.return_value = mock_response

    client = OmdbClient(api_key="dummy-key")

    with pytest.raises(Exception):
        client.search_by_title("Inception")
