from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import Config


PAIRING_TOKEN_MAX_AGE_SECONDS = 10 * 60
PAIRING_TOKEN_SALT = "learn-words-family-pairing-v1"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=Config.SECRET_KEY,
        salt=PAIRING_TOKEN_SALT,
    )


def create_pairing_token(child_user_id: str | int) -> str:
    return _serializer().dumps({"child_user_id": str(child_user_id)})


def verify_pairing_token(
    token: str,
    max_age: int = PAIRING_TOKEN_MAX_AGE_SECONDS,
) -> str:
    if not token:
        return ""
    try:
        data = _serializer().loads(str(token), max_age=max_age)
    except (BadSignature, SignatureExpired):
        return ""
    return str((data or {}).get("child_user_id") or "").strip()
