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
        c.commit()

def get_lessons(db_path: str, user_id: Optional[str]) -> List[Dict[str, Any]]:
    """
    Возвращает список уроков с количеством слов и флагом hidden для данного пользователя.
    [ИЗМЕНЕНО v3] Дополнительно вычисляет lesson_index из words.number (число ДО первой точки).
    Сортировка: видимые → скрытые; затем по lesson_index; затем по названию.
    """
    ensure_user_tables(db_path)
    with _conn(db_path) as c:
        # Вытягиваем:
        # - title из w.lesson (как есть — это твоё «Familie (1)», «Ik, jij, wij» и т.п.)
        # - words_count
        # - lesson_index = MIN(первое число из колонки number), например для "2.3" → 2
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
            GROUP BY w.lesson
        """).fetchall()

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

def set_lesson_hidden(db_path: str, user_id: str, lesson: str, hidden: int) -> None:
    """Пометить урок скрытым/видимым для пользователя."""
    ensure_user_tables(db_path)
    with _conn(db_path) as c:
        c.execute("""
            INSERT INTO user_lessons (user_id, lesson, hidden, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, lesson) DO UPDATE SET
                hidden=excluded.hidden,
                updated_at=excluded.updated_at
        """, (str(user_id), lesson, int(hidden), datetime.utcnow().isoformat()))
        c.commit()

def get_lesson_words(db_path: str, lesson: str) -> List[Dict[str, Any]]:
    """Все слова конкретного урока (для страницы урока)."""
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
            WHERE lesson = ?
            ORDER BY number
        """, (lesson,)).fetchall()
        return [dict(r) for r in rows]
