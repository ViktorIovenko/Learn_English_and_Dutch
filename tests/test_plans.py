import gc
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from flask import Flask

from config import Config
from app import ai_platform, content_providers, plans, routes
from app.family_invites import ensure_invitation_schema
from app.family_pairing import create_invite_code, link_child_with_invite_code

ADMIN = "999"
TEMPLATES = Path(__file__).resolve().parents[1] / "app" / "templates"


class TariffPlansTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "plans.db")
        keys = ("DB_PATH", "SECRET_KEY", "ADMIN_IDS", "ALLOW_LEGACY_UID_AUTH", "PAID_AI_ENABLED",
                "ADS_ENABLED", "ENFORCE_PLAN_LIMITS", "CONTENT_PROVIDER_MODULE", "CONTENT_TTS_PROVIDER_MODULE")
        self.original = {key: getattr(Config, key) for key in keys}
        Config.DB_PATH = self.db_path
        Config.SECRET_KEY = "plans-secret"
        Config.ADMIN_IDS = (int(ADMIN),)
        Config.ALLOW_LEGACY_UID_AUTH = True
        Config.PAID_AI_ENABLED = False
        Config.ADS_ENABLED = False
        Config.ENFORCE_PLAN_LIMITS = False
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE users (
                    user_id TEXT PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    account_type TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
            """)
            conn.execute("CREATE TABLE words (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, lesson TEXT, number TEXT)")
            conn.commit()
        routes._ensure_family_schema()
        with sqlite3.connect(self.db_path) as conn:
            ensure_invitation_schema(conn)
            conn.commit()
        self.app = Flask(__name__, template_folder=str(TEMPLATES))
        self.app.config.update(TESTING=True, SECRET_KEY=Config.SECRET_KEY)
        self.app.context_processor(lambda: {
            "t": lambda key, **kwargs: key,
            "current_ui_language": "en",
            "i18n_catalog": {},
            "legacy_i18n_catalog": {},
        })
        self.app.register_blueprint(routes.web)
        self.add_user(ADMIN, "standard")

    def tearDown(self):
        for key, value in self.original.items():
            setattr(Config, key, value)
        self.app = None
        gc.collect()
        self.temp_dir.cleanup()

    # helpers -------------------------------------------------------------
    def add_user(self, user_id, account_type="standard"):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, account_type) VALUES (?, ?, ?, '', ?)",
                (user_id, user_id, user_id.title(), account_type),
            )
            conn.commit()

    def session_client(self, user_id):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["is_auth"] = True
            sess["tg_user_id"] = user_id
        return client

    def set_subscription(self, user_id, status, *, ends_in_ms=None, plan=None):
        routes._ensure_subscription_schema()
        now = int(time.time() * 1000)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_subscriptions (user_id, status, trial_started_at, trial_ends_at, "
                "current_period_ends_at, provider, updated_at, plan) VALUES (?, ?, ?, ?, ?, 'manual', ?, ?)",
                (user_id, status, now - 1000, now + (ends_in_ms if status == "trial" else -1),
                 now + ends_in_ms if status == "active" and ends_in_ms else None, now, plan),
            )
            conn.commit()

    def subscriptions_snapshot(self):
        routes._ensure_subscription_schema()
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT * FROM user_subscriptions ORDER BY user_id").fetchall()

    def link(self, parent, child):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO parent_child_links (parent_user_id, child_user_id) VALUES (?, ?)", (parent, child))
            conn.commit()

    # 1, 2, 9: admin access stays absolute; preview is session-only ----------
    def test_admin_preview_switches_ui_without_touching_real_rights(self):
        admin = self.session_client(ADMIN)
        me = admin.get("/api/me").get_json()
        self.assertTrue(me["is_admin"])
        self.assertEqual(me["plan_state"]["plan"], "admin")
        self.assertIn("dashboard-nav-admin", admin.get("/").get_data(as_text=True))
        before = self.subscriptions_snapshot()

        for plan, ads in (("free", True), ("premium", False), ("family", False)):
            with self.subTest(plan=plan):
                resp = admin.post("/api/admin/plan-preview", json={"plan": plan, "show_ads": True})
                self.assertEqual(resp.status_code, 200)
                me = admin.get("/api/me").get_json()
                self.assertFalse(me["is_admin"], "admin UI must be hidden during preview")
                self.assertEqual(me["plan_state"]["plan"], plan)
                self.assertEqual(me["plan_state"]["preview"], plan)
                self.assertEqual(me["plan_state"]["ads_visible"], ads)
                self.assertEqual(me["subscription"]["plan"], plan)
                self.assertTrue(me["subscription"]["preview"])
                # Real admin rights on the server are untouched.
                self.assertEqual(admin.get("/api/admin/users").status_code, 200)
                self.assertNotIn("dashboard-nav-admin", admin.get("/").get_data(as_text=True))

        self.assertEqual(self.subscriptions_snapshot(), before, "preview must not write subscriptions")
        admin.post("/api/admin/plan-preview", json={"plan": "exit"})
        me = admin.get("/api/me").get_json()
        self.assertTrue(me["is_admin"])
        self.assertIsNone(me["plan_state"]["preview"])
        self.assertIn("dashboard-nav-admin", admin.get("/").get_data(as_text=True))

    def test_preview_does_not_leak_to_other_users_or_sessions(self):
        self.add_user("alice")
        admin = self.session_client(ADMIN)
        admin.post("/api/admin/plan-preview", json={"plan": "free"})
        other_admin_session = self.session_client(ADMIN)
        self.assertIsNone(other_admin_session.get("/api/me").get_json()["plan_state"]["preview"])
        alice = self.session_client("alice")
        self.assertIsNone(alice.get("/api/me").get_json()["plan_state"]["preview"])
        self.assertEqual(alice.post("/api/admin/plan-preview", json={"plan": "free"}).status_code, 401)
        self.assertEqual(alice.get("/api/admin/plan-preview").status_code, 401)

    def test_invalid_preview_plan_is_rejected(self):
        admin = self.session_client(ADMIN)
        self.assertEqual(admin.post("/api/admin/plan-preview", json={"plan": "admin"}).status_code, 400)

    # 3, 7: Free has no paid AI; checks run on the server ---------------------
    def test_free_preview_blocks_family_server_side_and_family_preview_allows_it(self):
        admin = self.session_client(ADMIN)
        admin.post("/api/admin/plan-preview", json={"plan": "free"})
        resp = admin.get("/api/family/dashboard")
        self.assertEqual(resp.status_code, 402)
        self.assertEqual(resp.get_json()["required_plan"], "family")
        self.assertEqual(admin.get("/api/family/invite-code").status_code, 402)
        admin.post("/api/admin/plan-preview", json={"plan": "premium"})
        self.assertEqual(admin.get("/api/family/dashboard").status_code, 402)
        admin.post("/api/admin/plan-preview", json={"plan": "family"})
        self.assertNotEqual(admin.get("/api/family/dashboard").status_code, 402)
        self.assertEqual(admin.get("/api/family/invite-code").status_code, 200)

    def test_real_users_keep_family_features_until_limits_are_enforced(self):
        self.add_user("parent")
        self.add_user("kid", "child")
        self.link("parent", "kid")
        self.set_subscription("parent", "trial", ends_in_ms=-1)  # trial ended -> Free
        parent = self.session_client("parent")
        me = parent.get("/api/me").get_json()
        self.assertTrue(me["subscription"]["access"], "Free users keep using the app")
        self.assertFalse(me["subscription"]["paid_access"])
        self.assertEqual(me["plan_state"]["plan"], "free")
        self.assertEqual(parent.get("/api/family/dashboard").status_code, 200)
        Config.ENFORCE_PLAN_LIMITS = True
        self.assertEqual(parent.get("/api/family/dashboard").status_code, 402)

    # 5: Family = parent + up to 4 children, children inherit ----------------
    def test_family_plan_is_inherited_and_limited_to_four_children(self):
        self.add_user("parent")
        self.set_subscription("parent", "active", ends_in_ms=10 ** 9, plan="family")
        for index in range(5):
            self.add_user(f"kid{index}", "child")
        for index in range(4):
            code = create_invite_code(self.db_path, "parent")
            self.assertTrue(link_child_with_invite_code(self.db_path, f"kid{index}", code)["ok"])
        code = create_invite_code(self.db_path, "parent")
        result = link_child_with_invite_code(self.db_path, "kid4", code)
        self.assertEqual(result, {"ok": False, "error": "children_limit_reached"})
        with self.app.test_request_context():
            self.assertEqual(routes._real_plan("parent"), "family")
            self.assertEqual(routes._real_plan("kid0"), "family")
            self.assertEqual(routes._real_plan("kid4"), "free")

    def test_existing_links_above_limit_are_kept(self):
        self.add_user("parent")
        for index in range(6):
            self.add_user(f"kid{index}", "child")
            self.link("parent", f"kid{index}")
        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM parent_child_links WHERE parent_user_id='parent'").fetchone()[0]
        self.assertEqual(count, 6)

    # 4, 8: ads ---------------------------------------------------------------
    def test_ads_are_off_by_default_and_never_shown_to_paid_plans(self):
        self.add_user("free_user")
        self.add_user("premium_user")
        self.set_subscription("premium_user", "active", ends_in_ms=10 ** 9)
        free_state = self.session_client("free_user").get("/api/me").get_json()["plan_state"]
        self.assertEqual(free_state["plan"], "premium", "new users start with the Premium trial")
        self.set_subscription("free_user", "trial", ends_in_ms=-1)
        free_state = self.session_client("free_user").get("/api/me").get_json()["plan_state"]
        self.assertEqual(free_state["plan"], "free")
        self.assertFalse(free_state["ads_visible"], "ads are disabled by default")
        Config.ADS_ENABLED = True
        self.assertTrue(self.session_client("free_user").get("/api/me").get_json()["plan_state"]["ads_visible"])
        self.assertFalse(self.session_client("premium_user").get("/api/me").get_json()["plan_state"]["ads_visible"])

    def test_ad_slot_template_has_no_external_ad_network(self):
        markup = (TEMPLATES / "_ad_slot.html").read_text(encoding="utf-8")
        # The label ("Ad Preview" / localized "Ad") now comes from /api/ads/page.
        self.assertIn("data-ad-placement", markup)
        for forbidden in ("<script", "<iframe", "googlesyndication", "adsbygoogle", "http://", "https://"):
            self.assertNotIn(forbidden, markup)

    # 3: global paid-AI switch ----------------------------------------------
    def test_paid_ai_switch_blocks_every_provider_even_for_admin(self):
        Config.CONTENT_PROVIDER_MODULE = "tests.fake_paid_provider_that_must_not_load"
        Config.CONTENT_TTS_PROVIDER_MODULE = "tests.fake_paid_tts_that_must_not_load"
        for operation in ("translate_word", "translate_sentence", "generate_examples", "suggest_words"):
            self.assertIsNone(content_providers.adapter(operation))
        self.assertFalse(ai_platform.is_configured())
        self.assertIsInstance(content_providers.tts_provider(), content_providers.GttsProvider)
        with mock.patch("app.ai_platform.requests.post") as post:
            with self.assertRaises(ai_platform.AiPlatformError):
                ai_platform._call_runtime_chat("key", "huis")
            post.assert_not_called()
        admin = self.session_client(ADMIN)
        status = admin.get("/api/ai/status").get_json()
        self.assertFalse(status["paid_ai_enabled"])
        self.assertFalse(status["cloud_available"])
        # A configured paid provider module must never even be imported.
        with mock.patch("app.content_providers.importlib.import_module",
                        side_effect=AssertionError("paid provider loaded")):
            resp = admin.post("/api/translate/word", json={"word": "huis", "from_lang": "nl"})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json()["provider_calls"], 0)
            topic = admin.post("/api/generate/topic", json={"topic": "food"})
        self.assertEqual(topic.status_code, 403)
        self.assertEqual(topic.get_json()["error"], "paid_ai_disabled")

    def test_paid_ai_respects_tariff_when_enabled(self):
        Config.PAID_AI_ENABLED = True
        admin = self.session_client(ADMIN)
        with self.app.test_request_context():
            self.assertTrue(routes._paid_ai_allowed(ADMIN))
        admin.post("/api/admin/plan-preview", json={"plan": "free"})
        self.assertFalse(admin.get("/api/ai/status").get_json()["paid_ai_enabled"])
        admin.post("/api/admin/plan-preview", json={"plan": "premium"})
        self.assertTrue(admin.get("/api/ai/status").get_json()["paid_ai_enabled"])

    # 6: anonymous visitors ----------------------------------------------------
    def test_anonymous_visitors_have_no_app_access(self):
        Config.ALLOW_LEGACY_UID_AUTH = False
        client = self.app.test_client()
        self.assertFalse(client.get("/api/me").get_json()["auth"])
        for method, path in (("GET", "/api/subscription"), ("GET", "/api/family/dashboard"),
                             ("POST", "/api/translate/word"), ("GET", "/api/admin/plan-preview"),
                             ("POST", "/api/admin/plan-preview"), ("GET", "/api/ai/status")):
            with self.subTest(path=path):
                self.assertIn(client.open(path, method=method, json={}).status_code, (401, 403))

    # 10: data preservation ----------------------------------------------------
    def test_plan_column_migration_keeps_existing_subscriptions(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE user_subscriptions (
                    user_id TEXT PRIMARY KEY, status TEXT NOT NULL DEFAULT 'trial',
                    trial_started_at INTEGER NOT NULL, trial_ends_at INTEGER NOT NULL,
                    current_period_ends_at INTEGER, provider TEXT, provider_customer_id TEXT,
                    provider_subscription_id TEXT, cancel_at_period_end INTEGER NOT NULL DEFAULT 0,
                    updated_at INTEGER NOT NULL)
            """)
            conn.execute("INSERT INTO user_subscriptions (user_id, status, trial_started_at, trial_ends_at, "
                         "current_period_ends_at, provider, updated_at) VALUES ('legacy', 'active', 1, 2, 99999999999999, 'manual', 3)")
            conn.commit()
        routes._ensure_subscription_schema()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT status, provider, current_period_ends_at, plan FROM user_subscriptions "
                               "WHERE user_id='legacy'").fetchone()
        self.assertEqual(row, ("active", "manual", 99999999999999, None))
        with self.app.test_request_context():
            self.assertEqual(routes._real_plan("legacy"), "premium")

    def test_admin_grant_can_assign_family_and_revoke_clears_it(self):
        self.add_user("bob")
        admin = self.session_client(ADMIN)
        self.assertEqual(admin.post("/api/admin/grant_access", json={"user_id": "bob", "plan": "family"}).get_json()["plan"], "family")
        with self.app.test_request_context():
            self.assertEqual(routes._real_plan("bob"), "family")
        self.assertEqual(admin.post("/api/admin/grant_access", json={"user_id": "bob", "plan": "gold"}).status_code, 400)
        admin.post("/api/admin/revoke_access", json={"user_id": "bob"})
        with self.app.test_request_context():
            self.assertEqual(routes._real_plan("bob"), "free")

    def test_feature_matrix_matches_agreed_model(self):
        self.assertEqual(plans.PLANS["free"]["price_eur"], 0)
        self.assertEqual(plans.PLANS["premium"]["price_eur"], 4.99)
        self.assertEqual(plans.PLANS["family"]["price_eur"], 9.99)
        self.assertTrue(plans.PLANS["free"]["ads"])
        self.assertFalse(plans.PLANS["premium"]["ads"] or plans.PLANS["family"]["ads"])
        self.assertFalse(plans.PLANS["free"]["ai_paid"])
        self.assertTrue(plans.PLANS["premium"]["ai_paid"] and plans.PLANS["family"]["ai_paid"])
        self.assertEqual(plans.PLANS["family"]["max_children"], 4)
        for plan in plans.PREVIEW_PLANS:
            self.assertTrue(plans.PLANS[plan]["manual_words"] and plans.PLANS[plan]["exercises"])


if __name__ == "__main__":
    unittest.main()
