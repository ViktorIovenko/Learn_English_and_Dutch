# run.py
# [ИЗМЕНЕНО v6.4] Удалены "custom-слова": больше не создаём user_custom_words, при старте удаляем если есть.
import asyncio
import logging
import os
import sqlite3
import threading
from pathlib import Path

from flask import Flask
from config import Config
from app.routes import init_app as init_web

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, Defaults

from bot.auth import register_auth_handlers
from bot.upload import register_upload_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("runner")

def _conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with _conn(db_path) as c:
        # базовые таблицы
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    TEXT PRIMARY KEY,
                username   TEXT,
                first_name TEXT,
                last_name  TEXT,
                is_active  INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson     TEXT,
                number     TEXT,
                nl         TEXT,
                en         TEXT,
                ru         TEXT,
                ex_nl      TEXT,
                ex_en      TEXT,
                ex_ru      TEXT,
                audio_nl   TEXT,
                audio_en   TEXT,
                audio_ru   TEXT
            );
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_words_lesson ON words(lesson);")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS u_words_number ON words(number);")

        # [НЕ МЕНЯЛОСЬ] авто-миграция: колонка difficult в words
        cols = [r["name"] for r in c.execute("PRAGMA table_info(words)")]
        if "difficult" not in cols:
            c.execute("ALTER TABLE words ADD COLUMN difficult INTEGER NOT NULL DEFAULT 0;")

        # [НЕ МЕНЯЛОСЬ] таблица персональных флагов
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_word_flags (
                user_id   TEXT NOT NULL,
                word_id   INTEGER NOT NULL,
                difficult INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (user_id, word_id)
            );
        """)

        # [ИЗМЕНЕНО v6.4] Больше НЕ создаём user_custom_words
        # [ДОБАВЛЕНО v6.4] На всякий случай удалим существующую таблицу
        try:
            c.execute("DROP TABLE IF EXISTS user_custom_words;")
        except Exception:
            pass

        c.commit()

def _is_https_base(url: str) -> bool:
    return str(url or "").strip().lower().startswith("https://")

def create_app() -> Flask:
    app = Flask(__name__, static_folder="app/static", template_folder="app/templates")
    app.config.from_object(Config)
    # cookie-политика
    secure_cookies = _is_https_base(os.getenv("PUBLIC_BASE_URL", ""))
    app.config.update(
        SESSION_COOKIE_SAMESITE="None" if secure_cookies else "Lax",
        SESSION_COOKIE_SECURE=secure_cookies,
    )

    @app.after_request
    def skip_ngrok_warning(response):
        response.headers['ngrok-skip-browser-warning'] = 'true'
        return response

    init_db(app.config["DB_PATH"])
    init_web(app)
    return app

app = create_app()

async def on_error(update: object, context) -> None:
    try:
        u = update if isinstance(update, Update) else None
        chat_id = u.effective_chat.id if (u and u.effective_chat) else None
        log.exception("PTB error. chat=%s update=%s", chat_id, u)
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text="⚠ Произошла ошибка, попробуйте ещё раз.")
    except Exception:
        log.exception("Error inside error handler")

def build_bot_application():
    if not Config.BOT_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN пуст. Укажи токен в .env")
        return None
    defaults = Defaults(parse_mode="HTML")
    application = ApplicationBuilder().token(Config.BOT_TOKEN).defaults(defaults).build()
    register_auth_handlers(application)
    register_upload_handlers(application)
    application.add_error_handler(on_error)
    return application

def _bot_thread():
    app_bot = build_bot_application()
    if app_bot is None:
        log.info("Бот не запущен из-за отсутствия токена.")
        return
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        log.info("✅ Бот запускается (polling).")
        loop.run_until_complete(app_bot.run_polling(allowed_updates=Update.ALL_TYPES))
    except Exception as e:
        log.exception("Ошибка при запуске бота: %s", e)
    finally:
        try:
            pending = asyncio.all_tasks(loop=loop)
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            pass
        try:
            loop.close()
        except Exception:
            pass

if __name__ == "__main__":
    t = threading.Thread(target=_bot_thread, name="tg-bot", daemon=True)
    t.start()
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    log.info("🌐 Flask запущен на http://%s:%s (debug=%s)", host, port, debug)
    app.run(host=host, port=port, debug=debug, use_reloader=False)
