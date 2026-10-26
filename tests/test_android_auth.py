import hashlib
import secrets
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from app.account_types import migrate_auth_identities
from app.auth_links import verify_auth_token
from app.android_auth import android_auth_bp, ensure_android_auth_schema, complete_android_flow
from app.email_auth import email_bp, ensure_email_auth_schema
from app.telegram_oauth import _android_deep_link
from config import Config


class AndroidAuthTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='parallellingvo-android-auth-')
        self.addCleanup(temp.cleanup)
        for key, value in {'DB_PATH':str(Path(temp.name)/'test.db'), 'SECRET_KEY':'test-secret',
                           'SMTP_PASSWORD':'test-password', 'APP_BASE_URL':'https://app.parallellingvo.app'}.items():
            p=patch.object(Config,key,value);p.start();self.addCleanup(p.stop)
        with closing(sqlite3.connect(Config.DB_PATH)) as c,c:
            c.execute('''CREATE TABLE users (user_id TEXT PRIMARY KEY, username TEXT, first_name TEXT,
                last_name TEXT, is_active INTEGER, auth_provider TEXT, account_type TEXT)''')
            migrate_auth_identities(c)
            c.execute("INSERT INTO users (user_id,is_active) VALUES ('12345',1)")
        ensure_email_auth_schema();ensure_android_auth_schema()
        self.app=Flask(__name__,template_folder=str(Path('app/templates').resolve()))
        self.app.secret_key='test-secret'
        self.app.register_blueprint(email_bp);self.app.register_blueprint(android_auth_bp)
        self.client=self.app.test_client()
        self.verifier=secrets.token_urlsafe(32)

    def browser_link(self):
        from app.auth_links import create_auth_token
        response = self.client.post('/api/auth/android/browser-link',
            headers={'Authorization': 'Bearer ' + create_auth_token('12345'), 'X-Device-Language': 'ru'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        return response.json['browser_url'].split('#')[1]

    def test_browser_handoff_same_account_and_single_use(self):
        ticket = self.browser_link()
        browser = self.app.test_client()
        with browser.session_transaction() as state:
            state.update(tg_user_id='other-account', is_auth=True, pending_link='other-account')
        response = browser.post('/api/auth/android/browser-session', json={'ticket': ticket})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['next'], '/settings/mcp')
        with browser.session_transaction() as state:
            self.assertEqual(state['tg_user_id'], '12345')
            self.assertTrue(state['is_auth'])
            self.assertNotIn('pending_link', state)
        self.assertEqual(browser.post('/api/auth/android/browser-session', json={'ticket': ticket}).status_code, 400)
        page = browser.get('/auth/android/browser?lang=ru')
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.headers['Referrer-Policy'], 'no-referrer')
        self.assertNotIn(ticket.encode(), page.data)

    def test_browser_handoff_requires_bearer_and_active_user(self):
        self.assertEqual(self.client.post('/api/auth/android/browser-link', headers={'X-User-Id':'12345'}).status_code, 401)
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute('UPDATE users SET is_active=0')
        from app.auth_links import create_auth_token
        self.assertEqual(self.client.post('/api/auth/android/browser-link',
            headers={'Authorization':'Bearer '+create_auth_token('12345')}).status_code, 401)

    def test_browser_handoff_expired_and_superseded(self):
        first = self.browser_link()
        second = self.browser_link()
        self.assertEqual(self.client.post('/api/auth/android/browser-session', json={'ticket': first}).status_code, 400)
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute('UPDATE android_browser_links SET expires=0')
        self.assertEqual(self.client.post('/api/auth/android/browser-session', json={'ticket': second}).status_code, 400)
        with self.client.session_transaction() as state:
            self.assertNotIn('is_auth', state)

    def test_browser_handoff_revoked_or_disabled(self):
        from app.account_privacy import ensure_schema, subject_hash
        ticket = self.browser_link()
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            ensure_schema(c)
            c.execute('INSERT INTO account_revocations VALUES (?,?)', (subject_hash('12345'), 'revoked'))
        self.assertEqual(self.client.post('/api/auth/android/browser-session', json={'ticket':ticket}).status_code, 400)
        ticket = self.browser_link()
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute('UPDATE users SET is_active=0')
        self.assertEqual(self.client.post('/api/auth/android/browser-session', json={'ticket':ticket}).status_code, 400)

    def start(self,provider='telegram'):
        response=self.client.post('/api/auth/android/start',json={'provider':provider,
            'challenge':hashlib.sha256(self.verifier.encode()).hexdigest(),'language':'en','mode':'setup'})
        self.assertEqual(response.status_code,200)
        return response.json

    def exchange(self,flow,verifier=None):
        return self.client.post('/api/auth/android/exchange',json={'flow_id':flow,'verifier':verifier or self.verifier})

    def test_pending_bound_to_app_and_idempotent_retry(self):
        flow=self.start()['flow_id']
        self.assertEqual(self.exchange(flow).status_code,202)
        self.assertEqual(self.exchange(flow,secrets.token_urlsafe(32)).status_code,400)
        target=complete_android_flow(flow,'12345','telegram')
        self.assertIn('/auth/android/return?',target)
        self.assertNotIn('auth=',target)
        response=self.exchange(flow)
        self.assertEqual(response.json['provider'],'telegram')
        self.assertEqual(verify_auth_token(response.json['token']),'12345')
        self.assertEqual(self.exchange(flow).json['user_id'],'12345')
        with closing(sqlite3.connect(Config.DB_PATH)) as c,c:
            c.execute('UPDATE android_auth_flows SET delivered=delivered-61')
        self.assertEqual(self.exchange(flow).status_code,400)

    def test_login_start_without_account_privacy_module(self):
        with patch.dict(sys.modules, {'app.account_privacy': None}):
            for provider in ('telegram', 'email'):
                with self.subTest(provider=provider):
                    data = self.start(provider)
                    self.assertIn('/auth/' + provider + '?', data['browser_url'])
                    self.assertEqual(self.exchange(data['flow_id']).status_code, 202)

    def test_expired_provider_mismatch_and_disabled(self):
        flow=self.start()['flow_id']
        complete_android_flow(flow,'12345','email')
        self.assertEqual(self.exchange(flow).status_code,202)
        complete_android_flow(flow,'12345','telegram')
        with closing(sqlite3.connect(Config.DB_PATH)) as c,c:
            c.execute('UPDATE users SET is_active=0')
        self.assertEqual(self.exchange(flow).status_code,400)
        with closing(sqlite3.connect(Config.DB_PATH)) as c,c:
            c.execute('UPDATE android_auth_flows SET created=created-3601')
        self.assertEqual(self.exchange(flow).status_code,400)

    def test_email_registration_cross_browser_and_native_login(self):
        data=self.start('email');self.client.get(data['browser_url'].removeprefix(Config.APP_BASE_URL))
        with patch('app.email_auth._send_auth_mail') as mail:
            self.client.post('/api/auth/email/request',json={'email':'test@example.com','mode':'setup'})
            token=mail.call_args.args[1]
        other=self.app.test_client()
        password='A secure password 123'
        result=other.post('/api/auth/email/password',json={'token':token,'password':password,'password_confirmation':password})
        self.assertIn('/auth/android/return?',result.json['next'])
        self.assertIn(data['flow_id'],result.json['next'])
        result=self.exchange(data['flow_id']);self.assertEqual(result.json['provider'],'email')
        uid=result.json['user_id']
        result=other.post('/api/auth/email/login',json={'email':'test@example.com','password':password,'client':'android'})
        self.assertEqual(result.json['user_id'],uid)
        self.assertEqual(verify_auth_token(result.json['token']),uid)
        with closing(sqlite3.connect(Config.DB_PATH)) as c,c:
            c.execute("UPDATE email_auth_credentials SET version='changed'")
        self.assertEqual(self.exchange(data['flow_id']).status_code,400)

    def test_telegram_callback_and_error_resume_same_flow(self):
        from app.auth_links import create_auth_token
        flow=self.start()['flow_id']
        with self.app.test_request_context():
            from flask import session
            session['telegram_android_flow']=flow
            target=_android_deep_link(token=create_auth_token('12345'))
        self.assertIn(flow,target);self.assertEqual(self.exchange(flow).json['user_id'],'12345')
        flow=self.start()['flow_id']
        with self.app.test_request_context():
            session['telegram_android_flow']=flow
            _android_deep_link(error='telegram_auth_failed')
        self.assertEqual(self.exchange(flow).status_code,400)

    def test_callback_targets_package_and_contains_no_bearer_token(self):
        data=self.start();response=self.client.get('/auth/android/return?flow='+data['flow_id'])
        self.assertEqual(response.status_code,200)
        self.assertIn('package=app.parallellingvo',response.text)
        self.assertNotIn('auth=',response.text)
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual(self.client.get('/auth/android/return?flow=invalid').status_code,400)


if __name__=='__main__':unittest.main()
