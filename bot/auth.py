# bot/auth.py
# Регистрация по паролю + постоянная клавиатура с кнопками
# [ИЗМЕНЕНО v5.8] Единственный «якорь-меню»: перед показом нового удаляем старый; все служебные сообщения автоудаляются.
# [ИЗМЕНЕНО v5.7] Мгновенные ответы, удаление в фоне.
# [ИЗМЕНЕНО v4.9] Автоудаление сообщений, связанных с паролем.
# [ИСПРАВЛЕНО v5.9] Миграция схемы users: убран ранний return по наличию user_id; добавлена проверка полного набора столбцов и безопасная миграция.

import os
import sqlite3
import asyncio
import html
from urllib.parse import urlencode, urlparse
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update,
    WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from config import Config
from app.auth_links import create_auth_token

EPHEMERAL_SECONDS = 20.0  # время жизни всех служебных сообщений

# ---------- sqlite ----------
def _conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row; return conn

def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]

# [ИСПРАВЛЕНО v5.9] Полноценная проверка схемы и миграция
def _ensure_users_schema(db_path: str) -> None:
    expected = ["user_id", "username", "first_name", "last_name", "is_active", "created_at"]
    with _conn(db_path) as c:
        # Создадим таблицу, если её не было
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
        cols = _columns(c, "users")

        # Если схема уже совпадает (множества равны) — ничего не делаем
        if set(cols) == set(expected):
            return

        # Иначе мигрируем в новую таблицу с полной схемой
        c.execute("""
            CREATE TABLE IF NOT EXISTS users_new (
                user_id    TEXT PRIMARY KEY,
                username   TEXT,
                first_name TEXT,
                last_name  TEXT,
                is_active  INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

        old = set(cols)

        # Подготовим выражения-источники для копирования данных
        user_id_expr    = "CAST(user_id AS TEXT)" if "user_id" in old else (
                          "CAST(id AS TEXT)" if "id" in old else (
                          "CAST(user AS TEXT)" if "user" in old else "NULL"))
        username_expr   = "username"   if "username"   in old else "NULL"
        first_name_expr = "first_name" if "first_name" in old else "NULL"
        last_name_expr  = "last_name"  if "last_name"  in old else "NULL"
        is_active_expr  = "COALESCE(is_active,1)" if "is_active" in old else "1"
        created_at_expr = "COALESCE(created_at,CURRENT_TIMESTAMP)" if "created_at" in old else "CURRENT_TIMESTAMP"

        # Если старой таблицы вообще нет совместимых источников id — просто пересоздаём
        if user_id_expr == "NULL":
            c.execute("DROP TABLE IF EXISTS users")
            c.execute("ALTER TABLE users_new RENAME TO users")
            c.commit()
            return

        # Переливаем данные из старой таблицы в новую (в рамках того, что есть)
        c.execute(f"""
            INSERT OR IGNORE INTO users_new (user_id, username, first_name, last_name, is_active, created_at)
            SELECT {user_id_expr}, {username_expr}, {first_name_expr}, {last_name_expr}, {is_active_expr}, {created_at_expr}
            FROM users
        """)
        c.execute("DROP TABLE users")
        c.execute("ALTER TABLE users_new RENAME TO users")
        c.commit()

def _is_user_registered(db_path: str, user_id: int) -> bool:
    _ensure_users_schema(db_path)
    with _conn(db_path) as c:
        return bool(c.execute("SELECT 1 FROM users WHERE user_id=?", (str(user_id),)).fetchone())


def _has_telegram_identity(user: "telegram.User") -> bool:
    return bool(
        (user.username or "").strip()
        or (user.first_name or "").strip()
        or (user.last_name or "").strip()
    )


# [БЕЗ ИЗМЕНЕНИЙ] — сама запись уже включает username/first_name/last_name
def _register_user(db_path: str, user: "telegram.User") -> bool:
    _ensure_users_schema(db_path)
    if not _has_telegram_identity(user):
        return False
    with _conn(db_path) as c:
        existed = bool(c.execute("SELECT 1 FROM users WHERE user_id=?", (str(user.id),)).fetchone())
        c.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, is_active)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                is_active=1
        """, (str(user.id), user.username or "", user.first_name or "", user.last_name or ""))
        c.commit()
    return not existed


def _admin_ids() -> tuple[int, ...]:
    raw = getattr(Config, "ADMIN_IDS", ()) or ()
    result: list[int] = []
    for item in raw:
        try:
            result.append(int(item))
        except Exception:
            pass
    return tuple(dict.fromkeys(result))


def _format_new_user_notice(user: "telegram.User") -> str:
    username = f"@{user.username}" if user.username else "без username"
    full_name = " ".join(part for part in [user.first_name or "", user.last_name or ""] if part).strip()
    if not full_name:
        full_name = "без имени"
    return (
        "👤 Новый пользователь\n"
        f"ID: <code>{html.escape(str(user.id))}</code>\n"
        f"Имя: {html.escape(full_name)}\n"
        f"Username: {html.escape(username)}"
    )


async def _notify_admins_new_user(context: ContextTypes.DEFAULT_TYPE, user: "telegram.User") -> None:
    text = _format_new_user_notice(user)
    for admin_id in _admin_ids():
        try:
            await context.bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
        except Exception:
            pass

# ---------- helpers ----------
def _get_expected_password() -> str:
    return (getattr(Config, "BOT_PASSWORD", None)
            or getattr(Config, "REG_PASSWORD", None)
            or os.getenv("BOT_PASSWORD")
            or os.getenv("REG_PASSWORD")
            or "Viktor-07").strip()

def _is_https(url: str) -> bool:
    return str(url).strip().lower().startswith("https://")

def _is_local_address(url: str) -> bool:
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
    uid_suffix = "/?" + urlencode({"auth": create_auth_token(user_id)})
    if _is_https(base): return (base + uid_suffix, True, True)
    url = base + uid_suffix; return (url, False, not _is_local_address(url))

def _build_android_app_url(user_id: int) -> str:
    base = f"{Config.PUBLIC_BASE_URL}".rstrip("/")
    return base + "/android-auth?" + urlencode({"token": create_auth_token(user_id)})

def _build_android_download_url() -> str:
    base = f"{Config.PUBLIC_BASE_URL}".rstrip("/")
    return base + "/static/downloads/learnwords.apk"

def get_persistent_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    url, use_webapp, _ = _build_app_url(user_id)
    if use_webapp:
        btn_learn = KeyboardButton(text="Учить слова", web_app=WebAppInfo(url=url))
    else:
        btn_learn = KeyboardButton(text="Учить слова")
    btn_add = KeyboardButton(text="Загрузить слова")
    return ReplyKeyboardMarkup(
        keyboard=[[btn_learn], [btn_add]],
        resize_keyboard=True,
        is_persistent=True,
        one_time_keyboard=False
    )

# ---------- удаление/эфемерность ----------
async def _safe_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int) -> None:
    try: await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception: pass

async def _delete_user_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update and update.message:
            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    except Exception: pass

async def _delete_later(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: float = EPHEMERAL_SECONDS):
    await asyncio.sleep(delay); await _safe_delete(context, chat_id, message_id)

async def _ephemeral_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, delay: float = EPHEMERAL_SECONDS):
    m = await update.effective_chat.send_message(text)
    asyncio.create_task(_delete_later(context, m.chat_id, m.message_id, delay))

# ---------- НОВОЕ: единый показ «Меню» ----------
async def show_menu_with_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """
    Удаляет предыдущее 'меню-сообщение', шлёт новое с клавиатурой.
    Сообщение НЕ удаляется — иначе Telegram убирает клавиатуру вместе с ним.
    """
    anchor_key = "kb_anchor_msg_id"
    old_id = context.user_data.get(anchor_key)
    if old_id:
        asyncio.create_task(_safe_delete(context, update.effective_chat.id, old_id))
    m = await update.effective_chat.send_message("⬇️ Меню", reply_markup=get_persistent_keyboard(user_id))
    context.user_data[anchor_key] = m.message_id

# ---------- handlers ----------
OK_PWD  = "✅ Готово! Вам доступно 14 дней бесплатного пользования."

async def _ensure_open_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user if update else None
    if not user:
        return False
    if not _has_telegram_identity(user):
        await _ephemeral_send(
            update,
            context,
            "Для регистрации укажите имя или username в Telegram и нажмите /start снова.",
        )
        return False
    is_new = _register_user(Config.DB_PATH, user)
    if is_new:
        await _notify_admins_new_user(context, user)
    return is_new


async def _send_fresh_app_link(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, text: str = "") -> None:
    old_id = context.user_data.get("open_link_msg_id")
    if old_id:
        asyncio.create_task(_safe_delete(context, update.effective_chat.id, old_id))

    url, use_webapp, use_inline = _build_app_url(user_id)
    buttons = []
    if use_webapp:
        buttons.append([InlineKeyboardButton(text="Открыть мини-приложение", web_app=WebAppInfo(url=url))])
        buttons.append([InlineKeyboardButton(text="Открыть в браузере", url=url)])
    elif use_inline:
        buttons.append([InlineKeyboardButton(text="Открыть приложение", url=url)])
    buttons.append([InlineKeyboardButton(text="Скачать Android-приложение", url=_build_android_download_url())])
    buttons.append([InlineKeyboardButton(text="Войти в Android-приложение", url=_build_android_app_url(user_id))])

    if buttons:
        m = await update.effective_chat.send_message(
            text or "Свежая ссылка для входа:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        context.user_data["open_link_msg_id"] = m.message_id
    else:
        await update.effective_chat.send_message(text or f"Свежая ссылка для входа:\n{url}")


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await _delete_user_trigger(update, context)
    context.user_data.pop("await_pwd", None)
    is_new = await _ensure_open_registration(update, context)
    if not _is_user_registered(Config.DB_PATH, user.id):
        return
    await show_menu_with_keyboard(update, context, user.id)
    await _send_fresh_app_link(update, context, user.id)
    if is_new:
        await _ephemeral_send(update, context, OK_PWD)
    else:
        await _ephemeral_send(update, context, "С возвращением!")

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if context.user_data.get("await_pwd"):
        context.user_data.pop("await_pwd", None)
        for mid in context.user_data.get("pwd_bot_msg_ids", []):
            asyncio.create_task(_delete_later(context, update.effective_chat.id, mid, 0))
        context.user_data["pwd_bot_msg_ids"] = []
        is_new = await _ensure_open_registration(update, context)
        await show_menu_with_keyboard(update, context, user_id)
        await _ephemeral_send(update, context, OK_PWD if is_new else "Пароль больше не нужен. Можно пользоваться приложением.")
        return

    # Восстанавливаем клавиатуру для зарегистрированных пользователей
    # (один раз за сессию — после рестарта бота user_data сбрасывается)
    if not context.user_data.get("kb_shown") and _is_user_registered(Config.DB_PATH, user_id):
        context.user_data["kb_shown"] = True
        await show_menu_with_keyboard(update, context, user_id)

async def open_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_open(update, context)

async def send_open(update: Update, context: ContextTypes.DEFAULT_TYPE, hello: str = "") -> None:
    user_id = update.effective_user.id if (update and update.effective_user) else 0
    if update and update.effective_user:
        await _ensure_open_registration(update, context)
        if not _is_user_registered(Config.DB_PATH, user_id):
            return
    await _delete_user_trigger(update, context)
    await _send_fresh_app_link(update, context, user_id, hello or "Свежая ссылка для входа:")
    await show_menu_with_keyboard(update, context, user_id)  # ← ИЗМЕНЕНО

def register_auth_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("open", open_cmd))
    application.add_handler(MessageHandler(filters.Regex(r"^(Учить слова)$"), open_cmd))
    # Исключаем кнопки подтверждения (регистронезависимо)
    exclude_import_btns = ~filters.Regex(r"(?i)^(импортировать как есть|отменить импорт)$")
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND) & exclude_import_btns, on_text),
        group=100
    )
