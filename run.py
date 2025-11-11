# run.py
# [ИЗМЕНЕНО v6.11] Переход на ежедневное напоминание в 12:00 (Europe/Amsterdam) вместо интервала.
# [ИЗМЕНЕНО v6.10] Фолбэк: создаём JobQueue вручную, если отсутствует (экстры не установлены).
# [ИЗМЕНЕНО v6.8]  Бот в главном потоке (run_polling), Flask — в отдельном.

import asyncio
import logging
import os
import sqlite3
import threading
from pathlib import Path

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from app.routes import init_app as init_web

from telegram import Update
from telegram.ext import ApplicationBuilder, Defaults, JobQueue

from bot.auth import register_auth_handlers
from bot.upload import register_upload_handlers

# ▼▼▼ напоминания
from bot.reminder import (
    register_admin_handlers,
    register_reminders_daily_at,   # ← ИЗМЕНЕНО: используем ежедневное расписание
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("runner")


def _conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with _conn(db_path) as c:
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

        cols = [r["name"] for r in c.execute("PRAGMA table_info(words)")]
        if "difficult" not in cols:
            c.execute("ALTER TABLE words ADD COLUMN difficult INTEGER NOT NULL DEFAULT 0;")

        c.execute("""
            CREATE TABLE IF NOT EXISTS reminder_state (
                user_id        TEXT PRIMARY KEY,
                last_msg_id    INTEGER,
                last_sent_date TEXT
            );
        """)
        c.commit()


def _is_https_base(url: str) -> bool:
    return str(url or "").strip().lower().startswith("https://")


def create_app() -> Flask:
    app = Flask(__name__, static_folder="app/static", template_folder="app/templates")
    app.config.from_object(Config)

    # безопасные cookie только при https
    secure_cookies = _is_https_base(os.getenv("PUBLIC_BASE_URL", ""))
    app.config.update(
        SESSION_COOKIE_SAMESITE="None" if secure_cookies else "Lax",
        SESSION_COOKIE_SECURE=secure_cookies,
    )

    # корректная работа за reverse-proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    @app.after_request
    def skip_ngrok_warning(response):
        response.headers["ngrok-skip-browser-warning"] = "true"
        return response

    init_db(app.config["DB_PATH"])
    init_app = init_web
    init_app(app)
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

    # === ФОЛБЭК ДЛЯ JobQueue ===
    if application.job_queue is None:
        log.warning(
            "JobQueue не инициализирован. Включаю фолбэк через telegram.ext.JobQueue. "
            "Рекомендуется установить: pip install \"python-telegram-bot[job-queue]\""
        )
        jq = JobQueue()
        jq.set_application(application)
        jq.start()
        application.job_queue = jq
        log.info("JobQueue: фолбэк запущен.")

    # порядок важен
    register_upload_handlers(application)
    register_auth_handlers(application)

    # напоминания: АДМИН-команда + ЕЖЕДНЕВНО в 12:00 Europe/Amsterdam
    register_admin_handlers(application)
    register_reminders_daily_at(application)  # ← ИЗМЕНЕНО: ежедневное расписание (12:00 по TZ из reminder.py)

    log.info("Handlers registered: upload -> auth -> reminder_admin; jobs: reminder daily@12:00 Europe/Amsterdam")
    application.add_error_handler(on_error)
    return application


# === запуск Flask в отдельном потоке ===
def _flask_thread():
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "7001"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    log.info("🌐 Flask запущен на http://%s:%s (debug=%s)", host, port, debug)
    app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == "__main__":
    t = threading.Thread(target=_flask_thread, name="flask", daemon=True)
    t.start()

    bot_app = build_bot_application()
    if bot_app is None:
        log.info("Бот не запущен из-за отсутствия токена.")
    else:
        log.info("✅ Бот запускается (polling).")
        bot_app.run_polling(allowed_updates=Update.ALL_TYPES)
