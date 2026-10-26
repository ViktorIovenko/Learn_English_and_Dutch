from __future__ import annotations

import sqlite3
from contextlib import closing

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import Config

AUTH_LINK_MAX_AGE_SECONDS = 30 * 24 * 60 * 60
AUTH_LINK_SALT = "learn-words-auth-link-v1"


def _serializer() -> URLSafeTimedSerializer:
    secret = f"{Config.SECRET_KEY}:{Config.BOT_TOKEN}"
    return URLSafeTimedSerializer(secret_key=secret, salt=AUTH_LINK_SALT)


def email_credential_version(user_id: str) -> str | None:
    with closing(sqlite3.connect(Config.DB_PATH)) as conn:
        try:
            row = conn.execute("SELECT version FROM email_auth_credentials WHERE user_id=?", (str(user_id),)).fetchone()
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc):
                return None
            raise
    return str(row[0]) if row else None


def bind_email_session(user_id: str) -> None:
    from flask import session
    version = email_credential_version(str(user_id))
    session.pop("email_auth_version", None)
    if version is not None:
        session["email_auth_version"] = version


def create_auth_token(user_id: str | int, *, email_version: str | None = None) -> str:
    from app.account_privacy import generation
    data = {"user_id": str(user_id), "generation": generation(str(user_id))}
    version = email_version if email_version is not None else email_credential_version(str(user_id))
    if version is not None:
        data["email_version"] = version
    return _serializer().dumps(data)


def verify_auth_token(token: str, max_age: int = AUTH_LINK_MAX_AGE_SECONDS) -> str:
    if not token:
        return ""
    try:
        data = _serializer().loads(str(token), max_age=max_age)
    except (BadSignature, SignatureExpired):
        return ""
    if not isinstance(data, dict):
        return ""
    user_id = str(data.get("user_id") or "").strip()
    from app.account_privacy import generation
    if user_id and data.get("generation", "0") != generation(user_id):
        return ""
    version = email_credential_version(user_id) if user_id else None
    if version is not None and data.get("email_version") != version:
        return ""
    return user_id
