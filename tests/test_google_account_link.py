import gc
import sqlite3
import tempfile
import unittest
from pathlib import Path

from flask import Flask, redirect

from config import Config
from app import google_auth


class _FakeGoogleClient:
    def __init__(self, userinfo):
        self.userinfo = userinfo

    def authorize_redirect(self, _redirect_uri):
        return redirect("/fake-google")

    def authorize_access_token(self):
        return {"userinfo": self.userinfo}


class _FakeOAuth:
    def __init__(self, userinfo):
        self.google = _FakeGoogleClient(userinfo)


class GoogleAccountLinkTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "google-link.db")
        self.original_db_path = Config.DB_PATH
        self.original_client_id = Config.GOOGLE_CLIENT_ID
        self.original_oauth = google_auth._oauth
        Config.DB_PATH = self.db_path
        Config.GOOGLE_CLIENT_ID = "test-client-id"
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    account_type TEXT NOT NULL DEFAULT 'standard',
                    auth_provider TEXT DEFAULT 'telegram',
                    google_id TEXT,
                    google_email TEXT
                );
                CREATE UNIQUE INDEX u_users_google_id
                    ON users(google_id) WHERE google_id IS NOT NULL;
                CREATE TABLE auth_identities (
                    provider TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    email TEXT,
                    PRIMARY KEY (provider, external_id)
                );
                CREATE TABLE words (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    lesson TEXT
                );
                CREATE TABLE user_subscriptions (
                    user_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'trial'
                );
                INSERT INTO users(user_id,username,first_name) VALUES
                    ('alice','alice','Alice'),('bob','bob','Bob');
                INSERT INTO auth_identities(provider,external_id,user_id) VALUES
                    ('telegram','alice','alice'),('telegram','bob','bob');
                INSERT INTO words(id,user_id,lesson) VALUES (1,'alice','Lesson 1');
                INSERT INTO user_subscriptions(user_id,status) VALUES ('alice','active');
                """
            )
        google_auth._oauth = _FakeOAuth({
            "sub": "google-alice",
            "email": "alice@example.com",
            "name": "Alice Example",
        })
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.app.register_blueprint(google_auth.google_bp)
        self.client = self.app.test_client()

    def tearDown(self):
        google_auth._oauth = self.original_oauth
        Config.DB_PATH = self.original_db_path
        Config.GOOGLE_CLIENT_ID = self.original_client_id
        self.client = None
        self.app = None
        gc.collect()
        self.temp_dir.cleanup()

    def _login_telegram(self, user_id="alice"):
        with self.client.session_transaction() as session:
            session["tg_user_id"] = user_id
            session["is_auth"] = True

    def test_link_flow_keeps_existing_telegram_user(self):
        self._login_telegram()
        started = self.client.get(
            "/auth/google",
            query_string={"mode": "link", "next": "/upload?tab=mcp"},
        )
        self.assertEqual(302, started.status_code)

        completed = self.client.get("/auth/google/callback")
        self.assertEqual(302, completed.status_code)
        self.assertEqual("/upload?tab=mcp&google_link=linked", completed.location)
        with self.client.session_transaction() as session:
            self.assertEqual("alice", session["tg_user_id"])
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT google_id,google_email,auth_provider FROM users WHERE user_id='alice'"
            ).fetchone()
        self.assertEqual(("google-alice", "alice@example.com", "telegram"), row)

    def test_google_account_cannot_be_linked_to_two_users(self):
        self.assertEqual(
            "linked",
            google_auth._link_google_user("bob", "google-alice", "bob@example.com"),
        )
        self.assertEqual(
            "conflict",
            google_auth._link_google_user("alice", "google-alice", "alice@example.com"),
        )

    def test_empty_google_profile_is_merged_into_existing_telegram_user(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                INSERT INTO users(
                    user_id,username,first_name,auth_provider,google_id,google_email
                ) VALUES (
                    'legacy-google-profile','google@example.com','Google','google',
                    'google-existing','google@example.com'
                );
                INSERT INTO auth_identities(provider,external_id,user_id,email)
                VALUES ('google','google-existing','legacy-google-profile','google@example.com');
                INSERT INTO user_subscriptions(user_id,status)
                VALUES ('legacy-google-profile','trial');
            """)

        self.assertEqual(
            "linked",
            google_auth._link_google_user(
                "alice", "google-existing", "google@example.com"
            ),
        )
        self.assertEqual(
            "alice",
            google_auth._find_or_create_google_user(
                "google-existing", "google@example.com", "Alice Example"
            ),
        )
        with sqlite3.connect(self.db_path) as conn:
            identity_owner = conn.execute(
                "SELECT user_id FROM auth_identities "
                "WHERE provider='google' AND external_id='google-existing'"
            ).fetchone()[0]
            word_count = conn.execute(
                "SELECT COUNT(*) FROM words WHERE user_id='alice'"
            ).fetchone()[0]
            duplicate = conn.execute(
                "SELECT 1 FROM users WHERE user_id='legacy-google-profile'"
            ).fetchone()
            subscription = conn.execute(
                "SELECT status FROM user_subscriptions WHERE user_id='alice'"
            ).fetchone()[0]

        self.assertEqual("alice", identity_owner)
        self.assertEqual(1, word_count)
        self.assertIsNone(duplicate)
        self.assertEqual("active", subscription)

    def test_link_requires_authenticated_session(self):
        response = self.client.get("/auth/google", query_string={"mode": "link"})
        self.assertEqual(302, response.status_code)
        self.assertEqual("/upload?error=google_link_auth_required", response.location)

    def test_android_config_exposes_only_public_client_id(self):
        response = self.client.get("/api/auth/google/config")
        self.assertEqual(200, response.status_code)
        self.assertEqual({"ok": True, "client_id": "test-client-id"}, response.get_json())


if __name__ == "__main__":
    unittest.main()
