"""Email/password accounts with single-use setup and recovery links."""
import hashlib
import hmac
import json
import logging
import re
import secrets
import smtplib
import sqlite3
import ssl
import time
from contextlib import closing
from email.message import EmailMessage
from urllib.parse import urlencode

from flask import Blueprint, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config
from app.auth_links import create_auth_token, email_credential_version
from app.email_auth_i18n import TEXT, LANGUAGES

email_bp = Blueprint('email_auth', __name__)
log = logging.getLogger(__name__)
PASSWORD_METHOD = 'pbkdf2:sha256:600000'
# A real hash keeps unknown-account login checks comparable to known accounts.
_DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(32), method=PASSWORD_METHOD)


def _conn():
    connection = sqlite3.connect(Config.DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_email_auth_schema():
    with closing(_conn()) as c, c:
        c.execute('''CREATE TABLE IF NOT EXISTS email_auth_credentials (
            user_id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL, version TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS email_auth_links (
            token_hash TEXT PRIMARY KEY, email TEXT NOT NULL, purpose TEXT NOT NULL,
            created INTEGER NOT NULL, consumed INTEGER NOT NULL DEFAULT 0,
            language TEXT NOT NULL, next_url TEXT NOT NULL, android INTEGER NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS email_auth_attempts (
            email_hash TEXT NOT NULL, ip_hash TEXT NOT NULL, kind TEXT NOT NULL,
            created INTEGER NOT NULL)''')
        c.execute('CREATE INDEX IF NOT EXISTS email_attempt_address ON email_auth_attempts(email_hash,kind,created)')
        c.execute('CREATE INDEX IF NOT EXISTS email_attempt_ip ON email_auth_attempts(ip_hash,kind,created)')
        columns = {r[1] for r in c.execute('PRAGMA table_info(email_auth_links)')}
        if 'android_flow' not in columns:
            c.execute('ALTER TABLE email_auth_links ADD COLUMN android_flow TEXT')


@email_bp.record_once
def _register_session_check(state):
    @state.app.before_request
    def check_email_session():
        if session.get('is_auth') and ('email_auth_version' in session or session.get('auth_provider') == 'email'):
            version = email_credential_version(str(session.get('tg_user_id') or ''))
            if version is not None and session.get('email_auth_version') != version:
                session.clear()

    @state.app.after_request
    def private_email_pages(response):
        if request.path.startswith(('/auth/email', '/api/auth/email/')):
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Referrer-Policy'] = 'no-referrer'
        return response


def _data():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _language(data=None):
    value = request.args.get('lang') or (data or {}).get('language') or session.get('email_language')
    language = str(value or '').lower().split('-')[0]
    if language not in TEXT:
        language = request.accept_languages.best_match(list(TEXT)) or 'en'
    return language


def _safe_next(value):
    value = str(value or '/upload')
    return value if value.startswith('/') and not value.startswith('//') and '\\' not in value and not any(ord(x) < 32 for x in value) else '/upload'


def _email(data):
    value = str(data.get('email') or '').strip().lower()
    if len(value) <= 254 and re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}", value):
        return value
    return ''


def _hash(value):
    return hmac.new(Config.SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()


def _rate_limit(email, kind):
    now = int(time.time())
    address, ip = _hash('email:' + email), _hash('ip:' + (request.remote_addr or 'unknown'))
    with closing(_conn()) as c, c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('DELETE FROM email_auth_attempts WHERE created < ?', (now - 3600,))
        recent = c.execute('SELECT MAX(created),COUNT(*) FROM email_auth_attempts WHERE email_hash=? AND kind=?', (address, kind)).fetchone()
        ip_count = c.execute('SELECT COUNT(*) FROM email_auth_attempts WHERE ip_hash=? AND kind=?', (ip, kind)).fetchone()[0]
        if kind == 'mail':
            blocked = (recent[0] is not None and recent[0] > now - 60) or recent[1] >= 5 or ip_count >= 20
        else:
            count = c.execute('SELECT COUNT(*) FROM email_auth_attempts WHERE email_hash=? AND kind=? AND created>?', (address, kind, now - 900)).fetchone()[0]
            blocked = count >= 10 or ip_count >= 100
        if blocked:
            return False
        c.execute('INSERT INTO email_auth_attempts VALUES (?,?,?,?)', (address, ip, kind, now))
    return True


def _send_auth_mail(email, token, purpose, language):
    text = dict(TEXT[language])
    if purpose == 'native_link':
        text.update(setup_title=text['link'], setup_body=text['native_link_body'], setup_action=text['link'])
    prefix = 'reset' if purpose == 'reset' else 'setup'
    link = Config.APP_BASE_URL.rstrip('/') + '/auth/email/complete?' + urlencode({'lang': language}) + '#token=' + token
    message = EmailMessage()
    message['From'] = 'ParallelLingvo <accounts@parallellingvo.app>'
    message['To'] = email
    message['Subject'] = text[prefix + '_title'] + ' — ParallelLingvo'
    message.set_content('\n\n'.join(['ParallelLingvo', text[prefix + '_title'], text[prefix + '_body'], link, text['expiry'], text['ignore']]))
    message.add_alternative(render_template('email_message.html', text=text, prefix=prefix, link=link, language=language), subtype='html')
    context = ssl.create_default_context()
    connection = (smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20, context=context)
                  if Config.SMTP_PORT == 465 else smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20))
    with connection as smtp:
        if Config.SMTP_PORT != 465:
            smtp.starttls(context=context)
        smtp.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        smtp.send_message(message)


@email_bp.get('/auth/email')
@email_bp.get('/auth/email/complete')
def email_page():
    from app.android_auth import link_owner
    language = _language()
    session['email_language'] = language
    if request.path == '/auth/email':
        session['email_android'] = request.args.get('android') == '1'
        session['email_next'] = _safe_next(request.args.get('next'))
        flow = request.args.get('flow', '') if session['email_android'] else ''
        if flow:
            from app.android_auth import valid_android_flow
            if not valid_android_flow(flow, 'email'):
                return 'Invalid authentication attempt', 400
        session['email_android_flow'] = flow
    return render_template('email_auth.html', language=language, text=TEXT[language], languages=LANGUAGES,
                           complete=request.path.endswith('/complete'),
                           linking=bool(session.get('email_android_flow') and link_owner(session['email_android_flow'], 'email')),
                           initial_mode=request.args.get('mode') if request.args.get('mode') in ('setup', 'reset') else 'login')


@email_bp.post('/api/auth/email/request')
def request_link():
    if not request.is_json:
        return jsonify(ok=False, error='invalid_email'), 400
    if not Config.SMTP_PASSWORD or Config.SECRET_KEY == 'dev-key':
        return jsonify(ok=False, error='email_unavailable'), 503
    data = _data()
    email = _email(data)
    if not email:
        return jsonify(ok=False, error='invalid_email'), 400
    if not _rate_limit(email, 'mail'):
        return jsonify(ok=False, error='rate_limited'), 429
    language = _language(data)
    purpose = 'reset' if data.get('mode') == 'reset' else 'setup'
    from app.android_auth import link_owner, valid_android_flow
    flow = session.get('email_android_flow')
    if flow and not valid_android_flow(flow, 'email'):
        return jsonify(ok=False, error='invalid_link'), 400
    if flow and link_owner(flow, 'email'):
        purpose = 'link'
    token = secrets.token_urlsafe(32)
    token_hash = _hash('link:' + token)
    now = int(time.time())
    with closing(_conn()) as c, c:
        c.execute('BEGIN IMMEDIATE')
        credentials = c.execute('SELECT 1 FROM email_auth_credentials WHERE email=?', (email,)).fetchone()
        legacy = c.execute("SELECT 1 FROM auth_identities WHERE provider='email' AND external_id=?", (email,)).fetchone()
        if purpose == 'reset' and not credentials and not legacy:
            return jsonify(ok=True, resend_after=60)
        if purpose == 'setup' and credentials:
            # An existing owner receives a recovery link instead of losing access.
            purpose = 'reset'
        c.execute('DELETE FROM email_auth_links WHERE created < ?', (now - 86400,))
        c.execute('UPDATE email_auth_links SET consumed=1 WHERE email=?', (email,))
        c.execute('INSERT INTO email_auth_links (token_hash,email,purpose,created,language,next_url,android,android_flow) VALUES (?,?,?,?,?,?,?,?)',
                  (token_hash, email, purpose, now, language, _safe_next(session.get('email_next')), int(bool(session.get('email_android'))), session.get('email_android_flow')))
    try:
        _send_auth_mail(email, token, purpose, language)
    except (OSError, smtplib.SMTPException):
        log.warning('Email authentication delivery failed')
        with closing(_conn()) as c, c:
            c.execute('UPDATE email_auth_links SET consumed=1 WHERE token_hash=?', (token_hash,))
        return jsonify(ok=False, error='email_unavailable'), 503
    return jsonify(ok=True, resend_after=60)


def _link(c, token):
    if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
        return None
    return c.execute('SELECT * FROM email_auth_links WHERE token_hash=? AND consumed=0 AND created>?',
                     (_hash('link:' + token), int(time.time()) - 1800)).fetchone()


@email_bp.post('/api/auth/email/link')
def inspect_link():
    with closing(_conn()) as c:
        row = _link(c, _data().get('token'))
    if not row:
        return jsonify(ok=False, error='invalid_link'), 400
    return jsonify(ok=True, language=row['language'], purpose=row['purpose'],
                   email=row['email'] if row['purpose'] == 'native_link' else None)


def _pending_native_email_flow(c, flow, owner=None, verifier=None):
    from app.account_privacy import generation
    row = c.execute('SELECT * FROM android_auth_flows WHERE id=?', (str(flow or ''),)).fetchone()
    if (not row or row['provider'] != 'email' or not row['link_owner'] or row['user_id']
            or row['error'] or row['created'] < time.time() - 3600):
        return None
    if owner is not None and row['link_owner'] != owner:
        return None
    if verifier is not None and (not isinstance(verifier, str)
            or not re.fullmatch('[A-Za-z0-9_-]{43,128}', verifier)
            or not hmac.compare_digest(row['challenge'], hashlib.sha256(verifier.encode()).hexdigest())):
        return None
    if not c.execute('SELECT 1 FROM users WHERE user_id=? AND is_active=1', (row['link_owner'],)).fetchone():
        return None
    credential = c.execute('SELECT version FROM email_auth_credentials WHERE user_id=?', (row['link_owner'],)).fetchone()
    if row['link_version'] != (credential[0] if credential else None) or row['link_generation'] != generation(row['link_owner']):
        return None
    return row


@email_bp.post('/api/account/email/link')
def request_native_email_link():
    from app.auth_links import verify_auth_token
    auth = request.headers.get('Authorization', '')
    owner = verify_auth_token(auth[7:]) if auth.lower().startswith('bearer ') else ''
    if not owner:
        return jsonify(ok=False, error='not_authenticated'), 401
    data = _data()
    email, password = _email(data), data.get('password')
    if not isinstance(data.get('verifier'), str):
        return jsonify(ok=False, error='invalid_auth_link'), 400
    if not email:
        return jsonify(ok=False, error='invalid_email'), 400
    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        return jsonify(ok=False, error='weak_password'), 400
    if password != data.get('password_confirmation'):
        return jsonify(ok=False, error='password_mismatch'), 400
    if not Config.SMTP_PASSWORD or Config.SECRET_KEY == 'dev-key':
        return jsonify(ok=False, error='email_unavailable'), 503
    with closing(_conn()) as c:
        if not _pending_native_email_flow(c, data.get('flow_id'), owner, data.get('verifier', '')):
            return jsonify(ok=False, error='invalid_auth_link'), 400
    if not _rate_limit(email, 'mail'):
        return jsonify(ok=False, error='rate_limited'), 429
    password_hash = generate_password_hash(password, method=PASSWORD_METHOD)
    version, token = secrets.token_hex(16), secrets.token_urlsafe(32)
    token_hash, language = _hash('link:' + token), _language(data)
    with closing(_conn()) as c, c:
        c.execute('BEGIN IMMEDIATE')
        flow = _pending_native_email_flow(c, data.get('flow_id'), owner, data.get('verifier', ''))
        if not flow:
            return jsonify(ok=False, error='invalid_auth_link'), 400
        if c.execute('SELECT 1 FROM email_auth_credentials WHERE user_id=? OR email=?', (owner, email)).fetchone():
            return jsonify(ok=False, error='identity_conflict'), 409
        c.execute("UPDATE android_auth_flows SET error='superseded' WHERE link_owner=? AND provider='email' AND id<>? AND user_id IS NULL AND error IS NULL",
                  (owner, flow['id']))
        payload = json.dumps({'external_id': email, 'password_hash': password_hash, 'version': version})
        c.execute('UPDATE android_auth_flows SET link_payload=? WHERE id=?', (payload, flow['id']))
        c.execute('UPDATE email_auth_links SET consumed=1 WHERE email=? OR android_flow=?', (email, flow['id']))
        c.execute('INSERT INTO email_auth_links (token_hash,email,purpose,created,language,next_url,android,android_flow) VALUES (?,?,?,?,?,?,1,?)',
                  (token_hash, email, 'native_link', int(time.time()), language, '/settings', flow['id']))
    try:
        _send_auth_mail(email, token, 'native_link', language)
    except (OSError, smtplib.SMTPException):
        with closing(_conn()) as c, c:
            c.execute('UPDATE email_auth_links SET consumed=1 WHERE token_hash=?', (token_hash,))
        return jsonify(ok=False, error='email_unavailable'), 503
    return jsonify(ok=True, resend_after=60)


@email_bp.post('/api/auth/email/confirm')
def confirm_native_email_link():
    from app.account_linking import attach_identity
    data = _data()
    with closing(_conn()) as c, c:
        c.execute('BEGIN IMMEDIATE')
        link = _link(c, data.get('token'))
        if not link or link['purpose'] != 'native_link':
            return jsonify(ok=False, error='invalid_link'), 400
        flow = _pending_native_email_flow(c, link['android_flow'])
        payload = json.loads(flow['link_payload'] or '{}') if flow else {}
        if (not flow or payload.get('external_id') != link['email']
                or not payload.get('password_hash') or not payload.get('version')):
            return jsonify(ok=False, error='invalid_link'), 400
        try:
            attach_identity(c, flow['link_owner'], 'email', link['email'], payload['password_hash'], payload['version'])
        except ValueError as error:
            return jsonify(ok=False, error=str(error)), 409
        confirmed = json.dumps({'external_id': link['email'], 'version': payload['version'], 'confirmed_link': True})
        c.execute('UPDATE android_auth_flows SET user_id=link_owner,version=?,link_version=?,link_payload=? WHERE id=?',
                  (payload['version'], payload['version'], confirmed, flow['id']))
        c.execute('UPDATE email_auth_links SET consumed=1 WHERE token_hash=?', (link['token_hash'],))
        user = c.execute('SELECT * FROM users WHERE user_id=?', (flow['link_owner'],)).fetchone()
    return _finish_login(user, payload['version'], android=True, language=link['language'], flow=flow['id'])


def _owner(c, email):
    owner = c.execute("SELECT user_id FROM auth_identities WHERE provider='email' AND external_id=?", (email,)).fetchone()
    if owner:
        return str(owner[0]), False
    owners = c.execute("SELECT DISTINCT user_id FROM auth_identities WHERE provider='google' AND lower(email)=?", (email,)).fetchall()
    if len(owners) > 1:
        return None, False
    user_id = str(owners[0][0]) if owners else 'e_' + secrets.token_hex(16)
    if not owners:
        c.execute("INSERT INTO users (user_id,username,first_name,last_name,is_active,auth_provider,account_type) VALUES (?,?,?,'',1,'email','pending')", (user_id, email, email.split('@')[0]))
    c.execute("INSERT INTO auth_identities (provider,external_id,user_id,email) VALUES ('email',?,?,?)", (email, user_id, email))
    return user_id, not owners


def _finish_login(user, version, android=False, target='/upload', language='en', flow='', native=False):
    session.clear()
    session.update(is_auth=True, tg_user_id=str(user['user_id']), tg_username=user['username'] or '',
                   tg_first_name=user['first_name'] or '', tg_last_name=user['last_name'] or '',
                   auth_provider='email', email_auth_version=version, email_language=language)
    session.permanent = True
    if native:
        return jsonify(ok=True, user_id=str(user['user_id']), token=create_auth_token(user['user_id'], email_version=version), provider='email')
    if android:
        if flow:
            from app.android_auth import complete_android_flow
            target = complete_android_flow(flow, str(user['user_id']), 'email')
        else:
            target = 'learnwords://auth?' + urlencode({'server': Config.APP_BASE_URL.rstrip('/'), 'auth': create_auth_token(user['user_id'], email_version=version), 'provider': 'email'})
    return jsonify(ok=True, next=_safe_next(target) if not android else target)


@email_bp.post('/api/auth/email/password')
def set_password():
    data = _data()
    password = data.get('password')
    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        return jsonify(ok=False, error='weak_password'), 400
    if password != data.get('password_confirmation'):
        return jsonify(ok=False, error='password_mismatch'), 400
    # Validate before the expensive password hash, then recheck under the write lock.
    with closing(_conn()) as c:
        link = _link(c, data.get('token'))
        if not link or link['purpose'] == 'native_link':
            return jsonify(ok=False, error='invalid_link'), 400
    password_hash = generate_password_hash(password, method=PASSWORD_METHOD)
    version = secrets.token_hex(16)
    with closing(_conn()) as c, c:
        c.execute('BEGIN IMMEDIATE')
        row = _link(c, data.get('token'))
        if not row or row['purpose'] == 'native_link':
            return jsonify(ok=False, error='invalid_link'), 400
        existing = c.execute('SELECT 1 FROM email_auth_credentials WHERE email=?', (row['email'],)).fetchone()
        if row['purpose'] == 'setup' and existing:
            return jsonify(ok=False, error='invalid_link'), 400
        if row['purpose'] == 'link':
            from app.android_auth import link_owner
            owner = link_owner(row['android_flow'], 'email')
            if not owner:
                return jsonify(ok=False, error='invalid_link'), 400
            payload = json.dumps({'external_id': row['email'], 'password_hash': password_hash, 'version': version})
            c.execute('''UPDATE android_auth_flows SET user_id=link_owner,version=link_version,link_payload=?
                WHERE id=? AND user_id IS NULL AND error IS NULL AND link_owner=?''', (payload, row['android_flow'], owner))
            c.execute('UPDATE email_auth_links SET consumed=1 WHERE token_hash=?', (row['token_hash'],))
            return jsonify(ok=True, next=Config.APP_BASE_URL.rstrip('/') + '/auth/android/return?' + urlencode({'flow': row['android_flow']}))
        user_id, is_new = _owner(c, row['email'])
        user = c.execute('SELECT * FROM users WHERE user_id=?', (user_id,)).fetchone() if user_id else None
        if not user or not user['is_active']:
            return jsonify(ok=False, error='invalid_link'), 400
        c.execute('''INSERT INTO email_auth_credentials (user_id,email,password_hash,version) VALUES (?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET password_hash=excluded.password_hash,version=excluded.version''',
                  (user_id, row['email'], password_hash, version))
        c.execute('UPDATE email_auth_links SET consumed=1 WHERE email=?', (row['email'],))
    if is_new:
        from app.routes import _notify_admins_new_user
        _notify_admins_new_user(dict(user))
    return _finish_login(user, version, bool(row['android']), row['next_url'], row['language'], flow=row['android_flow'])


@email_bp.post('/api/auth/email/login')
def password_login():
    data = _data()
    email, password = _email(data), data.get('password')
    if not email or not isinstance(password, str) or len(password) > 128:
        return jsonify(ok=False, error='invalid_credentials'), 401
    if not _rate_limit(email, 'login'):
        return jsonify(ok=False, error='rate_limited'), 429
    with closing(_conn()) as c:
        row = c.execute('''SELECT u.*, e.password_hash, e.version FROM email_auth_credentials e
            JOIN users u ON u.user_id=e.user_id WHERE e.email=?''', (email,)).fetchone()
    valid = check_password_hash(row['password_hash'] if row else _DUMMY_HASH, password)
    if not valid or not row or not row['is_active']:
        return jsonify(ok=False, error='invalid_credentials'), 401
    return _finish_login(row, row['version'], bool(session.get('email_android')),
                         _safe_next(session.get('email_next')), _language(data),
                         flow=session.get('email_android_flow', ''), native=data.get('client') == 'android')


@email_bp.post('/api/auth/email/verify')
def legacy_code_disabled():
    return jsonify(ok=False, error='invalid_link'), 410
