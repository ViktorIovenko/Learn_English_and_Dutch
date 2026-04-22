# app/routes.py
from __future__ import annotations
import json
import time
from flask import Blueprint, request, jsonify, render_template, session, send_from_directory, current_app
import sqlite3
from typing import Any, List, Dict
from pathlib import Path
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
    return render_template("index.html", title="Уроки", display_name=_display_name_for_request())


@web.route("/lessons")  # ←←← [ДОБАВЛЕНО v8.17] алиас, чтобы фронтовый фолбэк не падал 404
def lessons_alias():
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
    return render_template("difficult.html", title="Сложные слова")


@web.route("/upload")
def upload_page():
    return render_template("upload.html", title="Загрузка слов",
                           public_url=Config.PUBLIC_BASE_URL, hide_timer=True)


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
        base   = "FROM words WHERE user_id=?"
        params: list = [str(user_id)]
        if q:
            base  += " AND (nl LIKE ? OR en LIKE ? OR ru LIKE ? OR lesson LIKE ?)"
            p      = f"%{q}%"
            params += [p, p, p, p]
        total = c.execute(f"SELECT COUNT(*) {base}", params).fetchone()[0]
        rows  = c.execute(
            f"SELECT id,lesson,number,nl,en,ru,ex_nl,ex_en,ex_ru,"
            f"audio_nl,audio_en,audio_ru,difficult {base} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()
    return jsonify({"ok": True, "words": [dict(r) for r in rows],
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
    updates["updated_at"] = int(time.time() * 1000)
    set_clause = ", ".join(f"{k}=?" for k in updates)
    with _conn() as c:
        c.execute(f"UPDATE words SET {set_clause} WHERE id=? AND user_id=?",
                  list(updates.values()) + [word_id, str(user_id)])
        c.commit()
    return jsonify({"ok": True})


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
                   COALESCE(uf.difficult, 0) AS difficult
            FROM words w
            LEFT JOIN user_word_flags uf
              ON uf.word_id = w.id AND uf.user_id = ?
            WHERE (w.user_id = ? OR w.status = 'test') AND w.lesson = ?
            ORDER BY w.number
        """, (uid, uid, lesson)).fetchall()
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
    ids = data.get("ids") or []
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
