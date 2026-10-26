import gc
import hashlib
import secrets
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask, redirect
from app.account_types import migrate_auth_identities
from app.account_linking import telegram_account_id, telegram_chat_id
from app.android_auth import android_auth_bp, ensure_android_auth_schema, complete_link_flow
from app.auth_links import create_auth_token, verify_auth_token
from app.email_auth import email_bp, ensure_email_auth_schema
from bot.auth import _register_user
from telegram import User
from config import Config


class AccountLinkingTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(gc.collect)
        for key, value in {'DB_PATH':str(Path(tmp.name)/'test.db'), 'SECRET_KEY':'test-secret',
                           'SMTP_PASSWORD':'test-password', 'APP_BASE_URL':'https://example.test'}.items():
            config = patch.object(Config, key, value)
            config.start(); self.addCleanup(config.stop)
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute('''CREATE TABLE users (user_id TEXT PRIMARY KEY, username TEXT, first_name TEXT,
                last_name TEXT, is_active INTEGER, auth_provider TEXT, account_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
            migrate_auth_identities(c)
            c.execute("INSERT INTO users (user_id,first_name,is_active,account_type) VALUES ('e_owner','Owner',1,'standard')")
            c.execute('CREATE TABLE words (user_id TEXT, word TEXT)')
            c.execute("INSERT INTO words VALUES ('e_owner','preserved')")
        ensure_email_auth_schema(); ensure_android_auth_schema()
        self.app = Flask(__name__, template_folder=str(Path('app/templates').resolve()))
        self.app.secret_key = 'test-secret'
        self.app.register_blueprint(android_auth_bp); self.app.register_blueprint(email_bp)
        self.client = self.app.test_client()
        self.verifier = secrets.token_urlsafe(32)
        self.token = create_auth_token('e_owner')

    def start(self, provider='telegram', headers=None):
        return self.client.post('/api/auth/android/start', json={'provider':provider, 'mode':'link',
            'challenge':hashlib.sha256(self.verifier.encode()).hexdigest()},
            headers=headers if headers is not None else {'Authorization':'Bearer '+self.token})

    def exchange(self, flow, verifier=None):
        return self.client.post('/api/auth/android/exchange', json={'flow_id':flow, 'verifier':verifier or self.verifier})

    def query(self, sql, args=()):
        with closing(sqlite3.connect(Config.DB_PATH)) as c:
            return c.execute(sql, args).fetchall()

    def request_native_email(self, email='native@example.com'):
        flow = self.start('email').json['flow_id']
        with patch('app.email_auth._send_auth_mail') as mail:
            response = self.client.post('/api/account/email/link', headers={'Authorization':'Bearer '+self.token}, json={
                'flow_id':flow, 'verifier':self.verifier, 'email':email,
                'password':'native-password-123', 'password_confirmation':'native-password-123', 'language':'en'})
        self.assertEqual(200, response.status_code, response.json)
        return flow, mail.call_args.args[1]

    def test_native_email_confirmation_finishes_in_browser_and_resumes_same_app_account(self):
        flow, token = self.request_native_email()
        self.assertEqual([], self.query('SELECT user_id FROM email_auth_credentials'))
        self.assertEqual(202, self.exchange(flow).status_code)
        browser = self.app.test_client()
        inspected = browser.post('/api/auth/email/link', json={'token':token})
        self.assertEqual('native_link', inspected.json['purpose'])
        confirmed = browser.post('/api/auth/email/confirm', json={'token':token})
        self.assertEqual(200, confirmed.status_code, confirmed.json)
        self.assertIn('/auth/android/return?flow='+flow, confirmed.json['next'])
        with browser.session_transaction() as session:
            self.assertEqual('e_owner', session['tg_user_id'])
        returned = browser.get('/auth/android/return?flow='+flow)
        self.assertIn('S.browser_fallback_url=', returned.text)
        self.assertIn('/settings', returned.text)
        self.assertNotIn('auth=', returned.text)
        self.assertEqual(400, browser.post('/api/auth/email/confirm', json={'token':token}).status_code)
        exchanged = self.exchange(flow)
        self.assertEqual('e_owner', exchanged.json['user_id'])
        self.assertEqual('e_owner', verify_auth_token(exchanged.json['token']))
        self.assertEqual('e_owner', self.exchange(flow).json['user_id'])
        self.assertEqual([('e_owner','preserved')], self.query('SELECT * FROM words'))

    def test_native_email_rejects_missing_owner_proof_and_password_route_bypass(self):
        flow = self.start('email').json['flow_id']
        data = {'flow_id':flow, 'email':'native@example.com', 'password':'native-password-123',
                'password_confirmation':'native-password-123'}
        for verifier in (None, '', secrets.token_urlsafe(32)):
            data['verifier'] = verifier
            response = self.client.post('/api/account/email/link', json=data, headers={'Authorization':'Bearer '+self.token})
            self.assertEqual(400, response.status_code)
        self.assertEqual(401, self.client.post('/api/account/email/link', json=data).status_code)
        flow, token = self.request_native_email()
        self.assertEqual(400, self.client.post('/api/auth/email/password', json={
            'token':token, 'password':'replacement-password-123', 'password_confirmation':'replacement-password-123'}).status_code)
        self.assertEqual([], self.query('SELECT user_id FROM email_auth_credentials'))

    def test_native_email_rejects_conflict_without_merging_accounts(self):
        flow, token = self.request_native_email()
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute("INSERT INTO users(user_id,is_active) VALUES ('other',1)")
            c.execute("INSERT INTO auth_identities(provider,external_id,user_id,email) VALUES ('email','native@example.com','other','native@example.com')")
        response = self.client.post('/api/auth/email/confirm', json={'token':token})
        self.assertEqual(409, response.status_code)
        self.assertEqual([], self.query('SELECT user_id FROM email_auth_credentials'))
        self.assertEqual(202, self.exchange(flow).status_code)

    def test_native_email_owner_changes_invalidate_confirmation(self):
        flow, token = self.request_native_email()
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute("INSERT INTO email_auth_credentials VALUES ('e_owner','changed@example.com','hash','changed')")
        self.assertEqual(400, self.client.post('/api/auth/email/confirm', json={'token':token}).status_code)
        self.assertEqual([('changed@example.com',)], self.query('SELECT email FROM email_auth_credentials'))

    def test_native_email_expired_link_cannot_be_confirmed(self):
        flow, token = self.request_native_email()
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute('UPDATE email_auth_links SET created=created-1801')
        self.assertEqual(400, self.client.post('/api/auth/email/confirm', json={'token':token}).status_code)
        self.assertEqual([], self.query('SELECT user_id FROM email_auth_credentials'))
        self.assertEqual(202, self.exchange(flow).status_code)

    def test_native_email_new_request_supersedes_old_attempt(self):
        flow, token = self.request_native_email()
        with patch('app.email_auth._rate_limit', return_value=True):
            next_flow, next_token = self.request_native_email('next@example.com')
        self.assertEqual(400, self.client.post('/api/auth/email/confirm', json={'token':token}).status_code)
        self.assertEqual(200, self.client.post('/api/auth/email/confirm', json={'token':next_token}).status_code)
        self.assertEqual('e_owner', self.exchange(next_flow).json['user_id'])

    def test_link_start_and_status_require_signed_owner(self):
        self.assertEqual(401, self.start(headers={'X-User-Id':'e_owner'}).status_code)
        self.assertEqual(401, self.client.get('/api/account/identities').status_code)
        status = self.client.get('/api/account/identities', headers={'Authorization':'Bearer '+self.token})
        self.assertFalse(status.json['telegram_linked'])
        self.assertIsNone(status.json['email'])

    def test_telegram_is_attached_only_after_device_proof_and_bot_uses_same_account(self):
        flow = self.start().json['flow_id']
        complete_link_flow(flow, 'telegram', {'external_id':'987654'})
        self.assertEqual(400, self.exchange(flow, secrets.token_urlsafe(32)).status_code)
        self.assertEqual('987654', telegram_account_id('987654'))
        response = self.exchange(flow)
        self.assertEqual('e_owner', response.json['user_id'])
        self.assertEqual('e_owner', verify_auth_token(response.json['token']))
        self.assertEqual('e_owner', telegram_account_id('987654'))
        self.assertEqual(987654, telegram_chat_id('e_owner'))
        self.assertFalse(_register_user(Config.DB_PATH, User(987654, 'Telegram Name', False)))
        self.assertEqual([('e_owner',)], self.query('SELECT user_id FROM users'))
        self.assertEqual([('preserved',)], self.query("SELECT word FROM words WHERE user_id='e_owner'"))
        self.assertEqual('e_owner', self.exchange(flow).json['user_id'])

    def test_existing_telegram_account_is_never_merged(self):
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute("INSERT INTO users(user_id,is_active) VALUES ('987654',1)")
        flow = self.start().json['flow_id']
        complete_link_flow(flow, 'telegram', {'external_id':'987654'})
        self.assertEqual(409, self.exchange(flow).status_code)
        self.assertEqual('987654', telegram_account_id('987654'))

    def test_email_confirmation_links_to_owner_without_registration(self):
        started = self.start('email').json
        from urllib.parse import urlsplit
        self.client.get(urlsplit(started['browser_url']).path + '?' + urlsplit(started['browser_url']).query)
        with patch('app.email_auth._send_auth_mail') as mail, patch('app.routes._notify_admins_new_user') as notice:
            response = self.client.post('/api/auth/email/request', json={'email':'linked@example.com', 'mode':'setup'})
            self.assertEqual(200, response.status_code)
            token = mail.call_args.args[1]
            other_browser = self.app.test_client()
            response = other_browser.post('/api/auth/email/password', json={
                'token':token, 'password':'A secure password 123!', 'password_confirmation':'A secure password 123!'})
            self.assertEqual(200, response.status_code)
            self.assertEqual([], self.query('SELECT user_id FROM email_auth_credentials'))
            result = self.exchange(started['flow_id'])
            self.assertEqual(200, result.status_code, result.json)
            self.assertEqual('e_owner', result.json['user_id'])
            self.assertEqual('e_owner', verify_auth_token(result.json['token']))
            self.assertEqual('', verify_auth_token(self.token))
            self.assertEqual([('e_owner','linked@example.com')], self.query('SELECT user_id,email FROM email_auth_credentials'))
            self.assertEqual('e_owner', self.exchange(started['flow_id']).json['user_id'])
            notice.assert_not_called()

    def test_email_of_another_account_is_rejected_without_changing_it(self):
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute("INSERT INTO users(user_id,is_active) VALUES ('other',1)")
            c.execute("INSERT INTO auth_identities(provider,external_id,user_id,email) VALUES ('email','taken@example.com','other','taken@example.com')")
        flow = self.start('email').json['flow_id']
        complete_link_flow(flow, 'email', {'external_id':'taken@example.com', 'password_hash':'hash', 'version':'new'})
        self.assertEqual(409, self.exchange(flow).status_code)
        self.assertEqual([], self.query('SELECT user_id FROM email_auth_credentials'))

    def test_owner_credential_change_invalidates_unfinished_link(self):
        flow = self.start().json['flow_id']
        complete_link_flow(flow, 'telegram', {'external_id':'987654'})
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute("INSERT INTO email_auth_credentials VALUES ('e_owner','owner@example.com','hash','changed')")
        self.assertEqual(400, self.exchange(flow).status_code)
        self.assertEqual('987654', telegram_account_id('987654'))

    def test_telegram_callback_preserves_link_intent_until_device_exchange(self):
        from app import telegram_oauth
        self.app.register_blueprint(telegram_oauth.telegram_oauth_bp)
        oauth = SimpleNamespace(telegram=SimpleNamespace(
            authorize_redirect=lambda uri: redirect('/provider'),
            authorize_access_token=lambda: {'userinfo':{'id':987654, 'given_name':'Telegram User'}}))
        with patch.object(Config, 'TELEGRAM_OIDC_CLIENT_ID', 'test-client'), patch.object(telegram_oauth, '_oauth', oauth):
            result = self.start()
            from urllib.parse import urlsplit
            url = urlsplit(result.json['browser_url'])
            self.assertEqual(302, self.client.get(url.path + '?' + url.query).status_code)
            self.assertEqual(302, self.client.get('/auth/telegram/callback').status_code)
            self.assertEqual('987654', telegram_account_id('987654'))
            self.assertEqual('e_owner', self.exchange(result.json['flow_id']).json['user_id'])

    def test_mini_app_login_resolves_linked_account(self):
        from app import routes
        self.app.register_blueprint(routes.web)
        flow = self.start().json['flow_id']
        complete_link_flow(flow, 'telegram', {'external_id':'987654'})
        self.assertEqual(200, self.exchange(flow).status_code)
        with patch.object(routes, 'verify_telegram_init_data', return_value={'user':{'id':987654, 'first_name':'Telegram'}}), \
                patch.object(routes, '_notify_admins_new_user') as notice:
            response = self.client.post('/api/auth/login_webapp', json={'init_data':'verified-by-test'})
        self.assertEqual(200, response.status_code)
        self.assertEqual('e_owner', response.json['user']['id'])
        notice.assert_not_called()
