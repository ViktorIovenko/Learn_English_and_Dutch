from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import Config

AUTH_LINK_MAX_AGE_SECONDS = 30 * 24 * 60 * 60
AUTH_LINK_SALT = "learn-words-auth-link-v1"


def _serializer() -> URLSafeTimedSerializer:
    secret = f"{Config.SECRET_KEY}:{Config.BOT_TOKEN}"
    return URLSafeTimedSerializer(secret_key=secret, salt=AUTH_LINK_SALT)


def create_auth_token(user_id: str | int) -> str:
    return _serializer().dumps({"user_id": str(user_id)})


def verify_auth_token(token: str, max_age: int = AUTH_LINK_MAX_AGE_SECONDS) -> str:
    if not token:
        return ""
    try:
        data = _serializer().loads(str(token), max_age=max_age)
    except (BadSignature, SignatureExpired):
        return ""
    user_id = str((data or {}).get("user_id") or "").strip()
    return user_id
