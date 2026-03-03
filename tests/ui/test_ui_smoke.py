from unittest import TestCase
import importlib


class TestUiSmoke(TestCase):
    def test_streamlit_app_imports(self):
        module = importlib.import_module("popcorn_meter.ui.streamlit_app")
        self.assertIsNotNone(module)
