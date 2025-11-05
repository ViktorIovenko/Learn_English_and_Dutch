# bot/auth.py
# Регистрация по паролю + постоянная клавиатура с кнопками
# [ИЗМЕНЕНО v4.8] Всегда добавляем ?uid=<id> в URL (даже для WebApp) как фолбэк.

import os
import sqlite3
from urllib.parse import urlparse

from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update,
    WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from config import Config


# ---------- sqlite utils ----------
def _conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

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
        p = urlparse(url)
        host = (p.hostname or "").lower()
        if host in ("localhost",):
            return True
        if host.startswith("127.") or host.startswith("10.") or host.startswith("192.168."):
            return True
        if host.startswith("172."):
            parts = host.split(".")
            if len(parts) >= 2:
                try:
                    second = int(parts[1])
                    return 16 <= second <= 31
                except Exception:
                    pass
        return False
    except Exception:
        return True

def _build_app_url(user_id: int) -> tuple[str, bool, bool]:
    """
    Возвращает (url, use_webapp, use_inline).
    [ИЗМЕНЕНО v4.8] Даже для HTTPS/WebApp добавляем ?uid=<id>, чтобы фронт
    всегда мог подставить X-User-Id и авторизоваться без initData.
    """
    base = f"{Config.PUBLIC_BASE_URL}".rstrip("/")
    uid_suffix = f"/?uid={user_id}"
    if _is_https(base):
        # WebApp доступен — даём URL с uid
        return (base + uid_suffix, True, True)
    # HTTP (локалка) — обычная ссылка с uid
    url = base + uid_suffix
    return (url, False, not _is_local_address(url))


# [ИЗМЕНЕНО v4.7] экспортируем функцию клавиатуры (без изменений ниже)
def get_persistent_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    url, use_webapp, _ = _build_app_url(user_id)
    if use_webapp:
        btn_learn = KeyboardButton(text="Учить слова", web_app=WebAppInfo(url=url))
    else:
        btn_learn = KeyboardButton(text="Учить слова")
    btn_add = KeyboardButton(text="Добавить слова")
    return ReplyKeyboardMarkup(
        keyboard=[[btn_learn], [btn_add]],
        resize_keyboard=True,
        is_persistent=True,
        one_time_keyboard=False
    )


# ---------- handlers ----------
ASK_PWD = "Введите пароль для регистрации:"
OK_PWD  = "✅ Готово! Вы зарегистрированы."

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if _is_user_registered(Config.DB_PATH, user.id):
        await update.message.reply_text("С возвращением!", reply_markup=get_persistent_keyboard(user.id))
        return
    await update.message.reply_text(ASK_PWD, reply_markup=get_persistent_keyboard(user.id))
    context.user_data["await_pwd"] = True

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("await_pwd"):
        pwd = (update.message.text or "").strip()
        expected = _get_expected_password()
        if pwd == expected:
            _register_user(Config.DB_PATH, update.effective_user)
            context.user_data.pop("await_pwd", None)
            await update.message.reply_text(OK_PWD, reply_markup=get_persistent_keyboard(update.effective_user.id))
        else:
            await update.message.reply_text("Пароль неверный. Попробуйте снова.",
                                            reply_markup=get_persistent_keyboard(update.effective_user.id))
        return
    if (update.message.text or "").strip() == "Учить слова":
        await send_open(update, context)

async def open_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_open(update, context)

async def send_open(update: Update, context: ContextTypes.DEFAULT_TYPE, hello: str = "") -> None:
    user_id = update.effective_user.id if (update and update.effective_user) else ""
    url, use_webapp, use_inline = _build_app_url(user_id)

    if use_webapp:
        kb_inline = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Открыть мини-приложение", web_app=WebAppInfo(url=url))]]
        )
        await update.message.reply_text(hello or "Откройте мини-приложение:", reply_markup=kb_inline)
    elif use_inline:
        kb_inline = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Открыть приложение в браузере", url=url)]]
        )
        await update.message.reply_text(hello or f"Откройте приложение:\n{url}", reply_markup=kb_inline)
    else:
        await update.message.reply_text(hello or f"Откройте приложение в браузере:\n{url}")

    try:
        await update.message.reply_text("Меню внизу ⬇️", reply_markup=get_persistent_keyboard(user_id))
    except Exception:
        pass


def register_auth_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("open", open_cmd))
    application.add_handler(MessageHandler(filters.Regex(r"^(Учить слова)$"), open_cmd))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), on_text))
