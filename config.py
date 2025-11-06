# config.py
# [ИЗМЕНЕНО v3.5] AUDIO_MAXIMIZE: компрессор + пик-нормализация до -0.1 dBFS

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET", "dev-key")

    # Telegram / Web
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5000")

    # DB
    DB_PATH = os.path.join(os.path.dirname(__file__), "words.db")

    # Login (если нужно)
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
