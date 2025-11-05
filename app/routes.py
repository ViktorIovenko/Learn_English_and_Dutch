# app/routes.py
from __future__ import annotations
from flask import Blueprint, request, jsonify, render_template, session
import sqlite3
from typing import Any, List, Dict
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

# --- [ИЗМЕНЕНО v6.3] миграция схемы: персональные флаги + кастомные слова ---
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
        # (3) пользовательские произвольные слова
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_custom_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT NOT NULL,
                source_lang TEXT NOT NULL,
                source_text TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                target_text TEXT NOT NULL,
                note        TEXT DEFAULT NULL,
                difficult   INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
    _ensure_schema()  # [ИЗМЕНЕНО v6.3]
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
                   COALESCE(uf.difficult, 0) AS difficult   -- [ИЗМЕНЕНО v6.3]
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
    _ensure_schema()  # [ИЗМЕНЕНО v6.3]
    lang = (request.args.get("lang") or "nl").lower()
    uid = _current_user_id() or ""
    with _conn() as c:
        rows = c.execute("""
            SELECT w.id,
                   w.nl AS nl_word, w.en AS en_word, w.ru AS ru_word,
                   w.ex_nl AS nl_sentence, w.ex_en AS en_sentence, w.ex_ru AS ru_sentence,
                   w.audio_nl AS nl_audio, w.audio_en AS en_audio, w.audio_ru AS ru_audio,
                   COALESCE(uf.difficult, 0) AS difficult   -- [ИЗМЕНЕНО v6.3]
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

# --- [ДОБАВЛЕНО v6.3] Список сложных слов ДЛЯ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ ---
@web.get("/api/difficult_words_user")
def api_difficult_words_user():
    """
    Персональный список:
      - слова из words, у которых user_word_flags.difficult=1 для текущего пользователя
      - пользовательские слова (user_custom_words) с difficult=1 для пользователя
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

        custom = c.execute("""
            SELECT id, user_id, source_lang, source_text, target_lang, target_text, note, difficult,
                   'custom' AS kind
            FROM user_custom_words
            WHERE user_id=? AND COALESCE(difficult,0)=1
            ORDER BY created_at DESC, id DESC
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

    for r in custom:
        rr = dict(r)
        mapped = {
            "id": f"c_{rr['id']}",
            "nl_word": "", "en_word": "", "ru_word": "",
            "nl_sentence": "", "en_sentence": "", "ru_sentence": "",
            "nl_audio": "", "en_audio": "", "ru_audio": "",
            "difficult": 1,
            "kind": "custom",
        }
        sl, tl = (rr.get("source_lang") or "").lower(), (rr.get("target_lang") or "").lower()
        st, tt = rr.get("source_text") or "", rr.get("target_text") or ""
        if sl == "nl": mapped["nl_word"] = st
        if sl == "en": mapped["en_word"] = st
        if sl == "ru": mapped["ru_word"] = st
        if tl == "nl": mapped["translation_nl"] = tt
        if tl == "en": mapped["word_en"]        = tt
        if tl == "ru": mapped["translation_ru"] = tt
        items.append(mapped)

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
            # при снятии отметки — ставим difficult=0 (не удаляем запись, чтобы можно было анализировать историю)
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

# --- Пользовательские слова ---
@web.post("/api/custom_words/add")
def api_custom_add():
    _ensure_schema()
    data = request.get_json(silent=True) or {}
    uid = _current_user_id() or (data.get("user_id") or "").strip() or ""
    if not uid:
        return jsonify({"ok": False, "error": "no_user"}), 400
    src_lang = (data.get("source_lang") or "").strip().lower()
    src_text = (data.get("source_text") or "").strip()
    tgt_lang = (data.get("target_lang") or "").strip().lower()
    tgt_text = (data.get("target_text") or "").strip()
    note     = (data.get("note") or "").strip()
    if not (src_lang and src_text and tgt_lang and tgt_text):
        return jsonify({"ok": False, "error": "fields_required"}), 400
    with _conn() as c:
        c.execute("""
            INSERT INTO user_custom_words (user_id, source_lang, source_text, target_lang, target_text, note, difficult)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (uid, src_lang, src_text, tgt_lang, tgt_text, note))
        c.commit()
    return jsonify({"ok": True})

@web.post("/api/custom_words/set_difficult")
def api_custom_set_difficult():
    _ensure_schema()
    data = request.get_json(silent=True) or {}
    try:
        id_ = int(data.get("id"))
    except Exception:
        return jsonify({"ok": False, "error": "bad_id"}), 400
    difficult = 1 if str(data.get("difficult")) in ("1","true","True","on") else 0
    uid = _current_user_id() or ""
    with _conn() as c:
        if uid:
            c.execute("UPDATE user_custom_words SET difficult=? WHERE id=? AND user_id=?", (difficult, id_, uid))
        else:
            c.execute("UPDATE user_custom_words SET difficult=? WHERE id=?", (difficult, id_))
        c.commit()
    return jsonify({"ok": True})

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
