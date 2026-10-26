"""Attach verified login identities to an existing account, without merging data."""
import sqlite3
from contextlib import closing

from config import Config


def telegram_account_id(telegram_id, db_path=None):
    uid = str(telegram_id)
    with closing(sqlite3.connect(db_path or Config.DB_PATH)) as c:
        try:
            row = c.execute("SELECT user_id FROM auth_identities WHERE provider='telegram' AND external_id=?", (uid,)).fetchone()
        except sqlite3.OperationalError as error:
            if 'no such table' not in str(error):
                raise
            row = None
    return str(row[0]) if row else uid


def telegram_chat_id(user_id):
    with closing(sqlite3.connect(Config.DB_PATH)) as c:
        try:
            row = c.execute("SELECT external_id FROM auth_identities WHERE provider='telegram' AND user_id=?", (str(user_id),)).fetchone()
        except sqlite3.OperationalError as error:
            if 'no such table' not in str(error):
                raise
            row = None
    value = str(row[0]) if row else str(user_id)
    return int(value) if value.isdigit() else None


def attach_identity(c, owner, provider, external_id, password_hash=None, version=None):
    """Called under the verifier-exchange transaction after proof of both identities."""
    if not c.execute('SELECT 1 FROM users WHERE user_id=? AND is_active=1', (owner,)).fetchone():
        raise ValueError('invalid_auth_link')
    existing = c.execute('SELECT user_id FROM auth_identities WHERE provider=? AND external_id=?', (provider, external_id)).fetchone()
    if existing and str(existing[0]) != owner:
        raise ValueError('identity_conflict')
    other = c.execute('SELECT external_id FROM auth_identities WHERE provider=? AND user_id=?', (provider, owner)).fetchone()
    if other and str(other[0]) != external_id:
        raise ValueError('identity_conflict')
    if provider == 'telegram':
        # Legacy Telegram users may predate auth_identities. Never merge them silently.
        if external_id != owner and c.execute('SELECT 1 FROM users WHERE user_id=?', (external_id,)).fetchone():
            raise ValueError('identity_conflict')
    else:
        credentials = c.execute('SELECT user_id FROM email_auth_credentials WHERE email=? OR user_id=?', (external_id, owner)).fetchone()
        google_owner = c.execute("SELECT user_id FROM auth_identities WHERE provider='google' AND lower(email)=?", (external_id,)).fetchall()
        if credentials or any(str(row[0]) != owner for row in google_owner):
            raise ValueError('identity_conflict')
        c.execute('INSERT INTO email_auth_credentials (user_id,email,password_hash,version) VALUES (?,?,?,?)',
                  (owner, external_id, password_hash, version))
    c.execute('INSERT OR IGNORE INTO auth_identities (provider,external_id,user_id,email) VALUES (?,?,?,?)',
              (provider, external_id, owner, external_id if provider == 'email' else None))
