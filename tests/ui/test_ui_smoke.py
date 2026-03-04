import importlib
import os
import sys
from unittest import TestCase
from unittest.mock import patch


class TestUiSmoke(TestCase):
    def test_streamlit_app_imports(self):
        # Ensure this smoke test does not depend on external API keys/network.
        with patch.dict(os.environ, {"OMDB_API_KEY": "test-key"}, clear=False):
            with patch(
                "popcorn_meter.infrastructure.omdb_client.OmdbClient.search_by_title",
                return_value={"Response": "False", "Error": "mocked"},
            ):
                sys.modules.pop("popcorn_meter.ui.streamlit_app", None)
                module = importlib.import_module("popcorn_meter.ui.streamlit_app")
                self.assertIsNotNone(module)
