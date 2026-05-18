# app/routes.py
from __future__ import annotations
import json
import time
import secrets
import html
from urllib.parse import urlencode
from urllib import request as urlrequest
from flask import Blueprint, request, jsonify, render_template, session, send_from_directory, current_app, redirect
import sqlite3
from typing import Any, List, Dict
from pathlib import Path
from config import Config
from app.telegram_auth import verify_telegram_init_data
from app.auth_links import verify_auth_token
from app import models
# [ДОБАВЛЕНО v7.0] генерация аудио
from app.audio_gen import ensure_audio_for_ids  # ← НОВОЕ

web = Blueprint("web", __name__)

LANGUAGE_OPTIONS = [
    {"code": "nl", "name": "Nederlands", "native": "Nederlands"},
    {"code": "en", "name": "English", "native": "English"},
    {"code": "ru", "name": "Russian", "native": "Русский"},
    {"code": "de", "name": "German", "native": "Deutsch"},
    {"code": "fr", "name": "French", "native": "Français"},
    {"code": "es", "name": "Spanish", "native": "Español"},
    {"code": "it", "name": "Italian", "native": "Italiano"},
    {"code": "pt", "name": "Portuguese", "native": "Português"},
    {"code": "pl", "name": "Polish", "native": "Polski"},
    {"code": "uk", "name": "Ukrainian", "native": "Українська"},
    {"code": "tr", "name": "Turkish", "native": "Türkçe"},
    {"code": "ar", "name": "Arabic", "native": "العربية"},
]
LANGUAGE_CODES = {item["code"] for item in LANGUAGE_OPTIONS}


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
    return str(
        session.get("tg_user_id")
        or request.headers.get("X-User-Id")
        or request.args.get("uid")
        or ""
    ).strip()


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
    with _conn() as c:
        existed = bool(c.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone())
        c.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, is_active)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
              username=excluded.username,
              first_name=excluded.first_name,
              last_name=excluded.last_name,
              is_active=1
        """, (user_id,
              user.get("username") or "",
              user.get("first_name") or "",
              user.get("last_name") or ""))
        c.commit()
    return not existed


def _upsert_user_minimal(user_id: str) -> bool:
    if not user_id:
        return False
    with _conn() as c:
        existed = bool(c.execute("SELECT 1 FROM users WHERE user_id=?", (str(user_id),)).fetchone())
        c.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, is_active)
            VALUES (?, '', '', '', 1)
            ON CONFLICT(user_id) DO NOTHING
        """, (str(user_id),))
        c.commit()
    return not existed


def _current_user_id() -> str | None:
    uid = session.get("tg_user_id") or request.headers.get("X-User-Id") or None
    if uid:
        uid = str(uid)
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
        c.commit()


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
    return 3 <= count <= 4


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
                "SELECT 1 FROM words WHERE audio_nl=? OR audio_en=? OR audio_ru=? LIMIT 1",
                (url, url, url),
            ).fetchone()
            if used:
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


@web.route("/settings")
def settings_page():
    return render_template(
        "settings.html",
        title="Настройки",
        hide_timer=True,
        language_options=LANGUAGE_OPTIONS,
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
    with _conn() as c:
        users = [dict(r) for r in c.execute("""
            SELECT user_id, username, first_name, last_name, is_active, created_at
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
        })

    return render_template(
        "admin_users.html",
        title="Пользователи",
        hide_timer=True,
        access_pending=False,
        access_denied=False,
        users=rows,
        admin_user_id=admin_user_id,
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

    with _conn() as c:
        rows = c.execute("""
            SELECT lesson, number, nl, en, ru
            FROM words
            WHERE (user_id = ? OR status = 'test') AND COALESCE(lesson, '') != ''
            ORDER BY lesson, number
        """, (str(user_id),)).fetchall()

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        grouped.setdefault(r["lesson"], []).append({
            "nl": r["nl"] or "",
            "en": r["en"] or "",
            "ru": r["ru"] or "",
        })

    lessons = [
        {"lesson": lesson, "words_count": len(words), "words": words}
        for lesson, words in grouped.items()
    ]
    lessons.sort(key=lambda item: item["lesson"] or "")
    if request.headers.get("X-Client") == "android":
        return jsonify(lessons)
    return jsonify({"ok": True, "lessons": lessons})


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
        return jsonify({"ok": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    lessons_data = data.get("lessons", [])
    if not lessons_data:
        return jsonify({"ok": False, "error": "No data"})

    # Determine next available lesson number
    with _conn() as c:
        row = c.execute(
            """SELECT MAX(CAST(SUBSTR(number, 1,
                CASE WHEN INSTR(number,'.') > 0
                     THEN INSTR(number,'.') - 1
                     ELSE LENGTH(number) END
               ) AS INTEGER)) FROM words WHERE user_id=?""",
            (user_id,)
        ).fetchone()
    next_lesson_num = (row[0] or 0) + 1

    rows: List[Dict] = []
    for lesson_data in lessons_data:
        lesson_name = (lesson_data.get("lesson") or "").strip()
        words = lesson_data.get("words") or []
        if not lesson_name or not words:
            continue
        for word_idx, w in enumerate(words, 1):
            nl = (w.get("nl") or "").strip()
            en = (w.get("en") or "").strip()
            if not nl and not en:
                continue
            rows.append({
                "lesson": lesson_name,
                "number": f"{next_lesson_num}.{word_idx}",
                "nl":     nl,
                "en":     en,
                "ru":     (w.get("ru") or "").strip(),
                "ex_nl":  (w.get("ex_nl") or "").strip(),
                "ex_en":  (w.get("ex_en") or "").strip(),
                "ex_ru":  (w.get("ex_ru") or "").strip(),
                "audio_nl": "", "audio_en": "", "audio_ru": "",
            })
        next_lesson_num += 1

    if not rows:
        return jsonify({"ok": False, "error": "No valid words"})

    from bot.db import bulk_upsert_words
    count = bulk_upsert_words(Config.DB_PATH, user_id, rows)
    return jsonify({"ok": True, "count": count})


@web.get("/api/words")
def api_get_words():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    q        = request.args.get("q", "").strip()
    page     = max(1, int(request.args.get("page", 1) or 1))
    per_page = min(100, max(10, int(request.args.get("per_page", 50) or 50)))
    offset   = (page - 1) * per_page
    with _conn() as c:
        include_test = request.headers.get("X-Client") == "android"
        if include_test:
            base = "FROM words WHERE (user_id=? OR status='test')"
        else:
            base = "FROM words WHERE user_id=?"
        params: list = [str(user_id)]
        if q:
            base  += " AND (nl LIKE ? OR en LIKE ? OR ru LIKE ? OR lesson LIKE ?)"
            p      = f"%{q}%"
            params += [p, p, p, p]
        total = c.execute(f"SELECT COUNT(*) {base}", params).fetchone()[0]
        rows  = c.execute(
            f"SELECT id,lesson,number,nl,en,ru,ex_nl,ex_en,ex_ru,"
            f"audio_nl,audio_en,audio_ru,difficult,status,user_id {base} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()
    words = []
    for r in rows:
        d = dict(r)
        d["difficult"] = bool(d.get("difficult"))
        d["editable"] = (d.get("user_id") or "") == str(user_id) or d.get("status") == "test"
        d.pop("user_id", None)
        words.append(d)
    return jsonify({"ok": True, "words": words,
                    "total": total, "page": page,
                    "pages": max(1, (total + per_page - 1) // per_page)})


@web.put("/api/words/<int:word_id>")
def api_update_word(word_id: int):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    data    = request.get_json(silent=True) or {}
    allowed = {"lesson", "number", "nl", "en", "ru", "ex_nl", "ex_en", "ex_ru", "difficult"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({"ok": False, "error": "No valid fields"}), 400

    # When a translated text field changes, clear its audio URL and delete the old file
    TEXT_AUDIO_MAP = {"nl": "audio_nl", "en": "audio_en", "ru": "audio_ru"}
    old_audio_urls: List[str] = []

    with _conn() as c:
        old = c.execute(
            """
            SELECT nl, en, ru, audio_nl, audio_en, audio_ru
            FROM words
            WHERE id=? AND (user_id=? OR status='test')
            """,
            (word_id, str(user_id))
        ).fetchone()
        if not old:
            return jsonify({"ok": False, "error": "Not found or not authorized"}), 404

        for text_col, audio_col in TEXT_AUDIO_MAP.items():
            if text_col in updates:
                old_val = (old[text_col] or "").strip()
                new_val = str(updates[text_col] or "").strip()
                if old_val != new_val:
                    old_url = (old[audio_col] or "").strip()
                    if old_url:
                        old_audio_urls.append(old_url)
                    updates[audio_col] = ""

        updates["updated_at"] = int(time.time() * 1000)
        set_clause = ", ".join(f"{k}=?" for k in updates)
        c.execute(
            f"UPDATE words SET {set_clause} WHERE id=? AND (user_id=? OR status='test')",
            list(updates.values()) + [word_id, str(user_id)]
        )
        c.commit()

        row = c.execute("""
            SELECT w.id, w.lesson, w.number,
                   w.nl AS nl_word, w.en AS en_word, w.ru AS ru_word,
                   w.ex_nl AS nl_sentence, w.ex_en AS en_sentence, w.ex_ru AS ru_sentence,
                   w.audio_nl AS nl_audio, w.audio_en AS en_audio, w.audio_ru AS ru_audio,
                   COALESCE(uf.difficult, 0) AS difficult
            FROM words w
            LEFT JOIN user_word_flags uf ON uf.word_id = w.id AND uf.user_id = ?
            WHERE w.id = ?
        """, (str(user_id), word_id)).fetchone()

    if old_audio_urls:
        _cleanup_audio_files(old_audio_urls)

    if not row:
        return jsonify({"ok": True})

    d = dict(row)
    d["nl"] = d.get("nl_word", "")
    d["en"] = d.get("en_word", "")
    d["ru"] = d.get("ru_word", "")
    d["ex_nl"] = d.get("nl_sentence", "")
    d["ex_en"] = d.get("en_sentence", "")
    d["ex_ru"] = d.get("ru_sentence", "")
    d["audio_nl"] = d.get("nl_audio", "")
    d["audio_en"] = d.get("en_audio", "")
    d["audio_ru"] = d.get("ru_audio", "")
    d["difficult"] = bool(d.get("difficult"))
    d.setdefault("status", "")
    d.setdefault("word_en",        d.get("en_word", ""))
    d.setdefault("translation_ru", d.get("ru_word", ""))
    d.setdefault("translation_nl", d.get("nl_word", ""))
    d.setdefault("audio_en", d.get("en_audio", ""))
    d.setdefault("audio_ru", d.get("ru_audio", ""))
    d.setdefault("audio_nl", d.get("nl_audio", ""))
    d.setdefault("sentence_en", d.get("en_sentence", ""))
    d.setdefault("sentence_ru", d.get("ru_sentence", ""))
    d.setdefault("sentence_nl", d.get("nl_sentence", ""))
    d["editable"] = True
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
    return jsonify({"ok": True, "user_id": user_id})


@web.post("/api/auth/login_android_token")
def login_android_token():
    data = request.get_json(silent=True) or {}
    token = str(data.get("auth", "")).strip()
    user_id = verify_auth_token(token)
    if not user_id:
        return jsonify({"ok": False, "error": "invalid_auth_token"}), 401
    if not _user_exists(user_id):
        return jsonify({"ok": False, "error": "open_telegram_bot_first"}), 403
    return jsonify({"ok": True, "user_id": user_id})


@web.get("/android-auth")
def android_auth_redirect():
    token = str(request.args.get("token", "")).strip()
    if not verify_auth_token(token):
        return jsonify({"ok": False, "error": "invalid_auth_token"}), 401
    base = f"{Config.PUBLIC_BASE_URL}".rstrip("/")
    deep_link = "learnwords://auth?" + urlencode({"server": base, "auth": token})
    return redirect(deep_link)


# --- API: авторизация WebApp ---
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
            "languages_configured": 3 <= len(language_preferences) <= 4,
            "language_preferences": language_preferences,
            "subscription": subscription,
            "is_admin": _is_admin_user_id(uid),
        })
    uid = request.headers.get("X-User-Id")
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
                "languages_configured": 3 <= len(language_preferences) <= 4,
                "language_preferences": language_preferences,
                "subscription": subscription,
                "is_admin": _is_admin_user_id(uid),
            })
        return jsonify({"ok": False, "auth": False, "error": "open_telegram_bot_first"}), 401
    return jsonify({"ok": False, "auth": False})


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

    # ── TODO: Заменить заглушку реальной верификацией через Google Play API ──
    # Сейчас просто помечаем подписку как активную на сервере.
    # В продакшене нужно проверить токен через Google Play Developer API
    # прежде чем активировать подписку!
    GOOGLE_PLAY_VERIFY_STUB = True  # TODO: убрать после реализации

    if GOOGLE_PLAY_VERIFY_STUB:
        expires_at = int(time.time() * 1000) + 30 * 24 * 60 * 60 * 1000  # +30 дней (заглушка)
        with _conn() as c:
            c.execute("""
                INSERT INTO user_subscriptions
                    (user_id, status, current_period_ends_at, provider,
                     provider_subscription_id, updated_at)
                VALUES (?, 'active', ?, 'google_play', ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    status='active',
                    current_period_ends_at=excluded.current_period_ends_at,
                    provider='google_play',
                    provider_subscription_id=excluded.provider_subscription_id,
                    updated_at=excluded.updated_at
            """, (user_id, expires_at, purchase_token, int(time.time() * 1000)))
            c.commit()

        return jsonify({
            "ok": True,
            "status": "active",
            "expires_at": expires_at,
            "note": "STUB — replace with real Google Play API verification"
        })

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
    return jsonify({"ok": True, "languages": LANGUAGE_OPTIONS})


@web.get("/api/user-languages")
def api_user_languages_get():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    languages = _get_user_languages(user_id)
    return jsonify({
        "ok": True,
        "configured": 3 <= len(languages) <= 4,
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

    if len(cleaned) < 3 or len(cleaned) > 4:
        return jsonify({"ok": False, "error": "choose_3_or_4_languages"}), 400

    now_ms = int(time.time() * 1000)
    with _conn() as c:
        c.execute("DELETE FROM user_language_preferences WHERE user_id = ?", (str(user_id),))
        c.executemany("""
            INSERT INTO user_language_preferences (user_id, priority, lang_code, updated_at)
            VALUES (?, ?, ?, ?)
        """, [(str(user_id), idx + 1, code, now_ms) for idx, code in enumerate(cleaned)])
        c.commit()

    languages = _get_user_languages(user_id)
    return jsonify({"ok": True, "configured": True, "languages": languages})


# --- API уроков/слов (ИЗМЕНЕНО: difficult берём из user_word_flags) ---
@web.get("/api/lessons")
def api_lessons():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _ensure_schema()
    lessons = models.get_lessons(Config.DB_PATH, user_id)
    return jsonify(lessons)


@web.get("/api/user_lessons")
def api_user_lessons():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    _ensure_schema()
    lessons = models.get_user_lessons(Config.DB_PATH, user_id)
    return jsonify(lessons)


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
        rows = c.execute(f"""
            SELECT w.id, w.lesson, w.number,
                   w.nl AS nl_word, w.en AS en_word, w.ru AS ru_word,
                   w.ex_nl AS nl_sentence, w.ex_en AS en_sentence, w.ex_ru AS ru_sentence,
                   w.audio_nl AS nl_audio, w.audio_en AS en_audio, w.audio_ru AS ru_audio,
                   COALESCE(uf.difficult, 0) AS difficult,
                   w.status AS status,
                   w.user_id AS _word_owner
            FROM words w
            LEFT JOIN user_word_flags uf
              ON uf.word_id = w.id AND uf.user_id = ?
            WHERE (w.user_id = ? OR w.status = 'test') AND w.lesson = ?
            ORDER BY w.number
        """, (uid, uid, lesson)).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        d["nl"] = d.get("nl_word", "")
        d["en"] = d.get("en_word", "")
        d["ru"] = d.get("ru_word", "")
        d["ex_nl"] = d.get("nl_sentence", "")
        d["ex_en"] = d.get("en_sentence", "")
        d["ex_ru"] = d.get("ru_sentence", "")
        d["audio_nl"] = d.get("nl_audio", "")
        d["audio_en"] = d.get("en_audio", "")
        d["audio_ru"] = d.get("ru_audio", "")
        d["difficult"] = bool(d.get("difficult"))
        d["status"] = d.get("status", "") or ""
        d.setdefault("word_en",        d.get("en_word", ""))
        d.setdefault("translation_ru", d.get("ru_word", ""))
        d.setdefault("translation_nl", d.get("nl_word", ""))
        d.setdefault("audio_en", d.get("en_audio", ""))
        d.setdefault("audio_ru", d.get("ru_audio", ""))
        d.setdefault("audio_nl", d.get("nl_audio", ""))
        d.setdefault("sentence_en", d.get("en_sentence", ""))
        d.setdefault("sentence_ru", d.get("ru_sentence", ""))
        d.setdefault("sentence_nl", d.get("nl_sentence", ""))
        d["editable"] = (d.get("_word_owner") or "") == uid or d.get("status") == "test"
        d.pop("_word_owner", None)
        items.append(d)
    if request.headers.get("X-Client") == "android":
        return jsonify(items)
    return jsonify({"ok": True, "items": items})


@web.get("/api/lessons/<int:lesson_id>/words")
def api_lesson_words(lesson_id: int):
    _ensure_schema()
    lang = (request.args.get("lang") or "nl").lower()
    uid = _current_user_id()
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    with _conn() as c:
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
        """, (uid, uid, str(lesson_id))).fetchall()
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
    uid = _current_user_id()
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    with _conn() as c:
        preset = c.execute("""
            SELECT w.id,
                   w.nl AS nl_word, w.en AS en_word, w.ru AS ru_word,
                   w.ex_nl AS nl_sentence, w.ex_en AS en_sentence, w.ex_ru AS ru_sentence,
                   w.audio_nl AS nl_audio, w.audio_en AS en_audio, w.audio_ru AS ru_audio,
                   1 AS difficult,
                   'preset' AS kind
            FROM words w
            JOIN user_word_flags uf
              ON uf.word_id = w.id AND uf.user_id = ? AND COALESCE(uf.difficult,0)=1
            WHERE (w.user_id = ? OR w.status = 'test')
            ORDER BY w.lesson, w.number
        """, (uid, uid)).fetchall()
    items: List[Dict[str, Any]] = []
    for r in preset:
        d = dict(r)
        d.setdefault("word_en",        d.get("en_word", ""))
        d.setdefault("translation_ru", d.get("ru_word", ""))
        d.setdefault("translation_nl", d.get("nl_word", ""))
        d.setdefault("sentence_en", d.get("en_sentence", ""))
        d.setdefault("sentence_ru", d.get("ru_sentence", ""))
        d.setdefault("sentence_nl", d.get("nl_sentence", ""))
        items.append(d)
    return jsonify({"ok": True, "items": items})


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
        exists = c.execute(
            "SELECT 1 FROM words WHERE id = ? AND (user_id = ? OR status = 'test')",
            (wid, uid)
        ).fetchone()
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
    data = request.get_json(silent=True) or {}
    events = data if isinstance(data, list) else data.get("events")
    if events is None:
        events = []
    if not isinstance(events, list):
        return jsonify({"ok": False, "error": "bad_events"}), 400

    user_id = _current_user_id() or ""
    rows = []
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

    if rows:
        with _conn() as c:
            c.executemany("""
                INSERT INTO progress_events (user_id, scope, event_type, event_ts, payload)
                VALUES (?, ?, ?, ?, ?)
            """, rows)
            c.commit()
    return jsonify({"ok": True, "stored": len(rows)})


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
        return jsonify(result)
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
# ------------------------------------------------------------------


# ─── Admin helpers ───────────────────────────────────────────────────────────

def _require_admin() -> tuple:
    uid = _session_admin_user_id()
    if not uid:
        return None, (jsonify({"ok": False, "error": "unauthorized"}), 401)
    return uid, None


@web.get("/api/admin/users")
def api_admin_users():
    """Список всех пользователей с их статусом подписки. Только для админов."""
    uid, err = _require_admin()
    if err:
        return err
    _ensure_subscription_schema()
    now_ms = int(time.time() * 1000)
    # 10 лет в мс — порог для определения «безлимитного» доступа
    ten_years_ms = 10 * 365 * 24 * 60 * 60 * 1000
    with _conn() as c:
        rows = c.execute("""
            SELECT
                u.user_id, u.username, u.first_name, u.last_name,
                s.status, s.current_period_ends_at, s.trial_ends_at, s.provider
            FROM users u
            LEFT JOIN user_subscriptions s ON u.user_id = s.user_id
            ORDER BY u.user_id
        """).fetchall()
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
        })
    return jsonify({"ok": True, "users": users})


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

        deletes = [
            ("words", "user_id"),
            ("user_word_flags", "user_id"),
            ("user_lessons", "user_id"),
            ("progress_events", "user_id"),
            ("user_language_preferences", "user_id"),
            ("user_subscriptions", "user_id"),
            ("reminder_state", "user_id"),
            ("shared_word_sets", "owner_user_id"),
            ("users", "user_id"),
        ]
        for table, column in deletes:
            try:
                c.execute(f"DELETE FROM {table} WHERE {column}=?", (target_uid,))
            except sqlite3.OperationalError:
                pass
        c.commit()

    return jsonify({"ok": True, "user_id": target_uid})


# ─── AI заглушки (Ollama-прокси) ────────────────────────────────────────────
# В веб-версии браузер обращается к Ollama напрямую (localhost:11434).
# В Android-приложении то же — OllamaService обращается напрямую к IP машины.
# Эти эндпоинты — заглушки для будущего проксирования через Flask,
# если нужно скрыть Ollama за сервером или добавить кеш переводов.

@web.post("/api/translate/word")
def api_translate_word():
    """
    ЗАГЛУШКА. Прямой вызов Ollama предпочтителен.
    Для прокси: настроить OLLAMA_URL и OLLAMA_MODEL в .env и раскомментировать код ниже.
    """
    # TODO: реализовать прокси при необходимости
    # import os, requests as req
    # data = request.get_json(silent=True) or {}
    # word = data.get('word', '')
    # from_lang = data.get('from_lang', 'nl')
    # level = data.get('level', 'A2')
    # ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    # ollama_model = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b')
    # prompt = build_translate_prompt(word, from_lang, level)  # TODO: перенести промпт сюда
    # r = req.post(f'{ollama_url}/api/chat', json={...}, timeout=60)
    # return jsonify(r.json()['message']['content'])
    return jsonify({"ok": False, "error": "Not implemented — use Ollama directly"}), 501


@web.post("/api/generate/topic")
def api_generate_topic():
    """
    ЗАГЛУШКА. Прямой вызов Ollama предпочтителен.
    Для прокси: настроить OLLAMA_URL и OLLAMA_MODEL в .env и раскомментировать код ниже.
    """
    # TODO: реализовать прокси при необходимости
    # import os, requests as req
    # data = request.get_json(silent=True) or {}
    # topic = data.get('topic', '')
    # level = data.get('level', 'A2')
    # count = data.get('count', 10)
    # languages = data.get('languages', ['nl', 'en', 'ru'])
    # ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    # ollama_model = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b')
    # prompt = build_generate_topic_prompt(topic, level, count, languages)  # TODO: перенести промпт сюда
    # r = req.post(f'{ollama_url}/api/chat', json={...}, timeout=120)
    # return jsonify(r.json()['message']['content'])
    return jsonify({"ok": False, "error": "Not implemented — use Ollama directly"}), 501


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
    app.register_blueprint(web)
    from app.google_auth import google_bp, init_google_oauth
    app.register_blueprint(google_bp)
    init_google_oauth(app)
