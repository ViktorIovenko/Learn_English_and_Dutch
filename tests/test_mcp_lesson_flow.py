"""MCP scenarios: per-user lesson completion, child assignment with language
top-up, personal difficult words, and the last-5 active lessons archive."""
import gc
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from config import Config
from app import ai_platform, routes
from app import mcp_service
from app.mcp_service import McpServiceError, ensure_mcp_schema, execute


PARENT, LEA, ROBERT = "parent", "lea", "robert"
NAMES = {"nl": "Dutch", "en": "English", "ru": "Russian", "it": "Italian", "fr": "French"}
CODES = {name: code for code, name in NAMES.items()}


def _fake_adapter(operation):
    """Independent translation and example provider operations."""
    if operation == "translate_word":
        return lambda **request: {"text": f"{request['text']}[{request['target_language']}]"}
    if operation == "generate_examples":
        return lambda **request: {f"ex_{code}": f"{request['examples'].get('nl',request['words'].get('nl','word'))}[{code}]" for code in request['languages']}
    return None


WORDS = [
    {"nl": "de hond", "en": "the dog", "ru": "собака", "ex_nl": "De hond blaft.", "ex_en": "The dog barks.", "ex_ru": "Собака лает."},
    {"nl": "de kat", "en": "the cat", "ru": "кошка", "ex_nl": "De kat slaapt.", "ex_en": "The cat sleeps.", "ex_ru": "Кошка спит."},
    {"nl": "het paard", "en": "the horse", "ru": "лошадь", "ex_nl": "Het paard rent.", "ex_en": "The horse runs.", "ex_ru": "Лошадь бежит."},
    {"nl": "de koe", "en": "the cow", "ru": "корова", "ex_nl": "De koe eet gras.", "ex_en": "The cow eats grass.", "ex_ru": "Корова ест траву."},
    {"nl": "de vogel", "en": "the bird", "ru": "птица", "ex_nl": "De vogel zingt.", "ex_en": "The bird sings.", "ex_ru": "Птица поёт."},
]


class McpLessonFlowTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "flow.db")
        self.original = {key: getattr(Config, key) for key in ("DB_PATH", "SECRET_KEY", "ADMIN_IDS", "MCP_INTERNAL_TOKEN", "AI_PLATFORM_BASE_URL")}
        Config.DB_PATH = self.db_path
        Config.SECRET_KEY = "flow-secret"
        Config.ADMIN_IDS = (999,)
        Config.MCP_INTERNAL_TOKEN = "internal"
        Config.AI_PLATFORM_BASE_URL = ""
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
                INSERT INTO users(user_id,username,first_name,account_type) VALUES
                    ('parent','parent','Parent','standard'),('lea','lea','Lea','child'),('robert','robert','Robert','child');
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
            conn.executemany("INSERT INTO parent_child_links(parent_user_id,child_user_id) VALUES(?,?)", [(PARENT, LEA), (PARENT, ROBERT)])
            rows = []
            for user, languages in ((PARENT, ["nl", "en", "ru"]), (LEA, ["nl", "en", "ru", "it"]), (ROBERT, ["nl", "en", "ru", "fr"])):
                rows.extend((user, index + 1, code, 0) for index, code in enumerate(languages))
            conn.executemany("INSERT INTO user_language_preferences(user_id,priority,lang_code,updated_at) VALUES(?,?,?,?)", rows)
            conn.commit()
        self.language_lookups: list[str] = []
        real_languages = routes._get_user_languages

        def spy(user_id):
            self.language_lookups.append(str(user_id))
            return real_languages(user_id)
        self.spy_patch = mock.patch.object(routes, "_get_user_languages", side_effect=spy)
        self.spy_patch.start()

    def tearDown(self):
        self.spy_patch.stop()
        for key, value in self.original.items():
            setattr(Config, key, value)
        gc.collect()
        self.temp_dir.cleanup()

    # -- helpers ----------------------------------------------------------
    def _create_parent_lesson(self, title="Animals", key="create-animals-1"):
        return execute("lesson_create_complete", PARENT, ["learning.write"], {"title": title, "words": WORDS, "idempotency_key": key, "use_cloud": False})

    def _lesson_words(self, owner, title):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute("SELECT * FROM words WHERE user_id=? AND lesson=? ORDER BY id", (owner, title))]

    def _active(self, child):
        return [item["lesson"] for item in execute("family_child_active_lessons_list", PARENT, ["family.read"], {"child_user_id": child})["items"]]

    def _archived(self, child):
        return [item["lesson"] for item in execute("family_child_archived_lessons_list", PARENT, ["family.read"], {"child_user_id": child})["items"]]

    # -- Test 1: create for the parent only -------------------------------
    def test_add_and_file_import_accept_partial_content_and_report_missing(self):
        for operation, scopes in (("words_add", ["learning.write"]), ("lesson_import_file", ["learning.files", "learning.write"])):
            for user in (PARENT, LEA):
                with self.subTest(operation=operation, user=user):
                    result = execute(operation, user, scopes, {"lesson_title": "Import", "words": [WORDS[0], {"nl": "tafel", "ru": "стол"}], "idempotency_key": operation + "-partial"})
                    self.assertEqual(2, result["created"])
                    self.assertTrue(result["pending"])
        result = execute("words_add", PARENT, ["learning.write"], {"lesson_title": "Import", "words": WORDS, "idempotency_key": "strict-import"})
        self.assertEqual(5, result["created"])

    def test_incomplete_bypass_and_missing_title_are_rejected(self):
        with self.assertRaises(McpServiceError) as error:
            execute("lesson_create_complete", PARENT, ["learning.write"], {"title": "Incomplete", "words": [{"nl": "tafel"}], "save_incomplete": True, "use_cloud": False, "idempotency_key": "no-bypass"})
        self.assertEqual("LESSON_INCOMPLETE", error.exception.code)
        self.assertEqual([], self._lesson_words(PARENT, "Incomplete"))
        for title in ("", "   ", "TODO"):
            with self.assertRaises(McpServiceError):
                execute("words_add", PARENT, ["learning.write"], {"lesson_title": title, "words": WORDS, "idempotency_key": "title-required"})

    def test_legacy_assignment_requires_child_languages(self):
        self._create_parent_lesson()
        for operation, target in (("family_child_lesson_assign", {"child_user_id": LEA}), ("family_children_lesson_assign", {"child_user_ids": [LEA, ROBERT]})):
            with self.assertRaises(McpServiceError) as error:
                execute(operation, PARENT, ["family.write"], {**target, "lesson_title": "Animals", "idempotency_key": "strict-assignment"})
            self.assertEqual("LESSON_INCOMPLETE", error.exception.code)
        self.assertEqual([], self._active(LEA))
        self.assertEqual([], self._active(ROBERT))

    def test_appending_to_assigned_lesson_reuses_child_languages_on_server(self):
        self._create_parent_lesson()
        fills = [{"word_id": word["id"], "fields": {"it": "animale", "ex_it": "Un animale."}} for word in self._lesson_words(PARENT, "Animals")]
        execute("lesson_assign_complete", PARENT, ["family.write"], {"child_user_id": LEA, "lesson_title": "Animals", "word_fills": fills, "use_cloud": False, "idempotency_key": "assign-strict"})
        result = execute("words_add", PARENT, ["learning.write"], {"lesson_title": "Animals", "words": [WORDS[0]], "idempotency_key": "append-strict"})
        self.assertEqual(1, result["created"])
        self.assertEqual(6, len(self._lesson_words(PARENT, "Animals")))
        self.assertTrue(self._lesson_words(PARENT, "Animals")[-1]["it"])

    def test_file_import_requires_title(self):
        from mcp_gateway.file_import import FileImportError, parse_words
        with self.assertRaises(FileImportError):
            parse_words(b"nl,ru\nhond,dog\n", file_name="animals.csv")
        title, words = parse_words(b"nl,ru\nhond,dog\n", lesson_title="Animals")
        self.assertEqual("Animals", title)
        self.assertEqual(1, len(words))

    def test_1_create_complete_lesson_for_parent_uses_only_parent_languages(self):
        result = self._create_parent_lesson()
        self.assertEqual("COMPLETE", result["status"])
        self.assertTrue(result["saved"])
        self.assertEqual(5, result["created_words"])
        self.assertEqual(["nl", "en", "ru"], result["validation"]["required_languages"])
        self.assertEqual(5, result["validation"]["complete_word_count"])
        self.assertEqual({PARENT}, set(self.language_lookups), "children's languages must not be requested")
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(0, conn.execute("SELECT COUNT(*) FROM family_lesson_assignments").fetchone()[0])
        # an incomplete lesson is not persisted
        with self.assertRaises(McpServiceError) as incomplete:
            execute("lesson_create_complete", PARENT, ["learning.write"], {"title": "Broken", "words": [{"nl": "de tafel", "en": "the table"}], "idempotency_key": "create-broken-1", "use_cloud": False})
        self.assertEqual("LESSON_INCOMPLETE", incomplete.exception.code)
        validation = incomplete.exception.details["validation"]
        self.assertEqual("INCOMPLETE", validation["status"])
        self.assertIn("ru", validation["missing_languages"])
        self.assertEqual({"ru", "ex_nl", "ex_en", "ex_ru"}, {item["field"] for item in validation["missing_fields"]})
        self.assertEqual([], self._lesson_words(PARENT, "Broken"))
        with self.assertRaises(McpServiceError) as not_found:
            execute("lesson_get", PARENT, ["learning.read"], {"lesson_title": "Broken"})
        self.assertEqual("LESSON_NOT_FOUND", not_found.exception.code)

    # -- Test 2: assign to Lea (needs IT) ---------------------------------
    def test_2_assign_to_lea_adds_only_italian_and_validates_for_lea(self):
        self._create_parent_lesson()
        self.language_lookups.clear()
        # without fills and without cloud: refused, missing fields listed
        with self.assertRaises(McpServiceError) as incomplete:
            execute("lesson_assign_complete", PARENT, ["family.write"], {"child_user_id": LEA, "lesson_title": "Animals", "idempotency_key": "assign-lea-0", "use_cloud": False})
        self.assertEqual("LESSON_INCOMPLETE", incomplete.exception.code)
        validation = incomplete.exception.details["validation"]
        self.assertEqual(LEA, validation["user_id"])
        self.assertEqual(["it"], validation["missing_languages"])
        self.assertEqual(["nl", "en", "ru", "it"], validation["required_languages"])
        self.assertEqual(10, len(validation["missing_fields"]))  # 5 words × (it + ex_it)
        self.assertEqual([], self._active(LEA))
        # cloud fills only the Italian gap
        calls = []

        def counting(operation):
            provider = _fake_adapter(operation)
            if not provider:
                return None
            def call(**request):
                calls.append((operation,request))
                return provider(**request)
            return call
        Config.AI_PLATFORM_BASE_URL = "https://ai.example"
        with mock.patch("app.content_service.adapter", side_effect=counting), mock.patch.object(routes, "_record_translation_request_usage"):
            result = execute("lesson_assign_complete", PARENT, ["family.write"], {"child_user_id": LEA, "lesson_title": "Animals", "idempotency_key": "assign-lea-1"})
        self.assertTrue(result["assigned"])
        self.assertEqual("COMPLETE", result["validation"]["status"])
        self.assertEqual(10, len(calls))
        self.assertEqual({"it"}, {request["target_language"] for operation,request in calls if operation=="translate_word"})
        self.assertTrue(all(request["languages"]==["it"] for operation,request in calls if operation=="generate_examples"))
        self.assertEqual(5, result["fill"]["cloud"]["filled_fields"] // 2)
        self.assertEqual({PARENT: 0, LEA: self.language_lookups.count(LEA), ROBERT: 0}, {user: self.language_lookups.count(user) for user in (PARENT, LEA, ROBERT)})
        for word in self._lesson_words(PARENT, "Animals"):
            self.assertEqual(f"{word['nl']}[it]", word["it"])
            self.assertEqual(f"{word['ex_nl']}[it]", word["ex_it"])
            self.assertEqual("", word.get("fr") or "", "French must not be pre-filled for a user not being assigned")
        self.assertEqual(["Animals"], self._active(LEA))
        self.assertEqual(5, result["active_limit"])
        self.assertEqual(["Animals"], [item["lesson"] for item in routes.get_visible_lessons_for_user(LEA)])
        # re-validation for Lea is COMPLETE, and nothing is regenerated for her on repeat
        with mock.patch("app.content_service.adapter", side_effect=AssertionError("must not be called")):
            again = execute("validate_lesson_for_user", PARENT, ["learning.read", "family.read"], {"lesson_title": "Animals", "child_user_id": LEA})
        self.assertEqual("COMPLETE", again["status"])
        with self.assertRaises(McpServiceError) as scope:
            execute("validate_lesson_for_user", PARENT, ["learning.read"], {"lesson_title": "Animals", "child_user_id": LEA})
        self.assertEqual("INSUFFICIENT_SCOPE", scope.exception.code)

    # -- Test 3: assign to Robert (needs FR only) --------------------------
    def test_3_assign_to_robert_adds_only_french_from_word_fills(self):
        self._create_parent_lesson()
        Config.AI_PLATFORM_BASE_URL = "https://ai.example"
        with mock.patch("app.content_service.adapter", side_effect=_fake_adapter), mock.patch.object(routes, "_record_translation_request_usage"):
            execute("lesson_assign_complete", PARENT, ["family.write"], {"child_user_id": LEA, "lesson_title": "Animals", "idempotency_key": "assign-lea-1"})
        before = self._lesson_words(PARENT, "Animals")
        self.language_lookups.clear()
        fills = [{"word_id": word["id"], "fields": {"fr": f"{word['en']} (fr)", "ex_fr": f"{word['ex_en']} (fr)", "it": "MUST NOT OVERWRITE", "nl": "MUST NOT OVERWRITE"}} for word in before]
        with mock.patch("app.content_service.adapter", side_effect=AssertionError("cloud must not be needed")):
            result = execute("lesson_assign_complete", PARENT, ["family.write"], {"child_user_id": ROBERT, "lesson_title": "Animals", "idempotency_key": "assign-robert-1", "word_fills": fills, "set_priority": True})
        self.assertTrue(result["assigned"])
        self.assertTrue(result["priority_set"])
        self.assertEqual(["nl", "en", "ru", "fr"], result["validation"]["required_languages"])
        self.assertEqual(10, result["fill"]["word_fills"]["applied"])
        self.assertEqual(10, result["fill"]["word_fills"]["skipped_existing"])
        self.assertEqual({ROBERT}, set(self.language_lookups))
        after = self._lesson_words(PARENT, "Animals")
        for old, new in zip(before, after):
            self.assertEqual(old["nl"], new["nl"])
            self.assertEqual(old["it"], new["it"])
            self.assertEqual(f"{old['en']} (fr)", new["fr"])
            self.assertEqual(f"{old['ex_en']} (fr)", new["ex_fr"])
        self.assertEqual(["Animals"], self._active(ROBERT))
        self.assertEqual("Animals", execute("family_child_active_lessons_list", PARENT, ["family.read"], {"child_user_id": ROBERT})["priority_lesson"])
        self.assertEqual(["Animals"], self._active(LEA))

    # -- Test 4: personal difficult words ---------------------------------
    def test_4_difficult_words_are_personal_per_child(self):
        self._create_parent_lesson()
        Config.AI_PLATFORM_BASE_URL = "https://ai.example"
        with mock.patch("app.content_service.adapter", side_effect=_fake_adapter), mock.patch.object(routes, "_record_translation_request_usage"):
            for child, key in ((LEA, "a-lea"), (ROBERT, "a-robert")):
                execute("lesson_assign_complete", PARENT, ["family.write"], {"child_user_id": child, "lesson_title": "Animals", "idempotency_key": f"assign-{key}-1"})
        word_id = self._lesson_words(PARENT, "Animals")[0]["id"]
        added = execute("family_child_difficult_words_add", PARENT, ["family.write"], {"child_user_id": LEA, "word_ids": [word_id]})
        self.assertEqual(1, added["updated"])
        lea_list = execute("family_child_difficult_words_list", PARENT, ["family.read"], {"child_user_id": LEA})
        self.assertEqual([word_id], [item["id"] for item in lea_list["items"]])
        self.assertEqual("parent", lea_list["items"][0]["difficult_source"])
        self.assertEqual("Animals", lea_list["items"][0]["lesson"])
        self.assertEqual([], execute("family_child_difficult_words_list", PARENT, ["family.read"], {"child_user_id": ROBERT})["items"])
        self.assertEqual([], execute("difficult_words_list", PARENT, ["learning.read"], {})["items"])
        # the child sees it in their own list and can also manage it
        self.assertEqual([word_id], [item["id"] for item in execute("difficult_words_list", LEA, ["learning.read"], {})["items"]])
        self.assertEqual([], execute("difficult_words_list", ROBERT, ["learning.read"], {})["items"])
        execute("difficult_words_add", ROBERT, ["learning.write"], {"word_ids": [word_id], "source": "auto_errors"})
        self.assertEqual("auto_errors", execute("difficult_words_list", ROBERT, ["learning.read"], {})["items"][0]["difficult_source"])
        removed = execute("family_child_difficult_words_remove", PARENT, ["family.write"], {"child_user_id": LEA, "word_ids": [word_id]})
        self.assertFalse(removed["difficult"])
        self.assertEqual([], execute("family_child_difficult_words_list", PARENT, ["family.read"], {"child_user_id": LEA})["items"])
        self.assertEqual([word_id], [item["id"] for item in execute("difficult_words_list", ROBERT, ["learning.read"], {})["items"]])
        execute("difficult_words_remove", ROBERT, ["learning.write"], {"word_ids": [word_id]})
        self.assertEqual([], execute("difficult_words_list", ROBERT, ["learning.read"], {})["items"])
        # a word from an unassigned lesson cannot be flagged for the child
        execute("lesson_create_complete", PARENT, ["learning.write"], {"title": "Private", "words": WORDS[:1], "idempotency_key": "create-private-1", "use_cloud": False})
        private_id = self._lesson_words(PARENT, "Private")[0]["id"]
        with self.assertRaises(McpServiceError) as denied:
            execute("family_child_difficult_words_add", PARENT, ["family.write"], {"child_user_id": LEA, "word_ids": [private_id]})
        self.assertEqual("FORBIDDEN", denied.exception.code)
        # error-based candidates: two wrong answers make the word a suggestion
        execute("progress_record_many", LEA, ["learning.write"], {"idempotency_key": "lea-progress-1", "items": [{"word_id": word_id, "result": "wrong"}, {"word_id": word_id, "result": "wrong"}, {"word_id": word_id, "result": "correct"}]})
        candidates = execute("family_child_difficult_words_candidates_get", PARENT, ["family.read"], {"child_user_id": LEA, "min_wrong": 2})
        self.assertEqual([word_id], candidates["suggested_word_ids"])
        self.assertEqual(2, candidates["items"][0]["errors"]["wrong"])
        self.assertEqual([], execute("family_child_difficult_words_candidates_get", PARENT, ["family.read"], {"child_user_id": ROBERT, "min_wrong": 2})["items"])

    # -- Test 5: archive / last-5 rule ------------------------------------
    def test_5_child_keeps_only_last_five_active_lessons(self):
        titles = [f"Lesson {index}" for index in range(1, 8)]
        Config.AI_PLATFORM_BASE_URL = "https://ai.example"
        with mock.patch("app.content_service.adapter", side_effect=_fake_adapter), mock.patch.object(routes, "_record_translation_request_usage"), mock.patch.object(mcp_service.time, "time", side_effect=iter(range(1_700_000_000, 1_700_100_000))):
            for index, title in enumerate(titles[:6]):
                self._create_parent_lesson(title, key=f"create-{index}")
                execute("lesson_assign_complete", PARENT, ["family.write"], {"child_user_id": LEA, "lesson_title": title, "idempotency_key": f"assign-{index}"})
            self.assertEqual(titles[5:0:-1], self._active(LEA))
            self.assertEqual(["Lesson 1"], self._archived(LEA))
            # priority is pinned: archive would otherwise drop Lesson 2
            execute("family_child_priority_lesson_set", PARENT, ["family.write"], {"child_user_id": LEA, "lesson_title": "Lesson 2"})
            word_id = self._lesson_words(PARENT, "Lesson 1")[0]["id"]
            execute("family_child_difficult_words_add", PARENT, ["family.write"], {"child_user_id": LEA, "word_ids": [word_id]})
            execute("progress_record_many", LEA, ["learning.write"], {"idempotency_key": "lea-l1", "items": [{"word_id": word_id, "result": "wrong"}]})
            self._create_parent_lesson(titles[6], key="create-6")
            result = execute("lesson_assign_complete", PARENT, ["family.write"], {"child_user_id": LEA, "lesson_title": titles[6], "idempotency_key": "assign-6"})
            self.assertEqual(["Lesson 3"], result["archived"])
            self.assertEqual(["Lesson 7", "Lesson 6", "Lesson 5", "Lesson 4", "Lesson 2"], self._active(LEA))
            self.assertEqual(["Lesson 3", "Lesson 1"], self._archived(LEA))
            self.assertEqual("Lesson 2", execute("family_child_lessons_list", PARENT, ["family.read"], {"child_user_id": LEA})["priority_lesson"])
            # archived lesson: words, progress and difficult flags are intact and readable
            self.assertEqual(5, len(self._lesson_words(PARENT, "Lesson 1")))
            self.assertEqual([word_id], [item["id"] for item in execute("family_child_difficult_words_list", PARENT, ["family.read"], {"child_user_id": LEA, "lesson_title": "Lesson 1"})["items"]])
            self.assertEqual(1, execute("progress_summary", LEA, ["learning.read"], {"days": 90, "lesson_title": "Lesson 1"})["wrong"])
            self.assertEqual(5, len(execute("family_child_lesson_words_list", PARENT, ["family.read"], {"child_user_id": LEA, "lesson_title": "Lesson 1"})["items"]))
            self.assertEqual(word_id, execute("word_get", LEA, ["learning.read"], {"word_id": word_id})["id"])
            # the child app only lists active lessons
            self.assertEqual(set(self._active(LEA)), {item["lesson"] for item in routes.get_visible_lessons_for_user(LEA)})
            # manual restore brings it back as newest and pushes the oldest non-priority lesson out
            restored = execute("family_child_lesson_restore", PARENT, ["family.write"], {"child_user_id": LEA, "lesson_title": "Lesson 1"})
            self.assertTrue(restored["restored"])
            self.assertEqual(["Lesson 4"], restored["archived"])
            self.assertEqual(["Lesson 1", "Lesson 7", "Lesson 6", "Lesson 5", "Lesson 2"], self._active(LEA))
            # manual archive of the priority lesson clears priority first
            archived = execute("family_child_lesson_archive", PARENT, ["family.write"], {"child_user_id": LEA, "lesson_title": "Lesson 2"})
            self.assertTrue(archived["priority_cleared"])
            self.assertIsNone(execute("family_child_lessons_list", PARENT, ["family.read"], {"child_user_id": LEA})["priority_lesson"])
            self.assertEqual(4, len(self._active(LEA)))
            # setting priority on an archived lesson restores it (and keeps max 5)
            execute("family_child_priority_lesson_set", PARENT, ["family.write"], {"child_user_id": LEA, "lesson_title": "Lesson 3"})
            self.assertEqual(["Lesson 3", "Lesson 1", "Lesson 7", "Lesson 6", "Lesson 5"], self._active(LEA))
            # explicit cleanup to fewer lessons keeps the priority lesson
            cleanup = execute("family_child_lessons_cleanup", PARENT, ["family.write"], {"child_user_id": LEA, "keep": 2})
            self.assertEqual(["Lesson 3", "Lesson 1"], cleanup["active"])
            self.assertEqual(["Lesson 7", "Lesson 6", "Lesson 5"], cleanup["archived"])
            # Robert's list is independent
            self.assertEqual([], self._active(ROBERT))
            # multi-child bulk assign also enforces the limit per child
            fills = [{"word_id": word["id"], "fields": {"fr": "animal", "ex_fr": "Un animal."}} for word in self._lesson_words(PARENT, "Lesson 4")]
            mcp_service._apply_word_fills(PARENT, "Lesson 4", fills)
            bulk = execute("family_children_lesson_assign", PARENT, ["family.write"], {"child_user_ids": [LEA, ROBERT], "lesson_title": "Lesson 4", "idempotency_key": "bulk-1"})
            self.assertEqual({LEA: [], ROBERT: []}, bulk["archived"])
            self.assertEqual(["Lesson 4", "Lesson 3", "Lesson 1"], self._active(LEA))
            self.assertEqual(["Lesson 4"], self._active(ROBERT))


if __name__ == "__main__":
    unittest.main()
