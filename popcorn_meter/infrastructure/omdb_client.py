from __future__ import annotations

import os
from typing import Any

import requests


class OmdbClient:
    """
    OMDb client.

    Behavior (matches unit tests):
    - If api_key is explicitly provided (including None), use it as-is (no fallback).
    - If api_key is omitted, try env/secrets fallback.
    - search_by_title raises RuntimeError("OMDB_API_KEY not set") when key missing.
    """

    def __init__(self, api_key: str | None = "__AUTO__") -> None:
        if api_key == "__AUTO__":
            self.api_key = self._resolve_key()
        else:
            # Explicitly provided (even None) -> do not fallback
            self.api_key = api_key

    def _resolve_key(self) -> str | None:
        k = os.getenv("OMDB_API_KEY")
        if k:
            return k

        # Optional: Streamlit secrets support
        try:
            import streamlit as st  # type: ignore
            k2 = st.secrets.get("OMDB_API_KEY")  # type: ignore[attr-defined]
            if k2:
                return str(k2)
        except Exception:
            pass

        return None

    def search_by_title(self, title: str) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("OMDB_API_KEY not set")

        t = (title or "").strip()
        if not t:
            return {"Response": "False", "Error": "Empty title"}

        url = "http://www.omdbapi.com/"
        r = requests.get(url, params={"apikey": self.api_key, "t": t}, timeout=10)
        r.raise_for_status()

        data = r.json()
        if not isinstance(data, dict):
            return {"Response": "False", "Error": "Invalid response from OMDb"}
        return data