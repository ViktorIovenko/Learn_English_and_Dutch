# config.py
# [ИЗМЕНЕНО v3.3] добавил BOT_PASSWORD и REG_PASSWORD (на случай старого имени)

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET", "dev-key")
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5000")
    DB_PATH = os.path.join(os.path.dirname(__file__), "words.db")

    # [ДОБАВЛЕНО v3.3] пароль регистрации: поддерживаем и BOT_PASSWORD, и REG_PASSWORD
    BOT_PASSWORD = os.getenv("BOT_PASSWORD") or os.getenv("REG_PASSWORD") 
