import gc
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from flask import Flask, redirect

from config import Config
from app import google_auth
from app.auth_links import create_auth_token


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
            "email_verified": True,
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

    def test_native_google_link_requires_owner_and_preserves_existing_account(self):
        headers = {'Authorization':'Bearer '+create_auth_token('alice')}
        self.assertEqual(401, self.client.post('/api/auth/google/link', json={'id_token':'test'}).status_code)
        with patch('google.oauth2.id_token.verify_oauth2_token', return_value={
                'sub':'native-google', 'email':'alice@example.com', 'email_verified':True}):
            response = self.client.post('/api/auth/google/link', json={'id_token':'test'}, headers=headers)
        self.assertEqual(200, response.status_code, response.json)
        with sqlite3.connect(self.db_path) as c:
            self.assertEqual('native-google', c.execute("SELECT google_id FROM users WHERE user_id='alice'").fetchone()[0])
            self.assertEqual(1, c.execute("SELECT COUNT(*) FROM words WHERE user_id='alice'").fetchone()[0])
        with patch('google.oauth2.id_token.verify_oauth2_token', return_value={
                'sub':'native-google', 'email':'alice@example.com', 'email_verified':True}):
            response = self.client.post('/api/auth/google/link', json={'id_token':'test'},
                headers={'Authorization':'Bearer '+create_auth_token('bob')})
        self.assertEqual(409, response.status_code)

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

    def test_unverified_google_email_is_not_saved_as_verified_identity(self):
        google_auth._oauth.google.userinfo["email_verified"] = False
        self._login_telegram()
        self.client.get("/auth/google", query_string={"mode": "link"})
        response = self.client.get("/auth/google/callback")
        self.assertEqual(response.status_code, 302)
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(conn.execute("SELECT google_email FROM users WHERE user_id='alice'").fetchone()[0], "")
            self.assertEqual(conn.execute("SELECT email FROM auth_identities WHERE provider='google' AND user_id='alice'").fetchone()[0], "")

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

    def test_android_google_login_returns_session_for_existing_identity(self):
        from app.auth_links import verify_auth_token
        self.assertEqual("linked", google_auth._link_google_user(
            "alice", "google-alice", "alice@example.com"))
        with patch("google.oauth2.id_token.verify_oauth2_token",
                   return_value=google_auth._oauth.google.userinfo) as verify:
            response = self.client.post("/api/auth/google/verify", json={"id_token": "test-id-token"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["user_id"], "alice")
        self.assertTrue(response.json["ok"])
        self.assertEqual(verify_auth_token(response.json["token"]), "alice")
        self.assertEqual(verify.call_args.args[2], "test-client-id")
        self.assertNotIn("Location", response.headers)

    def test_android_google_rejects_invalid_token(self):
        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=ValueError("invalid")):
            response = self.client.post("/api/auth/google/verify", json={"id_token": "invalid"})
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("token", response.json)


if __name__ == "__main__":
    unittest.main()
