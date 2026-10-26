import gc
import io
import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
from urllib import error as urlerror

from flask import Flask

from config import Config
from app import routes
from app.advertising import awin, init_advertising, policy, selection, store
from app.advertising import creatives as cr
from app.auth_links import create_auth_token
from app.family_invites import ensure_invitation_schema

ADMIN = "999"
TEMPLATES = Path(__file__).resolve().parents[1] / "app" / "templates"
STATIC = Path(__file__).resolve().parents[1] / "app" / "static"
AWIN_CODE = ('<a href="https://www.awin1.com/cread.php?s=111&v=222&q=333&r=3118768">'
             '<img src="https://www.awin1.com/cshow.php?s=111&v=222&q=333&r=3118768" '
             'width="728" height="90" border="0" alt="Books"></a>')


class FakeResponse(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class AdvertisingTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "ads.db")
        keys = ("DB_PATH", "SECRET_KEY", "ADMIN_IDS", "ALLOW_LEGACY_UID_AUTH", "ADS_LIVE_ALLOWED",
                "AWIN_API_TOKEN", "AWIN_PUBLISHER_ID", "ADS_COUNTRY_HEADER", "ENFORCE_PLAN_LIMITS")
        self.original = {key: getattr(Config, key) for key in keys}
        Config.DB_PATH = self.db_path
        Config.SECRET_KEY = "ads-secret"
        Config.ADMIN_IDS = (int(ADMIN),)
        Config.ALLOW_LEGACY_UID_AUTH = False
        Config.ADS_LIVE_ALLOWED = False
        Config.AWIN_API_TOKEN = ""
        Config.AWIN_PUBLISHER_ID = "3118768"
        Config.ADS_COUNTRY_HEADER = ""
        Config.ENFORCE_PLAN_LIMITS = False
        store.reset_schema_cache()
        awin.AwinClient._calls.clear()
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
        self.app = Flask(__name__, template_folder=str(TEMPLATES), static_folder=str(STATIC))
        self.app.config.update(TESTING=True, SECRET_KEY=Config.SECRET_KEY)
        self.app.context_processor(lambda: {
            "t": lambda key, **kwargs: key, "current_ui_language": "en",
            "i18n_catalog": {}, "legacy_i18n_catalog": {},
        })
        self.app.register_blueprint(routes.web)
        init_advertising(self.app, routes._ads_viewer)
        self.add_user(ADMIN)
        self.add_user("free_user")
        self.set_subscription("free_user", "trial", ends_in_ms=-1000)  # trial over -> Free

    def tearDown(self):
        for key, value in self.original.items():
            setattr(Config, key, value)
        store.reset_schema_cache()
        self.app = None
        gc.collect()
        self.temp_dir.cleanup()

    # helpers -------------------------------------------------------------
    def add_user(self, user_id, account_type="standard"):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO users (user_id, username, first_name, last_name, account_type) "
                         "VALUES (?, ?, ?, '', ?)", (user_id, user_id, user_id.title(), account_type))
            conn.commit()

    def client(self, user_id=None, consent=None):
        client = self.app.test_client()
        if user_id:
            with client.session_transaction() as sess:
                sess["is_auth"] = True
                sess["tg_user_id"] = user_id
        if consent:
            client.set_cookie("pl_ads_consent", f"v1:{consent}")
        return client

    def set_subscription(self, user_id, status, *, ends_in_ms=None, plan=None):
        routes._ensure_subscription_schema()
        now = int(time.time() * 1000)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_subscriptions (user_id, status, trial_started_at, trial_ends_at, "
                "current_period_ends_at, provider, updated_at, plan) VALUES (?, ?, ?, ?, ?, 'manual', ?, ?)",
                (user_id, status, now - 10_000, now + (ends_in_ms or 0) if status == "trial" else now - 10_000,
                 now + ends_in_ms if status == "active" and ends_in_ms else None, now, plan),
            )
            conn.commit()

    def set_mode(self, mode):
        store.save_settings({"mode": mode})

    def go_live(self, *, platforms=("web",)):
        Config.ADS_LIVE_ALLOWED = True
        store.save_settings({"mode": "live", "live_platforms": list(platforms)})

    def add_live_creative(self, **overrides):
        self._awin_seq = getattr(self, "_awin_seq", 4241) + 1
        advertiser_id = store.save_advertiser({"name": "Book shop", "awin_id": self._awin_seq, "enabled": True,
                                               "membership_status": "joined"})
        parsed = cr.parse_awin_creative(AWIN_CODE)
        item = {"advertiser_id": advertiser_id, "name": "Books 728", "kind": "awin_html", "enabled": True,
                "raw_code": AWIN_CODE, **parsed}
        item.update(overrides)
        return store.save_creative(item)

    def page(self, client, device="desktop", page="dashboard", **extra):
        query = "&".join(f"{k}={v}" for k, v in {"page": page, "device": device, **extra}.items())
        return client.get(f"/api/ads/page?{query}", headers={"Accept-Language": "nl-NL,nl;q=0.9"})

    def admin_post(self, client, url, body):
        return client.post(url, json=body)

    # --------------------------------------------------------------- modes
    def test_default_mode_is_off_and_no_script_or_ads(self):
        self.assertEqual(store.get_settings()["mode"], "off")
        for uid, reason in ((ADMIN, "admin_full_access"), ("free_user", "mode_off")):
            data = self.page(self.client(uid)).get_json()
            self.assertEqual(data["slots"], [])
            self.assertEqual(data["decision"]["reason"], reason)
        html = self.client("free_user").get("/").get_data(as_text=True)
        self.assertNotIn("ads.js", html, "OFF must not even load the ad client")
        self.assertNotIn("ads.js", self.client(ADMIN).get("/").get_data(as_text=True))

    def test_admin_free_simulation_shows_all_ad_places_even_in_off(self):
        admin = self.client(ADMIN)
        admin.post("/api/admin/plan-preview", json={"plan": "free"})
        self.assertIn("ads.js", admin.get("/").get_data(as_text=True))
        slots = self.page(admin, device="phone").get_json()["slots"]
        by_kind = {}
        for slot in slots:
            by_kind.setdefault(slot["render"], []).append(slot["placement"])
        self.assertEqual(by_kind["demo"], ["dashboard_bottom"], "one real demo banner per screen")
        self.assertEqual(sorted(by_kind["placeholder"]), ["dashboard_between", "dashboard_top"])
        self.assertTrue(all(s["preview"] and "click_url" not in s for s in slots))
        # Users still get nothing in OFF.
        self.assertEqual(self.page(self.client("free_user")).get_json()["slots"], [])

    def test_web_shows_a_row_of_three_banners_between_lessons_only_on_web(self):
        admin = self.client(ADMIN)
        admin.post("/api/admin/plan-preview", json={"plan": "free"})
        store.save_settings({"max_per_page": 4})
        for key in ("dashboard_top", "dashboard_between"):
            item = next(p for p in store.list_placements() if p["key"] == key)
            store.upsert_placement({**item, "enabled": True})

        def between(platform):
            resp = admin.get("/api/ads/page?page=dashboard&device=desktop&columns=5&platform=" + platform)
            return [s for s in resp.get_json()["slots"] if s["placement"] == "dashboard_between"]

        row = between("web")
        self.assertEqual([0, 1, 2], [s["column"] for s in row])
        self.assertEqual(3, len({s["creative_id"] for s in row}), "three different banners")
        self.assertTrue(all(s["size"] == "300x250" for s in row))
        self.assertEqual(1, len(between("telegram")), "Mini App keeps a single banner")

    def test_preview_shows_demo_only_to_admin_in_free_simulation(self):
        self.set_mode("preview")
        admin = self.client(ADMIN)
        self.assertEqual(self.page(admin).get_json()["decision"]["reason"], "admin_full_access")
        self.assertNotIn("ads.js", admin.get("/").get_data(as_text=True))
        admin.post("/api/admin/plan-preview", json={"plan": "free"})
        data = self.page(admin).get_json()
        self.assertEqual(data["decision"]["serve"], "demo")
        filled = [s for s in data["slots"] if s["render"] != "placeholder"]
        self.assertEqual(len(filled), 1, "only one demo banner per screen initially")
        slot = filled[0]
        self.assertTrue(slot["preview"])
        self.assertNotIn("click_url", slot)
        self.assertNotIn("image_url", slot)
        self.assertIn("ads.js", admin.get("/").get_data(as_text=True))
        # A regular Free user sees nothing in PREVIEW.
        free = self.page(self.client("free_user")).get_json()
        self.assertEqual((free["decision"]["reason"], free["slots"]), ("preview_admin_only", []))

    def test_admin_paid_simulation_and_exit_have_no_ads(self):
        self.set_mode("preview")
        admin = self.client(ADMIN)
        for plan in ("premium", "family"):
            admin.post("/api/admin/plan-preview", json={"plan": plan})
            self.assertEqual(self.page(admin).get_json()["slots"], [], plan)
        admin.post("/api/admin/plan-preview", json={"plan": "exit"})
        self.assertEqual(self.page(admin).get_json()["decision"]["reason"], "admin_full_access")
        # The simulation never touched the admin's real rights.
        self.assertTrue(routes._is_admin_user_id(ADMIN))

    def test_preview_never_exposes_real_material_or_tracking(self):
        self.set_mode("preview")
        self.add_live_creative()
        admin = self.client(ADMIN)
        admin.post("/api/admin/plan-preview", json={"plan": "free"})
        with mock.patch("urllib.request.urlopen") as urlopen:
            data = self.page(admin, device="desktop").get_json()
            admin.post("/api/ads/event", json={"event": "impression", "placement": "dashboard_bottom",
                                               "creative_id": 1})
        urlopen.assert_not_called()
        self.assertEqual(data["slots"][0]["render"], "mock")
        self.assertNotIn("awin1.com", json.dumps(data))
        self.assertEqual(store.stats_summary(), [], "preview must not count impressions")

    # -------------------------------------------------------------- tariffs
    def test_live_free_user_with_consent_gets_awin_material(self):
        self.go_live()
        creative_id = self.add_live_creative()
        data = self.page(self.client("free_user", consent="granted")).get_json()
        self.assertEqual(data["decision"]["serve"], "live")
        slot = data["slots"][0]
        self.assertEqual((slot["render"], slot["creative_id"], slot["size"]), ("image", creative_id, "728x90"))
        self.assertTrue(slot["click_url"].startswith("https://www.awin1.com/cread.php"))
        self.assertEqual(slot["label"], "Ad")  # user's UI language (default en)

    def test_paid_plans_trial_and_lapsed_paid_get_no_ads(self):
        self.go_live()
        self.add_live_creative()
        cases = {
            "premium_user": ("active", None, None, "paid_plan"),
            "family_user": ("active", None, "family", "paid_plan"),
            "trial_user": ("trial", 86_400_000, None, "paid_plan"),
            "lapsed_user": ("active", -1000, None, "status_not_free"),
        }
        for uid, (status, ends, plan, reason) in cases.items():
            with self.subTest(uid):
                self.add_user(uid)
                self.set_subscription(uid, status, ends_in_ms=ends, plan=plan)
                data = self.page(self.client(uid, consent="granted")).get_json()
                self.assertEqual((data["decision"]["reason"], data["slots"]), (reason, []))
        # Lapsed paid subscriptions count as Free only after an explicit switch.
        store.save_settings({"lapsed_paid_as_free": True})
        self.assertEqual(self.page(self.client("lapsed_user", consent="granted")).get_json()["decision"]["serve"], "live")

    def test_new_user_without_subscription_row_gets_no_ads(self):
        self.go_live()
        self.add_live_creative()
        self.add_user("fresh")
        self.assertEqual(self.page(self.client("fresh", consent="granted")).get_json()["decision"]["reason"],
                         "status_not_free")

    def test_child_accounts_and_family_children_never_get_ads(self):
        self.go_live()
        self.add_live_creative()
        self.add_user("kid", "child")
        self.set_subscription("kid", "trial", ends_in_ms=-1000)
        data = self.page(self.client("kid", consent="granted")).get_json()
        self.assertEqual((data["decision"]["reason"], data["slots"]), ("child_account", []))

    def test_frontend_cannot_fake_plan_or_admin(self):
        self.go_live()
        self.add_live_creative()
        self.add_user("premium_user")
        self.set_subscription("premium_user", "active")
        client = self.client("premium_user", consent="granted")
        with client.session_transaction() as sess:
            sess["plan_preview"] = "free"  # forged admin preview key
        resp = client.get("/api/ads/page?page=dashboard&device=desktop&plan=free&serve=live",
                          headers={"X-Plan": "free", "X-User-Id": "free_user"})
        self.assertEqual(resp.get_json()["slots"], [])
        self.assertEqual(client.get("/api/admin/ads/state").status_code, 401)
        self.assertEqual(client.post("/api/admin/ads/settings", json={"mode": "off"}).status_code, 401)

    def test_unauthenticated_and_forged_clients_get_nothing(self):
        self.set_mode("preview")
        self.assertEqual(self.app.test_client().get("/api/ads/page").status_code, 401)
        bearer = self.app.test_client().get("/api/ads/page", headers={"Authorization": "Bearer x"})
        self.assertEqual(bearer.status_code, 401, "invalid token")
        Config.ALLOW_LEGACY_UID_AUTH = True
        legacy = self.app.test_client().get("/api/ads/page", headers={"X-User-Id": "free_user"})
        self.assertEqual(legacy.status_code, 401, "spoofable X-User-Id is never trusted for ads")

    # -------------------------------------------------------------- Android
    def android(self, user_id):
        return {"Authorization": f"Bearer {create_auth_token(user_id)}", "X-Client": "android"}

    def test_android_free_user_gets_ads_after_in_app_consent(self):
        self.go_live(platforms=("web", "telegram", "android"))
        self.add_live_creative(width=320, height=50)
        client = self.app.test_client()
        headers = self.android("free_user")
        first = client.get("/api/ads/page?page=dashboard&device=phone", headers=headers).get_json()
        self.assertEqual(first["decision"]["reason"], "consent_required")
        self.assertIn("consent_prompt", first)
        resp = client.post("/api/ads/consent", json={"choice": "granted"}, headers=headers)
        self.assertNotIn("Set-Cookie", resp.headers, "app consent is stored server-side")
        self.assertEqual(store.get_consent("free_user", "android"), "granted")
        data = client.get("/api/ads/page?page=dashboard&device=phone&platform=web", headers=headers).get_json()
        self.assertEqual(data["decision"]["serve"], "live")
        self.assertEqual(data["slots"][0]["size"], "320x50")
        client.post("/api/ads/event", json={"event": "impression", "placement": "dashboard_bottom",
                                            "creative_id": data["slots"][0]["creative_id"], "device": "phone"},
                    headers=headers)
        self.assertEqual(store.stats_summary()[0]["impressions"], 1)
        client.post("/api/ads/consent", json={"choice": "denied"}, headers=headers)
        withdrawn = client.get("/api/ads/page?page=dashboard&device=phone", headers=headers).get_json()
        self.assertEqual((withdrawn["decision"]["reason"], withdrawn["slots"]), ("consent_denied", []))

    def test_android_platform_cannot_be_spoofed_and_rules_match_web(self):
        self.go_live(platforms=("web",))  # Android switched off by the admin
        self.add_live_creative(width=320, height=50)
        store.save_consent("free_user", "android", "granted")
        data = self.app.test_client().get("/api/ads/page?page=dashboard&device=phone&platform=web",
                                          headers=self.android("free_user")).get_json()
        self.assertEqual(data["decision"]["reason"], "platform_disabled")
        store.save_settings({"live_platforms": ["android"]})
        self.add_user("premium_user")
        self.set_subscription("premium_user", "active")
        store.save_consent("premium_user", "android", "granted")
        paid = self.app.test_client().get("/api/ads/page?page=dashboard&device=phone",
                                          headers=self.android("premium_user")).get_json()
        self.assertEqual((paid["decision"]["reason"], paid["slots"]), ("paid_plan", []))
        admin = self.app.test_client().get("/api/admin/ads/state", headers=self.android(ADMIN))
        self.assertEqual(admin.status_code, 401, "admin tools need the browser session")

    def test_default_live_platforms_cover_all_clients(self):
        self.assertEqual(store.get_settings()["live_platforms"], ["web", "telegram", "android"])

    # -------------------------------------------------------------- consent
    def test_consent_required_denied_and_gpc(self):
        self.go_live()
        self.add_live_creative()
        unknown = self.page(self.client("free_user")).get_json()
        self.assertTrue(unknown["decision"]["needs_consent"])
        self.assertEqual(unknown["slots"], [])
        self.assertIn("consent_prompt", unknown)
        denied = self.page(self.client("free_user", consent="denied")).get_json()
        self.assertEqual((denied["decision"]["reason"], denied["slots"]), ("consent_denied", []))
        client = self.client("free_user", consent="granted")
        gpc = client.get("/api/ads/page?page=dashboard&device=desktop", headers={"Sec-GPC": "1"}).get_json()
        self.assertEqual(gpc["decision"]["reason"], "consent_denied")

    def test_consent_endpoint_sets_only_choice_cookie(self):
        client = self.client("free_user")
        self.assertEqual(client.post("/api/ads/consent", data="choice=granted").status_code, 400)
        resp = client.post("/api/ads/consent", json={"choice": "granted"})
        self.assertEqual(resp.status_code, 200)
        cookie = resp.headers.get("Set-Cookie", "")
        self.assertIn("pl_ads_consent=v1:granted", cookie)
        self.assertIn("HttpOnly", cookie)
        cross = client.post("/api/ads/consent", json={"choice": "granted"}, headers={"Origin": "https://evil.example"})
        self.assertEqual(cross.status_code, 400)

    # ------------------------------------------------------------ selection
    def test_country_and_language_priority_and_empty_result(self):
        self.go_live()
        nl_id = self.add_live_creative(countries=["NL"], languages=["en"], name="NL")
        de_id = self.add_live_creative(countries=["DE"], name="DE")
        client = self.client("free_user", consent="granted")
        slot = self.page(client).get_json()["slots"][0]
        self.assertEqual(slot["creative_id"], nl_id)
        # Only DE material for a French visitor -> nothing at all.
        store.set_creative_enabled(nl_id, False)
        data = client.get("/api/ads/page?page=dashboard&device=desktop",
                          headers={"Accept-Language": "fr-FR"}).get_json()
        self.assertEqual(data["slots"], [])
        self.assertNotEqual(de_id, nl_id)

    def test_rank_order_country_then_language_then_topic(self):
        base = {"enabled": True, "kind": "text", "starts_on": "", "ends_on": ""}
        items = [
            {**base, "id": 1, "languages": ["ru"], "topics": ["language"]},
            {**base, "id": 2, "countries": ["NL"], "topics": []},
            {**base, "id": 3, "countries": ["NL"], "languages": ["ru"]},
        ]
        best = selection.pick(items, size="320x50", country="NL", language="ru", preferred=["language"], seed="s")
        self.assertEqual(best["id"], 3)
        self.assertIsNone(selection.pick(items[1:], size="320x50", country="", language="ru", preferred=[], seed="s"))

    def test_device_sizes_and_budget(self):
        self.go_live()
        self.add_live_creative()  # 728x90 only
        client = self.client("free_user", consent="granted")
        self.assertEqual(self.page(client, device="phone").get_json()["slots"], [], "no 728 banner on phones")
        self.assertEqual(len(self.page(client, device="tablet").get_json()["slots"]), 1)
        store.upsert_placement({**store.list_placements("dashboard")[0], "enabled": True})
        self.assertLessEqual(len(self.page(client).get_json()["slots"]), 1, "max_per_page=1")

    def test_unapproved_programme_is_not_served_live(self):
        self.go_live()
        creative_id = self.add_live_creative()
        store.set_membership(store.get_creative(creative_id)["advertiser_id"], "pending")
        self.assertEqual(self.page(self.client("free_user", consent="granted")).get_json()["slots"], [])

    # -------------------------------------------------------- creatives/safety
    def test_awin_creative_parser_rejects_unsafe_code(self):
        parsed = cr.parse_awin_creative(AWIN_CODE)
        self.assertEqual((parsed["width"], parsed["height"]), (728, 90))
        bad = [
            AWIN_CODE + "<script>alert(1)</script>",
            AWIN_CODE.replace("<img ", '<img onerror="x()" '),
            AWIN_CODE.replace("https://www.awin1.com/cread", "https://evil.example/cread"),
            AWIN_CODE.replace("<a href=\"https", "<a href=\"javascript:alert(1)//https"),
            '<iframe src="https://www.awin1.com/x"></iframe>',
            '<div>' + AWIN_CODE + '</div>',
        ]
        for code in bad:
            with self.subTest(code=code[:40]):
                with self.assertRaises(cr.CreativeError):
                    cr.parse_awin_creative(code)

    def test_admin_creative_api_validates_and_requires_json(self):
        admin = self.client(ADMIN)
        adv = admin.post("/api/admin/ads/advertisers", json={"name": "Shop", "awin_id": 7}).get_json()
        advertiser_id = adv["advertiser_id"]
        self.assertEqual(adv["advertisers"][0]["membership_status"], "manual",
                         "manual entry never becomes 'joined' without the Awin API")
        ok = admin.post("/api/admin/ads/creatives", json={"advertiser_id": advertiser_id, "kind": "awin_html",
                                                          "raw_code": AWIN_CODE, "enabled": True})
        self.assertEqual(ok.status_code, 200)
        bad = admin.post("/api/admin/ads/creatives", json={"advertiser_id": advertiser_id, "kind": "awin_html",
                                                           "raw_code": AWIN_CODE.replace('width="728"', 'width="600"')})
        self.assertEqual(bad.get_json()["error"], "unsupported_size")
        form = admin.post("/api/admin/ads/settings", data={"mode": "preview"})
        self.assertEqual(form.status_code, 400, "form posts (CSRF) are rejected")

    def test_live_switch_needs_env_token_and_confirmation(self):
        admin = self.client(ADMIN)
        self.assertEqual(admin.post("/api/admin/ads/settings", json={"mode": "live", "confirm": "LIVE"}).get_json()["error"],
                         "live_not_allowed_by_env")
        Config.ADS_LIVE_ALLOWED = True
        self.assertEqual(admin.post("/api/admin/ads/settings", json={"mode": "live", "confirm": "LIVE"}).get_json()["error"],
                         "awin_not_configured")
        Config.AWIN_API_TOKEN = "token"
        self.assertEqual(admin.post("/api/admin/ads/settings", json={"mode": "live"}).get_json()["error"],
                         "confirmation_required")
        self.assertEqual(store.get_settings()["mode"], "off")
        resp = admin.post("/api/admin/ads/settings", json={"mode": "live", "confirm": "LIVE"})
        self.assertEqual(resp.get_json()["settings"]["mode"], "live")

    def test_live_events_are_aggregated_without_user_data(self):
        self.go_live()
        creative_id = self.add_live_creative()
        client = self.client("free_user", consent="granted")
        for event in ("impression", "click", "bogus"):
            client.post("/api/ads/event", json={"event": event, "placement": "dashboard_bottom",
                                                "creative_id": creative_id, "device": "desktop"})
        rows = store.stats_summary()
        self.assertEqual((rows[0]["impressions"], rows[0]["clicks"]), (1, 1))
        with sqlite3.connect(self.db_path) as conn:
            columns = [r[1] for r in conn.execute("PRAGMA table_info(ad_stats)")]
            dump = json.dumps(conn.execute("SELECT * FROM ad_stats").fetchall())
        self.assertNotIn("user_id", columns)
        self.assertNotIn("free_user", dump)

    # ------------------------------------------------------------------ Awin
    def test_awin_client_uses_documented_endpoints_and_no_user_data(self):
        calls = []

        def opener(req, timeout):
            calls.append(req)
            if req.full_url.endswith("/linkbuilder/generate"):
                return FakeResponse(json.dumps({"url": "https://www.awin1.com/cread.php?awinmid=1&awinaffid=3118768"}).encode())
            return FakeResponse(json.dumps([{"id": 1, "name": "Shop", "primaryRegion": {"countryCode": "NL"}}]).encode())

        client = awin.AwinClient(token="secret-token", opener=opener)
        self.assertEqual(client.programmes("joined")[0]["id"], 1)
        client.generate_link(1, "https://shop.example/books", clickref="dashboard_bottom")
        self.assertEqual(calls[0].full_url, "https://api.awin.com/publishers/3118768/programmes?relationship=joined")
        self.assertEqual(calls[0].get_header("Authorization"), "Bearer secret-token")
        body = json.loads(calls[1].data)
        self.assertEqual(body, {"advertiserId": 1, "shorten": False, "destinationUrl": "https://shop.example/books",
                                "parameters": {"clickref": "dashboard_bottom"}})
        with self.assertRaises(awin.AwinError):
            client.generate_link(1, clickref="user@example.com")
        self.assertNotIn("secret-token", json.dumps(store.api_log()))

    def test_awin_errors_are_logged_and_shown_to_admin(self):
        Config.AWIN_API_TOKEN = "secret-token"

        def failing(req, timeout):
            raise urlerror.HTTPError(req.full_url, 401, "Unauthorized", {}, io.BytesIO(b'{"error":"bad secret-token"}'))

        admin = self.client(ADMIN)
        with mock.patch("app.advertising.awin.urlrequest.urlopen", failing):
            resp = admin.post("/api/admin/ads/awin/sync", json={"relationship": "joined"})
        self.assertEqual(resp.status_code, 502)
        self.assertEqual(resp.get_json()["http_status"], 401)
        log = admin.get("/api/admin/ads/state").get_json()["api_log"]
        self.assertEqual((log[0]["operation"], log[0]["ok"], log[0]["http_status"]), ("programmes", 0, 401))
        self.assertNotIn("secret-token", json.dumps(log))
        Config.AWIN_API_TOKEN = ""
        resp = admin.post("/api/admin/ads/awin/sync", json={})
        self.assertEqual(resp.get_json()["error"], "not_configured")

    def test_link_builder_only_for_joined_programmes(self):
        Config.AWIN_API_TOKEN = "t"
        admin = self.client(ADMIN)
        advertiser_id = store.save_advertiser({"name": "Shop", "awin_id": 9, "membership_status": "pending"})
        with mock.patch("app.advertising.awin.urlrequest.urlopen") as urlopen:
            resp = admin.post("/api/admin/ads/awin/link", json={"advertiser_id": advertiser_id})
        self.assertEqual(resp.get_json()["error"], "programme_not_joined")
        urlopen.assert_not_called()

    # ------------------------------------------------------------ templates
    def test_templates_have_no_ad_network_code(self):
        markup = (TEMPLATES / "_ad_slot.html").read_text(encoding="utf-8")
        script = (STATIC / "ads.js").read_text(encoding="utf-8")
        for forbidden in ("<script", "<iframe", "googlesyndication", "http://", "https://"):
            self.assertNotIn(forbidden, markup)
        for forbidden in ("innerHTML", "eval(", "document.write", "createElement(\"script\")"):
            self.assertNotIn(forbidden, script)

    def test_family_entry_points_are_plan_gated(self):
        index = (TEMPLATES / "index.html").read_text(encoding="utf-8")
        settings = (TEMPLATES / "settings.html").read_text(encoding="utf-8")
        base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
        self.assertRegex(index, r"parent_dashboard_page'\) }}\" data-family-feature")
        self.assertIn('id="family-panel" data-family-feature', settings)
        self.assertIn('querySelectorAll("[data-family-feature]")', base)
        admin = self.client(ADMIN)
        admin.post("/api/admin/plan-preview", json={"plan": "premium"})
        state = admin.get("/api/me").get_json()["plan_state"]
        self.assertTrue(state["enforced"] and not state["features"]["family"], "Premium preview locks Family UI")

    def test_lesson_ad_sits_below_navigation_only(self):
        learn = (TEMPLATES / "learn.html").read_text(encoding="utf-8")
        self.assertEqual(learn.count("_ad_slot.html"), 1)
        slot, nav = learn.index("lesson_bottom"), learn.index('id="next-btn"')
        self.assertGreater(slot, nav, "after the word navigation buttons")
        self.assertLess(slot, learn.index('id="delete-confirm-modal"'), "outside modals")
        self.assertLess(slot, learn.index('id="result-modal"'))
        self.assertNotIn("_ad_slot", (TEMPLATES / "difficult.html").read_text(encoding="utf-8"))
        lesson = next(p for p in store.list_placements("lesson"))
        self.assertEqual((lesson["key"], lesson["sizes"]["phone"]), ("lesson_bottom", ["320x50"]))
        admin = self.client(ADMIN)
        admin.post("/api/admin/plan-preview", json={"plan": "free"})
        slots = self.page(admin, page="lesson", device="phone").get_json()["slots"]
        self.assertEqual([(s["placement"], s["size"]) for s in slots], [("lesson_bottom", "320x50")])

    # ------------------------------------------------ Awin preview candidates
    def test_bundled_awin_check_imports_as_preview_only(self):
        admin = self.client(ADMIN)
        with mock.patch("urllib.request.urlopen") as urlopen:
            data = admin.post("/api/admin/ads/import-preview", json={}).get_json()
        urlopen.assert_not_called()
        self.assertEqual(sorted(data["imported"]), [8177, 9243, 18785, 32301])
        self.assertEqual(data["mode"], "preview", "OFF -> PREVIEW only, never LIVE")
        self.assertTrue(all(a["membership_status"] == "notjoined" for a in data["advertisers"]))
        self.assertTrue(all(c["preview_only"] for c in data["creatives"]))
        sizes = {p["key"]: p["sizes"] for p in data["placements"]}
        self.assertEqual(sizes["dashboard_bottom"], {"phone": ["320x50"], "tablet": ["728x90"], "desktop": ["728x90"]})
        # Admin Free simulation (ru, NL) shows a candidate as a mock-up.
        admin.post("/api/admin/plan-preview", json={"plan": "free"})
        slot = self.page(admin, device="phone", country="NL", lang="ru").get_json()["slots"][0]
        self.assertEqual(slot["render"], "mock")
        self.assertIn("notjoined", slot["advertiser"])
        self.assertNotIn("click_url", slot)
        # Re-import is idempotent.
        again = admin.post("/api/admin/ads/import-preview", json={}).get_json()
        self.assertEqual(len(again["creatives"]), 4)

    def test_preview_copy_never_goes_live_even_after_joining(self):
        self.client(ADMIN).post("/api/admin/ads/import-preview", json={})
        self.go_live()
        for advertiser in store.list_advertisers():
            store.set_membership(advertiser["id"], "joined")
        for creative in store.list_creatives():
            store.set_creative_click_url(creative["id"], "https://www.awin1.com/cread.php?awinmid=1&awinaffid=3118768")
        self.add_user("ru_user")
        self.set_subscription("ru_user", "trial", ends_in_ms=-1000)
        client = self.client("ru_user", consent="granted")
        data = client.get("/api/ads/page?page=dashboard&device=phone",
                          headers={"Accept-Language": "ru-NL"}).get_json()
        self.assertEqual(data["decision"]["serve"], "live")
        self.assertEqual(data["slots"], [])
        candidates = store.creative_candidates()
        self.assertEqual(len(candidates), 4)
        self.assertFalse(any(selection.live_ready(c) for c in candidates), "preview_only blocks LIVE")
        self.assertTrue(selection.live_ready({**candidates[0], "preview_only": False}), "only that flag blocks it")

    def test_policy_unit_matrix(self):
        settings = {"mode": "live", "live_platforms": ["web"]}
        free = policy.Viewer("u", real_plan="free", subscription_status="trial_expired")
        self.assertEqual(policy.decide(free, settings, platform="web", consent="granted", live_allowed=False).reason,
                         "live_not_allowed")
        self.assertEqual(policy.decide(free, settings, platform="telegram", consent="granted", live_allowed=True).reason,
                         "platform_disabled")
        self.assertEqual(policy.decide(free, {**settings, "mode": "corrupt"}, platform="web", consent="granted",
                                       live_allowed=True).serve, "none")


if __name__ == "__main__":
    unittest.main()
