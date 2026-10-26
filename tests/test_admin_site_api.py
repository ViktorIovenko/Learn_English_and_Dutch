"""Main-site admin (parallellingvo.app/admin) talking to /api/admin/* cross-origin."""
import unittest

from config import Config
from app.admin_api import init_admin_api
import tests.test_advertising as ads_tests

ADMIN = ads_tests.ADMIN
SITE = "https://parallellingvo.app"
EVIL = "https://evil.example"


class _AdsFixture(unittest.TestCase):
    """The advertising test fixture (temp DB, users, Flask app) without its tests."""


for _name, _value in vars(ads_tests.AdvertisingTest).items():
    if callable(_value) and not _name.startswith("test"):
        setattr(_AdsFixture, "setUp_ads" if _name == "setUp" else _name, _value)


class AdminSiteApiTest(_AdsFixture):
    def setUp(self):
        self.setUp_ads()
        self.original_origins = Config.ADMIN_SITE_ORIGINS
        Config.ADMIN_SITE_ORIGINS = (SITE, "https://www.parallellingvo.app")
        self.addCleanup(setattr, Config, "ADMIN_SITE_ORIGINS", self.original_origins)
        init_admin_api(self.app)

    def csrf(self, client):
        data = client.get("/api/admin/session", headers={"Origin": SITE}).get_json()
        return data["csrf_token"]

    # ------------------------------------------------------------ auth status
    def test_auth_status_reports_server_side_admin_flag(self):
        anon = self.client().get("/auth/status", headers={"Origin": SITE})
        self.assertEqual((anon.json["authenticated"], anon.json["is_admin"]), (False, False))
        self.assertEqual(anon.headers["Access-Control-Allow-Origin"], SITE)
        user = self.client("free_user").get("/auth/status", headers={"Origin": SITE}).json
        self.assertEqual((user["authenticated"], user["is_admin"]), (True, False))
        admin = self.client(ADMIN).get("/auth/status", headers={"Origin": SITE}).json
        self.assertTrue(admin["is_admin"])
        evil = self.client(ADMIN).get("/auth/status", headers={"Origin": EVIL})
        self.assertNotIn("Access-Control-Allow-Origin", evil.headers)

    def test_admin_session_endpoint_status_codes(self):
        self.assertEqual(self.client().get("/api/admin/session").status_code, 401)
        self.assertEqual(self.client("free_user").get("/api/admin/session").status_code, 403)
        resp = self.client(ADMIN).get("/api/admin/session", headers={"Origin": SITE})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["csrf_token"])
        self.assertEqual(resp.headers["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(resp.headers["Cache-Control"], "no-store")

    # ------------------------------------------------------------------- CORS
    def test_only_exact_allowlisted_origins_get_cors(self):
        admin = self.client(ADMIN)
        ok = admin.get("/api/admin/overview", headers={"Origin": SITE})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.headers["Access-Control-Allow-Origin"], SITE)
        self.assertIn("users", ok.json)
        for origin in (EVIL, "https://parallellingvo.app.evil.example", "null", "*"):
            with self.subTest(origin=origin):
                resp = admin.get("/api/admin/overview", headers={"Origin": origin})
                self.assertEqual(resp.status_code, 403)
                self.assertNotIn("Access-Control-Allow-Origin", resp.headers)
        preflight = admin.options("/api/admin/ads/settings", headers={
            "Origin": SITE, "Access-Control-Request-Method": "POST"})
        self.assertEqual(preflight.status_code, 204)
        self.assertIn("X-CSRF-Token", preflight.headers["Access-Control-Allow-Headers"])
        self.assertEqual(admin.options("/api/admin/ads/settings", headers={"Origin": EVIL}).status_code, 403)

    def test_ordinary_user_gets_no_admin_data_cross_origin(self):
        user = self.client("free_user")
        token = user.get("/api/admin/session", headers={"Origin": SITE})
        self.assertEqual(token.status_code, 403)
        self.assertEqual(user.get("/api/admin/overview", headers={"Origin": SITE}).status_code, 401)
        self.assertEqual(user.get("/api/admin/ads/state", headers={"Origin": SITE}).status_code, 401)
        with user.session_transaction() as sess:
            sess["admin_csrf"] = "user-token"
        resp = user.post("/api/admin/grant_access", json={"user_id": "free_user"},
                         headers={"Origin": SITE, "X-CSRF-Token": "user-token"})
        self.assertEqual(resp.status_code, 401)

    # ------------------------------------------------------------------- CSRF
    def test_cross_origin_changes_need_csrf_token(self):
        admin = self.client(ADMIN)
        no_token = admin.post("/api/admin/ads/settings", json={"mode": "preview"}, headers={"Origin": SITE})
        self.assertEqual((no_token.status_code, no_token.json["error"]), (403, "csrf_failed"))
        self.assertEqual(no_token.headers["Access-Control-Allow-Origin"], SITE, "error is readable by the site")
        wrong = admin.post("/api/admin/ads/settings", json={"mode": "preview"},
                           headers={"Origin": SITE, "X-CSRF-Token": "forged"})
        self.assertEqual(wrong.status_code, 403)
        token = self.csrf(admin)
        ok = admin.post("/api/admin/ads/settings", json={"mode": "preview"},
                        headers={"Origin": SITE, "X-CSRF-Token": token})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json["settings"]["mode"], "preview")
        evil = admin.post("/api/admin/ads/settings", json={"mode": "off"},
                          headers={"Origin": EVIL, "X-CSRF-Token": token})
        self.assertEqual(evil.status_code, 403)

    def test_form_posts_are_rejected_for_every_admin_route(self):
        admin = self.client(ADMIN)
        token = self.csrf(admin)
        for path in ("/api/admin/tts_usage/reset", "/api/admin/translation_usage/reset", "/api/admin/grant_access"):
            with self.subTest(path=path):
                resp = admin.post(path, data="{}", content_type="text/plain",
                                  headers={"Origin": SITE, "X-CSRF-Token": token})
                self.assertEqual(resp.status_code, 400)

    def test_live_still_needs_server_side_safety_checks(self):
        admin = self.client(ADMIN)
        token = self.csrf(admin)
        resp = admin.post("/api/admin/ads/settings", json={"mode": "live", "confirm": "LIVE"},
                          headers={"Origin": SITE, "X-CSRF-Token": token})
        self.assertEqual(resp.json["error"], "live_not_allowed_by_env")

    def test_secrets_never_reach_admin_responses(self):
        Config.AWIN_API_TOKEN = "awin-secret-token"
        admin = self.client(ADMIN)
        state = admin.get("/api/admin/ads/state", headers={"Origin": SITE})
        self.assertTrue(state.json["awin"]["configured"])
        self.assertNotIn("awin-secret-token", state.get_data(as_text=True))

    # --------------------------------------------------------------- legacy UI
    def test_legacy_admin_pages_redirect_to_main_site(self):
        admin = self.client(ADMIN)
        for path, tab in (("/admin/users", "general"), ("/admin/ads", "ads")):
            with self.subTest(path=path):
                resp = admin.get(path)
                self.assertEqual(resp.status_code, 302)
                self.assertTrue(resp.headers["Location"].endswith("tab=" + tab))
        self.assertEqual(self.client("free_user").get("/admin/ads").status_code, 403)

    def test_ads_stats_breakdown_is_anonymous(self):
        resp = self.client(ADMIN).get("/api/admin/ads/stats?days=7")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["days"], 7)
        self.assertEqual(self.client("free_user").get("/api/admin/ads/stats").status_code, 401)


if __name__ == "__main__":
    unittest.main()
