import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

from config import Config
from app.family_invites import invitation_payload, preview_invitation, accept_invitation
from app.family_pairing import create_pairing_code, create_invite_code, link_parent_with_pairing_code
from tests import test_family_accounts as family_test_fixtures


class UniversalFamilyTest(unittest.TestCase):
    def setUp(self):
        self.fixture = family_test_fixtures.FamilyAccountsTest()
        self.fixture.setUp()
        self.original_base = Config.APP_BASE_URL
        Config.APP_BASE_URL = "https://app.parallellingvo.app"
        for uid, role in [("parent", "standard"), ("other-parent", "standard"),
                          ("g_child", "child"), ("g_other", "child")]:
            self.fixture.add_user(uid, role)

    def tearDown(self):
        Config.APP_BASE_URL = self.original_base
        self.fixture.tearDown()

    def test_google_child_accepts_parent_short_code_without_telegram(self):
        with patch("app.routes._telegram_bot_username", side_effect=AssertionError("Telegram is not required")):
            response = self.fixture.request("GET", "/api/family/invite-code", "parent")
        payload = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertTrue(payload["invite_url"].startswith(Config.APP_BASE_URL + "/family/connect?"))
        short = payload["short_code"]
        code = short[:5].lower() + "-" + short[5:].lower()
        preview = self.fixture.request("POST", "/api/family/invitation/preview", "g_child", json={"code": code})
        self.assertEqual(200, preview.status_code)
        with sqlite3.connect(Config.DB_PATH) as conn:
            self.assertEqual(0, conn.execute("SELECT COUNT(*) FROM parent_child_links").fetchone()[0])
        accepted = self.fixture.request("POST", "/api/family/invitation/accept", "g_child", json=preview.get_json())
        self.assertEqual(200, accepted.status_code)
        with sqlite3.connect(Config.DB_PATH) as conn:
            self.assertEqual(("parent", "g_child"), conn.execute("SELECT * FROM parent_child_links").fetchone()[:2])

    def test_app_links_uses_configured_static_folder(self):
        self.fixture.app.static_folder = str(Path(__file__).resolve().parents[1] / "app" / "static")
        with self.fixture.client.get("/.well-known/assetlinks.json") as response:
            self.assertEqual(200, response.status_code)
            self.assertEqual("com.learnwords.app", response.get_json()[0]["target"]["package_name"])

    def test_retries_are_idempotent_but_another_account_cannot_reuse_invite(self):
        code = create_invite_code(Config.DB_PATH, "parent")
        self.assertTrue(accept_invitation("g_child", code, "invite")["ok"])
        self.assertTrue(accept_invitation("g_child", code, "invite")["ok"])
        self.assertFalse(accept_invitation("g_other", code, "invite")["ok"])

    def test_reverse_invite_has_same_replay_protection_in_bot_helper(self):
        code = create_pairing_code(Config.DB_PATH, "g_child")
        payload = invitation_payload(code, "family")
        self.assertTrue(accept_invitation("parent", payload["url"])["ok"])
        self.assertTrue(link_parent_with_pairing_code(Config.DB_PATH, "parent", code)["ok"])
        self.assertFalse(link_parent_with_pairing_code(Config.DB_PATH, "other-parent", code)["ok"])

    def test_new_invite_does_not_break_an_already_shared_link(self):
        old = create_invite_code(Config.DB_PATH, "parent")
        create_invite_code(Config.DB_PATH, "parent")
        self.assertTrue(accept_invitation("g_child", old, "invite")["ok"])

    def test_expiry_and_wrong_roles(self):
        code = create_invite_code(Config.DB_PATH, "parent")
        self.assertFalse(preview_invitation("other-parent", code, "invite")["ok"])
        with sqlite3.connect(Config.DB_PATH) as conn:
            conn.execute("UPDATE family_invite_codes SET expires_at=0 WHERE code=?", (code,))
        self.assertFalse(accept_invitation("g_child", code, "invite")["ok"])

    def test_rate_limit_and_authentication(self):
        path = "/api/family/invitation/preview"
        self.assertEqual(401, self.fixture.client.post(path, json={"code": "bad"}).status_code)
        for _ in range(30):
            self.assertEqual(400, self.fixture.request("POST", path, "parent", json={"code": "bad"}).status_code)
        self.assertEqual(429, self.fixture.request("POST", path, "parent", json={"code": "bad"}).status_code)

    def test_untrusted_url_is_rejected(self):
        payload = invitation_payload(create_invite_code(Config.DB_PATH, "parent"), "invite")
        self.assertFalse(preview_invitation("g_child", payload["url"].replace("app.parallellingvo.app", "example.com"))["ok"])

    def test_consumed_invite_cannot_restore_a_removed_connection(self):
        code = create_invite_code(Config.DB_PATH, "parent")
        self.assertTrue(accept_invitation("g_child", code, "invite")["ok"])
        with sqlite3.connect(Config.DB_PATH) as conn:
            conn.execute("DELETE FROM parent_child_links")
        self.assertFalse(accept_invitation("g_child", code, "invite")["ok"])

    def test_legacy_token_preview_and_parent_limit(self):
        token = self.fixture.request("GET", "/api/family/pairing-code", "g_child").get_json()["token"]
        self.assertEqual(200, self.fixture.request("POST", "/api/family/invitation/preview", "parent", json={"token": token}).status_code)
        for i in range(5):
            uid = "adult" + str(i)
            self.fixture.add_user(uid, "standard")
            code = create_pairing_code(Config.DB_PATH, "g_child")
            self.assertTrue(accept_invitation(uid, code, "family")["ok"])
        code = create_pairing_code(Config.DB_PATH, "g_child")
        self.assertEqual("parent_limit_reached", accept_invitation("parent", code, "family")["error"])
