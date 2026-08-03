import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from bot.onboarding import (
    BOT_INTERFACE_TEXT,
    LANGUAGE_LABELS,
    ONBOARDING_TEXT,
    account_type,
    bot_interface_text,
    bot_interface_values,
    complete_account_type,
    normalize_telegram_language,
    onboarding_text,
    save_detected_language,
    save_selected_ui_language,
    selected_ui_language,
)
from app.i18n import SUPPORTED_UI_LANGUAGES


class TelegramOnboardingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.db")
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE users (
                    user_id TEXT PRIMARY KEY,
                    account_type TEXT NOT NULL DEFAULT 'pending'
                )
            """)
            conn.execute(
                "INSERT INTO users (user_id, account_type) VALUES ('42', 'pending')"
            )
            conn.commit()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_telegram_language_is_normalized_for_supported_locales(self):
        self.assertEqual("pt", normalize_telegram_language("pt-BR"))
        self.assertEqual("uk", normalize_telegram_language("uk_UA"))
        self.assertEqual("en", normalize_telegram_language("tr"))

    def test_questions_are_localized_using_telegram_language(self):
        self.assertEqual(
            "Какой аккаунт вам нужен?",
            onboarding_text("ru", "choose_account"),
        )
        self.assertEqual(
            "Welk type account heb je nodig?",
            onboarding_text("nl", "choose_account"),
        )
        self.assertEqual(
            "De interfacetaal van je Telegram is Nederlands. Deze taal ook voor de app gebruiken?",
            onboarding_text(
                "nl",
                "confirm_detected_language",
                language=LANGUAGE_LABELS["nl"],
            ),
        )

    def test_every_supported_interface_language_has_complete_bot_copy(self):
        expected_keys = set(ONBOARDING_TEXT["en"])
        self.assertEqual(set(SUPPORTED_UI_LANGUAGES), set(LANGUAGE_LABELS))
        self.assertEqual(set(SUPPORTED_UI_LANGUAGES), set(ONBOARDING_TEXT))
        for language in SUPPORTED_UI_LANGUAGES:
            self.assertEqual(expected_keys, set(ONBOARDING_TEXT[language]))

        expected_interface_keys = set(BOT_INTERFACE_TEXT["en"])
        for language in SUPPORTED_UI_LANGUAGES:
            self.assertEqual(
                expected_interface_keys,
                set(BOT_INTERFACE_TEXT[language]),
            )

    def test_language_choice_is_persisted_without_losing_detected_language(self):
        save_detected_language(self.db_path, "42", "nl-NL")
        self.assertTrue(save_selected_ui_language(self.db_path, "42", "ru"))
        self.assertEqual("ru", selected_ui_language(self.db_path, "42"))

        with closing(sqlite3.connect(self.db_path)) as conn:
            detected = conn.execute(
                "SELECT detected_ui_language FROM user_settings WHERE user_id='42'"
            ).fetchone()[0]
        self.assertEqual("nl", detected)

    def test_dutch_bot_menu_and_buttons_are_localized(self):
        self.assertEqual("⬇️ Menu", bot_interface_text("nl", "menu"))
        self.assertEqual("Woorden leren", bot_interface_text("nl", "learn_words"))
        self.assertEqual("Woorden uploaden", bot_interface_text("nl", "upload_words"))
        self.assertIn("Woorden uploaden", bot_interface_values("upload_words"))

    def test_account_type_can_only_be_selected_once(self):
        self.assertEqual("pending", account_type(self.db_path, "42"))
        self.assertTrue(complete_account_type(self.db_path, "42", "child"))
        self.assertEqual("child", account_type(self.db_path, "42"))
        self.assertFalse(complete_account_type(self.db_path, "42", "standard"))

    def test_invalid_choices_are_rejected(self):
        self.assertFalse(save_selected_ui_language(self.db_path, "42", "xx"))
        self.assertIsNone(selected_ui_language(self.db_path, "42"))
        self.assertFalse(complete_account_type(self.db_path, "42", "admin"))


if __name__ == "__main__":
    unittest.main()
