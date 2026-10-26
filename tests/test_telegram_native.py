import hashlib
import gc
import secrets
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from authlib.jose import JsonWebKey, JsonWebToken
from flask import Flask

from app import android_auth
from app.account_types import migrate_auth_identities
from app.auth_links import verify_auth_token
from app.email_auth import ensure_email_auth_schema
from config import Config


class TelegramNativeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        for key, value in {'DB_PATH': str(Path(temp.name) / 'auth.db'), 'SECRET_KEY': 'test',
                           'TELEGRAM_OIDC_CLIENT_ID': '8903357617'}.items():
            p = patch.object(Config, key, value)
            p.start()
            self.addCleanup(p.stop)
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute('''CREATE TABLE users (user_id TEXT PRIMARY KEY, username TEXT,
                first_name TEXT, last_name TEXT, is_active INTEGER, account_type TEXT,
                auth_provider TEXT)''')
            migrate_auth_identities(c)
        ensure_email_auth_schema()
        android_auth.ensure_android_auth_schema()
        app = Flask(__name__)
        app.register_blueprint(android_auth.android_auth_bp)
        self.client = app.test_client()
        self.key = JsonWebKey.generate_key('RSA', 2048, is_private=True)
        self.key_patch = patch.object(android_auth, '_telegram_keys', return_value={'keys': [self.key.as_dict()]})
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)
        self.verifier = secrets.token_urlsafe(32)
        # Legacy routes use sqlite context managers without closing connections.
        # Collect them before removing the temporary database on Windows.
        self.addCleanup(gc.collect)

    def start(self, **changes):
        body = dict(provider='telegram', transport='native', mode='login', language='ru',
                    challenge=hashlib.sha256(self.verifier.encode()).hexdigest())
        body.update(changes)
        response = self.client.post('/api/auth/android/start', json=body)
        self.assertEqual(response.status_code, 200)
        return response.json

    def token(self, **changes):
        claims = dict(iss='https://oauth.telegram.org', aud=Config.TELEGRAM_OIDC_CLIENT_ID,
                      sub='opaque-subject', id=12345, name='Test User', iat=int(time.time()),
                      exp=int(time.time()) + 300)
        claims.update(changes)
        return JsonWebToken(['RS256']).encode({'alg': 'RS256'}, claims, self.key).decode()

    def submit(self, flow, token, **changes):
        body = dict(flow_id=flow, verifier=self.verifier, id_token=token)
        body.update(changes)
        return self.client.post('/api/auth/telegram/native', json=body)

    def exchange(self, flow):
        return self.client.post('/api/auth/android/exchange', json={'flow_id': flow, 'verifier': self.verifier})

    def test_new_and_existing_registration_and_exchange(self):
        from app import routes
        with patch.object(routes, '_notify_admins_new_user') as notify:
            flow = self.start()
            self.assertEqual(flow['client_id'], Config.TELEGRAM_OIDC_CLIENT_ID)
            self.assertEqual(flow['redirect_uri'], 'https://app4151474097-login.tg.dev/tglogin')
            token = self.token()
            self.assertEqual(self.submit(flow['flow_id'], token).status_code, 200)
            self.assertEqual(self.submit(flow['flow_id'], token).status_code, 200)
            result = self.exchange(flow['flow_id'])
            self.assertEqual(result.json['user_id'], '12345')
            self.assertEqual(verify_auth_token(result.json['token']), '12345')
            self.assertEqual(notify.call_count, 1)
            with closing(sqlite3.connect(Config.DB_PATH)) as c:
                self.assertEqual(c.execute('SELECT account_type FROM users').fetchone()[0], 'pending')
            second = self.start()['flow_id']
            self.assertEqual(self.submit(second, token).status_code, 400)
            self.assertEqual(self.submit(second, self.token(exp=int(time.time()) + 301)).status_code, 200)
            self.assertEqual(self.exchange(second).json['user_id'], '12345')
            self.assertEqual(notify.call_count, 1)

    def test_reject_invalid_tokens_before_registration(self):
        flow = self.start()['flow_id']
        invalid = [self.token(aud='other'), self.token(iss='https://other.example'),
                   self.token(exp=int(time.time()) - 60), self.token(id=None),
                   self.token(iat=int(time.time()) - 120), 'invalid.jwt']
        attacker_key = JsonWebKey.generate_key('RSA', 2048, is_private=True)
        invalid.append(JsonWebToken(['RS256']).encode({'alg': 'RS256'},
                       dict(iss='https://oauth.telegram.org', aud=Config.TELEGRAM_OIDC_CLIENT_ID,
                            sub='forged', id=12345, iat=int(time.time()), exp=int(time.time()) + 300),
                       attacker_key).decode())
        with patch.object(android_auth, '_native_telegram_user') as register:
            for token in invalid:
                with self.subTest(token=token[:12]):
                    self.assertEqual(self.submit(flow, token).status_code, 401)
            register.assert_not_called()
        self.assertEqual(self.exchange(flow).status_code, 202)

    def test_key_server_outage_keeps_attempt_retryable(self):
        import requests
        flow = self.start()['flow_id']
        token = self.token()
        with patch.object(android_auth, '_telegram_keys', side_effect=requests.Timeout):
            self.assertEqual(self.submit(flow, token).status_code, 503)
        self.assertEqual(self.exchange(flow).status_code, 202)

    def test_reject_wrong_verifier_expired_and_provider(self):
        flow = self.start()['flow_id']
        with patch.object(android_auth, '_verify_native_telegram_token') as verify:
            self.assertEqual(self.submit(flow, self.token(), verifier=secrets.token_urlsafe(32)).status_code, 400)
            with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
                c.execute('UPDATE android_auth_flows SET provider="email" WHERE id=?', (flow,))
            self.assertEqual(self.submit(flow, self.token()).status_code, 400)
            with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
                c.execute('UPDATE android_auth_flows SET provider="telegram",created=created-3601 WHERE id=?', (flow,))
            self.assertEqual(self.submit(flow, self.token()).status_code, 400)
            verify.assert_not_called()

    def test_link_attaches_only_on_verified_app_exchange(self):
        flow = self.start()['flow_id']
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute("INSERT INTO users (user_id,is_active,account_type) VALUES ('owner',1,'standard')")
            c.execute("UPDATE android_auth_flows SET link_owner='owner',link_version=NULL,link_generation=? WHERE id=?",
                      ('0', flow))
        from app.account_privacy import generation
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute('UPDATE android_auth_flows SET link_generation=? WHERE id=?', (generation('owner'), flow))
        self.assertEqual(self.submit(flow, self.token()).status_code, 200)
        with closing(sqlite3.connect(Config.DB_PATH)) as c:
            self.assertIsNone(c.execute('SELECT 1 FROM auth_identities').fetchone())
        self.assertEqual(self.exchange(flow).json['user_id'], 'owner')
        with closing(sqlite3.connect(Config.DB_PATH)) as c:
            self.assertEqual(c.execute('SELECT user_id FROM auth_identities WHERE provider="telegram"').fetchone()[0], 'owner')


if __name__ == '__main__':
    unittest.main()
