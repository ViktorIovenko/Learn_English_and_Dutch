import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from app.auth_links import verify_auth_token
from bot.auth import _build_app_url
from config import Config


class TelegramWebAppLinkTests(unittest.TestCase):
    def test_https_webapp_url_contains_valid_auth_token(self):
        with (
            patch.object(Config, "PUBLIC_BASE_URL", "https://app.example.test"),
            patch.object(Config, "SECRET_KEY", "test-secret"),
            patch.object(Config, "BOT_TOKEN", "test-bot-token"),
        ):
            url, use_webapp, use_inline = _build_app_url(12345)
            parsed = urlsplit(url)
            token = parse_qs(parsed.query)["auth"][0]

            self.assertTrue(use_webapp)
            self.assertTrue(use_inline)
            self.assertEqual("", parsed.fragment)
            self.assertEqual("12345", verify_auth_token(token))


if __name__ == "__main__":
    unittest.main()
