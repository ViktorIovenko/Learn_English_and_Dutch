import io
import gc
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app import google_auth, routes
from bot import auth
from config import Config


class RegistrationNotificationsTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = str(Path(self.tmp.name) / 'test.db')
        config = patch.object(Config, 'DB_PATH', self.db)
        config.start()
        self.addCleanup(config.stop)
        self.addCleanup(gc.collect)
        with closing(sqlite3.connect(self.db)) as conn:
            conn.executescript('''
                CREATE TABLE users (
                    user_id TEXT PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT,
                    is_active INTEGER DEFAULT 1, account_type TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP, auth_provider TEXT,
                    google_id TEXT, google_email TEXT, photo_url TEXT
                );
                CREATE TABLE auth_identities (
                    provider TEXT, external_id TEXT, user_id TEXT, email TEXT,
                    PRIMARY KEY(provider, external_id)
                );
            ''')

    async def test_telegram_first_registration_notifies_once(self):
        user = SimpleNamespace(id=42, username='test', first_name='Test', last_name='', language_code='nl')
        with patch.object(auth, '_notify_admins_new_user', new_callable=AsyncMock) as notice:
            self.assertTrue(await auth._ensure_open_registration(SimpleNamespace(effective_user=user), object()))
            self.assertFalse(await auth._ensure_open_registration(SimpleNamespace(effective_user=user), object()))
        notice.assert_awaited_once()

    def test_google_new_account_notifies_but_login_and_email_match_do_not(self):
        with patch.object(routes, '_notify_admins_new_user') as notice:
            uid = google_auth._find_or_create_google_user('new', 'test@example.com', 'Test User')
            self.assertEqual('g_new', uid)
            notice.assert_called_once()
            self.assertEqual('google', notice.call_args.args[0]['auth_provider'])
            self.assertEqual(uid, google_auth._find_or_create_google_user('new', 'test@example.com', 'Test User'))
            self.assertEqual(uid, google_auth._find_or_create_google_user('other', 'test@example.com', 'Test User'))
            notice.assert_called_once()

    async def test_bot_send_failure_is_logged_and_other_admin_still_receives(self):
        bot = SimpleNamespace(send_message=AsyncMock(side_effect=[RuntimeError('unavailable'), None]))
        user = SimpleNamespace(id=42, username='test', first_name='<Test>', last_name='')
        with patch.object(auth, '_admin_ids', return_value=(10, 20)), self.assertLogs('bot.auth', level='WARNING'):
            await auth._notify_admins_new_user(SimpleNamespace(bot=bot), user)
        self.assertEqual(2, bot.send_message.await_count)
        self.assertIn('&lt;Test&gt;', bot.send_message.call_args.kwargs['text'])

    def test_api_failure_is_logged_and_other_admin_still_receives(self):
        with patch.object(Config, 'BOT_TOKEN', 'test-token'), patch.object(routes, '_admin_ids', return_value=(10, 20)), \
                patch.object(routes.urlrequest, 'urlopen', side_effect=[io.BytesIO(b'{"ok":false}'), io.BytesIO(b'{"ok":true}')]) as send, \
                self.assertLogs('app.routes', level='WARNING'):
            routes._notify_admins_new_user({'user_id':'g_new', 'first_name':'Test', 'auth_provider':'google'})
        self.assertEqual(2, send.call_count)
