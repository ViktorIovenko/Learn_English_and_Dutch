import sqlite3
import unittest

from app.languages import LANGUAGES, MIN_PARALLEL_LANGUAGES
from app.multilingual import (
    ensure_multilingual_schema,
    get_user_languages,
    get_word_translations,
    set_user_languages,
    upsert_word_translation,
)


class MultilingualSchemaTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'user',
                lesson TEXT,
                number TEXT,
                nl TEXT,
                en TEXT,
                ru TEXT,
                ex_nl TEXT,
                ex_en TEXT,
                ex_ru TEXT,
                audio_nl TEXT,
                audio_en TEXT,
                audio_ru TEXT,
                updated_at INTEGER
            )
        """)
        self.conn.execute("""
            INSERT INTO words (user_id, lesson, number, nl, en, ru)
            VALUES ('u1', '1', '1.1', 'ontwikkeling', 'development', 'развитие')
        """)
        ensure_multilingual_schema(self.conn, backfill_legacy=True)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_launch_catalog_has_45_languages(self):
        self.assertEqual(len(LANGUAGES), 45)
        self.assertEqual(MIN_PARALLEL_LANGUAGES, 3)

    def test_legacy_languages_are_backfilled(self):
        translations = get_word_translations(self.conn, 1)
        self.assertEqual(translations["nl"]["text"], "ontwikkeling")
        self.assertEqual(translations["en"]["text"], "development")
        self.assertEqual(translations["ru"]["text"], "развитие")

    def test_backfill_marker_is_created(self):
        row = self.conn.execute(
            "SELECT value FROM multilingual_meta WHERE key = 'legacy_nl_en_ru_backfill_v1'"
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["value"], "done")

    def test_new_language_does_not_need_new_words_column(self):
        upsert_word_translation(
            self.conn,
            1,
            "de",
            text="Entwicklung",
            example="Die Entwicklung geht weiter.",
        )
        self.conn.commit()
        translations = get_word_translations(self.conn, 1)
        self.assertEqual(translations["de"]["text"], "Entwicklung")
        columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(words)")}
        self.assertNotIn("de", columns)

    def test_legacy_update_is_synced_to_normalized_storage(self):
        self.conn.execute("""
            UPDATE words
            SET en = 'growth', ex_en = 'The growth continues.', audio_en = '/audio/growth.mp3', updated_at = 123
            WHERE id = 1
        """)
        self.conn.commit()
        translations = get_word_translations(self.conn, 1)
        self.assertEqual(translations["en"]["text"], "growth")
        self.assertEqual(translations["en"]["example"], "The growth continues.")
        self.assertEqual(translations["en"]["audio_url"], "/audio/growth.mp3")
        self.assertEqual(translations["en"]["updated_at"], 123)

    def test_legacy_insert_is_synced_to_normalized_storage(self):
        cursor = self.conn.execute("""
            INSERT INTO words (user_id, lesson, number, nl, en, ru, updated_at)
            VALUES ('u1', '1', '1.2', 'stad', 'city', 'город', 456)
        """)
        word_id = cursor.lastrowid
        self.conn.commit()
        translations = get_word_translations(self.conn, word_id)
        self.assertEqual(translations["nl"]["text"], "stad")
        self.assertEqual(translations["en"]["text"], "city")
        self.assertEqual(translations["ru"]["text"], "город")

    def test_normalized_legacy_write_is_synced_back_to_old_columns(self):
        upsert_word_translation(
            self.conn,
            1,
            "nl",
            text="groei",
            example="De groei gaat door.",
            audio_url="/audio/groei.mp3",
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT nl, ex_nl, audio_nl FROM words WHERE id = 1"
        ).fetchone()
        self.assertEqual(row["nl"], "groei")
        self.assertEqual(row["ex_nl"], "De groei gaat door.")
        self.assertEqual(row["audio_nl"], "/audio/groei.mp3")

    def test_deleting_word_deletes_normalized_translations(self):
        upsert_word_translation(self.conn, 1, "de", text="Entwicklung")
        self.conn.commit()
        self.conn.execute("DELETE FROM words WHERE id = 1")
        self.conn.commit()
        count = self.conn.execute(
            "SELECT COUNT(*) AS n FROM word_translations WHERE word_id = 1"
        ).fetchone()["n"]
        self.assertEqual(count, 0)

    def test_clearing_legacy_language_removes_empty_translation(self):
        self.conn.execute("""
            UPDATE words
            SET en = '', ex_en = '', audio_en = '', updated_at = 789
            WHERE id = 1
        """)
        self.conn.commit()
        translations = get_word_translations(self.conn, 1)
        self.assertNotIn("en", translations)

    def test_user_can_select_three_or_more_languages(self):
        saved = set_user_languages(self.conn, "u1", ["nl", "en", "de", "fr"])
        self.conn.commit()
        self.assertEqual(saved, ["nl", "en", "de", "fr"])
        self.assertEqual(get_user_languages(self.conn, "u1"), saved)

    def test_two_languages_are_rejected(self):
        with self.assertRaises(ValueError):
            set_user_languages(self.conn, "u1", ["en", "nl"])


if __name__ == "__main__":
    unittest.main()
