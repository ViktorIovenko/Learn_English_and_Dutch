import gc
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from app import ai_platform
from app.ai_platform import AiPlatformError, TokenUsage
from app.routes import web
from app.translation_usage import (
    get_translation_usage_snapshot,
    record_translation_usage,
    reset_translation_usage,
)
from config import Config


class TranslationUsageCounterTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()

    def test_tokens_accumulate_without_monthly_period(self):
        record_translation_usage(
            self.conn,
            "101",
            successful=True,
            prompt_tokens=10,
            completion_tokens=4,
            total_tokens=14,
        )
        record_translation_usage(
            self.conn,
            "101",
            successful=False,
            prompt_tokens=8,
            completion_tokens=2,
            total_tokens=10,
        )

        snapshot = get_translation_usage_snapshot(self.conn)

        self.assertEqual(snapshot["scope"], "lifetime")
        self.assertEqual(snapshot["total_tokens"], 24)
        self.assertEqual(snapshot["prompt_tokens"], 18)
        self.assertEqual(snapshot["completion_tokens"], 6)
        self.assertEqual(snapshot["successful_requests"], 1)
        self.assertEqual(snapshot["failed_requests"], 1)
        columns = {
            row["name"] for row in self.conn.execute("PRAGMA table_info(translation_token_usage)")
        }
        self.assertNotIn("period_key", columns)

    def test_total_tokens_falls_back_to_prompt_plus_completion(self):
        record_translation_usage(
            self.conn,
            "101",
            successful=True,
            prompt_tokens=7,
            completion_tokens=3,
            total_tokens=None,
        )
        self.assertEqual(get_translation_usage_snapshot(self.conn)["total_tokens"], 10)

    def test_manual_reset_can_target_user_or_everyone(self):
        record_translation_usage(self.conn, "101", successful=True, total_tokens=12)
        record_translation_usage(self.conn, "202", successful=True, total_tokens=9)

        self.assertEqual(reset_translation_usage(self.conn, user_id="101"), 1)
        snapshot = get_translation_usage_snapshot(self.conn)
        self.assertNotIn("101", snapshot["by_user"])
        self.assertEqual(snapshot["by_user"]["202"]["total_tokens"], 9)
        self.assertEqual(reset_translation_usage(self.conn), 1)
        self.assertEqual(get_translation_usage_snapshot(self.conn)["total_tokens"], 0)


class AiPlatformTokenUsageTests(unittest.TestCase):
    def setUp(self):
        self.old_base_url = Config.AI_PLATFORM_BASE_URL
        self.old_api_key = Config.AI_PLATFORM_API_KEY_TRANSLATE_WORD
        self.old_topic_api_key = Config.AI_PLATFORM_API_KEY_SUGGEST_TOPIC_WORDS
        Config.AI_PLATFORM_BASE_URL = "https://ai.example.test"
        Config.AI_PLATFORM_API_KEY_TRANSLATE_WORD = "test-key"
        Config.AI_PLATFORM_API_KEY_SUGGEST_TOPIC_WORDS = "test-topic-key"

    def tearDown(self):
        Config.AI_PLATFORM_BASE_URL = self.old_base_url
        Config.AI_PLATFORM_API_KEY_TRANSLATE_WORD = self.old_api_key
        Config.AI_PLATFORM_API_KEY_SUGGEST_TOPIC_WORDS = self.old_topic_api_key

    @staticmethod
    def _response(content: str, usage: dict):
        class Response:
            status_code = 200
            ok = True

            def json(self):
                return {"content": content, "usage": usage}

        return Response()

    def test_translate_word_returns_real_provider_usage(self):
        response = self._response(
            '{"nl":"huis","en":"house","ru":"дом"}',
            {"prompt_tokens": 21, "completion_tokens": 9, "total_tokens": 30},
        )
        with patch("app.ai_platform.requests.post", return_value=response):
            runtime = ai_platform._call_runtime_chat(Config.AI_PLATFORM_API_KEY_TRANSLATE_WORD,"huis")
            item, usage = ai_platform._extract_json(runtime.content), runtime.usage

        self.assertEqual(item["en"], "house")
        self.assertEqual(usage, TokenUsage(21, 9, 30))

    def test_invalid_translation_keeps_consumed_token_usage_on_error(self):
        response = self._response(
            "not json",
            {"prompt_tokens": 15, "completion_tokens": 2, "total_tokens": 17},
        )
        with patch("app.ai_platform.requests.post", return_value=response):
            runtime = ai_platform._call_runtime_chat(Config.AI_PLATFORM_API_KEY_TRANSLATE_WORD,"huis")
            with self.assertRaises(AiPlatformError):
                ai_platform._extract_json(runtime.content)

        self.assertEqual(runtime.usage.total_tokens, 17)

    def test_http_error_keeps_provider_usage_when_tokens_were_consumed(self):
        class Response:
            status_code = 502
            ok = False

            def json(self):
                return {
                    "detail": "upstream parse error",
                    "usage": {
                        "prompt_tokens": 19,
                        "completion_tokens": 4,
                        "total_tokens": 23,
                    },
                }

        with patch("app.ai_platform.requests.post", return_value=Response()):
            with self.assertRaises(AiPlatformError) as raised:
                ai_platform._call_runtime_chat(Config.AI_PLATFORM_API_KEY_TRANSLATE_WORD,"huis")

        self.assertEqual(raised.exception.usage, TokenUsage(19, 4, 23))

    def test_topic_generation_returns_real_provider_usage(self):
        response = self._response(
            '["huis", "kamer"]',
            {"prompt_tokens": 30, "completion_tokens": 6, "total_tokens": 36},
        )
        with patch("app.ai_platform.requests.post", return_value=response):
            runtime = ai_platform._call_runtime_chat(Config.AI_PLATFORM_API_KEY_SUGGEST_TOPIC_WORDS,"home")
            words, usage = ai_platform._extract_json(runtime.content), runtime.usage

        self.assertEqual(words, ["huis", "kamer"])
        self.assertEqual(usage, TokenUsage(30, 6, 36))


class TranslationRoutesUsageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "words.db"
        self.old_db_path = Config.DB_PATH
        Config.DB_PATH = str(self.db_path)

        app = Flask(__name__)
        app.secret_key = "test"
        app.register_blueprint(web)
        app.testing = True
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["is_auth"] = True
            session["tg_user_id"] = "101"

    def tearDown(self):
        Config.DB_PATH = self.old_db_path
        self.client = None
        gc.collect()
        self.tmp.cleanup()

    def _snapshot(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            return get_translation_usage_snapshot(conn)

    def test_all_paid_ai_routes_record_real_tokens(self):
        with patch(
            "app.routes.ai_platform.translate_word",
            return_value=({"nl": "huis", "en": "house"}, TokenUsage(20, 5, 25)),
        ):
            response = self.client.post(
                "/api/translate/word",
                json={"word": "huis", "from_lang": "nl"},
            )
        self.assertEqual(response.status_code, 200)

        with patch(
            "app.routes.ai_platform.translate_language",
            return_value=({"word": "maison", "sentence": "La maison."}, TokenUsage(18, 4, 22)),
        ):
            response = self.client.post(
                "/api/translate/language",
                json={
                    "source_word": "huis",
                    "source_sentence": "Het huis.",
                    "source_lang_name": "Dutch",
                    "target_lang_name": "French",
                },
            )
        self.assertEqual(response.status_code, 200)

        with patch(
            "app.routes.ai_platform.suggest_topic_words",
            return_value=(["huis", "kamer"], TokenUsage(30, 6, 36)),
        ):
            response = self.client.post(
                "/api/generate/topic",
                json={"topic": "home", "lang": "nl", "level": "A2", "count": 2},
            )
        self.assertEqual(response.status_code, 200)

        snapshot = self._snapshot()
        self.assertEqual(snapshot["successful_requests"], 3)
        self.assertEqual(snapshot["total_tokens"], 83)

    def test_failed_translation_records_request_and_consumed_tokens(self):
        error = AiPlatformError("bad translation", usage=TokenUsage(12, 3, 15))
        with patch("app.routes.ai_platform.translate_word", side_effect=error):
            response = self.client.post(
                "/api/translate/word",
                json={"word": "huis", "from_lang": "nl"},
            )

        self.assertEqual(response.status_code, 502)
        snapshot = self._snapshot()
        self.assertEqual(snapshot["failed_requests"], 1)
        self.assertEqual(snapshot["total_tokens"], 15)

    def test_failed_topic_generation_records_request_and_consumed_tokens(self):
        error = AiPlatformError("bad generation", usage=TokenUsage(11, 2, 13))
        with patch("app.routes.ai_platform.suggest_topic_words", side_effect=error):
            response = self.client.post(
                "/api/generate/topic",
                json={"topic": "home", "lang": "nl", "count": 10},
            )

        self.assertEqual(response.status_code, 502)
        snapshot = self._snapshot()
        self.assertEqual(snapshot["failed_requests"], 1)
        self.assertEqual(snapshot["total_tokens"], 13)

    def test_invalid_input_does_not_increment_usage(self):
        response = self.client.post("/api/translate/word", json={"word": ""})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._snapshot()["total_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
