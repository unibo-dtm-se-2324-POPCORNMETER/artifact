import os
import requests

class OmdbClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OMDB_API_KEY")

    def search_by_title(self, title: str) -> dict:
        if not self.api_key:
            raise RuntimeError("OMDB_API_KEY not set")
        url = "http://www.omdbapi.com/"
        params = {"apikey": self.api_key, "t": title}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()