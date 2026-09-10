# config.py
# [ИЗМЕНЕНО v3.6] ParallelLingvo app domain + Google/Telegram OIDC settings
# [ИЗМЕНЕНО v3.5] AUDIO_MAXIMIZE: компрессор + пик-нормализация до -0.1 dBFS

import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET", "dev-key")

    # ParallelLingvo domains
    SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://parallellingvo.app").rstrip("/")
    APP_BASE_URL = os.getenv("APP_BASE_URL", "https://app.parallellingvo.app").rstrip("/")

    # Telegram / WebApp. Keep PUBLIC_BASE_URL for backwards compatibility with the bot code.
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", APP_BASE_URL).rstrip("/")

    # Web authentication
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    TELEGRAM_OIDC_CLIENT_ID = os.getenv("TELEGRAM_OIDC_CLIENT_ID", "")
    TELEGRAM_OIDC_CLIENT_SECRET = os.getenv("TELEGRAM_OIDC_CLIENT_SECRET", "")

    # Legacy ?uid=/X-User-Id authentication is unsafe for a public app and is disabled by default.
    # Set ALLOW_LEGACY_UID_AUTH=1 only temporarily during a controlled migration/debug session.
    ALLOW_LEGACY_UID_AUTH = _env_bool("ALLOW_LEGACY_UID_AUTH", False)

    # DB
    DB_PATH = os.path.join(os.path.dirname(__file__), "words.db")

    # Login (legacy Telegram-bot registration flow)
    BOT_PASSWORD = os.getenv("BOT_PASSWORD") or os.getenv("REG_PASSWORD")

    # -------------------- AUDIO (громкость) --------------------
    # [ДОБАВЛЕНО v3.5] Максимизация громкости:
    # 1) компрессия (сжимает пики, поднимает среднюю громкость)
    # 2) пик-нормализация до целевого уровня (по умолчанию -0.1 dBFS)
    AUDIO_MAXIMIZE = str(os.getenv("AUDIO_MAXIMIZE", "1")).lower() in ("1", "true", "yes", "on")

    # Целевой пик после нормализации (чем ближе к 0, тем громче; оставляем небольшой запас)
    AUDIO_PEAK_DBFS = float(os.getenv("AUDIO_PEAK_DBFS", "-0.1"))

    # Параметры компрессии (агрессивные, но без артефактов для речи)
    AUDIO_COMP_THRESHOLD_DBFS = float(os.getenv("AUDIO_COMP_THRESHOLD_DBFS", "-18"))  # порог
    AUDIO_COMP_RATIO = float(os.getenv("AUDIO_COMP_RATIO", "6.0"))                    # отношение
    AUDIO_COMP_ATTACK_MS = int(os.getenv("AUDIO_COMP_ATTACK_MS", "3"))
    AUDIO_COMP_RELEASE_MS = int(os.getenv("AUDIO_COMP_RELEASE_MS", "80"))

    # Экспорт
    AUDIO_MP3_BITRATE = os.getenv("AUDIO_MP3_BITRATE", "256k")  # чем выше, тем лучше качество
