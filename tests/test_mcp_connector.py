import base64
import gc
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from flask import Flask

from config import Config
from app import routes
from app.mcp_api import mcp_api
from app.mcp_service import McpServiceError, ensure_mcp_schema, execute


class McpConnectorTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "mcp.db")
        self.original = {
            "DB_PATH": Config.DB_PATH,
            "SECRET_KEY": Config.SECRET_KEY,
            "ADMIN_IDS": Config.ADMIN_IDS,
            "MCP_INTERNAL_TOKEN": Config.MCP_INTERNAL_TOKEN,
            "MCP_PUBLIC_URL": Config.MCP_PUBLIC_URL,
            "MCP_ISSUER_URL": Config.MCP_ISSUER_URL,
        }
        Config.DB_PATH = self.db_path
        Config.SECRET_KEY = "mcp-test-secret"
        Config.ADMIN_IDS = (999,)
        Config.MCP_INTERNAL_TOKEN = "internal-test-token"
        Config.MCP_PUBLIC_URL = "https://learn.iovenko.eu/mcp"
        Config.MCP_ISSUER_URL = "https://learn.iovenko.eu"
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE users (
                    user_id TEXT PRIMARY KEY, username TEXT, first_name TEXT,
                    last_name TEXT, is_active INTEGER NOT NULL DEFAULT 1,
                    account_type TEXT NOT NULL DEFAULT 'standard',
                    google_id TEXT, google_email TEXT
                );
                CREATE TABLE words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'user', lesson TEXT, number TEXT,
                    nl TEXT, en TEXT, ru TEXT, ex_nl TEXT, ex_en TEXT, ex_ru TEXT,
                    audio_nl TEXT, audio_en TEXT, audio_ru TEXT, difficult INTEGER DEFAULT 0,
                    updated_at INTEGER
                );
                CREATE UNIQUE INDEX u_words_user_lesson_number ON words(user_id,lesson,number);
                INSERT INTO users(user_id,username,first_name) VALUES
                    ('alice','alice','Alice'),('bob','bob','Bob'),('999','admin','Admin');
                INSERT INTO words(user_id,status,lesson,number,nl,en,ru) VALUES
                    ('alice','user','Travel','1.1','reis','trip','поездка'),
                    ('bob','user','Private','1.1','geheim','secret','секрет');
                """
            )
            conn.commit()
        routes._ensure_schema()
        routes._ensure_progress_schema()
        routes._ensure_daily_goal_schema()
        routes._ensure_user_language_schema()
        routes._ensure_user_settings_schema()
        routes._ensure_family_schema()
        routes._ensure_subscription_schema()
        ensure_mcp_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT INTO user_language_preferences(user_id,priority,lang_code,updated_at) VALUES(?,?,?,0)",
                [(user, priority, language) for user in ("alice", "bob") for priority, language in enumerate(("nl", "en", "ru"), 1)],
            )
            conn.execute("UPDATE words SET ex_nl='Ik maak een reis.',ex_en='I take a trip.',ex_ru='Я отправляюсь в поездку.' WHERE user_id='alice' AND lesson='Travel'")
            conn.commit()
        self.app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / "app" / "templates"))
        self.app.config.update(TESTING=True, SECRET_KEY=Config.SECRET_KEY)
        self.app.register_blueprint(mcp_api)

        # mcp_consent.html relies on the i18n context processor that
        # routes.init_app() registers in production; register the same one
        # here so the template renders exactly as it does live.
        @self.app.context_processor
        def inject_i18n():
            from app.i18n import get_catalog, translate
            language = routes._current_ui_language()
            return {
                "current_ui_language": language,
                "i18n_catalog": get_catalog(language),
                "t": lambda key, **kwargs: translate(language, key, **kwargs),
            }

        self.client = self.app.test_client()

    def tearDown(self):
        for key, value in self.original.items():
            setattr(Config, key, value)
        self.client = None
        self.app = None
        gc.collect()
        self.temp_dir.cleanup()

    def _login(self, user_id: str):
        with self.client.session_transaction() as session:
            session["tg_user_id"] = user_id
            session["is_auth"] = True

    def test_oauth_pkce_code_is_single_use_and_token_resolves_user(self):
        registered = self.client.post("/oauth/register", json={
            "client_name": "ChatGPT test",
            "redirect_uris": ["https://chatgpt.com/aip/callback"],
            "token_endpoint_auth_method": "none",
        })
        self.assertEqual(201, registered.status_code)
        client_id = registered.get_json()["client_id"]
        verifier = "v" * 64
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        query = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": "https://chatgpt.com/aip/callback",
            "state": "state-1",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "resource": Config.MCP_PUBLIC_URL,
        }
        self._login("alice")
        # No stored UI-language preference yet: the consent page must pick up
        # the browser's Accept-Language automatically instead of always
        # rendering in Russian.
        consent = self.client.get("/oauth/authorize", query_string=query, headers={"Accept-Language": "ru"})
        self.assertEqual(200, consent.status_code)
        consent_html = consent.get_data(as_text=True)
        self.assertIn('lang="ru"', consent_html)
        self.assertIn("mcp-icon-small.png", consent_html)
        self.assertIn("Разрешить подключение", consent_html)
        self.assertIn("Просмотр данных обучения", consent_html)
        consent_en = self.client.get("/oauth/authorize", query_string=query, headers={"Accept-Language": "en"})
        consent_en_html = consent_en.get_data(as_text=True)
        self.assertIn('lang="en"', consent_en_html)
        self.assertIn("Allow connection", consent_en_html)
        self.assertIn("View learning data", consent_en_html)
        approved = self.client.post(
            "/oauth/authorize",
            data={**query, "decision": "allow", "granted_scope": ["learning.read"]},
        )
        self.assertEqual(302, approved.status_code)
        code = parse_qs(urlparse(approved.location).query)["code"][0]
        token_form = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "redirect_uri": query["redirect_uri"],
            "code_verifier": verifier,
            "resource": Config.MCP_PUBLIC_URL,
        }
        token_response = self.client.post("/oauth/token", data=token_form)
        self.assertEqual(200, token_response.status_code)
        self.assertEqual("learning.read learning.write family.read family.write", token_response.get_json()["scope"])
        access_token = token_response.get_json()["access_token"]
        reused = self.client.post("/oauth/token", data=token_form)
        self.assertEqual(400, reused.status_code)
        resolved = self.client.post(
            "/api/internal/mcp/resolve",
            headers={"Authorization": "Bearer internal-test-token", "X-MCP-Access-Token": access_token},
        )
        self.assertEqual("alice", resolved.get_json()["grant"]["user_id"])
        status = self.client.get("/api/mcp/user")
        self.assertTrue(status.get_json()["connected"])
        self.assertFalse(status.get_json()["google_account"]["linked"])
        disabled = self.client.post("/api/mcp/user", json={"enabled": False})
        self.assertFalse(disabled.get_json()["enabled"])
        self.assertEqual(403, self.client.get("/oauth/authorize", query_string=query).status_code)
        rejected = self.client.post(
            "/api/internal/mcp/resolve",
            headers={"Authorization": "Bearer internal-test-token", "X-MCP-Access-Token": access_token},
        )
        self.assertEqual(401, rejected.status_code)
        paused = self.client.get("/api/mcp/user").get_json()
        self.assertEqual("paused", paused["state"])
        self.client.post("/api/mcp/user", json={"enabled": True})
        restored = self.client.post(
            "/api/internal/mcp/resolve",
            headers={"Authorization": "Bearer internal-test-token", "X-MCP-Access-Token": access_token},
        )
        self.assertEqual(200, restored.status_code)
        revoked = self.client.post("/api/mcp/user/revoke-all")
        self.assertEqual(1, revoked.get_json()["revoked"])
        self.assertFalse(self.client.get("/api/mcp/user").get_json()["connected"])

    def test_unauthenticated_consent_returns_to_the_same_oauth_request_after_google_login(self):
        registered = self.client.post("/oauth/register", json={
            "client_name": "ChatGPT test",
            "redirect_uris": ["https://chatgpt.com/aip/callback"],
            "token_endpoint_auth_method": "none",
        })
        client_id = registered.get_json()["client_id"]
        query = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": "https://chatgpt.com/aip/callback",
            "state": "state-1",
            "code_challenge": "x" * 43,
            "code_challenge_method": "S256",
            "resource": Config.MCP_PUBLIC_URL,
        }

        consent = self.client.get("/oauth/authorize", query_string=query)

        self.assertEqual(401, consent.status_code)
        self.assertIn('href="/auth/google?next=%2Foauth%2Fauthorize%3F', consent.get_data(as_text=True))

    def test_word_ownership_is_enforced(self):
        own = execute("words_search", "alice", ["learning.read"], {"query": "trip"})
        self.assertEqual(1, len(own["items"]))
        with self.assertRaises(McpServiceError) as denied:
            execute("word_get", "alice", ["learning.read"], {"word_id": 2})
        self.assertEqual("FORBIDDEN", denied.exception.code)

    def test_admin_subscription_scope_requires_real_superuser(self):
        with self.assertRaises(McpServiceError) as denied:
            execute("subscriptions_list", "alice", ["subscriptions.admin"], {})
        self.assertEqual("ADMIN_REQUIRED", denied.exception.code)
        result = execute("subscriptions_list", "999", ["subscriptions.admin"], {"limit": 10})
        self.assertEqual(3, len(result["items"]))

    def test_admin_directory_analytics_and_manual_access_are_server_protected_and_audited(self):
        with self.assertRaises(McpServiceError) as denied:
            execute("users_list", "alice", ["users.admin"], {"limit": 10})
        self.assertEqual("ADMIN_REQUIRED", denied.exception.code)

        users = execute("users_list", "999", ["users.admin"], {"limit": 10})
        self.assertEqual(3, len(users["items"]))
        self.assertEqual("alice", execute("users_search", "999", ["users.admin"], {"query": "alice"})["items"][0]["user_id"])
        card = execute("admin_user_get", "999", ["users.admin"], {"user_id": "alice"})
        self.assertEqual("alice", card["user_id"])
        self.assertIn("learning", card)
        self.assertEqual(0, execute("admin_user_progress_get", "999", ["analytics.admin"], {"user_id": "alice", "days": 30})["attempts"])
        self.assertIn("total_users", execute("admin_analytics_summary", "999", ["analytics.admin"], {"days": 30})["users"])

        granted = execute("subscription_grant_access", "999", ["subscriptions.admin"], {"user_id": "alice", "confirm": True})
        self.assertTrue(granted["granted"])
        audit = execute("admin_audit_log_list", "999", ["subscriptions.admin"], {"limit": 10})
        self.assertEqual("subscription_manual_grant", audit["items"][0]["action"])

    def test_words_add_is_idempotent(self):
        params = {
            "lesson_title": "Food",
            "words": [{"nl": "brood", "en": "bread", "ru": "хлеб", "ex_nl": "Ik eet brood.", "ex_en": "I eat bread.", "ex_ru": "Я ем хлеб."}],
            "idempotency_key": "same-request-123",
        }
        first = execute("words_add", "alice", ["learning.write"], params)
        second = execute("words_add", "alice", ["learning.write"], params)
        self.assertEqual(first, second)
        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM words WHERE user_id='alice' AND lesson='Food'").fetchone()[0]
        self.assertEqual(1, count)

    def test_write_scope_allows_word_and_sentence_updates_only_for_owner(self):
        created = execute("lesson_create", "alice", ["learning.write"], {
            "title": "B1 Work", "idempotency_key": "create-work-lesson-1",
        })
        self.assertEqual("B1 Work", created["lesson"])
        renamed = execute("lesson_rename", "alice", ["learning.write"], {
            "lesson_title": "B1 Work", "new_title": "B1 Work and Career",
        })
        self.assertEqual("B1 Work and Career", renamed["lesson"])
        added = execute("words_add", "alice", ["learning.write"], {
            "lesson_title": "B1 Work and Career",
            "words": [{"nl": "de meterstand", "en": "meter reading", "ru": "показания счетчика", "ex_nl": "De meterstand is hoog.", "ex_en": "The meter reading is high.", "ex_ru": "Показания счетчика высокие."}],
            "idempotency_key": "add-work-word-001",
        })
        self.assertEqual(1, added["created"])
        word = execute("words_search", "alice", ["learning.read"], {"query": "meterstand"})["items"][0]
        updated = execute("word_update", "alice", ["learning.write"], {
            "word_id": word["id"], "fields": {"ru": "показания счётчика", "ex_nl": "Ik noteer de meterstand."},
        })
        self.assertEqual("показания счётчика", updated["ru"])
        self.assertEqual("Ik noteer de meterstand.", updated["ex_nl"])
        with self.assertRaises(McpServiceError) as denied:
            execute("word_update", "bob", ["learning.write"], {"word_id": word["id"], "fields": {"ru": "чужое"}})
        self.assertEqual("FORBIDDEN", denied.exception.code)
        with self.assertRaises(McpServiceError) as denied_scope:
            execute("words_add", "alice", ["learning.read"], {"lesson_title": "B1 Work and Career", "words": [{"nl": "werk"}], "idempotency_key": "read-only-write-001"})
        self.assertEqual("INSUFFICIENT_SCOPE", denied_scope.exception.code)

    def test_family_child_access_requires_link(self):
        with self.assertRaises(McpServiceError) as denied:
            execute("family_child_progress_get", "alice", ["family.read"], {"child_user_id": "bob", "days": 7})
        self.assertEqual("CHILD_NOT_LINKED", denied.exception.code)

    def test_parent_assignment_uses_live_canonical_words_without_child_copies(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO parent_child_links(parent_user_id,child_user_id) VALUES('alice','bob')")
            conn.commit()
        assigned = execute("family_child_lesson_assign", "alice", ["family.write"], {
            "child_user_id": "bob", "lesson_title": "Travel", "idempotency_key": "assign-travel-001",
        })
        self.assertTrue(assigned["assigned"])
        self.assertEqual(assigned, execute("family_child_lesson_assign", "alice", ["family.write"], {
            "child_user_id": "bob", "lesson_title": "Travel", "idempotency_key": "assign-travel-001",
        }))
        child_words = execute("family_child_lesson_words_list", "alice", ["family.read"], {
            "child_user_id": "bob", "lesson_title": "Travel",
        })
        self.assertEqual("trip", child_words["items"][0]["en"])
        word_id = child_words["items"][0]["id"]
        execute("word_update", "alice", ["learning.write"], {"word_id": word_id, "fields": {"en": "journey"}})
        after_edit = execute("family_child_lesson_words_list", "alice", ["family.read"], {
            "child_user_id": "bob", "lesson_title": "Travel",
        })
        self.assertEqual("journey", after_edit["items"][0]["en"])
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(0, conn.execute("SELECT COUNT(*) FROM words WHERE user_id='bob' AND lesson='Travel'").fetchone()[0])
        with self.assertRaises(McpServiceError) as denied:
            execute("family_child_lesson_assign", "bob", ["family.write"], {
                "child_user_id": "alice", "lesson_title": "Private", "idempotency_key": "forbidden-assign-001",
            })
        # bob is a linked child account, so family scope is refused outright
        # (live-checked) before the specific child link is even considered.
        self.assertEqual("FAMILY_SCOPE_NOT_AVAILABLE", denied.exception.code)

    def test_parent_records_child_progress_for_historical_days_and_retries_idempotently(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO parent_child_links(parent_user_id,child_user_id) VALUES('alice','bob')")
            conn.commit()
        execute("family_child_lesson_assign", "alice", ["family.write"], {
            "child_user_id": "bob", "lesson_title": "Travel", "idempotency_key": "assign-travel-progress",
        })
        with sqlite3.connect(self.db_path) as conn:
            word_id = conn.execute("SELECT id FROM words WHERE user_id='alice' AND lesson='Travel'").fetchone()[0]
        import datetime
        # Даты относительно сегодняшнего дня, чтобы окно "days=30" всегда их покрывало.
        today = datetime.datetime.now(datetime.timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        history = [today - datetime.timedelta(days=offset) for offset in range(6, 0, -1)]
        to_ms = lambda moment: int(moment.timestamp() * 1000)
        single_ts = to_ms(history[0])
        single = execute("family_child_progress_record", "alice", ["family.write"], {
            "child_user_id": "bob", "word_id": word_id, "result": "learned", "occurred_at": single_ts,
            "idempotency_key": "bob-first-day",
        })
        self.assertEqual({"stored": True, "child_user_id": "bob", "word_id": word_id, "occurred_at": single_ts}, single)
        items = [
            {"word_id": word_id, "result": "learned", "occurred_at": to_ms(moment)}
            for moment in history[1:]
        ]
        params = {"child_user_id": "bob", "items": items, "idempotency_key": "bob-fill-gap"}
        first = execute("family_child_progress_record_many", "alice", ["family.write"], params)
        second = execute("family_child_progress_record_many", "alice", ["family.write"], params)
        self.assertEqual({"stored": 5, "child_user_id": "bob"}, first)
        self.assertEqual(first, second)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT user_id,event_ts FROM progress_events WHERE scope='learn'").fetchall()
        self.assertEqual(6, len(rows))
        self.assertTrue(all(row[0] == "bob" for row in rows))
        progress = execute("family_child_progress_get", "alice", ["family.read"], {"child_user_id": "bob", "days": 30})
        daily = {item["date"]: item for item in progress["daily"]}
        for moment in history:
            self.assertEqual(1, daily[moment.strftime("%Y-%m-%d")]["correct"])

    def test_parent_cannot_record_progress_for_unlinked_child_or_unassigned_word(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO parent_child_links(parent_user_id,child_user_id) VALUES('bob','999')")
            conn.commit()
        with self.assertRaises(McpServiceError) as denied:
            execute("family_child_progress_record", "alice", ["family.write"], {
                "child_user_id": "999", "word_id": 1, "result": "learned", "idempotency_key": "foreign-child-key",
            })
        self.assertEqual("CHILD_NOT_LINKED", denied.exception.code)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO parent_child_links(parent_user_id,child_user_id) VALUES('alice','bob')")
            conn.commit()
        with self.assertRaises(McpServiceError) as denied_word:
            execute("family_child_progress_record", "alice", ["family.write"], {
                "child_user_id": "bob", "word_id": 1, "result": "learned", "idempotency_key": "unassigned-word-key",
            })
        self.assertEqual("FORBIDDEN", denied_word.exception.code)


if __name__ == "__main__":
    unittest.main()
