# [ИЗМЕНЕНО v6.4] Приведён к актуальной схеме words (id INTEGER, lesson TEXT, number TEXT, ...)

import sqlite3
from config import Config
from pathlib import Path

DEMO = [
    # number, lesson, nl, en, ru, ex_nl, ex_en, ex_ru, audio_nl, audio_en, audio_ru, difficult
    ("1.1", "Познакомимся", "hallo", "hello", "привет",
     "Hallo! Ik ben Victor.", "Hello! I'm Victor.", "Привет! Я Виктор.",
     "", "", "", 0),
    ("1.2", "Познакомимся", "dank je", "thank you", "спасибо",
     "Dank je voor je hulp.", "Thank you for your help.", "Спасибо за помощь.",
     "", "", "", 0),
    ("2.1", "Где ты живешь?", "stad", "city", "город",
     "Mijn stad is groot.", "My city is big.", "Мой город большой.",
     "", "", "", 1),
]

SCHEMA_ACTUAL = """
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson     TEXT,
    number     TEXT,
    nl         TEXT,
    en         TEXT,
    ru         TEXT,
    ex_nl      TEXT,
    ex_en      TEXT,
    ex_ru      TEXT,
    audio_nl   TEXT,
    audio_en   TEXT,
    audio_ru   TEXT
);
"""

def _conn():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_words_schema(conn: sqlite3.Connection) -> None:
    # Создадим базовую таблицу, если её нет (актуальная структура)
    conn.executescript(SCHEMA_ACTUAL)

    # Индексы
    conn.execute("CREATE INDEX IF NOT EXISTS idx_words_lesson ON words(lesson);")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS u_words_number ON words(number);")

    # Колонка difficult (если отсутствует) — как в приложении
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(words)")]
    if "difficult" not in cols:
        conn.execute("ALTER TABLE words ADD COLUMN difficult INTEGER NOT NULL DEFAULT 0;")

def _insert_demo(conn: sqlite3.Connection) -> None:
    # Идемпотентная вставка/обновление демо-записей по UNIQUE(number)
    conn.executemany(
        """
        INSERT INTO words (
            lesson, number, nl, en, ru, ex_nl, ex_en, ex_ru, audio_nl, audio_en, audio_ru, difficult
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(number) DO UPDATE SET
            lesson=excluded.lesson,
            nl=excluded.nl,
            en=excluded.en,
            ru=excluded.ru,
            ex_nl=excluded.ex_nl,
            ex_en=excluded.ex_en,
            ex_ru=excluded.ex_ru,
            audio_nl=excluded.audio_nl,
            audio_en=excluded.audio_en,
            audio_ru=excluded.audio_ru,
            difficult=excluded.difficult
        """,
        [(row[1], row[0], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11]) for row in DEMO]
    )

def main():
    # Убедимся, что директория БД существует
    Path(Config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    conn = _conn()
    try:
        _ensure_words_schema(conn)
        _insert_demo(conn)
        conn.commit()
        print("DB initialized at:", Config.DB_PATH)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
