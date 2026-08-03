import sqlite3
import tempfile
import unittest
import gc
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from app.audio_gen import ensure_audio_for_ids
from app.routes import web
from app.tts_usage import (
    TtsUsageLimitExceeded,
    get_tts_usage_snapshot,
    record_tts_request,
    reserve_tts_characters,
    reset_tts_usage,
    set_tts_character_limit,
    usage_period,
)
from app.translation_usage import record_translation_usage
from config import Config


class TtsUsageCounterTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()

    def test_month_changes_at_amsterdam_midnight(self):
        before = usage_period(
            now=datetime(2026, 7, 31, 21, 59, 59, tzinfo=timezone.utc),
            timezone_name="Europe/Amsterdam",
        )
        after = usage_period(
            now=datetime(2026, 7, 31, 22, 0, 0, tzinfo=timezone.utc),
            timezone_name="Europe/Amsterdam",
        )
        self.assertEqual(before["key"], "2026-07")
        self.assertEqual(after["key"], "2026-08")

    def test_snapshot_has_global_and_per_user_counts(self):
        now = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)
        record_tts_request(self.conn, "101", successful=True, now=now)
        record_tts_request(self.conn, "101", successful=False, now=now)
        record_tts_request(self.conn, "202", successful=True, now=now)

        snapshot = get_tts_usage_snapshot(self.conn, now=now)

        self.assertEqual(snapshot["successful_requests"], 2)
        self.assertEqual(snapshot["failed_requests"], 1)
        self.assertEqual(snapshot["total_requests"], 3)
        self.assertEqual(snapshot["by_user"]["101"]["total_requests"], 2)
        self.assertEqual(snapshot["by_user"]["202"]["successful_requests"], 1)

    def test_manual_reset_can_target_one_user_or_everyone(self):
        now = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)
        record_tts_request(self.conn, "101", successful=True, now=now)
        record_tts_request(self.conn, "202", successful=False, now=now)

        self.assertEqual(reset_tts_usage(self.conn, user_id="101", now=now), 1)
        snapshot = get_tts_usage_snapshot(self.conn, now=now)
        self.assertNotIn("101", snapshot["by_user"])
        self.assertEqual(snapshot["by_user"]["202"]["failed_requests"], 1)

        self.assertEqual(reset_tts_usage(self.conn, now=now), 1)
        self.assertEqual(get_tts_usage_snapshot(self.conn, now=now)["total_requests"], 0)

    def test_new_month_starts_at_zero_and_keeps_history(self):
        july = datetime(2026, 7, 31, 20, 0, tzinfo=timezone.utc)
        august = datetime(2026, 7, 31, 22, 0, tzinfo=timezone.utc)
        record_tts_request(self.conn, "101", successful=True, now=july)

        self.assertEqual(get_tts_usage_snapshot(self.conn, now=august)["total_requests"], 0)
        periods = self.conn.execute(
            "SELECT period_key FROM google_tts_usage_monthly ORDER BY period_key"
        ).fetchall()
        self.assertEqual([row["period_key"] for row in periods], ["2026-07"])

    def test_default_global_limit_is_500000_characters(self):
        snapshot = get_tts_usage_snapshot(self.conn)
        self.assertEqual(snapshot["character_limit"], 500_000)
        self.assertEqual(snapshot["characters_remaining"], 500_000)

    def test_global_character_limit_blocks_before_external_call(self):
        now = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)
        reserve_tts_characters(self.conn, "101", characters=499_998, now=now)

        with self.assertRaises(TtsUsageLimitExceeded) as raised:
            reserve_tts_characters(self.conn, "202", characters=3, now=now)

        self.assertEqual(raised.exception.scope, "global")
        snapshot = get_tts_usage_snapshot(self.conn, now=now)
        self.assertEqual(snapshot["characters"], 499_998)
        self.assertEqual(snapshot["blocked_requests"], 1)
        self.assertEqual(snapshot["characters_remaining"], 2)

    def test_user_limit_is_unlimited_until_admin_sets_one(self):
        now = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)
        reserve_tts_characters(self.conn, "101", characters=20, now=now)
        self.assertIsNone(
            get_tts_usage_snapshot(self.conn, now=now)["by_user"]["101"]["character_limit"]
        )

        set_tts_character_limit(
            self.conn,
            user_id="101",
            monthly_character_limit=25,
        )
        with self.assertRaises(TtsUsageLimitExceeded) as raised:
            reserve_tts_characters(self.conn, "101", characters=6, now=now)
        self.assertEqual(raised.exception.scope, "user")

    def test_resetting_request_statistics_does_not_restore_budget(self):
        now = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)
        reserve_tts_characters(self.conn, "101", characters=5, now=now)
        record_tts_request(self.conn, "101", successful=True, now=now)
        reset_tts_usage(self.conn, user_id="101", now=now)

        snapshot = get_tts_usage_snapshot(self.conn, now=now)
        self.assertEqual(snapshot["total_requests"], 0)
        self.assertEqual(snapshot["characters"], 5)


class AudioGenerationUsageTests(unittest.TestCase):
    def _create_database(self, path: Path) -> None:
        with closing(sqlite3.connect(path)) as conn:
            conn.execute(
                """
                CREATE TABLE words (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    lesson TEXT,
                    en TEXT,
                    ex_en TEXT,
                    audio_en TEXT,
                    updated_at INTEGER
                )
                """
            )
            conn.execute(
                """
                INSERT INTO words (id, user_id, status, lesson, en, audio_en)
                VALUES (1, '101', 'user', 'Lesson 1', 'hello', '')
                """
            )
            conn.commit()

    def _snapshot(self, path: Path) -> dict:
        with closing(sqlite3.connect(path)) as conn:
            conn.row_factory = sqlite3.Row
            return get_tts_usage_snapshot(conn)

    def test_successful_google_call_is_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "words.db"
            audio_root = root / "audio"
            self._create_database(db_path)

            def fake_tts(_text: str, _lang: str, out_path: Path) -> None:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(b"a" * 700)

            with patch("app.audio_gen.AUDIO_ROOT", audio_root), \
                    patch("app.audio_gen._tts_make", side_effect=fake_tts), \
                    patch("app.audio_gen._maximize_loudness"):
                result = ensure_audio_for_ids(str(db_path), [1], ["en"], user_id="101")

            self.assertEqual(result["generated"], 1)
            snapshot = self._snapshot(db_path)
            self.assertEqual(snapshot["by_user"]["101"]["successful_requests"], 1)
            self.assertEqual(snapshot["by_user"]["101"]["characters"], 5)

    def test_failed_google_call_is_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "words.db"
            self._create_database(db_path)

            with patch("app.audio_gen.AUDIO_ROOT", root / "audio"), \
                    patch("app.audio_gen._tts_make", side_effect=RuntimeError("Google unavailable")):
                result = ensure_audio_for_ids(str(db_path), [1], ["en"], user_id="101")

            self.assertEqual(result["generated"], 0)
            self.assertEqual(self._snapshot(db_path)["by_user"]["101"]["failed_requests"], 1)

    def test_reused_audio_does_not_increment_google_counter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "words.db"
            audio_path = root / "audio" / "en" / "Lesson 1" / "hello_en.mp3"
            audio_path.parent.mkdir(parents=True)
            audio_path.write_bytes(b"a" * 700)
            self._create_database(db_path)

            with patch("app.audio_gen.AUDIO_ROOT", root / "audio"), \
                    patch("app.audio_gen._tts_make") as tts_make:
                result = ensure_audio_for_ids(str(db_path), [1], ["en"], user_id="101")

            self.assertEqual(result["skipped"], 1)
            tts_make.assert_not_called()
            self.assertEqual(self._snapshot(db_path)["total_requests"], 0)

    def test_monthly_limit_blocks_generation_without_calling_gtts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "words.db"
            self._create_database(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                set_tts_character_limit(
                    conn,
                    monthly_character_limit=4,
                )
                conn.commit()

            with patch("app.audio_gen.AUDIO_ROOT", root / "audio"), \
                    patch("app.audio_gen._tts_make") as tts_make:
                result = ensure_audio_for_ids(str(db_path), [1], ["en"], user_id="101")

            self.assertFalse(result["ok"])
            self.assertTrue(result["limit_reached"])
            self.assertEqual(result["blocked"], 1)
            tts_make.assert_not_called()
            snapshot = self._snapshot(db_path)
            self.assertEqual(snapshot["characters"], 0)
            self.assertEqual(snapshot["blocked_requests"], 1)


class AdminTtsUsageApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "words.db"
        self.old_db_path = Config.DB_PATH
        self.old_admin_ids = Config.ADMIN_IDS
        self.old_platform_admin_token = Config.AI_PLATFORM_ADMIN_TOKEN
        Config.DB_PATH = str(self.db_path)
        Config.ADMIN_IDS = (999,)
        Config.AI_PLATFORM_ADMIN_TOKEN = "test-platform-secret"

        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute(
                """
                CREATE TABLE users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    account_type TEXT DEFAULT 'standard',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                "INSERT INTO users (user_id, username, first_name) VALUES ('101', 'test', 'Test')"
            )
            conn.execute(
                """
                CREATE TABLE words (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    status TEXT,
                    lesson TEXT,
                    number INTEGER,
                    difficult INTEGER DEFAULT 0,
                    updated_at INTEGER
                )
                """
            )
            record_tts_request(conn, "101", successful=True)
            record_tts_request(conn, "101", successful=False)
            record_translation_usage(
                conn,
                "101",
                successful=True,
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            )
            conn.commit()

        project_root = Path(__file__).resolve().parents[1]
        app = Flask(
            __name__,
            template_folder=str(project_root / "app" / "templates"),
            static_folder=str(project_root / "app" / "static"),
        )
        app.secret_key = "test"
        app.register_blueprint(web)
        app.context_processor(lambda: {
            "t": lambda key, **kwargs: key,
            "current_ui_language": "ru",
            "i18n_catalog": {},
        })
        app.testing = True
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["is_auth"] = True
            session["tg_user_id"] = "999"

    def tearDown(self):
        Config.DB_PATH = self.old_db_path
        Config.ADMIN_IDS = self.old_admin_ids
        Config.AI_PLATFORM_ADMIN_TOKEN = self.old_platform_admin_token
        self.client = None
        gc.collect()
        self.tmp.cleanup()

    def test_admin_users_returns_global_and_user_tts_counts(self):
        response = self.client.get("/api/admin/users")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tts_usage"]["total_requests"], 2)
        self.assertEqual(payload["tts_usage"]["character_limit"], 500_000)
        self.assertEqual(payload["translation_usage"]["total_tokens"], 15)
        user = next(item for item in payload["users"] if item["user_id"] == "101")
        self.assertEqual(user["tts_successful_requests"], 1)
        self.assertEqual(user["tts_failed_requests"], 1)
        self.assertIsNone(user["tts_character_limit"])
        self.assertEqual(user["translation_total_tokens"], 15)
        self.assertEqual(user["translation_successful_requests"], 1)

    def test_admin_can_reset_one_user(self):
        response = self.client.post(
            "/api/admin/tts_usage/reset",
            json={"user_id": "101"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["tts_usage"]["total_requests"], 0)

    def test_non_admin_cannot_reset_tts_usage(self):
        with self.client.session_transaction() as session:
            session["tg_user_id"] = "101"
        response = self.client.post("/api/admin/tts_usage/reset", json={})
        self.assertEqual(response.status_code, 401)

    def test_ai_platform_token_can_read_usage_and_change_limits(self):
        with self.client.session_transaction() as session:
            session.clear()
        headers = {"Authorization": "Bearer test-platform-secret"}

        usage = self.client.get("/api/admin/users", headers=headers)
        changed = self.client.post(
            "/api/admin/tts_usage/limit",
            json={"user_id": "101", "monthly_character_limit": 2500},
            headers=headers,
        )

        self.assertEqual(usage.status_code, 200)
        self.assertEqual(usage.get_json()["translation_usage"]["total_tokens"], 15)
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.get_json()["monthly_character_limit"], 2500)

    def test_ai_platform_token_must_be_configured_and_exact(self):
        with self.client.session_transaction() as session:
            session.clear()
        invalid = self.client.get(
            "/api/admin/users",
            headers={"Authorization": "Bearer wrong-secret"},
        )
        Config.AI_PLATFORM_ADMIN_TOKEN = ""
        empty_config = self.client.get(
            "/api/admin/users",
            headers={"Authorization": "Bearer test-platform-secret"},
        )

        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(empty_config.status_code, 401)

    def test_ai_platform_token_does_not_grant_other_admin_actions(self):
        with self.client.session_transaction() as session:
            session.clear()
        response = self.client.post(
            "/api/admin/grant_access",
            json={"user_id": "101"},
            headers={"Authorization": "Bearer test-platform-secret"},
        )

        self.assertEqual(response.status_code, 401)

    def test_admin_can_reset_translation_usage(self):
        response = self.client.post(
            "/api/admin/translation_usage/reset",
            json={"user_id": "101"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["translation_usage"]["total_tokens"], 0)

    def test_admin_can_set_global_and_user_character_limits(self):
        response = self.client.post(
            "/api/admin/tts_usage/limit",
            json={"monthly_character_limit": 500_000},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["tts_usage"]["character_limit"], 500_000)

        response = self.client.post(
            "/api/admin/tts_usage/limit",
            json={"user_id": "101", "monthly_character_limit": 1_000},
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/admin/users")
        user = next(item for item in response.get_json()["users"] if item["user_id"] == "101")
        self.assertEqual(user["tts_character_limit"], 1_000)

        response = self.client.post(
            "/api/admin/tts_usage/limit",
            json={"user_id": "101", "monthly_character_limit": None},
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_page_has_general_subscription_and_cost_tabs(self):
        response = self.client.get("/admin/users")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('data-admin-tab="general"', html)
        self.assertIn('data-admin-tab="subscriptions"', html)
        self.assertIn('data-admin-tab="costs"', html)
        self.assertIn('value="500000"', html)


if __name__ == "__main__":
    unittest.main()
