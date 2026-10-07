# app/routes.py
from __future__ import annotations
import json
import time
import secrets
import html
from contextlib import closing
from io import BytesIO
from urllib.parse import urlencode
from urllib import request as urlrequest
from flask import Blueprint, request, jsonify, render_template, session, send_file, send_from_directory, current_app, redirect
import sqlite3
from typing import Any, List, Dict
from pathlib import Path
from config import Config
from app.telegram_auth import verify_telegram_init_data
from app.auth_links import create_auth_token, verify_auth_token
from app.account_types import migrate_account_types, migrate_auth_identities
from app.family_tokens import (
    PAIRING_TOKEN_MAX_AGE_SECONDS,
    create_pairing_token,
    verify_pairing_token,
)
from app.family_pairing import (
    MAX_PARENTS_PER_CHILD,
    create_invite_code,
    create_pairing_code,
    invite_code_details,
    link_child_with_invite_code,
    pairing_code_details,
)
from app.family_invites import invitation_payload, preview_invitation, accept_invitation, allow_invitation_attempt
from app.i18n import get_catalog, get_legacy_catalog, normalize_language, translate
from app import models
# [ДОБАВЛЕНО v7.0] генерация аудио
from app.audio_gen import ensure_audio_for_ids  # ← НОВОЕ
from app.tts_usage import (
    get_tts_usage_snapshot,
    reset_tts_usage,
    set_tts_character_limit,
)
from app.translation_usage import (
    get_translation_usage_snapshot,
    record_translation_usage,
    reset_translation_usage,
)
from app import ai_platform

web = Blueprint("web", __name__)

LANGUAGE_OPTIONS = [
    {"code": "en", "name": "English", "native": "English"},
    {"code": "ru", "name": "Russian", "native": "Русский"},
    {"code": "nl", "name": "Dutch", "native": "Nederlands"},
    {"code": "de", "name": "German", "native": "Deutsch"},
    {"code": "fr", "name": "French", "native": "Français"},
    {"code": "es", "name": "Spanish", "native": "Español"},
    {"code": "it", "name": "Italian", "native": "Italiano"},
    {"code": "pt", "name": "Portuguese", "native": "Português"},
    {"code": "pl", "name": "Polish", "native": "Polski"},
    {"code": "uk", "name": "Ukrainian", "native": "Українська"},
]
LANGUAGE_CODES = {item["code"] for item in LANGUAGE_OPTIONS}
LANGUAGE_META = {item["code"]: item for item in LANGUAGE_OPTIONS}
BASE_WORD_COLUMNS = {"id", "user_id", "status", "lesson", "number", "difficult", "updated_at"}
_BOT_USERNAME_CACHE = ""


def _telegram_bot_username() -> str:
    global _BOT_USERNAME_CACHE
    configured = str(getattr(Config, "BOT_USERNAME", "") or "").strip().lstrip("@")
    if configured:
        return configured
    if _BOT_USERNAME_CACHE:
        return _BOT_USERNAME_CACHE
    token = str(getattr(Config, "BOT_TOKEN", "") or "").strip()
    if not token:
        return ""
    try:
        with urlrequest.urlopen(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=8,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
        username = str((payload.get("result") or {}).get("username") or "").strip().lstrip("@")
        if username:
            _BOT_USERNAME_CACHE = username
        return username
    except Exception:
        return ""


def _word_text_col(lang: str) -> str:
    return lang


def _word_sentence_col(lang: str) -> str:
    return f"ex_{lang}"


def _word_audio_col(lang: str) -> str:
    return f"audio_{lang}"


def _language_select_parts(languages: list[str]) -> list[str]:
    parts: list[str] = []
    for lang in languages:
        parts.extend([
            f"w.{_word_text_col(lang)} AS {lang}_word",
            f"w.{_word_sentence_col(lang)} AS {lang}_sentence",
            f"w.{_word_audio_col(lang)} AS {lang}_audio",
        ])
    return parts


def _ensure_word_language_columns(conn: sqlite3.Connection, languages: list[str] | set[str]) -> None:
    valid = [str(code).strip().lower() for code in languages if str(code).strip().lower() in LANGUAGE_CODES]
    if not valid:
        return
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(words)")}
    for lang in valid:
        for col in (_word_text_col(lang), _word_sentence_col(lang), _word_audio_col(lang)):
            if col not in cols:
                conn.execute(f"ALTER TABLE words ADD COLUMN {col} TEXT;")
                cols.add(col)


def _existing_word_languages(conn: sqlite3.Connection) -> list[str]:
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(words)")}
    ordered_codes = [
        "nl", "en", "ru",
        *[item["code"] for item in LANGUAGE_OPTIONS if item["code"] not in {"nl", "en", "ru"}],
    ]
    return [
        code for code in ordered_codes
        if _word_text_col(code) in cols and _word_sentence_col(code) in cols and _word_audio_col(code) in cols
    ]


def _word_payload_from_row(row: sqlite3.Row | dict[str, Any], languages: list[str], user_id: str | None = None) -> dict[str, Any]:
    d = dict(row)
    payload = {
        "id": d.get("id"),
        "lesson": d.get("lesson", ""),
        "number": d.get("number", ""),
        "difficult": bool(d.get("difficult")),
        "status": d.get("status", "") or "",
    }
    payload.update({key: str(d.get(key) or "") for key in ("content_sense","content_context","example_level")})
    for lang in languages:
        word = d.get(f"{lang}_word", d.get(lang, "")) or ""
        sentence = d.get(f"{lang}_sentence", d.get(f"ex_{lang}", "")) or ""
        audio = d.get(f"{lang}_audio", d.get(f"audio_{lang}", "")) or ""
        payload[f"{lang}_word"] = word
        payload[f"{lang}_sentence"] = sentence
        payload[f"{lang}_audio"] = audio
        payload[lang] = word
        payload[f"ex_{lang}"] = sentence
        payload[f"audio_{lang}"] = audio
        payload[f"sentence_{lang}"] = sentence
    payload.setdefault("word_en", payload.get("en_word", ""))
    payload.setdefault("translation_ru", payload.get("ru_word", ""))
    payload.setdefault("translation_nl", payload.get("nl_word", ""))
    payload.setdefault("sentence_en", payload.get("en_sentence", ""))
    payload.setdefault("sentence_ru", payload.get("ru_sentence", ""))
    payload.setdefault("sentence_nl", payload.get("nl_sentence", ""))
    payload.setdefault("audio_en", payload.get("en_audio", ""))
    payload.setdefault("audio_ru", payload.get("ru_audio", ""))
    payload.setdefault("audio_nl", payload.get("nl_audio", ""))
    if user_id is not None:
        payload["editable"] = (d.get("_word_owner") or d.get("user_id") or "") == str(user_id) or d.get("status") == "test"
    return payload


def _lesson_available_languages(rows: list[sqlite3.Row] | list[dict[str, Any]], preferred: list[str], all_languages: list[str]) -> list[dict[str, Any]]:
    ordered = list(dict.fromkeys(preferred or all_languages))
    available: list[dict[str, Any]] = []
    for lang in ordered:
        has_value = any(
            str((dict(row).get(f"{lang}_word") or dict(row).get(lang) or "")).strip()
            for row in rows
        )
        if has_value:
            meta = LANGUAGE_META.get(lang, {"code": lang, "name": lang.upper(), "native": lang.upper()})
            available.append({"code": lang, "name": meta["name"], "native": meta["native"]})
    return available


def _conn() -> sqlite3.Connection:
    from app.content_db import connect
    conn = connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _record_translation_request_usage(
    user_id: str,
    *,
    successful: bool,
    usage: Any = None,
) -> None:
    """Persist usage without allowing telemetry failures to break translation."""
    try:
        with closing(_conn()) as conn:
            record_translation_usage(
                conn,
                user_id,
                successful=successful,
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
                total_tokens=getattr(usage, "total_tokens", 0),
            )
            conn.commit()
    except Exception:
        current_app.logger.exception("Could not record translation token usage")


def _admin_ids() -> tuple[int, ...]:
    raw = getattr(Config, "ADMIN_IDS", ()) or ()
    result: list[int] = []
    for item in raw:
        try:
            result.append(int(item))
        except Exception:
            pass
    return tuple(dict.fromkeys(result))


def _is_admin_user_id(user_id: str | int | None) -> bool:
    if user_id is None:
        return False
    try:
        return int(str(user_id)) in set(_admin_ids())
    except Exception:
        return False


def _request_user_id() -> str:
    if session.get("is_auth"):
        return str(session.get("tg_user_id") or "").strip()
    bearer = _bearer_user_id()
    if bearer:
        return bearer
    if Config.ALLOW_LEGACY_UID_AUTH:
        return str(request.headers.get("X-User-Id") or request.args.get("uid") or "").strip()
    return ""


def _session_admin_user_id() -> str:
    uid = str(session.get("tg_user_id") or "").strip()
    if not uid or not session.get("is_auth"):
        return ""
    return uid if _is_admin_user_id(uid) else ""


def _session_user_id() -> str:
    uid = str(session.get("tg_user_id") or "").strip()
    if not uid or not session.get("is_auth"):
        return ""
    return uid


def _user_exists(user_id: str | None) -> bool:
    uid = str(user_id or "").strip()
    if not uid:
        return False
    with _conn() as c:
        return bool(c.execute("SELECT 1 FROM users WHERE user_id=?", (uid,)).fetchone())


def _has_telegram_identity(user: dict[str, Any]) -> bool:
    return bool(
        str(user.get("username") or "").strip()
        or str(user.get("first_name") or "").strip()
        or str(user.get("last_name") or "").strip()
    )


def _load_user_to_session(user_id: str) -> bool:
    uid = str(user_id or "").strip()
    if not uid or not _user_exists(uid):
        return False
    with _conn() as c:
        row = c.execute(
            "SELECT username, first_name, last_name FROM users WHERE user_id=?",
            (uid,),
        ).fetchone()
    session["tg_user_id"] = uid
    session["tg_username"] = (row["username"] if row else "") or ""
    session["tg_first_name"] = (row["first_name"] if row else "") or ""
    session["tg_last_name"] = (row["last_name"] if row else "") or ""
    session["is_auth"] = True
    return True


def _redirect_without_auth_param():
    args = request.args.to_dict(flat=True)
    args.pop("auth", None)
    query = urlencode(args)
    target = request.path + (f"?{query}" if query else "")
    return redirect(target, code=302)


@web.before_request
def consume_auth_link_token():
    token = (request.args.get("auth") or "").strip()
    if not token:
        return None
    user_id = verify_auth_token(token)
    if user_id:
        _load_user_to_session(user_id)
    return _redirect_without_auth_param()


def _format_user_name(row: sqlite3.Row | dict[str, Any]) -> str:
    first = (row["first_name"] or "").strip()
    last = (row["last_name"] or "").strip()
    username = (row["username"] or "").strip()
    full = " ".join(part for part in [first, last] if part).strip()
    return full or (f"@{username}" if username else "")


def _notify_admins_new_user(user: dict[str, Any]) -> None:
    token = (Config.BOT_TOKEN or "").strip()
    if not token:
        return
    user_id = str(user.get("id") or user.get("user_id") or "").strip()
    if not user_id:
        return
    username = str(user.get("username") or "").strip()
    full_name = " ".join(
        part for part in [
            str(user.get("first_name") or "").strip(),
            str(user.get("last_name") or "").strip(),
        ] if part
    ).strip() or "без имени"
    username_text = f"@{username}" if username else "без username"
    text = (
        "👤 Новый пользователь\n"
        f"ID: <code>{html.escape(user_id)}</code>\n"
        f"Имя: {html.escape(full_name)}\n"
        f"Username: {html.escape(username_text)}"
    )
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    for admin_id in _admin_ids():
        payload = urlencode({
            "chat_id": str(admin_id),
            "text": text,
            "parse_mode": "HTML",
        }).encode("utf-8")
        try:
            urlrequest.urlopen(api_url, data=payload, timeout=4).read()
        except Exception:
            current_app.logger.exception("Failed to notify admin %s about new user %s", admin_id, user_id)


def _upsert_user(user: dict[str, Any]) -> bool:
    user_id = str(user.get("id") or "").strip()
    if not user_id or not _has_telegram_identity(user):
        return False
    photo_url = str(user.get("photo_url") or "").strip()
    with _conn() as c:
        columns = {row[1] for row in c.execute("PRAGMA table_info(users)")}
        if "photo_url" not in columns:
            c.execute("ALTER TABLE users ADD COLUMN photo_url TEXT")
        existed = bool(c.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone())
        c.execute("""
            INSERT INTO users (
                user_id, username, first_name, last_name, is_active, account_type, photo_url
            )
            VALUES (?, ?, ?, ?, 1, 'pending', ?)
            ON CONFLICT(user_id) DO UPDATE SET
              username=excluded.username,
              first_name=excluded.first_name,
              last_name=excluded.last_name,
              is_active=1,
              photo_url=CASE WHEN excluded.photo_url <> '' THEN excluded.photo_url ELSE photo_url END
        """, (user_id,
              user.get("username") or "",
              user.get("first_name") or "",
              user.get("last_name") or "",
              photo_url))
        c.commit()
    return not existed


def _upsert_user_minimal(user_id: str) -> bool:
    if not user_id:
        return False
    with _conn() as c:
        existed = bool(c.execute("SELECT 1 FROM users WHERE user_id=?", (str(user_id),)).fetchone())
        c.execute("""
            INSERT INTO users (
                user_id, username, first_name, last_name, is_active, account_type
            )
            VALUES (?, '', '', '', 1, 'pending')
            ON CONFLICT(user_id) DO NOTHING
        """, (str(user_id),))
        c.commit()
    return not existed


def _bearer_user_id() -> str:
    """Signed, server-issued token from Authorization: Bearer <token>.

    Unlike X-User-Id (a raw value the client can set to anything), this token
    is HMAC-signed by create_auth_token() at login time and can't be forged,
    so native clients (Android) can authenticate without reintroducing
    browser-controlled X-User-Id — see docs/APP_DOMAIN_MIGRATION.md.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return ""
    return verify_auth_token(auth_header[7:].strip())


def _current_user_id() -> str | None:
    uid = session.get("tg_user_id") if session.get("is_auth") else None
    if not uid:
        uid = _bearer_user_id() or None
    if not uid and Config.ALLOW_LEGACY_UID_AUTH:
        uid = request.headers.get("X-User-Id") or request.args.get("uid") or None
    if uid:
        uid = str(uid)
        _update_detected_ui_language(uid, request.headers.get("X-Device-Language"))
    return uid if uid else None


# --- [ИЗМЕНЕНО v6.4] миграция схемы: персональные флаги; УБРАНЫ кастомные слова ---
def _ensure_schema() -> None:
    with _conn() as c:
        # (1) на всякий случай колонка difficult в words (оставляем как legacy)
        cols = [r["name"] for r in c.execute("PRAGMA table_info(words)")]
        if "user_id" not in cols:
            c.execute("ALTER TABLE words ADD COLUMN user_id TEXT;")
            c.execute("UPDATE words SET user_id = '' WHERE user_id IS NULL;")
        if "status" not in cols:
            c.execute("ALTER TABLE words ADD COLUMN status TEXT NOT NULL DEFAULT 'user';")
        c.execute("""
            UPDATE words
            SET status = 'user'
            WHERE COALESCE(status, '') = ''
        """)
        c.execute("DROP INDEX IF EXISTS u_words_number;")
        c.execute("DROP INDEX IF EXISTS idx_words_lesson_number;")
        c.execute("DROP INDEX IF EXISTS idx_words_user_lesson_number;")
        c.execute("CREATE INDEX IF NOT EXISTS idx_words_lesson ON words(lesson);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_words_user_lesson ON words(user_id, lesson);")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS u_words_user_lesson_number ON words(user_id, lesson, number);")
        if "difficult" not in cols:
            c.execute("ALTER TABLE words ADD COLUMN difficult INTEGER NOT NULL DEFAULT 0;")
        if "updated_at" not in cols:
            c.execute("ALTER TABLE words ADD COLUMN updated_at INTEGER;")
            c.execute("UPDATE words SET updated_at = (strftime('%s','now') * 1000) WHERE updated_at IS NULL;")
        _ensure_word_language_columns(c, ["nl", "en", "ru"])
        # (2) флаги пользователя для слов из words
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_word_flags (
                user_id  TEXT NOT NULL,
                word_id  INTEGER NOT NULL,
                difficult INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (user_id, word_id)
            );
        """)
        c.commit()


def _ensure_progress_schema() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS progress_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                scope TEXT,
                event_type TEXT,
                event_ts INTEGER,
                payload TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_progress_events_user_ts
            ON progress_events(user_id, event_ts);
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS child_goal_notifications (
                child_user_id TEXT NOT NULL,
                parent_user_id TEXT NOT NULL,
                local_date TEXT NOT NULL,
                message_id INTEGER,
                sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (child_user_id, parent_user_id, local_date)
            );
        """)
        notification_columns = {
            str(row["name"]) for row in c.execute(
                "PRAGMA table_info(child_goal_notifications)"
            ).fetchall()
        }
        if "message_id" not in notification_columns:
            c.execute(
                "ALTER TABLE child_goal_notifications ADD COLUMN message_id INTEGER"
            )
        c.commit()


CHILD_DAILY_WORD_GOAL = 25
CHILD_WORD_MASTERY_COUNT = 10
STANDARD_DAILY_MINUTES_GOAL = 10


def _ensure_daily_goal_schema() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_daily_goals (
                user_id TEXT PRIMARY KEY,
                goal_value INTEGER NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.commit()


def _daily_goal_settings(user_id: str) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    account_type = _account_context(uid)["account_type"]
    goal_type = "words" if account_type == "child" else "minutes"
    default_value = CHILD_DAILY_WORD_GOAL if goal_type == "words" else STANDARD_DAILY_MINUTES_GOAL
    _ensure_daily_goal_schema()
    with _conn() as c:
        row = c.execute(
            "SELECT goal_value FROM user_daily_goals WHERE user_id=?", (uid,)
        ).fetchone()
    value = int(row["goal_value"]) if row else default_value
    minimum, maximum = ((5, 100) if goal_type == "words" else (1, 180))
    return {
        "goal_type": goal_type,
        "goal_value": max(minimum, min(maximum, value)),
        "minimum": minimum,
        "maximum": maximum,
    }


def _child_learning_stats(
    user_id: str,
    timezone_offset_minutes: int = 0,
    connection=None,
) -> Dict[str, Any]:
    """Derive the child's daily goal and per-word mastery from accepted answers."""
    uid = str(user_id or "").strip()
    if not uid:
        return {"today_count": 0, "word_counts": {}, "mastered_word_ids": set()}
    owns_connection = connection is None
    if owns_connection:
        _ensure_progress_schema()
    c = connection or _conn()
    try:
        rows = c.execute("""
            SELECT event_type, event_ts, payload
            FROM progress_events
            WHERE user_id = ? AND scope = 'learn'
            ORDER BY event_ts ASC, id ASC
        """, (uid,)).fetchall()
    finally:
        if owns_connection:
            c.close()

    offset_ms = int(timezone_offset_minutes) * 60 * 1000
    day_ms = 24 * 60 * 60 * 1000
    today_number = (int(time.time() * 1000) - offset_ms) // day_ms
    counts: Dict[str, int] = {}
    today_count = 0
    for row in rows:
        try:
            payload = json.loads(row["payload"] or "{}")
        except (TypeError, ValueError):
            continue
        state = payload.get("state") if isinstance(payload, dict) else None
        if not isinstance(state, dict):
            continue
        reason = str(state.get("reason") or "")
        if reason != "answer_ok" and str(row["event_type"] or "") != "word_correct":
            continue
        word_id = str(state.get("word_id") or "").strip()
        if not word_id or counts.get(word_id, 0) >= CHILD_WORD_MASTERY_COUNT:
            continue
        counts[word_id] = counts.get(word_id, 0) + 1
        try:
            event_day = (int(row["event_ts"]) - offset_ms) // day_ms
        except (TypeError, ValueError):
            event_day = -1
        if event_day == today_number:
            today_count += 1
    return {
        "today_count": today_count,
        "word_counts": counts,
        "mastered_word_ids": {
            word_id for word_id, count in counts.items()
            if count >= CHILD_WORD_MASTERY_COUNT
        },
    }


def _notify_parents_child_goal(user_id: str, timezone_offset_minutes: int) -> int:
    """Notify linked Telegram parents once when today's 25-word goal is reached."""
    uid = str(user_id or "").strip()
    if not uid or _account_context(uid)["account_type"] != "child":
        return 0
    stats = _child_learning_stats(uid, timezone_offset_minutes)
    goal = _daily_goal_settings(uid)["goal_value"]
    if stats["today_count"] < goal:
        return 0
    token = str(Config.BOT_TOKEN or "").strip()
    if not token:
        return 0
    offset_ms = int(timezone_offset_minutes) * 60 * 1000
    local_day = (int(time.time() * 1000) - offset_ms) // (24 * 60 * 60 * 1000)
    local_date = time.strftime("%Y-%m-%d", time.gmtime(local_day * 24 * 60 * 60))
    with _conn() as c:
        child = c.execute(
            "SELECT user_id, username, first_name, last_name FROM users WHERE user_id=?",
            (uid,),
        ).fetchone()
        parents = c.execute("""
            SELECT u.user_id
            FROM parent_child_links l
            JOIN users u ON u.user_id = l.parent_user_id
            WHERE l.child_user_id = ? AND COALESCE(u.is_active, 1) = 1
        """, (uid,)).fetchall()
    child_name = _format_user_name(child) if child else uid
    text = f"🏆 Ребёнок {child_name or uid} выполнил дневную цель — {goal} слов!"
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    delete_url = f"https://api.telegram.org/bot{token}/deleteMessage"
    sent = 0
    for parent in parents:
        parent_id = str(parent["user_id"] or "").strip()
        if not parent_id.isdigit():
            continue
        with _conn() as c:
            previous = c.execute("""
                SELECT message_id
                FROM child_goal_notifications
                WHERE child_user_id=? AND parent_user_id=?
                  AND message_id IS NOT NULL
                ORDER BY local_date DESC
                LIMIT 1
            """, (uid, parent_id)).fetchone()
            previous_message_id = int(previous["message_id"]) if previous else None
            cursor = c.execute("""
                INSERT OR IGNORE INTO child_goal_notifications
                    (child_user_id, parent_user_id, local_date)
                VALUES (?, ?, ?)
            """, (uid, parent_id, local_date))
            c.commit()
            reserved = cursor.rowcount > 0
        if not reserved:
            continue
        payload = urlencode({"chat_id": parent_id, "text": text}).encode("utf-8")
        try:
            with urlrequest.urlopen(api_url, data=payload, timeout=4) as response:
                result = json.loads(response.read().decode("utf-8"))
            if not result.get("ok"):
                raise RuntimeError("telegram_send_failed")
            message_id = int((result.get("result") or {}).get("message_id") or 0)
            if not message_id:
                raise RuntimeError("telegram_message_id_missing")
            with _conn() as c:
                c.execute("""
                    UPDATE child_goal_notifications
                    SET message_id=?, sent_at=CURRENT_TIMESTAMP
                    WHERE child_user_id=? AND parent_user_id=? AND local_date=?
                """, (message_id, uid, parent_id, local_date))
                c.commit()
            sent += 1
            if previous_message_id and previous_message_id != message_id:
                delete_payload = urlencode({
                    "chat_id": parent_id,
                    "message_id": str(previous_message_id),
                }).encode("utf-8")
                try:
                    urlrequest.urlopen(delete_url, data=delete_payload, timeout=4).read()
                except Exception:
                    current_app.logger.warning(
                        "Could not delete previous child-goal message %s for parent %s",
                        previous_message_id,
                        parent_id,
                    )
        except Exception:
            with _conn() as c:
                c.execute("""
                    DELETE FROM child_goal_notifications
                    WHERE child_user_id=? AND parent_user_id=? AND local_date=?
                """, (uid, parent_id, local_date))
                c.commit()
            current_app.logger.exception(
                "Failed to notify parent %s about child goal %s", parent_id, uid
            )
    return sent


def _ensure_user_language_schema() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_language_preferences (
                user_id TEXT NOT NULL,
                priority INTEGER NOT NULL,
                lang_code TEXT NOT NULL,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY (user_id, priority),
                UNIQUE (user_id, lang_code)
            );
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_language_preferences_user
            ON user_language_preferences(user_id, priority);
        """)
        c.commit()


def _normalize_supported_language(code: str | None, fallback: str = "en") -> str:
    raw = str(code or "").strip().lower().split("-", 1)[0].split("_", 1)[0]
    return raw if raw in LANGUAGE_CODES else fallback


def _ensure_user_settings_schema() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                detected_ui_language TEXT,
                ui_language_override TEXT,
                updated_at INTEGER NOT NULL
            );
        """)
        c.commit()


def _ensure_family_schema() -> None:
    with _conn() as c:
        migrate_account_types(c)
        user_columns = {row[1] for row in c.execute("PRAGMA table_info(users)")}
        if "photo_url" not in user_columns:
            c.execute("ALTER TABLE users ADD COLUMN photo_url TEXT")
        c.execute("""
            CREATE TABLE IF NOT EXISTS parent_child_links (
                parent_user_id TEXT NOT NULL,
                child_user_id  TEXT NOT NULL,
                created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (parent_user_id, child_user_id),
                CHECK (parent_user_id <> child_user_id),
                FOREIGN KEY (parent_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (child_user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_parent_child_links_child "
            "ON parent_child_links(child_user_id)"
        )
        # Canonical family lessons are deliberately not copied into the child
        # account.  The assignment is the access grant to the parent's words.
        c.execute("""
            CREATE TABLE IF NOT EXISTS family_lesson_assignments (
                parent_user_id TEXT NOT NULL,
                child_user_id  TEXT NOT NULL,
                lesson         TEXT NOT NULL,
                created_at     INTEGER NOT NULL,
                PRIMARY KEY (parent_user_id, child_user_id, lesson),
                FOREIGN KEY (parent_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (child_user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_family_lesson_assignments_child "
            "ON family_lesson_assignments(child_user_id, lesson)"
        )
        _ensure_family_assignment_archive_columns(c)
        shared_words_table_existed = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='shared_lesson_words'"
        ).fetchone() is not None
        c.execute("""
            CREATE TABLE IF NOT EXISTS shared_lesson_words (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_user_id TEXT NOT NULL,
                child_user_id  TEXT NOT NULL,
                lesson         TEXT NOT NULL,
                parent_word_id INTEGER NOT NULL,
                child_word_id  INTEGER NOT NULL UNIQUE,
                created_at     INTEGER NOT NULL,
                UNIQUE (parent_user_id, child_user_id, parent_word_id)
            )
        """)
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_shared_lesson_words_parent "
            "ON shared_lesson_words(parent_word_id)"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_shared_lesson_words_child "
            "ON shared_lesson_words(child_word_id)"
        )
        if not shared_words_table_existed:
            word_columns = {row["name"] for row in c.execute("PRAGMA table_info(words)")}
            signature_columns = []
            for language in _existing_word_languages(c):
                signature_columns.extend(
                    column for column in (_word_text_col(language), _word_sentence_col(language))
                    if column in word_columns
                )
            if signature_columns:
                selected = ", ".join(["id", "lesson", *signature_columns])
                pairs = c.execute(
                    "SELECT parent_user_id, child_user_id FROM parent_child_links"
                ).fetchall()
                now_ms = int(time.time() * 1000)
                for pair in pairs:
                    parent_rows = c.execute(
                        f"SELECT {selected} FROM words WHERE user_id=? ORDER BY id",
                        (pair["parent_user_id"],),
                    ).fetchall()
                    child_rows = c.execute(
                        f"SELECT {selected} FROM words WHERE user_id=? ORDER BY id",
                        (pair["child_user_id"],),
                    ).fetchall()
                    parent_by_content: Dict[tuple, List[int]] = {}
                    for row in parent_rows:
                        signature = (row["lesson"], *(row[column] or "" for column in signature_columns))
                        parent_by_content.setdefault(signature, []).append(int(row["id"]))
                    for row in child_rows:
                        signature = (row["lesson"], *(row[column] or "" for column in signature_columns))
                        matches = parent_by_content.get(signature) or []
                        if not matches:
                            continue
                        c.execute("""
                            INSERT OR IGNORE INTO shared_lesson_words (
                                parent_user_id, child_user_id, lesson,
                                parent_word_id, child_word_id, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            pair["parent_user_id"], pair["child_user_id"], row["lesson"],
                            matches.pop(0), int(row["id"]), now_ms,
                        ))
        c.execute("""
            CREATE TABLE IF NOT EXISTS child_lesson_priorities (
                child_user_id  TEXT PRIMARY KEY,
                lesson         TEXT NOT NULL,
                parent_user_id TEXT NOT NULL,
                updated_at     INTEGER NOT NULL,
                FOREIGN KEY (child_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (parent_user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS child_lesson_priority_history (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                child_user_id     TEXT NOT NULL,
                lesson            TEXT NOT NULL,
                parent_user_id    TEXT NOT NULL,
                started_at        INTEGER NOT NULL,
                ended_at          INTEGER,
                FOREIGN KEY (child_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (parent_user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_child_priority_history_child_started
            ON child_lesson_priority_history(child_user_id, started_at DESC)
        """)
        c.execute("""
            INSERT INTO child_lesson_priority_history
                (child_user_id, lesson, parent_user_id, started_at, ended_at)
            SELECT p.child_user_id, p.lesson, p.parent_user_id, p.updated_at, NULL
            FROM child_lesson_priorities p
            WHERE NOT EXISTS (
                SELECT 1
                FROM child_lesson_priority_history h
                WHERE h.child_user_id = p.child_user_id AND h.ended_at IS NULL
            )
        """)
        c.commit()


def _ensure_family_assignment_archive_columns(connection) -> None:
    """Archive support for child assignments: an archived lesson keeps its
    assignment row (words, progress and difficult flags stay reachable) but
    leaves the child's active lesson list. ``activated_at`` is bumped when a
    lesson is (re)activated so the "last N assigned" rule follows the latest
    activation, not the original assignment date."""
    columns = {row[1] for row in connection.execute("PRAGMA table_info(family_lesson_assignments)")}
    if "archived_at" not in columns:
        connection.execute("ALTER TABLE family_lesson_assignments ADD COLUMN archived_at INTEGER")
    if "activated_at" not in columns:
        connection.execute("ALTER TABLE family_lesson_assignments ADD COLUMN activated_at INTEGER")
    flag_columns = {row[1] for row in connection.execute("PRAGMA table_info(user_word_flags)")}
    if flag_columns:
        # Per-user difficult flags keep their origin so error-based automation
        # can later be distinguished from a manual mark.
        if "source" not in flag_columns:
            connection.execute("ALTER TABLE user_word_flags ADD COLUMN source TEXT NOT NULL DEFAULT 'manual'")
        if "updated_at" not in flag_columns:
            connection.execute("ALTER TABLE user_word_flags ADD COLUMN updated_at INTEGER")


def _child_priority_lesson(child_user_id: str, connection=None) -> str:
    uid = str(child_user_id or "").strip()
    if not uid:
        return ""

    def read(c):
        row = c.execute(
            "SELECT lesson FROM child_lesson_priorities WHERE child_user_id=?",
            (uid,),
        ).fetchone()
        return str((row["lesson"] if row else "") or "")

    if connection is not None:
        return read(connection)
    _ensure_family_schema()
    with _conn() as c:
        return read(c)


def _lessons_available_to_child(child_user_id: str) -> List[Dict[str, Any]]:
    try:
        return models.get_lessons(Config.DB_PATH, child_user_id)
    except sqlite3.OperationalError as exc:
        if "no such column: w.status" not in str(exc):
            raise
        return models.get_user_lessons(Config.DB_PATH, child_user_id)


def _revoke_family_lesson_access(connection, parent_user_id: str, child_user_id: str) -> None:
    """Unlinking a parent/child must also drop the assignment rows those two
    accounts left behind — _child_lesson_owner() below only checks
    family_lesson_assignments, not parent_child_links, so a former child
    keeps read access to the ex-parent's lessons (via MCP and the Mini App)
    for as long as those rows survive an unlink."""
    connection.execute(
        "DELETE FROM family_lesson_assignments WHERE parent_user_id=? AND child_user_id=?",
        (parent_user_id, child_user_id),
    )
    connection.execute(
        "DELETE FROM child_lesson_priorities WHERE parent_user_id=? AND child_user_id=?",
        (parent_user_id, child_user_id),
    )
    connection.execute(
        "UPDATE child_lesson_priority_history SET ended_at=? "
        "WHERE parent_user_id=? AND child_user_id=? AND ended_at IS NULL",
        (int(time.time() * 1000), parent_user_id, child_user_id),
    )


def _child_lesson_owner(connection, child_user_id: str, lesson: str) -> str:
    """Return the canonical word owner when this child may read *lesson*."""
    child_id = str(child_user_id or "").strip()
    title = str(lesson or "").strip()
    if not child_id or not title:
        return ""
    connection.execute("""
        CREATE TABLE IF NOT EXISTS user_lessons (
            user_id TEXT NOT NULL,
            lesson  TEXT NOT NULL,
            hidden  INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, lesson)
        );
    """)
    if connection.execute(
        "SELECT 1 FROM words WHERE user_id=? AND lesson=? LIMIT 1",
        (child_id, title),
    ).fetchone():
        return child_id
    row = connection.execute("""
        SELECT a.parent_user_id
        FROM family_lesson_assignments a
        JOIN words w ON w.user_id=a.parent_user_id AND w.lesson=a.lesson
        LEFT JOIN user_lessons canonical_state
          ON canonical_state.user_id=a.parent_user_id AND canonical_state.lesson=a.lesson
        WHERE a.child_user_id=? AND a.lesson=?
          AND COALESCE(canonical_state.hidden, 0)=0
        LIMIT 1
    """, (child_id, title)).fetchone()
    return str(row["parent_user_id"]) if row else ""


def get_visible_lessons_for_user(user_id: str) -> List[Dict[str, Any]]:
    """Single child-aware lesson resolver used by Mini App and MCP."""
    uid = str(user_id or "").strip()
    own = models.get_lessons(Config.DB_PATH, uid)
    if not uid or _account_context(uid)["account_type"] != "child":
        return own
    _ensure_family_schema()
    by_title = {str(item.get("lesson") or ""): item for item in own}
    with _conn() as c:
        child_hidden = {
            str(row["lesson"]): bool(row["hidden"])
            for row in c.execute("SELECT lesson, hidden FROM user_lessons WHERE user_id=?", (uid,))
        }
        rows = c.execute("""
            SELECT a.lesson, a.parent_user_id, COUNT(w.id) AS words_count,
                   MAX(w.id) AS upload_order,
                   MIN(CAST(SUBSTR(w.number, 1, INSTR(w.number || '.', '.') - 1) AS INTEGER)) AS lesson_index
            FROM family_lesson_assignments a
            JOIN words w ON w.user_id=a.parent_user_id AND w.lesson=a.lesson
            LEFT JOIN user_lessons canonical_state
              ON canonical_state.user_id=a.parent_user_id AND canonical_state.lesson=a.lesson
            WHERE a.child_user_id=? AND COALESCE(canonical_state.hidden, 0)=0
              AND a.archived_at IS NULL
            GROUP BY a.parent_user_id, a.lesson
        """, (uid,)).fetchall()
    for row in rows:
        title = str(row["lesson"] or "")
        # A child's own lesson remains authoritative if titles collide.
        if not title or title in by_title:
            continue
        by_title[title] = {
            "lesson": title,
            "lesson_title": title,
            "word_count": int(row["words_count"] or 0),
            "words_count": int(row["words_count"] or 0),
            "upload_order": int(row["upload_order"] or 0),
            "lesson_index": int(row["lesson_index"] or 0),
            "hidden": child_hidden.get(title, False),
            "assigned_family_lesson": True,
            "owner_user_id": str(row["parent_user_id"]),
        }
    return list(by_title.values())


def _lesson_owner_map(user_id: str, lessons: List[Dict[str, Any]] | None = None) -> Dict[str, str]:
    """Map lesson title -> the user_id whose `words` rows actually hold it.

    A child's own lessons are owned by the child; a lesson assigned by a
    parent (family_lesson_assignments) is still stored under the parent's
    user_id, so progress lookups must query that owner, not the child.
    """
    uid = str(user_id or "").strip()
    items = lessons if lessons is not None else get_visible_lessons_for_user(uid)
    return {
        str(item.get("lesson_title") or item.get("lesson") or ""): str(item.get("owner_user_id") or uid)
        for item in items
    }


def _account_context(user_id: str | None) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        return {
            "account_type": "",
            "needs_account_type": False,
            "is_parent": False,
            "children_count": 0,
        }
    _ensure_family_schema()
    with _conn() as c:
        row = c.execute(
            "SELECT account_type FROM users WHERE user_id=?",
            (uid,),
        ).fetchone()
        children_count = int(c.execute(
            "SELECT COUNT(*) FROM parent_child_links WHERE parent_user_id=?",
            (uid,),
        ).fetchone()[0])
        is_linked_child = bool(c.execute(
            "SELECT 1 FROM parent_child_links WHERE child_user_id=?",
            (uid,),
        ).fetchone())
    account_type = str((row["account_type"] if row else "") or "standard")
    if account_type not in {"pending", "child", "standard"}:
        account_type = "standard"
    # A user still linked as a child under a parent account must stay a child
    # account no matter what account_type ended up stored (missing row, bad
    # migration, blank/corrupt value, etc.) — only unlinking clears this.
    if is_linked_child:
        account_type = "child"
    return {
        "account_type": account_type,
        "needs_account_type": account_type == "pending",
        "is_parent": children_count > 0,
        "children_count": children_count,
    }


def _family_status(user_id: str) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    account = _account_context(uid)
    with _conn() as c:
        children = [dict(row) for row in c.execute("""
            SELECT u.user_id, u.username, u.first_name, u.last_name, u.photo_url, l.created_at
            FROM parent_child_links l
            JOIN users u ON u.user_id = l.child_user_id
            WHERE l.parent_user_id = ?
            ORDER BY COALESCE(u.first_name, ''), COALESCE(u.username, ''), u.user_id
        """, (uid,)).fetchall()]
        parents = [dict(row) for row in c.execute("""
            SELECT u.user_id, u.username, u.first_name, u.last_name, u.photo_url, l.created_at
            FROM parent_child_links l
            JOIN users u ON u.user_id = l.parent_user_id
            WHERE l.child_user_id = ?
            ORDER BY COALESCE(u.first_name, ''), COALESCE(u.username, ''), u.user_id
        """, (uid,)).fetchall()]
    for item in children + parents:
        item["display_name"] = _format_user_name(item) or item["user_id"]
    return {**account, "children": children, "parents": parents}


def _family_dashboard_data(parent_user_id: str, days: int, timezone_offset_minutes: int) -> Dict[str, Any]:
    """Build learning statistics only for children linked to this parent."""
    _ensure_family_schema()
    _ensure_progress_schema()
    uid = str(parent_user_id or "").strip()
    now_ms = int(time.time() * 1000)
    day_ms = 24 * 60 * 60 * 1000
    offset_ms = timezone_offset_minutes * 60 * 1000
    local_today_number = (now_ms + offset_ms) // day_ms
    first_day_number = local_today_number - days + 1
    range_start_ms = first_day_number * day_ms - offset_ms

    def day_key(day_number: int) -> str:
        return time.strftime("%Y-%m-%d", time.gmtime(day_number * 24 * 60 * 60))

    day_keys = [day_key(first_day_number + index) for index in range(days)]
    with _conn() as c:
        children = [dict(row) for row in c.execute("""
            SELECT u.user_id, u.username, u.first_name, u.last_name, u.photo_url, l.created_at
            FROM parent_child_links l
            JOIN users u ON u.user_id = l.child_user_id
            WHERE l.parent_user_id = ?
            ORDER BY COALESCE(u.first_name, ''), COALESCE(u.username, ''), u.user_id
        """, (uid,)).fetchall()]
        child_ids = [str(item["user_id"]) for item in children]
        if not child_ids:
            return {
                "days": days,
                "timezone_offset_minutes": timezone_offset_minutes,
                "range_start": day_keys[0],
                "range_end": day_keys[-1],
                "children": [],
            }

        placeholders = ",".join("?" for _ in child_ids)
        parents_by_child: Dict[str, List[Dict[str, Any]]] = {
            child_id: [] for child_id in child_ids
        }
        for row in c.execute(f"""
            SELECT
                l.child_user_id,
                u.user_id,
                u.username,
                u.first_name,
                u.last_name,
                u.photo_url,
                l.created_at
            FROM parent_child_links l
            JOIN users u ON u.user_id = l.parent_user_id
            WHERE l.child_user_id IN ({placeholders})
            ORDER BY l.child_user_id,
                     COALESCE(u.first_name, ''),
                     COALESCE(u.username, ''),
                     u.user_id
        """, child_ids).fetchall():
            parent = dict(row)
            child_id = str(parent.pop("child_user_id"))
            parent["display_name"] = _format_user_name(parent) or str(parent["user_id"])
            parents_by_child.setdefault(child_id, []).append(parent)
        events = [dict(row) for row in c.execute(f"""
            SELECT user_id, event_type, event_ts, payload
            FROM progress_events
            WHERE user_id IN ({placeholders}) AND event_ts >= ? AND event_ts <= ?
            ORDER BY event_ts ASC, id ASC
        """, [*child_ids, range_start_ms, now_ms]).fetchall()]
        last_activity = {
            str(row["user_id"]): int(row["last_event_ts"] or 0)
            for row in c.execute(f"""
                SELECT user_id, MAX(event_ts) AS last_event_ts
                FROM progress_events
                WHERE user_id IN ({placeholders})
                GROUP BY user_id
            """, child_ids).fetchall()
        }
        streaks = _learning_streaks(child_ids, timezone_offset_minutes, connection=c)
        child_learning_stats = {
            child_id: _child_learning_stats(
                child_id,
                -timezone_offset_minutes,
                connection=c,
            )
            for child_id in child_ids
        }
        priority_lessons = {
            child_id: _child_priority_lesson(child_id, connection=c)
            for child_id in child_ids
        }
        priority_history: Dict[str, List[Dict[str, Any]]] = {
            child_id: [] for child_id in child_ids
        }
        for row in c.execute(f"""
            SELECT child_user_id, lesson, parent_user_id, started_at, ended_at
            FROM child_lesson_priority_history
            WHERE child_user_id IN ({placeholders})
            ORDER BY child_user_id, started_at DESC, id DESC
        """, child_ids).fetchall():
            item = dict(row)
            child_id = str(item.pop("child_user_id"))
            started_at = int(item.get("started_at") or 0)
            ended_at = int(item.get("ended_at") or 0)
            item["started_at"] = started_at
            item["ended_at"] = ended_at or None
            item["duration_seconds"] = max(
                0,
                ((ended_at or now_ms) - started_at) // 1000,
            )
            item["is_active"] = ended_at == 0
            priority_history.setdefault(child_id, []).append(item)
        words_table_exists = bool(c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='words'"
        ).fetchone())
        word_stats: Dict[str, Dict[str, int]] = {}
        if words_table_exists:
            word_stats = {
                str(row["user_id"]): {
                    "words_count": int(row["words_count"] or 0),
                    "lessons_count": int(row["lessons_count"] or 0),
                }
                for row in c.execute(f"""
                    SELECT user_id,
                           COUNT(*) AS words_count,
                           COUNT(DISTINCT NULLIF(TRIM(lesson), '')) AS lessons_count
                    FROM words
                    WHERE user_id IN ({placeholders})
                    GROUP BY user_id
                """, child_ids).fetchall()
            }

    stats_by_child: Dict[str, Dict[str, Any]] = {}
    for child_id in child_ids:
        stats_by_child[child_id] = {
            "daily": {
                key: {"date": key, "correct": 0, "incorrect": 0, "events": 0, "_timestamps": []}
                for key in day_keys
            },
            "correct_answers": 0,
            "incorrect_answers": 0,
            "learning_days": set(),
            "active_lessons": set(),
            "mastered_words": set(),
            "word_practice_counts": {},
            "latest_progress": None,
            "latest_progress_ts": 0,
        }

    for event in events:
        child_id = str(event.get("user_id") or "")
        child_stats = stats_by_child.get(child_id)
        event_ts = int(event.get("event_ts") or 0)
        if not child_stats or event_ts <= 0:
            continue
        event_day_number = (event_ts + offset_ms) // day_ms
        key = day_key(event_day_number)
        daily = child_stats["daily"].get(key)
        if not daily:
            continue
        daily["events"] += 1
        daily["_timestamps"].append(event_ts)
        child_stats["learning_days"].add(key)
        try:
            payload = json.loads(event.get("payload") or "{}")
        except (TypeError, ValueError):
            payload = {}
        state = payload.get("state") if isinstance(payload, dict) else {}
        if not isinstance(state, dict):
            state = {}
        lesson = str(state.get("lesson") or "").strip()
        if lesson:
            child_stats["active_lessons"].add(lesson)
        reason = str(state.get("reason") or "")
        android_event_type = str(event.get("event_type") or "")
        if reason == "answer_wrong":
            # Older Android builds sent "answer_wrong" instead of "answer_fail".
            reason = "answer_fail"
        elif not reason:
            if android_event_type == "word_correct":
                reason = "answer_ok"
            elif android_event_type == "word_wrong":
                reason = "answer_fail"
        if reason == "answer_ok":
            word_id = state.get("word_id")
            word_key = str(word_id) if word_id is not None else ""
            practice_counts = child_stats["word_practice_counts"]
            if word_key and practice_counts.get(word_key, 0) >= CHILD_WORD_MASTERY_COUNT:
                continue
            if word_key:
                practice_counts[word_key] = practice_counts.get(word_key, 0) + 1
            daily["correct"] += 1
            child_stats["correct_answers"] += 1
            if word_key and practice_counts[word_key] >= CHILD_WORD_MASTERY_COUNT:
                child_stats["mastered_words"].add(word_key)
        elif reason == "answer_fail":
            daily["incorrect"] += 1
            child_stats["incorrect_answers"] += 1
        if event_ts >= child_stats["latest_progress_ts"]:
            child_stats["latest_progress_ts"] = event_ts
            child_stats["latest_progress"] = {
                "lesson": lesson,
                "passed": int(state.get("passed") or 0),
                "total": int(state.get("total") or 0),
                "event_ts": event_ts,
            }

    result_children = []
    for child in children:
        child_id = str(child["user_id"])
        stats = stats_by_child[child_id]
        correct = int(stats["correct_answers"])
        incorrect = int(stats["incorrect_answers"])
        answers = correct + incorrect
        stored = word_stats.get(child_id, {})
        today = stats["daily"][day_keys[-1]]
        today_timestamps = today["_timestamps"]
        today_learning_seconds = 0
        if today_timestamps:
            today_learning_seconds = 30
            for previous, current in zip(today_timestamps, today_timestamps[1:]):
                gap_seconds = max(0, (current - previous) // 1000)
                if gap_seconds <= 5 * 60:
                    today_learning_seconds += gap_seconds
        lifetime_learning = child_learning_stats[child_id]
        child_goal = _daily_goal_settings(child_id)["goal_value"]
        today_words = min(int(lifetime_learning["today_count"]), child_goal)
        today_milestone = max(
            (value for value in (5, 10, 15, 20, 25) if today_words >= value),
            default=0,
        )
        public_daily = []
        for daily_item in stats["daily"].values():
            public_daily.append({
                key: value for key, value in daily_item.items()
                if not key.startswith("_")
            })
        available_lessons = sorted(
            (
                item for item in _lessons_available_to_child(child_id)
                if str(item.get("lesson") or "").strip()
            ),
            key=lambda item: (
                -int(item.get("upload_order") or 0),
                str(item.get("lesson") or ""),
            ),
        )
        result_children.append({
            **child,
            "display_name": _format_user_name(child) or child_id,
            "languages": _get_user_languages(child_id),
            "parents": parents_by_child.get(child_id, []),
            "priority_lesson": priority_lessons.get(child_id, ""),
            "priority_history": priority_history.get(child_id, []),
            "available_lessons": [
                {
                    "lesson": str(item.get("lesson") or ""),
                    "lesson_title": str(item.get("lesson_title") or item.get("lesson") or ""),
                    "upload_order": int(item.get("upload_order") or 0),
                    "lesson_index": int(item.get("lesson_index") or 0),
                    "words_count": int(item.get("words_count") or item.get("word_count") or 0),
                }
                for item in available_lessons
            ],
            "summary": {
                "words_count": int(stored.get("words_count", 0)),
                "lessons_count": int(stored.get("lessons_count", 0)),
                "learning_days": len(stats["learning_days"]),
                "learning_streak_days": streaks.get(child_id, 0),
                "active_lessons": len(stats["active_lessons"]),
                "correct_answers": correct,
                "incorrect_answers": incorrect,
                "answers_count": answers,
                "success_rate": round(correct * 100 / answers) if answers else 0,
                "mastered_words": len(lifetime_learning["mastered_word_ids"]),
                "last_activity_ts": last_activity.get(child_id, 0),
                "studied_today": bool(today["events"]),
                "today_words": today_words,
                "daily_goal": child_goal,
                "today_goal_complete": today_words >= child_goal,
                "today_status_milestone": today_milestone,
                "today_learning_seconds": today_learning_seconds,
                "today_first_activity_ts": today_timestamps[0] if today_timestamps else 0,
                "today_last_activity_ts": today_timestamps[-1] if today_timestamps else 0,
            },
            "latest_progress": stats["latest_progress"],
            "daily": public_daily,
        })

    return {
        "days": days,
        "timezone_offset_minutes": timezone_offset_minutes,
        "range_start": day_keys[0],
        "range_end": day_keys[-1],
        "children": result_children,
    }


def _learning_streaks(
    user_ids: List[str],
    timezone_offset_minutes: int,
    connection=None,
) -> Dict[str, int]:
    """Return current consecutive learning-day streaks in the user's local time."""
    ids = [str(user_id).strip() for user_id in user_ids if str(user_id).strip()]
    if not ids:
        return {}
    _ensure_progress_schema()
    offset_ms = int(timezone_offset_minutes) * 60 * 1000
    day_ms = 24 * 60 * 60 * 1000
    today = (int(time.time() * 1000) + offset_ms) // day_ms
    placeholders = ",".join("?" for _ in ids)

    def read_rows(c):
        return c.execute(f"""
            SELECT user_id, event_ts
            FROM progress_events
            WHERE user_id IN ({placeholders})
            ORDER BY event_ts DESC
        """, ids).fetchall()

    if connection is None:
        with _conn() as c:
            rows = read_rows(c)
    else:
        rows = read_rows(connection)

    days_by_user = {user_id: set() for user_id in ids}
    for row in rows:
        event_ts = int(row["event_ts"] or 0)
        if event_ts > 0:
            days_by_user[str(row["user_id"])].add((event_ts + offset_ms) // day_ms)

    result: Dict[str, int] = {}
    for user_id, learning_days in days_by_user.items():
        cursor = today if today in learning_days else today - 1
        streak = 0
        while cursor in learning_days:
            streak += 1
            cursor -= 1
        result[user_id] = streak
    return result


def _update_detected_ui_language(user_id: str | None, language_code: str | None) -> None:
    uid = str(user_id or "").strip()
    if not uid:
        return
    lang = _normalize_supported_language(language_code, fallback="")
    if not lang:
        return
    _ensure_user_settings_schema()
    now_ms = int(time.time() * 1000)
    with _conn() as c:
        c.execute("""
            INSERT INTO user_settings (user_id, detected_ui_language, ui_language_override, updated_at)
            VALUES (?, ?, NULL, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                detected_ui_language=excluded.detected_ui_language,
                updated_at=excluded.updated_at
        """, (uid, lang, now_ms))
        c.commit()


def _get_ui_language(user_id: str | None) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    fallback = "en"
    if not uid:
        return {"ui_language": fallback, "detected_ui_language": fallback, "ui_language_override": None}
    _ensure_user_settings_schema()
    with _conn() as c:
        row = c.execute("""
            SELECT detected_ui_language, ui_language_override
            FROM user_settings
            WHERE user_id = ?
        """, (uid,)).fetchone()
    detected = _normalize_supported_language(row["detected_ui_language"] if row else None, fallback=fallback)
    override = row["ui_language_override"] if row and row["ui_language_override"] else None
    override = _normalize_supported_language(override, fallback="") or None
    return {
        "ui_language": override or detected,
        "detected_ui_language": detected,
        "ui_language_override": override,
    }


def _detect_browser_language() -> str:
    """Best-guess language from the client itself, for pages rendered before
    (or without) a stored per-user preference: the SPA/Android app's own
    header first, then the browser's standard Accept-Language."""
    return normalize_language(
        request.headers.get("X-Device-Language")
        or request.accept_languages.best_match(list(LANGUAGE_CODES))
        or "en"
    )


def _current_ui_language() -> str:
    uid = _current_user_id()
    if uid:
        return str(_get_ui_language(uid).get("ui_language") or "en")
    return _detect_browser_language()


def _save_ui_language_override(user_id: str, language_code: str | None) -> Dict[str, Any]:
    _ensure_user_settings_schema()
    override = _normalize_supported_language(language_code, fallback="") or None
    now_ms = int(time.time() * 1000)
    with _conn() as c:
        c.execute("""
            INSERT INTO user_settings (user_id, detected_ui_language, ui_language_override, updated_at)
            VALUES (?, NULL, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                ui_language_override=excluded.ui_language_override,
                updated_at=excluded.updated_at
        """, (str(user_id), override, now_ms))
        c.commit()
    return _get_ui_language(user_id)


def _ensure_subscription_schema() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                user_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'trial',
                trial_started_at INTEGER NOT NULL,
                trial_ends_at INTEGER NOT NULL,
                current_period_ends_at INTEGER,
                provider TEXT,
                provider_customer_id TEXT,
                provider_subscription_id TEXT,
                cancel_at_period_end INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL
            );
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status
            ON user_subscriptions(status, trial_ends_at, current_period_ends_at);
        """)
        c.commit()


def _get_subscription(user_id: str | None) -> Dict[str, Any]:
    if not user_id:
        return {"configured": False, "status": "anonymous", "access": False}
    if _is_admin_user_id(user_id):
        return {
            "configured": True,
            "status": "active",
            "raw_status": "active",
            "access": True,
            "trial_started_at": 0,
            "trial_ends_at": 0,
            "current_period_ends_at": None,
            "cancel_at_period_end": False,
            "provider": "admin",
            "days_left": 0,
            "is_admin": True,
            "is_unlimited": True,
        }
    _ensure_subscription_schema()
    now_ms = int(time.time() * 1000)
    trial_ms = 14 * 24 * 60 * 60 * 1000
    with _conn() as c:
        row = c.execute("""
            SELECT *
            FROM user_subscriptions
            WHERE user_id = ?
        """, (str(user_id),)).fetchone()
        if not row:
            trial_started_at = now_ms
            trial_ends_at = now_ms + trial_ms
            c.execute("""
                INSERT INTO user_subscriptions (
                    user_id, status, trial_started_at, trial_ends_at, updated_at
                ) VALUES (?, 'trial', ?, ?, ?)
            """, (str(user_id), trial_started_at, trial_ends_at, now_ms))
            c.commit()
            row = c.execute("SELECT * FROM user_subscriptions WHERE user_id = ?", (str(user_id),)).fetchone()

    status = row["status"] or "trial"
    trial_ends_at = int(row["trial_ends_at"] or 0)
    period_ends_at = row["current_period_ends_at"]
    period_ends_at = int(period_ends_at) if period_ends_at is not None else None

    trial_active = status == "trial" and trial_ends_at > now_ms
    paid_active = status == "active" and (period_ends_at is None or period_ends_at > now_ms)
    access = bool(trial_active or paid_active)
    unlimited_threshold_ms = now_ms + 10 * 365 * 24 * 60 * 60 * 1000
    is_unlimited = bool(
        paid_active
        and period_ends_at is not None
        and period_ends_at > unlimited_threshold_ms
    )
    days_left = 0
    if access:
        ends_at = trial_ends_at if trial_active else period_ends_at
        if ends_at:
            days_left = max(0, int((ends_at - now_ms + 86_399_999) // 86_400_000))

    effective_status = status
    if status == "trial" and not trial_active:
        effective_status = "trial_expired"
    elif status == "active" and not paid_active:
        effective_status = "expired"

    return {
        "configured": True,
        "status": effective_status,
        "raw_status": status,
        "access": access,
        "trial_started_at": int(row["trial_started_at"] or 0),
        "trial_ends_at": trial_ends_at,
        "current_period_ends_at": period_ends_at,
        "cancel_at_period_end": bool(row["cancel_at_period_end"]),
        "provider": row["provider"] or "",
        "days_left": days_left,
        "is_unlimited": is_unlimited,
    }


def _get_user_languages(user_id: str | None) -> List[Dict[str, Any]]:
    if not user_id:
        return []
    _ensure_user_language_schema()
    names = {item["code"]: item for item in LANGUAGE_OPTIONS}
    with _conn() as c:
        rows = c.execute("""
            SELECT priority, lang_code
            FROM user_language_preferences
            WHERE user_id = ?
            ORDER BY priority
        """, (str(user_id),)).fetchall()
    result = []
    for r in rows:
        meta = names.get(r["lang_code"], {"code": r["lang_code"], "name": r["lang_code"], "native": r["lang_code"]})
        result.append({
            "priority": int(r["priority"]),
            "code": r["lang_code"],
            "name": meta["name"],
            "native": meta["native"],
        })
    return result


def _languages_configured(user_id: str | None) -> bool:
    count = len(_get_user_languages(user_id))
    return 3 <= count <= 5


def _word_missing_language_summary(user_id: str, languages: list[str]) -> dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        return {"total_words": 0, "missing": [], "missing_total": 0}
    valid = [code for code in dict.fromkeys(languages) if code in LANGUAGE_CODES]
    with _conn() as c:
        _ensure_word_language_columns(c, valid)
        c.commit()
        total_words = int(c.execute(
            "SELECT COUNT(*) FROM words WHERE user_id=? AND COALESCE(lesson,'') != ''",
            (uid,),
        ).fetchone()[0] or 0)
        missing = []
        missing_total = 0
        for code in valid:
            col = _word_text_col(code)
            sentence_col = _word_sentence_col(code)
            count = int(c.execute(f"""
                SELECT COUNT(*)
                FROM words
                WHERE user_id=?
                  AND COALESCE(lesson,'') != ''
                  AND (COALESCE({col}, '') = '' OR COALESCE({sentence_col}, '') = '')
            """, (uid,)).fetchone()[0] or 0)
            if count:
                meta = LANGUAGE_META.get(code, {"code": code, "name": code.upper(), "native": code.upper()})
                missing.append({"code": code, "name": meta["name"], "native": meta["native"], "count": count})
                missing_total += count
    return {"total_words": total_words, "missing": missing, "missing_total": missing_total}


def _ensure_share_schema() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS shared_word_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL UNIQUE,
                owner_user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                lesson TEXT,
                payload TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER,
                import_count INTEGER NOT NULL DEFAULT 0,
                max_imports INTEGER
            );
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_shared_word_sets_token
            ON shared_word_sets(token);
        """)
        c.commit()


def _public_url(path: str) -> str:
    base = (Config.PUBLIC_BASE_URL or request.host_url or "").strip()
    if not base:
        base = request.host_url
    return base.rstrip("/") + "/" + path.lstrip("/")


# --- Audio cleanup helpers ---
def _audio_path_from_url(url: str) -> Path | None:
    raw = (url or "").split("?", 1)[0].strip()
    if not raw:
        return None
    if raw.startswith("/"):
        raw = raw[1:]
    if not raw.startswith("static/audio/"):
        return None
    root = Path(current_app.root_path).resolve()
    audio_root = (root / "static" / "audio").resolve()
    target = (root / raw).resolve()
    if target != audio_root and audio_root not in target.parents:
        return None
    return target


def _cleanup_audio_files(audio_urls: List[str]) -> int:
    if not audio_urls:
        return 0
    deleted = 0
    root = Path(current_app.root_path).resolve()
    audio_root = (root / "static" / "audio").resolve()
    with _conn() as c:
        for url in audio_urls:
            if not url:
                continue
            used = c.execute(
                "SELECT 1 FROM words WHERE " + " OR ".join(f'"{_word_audio_col(lang)}"=?' for lang in _existing_word_languages(c)) + " LIMIT 1",
                [url] * len(_existing_word_languages(c)),
            ).fetchone()
            if used:
                continue
            from app.audio_gen import is_cached_audio
            if is_cached_audio(Config.DB_PATH,url):
                continue
            target = _audio_path_from_url(url)
            if not target or not target.exists():
                continue
            try:
                target.unlink()
                deleted += 1
            except Exception:
                continue
            parent = target.parent
            while parent != audio_root:
                try:
                    next(parent.iterdir())
                    break
                except StopIteration:
                    try:
                        parent.rmdir()
                    except Exception:
                        break
                    parent = parent.parent
    return deleted


# --- имя для приветствия ---
def _display_name_for_request() -> str:
    first = (session.get("tg_first_name") or "").strip()
    if first: return first
    usern = (session.get("tg_username") or "").strip()
    if usern: return f"@{usern}"
    uid = request.headers.get("X-User-Id")
    if uid:
        with _conn() as c:
            row = c.execute(
                "SELECT first_name, username FROM users WHERE user_id=?",
                (str(uid),)
            ).fetchone()
        if row:
            first = (row["first_name"] or "").strip()
            if first: return first
            usern = (row["username"] or "").strip()
            if usern: return f"@{usern}"
    return ""


@web.get("/sw.js")
def service_worker():
    response = send_from_directory(current_app.static_folder, "sw.js")
    response.headers["Cache-Control"] = "no-cache"
    return response


# --- страницы ---
@web.route("/")
def home():
    admin_user_id = _request_user_id()
    return render_template(
        "index.html",
        title="Уроки",
        display_name=_display_name_for_request(),
        is_admin=_is_admin_user_id(admin_user_id),
        admin_user_id=admin_user_id,
        show_auth_gate=True,
    )


@web.route("/lessons")  # ←←← [ДОБАВЛЕНО v8.17] алиас, чтобы фронтовый фолбэк не падал 404
def lessons_alias():
    admin_user_id = _request_user_id()
    return render_template(
        "index.html",
        title="Уроки",
        display_name=_display_name_for_request(),
        is_admin=_is_admin_user_id(admin_user_id),
        admin_user_id=admin_user_id,
        show_auth_gate=True,
    )


@web.route("/lesson/<int:lesson_id>")
def lesson_page(lesson_id: int):
    return render_template("lesson.html", title=f"Урок {lesson_id}", lesson_id=lesson_id)


@web.route("/learn")
def learn_page():
    lesson_title = (request.args.get("lesson") or "").strip()
    return render_template(
        "learn.html",
        title="Обучение",
        lesson_title=lesson_title,
        display_name=_display_name_for_request(),
    )


@web.route("/difficult")
def difficult_page():
    return render_template("difficult.html", title="Сложные слова")


@web.route("/upload")
def upload_page():
    if request.args.get("tab") == "db":
        return redirect(url_for("web.word_database_page"))
    if request.args.get("tab") == "mcp":
        return redirect(url_for("web.mcp_connector_page", **{
            key: request.args[key] for key in ("google_link",) if key in request.args
        }))
    user_id = _session_user_id()
    access_pending = not user_id
    access_denied = bool(user_id and not _user_exists(user_id))
    return render_template(
        "upload.html",
        title="Загрузка слов",
        public_url=Config.PUBLIC_BASE_URL,
        hide_timer=True,
        is_admin=_is_admin_user_id(user_id),
        admin_user_id=user_id,
        upload_access_pending=access_pending,
        upload_access_denied=access_denied,
    )


@web.route("/word-database")
def word_database_page():
    return render_template(
        "word_database.html",
        title="База слов",
        hide_timer=True,
        show_auth_gate=True,
    )


@web.route("/settings/mcp")
def mcp_connector_page():
    return render_template(
        "mcp_connector.html",
        title="MCP-коннектор",
        hide_timer=True,
        show_auth_gate=True,
    )


@web.route("/settings")
def settings_page():
    return render_template(
        "settings.html",
        title="Настройки",
        hide_timer=True,
        language_options=LANGUAGE_OPTIONS,
    )


@web.route("/account-type")
def account_type_page():
    return render_template(
        "account_type.html",
        title="Account type",
        hide_timer=True,
    )


@web.get("/.well-known/assetlinks.json")
def android_app_links():
    return send_from_directory(Path(current_app.static_folder) / ".well-known", "assetlinks.json", mimetype="application/json")


@web.route("/family/connect")
@web.route("/family/link")
def family_link_page():
    code = str(request.args.get("code") or "").strip()
    if code or not request.args.get("token"):
        response = current_app.make_response(render_template("family_invite.html", title="Family", hide_timer=True, family_bot_username=Config.BOT_USERNAME or ""))
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response
    token = str(request.args.get("token") or "").strip()
    child_user_id = verify_pairing_token(token)
    child_name = ""
    if child_user_id:
        with _conn() as c:
            child = c.execute(
                "SELECT user_id, username, first_name, last_name, account_type "
                "FROM users WHERE user_id=?",
                (child_user_id,),
            ).fetchone()
        if not child or child["account_type"] != "child":
            child_user_id = ""
        else:
            child_name = _format_user_name(child) or child_user_id
    return render_template(
        "family_link.html",
        title="Link child account",
        hide_timer=True,
        pairing_token=token if child_user_id else "",
        child_name=child_name,
        pairing_valid=bool(child_user_id),
    )


@web.route("/parent")
def parent_dashboard_page():
    return render_template(
        "parent_dashboard.html",
        title=translate(_current_ui_language(), "parent.title"),
        hide_timer=True,
    )


@web.route("/subscription")
def subscription_page():
    return render_template("subscription.html", title="Подписка", hide_timer=True)


@web.route("/admin/users")
def admin_users_page():
    if not session.get("is_auth"):
        return render_template(
            "admin_users.html",
            title="Админка",
            hide_timer=True,
            access_pending=True,
            access_denied=False,
            users=[],
            admin_user_id="",
        )
    admin_user_id = _session_admin_user_id()
    if not admin_user_id:
        return render_template(
            "admin_users.html",
            title="Админка",
            hide_timer=True,
            access_pending=False,
            access_denied=True,
            users=[],
            admin_user_id=admin_user_id,
        ), 403

    _ensure_schema()
    _ensure_subscription_schema()
    _ensure_progress_schema()
    _ensure_family_schema()
    with _conn() as c:
        users = [dict(r) for r in c.execute("""
            SELECT user_id, username, first_name, last_name, is_active,
                   account_type, created_at
            FROM users
            ORDER BY datetime(created_at) DESC, user_id DESC
        """).fetchall()]
        word_counts = {
            str(r["user_id"]): int(r["cnt"] or 0)
            for r in c.execute("""
                SELECT user_id, COUNT(*) AS cnt
                FROM words
                WHERE COALESCE(user_id, '') != ''
                GROUP BY user_id
            """).fetchall()
        }
        lesson_counts = {
            str(r["user_id"]): int(r["cnt"] or 0)
            for r in c.execute("""
                SELECT user_id, COUNT(DISTINCT lesson) AS cnt
                FROM words
                WHERE COALESCE(user_id, '') != '' AND COALESCE(lesson, '') != ''
                GROUP BY user_id
            """).fetchall()
        }
        progress_last = {
            str(r["user_id"]): int(r["last_event_ts"] or 0)
            for r in c.execute("""
                SELECT user_id, MAX(event_ts) AS last_event_ts
                FROM progress_events
                WHERE COALESCE(user_id, '') != ''
                GROUP BY user_id
            """).fetchall()
        }
        subscriptions = {
            str(r["user_id"]): dict(r)
            for r in c.execute("""
                SELECT user_id, status, trial_started_at, trial_ends_at,
                       current_period_ends_at, provider, cancel_at_period_end
                FROM user_subscriptions
            """).fetchall()
        }
        family_links = [dict(r) for r in c.execute("""
            SELECT
                l.parent_user_id,
                l.child_user_id,
                l.created_at,
                p.username AS parent_username,
                p.first_name AS parent_first_name,
                p.last_name AS parent_last_name,
                ch.username AS child_username,
                ch.first_name AS child_first_name,
                ch.last_name AS child_last_name
            FROM parent_child_links l
            JOIN users p ON p.user_id = l.parent_user_id
            JOIN users ch ON ch.user_id = l.child_user_id
            ORDER BY l.created_at DESC
        """).fetchall()]
        tts_usage = get_tts_usage_snapshot(
            c,
            timezone_name=Config.TTS_USAGE_TIMEZONE,
        )
        translation_usage = get_translation_usage_snapshot(c)

    family_relations: Dict[str, List[Dict[str, Any]]] = {}
    for link in family_links:
        parent_id = str(link["parent_user_id"])
        child_id = str(link["child_user_id"])
        parent_name = _format_user_name({
            "username": link.get("parent_username"),
            "first_name": link.get("parent_first_name"),
            "last_name": link.get("parent_last_name"),
        }) or parent_id
        child_name = _format_user_name({
            "username": link.get("child_username"),
            "first_name": link.get("child_first_name"),
            "last_name": link.get("child_last_name"),
        }) or child_id
        common = {
            "parent_user_id": parent_id,
            "child_user_id": child_id,
            "created_at": link.get("created_at") or "",
        }
        family_relations.setdefault(parent_id, []).append({
            **common,
            "direction": "parent_of",
            "counterpart_name": child_name,
            "description": f"Взрослый {parent_name} → ребёнок {child_name}",
        })
        family_relations.setdefault(child_id, []).append({
            **common,
            "direction": "child_of",
            "counterpart_name": parent_name,
            "description": f"Взрослый {parent_name} → ребёнок {child_name}",
        })

    rows = []
    now_ms = int(time.time() * 1000)
    unlimited_threshold_ms = now_ms + 10 * 365 * 24 * 60 * 60 * 1000
    for u in users:
        uid = str(u.get("user_id") or "")
        is_admin_user = _is_admin_user_id(uid)
        sub = subscriptions.get(uid) or {}
        sub_status = sub.get("status") or "нет"
        raw_status = sub_status
        provider = sub.get("provider") or ""
        cancel_at_period_end = bool(sub.get("cancel_at_period_end") or 0)
        trial_started_at = int(sub.get("trial_started_at") or 0) if sub else 0
        trial_ends_at = int(sub.get("trial_ends_at") or 0) if sub else 0
        period_ends_at = int(sub.get("current_period_ends_at") or 0) if sub and sub.get("current_period_ends_at") else 0
        access_until = period_ends_at or trial_ends_at
        is_unlimited = bool(is_admin_user or (sub_status == "active" and period_ends_at and period_ends_at > unlimited_threshold_ms))
        if is_admin_user:
            sub_status = "Админ"
            provider = "env"
        elif is_unlimited:
            sub_status = "Безлимит"
        rows.append({
            **u,
            "display_name": _format_user_name(u) or "Без имени",
            "words_count": word_counts.get(uid, 0),
            "lessons_count": lesson_counts.get(uid, 0),
            "last_event_ts": progress_last.get(uid, 0),
            "subscription_status": sub_status,
            "subscription_raw_status": raw_status,
            "subscription_provider": provider,
            "cancel_at_period_end": cancel_at_period_end,
            "trial_started_at": trial_started_at,
            "trial_ends_at": trial_ends_at,
            "current_period_ends_at": period_ends_at,
            "access_until": access_until,
            "subscription_active": bool(is_unlimited or (access_until and access_until > now_ms)),
            "is_unlimited": is_unlimited,
            "is_admin": is_admin_user,
            "account_type": str(u.get("account_type") or "standard"),
            "account_type_label": "Детский" if u.get("account_type") == "child" else "Обычный",
            "family_relations": family_relations.get(uid, []),
            "tts_successful_requests": tts_usage["by_user"].get(uid, {}).get("successful_requests", 0),
            "tts_failed_requests": tts_usage["by_user"].get(uid, {}).get("failed_requests", 0),
            "tts_total_requests": tts_usage["by_user"].get(uid, {}).get("total_requests", 0),
            "tts_characters": tts_usage["by_user"].get(uid, {}).get("characters", 0),
            "tts_blocked_requests": tts_usage["by_user"].get(uid, {}).get("blocked_requests", 0),
            "tts_character_limit": tts_usage["by_user"].get(uid, {}).get("character_limit"),
            "tts_characters_remaining": tts_usage["by_user"].get(uid, {}).get("characters_remaining"),
            "translation_successful_requests": translation_usage["by_user"].get(uid, {}).get("successful_requests", 0),
            "translation_failed_requests": translation_usage["by_user"].get(uid, {}).get("failed_requests", 0),
            "translation_prompt_tokens": translation_usage["by_user"].get(uid, {}).get("prompt_tokens", 0),
            "translation_completion_tokens": translation_usage["by_user"].get(uid, {}).get("completion_tokens", 0),
            "translation_total_tokens": translation_usage["by_user"].get(uid, {}).get("total_tokens", 0),
        })

    return render_template(
        "admin_users.html",
        title="Пользователи",
        hide_timer=True,
        access_pending=False,
        access_denied=False,
        users=rows,
        admin_user_id=admin_user_id,
        tts_usage_summary=tts_usage,
        translation_usage_summary=translation_usage,
    )


@web.get("/share/<token>")
def share_page(token: str):
    _ensure_share_schema()
    now_ms = int(time.time() * 1000)
    with _conn() as c:
        row = c.execute("""
            SELECT s.token, s.title, s.lesson, s.payload, s.expires_at,
                   s.import_count, s.max_imports,
                   u.username, u.first_name, u.last_name
            FROM shared_word_sets s
            LEFT JOIN users u ON u.user_id = s.owner_user_id
            WHERE s.token = ?
        """, (token,)).fetchone()

    if not row:
        return render_template("share.html", title="Общий урок", hide_timer=True, share=None, error="Ссылка не найдена")
    if row["expires_at"] and int(row["expires_at"]) < now_ms:
        return render_template("share.html", title="Общий урок", hide_timer=True, share=None, error="Срок действия ссылки истек")
    if row["max_imports"] is not None and int(row["import_count"] or 0) >= int(row["max_imports"]):
        return render_template("share.html", title="Общий урок", hide_timer=True, share=None, error="Лимит импортов исчерпан")

    try:
        payload = json.loads(row["payload"] or "{}")
    except Exception:
        payload = {}
    shared_lessons = []
    if isinstance(payload, dict) and isinstance(payload.get("lessons"), list):
        for item in payload.get("lessons") or []:
            if not isinstance(item, dict):
                continue
            lesson_words = item.get("words") if isinstance(item.get("words"), list) else []
            shared_lessons.append({
                "lesson": item.get("lesson") or row["lesson"] or row["title"],
                "words": lesson_words,
                "words_count": len(lesson_words),
                "preview": lesson_words,
            })
    else:
        words = payload.get("words") if isinstance(payload, dict) else []
        words = words if isinstance(words, list) else []
        shared_lessons.append({
            "lesson": row["lesson"] or row["title"],
            "words": words,
            "words_count": len(words),
            "preview": words,
        })
    total_words = sum(int(item.get("words_count") or 0) for item in shared_lessons)

    owner_name = (row["first_name"] or "").strip()
    if not owner_name and (row["username"] or "").strip():
        owner_name = "@" + (row["username"] or "").strip()

    return render_template("share.html", title="Общий урок", hide_timer=True, share={
        "token": row["token"],
        "title": row["title"],
        "lesson": row["lesson"],
        "lessons_count": len(shared_lessons),
        "words_count": total_words,
        "owner_name": owner_name,
        "lessons": shared_lessons,
        "preview": shared_lessons[0]["preview"] if shared_lessons else [],
    }, error="")


@web.post("/api/share/create")
def api_share_create():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _ensure_schema()
    _ensure_share_schema()

    data = request.get_json(silent=True) or {}
    raw_lessons = data.get("lessons")
    if raw_lessons is None:
        raw_lessons = [data.get("lesson")]
    if isinstance(raw_lessons, str):
        raw_lessons = [raw_lessons]
    if not isinstance(raw_lessons, list):
        return jsonify({"ok": False, "error": "lessons_required"}), 400

    lessons: List[str] = []
    seen = set()
    for item in raw_lessons:
        lesson = str(item or "").strip()
        if not lesson or lesson in seen:
            continue
        lessons.append(lesson)
        seen.add(lesson)
    if not lessons:
        return jsonify({"ok": False, "error": "lessons_required"}), 400

    with _conn() as c:
        qmarks = ",".join("?" * len(lessons))
        rows = c.execute(f"""
            SELECT lesson, number, nl, en, ru, ex_nl, ex_en, ex_ru
            FROM words
            WHERE (user_id = ? OR status = 'test') AND lesson IN ({qmarks})
            ORDER BY lesson, number
        """, [str(user_id)] + lessons).fetchall()
        if not rows:
            return jsonify({"ok": False, "error": "lessons_not_found"}), 404

        grouped: Dict[str, List[Dict[str, Any]]] = {lesson: [] for lesson in lessons}
        for r in rows:
            grouped.setdefault(r["lesson"], []).append(dict(r))
        shared_lessons = [
            {"lesson": lesson, "words": grouped.get(lesson, [])}
            for lesson in lessons
            if grouped.get(lesson)
        ]
        if not shared_lessons:
            return jsonify({"ok": False, "error": "lessons_not_found"}), 404

        total_words = sum(len(item["words"]) for item in shared_lessons)
        requested_title = str(data.get("title") or "").strip()
        title = requested_title or (
            shared_lessons[0]["lesson"] if len(shared_lessons) == 1 else f"Набор из {len(shared_lessons)} уроков"
        )
        lesson_value = shared_lessons[0]["lesson"] if len(shared_lessons) == 1 else ""
        payload = json.dumps({"lessons": shared_lessons}, ensure_ascii=False)
        now_ms = int(time.time() * 1000)
        token = secrets.token_urlsafe(18)
        while c.execute("SELECT 1 FROM shared_word_sets WHERE token = ?", (token,)).fetchone():
            token = secrets.token_urlsafe(18)

        c.execute("""
            INSERT INTO shared_word_sets (
                token, owner_user_id, title, lesson, payload, created_at, expires_at, max_imports
            ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)
        """, (token, str(user_id), title, lesson_value, payload, now_ms))
        c.commit()

    return jsonify({
        "ok": True,
        "token": token,
        "url": _public_url(f"share/{token}"),
        "lessons": [item["lesson"] for item in shared_lessons],
        "lessons_count": len(shared_lessons),
        "words_count": total_words,
    })


@web.get("/api/share/source_lessons")
def api_share_source_lessons():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _ensure_schema()

    _ensure_family_schema()
    preferred_languages = [item["code"] for item in _get_user_languages(str(user_id))]
    with _conn() as c:
        languages = _existing_word_languages(c)
        languages = [
            *[code for code in preferred_languages if code in languages],
            *[code for code in languages if code not in preferred_languages],
        ]
        visible_languages = preferred_languages or languages
        language_columns = []
        for lang in languages:
            language_columns.extend([_word_text_col(lang), _word_sentence_col(lang)])
        word_columns = ", ".join(f'"{column}"' for column in language_columns)
        select_languages = f", {word_columns}" if word_columns else ""
        rows = c.execute(f"""
            SELECT id, user_id, lesson, number{select_languages}
            FROM words
            WHERE (user_id = ? OR status = 'test') AND COALESCE(lesson, '') != ''
            ORDER BY lesson, number
        """, (str(user_id),)).fetchall()

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    upload_order: Dict[str, int] = {}
    editable_lessons: Dict[str, bool] = {}
    for r in rows:
        word = {"id": r["id"], "number": r["number"] or ""}
        for lang in languages:
            word[lang] = r[_word_text_col(lang)] or ""
            word[f"ex_{lang}"] = r[_word_sentence_col(lang)] or ""
        grouped.setdefault(r["lesson"], []).append(word)
        upload_order[r["lesson"]] = max(upload_order.get(r["lesson"], 0), int(r["id"] or 0))
        editable_lessons[r["lesson"]] = (
            editable_lessons.get(r["lesson"], False)
            or str(r["user_id"] or "") == str(user_id)
        )

    lessons = [
        {
            "lesson": lesson,
            "upload_order": upload_order.get(lesson, 0),
            "editable_name": editable_lessons.get(lesson, False),
            "words_count": len(words),
            "words": words,
            "languages": [
                {
                    "code": lang,
                    "name": LANGUAGE_META.get(lang, {}).get("name", lang.upper()),
                    "native": LANGUAGE_META.get(lang, {}).get("native", lang.upper()),
                }
                for lang in visible_languages
                if any(str(word.get(lang) or "").strip() for word in words)
            ],
        }
        for lesson, words in grouped.items()
    ]
    lessons.sort(key=lambda item: (-int(item.get("upload_order") or 0), item["lesson"] or ""))
    if request.headers.get("X-Client") == "android":
        return jsonify(lessons)
    children = _family_status(str(user_id)).get("children", [])
    for child in children:
        child["languages"] = _get_user_languages(str(child.get("user_id") or ""))
    return jsonify({
        "ok": True,
        "lessons": lessons,
        "children": children,
        "language_options": LANGUAGE_OPTIONS,
        "preferred_languages": _get_user_languages(str(user_id)),
    })


@web.post("/api/share/assign_child")
def api_share_assign_child():
    parent_user_id = _current_user_id()
    if not parent_user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _ensure_schema()
    _ensure_family_schema()

    data = request.get_json(silent=True) or {}
    child_user_id = str(data.get("child_user_id") or "").strip()
    raw_lessons = data.get("lessons") or []
    if isinstance(raw_lessons, str):
        raw_lessons = [raw_lessons]
    lessons = list(dict.fromkeys(
        str(item or "").strip() for item in raw_lessons if str(item or "").strip()
    )) if isinstance(raw_lessons, list) else []
    if not child_user_id:
        return jsonify({"ok": False, "error": "child_required"}), 400
    if not lessons:
        return jsonify({"ok": False, "error": "lessons_required"}), 400

    with _conn() as c:
        linked_child = c.execute("""
            SELECT u.user_id
            FROM parent_child_links l
            JOIN users u ON u.user_id = l.child_user_id
            WHERE l.parent_user_id = ? AND l.child_user_id = ? AND u.account_type = 'child'
        """, (str(parent_user_id), child_user_id)).fetchone()
        if not linked_child:
            return jsonify({"ok": False, "error": "child_not_linked"}), 403

        columns = {row["name"] for row in c.execute("PRAGMA table_info(words)")}
        copy_columns = ["lesson", "number", "difficult"]
        for lang in _existing_word_languages(c):
            copy_columns.extend([
                _word_text_col(lang), _word_sentence_col(lang), _word_audio_col(lang)
            ])
        copy_columns = [column for column in copy_columns if column in columns]
        qmarks = ",".join("?" * len(lessons))
        quoted = ", ".join(f'"{column}"' for column in copy_columns)
        source_rows = c.execute(f"""
            SELECT id AS source_word_id, user_id AS source_owner, {quoted}
            FROM words
            WHERE (user_id = ? OR status = 'test') AND lesson IN ({qmarks})
            ORDER BY lesson, number, id
        """, [str(parent_user_id), *lessons]).fetchall()
        if not source_rows:
            return jsonify({"ok": False, "error": "lessons_not_found"}), 404

        old_shared_rows = c.execute(f"""
            SELECT child_word_id
            FROM shared_lesson_words
            WHERE parent_user_id=? AND child_user_id=? AND lesson IN ({qmarks})
        """, [str(parent_user_id), child_user_id, *lessons]).fetchall()
        old_child_ids = [int(row["child_word_id"]) for row in old_shared_rows]
        if old_child_ids:
            old_qmarks = ",".join("?" * len(old_child_ids))
            c.execute(
                f"DELETE FROM words WHERE user_id=? AND id IN ({old_qmarks})",
                [child_user_id, *old_child_ids],
            )
        c.execute(f"""
            DELETE FROM shared_lesson_words
            WHERE parent_user_id=? AND child_user_id=? AND lesson IN ({qmarks})
        """, [str(parent_user_id), child_user_id, *lessons])

        max_row = c.execute("""
            SELECT MAX(CAST(SUBSTR(number, 1,
                CASE WHEN INSTR(number, '.') > 0 THEN INSTR(number, '.') - 1
                     ELSE LENGTH(number) END) AS INTEGER))
            FROM words WHERE user_id = ?
        """, (child_user_id,)).fetchone()
        next_lesson_num = int(max_row[0] or 0) + 1
        lesson_numbers = {lesson: next_lesson_num + index for index, lesson in enumerate(lessons)}
        per_lesson_index: Dict[str, int] = {}
        insert_columns = ["user_id", "status", *copy_columns]
        if "updated_at" in columns:
            insert_columns.append("updated_at")
        insert_sql = (
            f"INSERT INTO words ({', '.join(insert_columns)}) "
            f"VALUES ({','.join('?' * len(insert_columns))})"
        )
        now_ms = int(time.time() * 1000)
        inserted = 0
        assigned_lessons = set()
        for source in source_rows:
            lesson = str(source["lesson"] or "").strip()
            if lesson not in lesson_numbers:
                continue
            per_lesson_index[lesson] = per_lesson_index.get(lesson, 0) + 1
            values: List[Any] = [child_user_id, "user"]
            for column in copy_columns:
                if column == "number":
                    values.append(f"{lesson_numbers[lesson]}.{per_lesson_index[lesson]}")
                else:
                    values.append(source[column])
            if "updated_at" in columns:
                values.append(now_ms)
            cursor = c.execute(insert_sql, values)
            child_word_id = int(cursor.lastrowid)
            if str(source["source_owner"] or "") == str(parent_user_id):
                c.execute("""
                    INSERT INTO shared_lesson_words (
                        parent_user_id, child_user_id, lesson,
                        parent_word_id, child_word_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(parent_user_id), child_user_id, lesson,
                    int(source["source_word_id"]), child_word_id, now_ms,
                ))
            inserted += 1
            assigned_lessons.add(lesson)
        c.commit()

    return jsonify({
        "ok": True,
        "count": inserted,
        "lessons_count": len(assigned_lessons),
        "lessons": sorted(assigned_lessons),
        "child_user_id": child_user_id,
    })


@web.post("/api/share/<token>/import")
def api_share_import(token: str):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _ensure_schema()
    _ensure_share_schema()

    now_ms = int(time.time() * 1000)
    with _conn() as c:
        row = c.execute("""
            SELECT id, title, lesson, payload, expires_at, import_count, max_imports
            FROM shared_word_sets
            WHERE token = ?
        """, (token,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "share_not_found"}), 404
        if row["expires_at"] and int(row["expires_at"]) < now_ms:
            return jsonify({"ok": False, "error": "share_expired"}), 410
        if row["max_imports"] is not None and int(row["import_count"] or 0) >= int(row["max_imports"]):
            return jsonify({"ok": False, "error": "share_limit_reached"}), 410

        try:
            payload = json.loads(row["payload"] or "{}")
        except Exception:
            return jsonify({"ok": False, "error": "bad_share_payload"}), 500

        if isinstance(payload, dict) and isinstance(payload.get("lessons"), list):
            payload_lessons = []
            for item in payload.get("lessons") or []:
                if not isinstance(item, dict):
                    continue
                lesson_words = item.get("words") if isinstance(item.get("words"), list) else []
                if lesson_words:
                    payload_lessons.append({
                        "lesson": (item.get("lesson") or row["title"] or "Shared lesson").strip(),
                        "words": lesson_words,
                    })
        else:
            words = payload.get("words") if isinstance(payload, dict) else []
            payload_lessons = [{
                "lesson": (row["lesson"] or row["title"] or payload.get("lesson") or "Shared lesson").strip(),
                "words": words if isinstance(words, list) else [],
            }]

        if not payload_lessons:
            return jsonify({"ok": False, "error": "empty_share"}), 400

        next_row = c.execute("""
            SELECT MAX(CAST(SUBSTR(number, 1,
                CASE WHEN INSTR(number,'.') > 0
                     THEN INSTR(number,'.') - 1
                     ELSE LENGTH(number) END
               ) AS INTEGER))
            FROM words
            WHERE user_id = ?
        """, (str(user_id),)).fetchone()
        next_lesson_num = (next_row[0] or 0) + 1

    rows: List[Dict[str, Any]] = []
    imported_lessons: List[str] = []
    lesson_num = next_lesson_num
    for lesson_item in payload_lessons:
        lesson = (lesson_item.get("lesson") or "Shared lesson").strip()
        words = lesson_item.get("words") or []
        added_for_lesson = 0
        for idx, w in enumerate(words, start=1):
            if not isinstance(w, dict):
                continue
            nl = (w.get("nl") or "").strip()
            en = (w.get("en") or "").strip()
            if not nl and not en:
                continue
            rows.append({
                "lesson": lesson,
                "number": f"{lesson_num}.{idx}",
                "nl": nl,
                "en": en,
                "ru": (w.get("ru") or "").strip(),
                "ex_nl": (w.get("ex_nl") or "").strip(),
                "ex_en": (w.get("ex_en") or "").strip(),
                "ex_ru": (w.get("ex_ru") or "").strip(),
                "audio_nl": "",
                "audio_en": "",
                "audio_ru": "",
            })
            added_for_lesson += 1
        if added_for_lesson:
            imported_lessons.append(lesson)
            lesson_num += 1

    if not rows:
        return jsonify({"ok": False, "error": "empty_share"}), 400

    from bot.db import bulk_upsert_words
    count = bulk_upsert_words(Config.DB_PATH, user_id, rows)

    with _conn() as c:
        c.execute("UPDATE shared_word_sets SET import_count = import_count + 1 WHERE token = ?", (token,))
        c.commit()

    return jsonify({"ok": True, "count": count, "lessons": imported_lessons, "lessons_count": len(imported_lessons)})


@web.post("/api/import-words")
def api_import_words():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok":False,"error":"Not authenticated"}),401
    data = request.get_json(silent=True) or {}
    lessons = data.get("lessons")
    if lessons is None and data.get("lesson"):
        lessons = [{"lesson":data["lesson"],"words":data.get("words",[])}]
    from app.content_service import import_words
    try:
        result = import_words(Config.DB_PATH,user_id,lessons,source="app",idempotency_key=data.get("idempotency_key"))
    except ValueError as exc:
        return jsonify({"ok":False,"error":str(exc)}),(409 if str(exc)=="idempotency_conflict" else 400)
    return jsonify(result)


@web.get("/api/words")
def api_get_words():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    q        = request.args.get("q", "").strip()
    page     = max(1, int(request.args.get("page", 1) or 1))
    per_page = min(100, max(10, int(request.args.get("per_page", 50) or 50)))
    offset   = (page - 1) * per_page
    preferred = _get_user_languages(str(user_id))
    display_languages = [item["code"] for item in preferred] or ["nl", "en", "ru"]
    with _conn() as c:
        _ensure_word_language_columns(c, display_languages)
        c.commit()
        existing_languages = _existing_word_languages(c)
        select_languages = list(dict.fromkeys(["nl", "en", "ru", *display_languages]))
        select_languages = [code for code in select_languages if code in existing_languages]
        include_test = request.headers.get("X-Client") == "android"
        if include_test:
            base = "FROM words WHERE (user_id=? OR status='test')"
        else:
            base = "FROM words WHERE user_id=?"
        params: list = [str(user_id)]
        if q:
            search_columns = [*[_word_text_col(code) for code in display_languages], "lesson"]
            base += " AND (" + " OR ".join(f'"{column}" LIKE ?' for column in search_columns) + ")"
            p      = f"%{q}%"
            params += [p] * len(search_columns)
        total = c.execute(f"SELECT COUNT(*) {base}", params).fetchone()[0]
        word_columns = []
        for code in select_languages:
            word_columns.extend([
                _word_text_col(code),
                _word_sentence_col(code),
                _word_audio_col(code),
            ])
        columns = {row["name"] for row in c.execute("PRAGMA table_info(words)")}
        word_columns += [name for name in ("content_sense","content_context","example_level") if name in columns]
        selected_word_columns = ",".join(f'"{column}"' for column in word_columns)
        rows  = c.execute(
            f"SELECT id,lesson,number,{selected_word_columns},difficult,status,user_id "
            f"{base} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()
    words = []
    for r in rows:
        d = dict(r)
        d["difficult"] = bool(d.get("difficult"))
        d["editable"] = (d.get("user_id") or "") == str(user_id) or d.get("status") == "test"
        d.pop("user_id", None)
        words.append(d)
    display_meta = [
        LANGUAGE_META.get(code, {"code": code, "name": code.upper(), "native": code.upper()})
        for code in display_languages
    ]
    return jsonify({"ok": True, "words": words, "languages": display_meta,
                    "total": total, "page": page,
                    "pages": max(1, (total + per_page - 1) // per_page)})


@web.put("/api/words/<int:word_id>")
def api_update_word(word_id: int):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    _ensure_family_schema()
    from app.content_db import transaction
    from app.content_service import ensure_schema
    with transaction(Config.DB_PATH) as conn:
        ensure_schema(conn)
    data    = request.get_json(silent=True) or {}
    for alias, column in (("sense","content_sense"),("context","content_context"),("level","example_level")):
        if alias in data:
            data[column]=data.pop(alias)
    payload_langs = set()
    for key in data:
        raw = str(key or "").strip().lower()
        if raw in LANGUAGE_CODES:
            payload_langs.add(raw)
        elif raw.startswith("ex_") and raw[3:] in LANGUAGE_CODES:
            payload_langs.add(raw[3:])
        elif raw.startswith("audio_") and raw[6:] in LANGUAGE_CODES:
            payload_langs.add(raw[6:])

    with _conn() as c:
        _ensure_word_language_columns(c, payload_langs)
        c.commit()

    with _conn() as c:
        languages = _existing_word_languages(c)

    dynamic_allowed = set()
    for lang in languages:
        dynamic_allowed.update({_word_text_col(lang), _word_sentence_col(lang), _word_audio_col(lang)})
    allowed = {"lesson", "number", "difficult", "content_sense", "content_context", "example_level"} | dynamic_allowed
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({"ok": False, "error": "No valid fields"}), 400

    # When a translated text field changes, clear its audio URL and delete the old file
    TEXT_AUDIO_MAP = {_word_text_col(lang): _word_audio_col(lang) for lang in languages}
    old_audio_urls: List[str] = []

    with _conn() as c:
        old_select_cols = ", ".join(dict.fromkeys([*TEXT_AUDIO_MAP.keys(), *TEXT_AUDIO_MAP.values()]))
        old = c.execute(
            f"""
            SELECT {old_select_cols}
            FROM words
            WHERE id=? AND (user_id=? OR status='test')
            """,
            (word_id, str(user_id))
        ).fetchone()
        if not old:
            return jsonify({"ok": False, "error": "Not found or not authorized"}), 404

        canonical_rows = c.execute("""
            SELECT DISTINCT parent_word_id
            FROM shared_lesson_words
            WHERE parent_word_id=? OR child_word_id=?
        """, (word_id, word_id)).fetchall()
        canonical_ids = [int(row["parent_word_id"]) for row in canonical_rows]
        shared_word_ids = {word_id}
        if canonical_ids:
            canonical_qmarks = ",".join("?" * len(canonical_ids))
            mapped_rows = c.execute(f"""
                SELECT parent_word_id, child_word_id
                FROM shared_lesson_words
                WHERE parent_word_id IN ({canonical_qmarks})
            """, canonical_ids).fetchall()
            for mapped in mapped_rows:
                shared_word_ids.add(int(mapped["parent_word_id"]))
                shared_word_ids.add(int(mapped["child_word_id"]))

        target_qmarks = ",".join("?" * len(shared_word_ids))
        target_rows = c.execute(
            f"SELECT id, {old_select_cols} FROM words WHERE id IN ({target_qmarks})",
            list(shared_word_ids),
        ).fetchall()
        from app.content_service import prepare_edit
        updates = prepare_edit(dict(old),updates)
        for text_col, audio_col in TEXT_AUDIO_MAP.items():
            if text_col in updates:
                old_val = (old[text_col] or "").strip()
                new_val = str(updates[text_col] or "").strip()
                if old_val != new_val:
                    for target in target_rows:
                        old_url = (target[audio_col] or "").strip()
                        if old_url:
                            old_audio_urls.append(old_url)
                    updates[audio_col] = ""

        updates["updated_at"] = int(time.time() * 1000)
        set_clause = ", ".join(f"{k}=?" for k in updates)
        c.execute(
            f"UPDATE words SET {set_clause} WHERE id=? AND (user_id=? OR status='test')",
            list(updates.values()) + [word_id, str(user_id)]
        )
        shared_updates = {
            key: value for key, value in updates.items()
            if key in dynamic_allowed or key == "updated_at"
        }
        if canonical_ids and shared_updates:
            shared_set_clause = ", ".join(f"{key}=?" for key in shared_updates)
            c.execute(
                f"UPDATE words SET {shared_set_clause} WHERE id IN ({target_qmarks})",
                [*shared_updates.values(), *shared_word_ids],
            )
        c.commit()

        select_cols = ",\n                   ".join(_language_select_parts(languages))
        row = c.execute(f"""
            SELECT w.id, w.lesson, w.number,
                   {select_cols},
                   COALESCE(uf.difficult, 0) AS difficult,
                   w.status AS status,
                   w.user_id AS _word_owner
            FROM words w
            LEFT JOIN user_word_flags uf ON uf.word_id = w.id AND uf.user_id = ?
            WHERE w.id = ?
        """, (str(user_id), word_id)).fetchone()

    from app.content_service import remember_word_ids
    remember_word_ids(Config.DB_PATH,list(shared_word_ids))
    if old_audio_urls:
        _cleanup_audio_files(old_audio_urls)

    if not row:
        return jsonify({"ok": True})

    d = _word_payload_from_row(row, languages, str(user_id))
    return jsonify({"ok": True, "word": d})


@web.delete("/api/words/<int:word_id>")
def api_delete_word(word_id: int):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    with _conn() as c:
        c.execute("DELETE FROM user_word_flags WHERE user_id=? AND word_id=?",
                  (str(user_id), word_id))
        c.execute("DELETE FROM words WHERE id=? AND user_id=?",
                  (word_id, str(user_id)))
        c.commit()
    return jsonify({"ok": True})


@web.get("/api/words/nl-list")
def api_words_nl_list():
    """Lightweight list of all NL words for the current user (used for deduplication)."""
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    with _conn() as c:
        rows = c.execute(
            "SELECT LOWER(TRIM(nl)) AS nl FROM words WHERE user_id=? AND TRIM(nl) != '' ORDER BY nl",
            (str(user_id),)
        ).fetchall()
    return jsonify({"ok": True, "words": [r["nl"] for r in rows]})


@web.get("/api/words/duplicates")
def api_words_duplicates():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    _ensure_schema()
    with _conn() as c:
        keys = c.execute("""
            SELECT LOWER(TRIM(nl)) AS key, COUNT(*) AS count
            FROM words
            WHERE user_id = ? AND TRIM(COALESCE(nl, '')) != ''
            GROUP BY LOWER(TRIM(nl))
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC, key
        """, (str(user_id),)).fetchall()

        groups = []
        for k in keys:
            rows = c.execute("""
                SELECT id, lesson, number, nl, en, ru, ex_nl, ex_en, ex_ru
                FROM words
                WHERE user_id = ? AND LOWER(TRIM(nl)) = ?
                ORDER BY lesson, number, id
            """, (str(user_id), k["key"])).fetchall()
            groups.append({
                "key": k["key"],
                "count": int(k["count"] or 0),
                "items": [dict(r) for r in rows],
            })

    return jsonify({
        "ok": True,
        "groups": groups,
        "groups_count": len(groups),
        "duplicates_count": sum(max(0, int(g["count"]) - 1) for g in groups),
    })


@web.post("/api/parse-file")
def api_parse_file():
    """Parse uploaded CSV or Excel file, return rows as JSON for preview."""
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401

    f = request.files.get("file")
    if not f:
        return jsonify({"ok": False, "error": "No file uploaded"}), 400

    fname = (f.filename or "").lower()
    import tempfile, os
    suffix = ".xlsx" if fname.endswith((".xlsx", ".xls")) else ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name

    try:
        if suffix == ".csv":
            from bot.validators import parse_csv_to_rows
            rows = parse_csv_to_rows(tmp_path)
        else:
            rows = _parse_excel_to_rows(tmp_path)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    finally:
        try: os.unlink(tmp_path)
        except Exception: pass

    return jsonify({"ok": True, "rows": rows, "count": len(rows)})


def _parse_excel_to_rows(path: str) -> List[Dict]:
    """Read xlsx/xls and produce the same row dicts as parse_csv_to_rows."""
    import openpyxl
    from bot.validators import normalize_header, split_number_and_lesson, REQUIRED_KEYS_MIN

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    rows_raw = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows_raw:
        raise ValueError("Файл пустой.")

    raw_headers = [str(c or "").strip() for c in rows_raw[0]]
    headers = [normalize_header(h) for h in raw_headers]
    seen = ", ".join(headers)

    result: List[Dict] = []
    last_lesson = ""

    for lineno, row in enumerate(rows_raw[1:], start=2):
        cells = [str(c or "").strip() for c in row]
        if not any(cells):
            continue

        rec_raw = {headers[i]: (cells[i] if i < len(cells) else "") for i in range(len(headers))}

        number_val = rec_raw.get("number", "")
        lesson_val = rec_raw.get("lesson", "")

        if number_val and not lesson_val:
            n_split, l_split = split_number_and_lesson(number_val)
            if l_split:
                number_val, lesson_val = n_split, l_split

        if not lesson_val:
            lesson_val = last_lesson

        missing = [k for k in REQUIRED_KEYS_MIN if not (rec_raw.get(k) or (k == "number" and number_val))]
        if missing:
            raise ValueError(f"Строка {lineno}: отсутствуют поля ({', '.join(missing)}). Заголовки: {seen}")

        if lesson_val:
            last_lesson = lesson_val

        result.append({
            "lesson":   lesson_val,
            "number":   number_val or rec_raw.get("number", ""),
            "nl":       rec_raw.get("nl", ""),
            "en":       rec_raw.get("en", ""),
            "ru":       rec_raw.get("ru", ""),
            "ex_nl":    rec_raw.get("ex_nl", ""),
            "ex_en":    rec_raw.get("ex_en", ""),
            "ex_ru":    rec_raw.get("ex_ru", ""),
            "audio_nl": rec_raw.get("audio_nl", ""),
            "audio_en": rec_raw.get("audio_en", ""),
            "audio_ru": rec_raw.get("audio_ru", ""),
        })

    if not result:
        raise ValueError(f"Ни одной строки с данными. Заголовки: {seen}")

    return result


# --- API: Android авторизация ---
@web.post("/api/auth/login_android")
def login_android():
    data = request.get_json(silent=True) or {}
    user_id = str(data.get("user_id", "")).strip()
    if not user_id:
        return jsonify({"ok": False, "error": "user_id required"}), 400
    if not _user_exists(user_id):
        return jsonify({"ok": False, "error": "open_telegram_bot_first"}), 403
    return jsonify({"ok": True, "user_id": user_id, "token": create_auth_token(user_id)})


@web.post("/api/auth/login_android_token")
def login_android_token():
    data = request.get_json(silent=True) or {}
    token = str(data.get("auth", "")).strip()
    user_id = verify_auth_token(token)
    if not user_id:
        return jsonify({"ok": False, "error": "invalid_auth_token"}), 401
    if not _user_exists(user_id):
        return jsonify({"ok": False, "error": "open_telegram_bot_first"}), 403
    return jsonify({"ok": True, "user_id": user_id, "token": token})


@web.post("/api/auth/login_link")
def login_link():
    data = request.get_json(silent=True) or {}
    user_id = verify_auth_token(str(data.get("auth", "")).strip())
    if not user_id:
        return jsonify({"ok": False, "error": "invalid_auth_token"}), 401
    if not _user_exists(user_id):
        return jsonify({"ok": False, "error": "open_telegram_bot_first"}), 403
    _load_user_to_session(user_id)
    return jsonify({"ok": True})


@web.get("/android-auth")
def android_auth_redirect():
    token = str(request.args.get("token", "")).strip()
    if not verify_auth_token(token):
        return jsonify({"ok": False, "error": "invalid_auth_token"}), 401
    base = f"{Config.PUBLIC_BASE_URL}".rstrip("/")
    deep_link = "learnwords://auth?" + urlencode({"server": base, "auth": token})
    return redirect(deep_link)


# --- API: авторизация WebApp ---
# Плоское "/auth/telegram" (браузерный OAuth-логин) теперь обслуживает
# app/telegram_oauth.py — см. регистрацию в init_app() ниже.
@web.post("/api/auth/login_webapp")
def login_webapp():
    data = request.get_json(silent=True) or {}
    init_data = data.get("init_data", "")
    v = verify_telegram_init_data(init_data, Config.BOT_TOKEN)
    if not v or not isinstance(v.get("user"), dict):
        return jsonify({"ok": False, "error": "invalid_init_data"}), 401
    user = v["user"]
    if not _has_telegram_identity(user):
        return jsonify({"ok": False, "error": "telegram_name_or_username_required"}), 403
    if _upsert_user(user):
        _notify_admins_new_user(user)
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO auth_identities (provider, external_id, user_id) VALUES ('telegram', ?, ?)",
            (str(user.get("id") or ""), str(user.get("id") or "")),
        )
        c.commit()
    _update_detected_ui_language(str(user.get("id") or ""), user.get("language_code"))
    session["tg_user_id"]    = str(user.get("id") or "")
    session["tg_username"]   = user.get("username") or ""
    session["tg_first_name"] = user.get("first_name") or ""
    session["tg_last_name"]  = user.get("last_name") or ""
    session["is_auth"]       = True
    return jsonify({"ok": True, "user": {
        "id": session["tg_user_id"],
        "username": session["tg_username"],
        "first_name": session["tg_first_name"],
        "last_name": session["tg_last_name"]
    }})


@web.get("/api/me")
def api_me():
    if session.get("is_auth"):
        uid = str(session.get("tg_user_id") or "")
        language_preferences = _get_user_languages(uid)
        subscription = _get_subscription(uid)
        return jsonify({
            "ok": True, "auth": True,
            "user_id": uid,
            "username": session.get("tg_username"),
            "first_name": session.get("tg_first_name") or "",
            "last_name": session.get("tg_last_name") or "",
            "languages_configured": 3 <= len(language_preferences) <= 5,
            "language_preferences": language_preferences,
            "subscription": subscription,
            "is_admin": _is_admin_user_id(uid),
            **_account_context(uid),
            **_get_ui_language(uid),
        })
    uid = _bearer_user_id() or (request.headers.get("X-User-Id") if Config.ALLOW_LEGACY_UID_AUTH else None)
    if uid:
        language_preferences = _get_user_languages(str(uid))
        subscription = _get_subscription(str(uid))
        with _conn() as c:
            row = c.execute("SELECT username, first_name, last_name FROM users WHERE user_id=?",
                            (str(uid),)).fetchone()
        if row:
            return jsonify({
                "ok": True, "auth": True,
                "user_id": str(uid),
                "username": row["username"] or "",
                "first_name": row["first_name"] or "",
                "last_name": row["last_name"] or "",
                "languages_configured": 3 <= len(language_preferences) <= 5,
                "language_preferences": language_preferences,
                "subscription": subscription,
                "is_admin": _is_admin_user_id(uid),
                **_account_context(str(uid)),
                **_get_ui_language(str(uid)),
            })
        return jsonify({"ok": False, "auth": False, "error": "open_telegram_bot_first"}), 401
    return jsonify({"ok": False, "auth": False})


@web.post("/api/account/type")
def api_account_type_save():
    user_id = _current_user_id()
    if not user_id or not _user_exists(user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    data = request.get_json(silent=True) or {}
    account_type = str(data.get("account_type") or "").strip().lower()
    if account_type not in {"child", "standard"}:
        return jsonify({"ok": False, "error": "invalid_account_type"}), 400
    _ensure_family_schema()
    with _conn() as c:
        row = c.execute(
            "SELECT account_type FROM users WHERE user_id=?",
            (str(user_id),),
        ).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "user_not_found"}), 404
        current_type = str(row["account_type"] or "standard")
        if current_type not in {"pending", account_type}:
            return jsonify({"ok": False, "error": "account_type_locked"}), 409
        c.execute(
            "UPDATE users SET account_type=? WHERE user_id=?",
            (account_type, str(user_id)),
        )
        c.commit()
    return jsonify({"ok": True, **_account_context(str(user_id))})


@web.get("/api/family")
def api_family_status():
    user_id = _current_user_id()
    if not user_id or not _user_exists(user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    return jsonify({"ok": True, **_family_status(str(user_id))})


@web.get("/api/learning/streak")
def api_learning_streak():
    user_id = _current_user_id()
    if not user_id or not _user_exists(user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    try:
        timezone_offset_minutes = int(request.args.get("tz_offset") or 0)
    except (TypeError, ValueError):
        timezone_offset_minutes = 0
    timezone_offset_minutes = max(-14 * 60, min(14 * 60, timezone_offset_minutes))
    streak = _learning_streaks([str(user_id)], timezone_offset_minutes)
    return jsonify({
        "ok": True,
        "learning_streak_days": streak.get(str(user_id), 0),
        "timezone_offset_minutes": timezone_offset_minutes,
    })


@web.get("/api/family/dashboard")
def api_family_dashboard():
    user_id = _current_user_id()
    if not user_id or not _user_exists(user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    account = _account_context(str(user_id))
    if not account["is_parent"]:
        return jsonify({"ok": False, "error": "parent_account_required"}), 403
    _ensure_schema()
    try:
        days = int(request.args.get("days") or 30)
    except (TypeError, ValueError):
        days = 30
    if days not in {7, 30, 90}:
        return jsonify({"ok": False, "error": "invalid_period"}), 400
    try:
        timezone_offset_minutes = int(request.args.get("tz_offset") or 0)
    except (TypeError, ValueError):
        timezone_offset_minutes = 0
    timezone_offset_minutes = max(-14 * 60, min(14 * 60, timezone_offset_minutes))
    return jsonify({
        "ok": True,
        **_family_dashboard_data(str(user_id), days, timezone_offset_minutes),
    })


@web.get("/api/family/children/<child_user_id>/lesson-words")
def api_family_child_lesson_words(child_user_id: str):
    parent_user_id = _current_user_id()
    if not parent_user_id or not _user_exists(parent_user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    if not _account_context(str(parent_user_id))["is_parent"]:
        return jsonify({"ok": False, "error": "parent_account_required"}), 403

    child_id = str(child_user_id or "").strip()
    lesson = str(request.args.get("lesson") or "").strip()
    if not lesson:
        return jsonify({"ok": False, "error": "lesson_required"}), 400

    _ensure_schema()
    with _conn() as c:
        linked = c.execute(
            "SELECT 1 FROM parent_child_links WHERE parent_user_id=? AND child_user_id=?",
            (str(parent_user_id), child_id),
        ).fetchone()
        if not linked:
            return jsonify({"ok": False, "error": "family_link_not_found"}), 404

        preferred = [item["code"] for item in _get_user_languages(child_id)]
        all_languages = _existing_word_languages(c)
        select_cols = ", ".join(
            f"w.{_word_text_col(language)} AS {language}_word"
            for language in all_languages
        )
        rows = c.execute(f"""
            SELECT w.id, w.number, {select_cols}
            FROM words w
            WHERE (w.user_id=? OR w.status='test') AND w.lesson=?
            ORDER BY w.number, w.id
        """, (child_id, lesson)).fetchall()

    languages = _lesson_available_languages(rows, preferred, all_languages)
    language_codes = [item["code"] for item in languages]
    return jsonify({
        "ok": True,
        "lesson": lesson,
        "languages": languages,
        "items": [
            {
                "id": row["id"],
                "number": row["number"] or "",
                "words": {
                    language: str(row[f"{language}_word"] or "")
                    for language in language_codes
                },
            }
            for row in rows
        ],
    })


@web.put("/api/family/children/<child_user_id>/priority-lesson")
def api_family_set_priority_lesson(child_user_id: str):
    parent_user_id = _current_user_id()
    if not parent_user_id or not _user_exists(parent_user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    _ensure_family_schema()
    child_id = str(child_user_id or "").strip()
    with _conn() as c:
        linked = c.execute(
            "SELECT 1 FROM parent_child_links WHERE parent_user_id=? AND child_user_id=?",
            (str(parent_user_id), child_id),
        ).fetchone()
    if not linked:
        return jsonify({"ok": False, "error": "family_link_not_found"}), 404

    data = request.get_json(silent=True) or {}
    lesson = str(data.get("lesson") or "").strip()
    if lesson:
        available = {
            str(item.get("lesson") or "").strip()
            for item in _lessons_available_to_child(child_id)
        }
        if lesson not in available:
            return jsonify({"ok": False, "error": "lesson_not_available"}), 400

    now_ms = int(time.time() * 1000)
    with _conn() as c:
        current = c.execute(
            "SELECT lesson FROM child_lesson_priorities WHERE child_user_id=?",
            (child_id,),
        ).fetchone()
        current_lesson = str((current["lesson"] if current else "") or "")
        if current_lesson == lesson:
            if lesson:
                models.set_lesson_hidden(Config.DB_PATH, child_id, lesson, 0)
            return jsonify({"ok": True, "child_user_id": child_id, "priority_lesson": lesson})
        c.execute("""
            UPDATE child_lesson_priority_history
            SET ended_at=?
            WHERE child_user_id=? AND ended_at IS NULL
        """, (now_ms, child_id))
        if lesson:
            c.execute("""
                INSERT INTO child_lesson_priorities
                    (child_user_id, lesson, parent_user_id, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(child_user_id) DO UPDATE SET
                    lesson=excluded.lesson,
                    parent_user_id=excluded.parent_user_id,
                    updated_at=excluded.updated_at
            """, (child_id, lesson, str(parent_user_id), now_ms))
            c.execute("""
                INSERT INTO child_lesson_priority_history
                    (child_user_id, lesson, parent_user_id, started_at, ended_at)
                VALUES (?, ?, ?, ?, NULL)
            """, (child_id, lesson, str(parent_user_id), now_ms))
        else:
            c.execute(
                "DELETE FROM child_lesson_priorities WHERE child_user_id=?",
                (child_id,),
            )
        c.commit()
    if lesson:
        models.set_lesson_hidden(Config.DB_PATH, child_id, lesson, 0)
    return jsonify({"ok": True, "child_user_id": child_id, "priority_lesson": lesson})


def _pairing_payload(user_id: str) -> tuple[Dict[str, Any] | None, tuple | None]:
    account = _account_context(user_id)
    if account["account_type"] != "child":
        return None, (jsonify({"ok": False, "error": "child_account_required"}), 403)
    token = create_pairing_token(user_id)
    try:
        code = create_pairing_code(Config.DB_PATH, user_id)
    except ValueError:
        return None, (jsonify({"ok": False, "error": "child_account_required"}), 403)
    transport = invitation_payload(code, "family")
    pairing_url = transport["url"]
    return {
        "ok": True,
        "token": token,
        **transport,
        "pairing_url": pairing_url,
        "expires_in": PAIRING_TOKEN_MAX_AGE_SECONDS,
    }, None


@web.get("/api/family/pairing-code")
def api_family_pairing_code():
    user_id = _current_user_id()
    if not user_id or not _user_exists(user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    payload, error = _pairing_payload(str(user_id))
    if error:
        return error
    return jsonify(payload)


@web.post("/api/family/invitation/preview")
@web.post("/api/family/invitation/accept")
def api_family_invitation():
    user_id = _current_user_id()
    if not user_id or not _user_exists(user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    if not allow_invitation_attempt(user_id):
        return jsonify({"ok": False, "error": "too_many_attempts"}), 429
    _ensure_family_schema()
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"ok": False, "error": "invalid_or_expired_pairing_code"}), 400
    if data.get("token") and request.path.endswith("/preview"):
        child_id = verify_pairing_token(str(data["token"]))
        if not child_id:
            return jsonify({"ok": False, "error": "invalid_or_expired_pairing_code"}), 400
        try:
            data = {"code": create_pairing_code(Config.DB_PATH, child_id), "kind": "family"}
        except ValueError:
            return jsonify({"ok": False, "error": "child_account_not_found"}), 400
    handler = accept_invitation if request.path.endswith("/accept") else preview_invitation
    result = handler(user_id, data.get("code"), data.get("kind", ""))
    return jsonify(result), 200 if result.get("ok") else 400


@web.get("/api/family/pairing-qr.png")
def api_family_pairing_qr():
    user_id = _current_user_id()
    if not user_id or not _user_exists(user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    code = str(request.args.get("code") or "").strip()
    if code:
        details = pairing_code_details(Config.DB_PATH, code)
        if not details or details["child_user_id"] != str(user_id):
            return jsonify({"ok": False, "error": "invalid_or_expired_pairing_code"}), 400
        pairing_url = invitation_payload(code, "family")["url"]
    else:
        payload, error = _pairing_payload(str(user_id))
        if error:
            return error
        pairing_url = payload["pairing_url"]
    import qrcode

    image = qrcode.make(pairing_url)
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    response = send_file(output, mimetype="image/png", download_name="parent-link.png")
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


def _invite_payload(user_id: str) -> tuple[Dict[str, Any] | None, tuple | None]:
    account = _account_context(user_id)
    if account["account_type"] != "standard":
        return None, (jsonify({"ok": False, "error": "parent_account_required"}), 403)
    code = create_invite_code(Config.DB_PATH, user_id)
    transport = invitation_payload(code, "invite")
    invite_url = transport["url"]
    return {
        "ok": True,
        **transport,
        "invite_url": invite_url,
        "expires_in": PAIRING_TOKEN_MAX_AGE_SECONDS,
    }, None


@web.get("/api/family/invite-code")
def api_family_invite_code():
    user_id = _current_user_id()
    if not user_id or not _user_exists(user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    payload, error = _invite_payload(str(user_id))
    if error:
        return error
    return jsonify(payload)


@web.get("/api/family/invite-qr.png")
def api_family_invite_qr():
    user_id = _current_user_id()
    if not user_id or not _user_exists(user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    code = str(request.args.get("code") or "").strip()
    if code:
        details = invite_code_details(Config.DB_PATH, code)
        if not details or details["parent_user_id"] != str(user_id):
            return jsonify({"ok": False, "error": "invalid_or_expired_pairing_code"}), 400
        invite_url = invitation_payload(code, "invite")["url"]
    else:
        payload, error = _invite_payload(str(user_id))
        if error:
            return error
        invite_url = payload["invite_url"]
    import qrcode

    image = qrcode.make(invite_url)
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    response = send_file(output, mimetype="image/png", download_name="child-invite.png")
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@web.post("/api/family/join")
def api_family_join():
    child_user_id = _current_user_id()
    if not child_user_id or not _user_exists(child_user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    data = request.get_json(silent=True) or {}
    code = str(data.get("code") or "").strip()
    if not code:
        return jsonify({"ok": False, "error": "invalid_or_expired_pairing_code"}), 400
    _ensure_family_schema()
    result = link_child_with_invite_code(Config.DB_PATH, str(child_user_id), code)
    if not result.get("ok"):
        status = 409 if result.get("error") == "parent_limit_reached" else 400
        return jsonify(result), status
    return jsonify({**result, **_account_context(str(child_user_id))})


@web.post("/api/family/link")
def api_family_link():
    parent_user_id = _current_user_id()
    if not parent_user_id or not _user_exists(parent_user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    parent_account = _account_context(str(parent_user_id))
    if parent_account["account_type"] == "pending":
        return jsonify({"ok": False, "error": "account_type_required"}), 409
    if parent_account["account_type"] != "standard":
        return jsonify({"ok": False, "error": "child_cannot_be_parent"}), 403
    data = request.get_json(silent=True) or {}
    if data.get("code"):
        if not allow_invitation_attempt(parent_user_id):
            return jsonify({"ok": False, "error": "too_many_attempts"}), 429
        result = accept_invitation(parent_user_id, data["code"], "family")
        return jsonify(result), 200 if result.get("ok") else 400
    token = str(data.get("token") or "").strip()
    child_user_id = verify_pairing_token(token)
    if not child_user_id:
        return jsonify({"ok": False, "error": "invalid_or_expired_pairing_code"}), 400
    if child_user_id == str(parent_user_id):
        return jsonify({"ok": False, "error": "cannot_link_self"}), 400
    _ensure_family_schema()
    with _conn() as c:
        c.execute("BEGIN IMMEDIATE")
        child = c.execute(
            "SELECT user_id, username, first_name, last_name, account_type "
            "FROM users WHERE user_id=?",
            (child_user_id,),
        ).fetchone()
        if not child or child["account_type"] != "child":
            return jsonify({"ok": False, "error": "child_account_not_found"}), 404
        existing = c.execute(
            """
            SELECT 1 FROM parent_child_links
            WHERE parent_user_id=? AND child_user_id=?
            """,
            (str(parent_user_id), child_user_id),
        ).fetchone()
        parents_count = int(c.execute(
            "SELECT COUNT(*) FROM parent_child_links WHERE child_user_id=?",
            (child_user_id,),
        ).fetchone()[0])
        if not existing and parents_count >= MAX_PARENTS_PER_CHILD:
            return jsonify({"ok": False, "error": "parent_limit_reached"}), 409
        c.execute("""
            INSERT INTO parent_child_links (parent_user_id, child_user_id)
            VALUES (?, ?)
            ON CONFLICT(parent_user_id, child_user_id) DO NOTHING
        """, (str(parent_user_id), child_user_id))
        c.commit()
    return jsonify({
        "ok": True,
        "child": {
            "user_id": child_user_id,
            "display_name": _format_user_name(child) or child_user_id,
        },
        **_account_context(str(parent_user_id)),
    })


@web.delete("/api/family/children/<child_user_id>")
def api_family_unlink_child(child_user_id: str):
    parent_user_id = _current_user_id()
    if not parent_user_id or not _user_exists(parent_user_id):
        return jsonify({"ok": False, "error": "auth_required"}), 401
    _ensure_family_schema()
    with _conn() as c:
        cursor = c.execute(
            "DELETE FROM parent_child_links WHERE parent_user_id=? AND child_user_id=?",
            (str(parent_user_id), str(child_user_id)),
        )
        if cursor.rowcount:
            _revoke_family_lesson_access(c, str(parent_user_id), str(child_user_id))
        c.commit()
    if cursor.rowcount == 0:
        return jsonify({"ok": False, "error": "family_link_not_found"}), 404
    return jsonify({"ok": True, **_account_context(str(parent_user_id))})


@web.get("/api/subscription")
def api_subscription_get():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    return jsonify({"ok": True, "subscription": _get_subscription(user_id)})


# ─────────────────────────────────────────────────────────────────────────────
# ⚠️  ЗАГЛУШКА Google Play Billing — /api/subscription/verify_purchase
#
# Что нужно сделать для продакшена:
# 1. Включить Google Play Android Developer API:
#    https://console.cloud.google.com/ → APIs & Services → Enable APIs
#    → "Google Play Android Developer API"
#
# 2. Создать Service Account (сервисный аккаунт):
#    Google Play Console → Настройки → API-доступ → Создать сервисный аккаунт
#    → Скачать JSON-ключ → добавить в .env как GOOGLE_SERVICE_ACCOUNT_JSON
#
# 3. Установить библиотеку:
#    pip install google-auth google-api-python-client
#
# 4. Заменить заглушку ниже реальной верификацией через googleapiclient:
#    service = build('androidpublisher', 'v3', credentials=creds)
#    result = service.purchases().subscriptions().get(
#        packageName=package_name, subscriptionId=product_id,
#        token=purchase_token).execute()
#    expiry_ms = int(result['expiryTimeMillis'])
# ─────────────────────────────────────────────────────────────────────────────
@web.post("/api/subscription/verify_purchase")
def api_verify_purchase():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    purchase_token = data.get("purchase_token", "")
    product_id     = data.get("product_id", "")
    package_name   = data.get("package_name", "")

    if not purchase_token or not product_id:
        return jsonify({"ok": False, "error": "missing fields"}), 400

    # Fail closed until Google Play Developer API verification is configured.
    # Never grant subscription access based only on a client-supplied token.
    return jsonify({
        "ok": False,
        "error": "google_play_verification_not_configured"
    }), 503

    # ── Реальная верификация (раскомментировать после настройки) ─────────────
    # try:
    #     import google.oauth2.service_account as sa
    #     from googleapiclient.discovery import build
    #     import os, json
    #     key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    #     creds = sa.Credentials.from_service_account_info(
    #         json.loads(key_json),
    #         scopes=["https://www.googleapis.com/auth/androidpublisher"]
    #     )
    #     service = build("androidpublisher", "v3", credentials=creds)
    #     result = service.purchases().subscriptions().get(
    #         packageName=package_name,
    #         subscriptionId=product_id,
    #         token=purchase_token
    #     ).execute()
    #     expiry_ms = int(result["expiryTimeMillis"])
    #     # ... активировать подписку в БД ...
    #     return jsonify({"ok": True, "status": "active", "expires_at": expiry_ms})
    # except Exception as e:
    #     return jsonify({"ok": False, "error": str(e)}), 500


@web.get("/api/language-options")
def api_language_options():
    if request.headers.get("X-Client") == "android":
        return jsonify(LANGUAGE_OPTIONS)
    return jsonify({"ok": True, "languages": LANGUAGE_OPTIONS})


@web.get("/api/user-languages")
def api_user_languages_get():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    languages = _get_user_languages(user_id)
    if request.headers.get("X-Client") == "android":
        return jsonify(languages)
    return jsonify({
        "ok": True,
        "configured": 3 <= len(languages) <= 5,
        "languages": languages,
        "options": LANGUAGE_OPTIONS,
    })


@web.post("/api/user-languages")
def api_user_languages_save():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _ensure_user_language_schema()

    data = request.get_json(silent=True) or {}
    raw = data.get("languages") or []
    if not isinstance(raw, list):
        return jsonify({"ok": False, "error": "bad_languages"}), 400

    cleaned: List[str] = []
    seen = set()
    for item in raw:
        code = str(item or "").strip().lower()
        if not code or code in seen:
            continue
        if code not in LANGUAGE_CODES:
            return jsonify({"ok": False, "error": f"unsupported_language:{code}"}), 400
        cleaned.append(code)
        seen.add(code)

    if len(cleaned) < 3 or len(cleaned) > 5:
        return jsonify({"ok": False, "error": "choose_3_to_5_languages"}), 400

    now_ms = int(time.time() * 1000)
    with _conn() as c:
        _ensure_word_language_columns(c, cleaned)
        c.execute("DELETE FROM user_language_preferences WHERE user_id = ?", (str(user_id),))
        c.executemany("""
            INSERT INTO user_language_preferences (user_id, priority, lang_code, updated_at)
            VALUES (?, ?, ?, ?)
        """, [(str(user_id), idx + 1, code, now_ms) for idx, code in enumerate(cleaned)])
        c.commit()

    languages = _get_user_languages(user_id)
    missing = _word_missing_language_summary(str(user_id), cleaned)
    return jsonify({"ok": True, "configured": True, "languages": languages, "generation": missing})


@web.get("/api/user-languages/missing-words")
def api_user_languages_missing_words():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    raw = request.args.get("languages") or request.args.get("lang") or ""
    requested = [x.strip().lower() for x in raw.split(",") if x.strip()]
    if not requested:
        requested = [item["code"] for item in _get_user_languages(user_id)]
    requested = [code for code in dict.fromkeys(requested) if code in LANGUAGE_CODES]
    if not requested:
        return jsonify({"ok": False, "error": "bad_languages"}), 400
    with _conn() as c:
        _ensure_word_language_columns(c, requested)
        existing_languages = _existing_word_languages(c)
        select_cols = ",\n                   ".join(_language_select_parts(existing_languages))
        rows = c.execute(f"""
            SELECT w.id, w.lesson, w.number,
                   {select_cols}
            FROM words w
            WHERE w.user_id = ?
              AND COALESCE(w.lesson, '') != ''
              AND ({' OR '.join([f"(COALESCE(w.{_word_text_col(code)}, '') = '' OR COALESCE(w.{_word_sentence_col(code)}, '') = '')" for code in requested])})
            ORDER BY w.lesson, w.number
        """, (str(user_id),)).fetchall()
    items = []
    for row in rows:
        item = _word_payload_from_row(row, existing_languages)
        item["missing_languages"] = [
            code for code in requested
            if not str(item.get(f"{code}_word") or "").strip()
            or not str(item.get(f"{code}_sentence") or "").strip()
        ]
        if item["missing_languages"]:
            items.append(item)
    return jsonify({"ok": True, "items": items, "languages": requested})


@web.get("/api/ui-language")
def api_ui_language_get():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    payload = _get_ui_language(user_id)
    return jsonify({"ok": True, "options": LANGUAGE_OPTIONS, **payload})


@web.post("/api/ui-language")
def api_ui_language_save():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    language_code = data.get("ui_language")
    payload = _save_ui_language_override(user_id, language_code)
    return jsonify({"ok": True, "options": LANGUAGE_OPTIONS, **payload})


# --- API уроков/слов (ИЗМЕНЕНО: difficult берём из user_word_flags) ---
def _lesson_language_progress(
    user_id: str,
    lesson_titles: List[str],
    owner_by_lesson: Dict[str, str] | None = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Count distinct correctly assembled words per lesson and practice language."""
    _ensure_progress_schema()
    lessons = [str(title).strip() for title in lesson_titles if str(title).strip()]
    if not lessons:
        return {}
    owner_by_lesson = owner_by_lesson or {}
    owners = {lesson: str(owner_by_lesson.get(lesson) or user_id) for lesson in lessons}
    ui_language = str(_get_ui_language(user_id).get("ui_language") or "en")
    target_languages = [
        item for item in _get_user_languages(user_id)
        if str(item.get("code") or "") != ui_language
    ]
    if not target_languages:
        return {lesson: [] for lesson in lessons}

    codes = [str(item["code"]) for item in target_languages]
    placeholders = ",".join("?" for _ in lessons)
    owner_ids = sorted(set(owners.values()))
    owner_placeholders = ",".join("?" for _ in owner_ids)
    available_word_ids: Dict[tuple[str, str], set[int]] = {
        (lesson, code): set() for lesson in lessons for code in codes
    }
    lesson_word_ids: Dict[str, set[int]] = {lesson: set() for lesson in lessons}
    with _conn() as c:
        _ensure_word_language_columns(c, codes)
        language_columns = ", ".join(f'"{_word_text_col(code)}"' for code in codes)
        rows = c.execute(f"""
            SELECT id, lesson, user_id, status, {language_columns}
            FROM words
            WHERE lesson IN ({placeholders}) AND (status = 'test' OR user_id IN ({owner_placeholders}))
        """, [*lessons, *owner_ids]).fetchall()
        for row in rows:
            lesson = str(row["lesson"])
            if lesson not in lesson_word_ids:
                continue
            if str(row["status"]) != "test" and str(row["user_id"]) != owners[lesson]:
                continue
            lesson_word_ids[lesson].add(int(row["id"]))
            for code in codes:
                if str(row[_word_text_col(code)] or "").strip():
                    available_word_ids[(lesson, code)].add(int(row["id"]))

        event_rows = c.execute("""
            SELECT payload
            FROM progress_events
            WHERE user_id = ? AND scope = 'learn'
            ORDER BY event_ts ASC, id ASC
        """, (str(user_id),)).fetchall()

    learned_word_ids: Dict[tuple[str, str], set[int]] = {
        key: set() for key in available_word_ids
    }
    for row in event_rows:
        try:
            payload = json.loads(row["payload"] or "{}")
        except (TypeError, ValueError):
            continue
        state = payload.get("state") if isinstance(payload, dict) else None
        if not isinstance(state, dict) or state.get("reason") != "answer_ok":
            continue
        lesson = str(state.get("lesson") or "").strip()
        code = str(state.get("lang") or "").strip().lower()
        try:
            word_id = int(state.get("word_id"))
        except (TypeError, ValueError):
            continue
        key = (lesson, code)
        if word_id in available_word_ids.get(key, set()):
            learned_word_ids[key].add(word_id)

    result: Dict[str, List[Dict[str, Any]]] = {}
    for lesson in lessons:
        result[lesson] = []
        for language in target_languages:
            code = str(language["code"])
            total = len(available_word_ids[(lesson, code)])
            # Не показываем прогресс языка, пока перевод не добавлен
            # для каждого слова урока. Иначе появляется бесполезный IT0.
            if total == 0 or total != len(lesson_word_ids[lesson]):
                continue
            learned = len(learned_word_ids[(lesson, code)])
            result[lesson].append({
                **language,
                "learned_words": learned,
                "total_words": total,
                "percent": round(learned * 100 / total) if total else 0,
            })
    return result


def _completed_lessons(user_id: str, lesson_titles: List[str]) -> List[str]:
    progress = _lesson_language_progress(user_id, lesson_titles, _lesson_owner_map(user_id))
    completed: List[str] = []
    for lesson, languages in progress.items():
        languages_with_words = [
            item for item in languages if int(item.get("total_words") or 0) > 0
        ]
        if languages_with_words and all(
            int(item.get("learned_words") or 0) >= int(item.get("total_words") or 0)
            for item in languages_with_words
        ):
            completed.append(lesson)
    return completed


@web.get("/api/lessons")
def api_lessons():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _ensure_schema()
    lessons = get_visible_lessons_for_user(str(user_id))
    priority_lesson = ""
    if _account_context(str(user_id))["account_type"] == "child":
        priority_lesson = _child_priority_lesson(str(user_id))
    for lesson in lessons:
        lesson["is_priority"] = bool(
            priority_lesson and str(lesson.get("lesson") or "") == priority_lesson
        )
    lessons.sort(key=lambda item: (
        not bool(item.get("is_priority")),
        bool(item.get("hidden")),
        -int(item.get("upload_order") or 0),
        str(item.get("lesson") or ""),
    ))
    progress = _lesson_language_progress(
        str(user_id),
        [str(item.get("lesson_title") or item.get("lesson") or "") for item in lessons],
        _lesson_owner_map(str(user_id), lessons),
    )
    for lesson in lessons:
        title = str(lesson.get("lesson_title") or lesson.get("lesson") or "")
        lesson["language_progress"] = progress.get(title, [])
    return jsonify(lessons)


@web.get("/api/user_lessons")
def api_user_lessons():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _ensure_schema()
    lessons = models.get_user_lessons(Config.DB_PATH, user_id)
    return jsonify(lessons)


@web.post("/api/user_lessons/rename")
def api_user_lessons_rename():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _ensure_schema()
    _ensure_family_schema()
    models.ensure_user_tables(Config.DB_PATH)

    data = request.get_json(silent=True) or {}
    old_lesson = str(data.get("lesson") or "").strip()
    new_lesson = " ".join(str(data.get("new_lesson") or "").split())
    if not old_lesson or not new_lesson:
        return jsonify({"ok": False, "error": "lesson_required"}), 400
    if len(new_lesson) > 200:
        return jsonify({"ok": False, "error": "lesson_too_long"}), 400
    if old_lesson == new_lesson:
        return jsonify({"ok": True, "lesson": new_lesson, "renamed_words": 0})

    with _conn() as c:
        owned_rows = c.execute(
            "SELECT id FROM words WHERE user_id=? AND lesson=? ORDER BY id",
            (str(user_id), old_lesson),
        ).fetchall()
        if not owned_rows:
            return jsonify({"ok": False, "error": "lesson_not_found"}), 404

        owned_ids = [int(row["id"]) for row in owned_rows]
        owned_qmarks = ",".join("?" * len(owned_ids))
        canonical_rows = c.execute(f"""
            SELECT DISTINCT parent_word_id
            FROM shared_lesson_words
            WHERE parent_word_id IN ({owned_qmarks}) OR child_word_id IN ({owned_qmarks})
        """, [*owned_ids, *owned_ids]).fetchall()
        canonical_ids = [int(row["parent_word_id"]) for row in canonical_rows]

        target_ids = set(owned_ids)
        if canonical_ids:
            canonical_qmarks = ",".join("?" * len(canonical_ids))
            mappings = c.execute(f"""
                SELECT parent_word_id, child_word_id
                FROM shared_lesson_words
                WHERE parent_word_id IN ({canonical_qmarks})
            """, canonical_ids).fetchall()
            for mapping in mappings:
                target_ids.add(int(mapping["parent_word_id"]))
                target_ids.add(int(mapping["child_word_id"]))

        target_qmarks = ",".join("?" * len(target_ids))
        target_rows = c.execute(
            f"SELECT id, user_id FROM words WHERE id IN ({target_qmarks})",
            list(target_ids),
        ).fetchall()
        affected_users = {str(row["user_id"] or "") for row in target_rows}
        for affected_user in affected_users:
            conflict = c.execute(f"""
                SELECT 1 FROM words
                WHERE user_id=? AND lesson=? AND id NOT IN ({target_qmarks})
                LIMIT 1
            """, [affected_user, new_lesson, *target_ids]).fetchone()
            if conflict:
                return jsonify({"ok": False, "error": "lesson_exists"}), 409

        now_ms = int(time.time() * 1000)
        c.execute(
            f"UPDATE words SET lesson=?, updated_at=? WHERE id IN ({target_qmarks})",
            [new_lesson, now_ms, *target_ids],
        )
        if canonical_ids:
            canonical_qmarks = ",".join("?" * len(canonical_ids))
            c.execute(f"""
                UPDATE shared_lesson_words SET lesson=?
                WHERE parent_word_id IN ({canonical_qmarks})
            """, [new_lesson, *canonical_ids])
        c.execute(
            "UPDATE family_lesson_assignments SET lesson=? WHERE parent_user_id=? AND lesson=?",
            (new_lesson, str(user_id), old_lesson),
        )

        for affected_user in affected_users:
            lesson_state = c.execute(
                "SELECT hidden FROM user_lessons WHERE user_id=? AND lesson=?",
                (affected_user, old_lesson),
            ).fetchone()
            if lesson_state:
                c.execute("""
                    INSERT INTO user_lessons (user_id, lesson, hidden, updated_at, updated_at_ts)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                    ON CONFLICT(user_id, lesson) DO UPDATE SET
                        hidden=excluded.hidden,
                        updated_at=excluded.updated_at,
                        updated_at_ts=excluded.updated_at_ts
                """, (affected_user, new_lesson, int(lesson_state["hidden"] or 0), now_ms))
                c.execute(
                    "DELETE FROM user_lessons WHERE user_id=? AND lesson=?",
                    (affected_user, old_lesson),
                )
            c.execute("""
                UPDATE child_lesson_priorities SET lesson=?, updated_at=?
                WHERE child_user_id=? AND lesson=?
            """, (new_lesson, now_ms, affected_user, old_lesson))
            c.execute("""
                UPDATE child_lesson_priority_history SET lesson=?
                WHERE child_user_id=? AND lesson=?
            """, (new_lesson, affected_user, old_lesson))
        c.commit()

    return jsonify({
        "ok": True,
        "lesson": new_lesson,
        "renamed_words": len(target_rows),
        "affected_accounts": len(affected_users),
    })


@web.post("/api/user_lessons/delete")
def api_user_lessons_delete():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _ensure_schema()
    models.ensure_user_tables(Config.DB_PATH)

    data = request.get_json(silent=True) or {}
    lessons = data.get("lessons") or []
    if isinstance(lessons, str):
        lessons = [lessons]
    if not isinstance(lessons, list):
        return jsonify({"ok": False, "error": "bad_lessons"}), 400

    cleaned: List[str] = []
    seen = set()
    for item in lessons:
        title = str(item or "").strip()
        if not title or title in seen:
            continue
        cleaned.append(title)
        seen.add(title)
    if not cleaned:
        return jsonify({"ok": False, "error": "lessons_required"}), 400

    qmarks = ",".join("?" * len(cleaned))
    audio_urls: List[str] = []
    word_ids: List[int] = []
    with _conn() as c:
        rows = c.execute(f"""
            SELECT id,
                   COALESCE(audio_nl,'') AS audio_nl,
                   COALESCE(audio_en,'') AS audio_en,
                   COALESCE(audio_ru,'') AS audio_ru
            FROM words
            WHERE user_id = ? AND lesson IN ({qmarks})
        """, [str(user_id)] + cleaned).fetchall()
        for r in rows:
            word_ids.append(int(r["id"]))
            for key in ("audio_nl", "audio_en", "audio_ru"):
                val = (r[key] or "").strip()
                if val:
                    audio_urls.append(val)

        if word_ids:
            id_marks = ",".join("?" * len(word_ids))
            c.execute(
                f"DELETE FROM user_word_flags WHERE user_id = ? AND word_id IN ({id_marks})",
                [str(user_id)] + word_ids,
            )
        c.execute(
            f"DELETE FROM family_lesson_assignments WHERE parent_user_id=? AND lesson IN ({qmarks})",
            [str(user_id), *cleaned],
        )
        c.execute(
            f"DELETE FROM words WHERE user_id = ? AND lesson IN ({qmarks})",
            [str(user_id)] + cleaned,
        )
        c.execute(
            f"DELETE FROM user_lessons WHERE user_id = ? AND lesson IN ({qmarks})",
            [str(user_id)] + cleaned,
        )
        c.commit()

    deleted_audio = _cleanup_audio_files(list(dict.fromkeys(audio_urls)))
    return jsonify({
        "ok": True,
        "deleted_lessons": len(cleaned),
        "deleted_words": len(word_ids),
        "deleted_audio": deleted_audio,
    })


@web.post("/api/lessons/set_hidden")
def api_lessons_set_hidden():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    lesson = (data.get("lesson") or "").strip()
    hidden = 1 if str(data.get("hidden")) in ("1", "true", "True", "on") else 0
    if not lesson:
        return jsonify({"ok": False, "error": "lesson_required"}), 400
    models.set_lesson_hidden(Config.DB_PATH, user_id, lesson, hidden)
    return jsonify({"ok": True})


@web.get("/api/lesson_words")
def api_lesson_words_by_title():
    _ensure_schema()  # [не менялось]
    lesson = (request.args.get("lesson") or "").strip()
    uid = _current_user_id()
    if not lesson:
        return jsonify({"ok": False, "error": "lesson_required"}), 400
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    with _conn() as c:
        owner_id = _child_lesson_owner(c, uid, lesson) if _account_context(uid)["account_type"] == "child" else uid
        if not owner_id:
            return jsonify({"ok": False, "error": "lesson_not_found"}), 404
        preferred = [item["code"] for item in _get_user_languages(uid)]
        languages = _existing_word_languages(c)
        select_cols = ",\n                   ".join(_language_select_parts(languages))
        rows = c.execute(f"""
            SELECT w.id, w.lesson, w.number,
                   {select_cols},
                   COALESCE(uf.difficult, 0) AS difficult,
                   w.status AS status,
                   w.user_id AS _word_owner
            FROM words w
            LEFT JOIN user_word_flags uf
              ON uf.word_id = w.id AND uf.user_id = ?
            WHERE (w.user_id = ? OR w.status = 'test') AND w.lesson = ?
            ORDER BY w.number
        """, (uid, owner_id, lesson)).fetchall()
    if not rows:
        return jsonify({"ok": False, "error": "lesson_not_found"}), 404
    available_languages = _lesson_available_languages(rows, preferred, languages)
    items = [_word_payload_from_row(r, languages, uid) for r in rows]
    if _account_context(uid)["account_type"] == "child":
        stats = _child_learning_stats(uid)
        counts = stats["word_counts"]
        for item in items:
            practice_count = counts.get(str(item.get("id")), 0)
            item["practice_count"] = practice_count
            item["learned"] = practice_count >= CHILD_WORD_MASTERY_COUNT
    if request.headers.get("X-Client") == "android":
        return jsonify(items)
    return jsonify({"ok": True, "items": items, "languages": available_languages})


@web.get("/api/child-learning/status")
def api_child_learning_status():
    uid = _current_user_id()
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    account = _account_context(uid)
    if account["account_type"] != "child":
        return jsonify({"ok": True, "is_child": False})
    try:
        timezone_offset = int(request.args.get("tz_offset") or 0)
    except (TypeError, ValueError):
        timezone_offset = 0
    timezone_offset = max(-14 * 60, min(14 * 60, timezone_offset))
    stats = _child_learning_stats(uid, timezone_offset)
    goal = _daily_goal_settings(uid)["goal_value"]
    today_count = min(stats["today_count"], goal)
    milestone = max((value for value in (5, 10, 15, 20, 25) if today_count >= value), default=0)
    return jsonify({
        "ok": True,
        "is_child": True,
        "today_count": today_count,
        "daily_goal": goal,
        "goal_complete": stats["today_count"] >= goal,
        "mastery_count": CHILD_WORD_MASTERY_COUNT,
        "mastered_words": len(stats["mastered_word_ids"]),
        "status_milestone": milestone,
    })


@web.get("/api/daily-goal")
def api_daily_goal_get():
    uid = _current_user_id()
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    return jsonify({"ok": True, **_daily_goal_settings(uid)})


@web.post("/api/daily-goal")
def api_daily_goal_save():
    uid = _current_user_id()
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    settings = _daily_goal_settings(uid)
    data = request.get_json(silent=True) or {}
    try:
        value = int(data.get("goal_value"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid_goal"}), 400
    if value < settings["minimum"] or value > settings["maximum"]:
        return jsonify({"ok": False, "error": "goal_out_of_range"}), 400
    with _conn() as c:
        c.execute("""
            INSERT INTO user_daily_goals(user_id, goal_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                goal_value=excluded.goal_value,
                updated_at=CURRENT_TIMESTAMP
        """, (uid, value))
        c.commit()
    return jsonify({"ok": True, **_daily_goal_settings(uid)})


@web.get("/api/lessons/<int:lesson_id>/words")
def api_lesson_words(lesson_id: int):
    _ensure_schema()
    lang = (request.args.get("lang") or "nl").lower()
    uid = _current_user_id()
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    with _conn() as c:
        owner_id = _child_lesson_owner(c, uid, str(lesson_id)) if _account_context(uid)["account_type"] == "child" else uid
        if not owner_id:
            return jsonify({"ok": False, "error": "lesson_not_found"}), 404
        rows = c.execute("""
            SELECT w.id,
                   w.nl AS nl_word, w.en AS en_word, w.ru AS ru_word,
                   w.ex_nl AS nl_sentence, w.ex_en AS en_sentence, w.ex_ru AS ru_sentence,
                   w.audio_nl AS nl_audio, w.audio_en AS en_audio, w.audio_ru AS ru_audio,
                   COALESCE(uf.difficult, 0) AS difficult
            FROM words w
            LEFT JOIN user_word_flags uf
              ON uf.word_id = w.id AND uf.user_id = ?
            WHERE (w.user_id = ? OR w.status = 'test') AND w.lesson = ?
            ORDER BY w.number
        """, (uid, owner_id, str(lesson_id))).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        d.setdefault("word_en",        d.get("en_word", ""))
        d.setdefault("translation_ru", d.get("ru_word", ""))
        d.setdefault("translation_nl", d.get("nl_word", ""))
        d.setdefault("audio_en", d.get("en_audio", ""))
        d.setdefault("audio_ru", d.get("ru_audio", ""))
        d.setdefault("audio_nl", d.get("nl_audio", ""))
        d.setdefault("sentence_en", d.get("en_sentence", ""))
        d.setdefault("sentence_ru", d.get("ru_sentence", ""))
        d.setdefault("sentence_nl", d.get("nl_sentence", ""))
        items.append(d)
    return jsonify({"lang": lang, "items": items})


@web.get("/api/difficult_words_user")
def api_difficult_words_user():
    """
    Персональный список:
      - слова из words, у которых user_word_flags.difficult=1 для текущего пользователя
      (кастомные слова удалены)
    """
    _ensure_schema()
    _ensure_family_schema()
    uid = _current_user_id()
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    language_meta = _get_user_languages(uid)
    languages = [item["code"] for item in language_meta] or ["nl", "en", "ru"]
    with _conn() as c:
        _ensure_word_language_columns(c, languages)
        c.commit()
        select_languages = ",\n                   ".join(_language_select_parts(languages))
        preset = c.execute(f"""
            SELECT w.id, w.lesson, w.number,
                   {select_languages},
                   1 AS difficult,
                   'preset' AS kind,
                   w.status AS status,
                   w.user_id AS _word_owner
            FROM words w
            JOIN user_word_flags uf
              ON uf.word_id = w.id AND uf.user_id = ? AND COALESCE(uf.difficult,0)=1
            WHERE (w.user_id = ? OR w.status = 'test'
                   OR EXISTS (
                       SELECT 1 FROM family_lesson_assignments a
                       WHERE a.child_user_id = ? AND a.parent_user_id = w.user_id AND a.lesson = w.lesson
                   ))
            ORDER BY w.lesson, w.number
        """, (uid, uid, uid)).fetchall()
    items: List[Dict[str, Any]] = []
    for r in preset:
        items.append(_word_payload_from_row(r, languages, uid))
    return jsonify({"ok": True, "items": items, "languages": language_meta or [LANGUAGE_META[code] for code in languages]})


@web.post("/api/difficult/user_set")
def api_difficult_user_set():
    """
    Body: {word_id: int, difficult: 0|1}
    """
    _ensure_schema()
    data = request.get_json(silent=True) or {}
    uid = _current_user_id()
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    try:
        wid = int(data.get("word_id"))
    except Exception:
        return jsonify({"ok": False, "error": "bad_word_id"}), 400
    difficult = 1 if str(data.get("difficult")) in ("1","true","True","on") else 0
    with _conn() as c:
        word = c.execute("SELECT user_id, lesson, status FROM words WHERE id=?", (wid,)).fetchone()
        exists = bool(word) and (
            str(word["user_id"]) == str(uid)
            or str(word["status"]) == "test"
            or (_account_context(uid)["account_type"] == "child"
                and _child_lesson_owner(c, uid, str(word["lesson"] or "")) == str(word["user_id"]))
        )
        if not exists:
            return jsonify({"ok": False, "error": "not_found"}), 404
        if difficult == 1:
            c.execute("""
                INSERT INTO user_word_flags (user_id, word_id, difficult)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, word_id) DO UPDATE SET difficult=1
            """, (uid, wid))
        else:
            c.execute("""
                INSERT INTO user_word_flags (user_id, word_id, difficult)
                VALUES (?, ?, 0)
                ON CONFLICT(user_id, word_id) DO UPDATE SET difficult=0
            """, (uid, wid))
        c.commit()
    return jsonify({"ok": True})


@web.post("/api/progress/sync")
def api_progress_sync():
    _ensure_progress_schema()
    _ensure_schema()
    data = request.get_json(silent=True) or {}
    events = data if isinstance(data, list) else data.get("events")
    if events is None:
        events = []
    if not isinstance(events, list):
        return jsonify({"ok": False, "error": "bad_events"}), 400

    user_id = _current_user_id() or ""
    rows = []
    affected_lessons = set()
    child_goal_offsets = []
    for ev in events:
        payload = ev if isinstance(ev, dict) else {"value": ev}
        scope = str(payload.get("scope") or "")
        event_type = str(payload.get("type") or "")
        event_ts = None
        try:
            event_ts = int(payload.get("ts")) if payload.get("ts") is not None else None
        except Exception:
            event_ts = None
        rows.append((user_id, scope, event_type, event_ts, json.dumps(payload, ensure_ascii=False)))
        state = payload.get("state") if isinstance(payload, dict) else None
        if (
            scope == "learn"
            and isinstance(state, dict)
            and state.get("reason") == "answer_ok"
            and str(state.get("lesson") or "").strip()
        ):
            affected_lessons.add(str(state["lesson"]).strip())
        if scope == "learn" and isinstance(state, dict):
            reason = str(state.get("reason") or "")
            if reason == "answer_ok" or event_type == "word_correct":
                try:
                    child_goal_offsets.append(int(state.get("tz_offset") or 0))
                except (TypeError, ValueError):
                    child_goal_offsets.append(0)

    if rows:
        with _conn() as c:
            c.executemany("""
                INSERT INTO progress_events (user_id, scope, event_type, event_ts, payload)
                VALUES (?, ?, ?, ?, ?)
            """, rows)
            c.commit()
    completed_lessons = _completed_lessons(user_id, sorted(affected_lessons)) if user_id else []
    for lesson in completed_lessons:
        models.set_lesson_hidden(Config.DB_PATH, user_id, lesson, 1)
    if user_id and child_goal_offsets:
        offset = max(-14 * 60, min(14 * 60, child_goal_offsets[-1]))
        _notify_parents_child_goal(user_id, offset)
    return jsonify({
        "ok": True,
        "stored": len(rows),
        "completed_lessons": completed_lessons,
    })


@web.get("/api/sync/updates")
def api_sync_updates():
    _ensure_schema()
    models.ensure_user_tables(Config.DB_PATH)
    since_raw = request.args.get("since") or "0"
    try:
        since = int(since_raw)
    except Exception:
        since = 0

    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    server_ts = int(time.time() * 1000)

    def _word_row_to_item(row):
        d = dict(row)
        d.setdefault("word_en",        d.get("en_word", ""))
        d.setdefault("translation_ru", d.get("ru_word", ""))
        d.setdefault("translation_nl", d.get("nl_word", ""))
        d.setdefault("audio_en", d.get("en_audio", ""))
        d.setdefault("audio_ru", d.get("ru_audio", ""))
        d.setdefault("audio_nl", d.get("nl_audio", ""))
        d.setdefault("sentence_en", d.get("en_sentence", ""))
        d.setdefault("sentence_ru", d.get("ru_sentence", ""))
        d.setdefault("sentence_nl", d.get("nl_sentence", ""))
        return d

    with _conn() as c:
        word_rows = c.execute("""
            SELECT id, lesson, number,
                   nl AS nl_word, en AS en_word, ru AS ru_word,
                   ex_nl AS nl_sentence, ex_en AS en_sentence, ex_ru AS ru_sentence,
                   audio_nl AS nl_audio, audio_en AS en_audio, audio_ru AS ru_audio,
                   updated_at
            FROM words
            WHERE (user_id = ? OR status = 'test') AND updated_at IS NOT NULL AND updated_at > ?
            ORDER BY updated_at ASC
        """, (str(user_id), since)).fetchall()

    words = [_word_row_to_item(r) for r in word_rows]
    changed_lessons = sorted({r["lesson"] for r in word_rows if r["lesson"]})

    user_lessons = []
    with _conn() as c:
        ul_rows = c.execute("""
            SELECT lesson, hidden, updated_at_ts
            FROM user_lessons
            WHERE user_id = ? AND COALESCE(updated_at_ts, 0) > ?
        """, (str(user_id), since)).fetchall()
    user_lessons = [dict(r) for r in ul_rows]

    lessons = []
    if changed_lessons:
        qmarks = ",".join("?" * len(changed_lessons))
        with _conn() as c:
            rows = c.execute(f"""
                SELECT
                    w.lesson AS lesson,
                    COUNT(*) AS words_count,
                    MIN(
                        CAST(
                            SUBSTR(w.number, 1, INSTR(w.number || '.', '.') - 1) AS INTEGER
                        )
                    ) AS lesson_index
                FROM words w
                WHERE (w.user_id = ? OR w.status = 'test') AND w.lesson IN ({qmarks})
                GROUP BY w.lesson
            """, [str(user_id)] + changed_lessons).fetchall()

        hidden_map = {}
        with _conn() as c:
            for r in c.execute("SELECT lesson, hidden FROM user_lessons WHERE user_id = ?", (str(user_id),)):
                hidden_map[r["lesson"]] = int(r["hidden"])

        for r in rows:
            lessons.append({
                "lesson": r["lesson"],
                "lesson_title": r["lesson"],
                "words_count": r["words_count"],
                "lesson_index": int(r["lesson_index"] or 0),
                "hidden": hidden_map.get(r["lesson"], 0)
            })

    return jsonify({
        "ok": True,
        "server_ts": server_ts,
        "words": words,
        "lessons": lessons,
        "user_lessons": user_lessons
    })


# ----------------- [ДОБАВЛЕНО v7.0] AUDIO ENSURE -----------------
@web.post("/api/audio/ensure")
def api_audio_ensure():
    """
    Body: { ids: [int,...], langs: ["nl","en","ru"] }
    Для каждого id создаёт недостающие MP3, обновляет ссылки в words.audio_*.
    Возвращает { ok: true, items: [ {ok,id,nl,en,ru}, ... ] }
    """
    _ensure_schema()
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    ids = data.get("ids") or data.get("word_ids") or []
    langs = data.get("langs") or ["nl", "en", "ru"]
    try:
        result = ensure_audio_for_ids(Config.DB_PATH, ids, langs, user_id=user_id)
        return jsonify(result), (429 if result.get("limit_reached") else 200)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ------------------------------ НОВОЕ ------------------------------
@web.get("/api/next_lesson")
def api_next_lesson():
    """
    Возвращает следующий ВИДИМЫЙ урок относительно текущего названия.
    Query: ?current=<lesson_title>
    Ответ: { ok: true, next: "<lesson>" } или { ok: false }
    """
    _ensure_schema()
    current = (request.args.get("current") or "").strip()
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    nxt = models.get_next_lesson_title(Config.DB_PATH, current, user_id)
    if not nxt:
        return jsonify({"ok": False})
    return jsonify({"ok": True, "next": nxt})


@web.get("/api/prev_lesson")
def api_prev_lesson():
    """
    Возвращает предыдущий ВИДИМЫЙ урок относительно текущего названия.
    Query: ?current=<lesson_title>
    Ответ: { ok: true, prev: "<lesson>" } или { ok: false }
    """
    _ensure_schema()
    current = (request.args.get("current") or "").strip()
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    prv = models.get_prev_lesson_title(Config.DB_PATH, current, user_id)
    if not prv:
        return jsonify({"ok": False})
    return jsonify({"ok": True, "prev": prv})
# ------------------------------------------------------------------


# ─── Admin helpers ───────────────────────────────────────────────────────────

def _require_admin(*, allow_platform: bool = False) -> tuple:
    uid = _session_admin_user_id()
    if not uid and allow_platform:
        configured_token = str(Config.AI_PLATFORM_ADMIN_TOKEN or "").strip()
        authorization = str(request.headers.get("Authorization") or "").strip()
        supplied_token = (
            authorization[7:].strip()
            if authorization.lower().startswith("bearer ")
            else ""
        )
        if (
            configured_token
            and supplied_token
            and secrets.compare_digest(supplied_token, configured_token)
        ):
            uid = "ai-platform"
    if not uid:
        return None, (jsonify({"ok": False, "error": "unauthorized"}), 401)
    return uid, None


@web.get("/api/admin/users")
def api_admin_users():
    """Список всех пользователей с их статусом подписки. Только для админов."""
    uid, err = _require_admin(allow_platform=True)
    if err:
        return err
    _ensure_subscription_schema()
    _ensure_family_schema()
    now_ms = int(time.time() * 1000)
    # 10 лет в мс — порог для определения «безлимитного» доступа
    ten_years_ms = 10 * 365 * 24 * 60 * 60 * 1000
    with _conn() as c:
        rows = c.execute("""
            SELECT
                u.user_id, u.username, u.first_name, u.last_name, u.account_type,
                s.status, s.current_period_ends_at, s.trial_ends_at, s.provider
            FROM users u
            LEFT JOIN user_subscriptions s ON u.user_id = s.user_id
            ORDER BY u.user_id
        """).fetchall()
        family_rows = c.execute("""
            SELECT l.parent_user_id, l.child_user_id,
                   p.username AS parent_username, p.first_name AS parent_first_name,
                   ch.username AS child_username, ch.first_name AS child_first_name
            FROM parent_child_links l
            JOIN users p ON p.user_id = l.parent_user_id
            JOIN users ch ON ch.user_id = l.child_user_id
            ORDER BY l.created_at DESC
        """).fetchall()
        tts_usage = get_tts_usage_snapshot(
            c,
            timezone_name=Config.TTS_USAGE_TIMEZONE,
        )
        translation_usage = get_translation_usage_snapshot(c)
    family_relations = {}
    for link in family_rows:
        parent_id = str(link["parent_user_id"])
        child_id = str(link["child_user_id"])
        parent_name = str(link["parent_first_name"] or link["parent_username"] or parent_id)
        child_name = str(link["child_first_name"] or link["child_username"] or child_id)
        family_relations.setdefault(parent_id, []).append({
            "direction": "parent_of", "parent_user_id": parent_id,
            "child_user_id": child_id, "display_name": child_name,
        })
        family_relations.setdefault(child_id, []).append({
            "direction": "child_of", "parent_user_id": parent_id,
            "child_user_id": child_id, "display_name": parent_name,
        })
    users = []
    for r in rows:
        status = r["status"] or "no_sub"
        period_ends = r["current_period_ends_at"]
        trial_ends = int(r["trial_ends_at"] or 0)
        is_unlimited = (
            _is_admin_user_id(r["user_id"])
            or status == "active"
            and period_ends is not None
            and int(period_ends) > now_ms + ten_years_ms
        )
        users.append({
            "user_id": r["user_id"],
            "username": r["username"] or "",
            "first_name": r["first_name"] or "",
            "last_name": r["last_name"] or "",
            "status": status,
            "current_period_ends_at": period_ends,
            "trial_ends_at": trial_ends,
            "provider": r["provider"] or "",
            "is_unlimited": is_unlimited,
            "is_admin": _is_admin_user_id(r["user_id"]),
            "account_type": str(r["account_type"] or "standard"),
            "family_relations": family_relations.get(str(r["user_id"]), []),
            "tts_successful_requests": tts_usage["by_user"].get(str(r["user_id"]), {}).get("successful_requests", 0),
            "tts_failed_requests": tts_usage["by_user"].get(str(r["user_id"]), {}).get("failed_requests", 0),
            "tts_total_requests": tts_usage["by_user"].get(str(r["user_id"]), {}).get("total_requests", 0),
            "tts_characters": tts_usage["by_user"].get(str(r["user_id"]), {}).get("characters", 0),
            "tts_blocked_requests": tts_usage["by_user"].get(str(r["user_id"]), {}).get("blocked_requests", 0),
            "tts_character_limit": tts_usage["by_user"].get(str(r["user_id"]), {}).get("character_limit"),
            "tts_characters_remaining": tts_usage["by_user"].get(str(r["user_id"]), {}).get("characters_remaining"),
            "translation_successful_requests": translation_usage["by_user"].get(str(r["user_id"]), {}).get("successful_requests", 0),
            "translation_failed_requests": translation_usage["by_user"].get(str(r["user_id"]), {}).get("failed_requests", 0),
            "translation_prompt_tokens": translation_usage["by_user"].get(str(r["user_id"]), {}).get("prompt_tokens", 0),
            "translation_completion_tokens": translation_usage["by_user"].get(str(r["user_id"]), {}).get("completion_tokens", 0),
            "translation_total_tokens": translation_usage["by_user"].get(str(r["user_id"]), {}).get("total_tokens", 0),
        })
    return jsonify({
        "ok": True,
        "users": users,
        "tts_usage": {key: value for key, value in tts_usage.items() if key != "by_user"},
        "translation_usage": {key: value for key, value in translation_usage.items() if key != "by_user"},
    })


@web.post("/api/admin/tts_usage/limit")
def api_admin_set_tts_usage_limit():
    """Sets the global or per-user monthly TTS character limit."""
    uid, err = _require_admin(allow_platform=True)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    target_uid = str(data.get("user_id") or "").strip() or None
    raw_limit = data.get("monthly_character_limit")
    if target_uid is None and raw_limit is None:
        return jsonify({"ok": False, "error": "global limit cannot be unlimited"}), 400
    try:
        limit = None if raw_limit in (None, "") else int(raw_limit)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "monthly_character_limit must be an integer"}), 400

    with _conn() as c:
        if target_uid is not None and not c.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (target_uid,)
        ).fetchone():
            return jsonify({"ok": False, "error": "user not found"}), 404
        try:
            set_tts_character_limit(
                c,
                user_id=target_uid,
                monthly_character_limit=limit,
            )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        c.commit()
        snapshot = get_tts_usage_snapshot(
            c,
            timezone_name=Config.TTS_USAGE_TIMEZONE,
        )

    return jsonify({
        "ok": True,
        "user_id": target_uid,
        "monthly_character_limit": limit,
        "tts_usage": {key: value for key, value in snapshot.items() if key != "by_user"},
    })


@web.post("/api/admin/tts_usage/reset")
def api_admin_reset_tts_usage():
    """Сбрасывает месячный Google TTS-счётчик одного пользователя или всех пользователей."""
    uid, err = _require_admin(allow_platform=True)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    target_uid = str(data.get("user_id") or "").strip() or None

    with _conn() as c:
        if target_uid is not None:
            exists = c.execute(
                "SELECT 1 FROM users WHERE user_id = ?",
                (target_uid,),
            ).fetchone()
            if not exists:
                return jsonify({"ok": False, "error": "user not found"}), 404
        reset_rows = reset_tts_usage(
            c,
            user_id=target_uid,
            timezone_name=Config.TTS_USAGE_TIMEZONE,
        )
        c.commit()
        snapshot = get_tts_usage_snapshot(
            c,
            timezone_name=Config.TTS_USAGE_TIMEZONE,
        )

    return jsonify({
        "ok": True,
        "user_id": target_uid,
        "reset_rows": reset_rows,
        "tts_usage": {key: value for key, value in snapshot.items() if key != "by_user"},
    })


@web.post("/api/admin/translation_usage/reset")
def api_admin_reset_translation_usage():
    """Сбрасывает накопительную статистику токенов одного пользователя или всех."""
    uid, err = _require_admin(allow_platform=True)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    target_uid = str(data.get("user_id") or "").strip() or None

    with _conn() as c:
        if target_uid is not None:
            exists = c.execute(
                "SELECT 1 FROM users WHERE user_id = ?",
                (target_uid,),
            ).fetchone()
            if not exists:
                return jsonify({"ok": False, "error": "user not found"}), 404
        reset_rows = reset_translation_usage(c, user_id=target_uid)
        c.commit()
        snapshot = get_translation_usage_snapshot(c)

    return jsonify({
        "ok": True,
        "user_id": target_uid,
        "reset_rows": reset_rows,
        "translation_usage": {
            key: value for key, value in snapshot.items() if key != "by_user"
        },
    })


@web.post("/api/admin/grant_access")
def api_admin_grant_access():
    """Выдаёт пользователю безлимитный доступ (100 лет). Только для админов."""
    uid, err = _require_admin()
    if err:
        return err
    _ensure_subscription_schema()
    data = request.get_json(silent=True) or {}
    target_uid = str(data.get("user_id", "")).strip()
    if not target_uid:
        return jsonify({"ok": False, "error": "user_id required"}), 400

    now_ms = int(time.time() * 1000)
    forever_ms = now_ms + 100 * 365 * 24 * 60 * 60 * 1000

    with _conn() as c:
        if not c.execute("SELECT 1 FROM users WHERE user_id=?", (target_uid,)).fetchone():
            return jsonify({"ok": False, "error": "user not found"}), 404
        c.execute("""
            INSERT INTO user_subscriptions
                (user_id, status, trial_started_at, trial_ends_at,
                 current_period_ends_at, provider, updated_at)
            VALUES (?, 'active', ?, ?, ?, 'manual', ?)
            ON CONFLICT(user_id) DO UPDATE SET
                status = 'active',
                current_period_ends_at = excluded.current_period_ends_at,
                provider = 'manual',
                updated_at = excluded.updated_at
        """, (target_uid, now_ms, now_ms, forever_ms, now_ms))
        c.commit()
    return jsonify({"ok": True, "user_id": target_uid, "expires_at": forever_ms})


@web.post("/api/admin/revoke_access")
def api_admin_revoke_access():
    """Отзывает безлимитный доступ — переводит пользователя в истёкший trial. Только для админов."""
    uid, err = _require_admin()
    if err:
        return err
    _ensure_subscription_schema()
    data = request.get_json(silent=True) or {}
    target_uid = str(data.get("user_id", "")).strip()
    if not target_uid:
        return jsonify({"ok": False, "error": "user_id required"}), 400

    now_ms = int(time.time() * 1000)
    with _conn() as c:
        c.execute("""
            UPDATE user_subscriptions
            SET status = 'trial',
                current_period_ends_at = NULL,
                provider = NULL,
                updated_at = ?
            WHERE user_id = ?
        """, (now_ms, target_uid))
        c.commit()
    return jsonify({"ok": True, "user_id": target_uid})


@web.post("/api/admin/unlink_family")
def api_admin_unlink_family():
    """Remove one exact adult-child relationship. Only for admins."""
    uid, err = _require_admin()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    parent_user_id = str(data.get("parent_user_id") or "").strip()
    child_user_id = str(data.get("child_user_id") or "").strip()
    if not parent_user_id or not child_user_id:
        return jsonify({"ok": False, "error": "parent_user_id and child_user_id required"}), 400
    _ensure_family_schema()
    with _conn() as c:
        cursor = c.execute(
            """
            DELETE FROM parent_child_links
            WHERE parent_user_id=? AND child_user_id=?
            """,
            (parent_user_id, child_user_id),
        )
        if cursor.rowcount:
            _revoke_family_lesson_access(c, parent_user_id, child_user_id)
        c.commit()
    if cursor.rowcount == 0:
        return jsonify({"ok": False, "error": "family_link_not_found"}), 404
    return jsonify({
        "ok": True,
        "parent_user_id": parent_user_id,
        "child_user_id": child_user_id,
    })


@web.post("/api/admin/delete_user")
def api_admin_delete_user():
    """Полностью удаляет пользователя и его данные, чтобы он мог зарегистрироваться заново."""
    uid, err = _require_admin()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    target_uid = str(data.get("user_id", "")).strip()
    if not target_uid:
        return jsonify({"ok": False, "error": "user_id required"}), 400
    if _is_admin_user_id(target_uid):
        return jsonify({"ok": False, "error": "admin users are managed through ADMIN_IDS"}), 400

    _ensure_schema()
    _ensure_subscription_schema()
    with _conn() as c:
        row = c.execute("SELECT 1 FROM users WHERE user_id=?", (target_uid,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "user not found"}), 404

        word_ids = [
            int(r["id"])
            for r in c.execute("SELECT id FROM words WHERE user_id=?", (target_uid,)).fetchall()
        ]
        if word_ids:
            marks = ",".join("?" * len(word_ids))
            c.execute(f"DELETE FROM user_word_flags WHERE word_id IN ({marks})", word_ids)

        try:
            c.execute(
                "DELETE FROM family_lesson_assignments "
                "WHERE parent_user_id=? OR child_user_id=?",
                (target_uid, target_uid),
            )
        except sqlite3.OperationalError:
            pass
        try:
            c.execute(
                "DELETE FROM parent_child_links "
                "WHERE parent_user_id=? OR child_user_id=?",
                (target_uid, target_uid),
            )
        except sqlite3.OperationalError:
            pass
        try:
            c.execute(
                "DELETE FROM child_lesson_priorities "
                "WHERE child_user_id=? OR parent_user_id=?",
                (target_uid, target_uid),
            )
        except sqlite3.OperationalError:
            pass
        try:
            c.execute(
                "DELETE FROM child_lesson_priority_history "
                "WHERE child_user_id=? OR parent_user_id=?",
                (target_uid, target_uid),
            )
        except sqlite3.OperationalError:
            pass

        deletes = [
            ("words", "user_id"),
            ("user_word_flags", "user_id"),
            ("user_lessons", "user_id"),
            ("progress_events", "user_id"),
            ("user_language_preferences", "user_id"),
            ("user_settings", "user_id"),
            ("user_subscriptions", "user_id"),
            ("google_tts_usage_monthly", "user_id"),
            ("google_tts_budget_monthly", "user_id"),
            ("translation_token_usage", "user_id"),
            ("reminder_state", "user_id"),
            ("shared_word_sets", "owner_user_id"),
            ("users", "user_id"),
        ]
        for table, column in deletes:
            try:
                c.execute(f"DELETE FROM {table} WHERE {column}=?", (target_uid,))
            except sqlite3.OperationalError:
                pass
        try:
            c.execute(
                "DELETE FROM google_tts_limits WHERE scope = ?",
                (f"user:{target_uid}",),
            )
        except sqlite3.OperationalError:
            pass
        c.commit()

    return jsonify({"ok": True, "user_id": target_uid})


# ─── AI: облачная генерация слов через AI Platform ─────────────────────────
# Единый серверный сервис контента для всех клиентов.
# Готовый контент переиспользуется, недостающий обрабатывают серверные адаптеры.

@web.get("/api/ai/status")
def api_ai_status():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    return jsonify({"ok": True, "cloud_available": ai_platform.is_configured()})


@web.post("/api/translate/word")
def api_translate_word():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    word = str(data.get("word", "")).strip()
    from_lang = str(data.get("from_lang", "nl"))
    level = str(data.get("level", "A2"))
    known_ru = data.get("known_ru")
    if not word:
        return jsonify({"ok": False, "error": "word required"}), 400

    try:
        item, usage = ai_platform.translate_word(
            word,from_lang,data.get("level", ""),known_ru,supplied=data.get("supplied"),
            languages=data.get("languages") or [entry["code"] for entry in _get_user_languages(str(user_id))] or ["nl","en","ru"],
            sense=str(data.get("sense") or ""),context=str(data.get("context") or ""),examples=data.get("examples",True) is not False)
    except ai_platform.AiPlatformError as exc:
        _record_translation_request_usage(
            user_id,
            successful=False,
            usage=exc.usage,
        )
        return jsonify({"ok": False, "error": str(exc)}), 502

    if getattr(usage,"provider_calls",1) or getattr(usage,"total_tokens",0):
        _record_translation_request_usage(user_id, successful=True, usage=usage)

    return jsonify({"ok": True, **item})


@web.post("/api/generate/topic")
def api_generate_topic():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic", "")).strip()
    lang = str(data.get("lang", "nl"))
    level = str(data.get("level", "A2"))
    count = int(data.get("count") or 10)
    existing_words = data.get("existing_words") or []
    if not topic:
        return jsonify({"ok": False, "error": "topic required"}), 400

    try:
        words, usage = ai_platform.suggest_topic_words(
            topic, lang, level, count, existing_words
        )
    except ai_platform.AiPlatformError as exc:
        _record_translation_request_usage(
            user_id,
            successful=False,
            usage=exc.usage,
        )
        return jsonify({"ok": False, "error": str(exc)}), 502

    if getattr(usage,"provider_calls",1) or getattr(usage,"total_tokens",0):
        _record_translation_request_usage(user_id, successful=True, usage=usage)

    return jsonify({"ok": True, "words": words})


@web.post("/api/translate/language")
def api_translate_language():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    source_word = str(data.get("source_word", "")).strip()
    source_sentence = str(data.get("source_sentence", ""))
    source_lang_name = str(data.get("source_lang_name", ""))
    target_lang_name = str(data.get("target_lang_name", ""))
    if not source_word or not target_lang_name:
        return jsonify({"ok": False, "error": "source_word and target_lang_name required"}), 400

    try:
        result, usage = ai_platform.translate_language(
            source_word, source_sentence, source_lang_name, target_lang_name,
            supplied=data.get("supplied"),sense=str(data.get("sense") or ""),context=str(data.get("context") or "")
        )
    except ai_platform.AiPlatformError as exc:
        _record_translation_request_usage(
            user_id,
            successful=False,
            usage=exc.usage,
        )
        return jsonify({"ok": False, "error": str(exc)}), 502

    if getattr(usage,"provider_calls",1) or getattr(usage,"total_tokens",0):
        _record_translation_request_usage(user_id, successful=True, usage=usage)

    return jsonify({"ok": True, **result})


# The marketing site (parallellingvo.app) polls this after a popup login to
# decide whether to show "Open app / Log out" instead of "Log in / Sign up".
# It's a cross-origin credentialed fetch, so it needs an explicit CORS
# allow-list (Origin echoed back, not "*", since credentials are involved).
_STATUS_CORS_ORIGINS = {
    "https://parallellingvo.app",
    "https://www.parallellingvo.app",
}


@web.get("/auth/status")
def auth_status():
    authenticated = bool(session.get("is_auth"))
    resp = jsonify({
        "authenticated": authenticated,
        "user": {
            "id": session.get("tg_user_id"),
            "first_name": session.get("tg_first_name"),
            "last_name": session.get("tg_last_name"),
        } if authenticated else None,
    })
    origin = request.headers.get("Origin")
    if origin in _STATUS_CORS_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Vary"] = "Origin"
    return resp


@web.get("/auth/logout")
def auth_logout():
    session.clear()
    # The marketing site calls this cross-origin via fetch (so the visitor
    # stays on parallellingvo.app instead of being navigated away) — a
    # redirect response here would need CORS headers on the redirect target
    # too, so just report success and let each caller decide what's next.
    # A same-origin caller that wants the old "navigate to next" behaviour
    # can still pass ?next=/path and follow it itself.
    resp = jsonify({"ok": True})
    origin = request.headers.get("Origin")
    if origin in _STATUS_CORS_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Vary"] = "Origin"
    return resp


# --- отладка ---
@web.get("/api/debug/whoami")
def api_debug_whoami():
    return jsonify({
        "session": {
            "is_auth": bool(session.get("is_auth")),
            "tg_user_id": session.get("tg_user_id"),
            "tg_username": session.get("tg_username"),
            "tg_first_name": session.get("tg_first_name"),
            "tg_last_name": session.get("tg_last_name"),
        },
        "headers": {
            "X-User-Id": request.headers.get("X-User-Id"),
            "User-Agent": request.get_json(silent=True) and request.get_json(silent=True).get("ua") or request.headers.get("User-Agent"),
        }
    })


def init_app(app):
    with _conn() as c:
        migrate_auth_identities(c)
    _ensure_family_schema()

    @app.context_processor
    def inject_i18n():
        language = _current_ui_language()
        return {
            "current_ui_language": language,
            "i18n_catalog": get_catalog(language),
            "legacy_i18n_catalog": get_legacy_catalog(language),
            "t": lambda key, **kwargs: translate(language, key, **kwargs),
        }

    app.register_blueprint(web)
    from app.mcp_api import mcp_api
    app.register_blueprint(mcp_api)
    from app.google_auth import google_bp, init_google_oauth
    app.register_blueprint(google_bp)
    init_google_oauth(app)
    from app.telegram_oauth import telegram_oauth_bp, init_telegram_oauth
    app.register_blueprint(telegram_oauth_bp)
    init_telegram_oauth(app)
