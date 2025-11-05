# app/telegram_auth.py
# Проверка подлинности Telegram WebApp initData по инструкции Telegram.
# https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def _hmac_sha256(key: bytes, msg: bytes) -> bytes:
    return hmac.new(key, msg, hashlib.sha256).digest()

def verify_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400):
    """
    Возвращает dict с полями Telegram (включая 'user') при успехе,
    либо None при неуспехе.
    """
    if not init_data or not bot_token:
        return None

    # init_data — это querystring: "query_id=...&user=...&auth_date=...&hash=..."
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    # data_check_string: отсортированные по алфавиту key=value через \n
    data_check_pairs = [f"{k}={pairs[k]}" for k in sorted(pairs.keys())]
    data_check_string = "\n".join(data_check_pairs).encode("utf-8")

    secret_key = _sha256(bot_token.encode("utf-8"))
    computed_hash = _hmac_sha256(secret_key, data_check_string).hex()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    # Проверка давности
    try:
        auth_date = int(pairs.get("auth_date", "0"))
    except ValueError:
        return None
    if auth_date <= 0 or (time.time() - auth_date) > max_age_seconds:
        return None

    # Преобразуем user (он внутри как JSON)
    try:
        user_json = pairs.get("user", "{}")
        user = json.loads(user_json)
    except Exception:
        return None

    # Вернём всю «полезную» структуру: user, auth_date, query_id и т.д.
    pairs["user"] = user
    pairs["hash"] = received_hash
    return pairs
