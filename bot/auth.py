# bot/auth.py
# Регистрация по паролю + постоянная клавиатура с кнопками
# [ИЗМЕНЕНО v5.8] Единственный «якорь-меню»: перед показом нового удаляем старый; все служебные сообщения автоудаляются.
# [ИЗМЕНЕНО v5.7] Мгновенные ответы, удаление в фоне.
# [ИЗМЕНЕНО v4.9] Автоудаление сообщений, связанных с паролем.
# [ИСПРАВЛЕНО v5.9] Миграция схемы users: убран ранний return по наличию user_id; добавлена проверка полного набора столбцов и безопасная миграция.

import os
import re
import sqlite3
import asyncio
import html
from io import BytesIO
from urllib.parse import urlencode, urlparse
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update,
    WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, MessageHandler,
    ContextTypes, filters,
)
from config import Config
from app.auth_links import create_auth_token
from app.account_types import migrate_account_types
from app.i18n import SUPPORTED_UI_LANGUAGES
from app.family_pairing import (
    create_invite_code,
    create_pairing_code,
    invite_code_details,
    link_child_with_invite_code,
    link_parent_with_pairing_code,
    linked_children,
    linked_parents,
    pairing_code_details,
)
from bot.onboarding import (
    LANGUAGE_LABELS,
    account_type,
    bot_interface_text,
    bot_interface_values,
    complete_account_type,
    normalize_telegram_language,
    onboarding_text,
    save_detected_language,
    save_selected_ui_language,
    selected_ui_language,
)

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
                account_type TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cols = _columns(c, "users")

        # Если схема уже совпадает (множества равны) — ничего не делаем
        if set(expected).issubset(set(cols)):
            migrate_account_types(c)
            return

        # Иначе мигрируем в новую таблицу с полной схемой
        c.execute("""
            CREATE TABLE IF NOT EXISTS users_new (
                user_id    TEXT PRIMARY KEY,
                username   TEXT,
                first_name TEXT,
                last_name  TEXT,
                is_active  INTEGER NOT NULL DEFAULT 1,
                account_type TEXT NOT NULL DEFAULT 'standard',
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
            migrate_account_types(c)
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
        migrate_account_types(c)
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
            INSERT INTO users (
                user_id, username, first_name, last_name, is_active, account_type
            )
            VALUES (?, ?, ?, ?, 1, 'pending')
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
    if _is_https(base):
        token = create_auth_token(user_id)
        return (base + "/?" + urlencode({"auth": token}), True, True)
    url = base + "/"; return (url, False, not _is_local_address(url))

def _build_android_app_url(user_id: int) -> str:
    base = f"{Config.PUBLIC_BASE_URL}".rstrip("/")
    return base + "/android-auth?" + urlencode({"token": create_auth_token(user_id)})

def _build_android_download_url() -> str:
    base = f"{Config.PUBLIC_BASE_URL}".rstrip("/")
    return base + "/static/downloads/learnwords.apk"

def _user_interface_language(user_id: int | str, telegram_language: str | None = None) -> str:
    return selected_ui_language(Config.DB_PATH, user_id) or normalize_telegram_language(
        telegram_language
    )


def get_persistent_keyboard(
    user_id: int,
    telegram_language: str | None = None,
) -> ReplyKeyboardMarkup:
    language = _user_interface_language(user_id, telegram_language)
    url, use_webapp, _ = _build_app_url(user_id)
    if use_webapp:
        btn_learn = KeyboardButton(
            text=bot_interface_text(language, "learn_words"),
            web_app=WebAppInfo(url=url),
        )
    else:
        btn_learn = KeyboardButton(text=bot_interface_text(language, "learn_words"))
    btn_add = KeyboardButton(text=bot_interface_text(language, "upload_words"))
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
    telegram_language = getattr(update.effective_user, "language_code", None)
    language = _user_interface_language(user_id, telegram_language)
    m = await update.effective_chat.send_message(
        bot_interface_text(language, "menu"),
        reply_markup=get_persistent_keyboard(user_id, telegram_language),
    )
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
            onboarding_text(user.language_code, "identity_required"),
        )
        return False
    is_new = _register_user(Config.DB_PATH, user)
    save_detected_language(Config.DB_PATH, user.id, user.language_code)
    if is_new:
        await _notify_admins_new_user(context, user)
    return is_new


def _language_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=LANGUAGE_LABELS[code],
            callback_data=f"onboarding:language:{code}",
        )
        for code in SUPPORTED_UI_LANGUAGES
    ]
    return InlineKeyboardMarkup([
        buttons[index:index + 2]
        for index in range(0, len(buttons), 2)
    ])


def _detected_language_keyboard(language_code: str | None) -> InlineKeyboardMarkup:
    language = normalize_telegram_language(language_code)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=onboarding_text(language, "confirm_language_yes"),
            callback_data=f"onboarding:language_keep:{language}",
        )],
        [InlineKeyboardButton(
            text=onboarding_text(language, "confirm_language_no"),
            callback_data="onboarding:language_change:list",
        )],
    ])


def _onboarding_language(user_id: int | str, telegram_language: str | None) -> str:
    return _user_interface_language(user_id, telegram_language)


def _account_type_keyboard(language_code: str | None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=onboarding_text(language_code, "standard_account"),
            callback_data="onboarding:account:standard",
        )],
        [InlineKeyboardButton(
            text=onboarding_text(language_code, "child_account"),
            callback_data="onboarding:account:child",
        )],
    ])


async def _replace_or_send_onboarding_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup: InlineKeyboardMarkup,
) -> None:
    query = update.callback_query
    if query and query.message:
        try:
            await query.edit_message_text(text=text, reply_markup=reply_markup)
            context.user_data["onboarding_msg_id"] = query.message.message_id
            return
        except Exception:
            pass

    old_id = context.user_data.get("onboarding_msg_id")
    if old_id:
        asyncio.create_task(_safe_delete(context, update.effective_chat.id, old_id))
    message = await update.effective_chat.send_message(text, reply_markup=reply_markup)
    context.user_data["onboarding_msg_id"] = message.message_id


async def _show_onboarding_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user or account_type(Config.DB_PATH, user.id) != "pending":
        return False
    if selected_ui_language(Config.DB_PATH, user.id):
        language = _onboarding_language(user.id, user.language_code)
        await _replace_or_send_onboarding_message(
            update,
            context,
            onboarding_text(language, "choose_account"),
            _account_type_keyboard(language),
        )
    else:
        language = normalize_telegram_language(user.language_code)
        await _replace_or_send_onboarding_message(
            update,
            context,
            onboarding_text(
                language,
                "confirm_detected_language",
                language=LANGUAGE_LABELS[language],
            ),
            _detected_language_keyboard(language),
        )
    return True


def _family_start_payload(context: ContextTypes.DEFAULT_TYPE) -> tuple[str, str]:
    """Returns (kind, code): kind is "family" for a child-issued code (scanned by a
    parent) or "invite" for a parent-issued code (accepted by a child)."""
    args = list(getattr(context, "args", None) or [])
    if not args:
        return "", ""
    payload = str(args[0] or "").strip()
    if payload.startswith("family_"):
        code = payload.removeprefix("family_")
        return ("family", code) if code and len(code) <= 48 else ("", "")
    if payload.startswith("invite_"):
        code = payload.removeprefix("invite_")
        return ("invite", code) if code and len(code) <= 48 else ("", "")
    return "", ""


async def _send_child_pairing_invite(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> bool:
    user = update.effective_user
    language = _user_interface_language(
        user_id,
        user.language_code if user else None,
    )
    if account_type(Config.DB_PATH, user_id) != "child":
        await update.effective_chat.send_message(
            onboarding_text(language, "pairing_child_only")
        )
        return False
    try:
        code = create_pairing_code(Config.DB_PATH, user_id)
        bot_user = await context.bot.get_me()
        bot_username = str(bot_user.username or "").lstrip("@")
        if not bot_username:
            raise ValueError("bot_username_required")
        pairing_url = f"https://t.me/{bot_username}?start=family_{code}"

        import qrcode

        image = qrcode.make(pairing_url)
        output = BytesIO()
        output.name = "parent-link.png"
        image.save(output, format="PNG")
        output.seek(0)
        caption = onboarding_text(
            language,
            "pairing_caption",
            url=pairing_url,
        )
        parents = linked_parents(Config.DB_PATH, user_id)
        if parents:
            caption += "\n\n👥 " + "\n👤 ".join(
                parent["display_name"] for parent in parents
            )
        await update.effective_chat.send_photo(
            photo=output,
            caption=caption,
        )
        return True
    except Exception:
        await update.effective_chat.send_message(
            onboarding_text(language, "pairing_invalid")
        )
        return False


async def _send_parent_invite(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> bool:
    """Reverse of _send_child_pairing_invite: a standard (parent) account invites a child."""
    user = update.effective_user
    language = _user_interface_language(
        user_id,
        user.language_code if user else None,
    )
    if account_type(Config.DB_PATH, user_id) != "standard":
        await update.effective_chat.send_message(
            onboarding_text(language, "pairing_parent_only")
        )
        return False
    try:
        code = create_invite_code(Config.DB_PATH, user_id)
        bot_user = await context.bot.get_me()
        bot_username = str(bot_user.username or "").lstrip("@")
        if not bot_username:
            raise ValueError("bot_username_required")
        invite_url = f"https://t.me/{bot_username}?start=invite_{code}"

        import qrcode

        image = qrcode.make(invite_url)
        output = BytesIO()
        output.name = "child-invite.png"
        image.save(output, format="PNG")
        output.seek(0)
        caption = onboarding_text(
            language,
            "invite_caption",
            url=invite_url,
        )
        children = linked_children(Config.DB_PATH, user_id)
        if children:
            caption += "\n\n👶 " + "\n🧒 ".join(
                child["display_name"] for child in children
            )
        await update.effective_chat.send_photo(
            photo=output,
            caption=caption,
        )
        return True
    except Exception:
        await update.effective_chat.send_message(
            onboarding_text(language, "pairing_invalid")
        )
        return False


def _pairing_error_text(language_code: str | None, error: str, kind: str = "family") -> str:
    if error == "parent_limit_reached":
        key = "pairing_parent_limit"
    elif kind == "invite" and error in {
        "account_type_required", "parent_cannot_be_child", "cannot_link_self",
    }:
        key = "pairing_child_required"
    elif error in {"account_type_required", "child_cannot_be_parent", "cannot_link_self"}:
        key = "pairing_parent_required"
    else:
        key = "pairing_invalid"
    return onboarding_text(language_code, key)


async def _show_pending_family_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    code = str(context.user_data.get("pending_family_code", "") or "")
    if not code:
        return False
    kind = str(context.user_data.get("pending_family_kind", "") or "family")
    user = update.effective_user
    language = _user_interface_language(user.id, user.language_code)

    if kind == "invite":
        if account_type(Config.DB_PATH, user.id) != "child":
            context.user_data.pop("pending_family_code", None)
            context.user_data.pop("pending_family_kind", None)
            await update.effective_chat.send_message(
                onboarding_text(language, "pairing_child_required")
            )
            return False
        details = invite_code_details(Config.DB_PATH, code)
        if not details:
            context.user_data.pop("pending_family_code", None)
            context.user_data.pop("pending_family_kind", None)
            await update.effective_chat.send_message(
                onboarding_text(language, "pairing_invalid")
            )
            return False
        await update.effective_chat.send_message(
            onboarding_text(
                language,
                "pairing_join_confirm",
                name=details["parent_display_name"],
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    onboarding_text(language, "pairing_confirm_button"),
                    callback_data=f"family_join:confirm:{code}",
                )],
                [InlineKeyboardButton(
                    onboarding_text(language, "pairing_cancel_button"),
                    callback_data=f"family_join:cancel:{code}",
                )],
            ]),
        )
        return True

    if account_type(Config.DB_PATH, user.id) != "standard":
        context.user_data.pop("pending_family_code", None)
        context.user_data.pop("pending_family_kind", None)
        await update.effective_chat.send_message(
            onboarding_text(language, "pairing_parent_required")
        )
        return False
    details = pairing_code_details(Config.DB_PATH, code)
    if not details:
        context.user_data.pop("pending_family_code", None)
        context.user_data.pop("pending_family_kind", None)
        await update.effective_chat.send_message(
            onboarding_text(language, "pairing_invalid")
        )
        return False
    await update.effective_chat.send_message(
        onboarding_text(
            language,
            "pairing_confirm",
            name=details["child_display_name"],
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                onboarding_text(language, "pairing_confirm_button"),
                callback_data=f"family_link:confirm:{code}",
            )],
            [InlineKeyboardButton(
                onboarding_text(language, "pairing_cancel_button"),
                callback_data=f"family_link:cancel:{code}",
            )],
        ]),
    )
    return True


async def family_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    parts = str(query.data or "").split(":", 2)
    if len(parts) != 3 or parts[0] != "family_join":
        await query.answer()
        return
    action, code = parts[1], parts[2]
    language = _user_interface_language(user.id, user.language_code)
    await query.answer()
    if context.user_data.get("pending_family_code") == code:
        context.user_data.pop("pending_family_code", None)
        context.user_data.pop("pending_family_kind", None)
    if action == "cancel":
        await query.edit_message_text(
            onboarding_text(language, "pairing_cancelled")
        )
        return
    if action != "confirm":
        return
    result = link_child_with_invite_code(Config.DB_PATH, user.id, code)
    if result.get("ok"):
        text = onboarding_text(
            language,
            "pairing_joined",
            name=result.get("parent_display_name") or result.get("parent_user_id") or "",
        )
    else:
        text = _pairing_error_text(language, str(result.get("error") or ""), kind="invite")
    await query.edit_message_text(text)


async def family_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return
    parts = str(query.data or "").split(":", 2)
    if len(parts) != 3 or parts[0] != "family_link":
        await query.answer()
        return
    action, code = parts[1], parts[2]
    language = _user_interface_language(user.id, user.language_code)
    await query.answer()
    if context.user_data.get("pending_family_code") == code:
        context.user_data.pop("pending_family_code", None)
        context.user_data.pop("pending_family_kind", None)
    if action == "cancel":
        await query.edit_message_text(
            onboarding_text(language, "pairing_cancelled")
        )
        return
    if action != "confirm":
        return
    result = link_parent_with_pairing_code(Config.DB_PATH, user.id, code)
    if result.get("ok"):
        text = onboarding_text(
            language,
            "pairing_linked",
            name=result.get("child_display_name") or result.get("child_user_id") or "",
        )
    else:
        text = _pairing_error_text(language, str(result.get("error") or ""))
    await query.edit_message_text(text)


async def onboarding_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return

    parts = str(query.data or "").split(":", 2)
    if len(parts) != 3 or parts[0] != "onboarding":
        await query.answer()
        return
    step, value = parts[1], parts[2]

    if account_type(Config.DB_PATH, user.id) != "pending":
        await query.answer()
        return

    language = _onboarding_language(user.id, user.language_code)

    if step == "language_keep":
        if value not in SUPPORTED_UI_LANGUAGES or not save_selected_ui_language(
            Config.DB_PATH, user.id, value
        ):
            await query.answer(
                onboarding_text(language, "invalid_choice"),
                show_alert=True,
            )
            return
        await query.answer()
        await _replace_or_send_onboarding_message(
            update,
            context,
            onboarding_text(value, "choose_account"),
            _account_type_keyboard(value),
        )
        return

    if step == "language_change":
        if value != "list":
            await query.answer(
                onboarding_text(language, "invalid_choice"),
                show_alert=True,
            )
            return
        await query.answer()
        await _replace_or_send_onboarding_message(
            update,
            context,
            onboarding_text(language, "choose_language"),
            _language_keyboard(),
        )
        return

    if step == "language":
        if not save_selected_ui_language(Config.DB_PATH, user.id, value):
            await query.answer(
                onboarding_text(language, "invalid_choice"),
                show_alert=True,
            )
            return
        await query.answer()
        await _replace_or_send_onboarding_message(
            update,
            context,
            onboarding_text(value, "choose_account"),
            _account_type_keyboard(value),
        )
        return

    if step != "account" or value not in {"standard", "child"}:
        await query.answer(
            onboarding_text(language, "invalid_choice"),
            show_alert=True,
        )
        return
    if not selected_ui_language(Config.DB_PATH, user.id):
        await query.answer(
            onboarding_text(language, "choose_language_first"),
            show_alert=True,
        )
        await _replace_or_send_onboarding_message(
            update,
            context,
            onboarding_text(
                language,
                "confirm_detected_language",
                language=LANGUAGE_LABELS[language],
            ),
            _detected_language_keyboard(language),
        )
        return
    if not complete_account_type(Config.DB_PATH, user.id, value):
        await query.answer()
        return

    await query.answer()
    language = _onboarding_language(user.id, user.language_code)
    completion_text = onboarding_text(language, "completed")
    try:
        await query.edit_message_text(completion_text)
    except Exception:
        await update.effective_chat.send_message(completion_text)
    context.user_data.pop("onboarding_msg_id", None)
    pending_kind = str(context.user_data.get("pending_family_kind", "") or "family")
    required_role = "child" if pending_kind == "invite" else "standard"
    handled_pending = False
    if context.user_data.get("pending_family_code"):
        if value == required_role:
            handled_pending = await _show_pending_family_confirmation(update, context)
        else:
            context.user_data.pop("pending_family_code", None)
            context.user_data.pop("pending_family_kind", None)
            await update.effective_chat.send_message(
                onboarding_text(
                    language,
                    "pairing_child_required" if required_role == "child" else "pairing_parent_required",
                )
            )
    if value != "standard" and not handled_pending:
        await _send_child_pairing_invite(update, context, user.id)
    await show_menu_with_keyboard(update, context, user.id)
    await _send_fresh_app_link(update, context, user.id)


async def _send_fresh_app_link(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, text: str = "") -> None:
    old_id = context.user_data.get("open_link_msg_id")
    if old_id:
        asyncio.create_task(_safe_delete(context, update.effective_chat.id, old_id))

    url, use_webapp, use_inline = _build_app_url(user_id)
    user = update.effective_user if update else None
    language = _user_interface_language(
        user_id,
        user.language_code if user else None,
    )
    buttons = []
    if use_webapp:
        buttons.append([InlineKeyboardButton(text=bot_interface_text(language, "open_mini_app"), web_app=WebAppInfo(url=url))])
        buttons.append([InlineKeyboardButton(text=bot_interface_text(language, "open_browser"), url=url)])
    elif use_inline:
        buttons.append([InlineKeyboardButton(text=bot_interface_text(language, "open_app"), url=url)])
    buttons.append([InlineKeyboardButton(text=bot_interface_text(language, "download_android"), url=_build_android_download_url())])
    buttons.append([InlineKeyboardButton(text=bot_interface_text(language, "login_android"), url=_build_android_app_url(user_id))])

    if buttons:
        m = await update.effective_chat.send_message(
            text or bot_interface_text(language, "fresh_login_link"),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        context.user_data["open_link_msg_id"] = m.message_id
    else:
        await update.effective_chat.send_message(
            text or f'{bot_interface_text(language, "fresh_login_link")}\n{url}'
        )


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await _delete_user_trigger(update, context)
    context.user_data.pop("await_pwd", None)
    is_new = await _ensure_open_registration(update, context)
    if not _is_user_registered(Config.DB_PATH, user.id):
        return
    family_kind, family_code = _family_start_payload(context)
    if family_code:
        context.user_data["pending_family_code"] = family_code
        context.user_data["pending_family_kind"] = family_kind
    if await _show_onboarding_step(update, context):
        return
    if await _show_pending_family_confirmation(update, context):
        return
    await show_menu_with_keyboard(update, context, user.id)
    await _send_fresh_app_link(update, context, user.id)
    if is_new:
        language = _user_interface_language(user.id, user.language_code)
        await _ephemeral_send(update, context, bot_interface_text(language, "trial_ready"))
    else:
        language = _user_interface_language(user.id, user.language_code)
        await _ephemeral_send(update, context, bot_interface_text(language, "welcome_back"))

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if context.user_data.get("await_pwd"):
        context.user_data.pop("await_pwd", None)
        for mid in context.user_data.get("pwd_bot_msg_ids", []):
            asyncio.create_task(_delete_later(context, update.effective_chat.id, mid, 0))
        context.user_data["pwd_bot_msg_ids"] = []
        is_new = await _ensure_open_registration(update, context)
        if await _show_onboarding_step(update, context):
            return
        await show_menu_with_keyboard(update, context, user_id)
        language = _user_interface_language(
            user_id,
            update.effective_user.language_code,
        )
        await _ephemeral_send(
            update,
            context,
            bot_interface_text(
                language,
                "trial_ready" if is_new else "password_not_needed",
            ),
        )
        return

    # Восстанавливаем клавиатуру для зарегистрированных пользователей
    # (один раз за сессию — после рестарта бота user_data сбрасывается)
    if account_type(Config.DB_PATH, user_id) == "pending":
        await _show_onboarding_step(update, context)
        return
    if not context.user_data.get("kb_shown") and _is_user_registered(Config.DB_PATH, user_id):
        context.user_data["kb_shown"] = True
        await show_menu_with_keyboard(update, context, user_id)

async def open_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_open(update, context)


async def family_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await _delete_user_trigger(update, context)
    await _ensure_open_registration(update, context)
    if not user or not _is_user_registered(Config.DB_PATH, user.id):
        return
    if await _show_onboarding_step(update, context):
        return
    if account_type(Config.DB_PATH, user.id) == "standard":
        await _send_parent_invite(update, context, user.id)
    else:
        await _send_child_pairing_invite(update, context, user.id)

async def send_open(update: Update, context: ContextTypes.DEFAULT_TYPE, hello: str = "") -> None:
    user_id = update.effective_user.id if (update and update.effective_user) else 0
    if update and update.effective_user:
        await _ensure_open_registration(update, context)
        if not _is_user_registered(Config.DB_PATH, user_id):
            return
        if await _show_onboarding_step(update, context):
            return
    await _delete_user_trigger(update, context)
    language = _user_interface_language(
        user_id,
        update.effective_user.language_code if update.effective_user else None,
    )
    await _send_fresh_app_link(
        update,
        context,
        user_id,
        hello or bot_interface_text(language, "fresh_login_link"),
    )
    await show_menu_with_keyboard(update, context, user_id)  # ← ИЗМЕНЕНО

def register_auth_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("open", open_cmd))
    application.add_handler(CommandHandler("family", family_cmd))
    application.add_handler(CallbackQueryHandler(
        onboarding_callback,
        pattern=r"^onboarding:(?:language|language_keep|language_change|account):",
    ))
    application.add_handler(CallbackQueryHandler(
        family_link_callback,
        pattern=r"^family_link:(?:confirm|cancel):",
    ))
    application.add_handler(CallbackQueryHandler(
        family_join_callback,
        pattern=r"^family_join:(?:confirm|cancel):",
    ))
    learn_words_pattern = "^(?:" + "|".join(
        re.escape(value) for value in bot_interface_values("learn_words")
    ) + ")$"
    application.add_handler(MessageHandler(filters.Regex(learn_words_pattern), open_cmd))
    # Исключаем кнопки подтверждения (регистронезависимо)
    exclude_import_btns = ~filters.Regex(r"(?i)^(импортировать как есть|отменить импорт)$")
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND) & exclude_import_btns, on_text),
        group=100
    )
