"""Browser-to-Android handoff bound to a verifier held only by the app."""
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from functools import lru_cache
from contextlib import closing
from urllib.parse import urlencode, quote

from flask import Blueprint, jsonify, render_template, request, session
from config import Config
from app.auth_links import create_auth_token, email_credential_version, verify_auth_token

android_auth_bp = Blueprint('android_auth', __name__)
# App URL generated for the Android native app in BotFather, not the OAuth client ID.
TELEGRAM_ANDROID_REDIRECT_URI = 'https://app4151474097-login.tg.dev/tglogin'


def _conn():
    c = sqlite3.connect(Config.DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    return c


def ensure_android_auth_schema():
    with closing(_conn()) as c, c:
        c.execute('''CREATE TABLE IF NOT EXISTS android_auth_flows (
            id TEXT PRIMARY KEY, challenge TEXT NOT NULL, provider TEXT NOT NULL,
            created INTEGER NOT NULL, ip_hash TEXT NOT NULL, user_id TEXT,
            version TEXT, error TEXT, delivered INTEGER)''')
        c.execute('CREATE INDEX IF NOT EXISTS android_auth_ip ON android_auth_flows(ip_hash,created)')
        columns = {row[1] for row in c.execute('PRAGMA table_info(android_auth_flows)')}
        for name in ('link_owner', 'link_version', 'link_generation', 'link_payload', 'native_token_hash'):
            if name not in columns:
                c.execute('ALTER TABLE android_auth_flows ADD COLUMN ' + name + ' TEXT')
        c.execute('CREATE UNIQUE INDEX IF NOT EXISTS android_native_token ON android_auth_flows(native_token_hash)')
        c.execute('''CREATE TABLE IF NOT EXISTS android_browser_links (
            ticket_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires INTEGER NOT NULL,
            version TEXT, generation TEXT NOT NULL)''')


@android_auth_bp.post('/api/auth/android/browser-link')
def create_browser_link():
    auth = request.headers.get('Authorization', '')
    uid = verify_auth_token(auth[7:]) if auth.lower().startswith('bearer ') else ''
    if not uid:
        return jsonify(ok=False, error='not_authenticated'), 401
    from app.account_privacy import generation
    now = int(time.time())
    ticket = secrets.token_urlsafe(32)
    with closing(_conn()) as c, c:
        if not c.execute('SELECT 1 FROM users WHERE user_id=? AND is_active=1', (uid,)).fetchone():
            return jsonify(ok=False, error='not_authenticated'), 401
        c.execute('DELETE FROM android_browser_links WHERE expires<=? OR user_id=?', (now, uid))
        c.execute('INSERT INTO android_browser_links VALUES (?,?,?,?,?)',
                  (hashlib.sha256(ticket.encode()).hexdigest(), uid, now + 60,
                   email_credential_version(uid), generation(uid)))
    language = request.headers.get('X-Device-Language', 'en').split('-')[0]
    url = Config.APP_BASE_URL.rstrip('/') + '/auth/android/browser?' + urlencode({'lang': language}) + '#' + ticket
    response = jsonify(ok=True, browser_url=url)
    response.headers['Cache-Control'] = 'no-store'
    return response


@android_auth_bp.get('/auth/android/browser')
def browser_link_page():
    response = render_template('android_browser_login.html', russian=request.args.get('lang') == 'ru')
    return response, 200, {'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'}


@android_auth_bp.post('/api/auth/android/browser-session')
def consume_browser_link():
    data = request.get_json(silent=True)
    ticket = data.get('ticket') if isinstance(data, dict) else None
    if not isinstance(ticket, str) or not re.fullmatch('[A-Za-z0-9_-]{43}', ticket):
        return jsonify(ok=False, error='invalid_link'), 400
    from app.account_privacy import generation
    from app.auth_links import bind_email_session
    with closing(_conn()) as c, c:
        c.execute('BEGIN IMMEDIATE')
        row = c.execute('SELECT * FROM android_browser_links WHERE ticket_hash=? AND expires>?',
                        (hashlib.sha256(ticket.encode()).hexdigest(), int(time.time()))).fetchone()
        if not row:
            return jsonify(ok=False, error='invalid_link'), 400
        user = c.execute('SELECT * FROM users WHERE user_id=? AND is_active=1', (row['user_id'],)).fetchone()
        if (not user or row['version'] != email_credential_version(row['user_id'])
                or row['generation'] != generation(row['user_id'])):
            return jsonify(ok=False, error='invalid_link'), 400
        c.execute('DELETE FROM android_browser_links WHERE ticket_hash=?', (row['ticket_hash'],))
    # Replace any other browser account and discard its pending login/link flows.
    session.clear()
    session.update(is_auth=True, tg_user_id=str(user['user_id']),
                   tg_username=user['username'] or '', tg_first_name=user['first_name'] or '',
                   tg_last_name=user['last_name'] or '', auth_provider=user['auth_provider'] or 'android',
                   account_generation=row['generation'])
    bind_email_session(row['user_id'])
    session.permanent = True
    response = jsonify(ok=True, next='/settings/mcp')
    response.headers['Cache-Control'] = 'no-store'
    return response


def link_owner(flow, provider):
    with closing(_conn()) as c:
        row = c.execute('SELECT link_owner FROM android_auth_flows WHERE id=? AND provider=? AND created>? AND user_id IS NULL AND error IS NULL',
                        (str(flow), provider, int(time.time()) - 3600)).fetchone()
    return str(row[0]) if row and row[0] else None


def complete_link_flow(flow, provider, payload):
    with closing(_conn()) as c, c:
        c.execute('''UPDATE android_auth_flows SET user_id=link_owner,version=link_version,link_payload=?
            WHERE id=? AND provider=? AND link_owner IS NOT NULL AND created>? AND user_id IS NULL AND error IS NULL''',
                  (json.dumps(payload), flow, provider, int(time.time()) - 3600))
    return Config.APP_BASE_URL.rstrip('/') + '/auth/android/return?' + urlencode({'flow': flow})


@android_auth_bp.get('/api/account/identities')
def identities():
    auth = request.headers.get('Authorization', '')
    uid = verify_auth_token(auth[7:]) if auth.lower().startswith('bearer ') else ''
    if not uid:
        return jsonify(ok=False, error='not_authenticated'), 401
    with closing(_conn()) as c:
        if not c.execute('SELECT 1 FROM users WHERE user_id=? AND is_active=1', (uid,)).fetchone():
            return jsonify(ok=False, error='not_authenticated'), 401
        telegram = c.execute("SELECT 1 FROM auth_identities WHERE user_id=? AND provider='telegram'", (uid,)).fetchone()
        email = c.execute('SELECT email FROM email_auth_credentials WHERE user_id=?', (uid,)).fetchone()
    return jsonify(ok=True, telegram_linked=bool(telegram) or uid.isdigit(), email=email[0] if email else None)


def valid_android_flow(flow, provider):
    with closing(_conn()) as c:
        return bool(c.execute('SELECT 1 FROM android_auth_flows WHERE id=? AND provider=? AND created>? AND user_id IS NULL AND error IS NULL',
                              (str(flow), provider, int(time.time()) - 3600)).fetchone())


def complete_android_flow(flow, user_id, provider, error=''):
    with closing(_conn()) as c, c:
        c.execute('''UPDATE android_auth_flows SET user_id=?,version=?,error=?
            WHERE id=? AND provider=? AND created>? AND user_id IS NULL AND error IS NULL''',
                  (user_id or None, email_credential_version(user_id) if user_id else None, error or None,
                   flow, provider, int(time.time()) - 3600))
    return Config.APP_BASE_URL.rstrip('/') + '/auth/android/return?' + urlencode({'flow': flow})


@android_auth_bp.post('/api/auth/android/start')
def start():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.get('provider') not in ('telegram', 'email'):
        return jsonify(ok=False, error='invalid_request'), 400
    native = data.get('transport') == 'native'
    client_id = str(Config.TELEGRAM_OIDC_CLIENT_ID or '')
    if native and (data['provider'] != 'telegram' or not client_id.isdigit()):
        return jsonify(ok=False, error='telegram_auth_not_configured'), 501
    challenge = str(data.get('challenge') or '')
    if not re.fullmatch('[a-f0-9]{64}', challenge):
        return jsonify(ok=False, error='invalid_request'), 400
    now = int(time.time())
    owner = None
    if data.get('mode') == 'link':
        auth = request.headers.get('Authorization', '')
        owner = verify_auth_token(auth[7:]) if auth.lower().startswith('bearer ') else ''
        if not owner:
            return jsonify(ok=False, error='not_authenticated'), 401
    ip_hash = hmac.new(Config.SECRET_KEY.encode(), (request.remote_addr or '').encode(), hashlib.sha256).hexdigest()
    flow = secrets.token_urlsafe(32)
    with closing(_conn()) as c, c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('DELETE FROM android_auth_flows WHERE created<?', (now - 3600,))
        if c.execute('SELECT COUNT(*) FROM android_auth_flows WHERE ip_hash=? AND created>?', (ip_hash, now - 900)).fetchone()[0] >= 20:
            return jsonify(ok=False, error='rate_limited'), 429
        if owner and not c.execute('SELECT 1 FROM users WHERE user_id=? AND is_active=1', (owner,)).fetchone():
            return jsonify(ok=False, error='not_authenticated'), 401
        owner_generation = None
        if owner:
            from app.account_privacy import generation
            owner_generation = generation(owner)
        c.execute('INSERT INTO android_auth_flows (id,challenge,provider,created,ip_hash,link_owner,link_version,link_generation) VALUES (?,?,?,?,?,?,?,?)',
                  (flow, challenge, data['provider'], now, ip_hash, owner,
                   email_credential_version(owner) if owner else None, owner_generation))
    params = {'android': '1', 'flow': flow, 'lang': str(data.get('language') or 'en')[:8]}
    if data['provider'] == 'email':
        params['mode'] = 'setup' if owner else (data.get('mode') if data.get('mode') in ('setup', 'reset') else 'login')
    url = Config.APP_BASE_URL.rstrip('/') + '/auth/' + data['provider'] + '?' + urlencode(params)
    return jsonify(ok=True, flow_id=flow, browser_url=url,
                   client_id=client_id if native else None,
                   redirect_uri=TELEGRAM_ANDROID_REDIRECT_URI if native else None)


@lru_cache(maxsize=2)
def _telegram_keys(bucket):
    import requests
    response = requests.get('https://oauth.telegram.org/.well-known/jwks.json', timeout=10)
    response.raise_for_status()
    return response.json()


def _verify_native_telegram_token(token):
    from authlib.jose import JsonWebToken
    claims = JsonWebToken(['RS256', 'ES256', 'EdDSA', 'ES256K']).decode(
        token, _telegram_keys(int(time.time()) // 300), claims_options={
            'iss': {'essential': True, 'value': 'https://oauth.telegram.org'},
            'aud': {'essential': True, 'value': str(Config.TELEGRAM_OIDC_CLIENT_ID)},
            'exp': {'essential': True}, 'iat': {'essential': True},
            'sub': {'essential': True},
        })
    claims.validate(leeway=30)
    return claims


def _native_telegram_user(claims):
    telegram_id = str(claims.get('id') or '')
    name = str(claims.get('name') or '').strip().split(maxsplit=1)
    user = {'id': telegram_id, 'username': str(claims.get('preferred_username') or ''),
            'first_name': str(claims.get('given_name') or (name[0] if name else '')),
            'last_name': str(claims.get('family_name') or (name[1] if len(name) > 1 else '')),
            'photo_url': str(claims.get('picture') or '')}
    from app.routes import _upsert_user, _has_telegram_identity, _notify_admins_new_user
    if not _has_telegram_identity(user):
        raise ValueError('telegram_name_or_username_required')
    from app.account_linking import telegram_account_id
    uid = telegram_account_id(telegram_id)
    if _upsert_user(user):
        _notify_admins_new_user(user)
    with closing(_conn()) as c, c:
        c.execute("INSERT OR IGNORE INTO auth_identities (provider,external_id,user_id) VALUES ('telegram',?,?)",
                  (telegram_id, uid))
    return uid


@android_auth_bp.post('/api/auth/telegram/native')
def native_telegram():
    import requests
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(ok=False, error='invalid_request'), 400
    verifier, token = data.get('verifier'), data.get('id_token')
    if (not isinstance(verifier, str) or not re.fullmatch('[A-Za-z0-9_-]{43,128}', verifier)
            or not isinstance(token, str) or not 1 <= len(token) <= 16384):
        return jsonify(ok=False, error='invalid_request'), 400
    flow = str(data.get('flow_id') or '')
    digest = hashlib.sha256(token.encode()).hexdigest()
    with closing(_conn()) as c:
        row = c.execute('SELECT * FROM android_auth_flows WHERE id=?', (flow,)).fetchone()
        if (not row or row['provider'] != 'telegram' or row['error'] or row['created'] < time.time() - 3600
                or not hmac.compare_digest(row['challenge'], hashlib.sha256(verifier.encode()).hexdigest())):
            return jsonify(ok=False, error='invalid_auth_link'), 400
        if row['native_token_hash'] == digest:
            return jsonify(ok=True)
        if row['user_id'] or c.execute('SELECT 1 FROM android_auth_flows WHERE native_token_hash=?', (digest,)).fetchone():
            return jsonify(ok=False, error='invalid_auth_link'), 400
    try:
        claims = _verify_native_telegram_token(token)
        telegram_id = str(claims.get('id') or '')
        if not telegram_id.isdigit() or int(telegram_id) <= 0 or claims['iat'] < row['created'] - 60:
            raise ValueError('invalid_token')
    except requests.RequestException:
        return jsonify(ok=False, error='telegram_unavailable'), 503
    except Exception:
        return jsonify(ok=False, error='invalid_token'), 401
    if row['link_owner']:
        uid, version = row['link_owner'], row['link_version']
        payload = json.dumps({'external_id': telegram_id})
    else:
        try:
            uid = _native_telegram_user(claims)
        except ValueError:
            return jsonify(ok=False, error='telegram_name_or_username_required'), 400
        version, payload = email_credential_version(uid), None
    try:
        with closing(_conn()) as c, c:
            result = c.execute('''UPDATE android_auth_flows SET user_id=?,version=?,link_payload=?,native_token_hash=?
                WHERE id=? AND user_id IS NULL AND error IS NULL AND created>?''',
                               (uid, version, payload, digest, flow, int(time.time()) - 3600))
            if not result.rowcount:
                return jsonify(ok=False, error='invalid_auth_link'), 400
    except sqlite3.IntegrityError:
        return jsonify(ok=False, error='invalid_auth_link'), 400
    return jsonify(ok=True)


@android_auth_bp.post('/api/auth/android/exchange')
def exchange():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(ok=False, error='invalid_auth_link'), 400
    verifier = data.get('verifier')
    if not isinstance(verifier, str) or not re.fullmatch('[A-Za-z0-9_-]{43,128}', verifier):
        return jsonify(ok=False, error='invalid_auth_link'), 400
    now = int(time.time())
    with closing(_conn()) as c, c:
        c.execute('BEGIN IMMEDIATE')
        row = c.execute('SELECT * FROM android_auth_flows WHERE id=?', (str(data.get('flow_id') or ''),)).fetchone()
        if not row or row['created'] < now - 3600 or not hmac.compare_digest(row['challenge'], hashlib.sha256(verifier.encode()).hexdigest()):
            return jsonify(ok=False, error='invalid_auth_link'), 400
        if row['error']:
            return jsonify(ok=False, error='authentication_failed'), 400
        if not row['user_id']:
            return jsonify(ok=True, pending=True), 202
        if row['link_owner'] and row['delivered'] is None:
            from app.account_privacy import generation
            if row['link_version'] != email_credential_version(row['link_owner']) or row['link_generation'] != generation(row['link_owner']):
                return jsonify(ok=False, error='invalid_auth_link'), 400
            from app.account_linking import attach_identity
            payload = json.loads(row['link_payload'] or '{}')
            if row['user_id'] != row['link_owner'] or not payload.get('external_id'):
                return jsonify(ok=False, error='invalid_auth_link'), 400
            try:
                if payload.get('confirmed_link'):
                    if row['provider'] != 'email' or not c.execute(
                            'SELECT 1 FROM email_auth_credentials WHERE user_id=? AND email=? AND version=?',
                            (row['link_owner'], payload['external_id'], payload.get('version'))).fetchone():
                        return jsonify(ok=False, error='invalid_auth_link'), 400
                else:
                    attach_identity(c, row['link_owner'], row['provider'], payload['external_id'], payload.get('password_hash'), payload.get('version'))
            except ValueError as error:
                return jsonify(ok=False, error=str(error)), 409
            c.execute('UPDATE android_auth_flows SET version=?,link_payload=NULL WHERE id=?',
                      (payload.get('version') if row['provider'] == 'email' else row['link_version'], row['id']))
            row = c.execute('SELECT * FROM android_auth_flows WHERE id=?', (row['id'],)).fetchone()
        # A brief retry window makes a lost response/process restart recoverable.
        if row['delivered'] is not None and row['delivered'] < now - 60:
            return jsonify(ok=False, error='invalid_auth_link'), 400
        user = c.execute('SELECT is_active FROM users WHERE user_id=?', (row['user_id'],)).fetchone()
        credential = c.execute('SELECT version FROM email_auth_credentials WHERE user_id=?', (row['user_id'],)).fetchone()
        current_version = credential[0] if credential else None
        if not user or not user['is_active'] or current_version != row['version']:
            return jsonify(ok=False, error='invalid_auth_link'), 400
        if row['delivered'] is None:
            c.execute('UPDATE android_auth_flows SET delivered=? WHERE id=?', (now, row['id']))
        token = create_auth_token(row['user_id'], email_version=row['version'])
    return jsonify(ok=True, pending=False, user_id=row['user_id'], token=token, provider=row['provider'])


@android_auth_bp.get('/auth/android/return')
def return_page():
    flow = str(request.args.get('flow') or '')
    if not re.fullmatch('[A-Za-z0-9_-]{43}', flow):
        return 'Invalid authentication link', 400
    browser_url = Config.APP_BASE_URL.rstrip('/') + '/settings'
    intent = ('intent://auth?flow=' + flow + '#Intent;scheme=learnwords;package=app.parallellingvo;'
              'S.browser_fallback_url=' + quote(browser_url, safe='') + ';end')
    from flask import session
    from app.email_auth_i18n import TEXT
    language = session.get('email_language', 'en')
    response = render_template('android_auth_return.html', intent_url=intent, browser_url=browser_url,
                               text=TEXT.get(language, TEXT['en']))
    return response, 200, {'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'}
