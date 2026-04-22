# app/models.py
# [ДОБАВЛЕНО v2] Модельный слой на sqlite3: уроки, скрытие уроков для каждого Telegram-пользователя.
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime


def _conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_user_tables(db_path: str) -> None:
    """Создаём таблицу пользовательских предпочтений (если ещё нет)."""
    with _conn(db_path) as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS user_lessons (
            user_id TEXT NOT NULL,
            lesson  TEXT NOT NULL,
            hidden  INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, lesson)
        );
        """)
        cols = [r["name"] for r in c.execute("PRAGMA table_info(user_lessons)")]
        if "updated_at_ts" not in cols:
            c.execute("ALTER TABLE user_lessons ADD COLUMN updated_at_ts INTEGER;")
            c.execute("""
                UPDATE user_lessons
                SET updated_at_ts = (
                    COALESCE(
                        CAST(strftime('%s', replace(substr(updated_at,1,19),'T',' ')) AS INTEGER),
                        CAST(strftime('%s','now') AS INTEGER)
                    ) * 1000
                )
                WHERE updated_at_ts IS NULL;
            """)
        c.commit()


def get_lessons(db_path: str, user_id: Optional[str]) -> List[Dict[str, Any]]:
    """
    Возвращает список уроков с количеством слов и флагом hidden для данного пользователя.
    [ИЗМЕНЕНО v3] Дополнительно вычисляет lesson_index из words.number (число ДО первой точки).
    Сортировка: видимые → скрытые; затем по lesson_index; затем по названию.
    """
    ensure_user_tables(db_path)
    if not user_id:
        return []
    with _conn(db_path) as c:
        rows = c.execute("""
            SELECT
                w.lesson AS lesson,
                COUNT(*) AS words_count,
                MIN(
                    CAST(
                        SUBSTR(w.number, 1, INSTR(w.number || '.', '.') - 1) AS INTEGER
                    )
                ) AS lesson_index
            FROM words w
            WHERE (w.user_id = ? OR w.status = 'test')
            GROUP BY w.lesson
        """, (str(user_id),)).fetchall()

        # подтянуть hidden для юзера
        hidden_map = {}
        if user_id:
            for r in c.execute("SELECT lesson, hidden FROM user_lessons WHERE user_id = ?", (str(user_id),)):
                hidden_map[r["lesson"]] = int(r["hidden"])

        lessons: List[Dict[str, Any]] = []
        for r in rows:
            lessons.append({
                "lesson": r["lesson"],                           # исходное название
                "lesson_title": r["lesson"],                     # совместимость
                "words_count": r["words_count"],
                "lesson_index": int(r["lesson_index"] or 0),     # [ДОБАВЛЕНО]
                "hidden": hidden_map.get(r["lesson"], 0)
            })

        # Сортировка: hidden → lesson_index → title
        def _lesson_key(item):
            return (
                item["hidden"],
                item.get("lesson_index", 0),
                (item["lesson"] or "")
            )
        lessons.sort(key=_lesson_key)
        return lessons


def get_user_lessons(db_path: str, user_id: Optional[str]) -> List[Dict[str, Any]]:
    """Возвращает список уроков, загруженных текущим пользователем."""
    if not user_id:
        return []
    with _conn(db_path) as c:
        rows = c.execute("""
            SELECT
                w.lesson AS lesson,
                COUNT(*) AS words_count,
                MIN(
                    CAST(
                        SUBSTR(w.number, 1, INSTR(w.number || '.', '.') - 1) AS INTEGER
                    )
                ) AS lesson_index
            FROM words w
            WHERE w.user_id = ? AND COALESCE(w.lesson, '') != ''
            GROUP BY w.lesson
        """, (str(user_id),)).fetchall()

        lessons: List[Dict[str, Any]] = []
        for r in rows:
            lessons.append({
                "lesson": r["lesson"],
                "lesson_title": r["lesson"],
                "words_count": r["words_count"],
                "lesson_index": int(r["lesson_index"] or 0),
            })

        lessons.sort(key=lambda item: (item.get("lesson_index", 0), (item.get("lesson") or "")))
        return lessons


def set_lesson_hidden(db_path: str, user_id: str, lesson: str, hidden: int) -> None:
    """Пометить урок скрытым/видимым для пользователя."""
    ensure_user_tables(db_path)
    with _conn(db_path) as c:
        now_iso = datetime.utcnow().isoformat()
        now_ts = int(datetime.utcnow().timestamp() * 1000)
        c.execute("""
            INSERT INTO user_lessons (user_id, lesson, hidden, updated_at, updated_at_ts)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, lesson) DO UPDATE SET
                hidden=excluded.hidden,
                updated_at=excluded.updated_at,
                updated_at_ts=excluded.updated_at_ts
        """, (str(user_id), lesson, int(hidden), now_iso, now_ts))
        c.commit()


def get_lesson_words(db_path: str, lesson: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Все слова конкретного урока (для страницы урока)."""
    if not user_id:
        return []
    with _conn(db_path) as c:
        rows = c.execute("""
            SELECT
                id,
                lesson,
                number,
                nl   AS nl_word,
                en   AS en_word,
                ru   AS ru_word,
                ex_nl AS nl_sentence,
                ex_en AS en_sentence,
                ex_ru AS ru_sentence,
                audio_nl AS nl_audio,
                audio_en AS en_audio,
                audio_ru AS ru_audio
            FROM words
            WHERE (user_id = ? OR status = 'test') AND lesson = ?
            ORDER BY number
        """, (str(user_id), lesson)).fetchall()
        return [dict(r) for r in rows]


# ------------------------------ НОВОЕ ------------------------------
# [ДОБАВЛЕНО v8.17] Следующий видимый урок по «текущему» названию
def get_next_lesson_title(db_path: str, current_lesson: str, user_id: Optional[str]) -> Optional[str]:
    """
    Возвращает название следующего ВИДИМОГО урока (hidden=0) в порядке, который
    используется на главной: hidden → lesson_index → lesson.
    Если current_lesson не найден — вернёт первый видимый.
    Если видимых нет — None.
    """
    lessons = get_lessons(db_path, user_id)
    visible = [x for x in lessons if int(x.get("hidden", 0)) == 0]
    if not visible:
        return None
    # найти позицию текущего среди всех (учтём, что он мог быть скрыт)
    try:
        i = next(i for i, x in enumerate(visible) if (x.get("lesson") or "") == (current_lesson or ""))
    except StopIteration:
        # если текущего нет среди видимых — просто первый видимый
        return visible[0]["lesson"]
    nxt = (i + 1) % len(visible)
    return visible[nxt]["lesson"]
# -------------------------------------------------------------------
