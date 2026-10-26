import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from werkzeug.security import check_password_hash
from app.account_types import migrate_auth_identities
from app.auth_links import create_auth_token, verify_auth_token
from app.email_auth import email_bp, ensure_email_auth_schema, _send_auth_mail
from app.email_auth_i18n import TEXT
from config import Config

PASSWORD = 'Correct password 123!'
NEW_PASSWORD = 'New secure password 456!'


class EmailAuthTests(unittest.TestCase):
    def setUp(self):
        notifier = patch('app.routes._notify_admins_new_user')
        self.notice = notifier.start()
        self.addCleanup(notifier.stop)
        self.temp = tempfile.TemporaryDirectory(prefix='parallellingvo-email-test-')
        self.addCleanup(self.temp.cleanup)
        for key, value in {'DB_PATH': str(Path(self.temp.name) / 'test.db'), 'SECRET_KEY':'test-secret',
                           'SMTP_PASSWORD':'test-password', 'APP_BASE_URL':'https://app.parallellingvo.app'}.items():
            p = patch.object(Config, key, value); p.start(); self.addCleanup(p.stop)
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute('''CREATE TABLE users (user_id TEXT PRIMARY KEY, username TEXT,
                first_name TEXT, last_name TEXT, is_active INTEGER, auth_provider TEXT,
                account_type TEXT)''')
            migrate_auth_identities(c)
        ensure_email_auth_schema()
        self.app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / 'app/templates'))
        self.app.secret_key = 'test-secret'
        self.app.register_blueprint(email_bp)
        self.client = self.app.test_client()
        self.sender = patch('app.email_auth._send_auth_mail'); self.mail = self.sender.start(); self.addCleanup(self.sender.stop)

    def request(self, mode='setup', language='en', email='test@example.com', client=None):
        return (client or self.client).post('/api/auth/email/request', json={'email':email,'mode':mode,'language':language})

    def token(self):
        return self.mail.call_args.args[1]

    def save(self, token=None, password=PASSWORD, confirmation=None, client=None):
        return (client or self.client).post('/api/auth/email/password', json={'token':token or self.token(), 'password':password,
            'password_confirmation':password if confirmation is None else confirmation})

    def login(self, password=PASSWORD, client=None):
        return (client or self.client).post('/api/auth/email/login', json={'email':'test@example.com','password':password})

    def clear_limits(self):
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute('DELETE FROM email_auth_attempts')

    def create_user(self):
        self.request(); self.assertEqual(self.save().status_code, 200)
        with self.client.session_transaction() as s:
            return s['tg_user_id']

    def test_signup_requires_link_and_password_cross_browser(self):
        self.assertEqual(self.request().status_code, 200)
        self.notice.assert_not_called()
        with closing(sqlite3.connect(Config.DB_PATH)) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM users').fetchone()[0], 0)
        other = self.app.test_client()
        other.get('/auth/email/complete?lang=en')
        token = self.token()
        self.assertEqual(other.post('/api/auth/email/link',json={'token':token}).status_code, 200)
        self.assertEqual(self.save(password='short').status_code, 400)
        self.assertEqual(self.save(confirmation='mismatch').status_code, 400)
        self.assertEqual(self.save(client=other).json['next'], '/upload')
        self.notice.assert_called_once()
        self.assertEqual('email', self.notice.call_args.args[0]['auth_provider'])
        with closing(sqlite3.connect(Config.DB_PATH)) as c:
            row = c.execute('SELECT password_hash FROM email_auth_credentials').fetchone()
            self.assertNotIn(PASSWORD, row[0]); self.assertTrue(check_password_hash(row[0],PASSWORD))
            self.assertEqual(c.execute('SELECT account_type FROM users').fetchone()[0], 'pending')
        self.assertEqual(self.save(token=token).status_code, 400)
        self.assertEqual(self.client.post('/api/auth/email/verify',json={'code':'123456'}).status_code, 410)

    def test_login_and_reset_revoke_old_sessions_and_tokens(self):
        user_id = self.create_user()
        old_token = create_auth_token(user_id)
        stale_client = self.app.test_client()
        self.assertEqual(self.login(client=stale_client).status_code, 200)
        self.clear_limits(); self.assertEqual(self.request('reset').status_code,200)
        self.assertEqual(self.mail.call_args.args[2], 'reset')
        self.assertEqual(self.save(password=NEW_PASSWORD).status_code,200)
        self.assertEqual(verify_auth_token(old_token),'')
        stale_client.get('/auth/email')
        with stale_client.session_transaction() as s:
            self.assertFalse(s.get('is_auth', False))
        self.assertEqual(self.login().status_code,401)
        self.assertEqual(self.login(NEW_PASSWORD).status_code,200)
        with self.client.session_transaction() as s:
            self.assertEqual(s['tg_user_id'],user_id)
        self.assertEqual(verify_auth_token(create_auth_token(user_id)),user_id)
        self.notice.assert_called_once()

    def test_expiry_and_superseded_link(self):
        self.request(); old = self.token(); self.clear_limits(); self.request()
        self.assertEqual(self.save(token=old).status_code,400)
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute('UPDATE email_auth_links SET created=created-1801')
        self.assertEqual(self.save().status_code,400)

    def test_existing_google_account_preserved(self):
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute("INSERT INTO users (user_id,is_active) VALUES ('g_existing',1)")
            c.execute("INSERT INTO auth_identities (provider,external_id,user_id,email) VALUES ('google','existing','g_existing','test@example.com')")
        self.request(); self.assertEqual(self.save().status_code,200)
        with self.client.session_transaction() as s:
            self.assertEqual(s['tg_user_id'],'g_existing')

    def test_legacy_email_user_can_set_first_password(self):
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute("INSERT INTO users (user_id,is_active,auth_provider) VALUES ('e_legacy',1,'email')")
            c.execute("INSERT INTO auth_identities (provider,external_id,user_id,email) VALUES ('email','test@example.com','e_legacy','test@example.com')")
        old_token = create_auth_token('e_legacy')
        self.request('reset'); self.assertEqual(self.save().status_code,200)
        self.assertEqual(verify_auth_token(old_token),'')
        with self.client.session_transaction() as s:
            self.assertEqual(s['tg_user_id'],'e_legacy')

    def test_limits_unknown_reset_and_disabled_user(self):
        self.assertEqual(self.request('reset').status_code,200); self.mail.assert_not_called()
        self.assertEqual(self.request('reset').status_code,429)
        self.clear_limits(); user_id=self.create_user()
        with closing(sqlite3.connect(Config.DB_PATH)) as c, c:
            c.execute('UPDATE users SET is_active=0 WHERE user_id=?',(user_id,))
        self.assertEqual(self.login().status_code,401)
        for _ in range(9):self.assertEqual(self.login('incorrect').status_code,401)
        self.assertEqual(self.login('incorrect').status_code,429)

    def test_delivery_failure_invalid_requests_and_invalid_token(self):
        self.assertEqual(self.client.post('/api/auth/email/request',json=[]).status_code,400)
        self.assertEqual(self.client.post('/api/auth/email/request',data={'email':'test@example.com'}).status_code,400)
        self.mail.side_effect=OSError('private recipient data')
        self.assertEqual(self.request().status_code,503)
        self.assertEqual(self.save().status_code,400)
        self.assertEqual(self.client.post('/api/auth/email/link',json={'token':[]}).status_code,400)

    def test_android_handoff_survives_other_browser(self):
        self.client.get('/auth/email?android=1&next=//evil.example&lang=en')
        self.request()
        result = self.save(client=self.app.test_client())
        self.assertTrue(result.json['next'].startswith('learnwords://auth?'))
        self.assertIn('auth=',result.json['next'])

    def test_language_precedence_and_all_templates(self):
        page=self.client.get('/auth/email?lang=en',headers={'Accept-Language':'ru'})
        self.assertIn('<html lang="en">',page.text)
        self.assertNotIn(TEXT['ru']['forgot'],page.text)
        self.request(language='nl'); self.assertEqual(self.mail.call_args.args[3],'nl')
        for language,text in TEXT.items():
            with self.app.test_request_context():
                from flask import render_template
                html=render_template('email_message.html',language=language,text=text,prefix='setup',link='https://app.parallellingvo.app/auth/email/complete#token=test')
                self.assertIn(text['setup_title'],html)
                for complete in (False,True):
                    html=render_template('email_auth.html',language=language,text=text,languages={language:language},complete=complete)
                    self.assertIn('<html lang="'+language+'">',html)

    def test_starttls_and_multipart_localized_email(self):
        with self.app.app_context(), patch.object(Config,'SMTP_PORT',587), patch('app.email_auth.smtplib.SMTP') as transport:
            _send_auth_mail('test@example.com','A'*43,'setup','en')
            smtp=transport.return_value.__enter__.return_value
            self.assertEqual([call[0] for call in smtp.method_calls],['starttls','login','send_message'])
            message=smtp.send_message.call_args.args[0]
            self.assertEqual(message.get_content_type(),'multipart/alternative')
            self.assertIn(TEXT['en']['setup_title'],message['Subject'])
            self.assertNotIn(TEXT['ru']['setup_title'],message.as_string())
            self.assertIn('#token=',message.get_body(preferencelist=('plain',)).get_content())


if __name__=='__main__':unittest.main()
