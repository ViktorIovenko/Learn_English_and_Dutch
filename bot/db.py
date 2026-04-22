# bot/db.py
# Универсальная работа с SQLite: поддержка двух вариантов схемы users
# 1) Старая:  users(tg_id, username, first_name, is_registered, registered_at)
# 2) Новая:   users(user_id, username, first_name, last_name, is_active, created_at)
# Плюс массовая загрузка слов (таблица words совместима в обеих ветках).

import os
import sqlite3
from datetime import datetime
from typing import Iterable, Dict, Any, Tuple, List

# ---------------- ВСПОМОГАТЕЛЬНОЕ ----------------

def _conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def _users_columns(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute("PRAGMA table_info(users)").fetchall()
    return [r["name"] for r in rows]

def _users_schema(conn: sqlite3.Connection) -> str:
    """
    Возвращает 'old' для схемы с tg_id/is_registered,
              'new' для схемы с user_id/is_active,
              'none' если таблицы users нет.
    """
    try:
        cols = _users_columns(conn)
    except sqlite3.OperationalError:
        return "none"
    cols_set = set(cols)
    if not cols_set:
        return "none"
    if {"tg_id", "is_registered"}.issubset(cols_set):
        return "old"
    if {"user_id"}.issubset(cols_set):
        # в новой схеме может не быть last_name, но user_id точно есть
        return "new"
    return "unknown"

# ---------------- РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ ----------------

def is_user_registered(db_path: str, tg_id: int) -> bool:
    """
    Возвращает True, если пользователь зарегистрирован.
    Работает и со старой, и с новой схемой users.
    """
    with _conn(db_path) as conn:
        schema = _users_schema(conn)

        if schema == "old":
            row = conn.execute(
                "SELECT is_registered FROM users WHERE tg_id = ?",
                (tg_id,)
            ).fetchone()
            return bool(row and int(row["is_registered"]) == 1)

        if schema == "new":
            row = conn.execute(
                "SELECT is_active FROM users WHERE user_id = ?",
                (str(tg_id),)
            ).fetchone()
            # В новой схеме считаем зарегистрированным факт наличия строки;
            # is_active (если есть) = 1 — предпочтительно.
            if row is None:
                return False
            try:
                return int(row["is_active"]) == 1
            except Exception:
                return True  # нет поля is_active — но строка есть

        if schema == "unknown":
            # Фоллбек: пробуем по любому из возможных полей
            row = conn.execute(
                "SELECT 1 FROM users WHERE "
                "(user_id = ? OR tg_id = ?) LIMIT 1",
                (str(tg_id), tg_id)
            ).fetchone()
            return bool(row)

        # таблицы нет — считаем незарегистрированным
        return False

def upsert_registered_user(db_path: str, tg_id: int, username: str, first_name: str) -> None:
    """
    Создаёт/обновляет запись о пользователе как зарегистрированную.
    Поддерживает обе схемы.
    """
    now = datetime.utcnow().isoformat()
    with _conn(db_path) as conn:
        schema = _users_schema(conn)

        if schema == "old":
            # старая схема
            try:
                conn.execute(
                    """
                    INSERT INTO users (tg_id, username, first_name, is_registered, registered_at)
                    VALUES (?, ?, ?, 1, ?)
                    """,
                    (tg_id, username, first_name, now),
                )
            except sqlite3.IntegrityError:
                conn.execute(
                    """
                    UPDATE users
                    SET username = ?, first_name = ?, is_registered = 1, registered_at = ?
                    WHERE tg_id = ?
                    """,
                    (username, first_name, now, tg_id),
                )
            conn.commit()
            return

        if schema == "new":
            # новая схема
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, is_active)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    is_active=1
                """,
                (str(tg_id), username, first_name),
            )
            conn.commit()
            return

        # если users нет — создадим новую схему и вставим
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id    TEXT PRIMARY KEY,
                username   TEXT,
                first_name TEXT,
                last_name  TEXT,
                is_active  INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, is_active)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                is_active=1
            """,
            (str(tg_id), username, first_name),
        )
        conn.commit()

# ---------------- СЛОВА ----------------

# [ДОБАВЛЕНО v4.15] Гарантируем уникальность (lesson, number) и чистим дубли, если уже есть
def _ensure_words_unique_pair(conn: sqlite3.Connection) -> None:
    """
    Обеспечивает UNIQUE(lesson, number) в таблице words.
    Если в таблице уже есть дубли, оставляет по одной записи (минимальный rowid).
    """
    # Проверим, существует ли индекс
    idx = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='u_words_user_lesson_number'"
    ).fetchone()
    if idx:
        return
    # Попытка создать индекс — может упасть, если есть дубли
    try:
        conn.execute("""
            CREATE UNIQUE INDEX u_words_user_lesson_number
            ON words(user_id, lesson, number);
        """)
        conn.commit()
        return
    except sqlite3.OperationalError:
        # Вероятно, дубли; удалим все повторы, оставив минимальный rowid
        try:
            conn.execute("""
                DELETE FROM words
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM words
                    GROUP BY user_id, lesson, number
                )
            """)
            conn.commit()
        except Exception:
            # если таблицы нет или иная проблема — пробросим дальше на вставке
            pass
        # Повторная попытка создать индекс
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS u_words_user_lesson_number
            ON words(user_id, lesson, number);
        """)
        conn.commit()


def _ensure_words_user_id(conn: sqlite3.Connection) -> None:
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(words)")]
    if "user_id" not in cols:
        conn.execute("ALTER TABLE words ADD COLUMN user_id TEXT;")
        conn.execute("UPDATE words SET user_id = '' WHERE user_id IS NULL;")
    if "status" not in cols:
        conn.execute("ALTER TABLE words ADD COLUMN status TEXT NOT NULL DEFAULT 'user';")
    conn.execute("""
        UPDATE words
        SET status = 'user'
        WHERE COALESCE(status, '') = ''
    """)
    conn.execute("DROP INDEX IF EXISTS u_words_number;")
    conn.execute("DROP INDEX IF EXISTS idx_words_lesson_number;")
    conn.execute("DROP INDEX IF EXISTS idx_words_user_lesson_number;")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_words_user_lesson ON words(user_id, lesson);")
    conn.commit()


def _ensure_words_updated_at(conn: sqlite3.Connection) -> None:
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(words)")]
    if "updated_at" in cols:
        return
    conn.execute("ALTER TABLE words ADD COLUMN updated_at INTEGER;")
    conn.execute("UPDATE words SET updated_at = (strftime('%s','now') * 1000) WHERE updated_at IS NULL;")
    conn.commit()

def bulk_upsert_words(db_path: str, user_id: str, rows: Iterable[Dict[str, Any]]) -> int:
    """
    Массовая вставка/обновление слов.
    Ожидаются ключи:
      lesson, number, nl, en, ru, ex_nl, ex_en, ex_ru, audio_nl, audio_en, audio_ru
    """
    rows = list(rows)
    user_id = str(user_id or "")
    if not user_id:
        return 0
    if not rows:
        return 0
    with _conn(db_path) as conn:
        try:
            _ensure_words_user_id(conn)
            _ensure_words_updated_at(conn)
        except Exception:
            pass
        # [ДОБАВЛЕНО v4.15] гарантируем UNIQUE(lesson, number) перед upsert
        try:
            _ensure_words_unique_pair(conn)
        except Exception:
            # Если не удалось — пусть падение проявится на вставке,
            # но в большинстве случаев мы индекс создадим успешно.
            pass

        # [ИЗМЕНЕНО v4.15] upsert по паре (lesson, number)
        now_ms = int(datetime.utcnow().timestamp() * 1000)
        prepared = []
        for r in rows:
            row = dict(r)
            row["user_id"] = user_id
            row["status"] = "user"
            row["updated_at"] = now_ms
            prepared.append(row)

        conn.executemany(
            """
            INSERT INTO words (user_id, status, lesson, number, nl, en, ru, ex_nl, ex_en, ex_ru, audio_nl, audio_en, audio_ru, updated_at)
            VALUES (:user_id, :status, :lesson, :number, :nl, :en, :ru, :ex_nl, :ex_en, :ex_ru, :audio_nl, :audio_en, :audio_ru, :updated_at)
            ON CONFLICT(user_id, lesson, number) DO UPDATE SET
                nl=excluded.nl,
                en=excluded.en,
                ru=excluded.ru,
                ex_nl=excluded.ex_nl,
                ex_en=excluded.ex_en,
                ex_ru=excluded.ex_ru,
                audio_nl=excluded.audio_nl,
                audio_en=excluded.audio_en,
                audio_ru=excluded.audio_ru,
                status=excluded.status,
                updated_at=excluded.updated_at
            """,
            prepared,
        )
        conn.commit()
        return len(rows)
