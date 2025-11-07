# bot/auth.py
# Регистрация по паролю + постоянная клавиатура с кнопками
# [ИЗМЕНЕНО v5.8] Единственный «якорь-меню»: перед показом нового удаляем старый; все служебные сообщения автоудаляются.
# [ИЗМЕНЕНО v5.7] Мгновенные ответы, удаление в фоне.
# [ИЗМЕНЕНО v4.9] Автоудаление сообщений, связанных с паролем.

import os
import sqlite3
import asyncio
from urllib.parse import urlparse
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update,
    WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from config import Config

EPHEMERAL_SECONDS = 20.0  # время жизни всех служебных сообщений

# ---------- sqlite ----------
def _conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row; return conn

def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]

def _ensure_users_schema(db_path: str) -> None:
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
        cols = _columns(c, "users")
        if "user_id" in cols:
            return
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
        if "id" in old:
            user_id_expr = "CAST(id AS TEXT)"
        elif "user" in old:
            user_id_expr = "CAST(user AS TEXT)"
        else:
            c.execute("DROP TABLE IF EXISTS users")
            c.execute("ALTER TABLE users_new RENAME TO users")
            c.commit()
            return
        username_expr   = "username"   if "username"   in old else "NULL"
        first_name_expr = "first_name" if "first_name" in old else "NULL"
        last_name_expr  = "last_name"  if "last_name"  in old else "NULL"
        is_active_expr  = "COALESCE(is_active,1)" if "is_active" in old else "1"
        created_at_expr = "COALESCE(created_at,CURRENT_TIMESTAMP)" if "created_at" in old else "CURRENT_TIMESTAMP"
        c.execute(f"""
            INSERT OR IGNORE INTO users_new (user_id, username, first_name, last_name, is_active, created_at)
            SELECT {user_id_expr},{username_expr},{first_name_expr},{last_name_expr},{is_active_expr},{created_at_expr}
            FROM users
        """)
        c.execute("DROP TABLE users")
        c.execute("ALTER TABLE users_new RENAME TO users")
        c.commit()

def _is_user_registered(db_path: str, user_id: int) -> bool:
    _ensure_users_schema(db_path)
    with _conn(db_path) as c:
        return bool(c.execute("SELECT 1 FROM users WHERE user_id=?", (str(user_id),)).fetchone())

def _register_user(db_path: str, user: "telegram.User") -> None:
    _ensure_users_schema(db_path)
    with _conn(db_path) as c:
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
    uid_suffix = f"/?uid={user_id}"
    if _is_https(base): return (base + uid_suffix, True, True)
    url = base + uid_suffix; return (url, False, not _is_local_address(url))

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
    Удаляет предыдущее 'меню-сообщение', шлёт новое с клавиатурой
    и планирует его удаление через EPHEMERAL_SECONDS.
    """
    anchor_key = "kb_anchor_msg_id"
    old_id = context.user_data.get(anchor_key)
    if old_id:
        asyncio.create_task(_safe_delete(context, update.effective_chat.id, old_id))
    m = await update.effective_chat.send_message("⬇️ Меню", reply_markup=get_persistent_keyboard(user_id))
    context.user_data[anchor_key] = m.message_id
    asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))

# ---------- handlers ----------
ASK_PWD = "Введите пароль для регистрации:"
OK_PWD  = "✅ Готово! Вы зарегистрированы."

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await _delete_user_trigger(update, context)
    await show_menu_with_keyboard(update, context, user.id)   # ← ИЗМЕНЕНО
    if _is_user_registered(Config.DB_PATH, user.id):
        await _ephemeral_send(update, context, "С возвращением!")
        return
    ask = await update.effective_chat.send_message(ASK_PWD)
    context.user_data.setdefault("pwd_bot_msg_ids", []).append(ask.message_id)
    context.user_data["await_pwd"] = True
    asyncio.create_task(_delete_later(context, ask.chat_id, ask.message_id))

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("await_pwd"):
        pwd_message = update.message
        chat_id = pwd_message.chat_id
        user_id = update.effective_user.id
        await _safe_delete(context, chat_id, pwd_message.message_id)
        pwd = (pwd_message.text or "").strip()
        expected = _get_expected_password()
        if pwd == expected:
            _register_user(Config.DB_PATH, update.effective_user)
            context.user_data.pop("await_pwd", None)
            for mid in context.user_data.get("pwd_bot_msg_ids", []):
                asyncio.create_task(_delete_later(context, chat_id, mid, 0))
            context.user_data["pwd_bot_msg_ids"] = []
            await show_menu_with_keyboard(update, context, user_id)  # ← ИЗМЕНЕНО
            await _ephemeral_send(update, context, OK_PWD)
        else:
            await show_menu_with_keyboard(update, context, user_id)  # ← ИЗМЕНЕНО
            err = await update.effective_chat.send_message("Пароль неверный. Попробуйте снова.")
            context.user_data.setdefault("pwd_bot_msg_ids", []).append(err.message_id)
            asyncio.create_task(_delete_later(context, err.chat_id, err.message_id))
        return
    return

async def open_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_open(update, context)

async def send_open(update: Update, context: ContextTypes.DEFAULT_TYPE, hello: str = "") -> None:
    user_id = update.effective_user.id if (update and update.effective_user) else 0
    await _delete_user_trigger(update, context)
    url, use_webapp, use_inline = _build_app_url(user_id)
    if use_webapp:
        kb_inline = InlineKeyboardMarkup([[InlineKeyboardButton(text="Открыть мини-приложение", web_app=WebAppInfo(url=url))]])
        m = await update.effective_chat.send_message(hello or "Откройте мини-приложение:", reply_markup=kb_inline)
        asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))
    elif use_inline:
        kb_inline = InlineKeyboardMarkup([[InlineKeyboardButton(text="Открыть приложение в браузере", url=url)]])
        m = await update.effective_chat.send_message(hello or f"Откройте приложение:\n{url}", reply_markup=kb_inline)
        asyncio.create_task(_delete_later(context, m.chat_id, m.message_id))
    else:
        await _ephemeral_send(update, context, hello or f"Откройте приложение в браузере:\n{url}")
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
