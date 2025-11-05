# app/routes.py
from __future__ import annotations
from flask import Blueprint, request, jsonify, render_template, session
import sqlite3
from typing import Any
from config import Config
from app.telegram_auth import verify_telegram_init_data
from app import models

web = Blueprint("web", __name__)

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _upsert_user(user: dict[str, Any]) -> None:
    with _conn() as c:
        c.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, is_active)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
              username=excluded.username,
              first_name=excluded.first_name,
              last_name=excluded.last_name,
              is_active=1
        """, (str(user.get("id") or ""),
              user.get("username") or "",
              user.get("first_name") or "",
              user.get("last_name") or ""))
        c.commit()

def _upsert_user_minimal(user_id: str) -> None:
    """[ДОБАВЛЕНО v5.9] Создать «пустого» пользователя при авторизации только по заголовку."""
    if not user_id:
        return
    with _conn() as c:
        c.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, is_active)
            VALUES (?, '', '', '', 1)
            ON CONFLICT(user_id) DO NOTHING
        """, (str(user_id),))
        c.commit()

def _current_user_id() -> str | None:
    uid = session.get("tg_user_id") or request.headers.get("X-User-Id") or None
    return str(uid) if uid else None

# --- [ДОБАВЛЕНО v5.7] серверное имя для приветствия ---
def _display_name_for_request() -> str:
    first = (session.get("tg_first_name") or "").strip()
    if first:
        return first
    usern = (session.get("tg_username") or "").strip()
    if usern:
        return f"@{usern}"
    uid = request.headers.get("X-User-Id")
    if uid:
        with _conn() as c:
            row = c.execute(
                "SELECT first_name, username FROM users WHERE user_id=?",
                (str(uid),)
            ).fetchone()
        if row:
            first = (row["first_name"] or "").strip()
            if first:
                return first
            usern = (row["username"] or "").strip()
            if usern:
                return f"@{usern}"
    return ""

# --- страницы ---
@web.route("/")
def home():
    return render_template("index.html", title="Уроки", display_name=_display_name_for_request())

@web.route("/lesson/<int:lesson_id>")
def lesson_page(lesson_id: int):
    return render_template("lesson.html", title=f"Урок {lesson_id}", lesson_id=lesson_id)

@web.route("/difficult")
def difficult_page():
    return render_template("difficult.html", title="Сложные слова")

# --- API: авторизация WebApp ---
@web.post("/api/auth/login_webapp")
def login_webapp():
    data = request.get_json(silent=True) or {}
    init_data = data.get("init_data", "")
    v = verify_telegram_init_data(init_data, Config.BOT_TOKEN)
    if not v or not isinstance(v.get("user"), dict):
        return jsonify({"ok": False, "error": "invalid_init_data"}), 401
    user = v["user"]
    _upsert_user(user)
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

# --- API: проверка авторизации ---
@web.get("/api/me")
def api_me():
    # Вариант 1: WebApp-сессия
    if session.get("is_auth"):
        return jsonify({
            "ok": True, "auth": True,
            "user_id": session.get("tg_user_id"),
            "username": session.get("tg_username"),
            "first_name": session.get("tg_first_name") or "",
            "last_name": session.get("tg_last_name") or "",
        })
    # Вариант 2: Фолбэк по X-User-Id (например, если initData не пришёл)
    uid = request.headers.get("X-User-Id")
    if uid:
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
            })
        # [ДОБАВЛЕНО v5.9] если записи нет — создаём «пустую» и авторизуем
        _upsert_user_minimal(str(uid))
        return jsonify({
            "ok": True, "auth": True,
            "user_id": str(uid),
            "username": "",
            "first_name": "",
            "last_name": "",
        })
    return jsonify({"ok": False, "auth": False})

# --- API уроков/слов ---
@web.get("/api/lessons")
def api_lessons():
    user_id = _current_user_id()
    lessons = models.get_lessons(Config.DB_PATH, user_id)
    return jsonify(lessons)

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
    lesson = (request.args.get("lesson") or "").strip()
    if not lesson:
        return jsonify({"ok": False, "error": "lesson_required"}), 400
    with _conn() as c:
        rows = c.execute("""
            SELECT id, lesson, number,
                   nl   AS nl_word, en AS en_word, ru AS ru_word,
                   ex_nl AS nl_sentence, ex_en AS en_sentence, ex_ru AS ru_sentence,
                   audio_nl AS nl_audio, audio_en AS en_audio, audio_ru AS ru_audio
            FROM words
            WHERE lesson = ?
            ORDER BY number
        """, (lesson,)).fetchall()
    return jsonify({"ok": True, "items": [dict(r) for r in rows]})

@web.get("/api/lessons/<int:lesson_id>/words")
def api_lesson_words(lesson_id: int):
    lang = (request.args.get("lang") or "nl").lower()
    with _conn() as c:
        rows = c.execute("""
            SELECT id,
                   nl AS nl_word, en AS en_word, ru AS ru_word,
                   ex_nl AS nl_sentence, ex_en AS en_sentence, ex_ru AS ru_sentence,
                   audio_nl AS nl_audio, audio_en AS en_audio, audio_ru AS ru_audio,
                   0 AS difficult
            FROM words
            WHERE lesson = ?
            ORDER BY number
        """, (str(lesson_id),)).fetchall()
    items = [dict(r) for r in rows]
    return jsonify({"lang": lang, "items": items})

# [ДОБАВЛЕНО v5.9] Простой отладочный эндпоинт
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
            "User-Agent": request.headers.get("User-Agent"),
        }
    })

def init_app(app):
    app.register_blueprint(web)
