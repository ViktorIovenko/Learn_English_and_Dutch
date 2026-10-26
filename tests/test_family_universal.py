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
        accept_invitation("g_other", create_invite_code(Config.DB_PATH, "other-parent"), "invite")
        code = create_invite_code(Config.DB_PATH, "parent")
        self.assertFalse(preview_invitation("other-parent", code, "invite")["ok"])
        with sqlite3.connect(Config.DB_PATH) as conn:
            conn.execute("UPDATE family_invite_codes SET expires_at=0 WHERE code=?", (code,))
        self.assertFalse(accept_invitation("g_child", code, "invite")["ok"])

    def test_adult_without_children_becomes_child_on_parent_invite(self):
        self.fixture.add_user("adult", "standard")
        with sqlite3.connect(Config.DB_PATH) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS user_daily_goals (user_id TEXT PRIMARY KEY, goal_value INTEGER NOT NULL, updated_at TEXT)")
            conn.execute("INSERT INTO user_daily_goals VALUES ('adult', 10, '')")
        code = create_invite_code(Config.DB_PATH, "parent")
        preview = preview_invitation("adult", code, "invite")
        self.assertTrue(preview["ok"])
        self.assertTrue(preview["becomes_child"])
        self.assertTrue(accept_invitation("adult", code, "invite")["ok"])
        with sqlite3.connect(Config.DB_PATH) as conn:
            self.assertEqual("child", conn.execute("SELECT account_type FROM users WHERE user_id='adult'").fetchone()[0])
            self.assertTrue(conn.execute("SELECT 1 FROM parent_child_links WHERE parent_user_id='parent' AND child_user_id='adult'").fetchone())
            # the adult's 10-minute goal must not turn into a 10-word goal
            self.assertIsNone(conn.execute("SELECT 1 FROM user_daily_goals WHERE user_id='adult'").fetchone())

    def test_new_account_becomes_parent_with_child_code(self):
        self.fixture.add_user("newbie", "pending")
        code = create_pairing_code(Config.DB_PATH, "g_child")
        preview = preview_invitation("newbie", code, "family")
        self.assertTrue(preview["ok"])
        self.assertTrue(preview["becomes_parent"])
        self.assertTrue(link_parent_with_pairing_code(Config.DB_PATH, "newbie", code)["ok"])
        with sqlite3.connect(Config.DB_PATH) as conn:
            self.assertEqual("standard", conn.execute("SELECT account_type FROM users WHERE user_id='newbie'").fetchone()[0])

    def test_connect_page_offers_sign_in_and_app_handoffs(self):
        with patch("app.routes._telegram_bot_username", return_value="testbot"):
            with self.fixture.client.get("/family/connect?code=abc_DEF-1&kind=invite") as response:
                page = response.get_data(as_text=True)
        self.assertIn('id="authGate"', page)
        self.assertIn("https://t.me/testbot?start=invite_abc_DEF-1", page)
        self.assertIn("package=com.learnwords.app", page)

    def test_adult_with_children_cannot_become_child(self):
        accept_invitation("g_child", create_invite_code(Config.DB_PATH, "other-parent"), "invite")
        code = create_invite_code(Config.DB_PATH, "parent")
        self.assertEqual("unlink_children_required", preview_invitation("other-parent", code, "invite")["error"])
        with sqlite3.connect(Config.DB_PATH) as conn:
            self.assertEqual("standard", conn.execute("SELECT account_type FROM users WHERE user_id='other-parent'").fetchone()[0])

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
