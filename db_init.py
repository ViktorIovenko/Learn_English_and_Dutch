# [ДОБАВЛЕНО v1]
import sqlite3
from config import Config

SCHEMA = """
CREATE TABLE IF NOT EXISTS words (
    id TEXT PRIMARY KEY,                    -- "1.1" (урок.слово)
    lesson INTEGER NOT NULL,                -- номер урока (целое)
    lesson_title TEXT NOT NULL,             -- название урока
    nl_word TEXT NOT NULL,                  -- слово на голландском
    nl_audio TEXT,                          -- ссылка на аудио NL
    en_word TEXT NOT NULL,                  -- перевод на английский
    en_audio TEXT,                          -- ссылка на аудио EN
    ru_word TEXT NOT NULL,                  -- перевод на русский
    ru_audio TEXT,                          -- ссылка на аудио RU
    nl_sentence TEXT,                       -- предложение NL
    en_sentence TEXT,                       -- предложение EN
    ru_sentence TEXT,                       -- предложение RU
    difficult INTEGER DEFAULT 0             -- 0/1 — в «отдельный список»
);

CREATE TABLE IF NOT EXISTS user_custom_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                  -- Telegram user id (строкой)
    source_lang TEXT NOT NULL,              -- 'nl'/'en'/'ru'
    source_text TEXT NOT NULL,
    target_lang TEXT NOT NULL,              -- 'nl'/'en'/'ru'
    target_text TEXT NOT NULL,
    note TEXT DEFAULT NULL,                 -- пояснение
    difficult INTEGER DEFAULT 1,            -- по дефолту попадает в сложные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

DEMO = [
    # id, lesson, lesson_title, nl_word, nl_audio, en_word, en_audio, ru_word, ru_audio,
    # nl_sentence, en_sentence, ru_sentence, difficult
    ("1.1", 1, "Познакомимся", "hallo", "", "hello", "", "привет", "",
     "Hallo! Ik ben Victor.", "Hello! I'm Victor.", "Привет! Я Виктор.", 0),
    ("1.2", 1, "Познакомимся", "dank je", "", "thank you", "", "спасибо", "",
     "Dank je voor je hulp.", "Thank you for your help.", "Спасибо за помощь.", 0),
    ("2.1", 2, "Где ты живешь?", "stad", "", "city", "", "город", "",
     "Mijn stad is groot.", "My city is big.", "Мой город большой.", 1),
]

def main():
    conn = sqlite3.connect(Config.DB_PATH)
    c = conn.cursor()
    c.executescript(SCHEMA)
    # idempotent insert
    for row in DEMO:
        c.execute("SELECT 1 FROM words WHERE id = ?", (row[0],))
        if not c.fetchone():
            c.execute("""
                INSERT INTO words (
                    id, lesson, lesson_title, nl_word, nl_audio, en_word, en_audio, ru_word, ru_audio,
                    nl_sentence, en_sentence, ru_sentence, difficult
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
    conn.commit()
    conn.close()
    print("DB initialized at:", Config.DB_PATH)

if __name__ == "__main__":
    main()
