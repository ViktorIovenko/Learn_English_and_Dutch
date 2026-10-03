import gc
import sqlite3
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock, patch

from flask import Flask
from config import Config
from app import content_service as content, audio_gen, routes, mcp_service
from app.content_db import transaction
from bot.db import bulk_upsert_words


class PipelineFixture:

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "test.db")
        self.original_db = Config.DB_PATH
        self.original_provider = Config.CONTENT_PROVIDER_MODULE
        Config.DB_PATH = self.db
        Config.CONTENT_PROVIDER_MODULE = ""
        with closing(sqlite3.connect(self.db)) as conn:
            conn.executescript("""
                CREATE TABLE words(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT,
                    status TEXT DEFAULT 'user',lesson TEXT,number TEXT,nl TEXT,en TEXT,ru TEXT,
                    ex_nl TEXT,ex_en TEXT,ex_ru TEXT,audio_nl TEXT,audio_en TEXT,audio_ru TEXT,
                    difficult INTEGER DEFAULT 0,updated_at INTEGER);
                CREATE UNIQUE INDEX u_words_user_lesson_number ON words(user_id,lesson,number);
                CREATE TABLE users(user_id TEXT PRIMARY KEY,username TEXT,first_name TEXT,last_name TEXT,
                    is_active INTEGER DEFAULT 1,account_type TEXT DEFAULT 'standard');
                INSERT INTO users(user_id) VALUES('alice'),('bob');
            """)
            conn.commit()
        routes._ensure_schema()
        routes._ensure_user_language_schema()
        routes._ensure_family_schema()
        mcp_service.ensure_mcp_schema()
        with closing(sqlite3.connect(self.db)) as conn:
            for user in ("alice", "bob"):
                conn.executemany("INSERT INTO user_language_preferences(user_id,priority,lang_code,updated_at) VALUES(?,?,?,0)", [(user, i, lang) for i, lang in enumerate(("nl", "en", "ru"), 1)])
            conn.commit()
        self.item = {"nl": "afstappen", "en": "get off", "ru": "слезть", "ex_nl": "Ik wil **afstappen**.", "ex_en": "I want to **get off**.", "ex_ru": "Я хочу **слезть**."}

    def tearDown(self):
        Config.DB_PATH = self.original_db
        Config.CONTENT_PROVIDER_MODULE = self.original_provider
        gc.collect()
        self.temp.cleanup()

    def import_item(self, user="alice", lesson="L", item=None, **kwargs):
        return content.import_words(self.db, user, [{"lesson": lesson, "words": [item or self.item]}], **kwargs)

    def rows(self, query, parameters=()):
        with closing(sqlite3.connect(self.db)) as conn:
            return conn.execute(query, parameters).fetchall()



class ContentPipelineTests(PipelineFixture, unittest.TestCase):
    def test_telegram_upload_handlers_register_without_starting_polling(self):
        from bot.upload import register_upload_handlers
        application = Mock()
        register_upload_handlers(application)
        self.assertEqual(application.add_handler.call_count, 7)

    def test_append_one_or_many_words_keeps_existing_lesson_number(self):
        self.import_item(lesson="First")
        self.import_item(lesson="Second")
        self.import_item(lesson="First")
        content.import_words(self.db, "alice", [{"lesson": "First", "words": [self.item, self.item]}])
        self.assertEqual(self.rows("SELECT number FROM words WHERE lesson='First' ORDER BY id"), [("1.1",), ("1.2",), ("1.3",), ("1.4",)])
        self.assertEqual(self.rows("SELECT number FROM words WHERE lesson='Second'"), [("2.1",)])

    def test_missing_lesson_name_rejects_whole_batch(self):
        for words in ([self.item], [self.item, self.item]):
            with self.assertRaisesRegex(ValueError, "lesson title"):
                content.import_words(self.db, "alice", [{"lesson": "Valid", "words": words}, {"lesson": "  ", "words": words}])
            self.assertEqual(self.rows("SELECT COUNT(*) FROM words"), [(0,)])

    def test_other_user_and_other_lesson_reuse_supplied_mcp_content(self):
        with patch("app.content_service.adapter") as adapter:
            self.import_item(source="mcp")
            second = self.import_item("bob", "B", {"nl": "afstappen"})
            third = self.import_item("alice", "L5", {"nl": "afstappen"})
            adapter.assert_not_called()
        self.assertEqual(second["pending"], [])
        self.assertEqual(third["pending"], [])
        self.assertEqual(len(self.rows("SELECT * FROM words")), 3)
        self.assertEqual(self.rows("SELECT ru FROM words WHERE user_id='bob'"), [("слезть",)])
        self.assertEqual(self.rows("SELECT COUNT(*) FROM content_translations"), [(6,)])

    def test_deliberate_repeated_words_create_user_records_not_content_copies(self):
        self.import_item()
        self.import_item()
        self.assertEqual(self.rows("SELECT COUNT(*) FROM words"), [(2,)])
        self.assertEqual(self.rows("SELECT COUNT(*) FROM content_examples"), [(1,)])

    def test_missing_content_is_pending_without_an_external_provider(self):
        result = self.import_item(item={"nl": "nieuw"})
        self.assertIn("ru", result["pending"][0]["missing_fields"])
        self.assertGreater(self.rows("SELECT COUNT(*) FROM content_pending")[0][0], 0)

    def test_provider_fills_only_missing_data_once_across_users(self):
        translate = Mock(side_effect=lambda **request: {"text": {"en": "get off", "ru": "слезть"}[request["target_language"]]})
        examples = Mock(return_value={key: value for key, value in self.item.items() if key.startswith("ex_")})
        def adapter(operation):
            return {"translate_word": translate, "generate_examples": examples}.get(operation)
        with patch("app.content_service.adapter", side_effect=adapter):
            first = self.import_item(item={"nl": "afstappen"})
            second = self.import_item("bob", "B", {"nl": "afstappen"})
        self.assertEqual(first["pending"], [])
        self.assertEqual(second["pending"], [])
        self.assertEqual(translate.call_count, 2)
        self.assertEqual(examples.call_count, 1)

    def test_known_translation_is_not_regenerated(self):
        provider = Mock(return_value={})
        with patch("app.content_service.adapter", return_value=provider):
            self.import_item(item={"nl": "afstappen", "ru": "слезть"})
        word_requests = [call.kwargs for call in provider.call_args_list if "target_language" in call.kwargs]
        self.assertEqual([request["target_language"] for request in word_requests], ["en"])

    def test_concurrent_first_imports_do_not_repeat_external_operations(self):
        translate = Mock(side_effect=lambda **request: {"text": {"en": "get off", "ru": "слезть"}[request["target_language"]]})
        examples = Mock(return_value={key: value for key, value in self.item.items() if key.startswith("ex_")})
        with patch("app.content_service.adapter", side_effect=lambda operation: {"translate_word": translate, "generate_examples": examples}.get(operation)):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda user: self.import_item(user, "L", {"nl": "afstappen"}), ("alice", "bob")))
        self.assertTrue(all(not result["pending"] for result in results))
        self.assertEqual(translate.call_count, 2)
        self.assertEqual(examples.call_count, 1)

    def test_ambiguous_meanings_are_not_selected_or_sent_to_provider(self):
        self.import_item(item={"nl": "bank", "en": "bank", "ru": "банк"})
        self.import_item(lesson="Bench", item={"nl": "bank", "en": "bench", "ru": "скамейка"})
        provider = Mock()
        with patch("app.content_service.adapter", return_value=provider):
            result = content.resolve_word("bank", "nl", ["nl", "en", "ru"], examples=False)
        self.assertEqual(set(result["ambiguous_languages"]), {"en", "ru"})
        provider.assert_not_called()
        result = content.resolve_word("bank", "nl", ["nl", "en", "ru"], supplied={"ru": "банк"}, examples=False)
        self.assertEqual(result["en"], "bank")

    def test_sense_and_context_do_not_leak_between_variants(self):
        self.import_item(item={"nl": "bank", "ru": "банк", "sense": "finance"})
        result = content.resolve_word("bank", "nl", ["nl", "ru"], sense="seat", examples=False)
        self.assertNotIn("ru", result)

    def test_word_translation_does_not_invent_sentence_translation(self):
        self.import_item()
        result = content.translate_language("afstappen", "Een heel andere zin.", "nl", "ru")
        self.assertEqual(result["word"], "слезть")
        self.assertEqual(result["sentence"], "")
        self.assertEqual(result["missing_fields"], ["sentence"])

    def test_exact_parallel_sentence_is_reused_without_generation(self):
        self.import_item()
        provider = Mock()
        with patch("app.content_service.adapter", return_value=provider):
            result = content.translate_language("afstappen", self.item["ex_nl"], "Dutch", "Russian")
        self.assertEqual(result["sentence"], self.item["ex_ru"])
        provider.assert_not_called()

    def test_example_bundle_is_not_mixed_with_a_different_supplied_sentence(self):
        self.import_item()
        result = content.resolve_word("afstappen", "nl", supplied={"ex_nl": "Ik stap morgen af."})
        self.assertEqual(result["ex_nl"], "Ik stap morgen af.")
        self.assertFalse(result.get("ex_ru"))

    def test_legacy_migration_preserves_word_ids_progress_and_all_rows(self):
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute("CREATE TABLE retained_progress(word_id INTEGER, score INTEGER)")
            conn.execute("INSERT INTO words(id,user_id,lesson,number,nl,ru) VALUES(42,'alice','Old','8.1','oud','старый')")
            conn.execute("INSERT INTO retained_progress VALUES(42,9)")
            conn.commit()
        self.import_item("bob", "B", {"nl": "oud"})
        self.assertEqual(self.rows("SELECT id,number FROM words WHERE id=42"), [(42, "8.1")])
        self.assertEqual(self.rows("SELECT * FROM retained_progress"), [(42, 9)])
        self.assertEqual(self.rows("SELECT ru FROM words WHERE user_id='bob'"), [("старый",)])

    def test_import_receipt_and_rows_are_atomic_and_retries_return_same_ids(self):
        first = self.import_item(idempotency_key="one")
        second = self.import_item(idempotency_key="one")
        self.assertEqual(first, second)
        self.assertEqual(self.rows("SELECT COUNT(*) FROM words"), [(1,)])
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            self.import_item(item={"nl": "different"}, idempotency_key="one")

    def test_telegram_compatibility_uses_shared_catalog_and_allows_repeats(self):
        self.import_item(source="mcp")
        for _ in range(2):
            self.assertEqual(bulk_upsert_words(self.db, "bob", [{"lesson": "Telegram", "nl": "afstappen"}]), 1)
        self.assertEqual(self.rows("SELECT ru FROM words WHERE user_id='bob'"), [("слезть",), ("слезть",)])

    def test_web_and_installed_android_payloads_share_one_contract(self):
        app = Flask(__name__)
        app.config.update(TESTING=True, SECRET_KEY="test")
        app.register_blueprint(routes.web)
        with app.test_client() as client:
            with client.session_transaction() as session:
                session["tg_user_id"] = "alice"
                session["is_auth"] = True
            web = client.post("/api/import-words", json={"lessons": [{"lesson": "W", "words": [self.item]}]}).get_json()
            android = client.post("/api/import-words", json={"lesson": "A", "words": [{"nl": "afstappen"}]}).get_json()
        self.assertTrue(web["ok"])
        self.assertEqual(web["count"], web["imported"])
        self.assertEqual(android["imported"], 1)
        self.assertEqual(android["skipped"], 0)

    def test_mcp_partial_content_reuse_retry_and_intentional_repeat(self):
        params = {"lesson_title": "M", "words": [self.item], "idempotency_key": "mcp-one"}
        first = mcp_service._words_add("alice", params)
        self.assertEqual(first, mcp_service._words_add("alice", params))
        mcp_service._words_add("alice", {**params, "idempotency_key": "mcp-two"})
        mcp_service._words_add("bob", {**params, "words": [{"nl": "afstappen"}], "idempotency_key": "mcp-three"})
        self.assertEqual(self.rows("SELECT COUNT(*) FROM words"), [(3,)])
        self.assertEqual(self.rows("SELECT ru FROM words WHERE user_id='bob'"), [("слезть",)])

    def test_concurrent_mcp_retry_inserts_once(self):
        params = {"lesson_title": "M", "words": [self.item], "idempotency_key": "same-delivery"}
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: mcp_service._words_add("alice", params), range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(self.rows("SELECT COUNT(*) FROM words"), [(1,)])

    def test_mcp_callback_failure_rolls_back_words_and_receipt(self):
        def callback():
            self.import_item()
            raise RuntimeError("after write, before receipt")
        with self.assertRaisesRegex(RuntimeError, "after write"):
            mcp_service._idempotent("alice", "test", {"idempotency_key": "crash"}, callback)
        self.assertEqual(self.rows("SELECT COUNT(*) FROM words"), [(0,)])
        self.assertEqual(self.rows("SELECT COUNT(*) FROM mcp_idempotency"), [(0,)])

    def test_supplied_sentence_disambiguates_known_word_meanings(self):
        self.import_item(item={"nl": "bank", "en": "bank", "ru": "банк", "ex_nl": "De bank is open.", "ex_ru": "Банк открыт."})
        self.import_item(lesson="Seat", item={"nl": "bank", "en": "bench", "ru": "скамейка", "ex_nl": "Ik zit op de bank.", "ex_ru": "Я сижу на скамейке."})
        result = content.translate_language("bank", "Ik zit op de bank.", "nl", "ru")
        self.assertEqual(result["word"], "скамейка")
        self.assertEqual(result["sentence"], "Я сижу на скамейке.")

    def test_declared_cefr_level_is_required_when_requested(self):
        self.import_item(item={**self.item, "level": "B2"})
        result = content.resolve_word("afstappen", "nl", level="A1")
        self.assertEqual(result["ru"], "слезть")
        self.assertFalse(result.get("ex_nl"))

    def test_paid_usage_is_not_replayed_on_cache_hits(self):
        from app import ai_platform
        def provider(**request):
            return {"text": "слезть", "_usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13}}
        with patch("app.content_service.adapter", return_value=provider):
            first, first_usage = ai_platform.translate_word("afstappen", "nl", languages=["nl", "ru"], examples=False)
            second, second_usage = ai_platform.translate_word("afstappen", "nl", languages=["nl", "ru"], examples=False)
        self.assertEqual(first["ru"], second["ru"])
        self.assertEqual(first_usage.total_tokens, 13)
        self.assertEqual(second_usage.total_tokens, 0)
        self.assertEqual(second_usage.provider_calls, 0)

    def test_empty_provider_response_can_be_retried(self):
        provider = Mock(side_effect=[{}, {"text": "слезть"}])
        with patch("app.content_service.adapter", return_value=provider):
            first = content.resolve_word("afstappen", "nl", ["nl", "ru"], examples=False)
            second = content.resolve_word("afstappen", "nl", ["nl", "ru"], examples=False)
        self.assertIn("ru", first["missing_fields"])
        self.assertEqual(second["ru"], "слезть")
        self.assertEqual(provider.call_count, 2)

    def test_invalid_batch_rolls_back_earlier_user_records_and_catalog(self):
        with self.assertRaises(ValueError):
            content.import_words(self.db, "alice", [{"lesson": "L", "words": [self.item, {}]}])
        self.assertEqual(self.rows("SELECT COUNT(*) FROM words"), [(0,)])

    def test_migration_backup_preserves_records_and_is_repeatable(self):
        from tools.migrate_content import migrate
        self.import_item()
        first = migrate(self.db)
        second = migrate(self.db)
        self.assertTrue(first.is_file())
        self.assertTrue(second.is_file())
        with closing(sqlite3.connect(first)) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM words").fetchone()[0], 1)
        self.assertEqual(self.rows("SELECT COUNT(*) FROM words"), [(1,)])

    def test_edit_invalidates_audio_and_example_but_keeps_explicit_replacement(self):
        result = content.prepare_edit({"en": "house", "ex_en": "A house.", "audio_en": "old"}, {"en": "home"})
        self.assertEqual(result["audio_en"], "")
        self.assertEqual(result["ex_en"], "")
        explicit = content.prepare_edit({"en": "house"}, {"en": "home", "ex_en": "A home."})
        self.assertEqual(explicit["ex_en"], "A home.")


class AudioPipelineTests(PipelineFixture, unittest.TestCase):
    # Reuse fixtures, not the inherited content tests.
    def audio_patch(self):
        root = Path(self.temp.name) / "app"
        audio = root / "static" / "audio"
        audio.mkdir(parents=True, exist_ok=True)
        return patch.multiple(audio_gen, APP_DIR=root, AUDIO_ROOT=audio)

    def fake_tts(self, text, lang, path):
        path.write_bytes((text + lang).encode("utf-8") * 600)

    def test_audio_reused_across_users_lessons_and_parallel_calls(self):
        first = self.import_item(item={"en": "get off"})["ids"][0]
        second = self.import_item("bob", "B", {"en": "get off"})["ids"][0]
        calls = []
        def fake(text, lang, path):
            calls.append(text)
            time.sleep(0.05)
            self.fake_tts(text, lang, path)
        with self.audio_patch(), patch("app.audio_gen._tts_make", side_effect=fake), patch("app.audio_gen._maximize_loudness"):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda pair: audio_gen.ensure_audio_for_ids(self.db, [pair[0]], ["en"], pair[1]), [(first, "alice"), (second, "bob")]))
        self.assertEqual(calls, ["get off"])
        self.assertEqual(results[0]["items"][0]["en"], results[1]["items"][0]["en"])
        self.assertTrue(all(result["ok"] for result in results))

    def test_hash_names_include_full_text_punctuation_and_voice_parameters(self):
        self.assertNotEqual(audio_gen._identity("a-b", "en")[0], audio_gen._identity("a b", "en")[0])
        self.assertNotEqual(audio_gen._identity("x" * 60 + "A", "en")[0], audio_gen._identity("x" * 60 + "B", "en")[0])
        provider = Mock(identity={"provider": "test", "voice": "different"})
        before = audio_gen._identity("word", "en")[0]
        with patch("app.audio_gen.tts_provider", return_value=provider):
            self.assertNotEqual(before, audio_gen._identity("word", "en")[0])

    def test_tampered_file_is_not_reused(self):
        word_id = self.import_item(item={"en": "word"})["ids"][0]
        with self.audio_patch(), patch("app.audio_gen._tts_make", side_effect=self.fake_tts) as tts, patch("app.audio_gen._maximize_loudness"):
            first = audio_gen.ensure_audio_for_ids(self.db, [word_id], ["en"], "alice")
            path = audio_gen._existing_audio_path(first["items"][0]["en"])
            path.write_bytes(b"changed" * 300)
            second = audio_gen.ensure_audio_for_ids(self.db, [word_id], ["en"], "alice")
            self.assertTrue(second["ok"])
            self.assertEqual(tts.call_count, 2)

    def test_gc_preserves_audio_referenced_only_by_non_baseline_language(self):
        word_id = self.import_item(item={"de": "Wort"})["ids"][0]
        with self.audio_patch(), patch("app.audio_gen._tts_make", side_effect=self.fake_tts), patch("app.audio_gen._maximize_loudness"):
            result = audio_gen.ensure_audio_for_ids(self.db, [word_id], ["de"], "alice")
            with closing(sqlite3.connect(self.db)) as conn:
                conn.execute("UPDATE audio_assets SET last_used_at=0")
                conn.commit()
            self.assertEqual(audio_gen.cleanup_unused_audio(self.db), 0)
            self.assertTrue(audio_gen._existing_audio_path(result["items"][0]["de"]))
            with closing(sqlite3.connect(self.db)) as conn:
                conn.execute("UPDATE words SET audio_de='' WHERE id=?", (word_id,))
                conn.commit()
            self.assertEqual(audio_gen.cleanup_unused_audio(self.db), 1)

    def test_legacy_collision_remains_rejected_after_one_row_is_repaired(self):
        first = self.import_item(item={"en": "a-b"})["ids"][0]
        second = self.import_item("bob", "B", {"en": "a b"})["ids"][0]
        with self.audio_patch(), patch("app.audio_gen._tts_make", side_effect=self.fake_tts) as tts, patch("app.audio_gen._maximize_loudness"):
            old = audio_gen.AUDIO_ROOT / "en" / "Old" / "a_b.mp3"
            old.parent.mkdir(parents=True)
            old.write_bytes(b"legacy" * 200)
            with closing(sqlite3.connect(self.db)) as conn:
                conn.execute("UPDATE words SET audio_en=?", ("/static/audio/en/Old/a_b.mp3",))
                conn.commit()
            audio_gen.ensure_audio_for_ids(self.db, [first], ["en"], "alice")
            audio_gen.ensure_audio_for_ids(self.db, [second], ["en"], "bob")
            self.assertEqual(tts.call_count, 2)

    def test_voice_change_generates_a_new_asset_instead_of_adopting_old_cache(self):
        word_id = self.import_item(item={"en": "word"})["ids"][0]
        with self.audio_patch(), patch("app.audio_gen._tts_make", side_effect=self.fake_tts) as tts, patch("app.audio_gen._maximize_loudness"):
            first = audio_gen.ensure_audio_for_ids(self.db, [word_id], ["en"], "alice")
            provider = Mock(identity={"provider": "different", "voice": "another"})
            with patch("app.audio_gen.tts_provider", return_value=provider):
                second = audio_gen.ensure_audio_for_ids(self.db, [word_id], ["en"], "alice")
            self.assertNotEqual(first["items"][0]["en"], second["items"][0]["en"])
            self.assertEqual(tts.call_count, 2)

    def test_edit_during_synthesis_does_not_attach_or_return_stale_audio(self):
        word_id = self.import_item(item={"en": "old word"})["ids"][0]
        def tts(text, lang, path):
            with closing(sqlite3.connect(self.db)) as conn:
                conn.execute("UPDATE words SET en='new word' WHERE id=?", (word_id,))
                conn.commit()
            self.fake_tts(text, lang, path)
        with self.audio_patch(), patch("app.audio_gen._tts_make", side_effect=tts), patch("app.audio_gen._maximize_loudness"):
            result = audio_gen.ensure_audio_for_ids(self.db, [word_id], ["en"], "alice")
        self.assertEqual(result["items"][0]["en"], "")
        self.assertEqual(result["items"][0]["errors"][0]["error"], "word_changed_retry")
        self.assertEqual(self.rows("SELECT audio_en FROM words WHERE id=?", (word_id,)), [("",)])


if __name__ == "__main__":
    unittest.main()
