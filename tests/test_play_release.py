"""Release-critical paths, isolated temporary SQLite and mocked Google transport."""
import copy
import gc
import base64
import json
import os
import sqlite3
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from config import Config
from app import routes, google_play as play, account_privacy as privacy
from app.auth_links import create_auth_token, verify_auth_token


class PlayReleaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = patch.multiple(Config, DB_PATH=str(Path(self.temp.name) / "test.db"),
                                     SECRET_KEY="isolated-test-secret", ALLOW_LEGACY_UID_AUTH=False)
        self.config.start()
        self.env = patch.dict(os.environ, {"GOOGLE_PLAY_PRODUCTS_JSON": json.dumps({"test.product": "premium"}),
                                           "PRIVACY_POLICY_APPROVED": "0"})
        self.env.start()
        with sqlite3.connect(Config.DB_PATH) as c:
            c.execute("CREATE TABLE users(user_id TEXT PRIMARY KEY,username TEXT,first_name TEXT,last_name TEXT,is_active INTEGER DEFAULT 1,account_type TEXT DEFAULT 'standard',created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
            c.executemany("INSERT INTO users(user_id) VALUES(?)", [("alice",), ("bob",)])
            c.execute("CREATE TABLE words(id INTEGER PRIMARY KEY,user_id TEXT,lesson TEXT,number TEXT)")
        routes._ensure_family_schema()
        routes._ensure_subscription_schema()
        self.app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / "app/templates"))
        self.app.config.update(TESTING=True, SECRET_KEY=Config.SECRET_KEY)
        self.app.register_blueprint(routes.web)
        self.client = self.app.test_client()
        self.headers = {"Authorization": "Bearer " + create_auth_token("alice")}
        self.expiry = int(time.time() * 1000) + 86400000
        self.payload = {
            "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
            "acknowledgementState": "ACKNOWLEDGEMENT_STATE_PENDING",
            "externalAccountIdentifiers": {"obfuscatedExternalAccountId": play.account_id("alice")},
            "lineItems": [{"productId": "test.product", "expiryTime": datetime.fromtimestamp(
                self.expiry / 1000, timezone.utc).isoformat()}],
        }

    def tearDown(self):
        self.env.stop()
        self.config.stop()
        self.client = None
        self.app = None
        gc.collect()
        self.temp.cleanup()

    def transport(self, method, path, body=None):
        return copy.deepcopy(self.payload) if method == "GET" else {}

    def state(self):
        with sqlite3.connect(Config.DB_PATH) as c:
            return c.execute("SELECT status,current_period_ends_at,provider,plan FROM user_subscriptions WHERE user_id='alice'").fetchone()

    def test_verified_purchase_is_bound_acknowledged_encrypted_and_idempotent(self):
        with patch.object(play, "_request", side_effect=self.transport) as remote:
            result = play.verify("alice", "secret-purchase", "test.product")
            self.assertTrue(result["active"] and result["acknowledged"])
            self.assertEqual(remote.call_args_list[0].args[0], "GET")
            self.assertEqual(remote.call_args_list[1].args[0], "POST")
            self.payload["acknowledgementState"] = "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED"
            play.verify("alice", "secret-purchase", "test.product")
            self.assertEqual(remote.call_count, 3)
        self.assertEqual(self.state(), ("active", self.expiry, "google_play", "premium"))
        with sqlite3.connect(Config.DB_PATH) as c:
            self.assertEqual(c.execute("SELECT count(*) FROM google_play_purchases").fetchone()[0], 1)
            self.assertNotIn("secret-purchase", c.execute("SELECT token_cipher FROM google_play_purchases").fetchone()[0])

    def test_stolen_token_or_wrong_package_cannot_grant_access(self):
        with patch.object(play, "_request", side_effect=self.transport):
            with self.assertRaises(play.PlayError):
                play.verify("bob", "stolen", "test.product")
            with self.assertRaises(play.PlayError):
                play.verify("alice", "stolen", "test.product", "other.package")
        self.assertIsNone(self.state())

    def test_unbound_legacy_purchase_is_not_claimed_by_first_requester(self):
        self.payload.pop("externalAccountIdentifiers")
        with patch.object(play, "_request", side_effect=self.transport):
            with self.assertRaises(play.PlayError):
                play.verify("alice", "unbound", "test.product")
        self.assertIsNone(self.state())

    def test_acknowledgement_failure_does_not_activate_or_lose_retry(self):
        def failed(method, path, body=None):
            if method == "POST":
                raise play.PlayError("google_play_temporarily_unavailable")
            return copy.deepcopy(self.payload)
        with patch.object(play, "_request", side_effect=failed):
            with self.assertRaises(play.PlayError):
                play.verify("alice", "retry", "test.product")
        self.assertIsNone(self.state())
        with patch.object(play, "_request", side_effect=self.transport):
            self.assertTrue(play.verify("alice", "retry", "test.product")["active"])

    def test_pending_does_not_grant_or_acknowledge(self):
        self.payload["subscriptionState"] = "SUBSCRIPTION_STATE_PENDING"
        with patch.object(play, "_request", side_effect=self.transport) as remote:
            result = play.verify("alice", "pending", "test.product")
            self.assertFalse(result["active"])
            self.assertEqual(remote.call_count, 1)
        self.assertIsNone(self.state())

    def test_cancelled_keeps_paid_period_and_hold_revokes_access(self):
        self.payload["subscriptionState"] = "SUBSCRIPTION_STATE_CANCELED"
        with patch.object(play, "_request", side_effect=self.transport):
            self.assertTrue(play.verify("alice", "paid", "test.product")["active"])
            self.payload["subscriptionState"] = "SUBSCRIPTION_STATE_ON_HOLD"
            self.assertFalse(play.verify("alice", "paid", "test.product")["active"])
        self.assertEqual(self.state()[0], "expired")

    def test_upgrade_supersedes_old_purchase(self):
        with patch.object(play, "_request", side_effect=self.transport):
            play.verify("alice", "old", "test.product")
            self.payload["linkedPurchaseToken"] = "old"
            play.verify("alice", "new", "test.product")
            with self.assertRaises(play.PlayError) as error:
                play.verify("alice", "old", "test.product")
            self.assertEqual(error.exception.code, "purchase_replaced")

    def test_manual_access_is_preserved(self):
        with sqlite3.connect(Config.DB_PATH) as c:
            c.execute("INSERT INTO user_subscriptions(user_id,status,trial_started_at,trial_ends_at,current_period_ends_at,provider,updated_at,plan) VALUES('alice','active',0,0,?,'manual',0,'family')", (self.expiry,))
        with patch.object(play, "_request", side_effect=self.transport):
            with self.assertRaises(play.PlayError):
                play.verify("alice", "paid", "test.product")
        self.assertEqual(self.state()[2:], ("manual", "family"))

    def test_api_requires_bearer_and_rejects_invalid_json(self):
        with patch.object(play, "_request") as remote:
            self.assertEqual(self.client.post("/api/subscription/verify_purchase", headers={"X-User-Id": "alice"}, json={}).status_code, 401)
            self.assertEqual(self.client.post("/api/subscription/verify_purchase", headers=self.headers, json=[]).status_code, 400)
            remote.assert_not_called()

    def test_api_returns_verified_server_entitlement(self):
        with patch.object(play, "_request", side_effect=self.transport):
            response = self.client.post("/api/subscription/verify_purchase", headers=self.headers,
                json={"purchase_token": "paid", "product_id": "test.product", "package_name": play.PACKAGE})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["verified"] and response.json["subscription"]["paid_access"])

    def test_delete_requires_confirmation_and_revokes_old_credentials(self):
        token = self.headers["Authorization"][7:]
        with patch.object(play, "_request", side_effect=self.transport):
            play.verify("alice", "purchase", "test.product")
        with sqlite3.connect(Config.DB_PATH) as c:
            c.execute("INSERT INTO words VALUES(1,'alice','personal','1')")
            c.execute("INSERT INTO words VALUES(2,'bob','keep','1')")
            c.execute("INSERT INTO parent_child_links(parent_user_id,child_user_id) VALUES('alice','bob')")
        self.assertEqual(self.client.post("/api/account/delete", headers=self.headers, json={"confirm": "DELETE"}).status_code, 400)
        proof = self.client.get("/api/account/deletion-challenge", headers=self.headers).json["challenge"]
        response = self.client.post("/api/account/delete", headers=self.headers,
                                    json={"confirm": "DELETE", "challenge": proof, "user_id": "bob"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(verify_auth_token(token), "")
        with sqlite3.connect(Config.DB_PATH) as c:
            self.assertEqual(c.execute("SELECT user_id FROM users").fetchall(), [("bob",)])
            self.assertEqual(c.execute("SELECT user_id FROM words").fetchall(), [("bob",)])
            self.assertEqual(c.execute("SELECT user_id,token_cipher FROM google_play_purchases").fetchone(), (None, ""))
            self.assertEqual(c.execute("SELECT count(*) FROM parent_child_links").fetchone()[0], 0)
            c.execute("INSERT INTO users(user_id) VALUES('alice')")
        self.assertEqual(verify_auth_token(token), "", "old token stays invalid after re-registration")
        self.assertEqual(verify_auth_token(create_auth_token("alice")), "alice")
        with patch.object(play, "_request", side_effect=self.transport):
            with self.assertRaises(play.PlayError):
                play.verify("alice", "purchase", "test.product")

    def test_web_csrf_and_stale_sessions(self):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session["is_auth"] = True
            session["tg_user_id"] = "alice"
        proof = client.get("/api/account/deletion-challenge").json["challenge"]
        other = self.app.test_client()
        with other.session_transaction() as session:
            session["is_auth"] = True
            session["tg_user_id"] = "alice"
        self.assertEqual(other.post("/api/account/delete", json={"confirm": "DELETE", "challenge": proof}).status_code, 400)
        privacy.erase("alice")
        self.assertEqual(client.get("/api/account/deletion-challenge").status_code, 401)

    def test_draft_privacy_not_public_and_delete_page_needs_no_app(self):
        self.app.testing = False
        self.assertEqual(self.client.get("/privacy").status_code, 404)
        response = self.client.get("/account/delete")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sign in with email", response.data)
        self.app.testing = True
        self.assertIn(b"DRAFT", self.client.get("/privacy").data)

    def test_replacement_prevents_later_claim_of_unseen_old_token(self):
        self.payload["linkedPurchaseToken"] = "unseen-old"
        with patch.object(play, "_request", side_effect=self.transport):
            play.verify("alice", "replacement", "test.product")
            with self.assertRaises(play.PlayError) as error:
                play.verify("alice", "unseen-old", "test.product")
            self.assertEqual(error.exception.code, "purchase_replaced")

    def test_expired_purchase_and_google_outage_never_grant_access(self):
        self.payload["lineItems"][0]["expiryTime"] = "2020-01-01T00:00:00Z"
        with patch.object(play, "_request", side_effect=self.transport):
            self.assertFalse(play.verify("alice", "expired", "test.product")["active"])
        self.assertIsNone(self.state())
        with patch.object(play, "_request", side_effect=play.PlayError("unavailable")):
            response = self.client.post("/api/subscription/verify_purchase", headers=self.headers,
                json={"purchase_token": "network", "product_id": "test.product", "package_name": play.PACKAGE})
        self.assertEqual(response.status_code, 503)
        self.assertIsNone(self.state())

    def test_restore_missing_token_cannot_revoke_another_verified_purchase(self):
        with patch.object(play, "_request", side_effect=self.transport):
            play.verify("alice", "live", "test.product")
            self.payload["subscriptionState"] = "SUBSCRIPTION_STATE_EXPIRED"
            play.verify("alice", "expired-other", "test.product")
        self.assertEqual(self.state()[0], "active")

    def test_purchases_disabled_until_owner_enables_catalog(self):
        with patch.dict(os.environ, {"GOOGLE_PLAY_PURCHASES_ENABLED": "0"}):
            self.assertEqual(self.client.get("/api/subscription/google-play-config", headers=self.headers).json["product_ids"], [])
        with patch.dict(os.environ, {"GOOGLE_PLAY_PURCHASES_ENABLED": "1"}):
            self.assertEqual(self.client.get("/api/subscription/google-play-config", headers=self.headers).json["product_ids"], ["test.product"])

    def test_rtdn_requires_configured_google_oidc_identity(self):
        endpoint = "/api/subscription/google-play-notifications"
        with patch.dict(os.environ, {"GOOGLE_PLAY_RTDN_AUDIENCE": "", "GOOGLE_PLAY_RTDN_SERVICE_ACCOUNT": ""}):
            self.assertEqual(self.client.post(endpoint, json={}).status_code, 503)
        env = {"GOOGLE_PLAY_RTDN_AUDIENCE": "https://test.invalid/rtdn", "GOOGLE_PLAY_RTDN_SERVICE_ACCOUNT": "push@test.invalid"}
        payload = {"message": {"data": base64.b64encode(json.dumps({"packageName": play.PACKAGE,
            "testNotification": {}}).encode()).decode()}}
        with patch.dict(os.environ, env), patch("google.oauth2.id_token.verify_oauth2_token") as oidc:
            self.assertEqual(self.client.post(endpoint, json=payload).status_code, 401)
            oidc.return_value = {"email": "wrong@test.invalid", "email_verified": True}
            self.assertEqual(self.client.post(endpoint, headers={"Authorization": "Bearer fake"}, json=payload).status_code, 401)
            oidc.return_value = {"email": env["GOOGLE_PLAY_RTDN_SERVICE_ACCOUNT"], "email_verified": True}
            self.assertEqual(self.client.post(endpoint, headers={"Authorization": "Bearer fake"}, json=payload).status_code, 200)

    def test_delete_erases_email_reset_links_mcp_and_consent(self):
        with sqlite3.connect(Config.DB_PATH) as c:
            c.execute("CREATE TABLE email_auth_credentials(user_id TEXT,email TEXT,version TEXT)")
            c.execute("INSERT INTO email_auth_credentials VALUES('alice','alice@test.invalid','one')")
            c.execute("CREATE TABLE email_auth_links(email TEXT,token_hash TEXT)")
            c.execute("INSERT INTO email_auth_links VALUES('alice@test.invalid','reset')")
            c.execute("CREATE TABLE mcp_access_grants(user_id TEXT,token_hash TEXT)")
            c.execute("INSERT INTO mcp_access_grants VALUES('alice','mcp-token')")
            c.execute("CREATE TABLE ad_consent(user_id TEXT,choice TEXT)")
            c.execute("INSERT INTO ad_consent VALUES('alice','granted')")
            c.execute("CREATE TABLE mcp_audit_log(user_hash TEXT)")
            c.execute("INSERT INTO mcp_audit_log VALUES(?)", (play.token_hash("alice")[:16],))
        privacy.erase("alice")
        with sqlite3.connect(Config.DB_PATH) as c:
            for table in ("email_auth_credentials", "email_auth_links", "mcp_access_grants", "ad_consent", "mcp_audit_log"):
                self.assertEqual(c.execute(f"SELECT count(*) FROM {table}").fetchone()[0], 0)

    def test_slow_google_response_does_not_lock_db_or_overwrite_newer_revocation(self):
        self.payload["acknowledgementState"] = "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED"
        with patch.object(play, "_request", side_effect=self.transport):
            play.verify("alice", "race", "test.product")

        def newer_revocation(method, path, body=None):
            # Another verification commits while this network request is in flight.
            # This connection would fail if verify held the global write lock.
            with sqlite3.connect(Config.DB_PATH, timeout=1) as c:
                c.execute("UPDATE google_play_purchases SET state='SUBSCRIPTION_STATE_ON_HOLD',checked_at_ns=? WHERE token_hash=?",
                          (time.time_ns(), play.token_hash("race")))
                c.execute("UPDATE user_subscriptions SET status='expired' WHERE user_id='alice'")
            return copy.deepcopy(self.payload)

        with patch.object(play, "_request", side_effect=newer_revocation):
            with self.assertRaises(play.PlayError) as error:
                play.verify("alice", "race", "test.product")
        self.assertEqual(error.exception.code, "purchase_verification_raced")
        self.assertEqual(self.state()[0], "expired")


if __name__ == "__main__":
    unittest.main()
