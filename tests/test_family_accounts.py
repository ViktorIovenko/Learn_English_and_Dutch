import gc
import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from flask import Flask

from config import Config
from app import routes


class FamilyAccountsTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.db")
        Config.DB_PATH = self.db_path
        Config.SECRET_KEY = "family-test-secret"
        Config.PUBLIC_BASE_URL = "https://learn.iovenko.eu"
        self.original_admin_ids = Config.ADMIN_IDS
        self.original_bot_username = Config.BOT_USERNAME
        self.original_allow_legacy_uid_auth = Config.ALLOW_LEGACY_UID_AUTH
        Config.ADMIN_IDS = (999,)
        Config.BOT_USERNAME = "TestFamilyBot"
        Config.ALLOW_LEGACY_UID_AUTH = True
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    account_type TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    lesson TEXT,
                    number TEXT
                )
            """)
            conn.commit()
        routes._ensure_family_schema()
        self.app = Flask(
            __name__,
            template_folder=str(Path(__file__).resolve().parents[1] / "app" / "templates"),
        )
        self.app.config.update(TESTING=True, SECRET_KEY=Config.SECRET_KEY)
        self.app.context_processor(lambda: {
            "t": lambda key, **kwargs: key,
            "current_ui_language": "en",
            "i18n_catalog": {},
        })
        self.app.register_blueprint(routes.web)
        self.client = self.app.test_client()

    def tearDown(self):
        Config.ADMIN_IDS = self.original_admin_ids
        Config.BOT_USERNAME = self.original_bot_username
        Config.ALLOW_LEGACY_UID_AUTH = self.original_allow_legacy_uid_auth
        self.client = None
        self.app = None
        gc.collect()
        self.temp_dir.cleanup()

    def add_user(self, user_id: str, account_type: str = "pending") -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO users (
                    user_id, username, first_name, last_name, is_active, account_type
                ) VALUES (?, ?, ?, '', 1, ?)
                """,
                (user_id, user_id, user_id.title(), account_type),
            )
            conn.commit()

    def request(self, method: str, path: str, user_id: str, **kwargs):
        headers = dict(kwargs.pop("headers", {}))
        headers["X-User-Id"] = user_id
        return self.client.open(path, method=method, headers=headers, **kwargs)

    def test_lesson_lists_show_latest_uploaded_first(self):
        self.add_user("student", "standard")
        routes._ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT INTO words (user_id, status, lesson, number, nl, en, ru)
                VALUES ('student', 'user', ?, ?, ?, ?, ?)
                """,
                [
                    ("Older lesson", "99.1", "oud", "old", "старый"),
                    ("Latest lesson", "1.1", "nieuw", "new", "новый"),
                ],
            )
            conn.commit()

        learning = self.request("GET", "/api/lessons", "student").get_json()
        management = self.request("GET", "/api/user_lessons", "student").get_json()
        android_management = self.request(
            "GET",
            "/api/share/source_lessons",
            "student",
            headers={"X-Client": "android"},
        ).get_json()

        expected = ["Latest lesson", "Older lesson"]
        self.assertEqual(expected, [item["lesson"] for item in learning])
        self.assertEqual(expected, [item["lesson"] for item in management])
        self.assertEqual(expected, [item["lesson"] for item in android_management])
        self.assertGreater(learning[0]["upload_order"], learning[1]["upload_order"])

    def test_existing_users_migrate_to_standard(self):
        other_db = str(Path(self.temp_dir.name) / "legacy.db")
        with sqlite3.connect(other_db) as conn:
            conn.execute("""
                CREATE TABLE users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("INSERT INTO users (user_id) VALUES ('legacy')")
            conn.commit()
        original_db = Config.DB_PATH
        Config.DB_PATH = other_db
        try:
            routes._ensure_family_schema()
        finally:
            Config.DB_PATH = original_db
        with sqlite3.connect(other_db) as conn:
            account_type = conn.execute(
                "SELECT account_type FROM users WHERE user_id='legacy'"
            ).fetchone()[0]
        self.assertEqual("standard", account_type)

    def test_daily_goal_defaults_branch_by_account_type(self):
        self.add_user("child", "child")
        self.add_user("student", "standard")

        child_goal = self.request("GET", "/api/daily-goal", "child")
        standard_goal = self.request("GET", "/api/daily-goal", "student")

        self.assertEqual(200, child_goal.status_code)
        self.assertEqual(200, standard_goal.status_code)
        self.assertEqual(
            {
                "goal_type": "words",
                "goal_value": 25,
                "minimum": 5,
                "maximum": 100,
            },
            {
                key: child_goal.get_json()[key]
                for key in ("goal_type", "goal_value", "minimum", "maximum")
            },
        )
        self.assertEqual(
            {
                "goal_type": "minutes",
                "goal_value": 10,
                "minimum": 1,
                "maximum": 180,
            },
            {
                key: standard_goal.get_json()[key]
                for key in ("goal_type", "goal_value", "minimum", "maximum")
            },
        )

    def test_web_timer_is_in_page_header_not_hidden_terms_modal(self):
        self.add_user("student", "standard")
        response = self.request("GET", "/learn", "student")
        self.assertEqual(200, response.status_code)
        template = response.get_data(as_text=True)

        header_end = template.index("</header>")
        terms_modal_start = template.index('<div id="termsModal"')
        standard_timer = template.index('id="daily-timer"')
        child_goal = template.index('id="child-daily-goal"')

        self.assertLess(child_goal, header_end)
        self.assertLess(standard_timer, header_end)
        self.assertLess(header_end, terms_modal_start)
        self.assertEqual(1, template.count('id="daily-timer"'))
        self.assertIn("style.css?v=", template)

    def test_hidden_learning_mode_is_not_overridden_by_timer_layout(self):
        stylesheet = (
            Path(__file__).resolve().parents[1] / "app" / "static" / "style.css"
        ).read_text(encoding="utf-8")

        hidden_rule = stylesheet.split(".daily-timer[hidden]", 1)[1].split("}", 1)[0]
        self.assertIn("display:none!important", hidden_rule.replace(" ", ""))

    def test_web_timer_pauses_while_app_is_not_visible(self):
        self.add_user("student", "standard")
        response = self.request("GET", "/learn", "student")
        self.assertEqual(200, response.status_code)
        page = response.get_data(as_text=True)

        self.assertIn("VISIBILITY_PAUSED_KEY", page)
        self.assertIn("document.addEventListener('visibilitychange'", page)
        self.assertIn("if (document.hidden) pauseForHiddenApp()", page)
        self.assertIn("else resumeAfterHiddenApp()", page)
        self.assertIn("window.addEventListener('pagehide', pauseForHiddenApp)", page)
        self.assertIn("lastTs = Date.now()", page)

    def test_parent_links_to_child_with_signed_pairing_code(self):
        self.add_user("child")
        self.add_user("parent")

        child_type = self.request(
            "POST", "/api/account/type", "child", json={"account_type": "child"}
        )
        parent_type = self.request(
            "POST", "/api/account/type", "parent", json={"account_type": "standard"}
        )
        self.assertEqual(200, child_type.status_code)
        self.assertEqual(200, parent_type.status_code)

        pairing = self.request("GET", "/api/family/pairing-code", "child")
        self.assertEqual(200, pairing.status_code)
        pairing_data = pairing.get_json()
        token = pairing_data["token"]
        self.assertTrue(pairing_data["pairing_url"].startswith(
            Config.APP_BASE_URL.rstrip("/") + "/family/connect?code="
        ))
        qr = self.request(
            "GET",
            f"/api/family/pairing-qr.png?code={pairing_data['code']}",
            "child",
        )
        self.assertEqual(200, qr.status_code)
        self.assertEqual("image/png", qr.content_type)
        self.assertTrue(qr.data.startswith(b"\x89PNG\r\n\x1a\n"))

        linked = self.request(
            "POST", "/api/family/link", "parent", json={"token": token}
        )
        self.assertEqual(200, linked.status_code)
        self.assertTrue(linked.get_json()["is_parent"])

        parent_family = self.request("GET", "/api/family", "parent").get_json()
        child_family = self.request("GET", "/api/family", "child").get_json()
        self.assertEqual(["child"], [item["user_id"] for item in parent_family["children"]])
        self.assertEqual(["parent"], [item["user_id"] for item in child_family["parents"]])

    def test_child_account_cannot_link_another_child(self):
        self.add_user("child-a", "child")
        self.add_user("child-b", "child")
        token = self.request("GET", "/api/family/pairing-code", "child-b").get_json()["token"]
        response = self.request(
            "POST", "/api/family/link", "child-a", json={"token": token}
        )
        self.assertEqual(403, response.status_code)
        self.assertEqual("child_cannot_be_parent", response.get_json()["error"])

    def test_parent_dashboard_contains_only_linked_child_statistics(self):
        self.add_user("parent", "standard")
        self.add_user("co-parent", "standard")
        self.add_user("child", "child")
        self.add_user("other-child", "child")
        routes._ensure_progress_schema()
        now_ms = int(time.time() * 1000)
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT INTO parent_child_links (parent_user_id, child_user_id) VALUES (?, ?)",
                [("parent", "child"), ("co-parent", "child")],
            )
            conn.executemany(
                "INSERT INTO words (user_id, lesson) VALUES (?, ?)",
                [("child", "Animals"), ("child", "Animals"), ("other-child", "Hidden")],
            )
            events = [
                ("child", "answer_ok", 1, 2),
                ("child", "answer_fail", 1, 2),
                ("other-child", "answer_ok", 1, 1),
            ]
            for index, (user_id, reason, passed, total) in enumerate(events):
                event_type = "word_wrong" if reason == "answer_fail" else "progress"
                payload = {
                    "type": event_type,
                    "scope": "learn",
                    "ts": now_ms + index,
                    "state": {
                        "lesson": "Animals",
                        "word_id": index + 1,
                        "passed": passed,
                        "total": total,
                        "reason": "" if event_type == "word_wrong" else reason,
                    },
                }
                conn.execute(
                    """
                    INSERT INTO progress_events (user_id, scope, event_type, event_ts, payload)
                    VALUES (?, 'learn', ?, ?, ?)
                    """,
                    (user_id, event_type, now_ms + index, json.dumps(payload)),
                )
            conn.commit()

        response = self.request(
            "GET", "/api/family/dashboard?days=30&tz_offset=120", "parent"
        )
        self.assertEqual(200, response.status_code)
        data = response.get_json()
        self.assertEqual(["child"], [item["user_id"] for item in data["children"]])
        self.assertEqual(
            ["co-parent", "parent"],
            [item["user_id"] for item in data["children"][0]["parents"]],
        )
        summary = data["children"][0]["summary"]
        self.assertEqual(2, summary["words_count"])
        self.assertEqual(1, summary["lessons_count"])
        self.assertEqual(1, summary["correct_answers"])
        self.assertEqual(1, summary["incorrect_answers"])
        self.assertEqual(50, summary["success_rate"])
        self.assertEqual(1, summary["learning_days"])
        self.assertEqual(1, summary["learning_streak_days"])
        self.assertEqual(30, len(data["children"][0]["daily"]))
        page = self.client.get("/parent")
        self.assertEqual(200, page.status_code)
        page_text = page.get_data(as_text=True)
        self.assertNotIn('id="parent-child-select"', page_text)
        self.assertIn('class="parent-child-head"', page_text)

    def test_parent_dashboard_counts_android_wrong_answers(self):
        # Android sends event_type="word_wrong" together with a non-empty
        # "reason" field, both the current "answer_fail" and the legacy
        # "answer_wrong" value from older app builds already stored in prod.
        self.add_user("parent", "standard")
        self.add_user("child", "child")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO parent_child_links (parent_user_id, child_user_id) VALUES (?, ?)",
                ("parent", "child"),
            )
            conn.commit()

        now_ms = int(time.time() * 1000)
        events = [
            {"scope": "learn", "type": "word_correct", "ts": now_ms, "state": {
                "lesson": "Animals", "word_id": 1, "reason": "answer_ok",
            }},
            {"scope": "learn", "type": "word_wrong", "ts": now_ms + 1, "state": {
                "lesson": "Animals", "word_id": 2, "reason": "answer_fail",
            }},
            {"scope": "learn", "type": "word_wrong", "ts": now_ms + 2, "state": {
                "lesson": "Animals", "word_id": 3, "reason": "answer_wrong",
            }},
        ]
        response = self.request(
            "POST", "/api/progress/sync", "child", json={"events": events}
        )
        self.assertEqual(200, response.status_code)

        response = self.request(
            "GET", "/api/family/dashboard?days=30&tz_offset=0", "parent"
        )
        self.assertEqual(200, response.status_code)
        summary = response.get_json()["children"][0]["summary"]
        self.assertEqual(1, summary["correct_answers"])
        self.assertEqual(2, summary["incorrect_answers"])
        self.assertEqual(33, summary["success_rate"])

    def test_learning_streak_uses_local_days_and_allows_today_to_be_pending(self):
        self.add_user("child", "child")
        routes._ensure_progress_schema()
        day_ms = 24 * 60 * 60 * 1000
        now_ms = int(time.time() * 1000)
        today = now_ms // day_ms
        with sqlite3.connect(self.db_path) as conn:
            for day_number in (today - 3, today - 2, today - 1):
                conn.execute(
                    """
                    INSERT INTO progress_events (user_id, scope, event_type, event_ts, payload)
                    VALUES ('child', 'learn', 'progress', ?, '{}')
                    """,
                    (day_number * day_ms + 12 * 60 * 60 * 1000,),
                )
            conn.commit()

        response = self.request("GET", "/api/learning/streak?tz_offset=0", "child")
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, response.get_json()["learning_streak_days"])

    def test_lesson_progress_counts_distinct_correct_words_per_non_ui_language(self):
        self.add_user("student", "standard")
        routes._ensure_schema()
        routes._ensure_user_language_schema()
        routes._ensure_user_settings_schema()
        routes._ensure_progress_schema()
        now_ms = int(time.time() * 1000)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE words SET en='cat', nl='kat', ru='кот' WHERE 0"
            )
            conn.executemany(
                """
                INSERT INTO words (user_id, lesson, number, en, nl, ru)
                VALUES ('student', 'Animals', ?, ?, ?, ?)
                """,
                [("1.1", "cat", "kat", "кот"), ("1.2", "dog", "hond", "собака")],
            )
            conn.executemany(
                """
                INSERT INTO user_language_preferences (user_id, priority, lang_code, updated_at)
                VALUES ('student', ?, ?, ?)
                """,
                [(0, "en", now_ms), (1, "nl", now_ms), (2, "ru", now_ms), (3, "it", now_ms)],
            )
            conn.execute(
                """
                INSERT INTO user_settings (user_id, detected_ui_language, ui_language_override, updated_at)
                VALUES ('student', 'en', 'en', ?)
                """,
                (now_ms,),
            )
            word_ids = [row[0] for row in conn.execute(
                "SELECT id FROM words WHERE user_id='student' ORDER BY number"
            )]
            events = [
                ("nl", word_ids[0]),
                ("nl", word_ids[0]),
                ("ru", word_ids[0]),
                ("ru", word_ids[1]),
                ("en", word_ids[0]),
            ]
            for index, (language, word_id) in enumerate(events):
                payload = {"scope": "learn", "type": "progress", "state": {
                    "lesson": "Animals", "lang": language, "word_id": word_id,
                    "reason": "answer_ok",
                }}
                conn.execute(
                    """
                    INSERT INTO progress_events (user_id, scope, event_type, event_ts, payload)
                    VALUES ('student', 'learn', 'progress', ?, ?)
                    """,
                    (now_ms + index, json.dumps(payload)),
                )
            conn.commit()

        response = self.request("GET", "/api/lessons", "student")
        self.assertEqual(200, response.status_code)
        progress = response.get_json()[0]["language_progress"]
        self.assertEqual(["nl", "ru"], [item["code"] for item in progress])
        self.assertEqual([1, 2], [item["learned_words"] for item in progress])
        self.assertEqual([2, 2], [item["total_words"] for item in progress])
        self.assertEqual([50, 100], [item["percent"] for item in progress])

    def test_completed_language_batteries_automatically_hide_lesson(self):
        self.add_user("student", "standard")
        routes._ensure_schema()
        routes._ensure_user_language_schema()
        routes._ensure_user_settings_schema()
        now_ms = int(time.time() * 1000)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO words (user_id, lesson, number, en, nl, ru)
                VALUES ('student', 'Animals', '1.1', 'cat', 'kat', 'кот')
                """
            )
            word_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.executemany(
                """
                INSERT INTO user_language_preferences (user_id, priority, lang_code, updated_at)
                VALUES ('student', ?, ?, ?)
                """,
                [(0, "en", now_ms), (1, "nl", now_ms), (2, "ru", now_ms)],
            )
            conn.execute(
                """
                INSERT INTO user_settings (user_id, detected_ui_language, ui_language_override, updated_at)
                VALUES ('student', 'en', 'en', ?)
                """,
                (now_ms,),
            )
            conn.commit()

        events = [
            {"scope": "learn", "type": "progress", "ts": now_ms + index, "state": {
                "lesson": "Animals", "word_id": word_id, "lang": language,
                "reason": "answer_ok",
            }}
            for index, language in enumerate(("nl", "ru"))
        ]
        response = self.request(
            "POST", "/api/progress/sync", "student", json={"events": events}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(["Animals"], response.get_json()["completed_lessons"])
        with sqlite3.connect(self.db_path) as conn:
            hidden = conn.execute(
                "SELECT hidden FROM user_lessons WHERE user_id='student' AND lesson='Animals'"
            ).fetchone()[0]
        self.assertEqual(1, hidden)

    def test_child_cannot_open_parent_dashboard_api(self):
        self.add_user("child", "child")
        response = self.request("GET", "/api/family/dashboard", "child")
        self.assertEqual(403, response.status_code)
        self.assertEqual("parent_account_required", response.get_json()["error"])

    def test_parent_sets_priority_lesson_and_child_receives_it_first(self):
        self.add_user("parent", "standard")
        self.add_user("other-parent", "standard")
        self.add_user("child", "child")
        routes._ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO parent_child_links (parent_user_id, child_user_id) VALUES (?, ?)",
                ("parent", "child"),
            )
            conn.executemany(
                """
                INSERT INTO words (
                    user_id, status, lesson, number, nl, en, ru,
                    ex_nl, ex_en, ex_ru, audio_nl, audio_en, audio_ru
                ) VALUES ('child', 'user', ?, ?, ?, ?, ?, '', '', '', '', '', '')
                """,
                [
                    ("First", "1.1", "een", "one", "один"),
                    ("Evening", "2.1", "avond", "evening", "вечер"),
                ],
            )
            conn.commit()

        routes.models.set_lesson_hidden(self.db_path, "child", "Evening", 1)
        initial_dashboard = self.request("GET", "/api/family/dashboard", "parent").get_json()
        self.assertEqual(
            ["Evening", "First"],
            [
                item["lesson"]
                for item in initial_dashboard["children"][0]["available_lessons"]
            ],
        )

        denied = self.request(
            "PUT",
            "/api/family/children/child/priority-lesson",
            "other-parent",
            json={"lesson": "Evening"},
        )
        self.assertEqual(404, denied.status_code)

        first_assignment = self.request(
            "PUT",
            "/api/family/children/child/priority-lesson",
            "parent",
            json={"lesson": "First"},
        )
        self.assertEqual(200, first_assignment.status_code)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE child_lesson_priority_history SET started_at=? WHERE child_user_id='child'",
                (int(time.time() * 1000) - 3_600_000,),
            )
            conn.commit()

        assigned = self.request(
            "PUT",
            "/api/family/children/child/priority-lesson",
            "parent",
            json={"lesson": "Evening"},
        )
        self.assertEqual(200, assigned.status_code)
        self.assertEqual("Evening", assigned.get_json()["priority_lesson"])

        dashboard = self.request("GET", "/api/family/dashboard", "parent").get_json()
        child_dashboard = dashboard["children"][0]
        self.assertEqual("Evening", child_dashboard["priority_lesson"])
        self.assertEqual(["Evening", "First"], [
            item["lesson"] for item in child_dashboard["priority_history"]
        ])
        self.assertTrue(child_dashboard["priority_history"][0]["is_active"])
        self.assertIsNone(child_dashboard["priority_history"][0]["ended_at"])
        self.assertFalse(child_dashboard["priority_history"][1]["is_active"])
        self.assertGreaterEqual(child_dashboard["priority_history"][1]["duration_seconds"], 3599)
        self.assertEqual(
            ["Evening", "First"],
            [item["lesson"] for item in child_dashboard["available_lessons"]],
        )

        child_lessons = self.request("GET", "/api/lessons", "child").get_json()
        self.assertEqual("Evening", child_lessons[0]["lesson"])
        self.assertTrue(child_lessons[0]["is_priority"])
        self.assertFalse(child_lessons[0]["hidden"])

        cleared = self.request(
            "PUT",
            "/api/family/children/child/priority-lesson",
            "parent",
            json={"lesson": ""},
        )
        self.assertEqual("", cleared.get_json()["priority_lesson"])
        cleared_dashboard = self.request("GET", "/api/family/dashboard", "parent").get_json()
        cleared_history = cleared_dashboard["children"][0]["priority_history"]
        self.assertFalse(any(item["is_active"] for item in cleared_history))
        self.assertTrue(all(item["ended_at"] for item in cleared_history))

    def test_parent_reads_linked_child_lesson_words(self):
        self.add_user("parent", "standard")
        self.add_user("child", "child")
        self.add_user("stranger", "standard")
        routes._ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO parent_child_links (parent_user_id, child_user_id) VALUES (?, ?)",
                ("parent", "child"),
            )
            conn.executemany(
                """
                INSERT INTO words (user_id, status, lesson, number, nl, en, ru)
                VALUES ('child', 'user', 'Family', ?, ?, ?, ?)
                """,
                [
                    ("1", "moeder", "mother", "мама"),
                    ("2", "vader", "father", "папа"),
                ],
            )
            conn.commit()

        response = self.request(
            "GET",
            "/api/family/children/child/lesson-words?lesson=Family",
            "parent",
        )
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertEqual(["1", "2"], [item["number"] for item in payload["items"]])
        self.assertEqual("mother", payload["items"][0]["words"]["en"])
        self.assertEqual(403, self.request(
            "GET",
            "/api/family/children/child/lesson-words?lesson=Family",
            "stranger",
        ).status_code)

    def test_parent_assigns_selected_lesson_to_linked_child(self):
        self.add_user("parent", "standard")
        self.add_user("child", "child")
        self.add_user("other-child", "child")
        routes._ensure_schema()
        routes._ensure_user_language_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO parent_child_links (parent_user_id, child_user_id) VALUES (?, ?)",
                ("parent", "child"),
            )
            conn.executemany(
                """
                INSERT INTO words (
                    user_id, status, lesson, number, nl, en, ru,
                    ex_nl, ex_en, ex_ru, audio_nl, audio_en, audio_ru
                ) VALUES (?, 'user', ?, ?, ?, ?, ?, '', '', '', '', '', '')
                """,
                [
                    ("parent", "Animals", "1.1", "de kat", "cat", "кот"),
                    ("parent", "Animals", "1.2", "de hond", "dog", "собака"),
                    ("parent", "Hidden", "2.1", "geheim", "secret", "секрет"),
                ],
            )
            conn.executemany(
                """
                INSERT INTO user_language_preferences (user_id, priority, lang_code, updated_at)
                VALUES ('child', ?, ?, 1)
                """,
                [(0, "nl"), (1, "en"), (2, "it")],
            )
            conn.executemany(
                """
                INSERT INTO user_language_preferences (user_id, priority, lang_code, updated_at)
                VALUES ('parent', ?, ?, 1)
                """,
                [(0, "nl"), (1, "en"), (2, "ru"), (3, "it")],
            )
            conn.commit()

        source = self.request("GET", "/api/share/source_lessons", "parent")
        self.assertEqual(200, source.status_code)
        source_data = source.get_json()
        self.assertEqual(
            ["nl", "en", "ru", "it"],
            [item["code"] for item in source_data["preferred_languages"]],
        )
        self.assertEqual(["child"], [item["user_id"] for item in source_data["children"]])
        self.assertEqual(
            ["nl", "en", "it"],
            [item["code"] for item in source_data["children"][0]["languages"]],
        )
        animals = next(item for item in source_data["lessons"] if item["lesson"] == "Animals")
        self.assertEqual({"nl", "en", "ru"}, {item["code"] for item in animals["languages"]})

        first_word_id = animals["words"][0]["id"]
        translated = self.request(
            "PUT",
            f"/api/words/{first_word_id}",
            "parent",
            json={"it": "il gatto", "ex_it": "Questo è **il gatto**."},
        )
        self.assertEqual(200, translated.status_code)
        refreshed = self.request("GET", "/api/share/source_lessons", "parent").get_json()
        refreshed_animals = next(item for item in refreshed["lessons"] if item["lesson"] == "Animals")
        self.assertIn("it", {item["code"] for item in refreshed_animals["languages"]})
        self.assertEqual("Questo è **il gatto**.", refreshed_animals["words"][0]["ex_it"])

        database = self.request("GET", "/api/words", "parent").get_json()
        self.assertEqual(
            ["nl", "en", "ru", "it"],
            [item["code"] for item in database["languages"]],
        )
        database_word = next(item for item in database["words"] if item["id"] == first_word_id)
        self.assertEqual("il gatto", database_word["it"])
        self.assertEqual("Questo è **il gatto**.", database_word["ex_it"])
        marked_difficult = self.request(
            "POST",
            "/api/difficult/user_set",
            "parent",
            json={"word_id": first_word_id, "difficult": 1},
        )
        self.assertEqual(200, marked_difficult.status_code)

        hidden_language = self.request(
            "POST",
            "/api/user-languages",
            "parent",
            json={"languages": ["nl", "en", "ru"]},
        )
        self.assertEqual(200, hidden_language.status_code)
        hidden_database = self.request("GET", "/api/words", "parent").get_json()
        self.assertEqual(
            ["nl", "en", "ru"],
            [item["code"] for item in hidden_database["languages"]],
        )
        hidden_word = next(item for item in hidden_database["words"] if item["id"] == first_word_id)
        self.assertNotIn("it", hidden_word)
        hidden_source = self.request("GET", "/api/share/source_lessons", "parent").get_json()
        hidden_animals = next(item for item in hidden_source["lessons"] if item["lesson"] == "Animals")
        self.assertNotIn("it", {item["code"] for item in hidden_animals["languages"]})
        hidden_difficult = self.request("GET", "/api/difficult_words_user", "parent").get_json()
        self.assertEqual(["nl", "en", "ru"], [item["code"] for item in hidden_difficult["languages"]])
        self.assertNotIn("it", hidden_difficult["items"][0])

        restored_language = self.request(
            "POST",
            "/api/user-languages",
            "parent",
            json={"languages": ["nl", "en", "ru", "it"]},
        )
        self.assertEqual(200, restored_language.status_code)
        restored_database = self.request("GET", "/api/words", "parent").get_json()
        restored_word = next(item for item in restored_database["words"] if item["id"] == first_word_id)
        self.assertEqual("il gatto", restored_word["it"])
        self.assertEqual("Questo è **il gatto**.", restored_word["ex_it"])
        restored_difficult = self.request("GET", "/api/difficult_words_user", "parent").get_json()
        self.assertEqual("il gatto", restored_difficult["items"][0]["it"])

        assigned = self.request(
            "POST",
            "/api/share/assign_child",
            "parent",
            json={"child_user_id": "child", "lessons": ["Animals"]},
        )
        self.assertEqual(200, assigned.status_code)
        self.assertEqual(2, assigned.get_json()["count"])
        with sqlite3.connect(self.db_path) as conn:
            copied = conn.execute(
                "SELECT id, lesson, nl, en, ru FROM words WHERE user_id='child' ORDER BY number"
            ).fetchall()
        self.assertEqual(
            [("Animals", "de kat", "cat", "кот"), ("Animals", "de hond", "dog", "собака")],
            [row[1:] for row in copied],
        )
        child_first_word_id = copied[0][0]
        with sqlite3.connect(self.db_path) as conn:
            mapping = conn.execute(
                """
                SELECT parent_word_id, child_word_id
                FROM shared_lesson_words
                WHERE parent_user_id='parent' AND child_user_id='child'
                ORDER BY parent_word_id
                """
            ).fetchall()
        self.assertEqual(2, len(mapping))

        parent_edit = self.request(
            "PUT",
            f"/api/words/{first_word_id}",
            "parent",
            json={"nl": "de huiskat", "ex_nl": "Dit is **de huiskat**."},
        )
        self.assertEqual(200, parent_edit.status_code)
        with sqlite3.connect(self.db_path) as conn:
            child_after_parent_edit = conn.execute(
                "SELECT nl, ex_nl FROM words WHERE id=?",
                (child_first_word_id,),
            ).fetchone()
        self.assertEqual(("de huiskat", "Dit is **de huiskat**."), child_after_parent_edit)
        child_lesson = self.request(
            "GET", "/api/lesson_words?lesson=Animals", "child"
        ).get_json()
        child_api_word = next(item for item in child_lesson["items"] if item["id"] == child_first_word_id)
        self.assertEqual("de huiskat", child_api_word["nl_word"])
        self.assertEqual("Dit is **de huiskat**.", child_api_word["nl_sentence"])

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DROP TABLE shared_lesson_words")
            conn.commit()
        routes._ensure_family_schema()
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(2, conn.execute("SELECT COUNT(*) FROM shared_lesson_words").fetchone()[0])

        child_edit = self.request(
            "PUT",
            f"/api/words/{child_first_word_id}",
            "child",
            json={"en": "house cat", "ex_en": "This is a **house cat**."},
        )
        self.assertEqual(200, child_edit.status_code)
        with sqlite3.connect(self.db_path) as conn:
            parent_after_child_edit = conn.execute(
                "SELECT en, ex_en FROM words WHERE id=?",
                (first_word_id,),
            ).fetchone()
        self.assertEqual(("house cat", "This is a **house cat**."), parent_after_child_edit)
        parent_lesson = self.request(
            "GET", "/api/lesson_words?lesson=Animals", "parent"
        ).get_json()
        parent_api_word = next(item for item in parent_lesson["items"] if item["id"] == first_word_id)
        self.assertEqual("house cat", parent_api_word["en_word"])
        self.assertEqual("This is a **house cat**.", parent_api_word["en_sentence"])

        priority = self.request(
            "PUT",
            "/api/family/children/child/priority-lesson",
            "parent",
            json={"lesson": "Animals"},
        )
        self.assertEqual(200, priority.status_code)
        renamed = self.request(
            "POST",
            "/api/user_lessons/rename",
            "parent",
            json={"lesson": "Animals", "new_lesson": "Family animals"},
        )
        self.assertEqual(200, renamed.status_code)
        self.assertEqual(2, renamed.get_json()["affected_accounts"])

        parent_titles = [
            item["lesson"] for item in self.request("GET", "/api/lessons", "parent").get_json()
        ]
        child_titles = [
            item["lesson"] for item in self.request("GET", "/api/lessons", "child").get_json()
        ]
        self.assertIn("Family animals", parent_titles)
        self.assertIn("Family animals", child_titles)
        self.assertNotIn("Animals", parent_titles)
        self.assertNotIn("Animals", child_titles)
        renamed_source = self.request("GET", "/api/share/source_lessons", "parent").get_json()
        source_lesson = next(
            item for item in renamed_source["lessons"] if item["lesson"] == "Family animals"
        )
        self.assertTrue(source_lesson["editable_name"])
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(
                "Family animals",
                conn.execute(
                    "SELECT lesson FROM child_lesson_priorities WHERE child_user_id='child'"
                ).fetchone()[0],
            )
            self.assertEqual(
                2,
                conn.execute(
                    "SELECT COUNT(*) FROM shared_lesson_words WHERE lesson='Family animals'"
                ).fetchone()[0],
            )

        denied = self.request(
            "POST",
            "/api/share/assign_child",
            "parent",
            json={"child_user_id": "other-child", "lessons": ["Animals"]},
        )
        self.assertEqual(403, denied.status_code)
        self.assertEqual("child_not_linked", denied.get_json()["error"])

    def test_web_pairing_rejects_sixth_adult(self):
        self.add_user("child", "child")
        for index in range(1, 7):
            self.add_user(f"parent-{index}", "standard")
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT INTO parent_child_links (parent_user_id, child_user_id) VALUES (?, 'child')",
                [(f"parent-{index}",) for index in range(1, 6)],
            )
            conn.commit()
        token = self.request(
            "GET", "/api/family/pairing-code", "child"
        ).get_json()["token"]
        response = self.request(
            "POST", "/api/family/link", "parent-6", json={"token": token}
        )
        self.assertEqual(409, response.status_code)
        self.assertEqual("parent_limit_reached", response.get_json()["error"])

    def test_admin_unlinks_only_selected_adult_child_pair(self):
        self.add_user("child", "child")
        self.add_user("parent-a", "standard")
        self.add_user("parent-b", "standard")
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT INTO parent_child_links (parent_user_id, child_user_id) VALUES (?, 'child')",
                [("parent-a",), ("parent-b",)],
            )
            conn.commit()
        with self.client.session_transaction() as session_data:
            session_data["is_auth"] = True
            session_data["tg_user_id"] = "999"

        page = self.client.get("/admin/users")
        self.assertEqual(200, page.status_code)
        page_text = page.get_data(as_text=True)
        self.assertIn("Тип аккаунта", page_text)
        self.assertIn("Семейные связи", page_text)
        self.assertIn("Открепить", page_text)

        response = self.client.post(
            "/api/admin/unlink_family",
            json={"parent_user_id": "parent-a", "child_user_id": "child"},
        )
        self.assertEqual(200, response.status_code)
        with sqlite3.connect(self.db_path) as conn:
            links = conn.execute(
                "SELECT parent_user_id, child_user_id FROM parent_child_links"
            ).fetchall()
        self.assertEqual([("parent-b", "child")], links)

    def test_child_authenticated_api_merges_canonical_family_lesson_without_copying(self):
        self.add_user("parent", "standard")
        self.add_user("child", "child")
        self.add_user("stranger", "standard")
        routes._ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            routes._ensure_word_language_columns(conn, ["it", "fr"])
            conn.execute("INSERT INTO parent_child_links(parent_user_id, child_user_id) VALUES ('parent', 'child')")
            conn.executemany(
                "INSERT INTO words(user_id,status,lesson,number,nl,en,ru,it,fr) VALUES(?,?,?,?,?,?,?,?,?)",
                [
                    ("child", "user", "Old child lesson", "1.1", "oud", "old", "старый", "vecchio", "vieux"),
                    ("parent", "user", "17.1 Ik ben heel handig", "17.1", "aannemen", "to hire", "нанимать", "assumere", "embaucher"),
                    ("parent", "user", "17.1 Ik ben heel handig", "17.2", "behulpzaam", "helpful", "полезный", "utile", "serviable"),
                ],
            )
            conn.execute("INSERT INTO family_lesson_assignments(parent_user_id,child_user_id,lesson,created_at) VALUES ('parent','child','17.1 Ik ben heel handig',1)")
            conn.execute("INSERT INTO child_lesson_priorities(child_user_id,lesson,parent_user_id,updated_at) VALUES ('child','17.1 Ik ben heel handig','parent',1)")
            conn.commit()

        lessons = self.request("GET", "/api/lessons", "child").get_json()
        self.assertEqual("17.1 Ik ben heel handig", lessons[0]["lesson"])
        self.assertTrue(lessons[0]["is_priority"])
        self.assertIn("Old child lesson", [item["lesson"] for item in lessons])
        words = self.request("GET", "/api/lesson_words?lesson=17.1%20Ik%20ben%20heel%20handig", "child").get_json()
        self.assertEqual(2, len(words["items"]))
        self.assertEqual("assumere", words["items"][0]["it"])
        self.assertEqual("embaucher", words["items"][0]["fr"])
        forbidden = self.request("GET", "/api/lesson_words?lesson=17.1%20Ik%20ben%20heel%20handig", "stranger")
        self.assertEqual(404, forbidden.status_code)


if __name__ == "__main__":
    unittest.main()
