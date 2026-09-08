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
