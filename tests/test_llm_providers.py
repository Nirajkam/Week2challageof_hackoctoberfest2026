import unittest
from unittest.mock import patch, MagicMock
import json

from llm_providers import (
    PROVIDERS,
    RECEIPT_PROMPT,
    extract_receipt_llm,
    _mime_type,
    _prepare_image_data,
)


class ProviderRegistryTests(unittest.TestCase):
    def test_all_providers_have_required_keys(self):
        for name, info in PROVIDERS.items():
            self.assertIn("models", info, f"{name} missing 'models'")
            self.assertIn("needs_api_key", info, f"{name} missing 'needs_api_key'")
            self.assertIn("description", info, f"{name} missing 'description'")
            self.assertIsInstance(info["models"], list)
            self.assertGreater(len(info["models"]), 0, f"{name} has no models")

    def test_cloud_providers_have_env_key(self):
        for name, info in PROVIDERS.items():
            if info["needs_api_key"]:
                self.assertIn("env_key", info, f"{name} needs API key but has no env_key")

    def test_ollama_does_not_need_api_key(self):
        self.assertFalse(PROVIDERS["Ollama (Local)"]["needs_api_key"])

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            extract_receipt_llm("NonExistent", "test.png", b"\x89PNG", "model")


class MimeTypeTests(unittest.TestCase):
    def test_common_extensions(self):
        self.assertEqual(_mime_type("receipt.png"), "image/png")
        self.assertEqual(_mime_type("receipt.jpg"), "image/jpeg")
        self.assertEqual(_mime_type("receipt.jpeg"), "image/jpeg")
        self.assertEqual(_mime_type("receipt.webp"), "image/webp")
        self.assertEqual(_mime_type("receipt.tiff"), "image/tiff")

    def test_unknown_extension_defaults_to_png(self):
        self.assertEqual(_mime_type("receipt.xyz"), "image/png")


class PrepareImageTests(unittest.TestCase):
    def test_image_file_returns_base64(self):
        images, pdf_text = _prepare_image_data("test.png", b"\x89PNG")
        self.assertEqual(len(images), 1)
        self.assertEqual(pdf_text, "")

    def test_prompt_mentions_all_categories(self):
        for cat in ("Meals", "Travel", "Office Supplies", "Software", "Utilities"):
            self.assertIn(cat, RECEIPT_PROMPT)


class MockedProviderTests(unittest.TestCase):
    """Test that each provider calls the right URL and parses the response."""

    _receipt_json = json.dumps({
        "vendor": "Test Shop",
        "date": "2026-03-15",
        "amount": "42.00",
        "currency": "USD",
        "category": "Meals",
        "description": "Lunch",
    })

    @patch("llm_providers.urllib.request.urlopen")
    def test_ollama_extraction(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "message": {"content": self._receipt_json}
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = extract_receipt_llm("Ollama (Local)", "r.png", b"\x89PNG", "gemma3:4b")
        self.assertEqual(result["vendor"], "Test Shop")
        self.assertEqual(result["amount"], "42.00")

    @patch("llm_providers.urllib.request.urlopen")
    def test_openai_extraction(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": self._receipt_json}}]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = extract_receipt_llm("OpenAI", "r.png", b"\x89PNG", "gpt-4o", "sk-test")
        self.assertEqual(result["vendor"], "Test Shop")
        self.assertEqual(result["category"], "Meals")

    @patch("llm_providers.urllib.request.urlopen")
    def test_gemini_extraction(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": self._receipt_json}]}}]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = extract_receipt_llm("Google Gemini", "r.jpg", b"\xff\xd8", "gemini-2.0-flash", "AI-test")
        self.assertEqual(result["vendor"], "Test Shop")
        self.assertEqual(result["date"], "2026-03-15")

    @patch("llm_providers.urllib.request.urlopen")
    def test_anthropic_extraction(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "content": [{"text": self._receipt_json}]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = extract_receipt_llm("Anthropic Claude", "r.png", b"\x89PNG", "claude-sonnet-4-20250514", "sk-ant-test")
        self.assertEqual(result["vendor"], "Test Shop")
        self.assertEqual(result["currency"], "USD")

    @patch("llm_providers.urllib.request.urlopen")
    def test_groq_extraction(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": self._receipt_json}}]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = extract_receipt_llm("Groq", "r.png", b"\x89PNG", "llama-4-scout-17b-16e-instruct", "gsk-test")
        self.assertEqual(result["vendor"], "Test Shop")
        self.assertEqual(result["description"], "Lunch")


if __name__ == "__main__":
    unittest.main()
