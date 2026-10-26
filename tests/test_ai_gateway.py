import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock, patch

from flask import Blueprint, Flask, session
from jinja2 import ChoiceLoader, DictLoader, FileSystemLoader

from config import Config
from app import ai_gateway as gateway, content_providers, content_service


class AiGatewayTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="parallellingvo-ai-")
        self.addCleanup(temp.cleanup)
        self.db = str(Path(temp.name) / "test.db")
        for key, value in {"DB_PATH": self.db, "SECRET_KEY": "test-key", "PAID_AI_ENABLED": True,
                           "CONTENT_PROVIDER_MODULE": "", "CONTENT_TRANSLATION_PROVIDER_MODULE": ""}.items():
            setting = patch.object(Config, key, value)
            setting.start(); self.addCleanup(setting.stop)
        self.app = Flask(__name__)
        self.app.secret_key = "test-session-key"
        self.app.jinja_loader = ChoiceLoader([
            DictLoader({"base.html": "<main>{% block content %}{% endblock %}</main>"}),
            FileSystemLoader(str(Path("app/templates").resolve())),
        ])
        web = Blueprint("web", __name__)
        web.add_url_rule("/admin/users", "admin_users_page", lambda: "users")
        gateway.register(web)
        self.app.register_blueprint(web)
        admin = patch("app.routes._is_admin_user_id", side_effect=lambda uid: uid == "admin")
        admin.start(); self.addCleanup(admin.stop)
        self.client = self.app.test_client()
        self.data = {"revision": 0, "enabled": True, "endpoint": "https://ai.example/v1/chat/completions",
                     "model": "model-one", "api_key": "secret-api-key", "timeout": 60, "tasks": {}}

    def login(self):
        with self.client.session_transaction() as state:
            state.update(is_auth=True, tg_user_id="admin")
        response = self.client.get("/api/admin/ai/settings")
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as state:
            return state["admin_csrf"]

    def response(self, result, **kwargs):
        return Mock(status_code=200, json=lambda: {
            "choices": [{"message": {"content": json.dumps(result)}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16}, **kwargs})

    def test_admin_session_csrf_and_secret_storage(self):
        self.assertEqual(self.client.get("/admin/ai").status_code, 401)
        self.assertEqual(self.client.post("/api/admin/ai/settings", json=self.data).status_code, 401)
        csrf = self.login()
        self.assertEqual(self.client.post("/api/admin/ai/settings", json=self.data).status_code, 403)
        with patch("app.ai_gateway.requests.post") as external:
            saved = self.client.post("/api/admin/ai/settings", json=self.data, headers={"X-CSRF-Token": csrf})
            external.assert_not_called()
        self.assertEqual(saved.status_code, 200)
        self.assertTrue(saved.json["settings"]["key_configured"])
        self.assertNotIn("secret-api-key", saved.text)
        page = self.client.get("/api/admin/ai/settings")
        self.assertEqual(page.status_code, 200)
        self.assertTrue(page.json["settings"]["key_configured"])
        self.assertNotIn("secret-api-key", page.text)
        self.assertNotIn("api_key", page.json["settings"])
        legacy = self.client.get("/admin/ai")
        self.assertEqual(legacy.status_code, 302, "the old UI moved to the main-site admin")
        self.assertTrue(legacy.headers["Location"].endswith("tab=ai"))
        with closing(sqlite3.connect(self.db)) as conn:
            row = conn.execute("SELECT config_json,encrypted_key FROM ai_gateway_settings").fetchone()
        self.assertNotIn("secret-api-key", " ".join(row))
        self.assertEqual(gateway.read_settings()["api_key"], "secret-api-key")
        with self.client.session_transaction() as state:
            state["tg_user_id"] = "ordinary-user"
        self.assertEqual(self.client.get("/admin/ai").status_code, 401)
        self.assertEqual(self.client.post("/api/admin/ai/settings", json=self.data, headers={"X-CSRF-Token": csrf}).status_code, 401)

    def test_save_validation_revision_and_key_retention(self):
        gateway.save_settings(self.data)
        with self.assertRaises(gateway.SettingsConflict):
            gateway.save_settings(self.data)
        update = {**self.data, "revision": 1, "model": "model-two", "api_key": ""}
        gateway.save_settings(update)
        self.assertEqual(gateway.read_settings()["api_key"], "secret-api-key")
        with self.assertRaisesRegex(ValueError, "новый ключ"):
            gateway.save_settings({**update, "revision": 2, "endpoint": "https://other.example/v1/chat/completions"})
        gateway.save_settings({**update, "revision": 2, "clear_key": True})
        self.assertEqual(gateway.read_settings()["api_key"], "")
        for invalid in ({"endpoint": "http://insecure/api"}, {"endpoint": "https://user:pass@host/api"},
                        {"endpoint": "https://host/api?api_key=secret"}, {"timeout": -1}, {"enabled": "true"}):
            with self.assertRaises(ValueError):
                gateway.save_settings({**update, "revision": 3, **invalid})

    def test_hot_model_switch_and_existing_content_reuse(self):
        gateway.save_settings(self.data)
        with patch("app.ai_gateway.requests.post", return_value=self.response({"text": "дом"})) as external:
            first = content_service.resolve_word("house", "en", ["en", "ru"], examples=False)
            self.assertEqual(first["ru"], "дом")
            self.assertEqual(first["provider_calls"], 1)
            self.assertEqual(first["usage"]["total_tokens"], 16)
            self.assertEqual(external.call_args.kwargs["json"]["model"], "model-one")
            self.assertNotIn("request_key", external.call_args.kwargs["json"]["messages"][1]["content"])
            gateway.save_settings({**self.data, "revision": 1, "model": "model-two", "api_key": ""})
            cached = content_service.resolve_word("house", "en", ["en", "ru"], examples=False)
            self.assertEqual(cached["provider_calls"], 0)
            self.assertEqual(external.call_count, 1)
            content_service.resolve_word("building", "en", ["en", "ru"], examples=False)
            self.assertEqual(external.call_count, 2)
            self.assertEqual(external.call_args.kwargs["json"]["model"], "model-two")
            self.assertFalse(external.call_args.kwargs["allow_redirects"])

    def test_task_models_prompts_examples_and_topics(self):
        task = {"model": "example-model", "prompt": "Use short sentences."}
        gateway.save_settings({**self.data, "tasks": {"generate_examples": task}})
        with patch("app.ai_gateway.requests.post", return_value=self.response({"ex_ru": "Мой **дом**."})) as external:
            result = content_providers.adapter("generate_examples")(
                languages=["ru"], words={"en": "house", "ru": "дом"}, examples={}, level="A1")
            self.assertEqual(result["ex_ru"], "Мой **дом**.")
            self.assertEqual(external.call_args.kwargs["json"]["model"], "example-model")
            self.assertIn("Use short sentences.", external.call_args.kwargs["json"]["messages"][0]["content"])
        with patch("app.ai_gateway.requests.post", return_value=self.response({"words": ["house", "room", "door"]})):
            result = content_providers.adapter("suggest_words")(topic="home", language="en", level="A1", count=2)
            self.assertEqual(result["words"], ["house", "room"])

    def test_off_switch_no_legacy_fallback_and_paid_gate(self):
        self.assertIsNone(content_providers.adapter("translate_word"))
        gateway.save_settings(self.data)
        with patch.object(Config, "PAID_AI_ENABLED", False), patch("app.ai_gateway.requests.post") as external:
            self.assertIsNone(content_providers.adapter("translate_word"))
            with self.assertRaisesRegex(RuntimeError, "paid_ai_disabled"):
                gateway.generate(gateway.read_settings(), "translate_word", {})
            external.assert_not_called()
        gateway.save_settings({**self.data, "revision": 1, "enabled": False})
        with patch.object(Config, "CONTENT_PROVIDER_MODULE", "module_that_must_not_load"):
            self.assertIsNone(content_providers.adapter("translate_word"))

    def test_legacy_production_bridge_preserves_old_provider_until_save(self):
        from types import SimpleNamespace
        from app.ai_platform import TokenUsage, AiPlatformError
        def translate_word(word, from_lang, level="A2", known_ru=None):
            return "legacy-word"
        def translate_language(source_word, source_sentence, source_lang_name, target_lang_name):
            return "legacy-language"
        def suggest_topic_words(topic, lang, level, count, existing_words):
            return "legacy-topic"
        module = SimpleNamespace(translate_word=translate_word, translate_language=translate_language,
                                 suggest_topic_words=suggest_topic_words, is_configured=lambda: True,
                                 TokenUsage=TokenUsage, AiPlatformError=AiPlatformError)
        gateway.install_legacy_bridge(module)
        self.assertTrue(module.is_configured())
        self.assertEqual(module.translate_word("house", "en"), "legacy-word")
        self.assertEqual(module.translate_language("house", "", "English", "Russian"), "legacy-language")
        gateway.save_settings(self.data)
        with patch("app.ai_gateway.requests.post", return_value=self.response({"text": "дом"})):
            result, usage = module.translate_language(source_word="house", source_sentence="",
                                                      source_lang_name="English", target_lang_name="Russian")
        self.assertEqual(result["word"], "дом")
        self.assertEqual(usage.total_tokens, 16)
        gateway.save_settings({**self.data, "revision": 1, "enabled": False})
        self.assertFalse(module.is_configured())

    def test_errors_do_not_cache_bad_content_or_expose_secrets(self):
        gateway.save_settings(self.data)
        with patch("app.ai_gateway.requests.post", return_value=Mock(status_code=302)):
            with self.assertRaisesRegex(RuntimeError, "HTTP 302"):
                content_service.resolve_word("house", "en", ["en", "ru"], examples=False)
        with patch("app.ai_gateway.requests.post", return_value=self.response({"text": []})):
            with self.assertRaisesRegex(RuntimeError, "формата"):
                content_service.resolve_word("house", "en", ["en", "ru"], examples=False)
        import requests
        with patch("app.ai_gateway.requests.post", side_effect=requests.Timeout("secret-api-key")):
            with self.assertRaises(RuntimeError) as error:
                content_service.resolve_word("house", "en", ["en", "ru"], examples=False)
            self.assertNotIn("secret-api-key", str(error.exception))
        with patch("app.ai_gateway.requests.post", return_value=self.response({"text": "дом"})) as external:
            result = content_service.resolve_word("house", "en", ["en", "ru"], examples=False)
            self.assertEqual(result["ru"], "дом")
            self.assertEqual(external.call_count, 1)


if __name__ == "__main__":
    unittest.main()
