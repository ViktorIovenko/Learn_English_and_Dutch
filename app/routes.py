# app/routes.py
from __future__ import annotations
from flask import Blueprint, request, jsonify, render_template, session
import sqlite3
from typing import Any, List, Dict
from config import Config
from app.telegram_auth import verify_telegram_init_data
from app import models

# [ДОБАВЛЕНО v7.0] генерация аудио
from app.audio_gen import ensure_audio_for_ids  # ← НОВОЕ

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

# --- [ИЗМЕНЕНО v6.4] миграция схемы: персональные флаги; УБРАНЫ кастомные слова ---
def _ensure_schema() -> None:
    with _conn() as c:
        # (1) на всякий случай колонка difficult в words (оставляем как legacy)
        cols = [r["name"] for r in c.execute("PRAGMA table_info(words)")]
        if "difficult" not in cols:
            c.execute("ALTER TABLE words ADD COLUMN difficult INTEGER NOT NULL DEFAULT 0;")
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

# --- страницы ---
@web.route("/")
def home():
    return render_template("index.html", title="Уроки", display_name=_display_name_for_request())

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
    # Страница «Сложные слова» (как урок)
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

@web.get("/api/me")
def api_me():
    if session.get("is_auth"):
        return jsonify({
            "ok": True, "auth": True,
            "user_id": session.get("tg_user_id"),
            "username": session.get("tg_username"),
            "first_name": session.get("tg_first_name") or "",
            "last_name": session.get("tg_last_name") or "",
        })
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
        _upsert_user_minimal(str(uid))
        return jsonify({
            "ok": True, "auth": True,
            "user_id": str(uid),
            "username": "",
            "first_name": "",
            "last_name": "",
        })
    return jsonify({"ok": False, "auth": False})

# --- API уроков/слов (ИЗМЕНЕНО: difficult берём из user_word_flags) ---
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
    _ensure_schema()  # [не менялось]
    lesson = (request.args.get("lesson") or "").strip()
    uid = _current_user_id() or ""
    if not lesson:
        return jsonify({"ok": False, "error": "lesson_required"}), 400
    with _conn() as c:
        rows = c.execute(f"""
            SELECT w.id, w.lesson, w.number,
                   w.nl AS nl_word, w.en AS en_word, w.ru AS ru_word,
                   w.ex_nl AS nl_sentence, w.ex_en AS en_sentence, w.ex_ru AS ru_sentence,
                   w.audio_nl AS nl_audio, w.audio_en AS en_audio, w.audio_ru AS ru_audio,
                   COALESCE(uf.difficult, 0) AS difficult
            FROM words w
            LEFT JOIN user_word_flags uf
              ON uf.word_id = w.id AND uf.user_id = ?
            WHERE w.lesson = ?
            ORDER BY w.number
        """, (uid, lesson)).fetchall()
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
    return jsonify({"ok": True, "items": items})

@web.get("/api/lessons/<int:lesson_id>/words")
def api_lesson_words(lesson_id: int):
    _ensure_schema()
    lang = (request.args.get("lang") or "nl").lower()
    uid = _current_user_id() or ""
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
            WHERE w.lesson = ?
            ORDER BY w.number
        """, (uid, str(lesson_id))).fetchall()
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

# --- [ИЗМЕНЕНО v6.4] Список сложных слов ДЛЯ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ (без custom)
@web.get("/api/difficult_words_user")
def api_difficult_words_user():
    """
    Персональный список:
      - слова из words, у которых user_word_flags.difficult=1 для текущего пользователя
      (кастомные слова удалены)
    """
    _ensure_schema()
    uid = _current_user_id() or ""
    if not uid:
        return jsonify({"ok": True, "items": []})
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
            ORDER BY w.lesson, w.number
        """, (uid,)).fetchall()
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

# --- [ДОБАВЛЕНО v6.3] Установить/снять флаг difficult ДЛЯ ПОЛЬЗОВАТЕЛЯ ---
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

# --- Глобальный (legacy) — оставлен для совместимости со старым фронтом ---
@web.post("/api/difficult/set")
def api_difficult_set_legacy():
    """
    Старый endpoint, меняющий глобальное поле words.difficult.
    Оставлен для обратной совместимости. Новый фронт НЕ ДОЛЖЕН его вызывать.
    """
    _ensure_schema()
    data = request.get_json(silent=True) or {}
    try:
        id_ = int(data.get("id"))
    except Exception:
        return jsonify({"ok": False, "error": "bad_id"}), 400
    difficult = 1 if str(data.get("difficult")) in ("1","true","True","on") else 0
    with _conn() as c:
        c.execute("UPDATE words SET difficult=? WHERE id=?", (difficult, id_))
        c.commit()
    return jsonify({"ok": True})

# ----------------- [ДОБАВЛЕНО v7.0] AUDIO ENSURE -----------------
@web.post("/api/audio/ensure")
def api_audio_ensure():
    """
    Body: { ids: [int,...], langs: ["nl","en","ru"] }
    Для каждого id создаёт недостающие MP3, обновляет ссылки в words.audio_*.
    Возвращает { ok: true, items: [ {ok,id,nl,en,ru}, ... ] }
    """
    data = request.get_json(silent=True) or {}
    ids = data.get("ids") or []
    langs = data.get("langs") or ["nl", "en", "ru"]
    try:
        result = ensure_audio_for_ids(Config.DB_PATH, ids, langs)
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
# ---------------------------------------------------------------

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
            "User-Agent": request.headers.get("User-Agent"),
        }
    })

def init_app(app):
    app.register_blueprint(web)
