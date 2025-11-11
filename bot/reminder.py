# bot/reminder.py
# [ДОБАВЛЕНО v1.0] Ежедневные напоминания «повторить слова» с заменой предыдущего сообщения.
# [ИЗМЕНЕНО v1.1] Вынесено время в константы REMINDER_HOUR/REMINDER_MINUTE + гибкая регистрация по строке "HH:MM".
# [ДОБАВЛЕНО v1.2] Команда /reminder_now (только админам), триггер единоразовой рассылки, подробные логи.
# [ДОБАВЛЕНО v1.3] Интервальный режим (оставлен для будущего, по умолчанию не используется).
# [ИЗМЕНЕНО v1.4] ★ Переход на ежедневное расписание в 12:00; в текст добавлен /start;
#                 вместе с сообщением отправляется inline-кнопка «Учить слова» (web_app/url).

from __future__ import annotations
import sqlite3
import logging
import os
from datetime import date, time, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Sequence, Tuple
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes, Application, CommandHandler
from config import Config

# ---------- КОНСТАНТЫ (МЕНЯЕМ ЗДЕСЬ) ----------
# Ежедневный режим (по Europe/Amsterdam):
REMINDER_HOUR   = 12
REMINDER_MINUTE = 0
TZ = ZoneInfo("Europe/Amsterdam")

# Текст напоминания (добавлен /start)
REMINDER_TEXT = (
    "🧠 Ежедневное напоминание: пора повторить слова!\n\n"
    "Нажми «Учить слова» ниже или набери /start — мини-приложение откроется с твоими уроками."
)

# (оставляем интервал на будущее; по умолчанию не используется)
SEND_ON_START           = False
FIRST_SEND_DELAY_SEC    = 1
REMINDER_INTERVAL_HOURS = 24
# -----------------------------------------------

log = logging.getLogger(__name__)

# ---------------- БАЗА ----------------
def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(Config.DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def _ensure_schema() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS reminder_state (
                user_id        TEXT PRIMARY KEY,
                last_msg_id    INTEGER,
                last_sent_date TEXT
            );
        """)
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
        c.commit()

def _get_active_user_ids() -> list[str]:
    """Берём всех активных пользователей из БД (users.is_active=1)."""
    _ensure_schema()
    with _conn() as c:
        rows = c.execute(
            "SELECT user_id FROM users WHERE COALESCE(is_active,1)=1"
        ).fetchall()
    ids: list[str] = []
    for r in rows:
        uid = (r["user_id"] or "").strip()
        if uid:
            ids.append(uid)
    return ids

def _get_last_state(user_id: str) -> Tuple[Optional[int], Optional[str]]:
    _ensure_schema()
    with _conn() as c:
        row = c.execute(
            "SELECT last_msg_id, last_sent_date FROM reminder_state WHERE user_id = ?",
            (str(user_id),)
        ).fetchone()
        if not row:
            return None, None
        try:
            return int(row["last_msg_id"]) if row["last_msg_id"] is not None else None, (row["last_sent_date"] or None)
        except Exception:
            return None, (row["last_sent_date"] or None)

def _set_last_state(user_id: str, msg_id: int, ymd: str) -> None:
    _ensure_schema()
    with _conn() as c:
        c.execute("""
            INSERT INTO reminder_state (user_id, last_msg_id, last_sent_date)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              last_msg_id=excluded.last_msg_id,
              last_sent_date=excluded.last_sent_date
        """, (str(user_id), int(msg_id), ymd))
        c.commit()

# ---------------- URL/КНОПКА «Учить слова» ----------------
# [ДОБАВЛЕНО v1.4] локальный билд ссылки так же, как в auth.py, но без импорта, чтобы избежать циклов
def _is_https(url: str) -> bool:
    return str(url or "").strip().lower().startswith("https://")

def _is_local_address(url: str) -> bool:
    from urllib.parse import urlparse
    try:
        p = urlparse(url); host = (p.hostname or "").lower()
        if host in ("localhost",): return True
        if host.startswith("127.") or host.startswith("10.") or host.startswith("192.168."): return True
        if host.startswith("172."):
            parts = host.split(".")
            if len(parts) >= 2:
                try:
                    second = int(parts[1]); return 16 <= second <= 31
                except Exception:
                    pass
        return False
    except Exception:
        return True

def _build_app_url(user_id: int) -> tuple[str, bool, bool]:
    base = f"{Config.PUBLIC_BASE_URL}".rstrip("/")
    uid_suffix = f"/?uid={user_id}"
    if _is_https(base):
        return (base + uid_suffix, True, True)
    url = base + uid_suffix
    return (url, False, not _is_local_address(url))

def _learn_inline_markup(user_id: int) -> InlineKeyboardMarkup:
    url, use_webapp, use_inline = _build_app_url(user_id)
    if use_webapp:
        btn = InlineKeyboardButton(text="Учить слова", web_app=WebAppInfo(url=url))
    elif use_inline:
        btn = InlineKeyboardButton(text="Учить слова", url=url)
    else:
        # последний фолбэк — обычная ссылка (телеграм всё равно откроет браузер)
        btn = InlineKeyboardButton(text="Учить слова", url=url)
    return InlineKeyboardMarkup([[btn]])

# ---------------- ОТПРАВКА ----------------
async def send_to_user_id(context: ContextTypes.DEFAULT_TYPE, user_id: str | int) -> bool:
    """
    Отсылает REMINDER_TEXT пользователю (chat_id == user_id) + inline-кнопку «Учить слова».
    Возвращает True, если успешно, иначе False.
    """
    chat_id = int(user_id)
    last_msg_id, _ = _get_last_state(str(user_id))
    today = date.today().isoformat()
    try:
        markup = _learn_inline_markup(chat_id)  # ← [ИЗМЕНЕНО v1.4] добавили кнопку
        m = await context.bot.send_message(chat_id=chat_id, text=REMINDER_TEXT, reply_markup=markup)
        _set_last_state(str(user_id), m.message_id, today)
        if last_msg_id:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=last_msg_id)
            except Exception as e:
                log.debug("delete previous reminder failed for %s: %r", chat_id, e)
        log.info("Reminder OK -> user_id=%s msg_id=%s", user_id, m.message_id)
        return True
    except Exception as e:
        log.warning("Reminder FAIL -> user_id=%s error=%r (возможно, не писал боту/заблокировал)", user_id, e)
        return False

async def send_reminders_all(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обходим всех активных пользователей и шлём напоминание.
    """
    user_ids = _get_active_user_ids()
    log.info("Reminders: going to send to %d users", len(user_ids))
    ok = 0
    for uid in user_ids:
        if await send_to_user_id(context, uid):
            ok += 1
    log.info("Reminders done: success=%d / total=%d", ok, len(user_ids))

# ---------------- РЕГИСТРАЦИЯ ДЖОБОВ ----------------
# ЕЖЕДНЕВНО В 12:00 (режим по умолчанию)
def register_reminders_daily_at(application: Application,
                                hour: int = REMINDER_HOUR,
                                minute: int = REMINDER_MINUTE) -> None:
    """
    Раз в сутки в HH:MM по Europe/Amsterdam.
    """
    _ensure_schema()
    hour = max(0, min(23, int(hour)))
    minute = max(0, min(59, int(minute)))
    when_local = time(hour, minute, tzinfo=TZ)
    application.job_queue.run_daily(
    send_reminders_all,
    time=when_local,  # ← ИЗМЕНЕНО: PTB v20+ требует параметр "time"
    name="reminder_daily_at"
    )
    log.info("Daily reminder scheduled at %02d:%02d Europe/Amsterdam", hour, minute)

# Интервальный режим — оставляем для будущего использования
def register_reminders_interval(application: Application,
                                first_delay_sec: int = FIRST_SEND_DELAY_SEC,
                                every_hours: int = REMINDER_INTERVAL_HOURS,
                                send_on_start: bool = SEND_ON_START) -> None:
    _ensure_schema()
    if send_on_start:
        application.job_queue.run_once(
            callback=lambda ctx: send_reminders_all(ctx),
            when=first_delay_sec,
            name="reminder_now_on_start"
        )
        log.info("One-shot reminder scheduled in %d seconds", first_delay_sec)
    interval = timedelta(hours=max(1, int(every_hours)))
    application.job_queue.run_repeating(
        callback=lambda ctx: send_reminders_all(ctx),
        interval=interval,
        first=interval,
        name="reminder_interval"
    )
    log.info("Repeating reminder scheduled: every %s", interval)

# ---------------- ДОП. ХЭНДЛЕРЫ / УТИЛИТЫ ----------------
async def _send_all_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_reminders_all(context)

def trigger_send_all_now(application: Application, delay_seconds: int = 1) -> None:
    """
    Вручную запланировать единоразовый запуск рассылки через delay_seconds.
    """
    application.job_queue.run_once(_send_all_job, when=delay_seconds, name="reminder_manual_once")
    log.info("Manual one-shot reminder scheduled in %d seconds", delay_seconds)

def _admin_ids() -> set[int]:
    raw: Optional[Sequence] = getattr(Config, "ADMIN_IDS", None)
    ids: set[int] = set()
    if raw:
        for v in raw:
            try:
                ids.add(int(v))
            except Exception:
                pass
    return ids

def _is_admin(tg_user_id: Optional[int]) -> bool:
    if tg_user_id is None:
        return False
    admins = _admin_ids()
    return (tg_user_id in admins) if admins else False

async def _cmd_reminder_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not _is_admin(user.id if user else None):
        await update.effective_message.reply_text("⛔ Доступ запрещён.")
        return
    await update.effective_message.reply_text("⏳ Отправляю напоминания всем активным пользователям…")
    await send_reminders_all(context)
    await update.effective_message.reply_text("✅ Готово.")

def register_admin_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("reminder_now", _cmd_reminder_now))
