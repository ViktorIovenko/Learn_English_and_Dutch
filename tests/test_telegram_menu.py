import tempfile
import unittest
from pathlib import Path
from string import Formatter
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from telegram import ReplyKeyboardRemove
from app.i18n import SUPPORTED_UI_LANGUAGES
from bot import auth, reminder
from bot.i18n import KEYS, OPEN_LABELS, TEXTS, text, user_language
from bot.onboarding import save_detected_language, save_selected_ui_language


class TelegramMenuTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = str(Path(self.tmp.name) / 'test.db')
        self.config = patch.object(auth.Config, 'DB_PATH', self.db)
        self.config.start()
        self.addCleanup(self.config.stop)

    def test_background_notifications_use_saved_language(self):
        save_detected_language(self.db, 42, 'nl-NL')
        self.assertEqual('nl', user_language(self.db, 42))
        save_selected_ui_language(self.db, 42, 'de')
        self.assertEqual('de', user_language(self.db, 42, 'ru'))
        self.assertEqual('en', user_language(self.db, 99))

    def test_all_languages_have_matching_placeholders(self):
        self.assertEqual(set(SUPPORTED_UI_LANGUAGES), set(TEXTS))
        self.assertEqual(set(SUPPORTED_UI_LANGUAGES), set(OPEN_LABELS))
        def fields(value):
            return {field for _, field, _, _ in Formatter().parse(value) if field}
        for lang, copy in TEXTS.items():
            self.assertEqual(set(KEYS), set(copy))
            for key, value in copy.items():
                self.assertEqual(fields(TEXTS['en'][key]), fields(value), (lang, key))

    def test_old_reply_keyboard_is_explicitly_removed(self):
        self.assertIsInstance(auth.get_persistent_keyboard(42), ReplyKeyboardRemove)

    async def test_start_menu_is_localized_and_removes_old_keyboard(self):
        save_selected_ui_language(self.db, 42, 'nl')
        chat = SimpleNamespace(id=42, send_message=AsyncMock(return_value=SimpleNamespace(message_id=1)))
        update = SimpleNamespace(effective_chat=chat, effective_user=SimpleNamespace(language_code='ru'))
        context = SimpleNamespace(user_data={}, bot=SimpleNamespace(set_chat_menu_button=AsyncMock()))
        with patch.object(auth.Config, 'PUBLIC_BASE_URL', 'https://example.test'):
            await auth.show_menu_with_keyboard(update, context, 42)
        self.assertEqual(OPEN_LABELS['nl'], context.bot.set_chat_menu_button.call_args.kwargs['menu_button'].text)
        self.assertIsInstance(chat.send_message.call_args.kwargs['reply_markup'], ReplyKeyboardRemove)

    async def test_login_message_contains_only_browser_and_download(self):
        save_selected_ui_language(self.db, 42, 'nl')
        chat = SimpleNamespace(id=42, send_message=AsyncMock(return_value=SimpleNamespace(message_id=1)))
        update = SimpleNamespace(effective_chat=chat, effective_user=SimpleNamespace(language_code='ru'))
        context = SimpleNamespace(user_data={})
        with patch.object(auth, '_build_app_url', return_value=('https://example.test', True, True)):
            await auth._send_fresh_app_link(update, context, 42)
        rows = chat.send_message.call_args.kwargs['reply_markup'].inline_keyboard
        self.assertEqual(2, len(rows))
        self.assertTrue(all(button.web_app is None for row in rows for button in row))
        self.assertNotIn('android-auth', str(rows))

    async def test_reminder_uses_recipient_language_without_duplicate_button(self):
        save_detected_language(self.db, 42, 'nl')
        bot = SimpleNamespace(send_message=AsyncMock(return_value=SimpleNamespace(message_id=1)))
        with patch.object(reminder, '_get_last_state', return_value=(None, None)), patch.object(reminder, '_set_last_state'):
            self.assertTrue(await reminder.send_to_user_id(SimpleNamespace(bot=bot), 42))
        self.assertEqual(text('nl', 'reminder'), bot.send_message.call_args.kwargs['text'])
        self.assertNotIn('reply_markup', bot.send_message.call_args.kwargs)
