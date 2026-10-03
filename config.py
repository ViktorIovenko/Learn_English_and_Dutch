# config.py
# [ИЗМЕНЕНО v3.5] AUDIO_MAXIMIZE: компрессор + пик-нормализация до -0.1 dBFS

import os
from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str | None) -> tuple[int, ...]:
    ids: list[int] = []
    for part in str(raw or "").replace(";", ",").replace(" ", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            continue
    return tuple(dict.fromkeys(ids))


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET", "dev-key")

    # Telegram / Web
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")
    SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://localhost:5000")
    APP_BASE_URL = os.getenv("APP_BASE_URL", os.getenv("PUBLIC_BASE_URL", "http://localhost:5000"))
    PUBLIC_BASE_URL = APP_BASE_URL
    ALLOW_LEGACY_UID_AUTH = str(os.getenv("ALLOW_LEGACY_UID_AUTH", "0")).lower() in {"1", "true", "yes", "on"}

    # DB
    DB_PATH = os.path.join(os.path.dirname(__file__), "words.db")

    # Login (если нужно)
    BOT_PASSWORD = os.getenv("BOT_PASSWORD") or os.getenv("REG_PASSWORD")
    ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS") or os.getenv("ADMIN_TG_IDS"))

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Telegram Login (OAuth 2.0 / OIDC via oauth.telegram.org — BotFather "Login Widget")
    TELEGRAM_OIDC_CLIENT_ID = os.getenv("TELEGRAM_OIDC_CLIENT_ID", "")
    TELEGRAM_OIDC_CLIENT_SECRET = os.getenv("TELEGRAM_OIDC_CLIENT_SECRET", "")

    # Optional provider adapter modules; translation/examples disabled by default.
    CONTENT_PROVIDER_MODULE = os.getenv("CONTENT_PROVIDER_MODULE", "")
    CONTENT_TRANSLATION_PROVIDER_MODULE = os.getenv("CONTENT_TRANSLATION_PROVIDER_MODULE", "")
    CONTENT_EXAMPLE_PROVIDER_MODULE = os.getenv("CONTENT_EXAMPLE_PROVIDER_MODULE", "")
    CONTENT_TOPIC_PROVIDER_MODULE = os.getenv("CONTENT_TOPIC_PROVIDER_MODULE", "")
    CONTENT_TTS_PROVIDER_MODULE = os.getenv("CONTENT_TTS_PROVIDER_MODULE", "")
    # Legacy settings for explicitly configured adapters.
    AI_PLATFORM_BASE_URL = os.getenv("AI_PLATFORM_BASE_URL", "")
    AI_PLATFORM_API_KEY_TRANSLATE_WORD = os.getenv("AI_PLATFORM_API_KEY_TRANSLATE_WORD", "")
    AI_PLATFORM_API_KEY_SUGGEST_TOPIC_WORDS = os.getenv("AI_PLATFORM_API_KEY_SUGGEST_TOPIC_WORDS", "")
    AI_PLATFORM_API_KEY_TRANSLATE_LANGUAGE = os.getenv("AI_PLATFORM_API_KEY_TRANSLATE_LANGUAGE", "")
    AI_PLATFORM_TIMEOUT_SECONDS = float(os.getenv("AI_PLATFORM_TIMEOUT_SECONDS", "60"))
    # Отдельный общий секрет для серверного чтения админской статистики из AI Platform.
    AI_PLATFORM_ADMIN_TOKEN = os.getenv("AI_PLATFORM_ADMIN_TOKEN", "")

    # MCP connector. The gateway receives only this dedicated shared secret;
    # it never receives the application's Google, Telegram or AI credentials.
    MCP_INTERNAL_TOKEN = os.getenv("MCP_INTERNAL_TOKEN", "")
    MCP_PUBLIC_URL = os.getenv("MCP_PUBLIC_URL", "https://learn.iovenko.eu/mcp")
    MCP_ISSUER_URL = os.getenv("MCP_ISSUER_URL", "https://learn.iovenko.eu")
    MCP_ACCESS_TOKEN_TTL_SECONDS = int(os.getenv("MCP_ACCESS_TOKEN_TTL_SECONDS", "2592000"))
    MCP_AUTH_CODE_TTL_SECONDS = int(os.getenv("MCP_AUTH_CODE_TTL_SECONDS", "300"))
    MCP_CONNECTOR_VERSION = os.getenv("MCP_CONNECTOR_VERSION", "1.0.0")
    MCP_BUILD_REVISION = os.getenv("MCP_BUILD_REVISION", "local")
    MCP_BUILD_CREATED = os.getenv("MCP_BUILD_CREATED", "unknown")
    MCP_BUILD_SOURCE = os.getenv("MCP_BUILD_SOURCE", "Learn_English_and_Dutch")

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

    # Месячные счётчики фактических обращений к Google TTS.
    TTS_USAGE_TIMEZONE = os.getenv("TTS_USAGE_TIMEZONE", "Europe/Amsterdam")
