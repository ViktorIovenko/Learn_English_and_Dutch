"""Normalized multilingual storage for ParallelLingvo.

This module adds a language-agnostic layer on top of the existing legacy
NL/EN/RU columns. Existing routes keep working while new clients can store any
supported language without adding columns to the `words` table.

Migration strategy:
- keep the legacy NL/EN/RU columns while the current UI still uses them;
- backfill legacy content into `word_translations` once;
- keep legacy writes synchronized with normalized rows through SQLite triggers;
- keep new NL/EN/RU API writes synchronized back to legacy columns;
- remove normalized translations automatically when a word is deleted.
"""

from __future__ import annotations

import sqlite3
import time
from typing import Any, Dict, Iterable, List, Sequence

from app.languages import (
    DEFAULT_USER_LANGUAGES,
    LANGUAGE_BY_CODE,
    MIN_PARALLEL_LANGUAGES,
    is_supported_language,
)


LEGACY_COLUMN_MAP = {
    "nl": ("nl", "ex_nl", "audio_nl"),
    "en": ("en", "ex_en", "audio_en"),
    "ru": ("ru", "ex_ru", "audio_ru"),
}

LEGACY_BACKFILL_MARKER = "legacy_nl_en_ru_backfill_v1"


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {
        row["name"] if isinstance(row, sqlite3.Row) else row[1]
        for row in conn.execute(f"PRAGMA table_info({table})")
    }


def _ensure_legacy_sync_triggers(conn: sqlite3.Connection) -> None:
    """Keep the current legacy UI and normalized storage in sync."""
    cols = _table_columns(conn, "words")
    if "id" not in cols:
        return

    # Clean normalized rows when an old route deletes from `words`.
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_words_delete_translations
        AFTER DELETE ON words
        BEGIN
            DELETE FROM word_translations WHERE word_id = OLD.id;
        END;
    """)

    for code, (text_col, example_col, audio_col) in LEGACY_COLUMN_MAP.items():
        if text_col not in cols:
            continue

        example_new = f"COALESCE(NEW.{example_col}, '')" if example_col in cols else "''"
        audio_new = f"COALESCE(NEW.{audio_col}, '')" if audio_col in cols else "''"
        updated_new = "NEW.updated_at" if "updated_at" in cols else "NULL"

        conn.execute(f"""
            CREATE TRIGGER IF NOT EXISTS trg_words_insert_translation_{code}
            AFTER INSERT ON words
            WHEN COALESCE(NEW.{text_col}, '') != ''
              OR {example_new} != ''
              OR {audio_new} != ''
            BEGIN
                INSERT INTO word_translations
                    (word_id, language_code, text, example, audio_url, updated_at)
                VALUES (
                    NEW.id,
                    '{code}',
                    COALESCE(NEW.{text_col}, ''),
                    {example_new},
                    {audio_new},
                    {updated_new}
                )
                ON CONFLICT(word_id, language_code) DO UPDATE SET
                    text=excluded.text,
                    example=excluded.example,
                    audio_url=excluded.audio_url,
                    updated_at=excluded.updated_at;
            END;
        """)

        watched_cols = [text_col]
        if example_col in cols:
            watched_cols.append(example_col)
        if audio_col in cols:
            watched_cols.append(audio_col)
        if "updated_at" in cols:
            watched_cols.append("updated_at")
        update_of = ", ".join(watched_cols)

        conn.execute(f"""
            CREATE TRIGGER IF NOT EXISTS trg_words_update_translation_{code}
            AFTER UPDATE OF {update_of} ON words
            BEGIN
                INSERT INTO word_translations
                    (word_id, language_code, text, example, audio_url, updated_at)
                VALUES (
                    NEW.id,
                    '{code}',
                    COALESCE(NEW.{text_col}, ''),
                    {example_new},
                    {audio_new},
                    {updated_new}
                )
                ON CONFLICT(word_id, language_code) DO UPDATE SET
                    text=excluded.text,
                    example=excluded.example,
                    audio_url=excluded.audio_url,
                    updated_at=excluded.updated_at;

                DELETE FROM word_translations
                WHERE word_id = NEW.id
                  AND language_code = '{code}'
                  AND COALESCE(NEW.{text_col}, '') = ''
                  AND {example_new} = ''
                  AND {audio_new} = '';
            END;
        """)


def ensure_multilingual_schema(conn: sqlite3.Connection, *, backfill_legacy: bool = True) -> None:
    """Create normalized tables without removing or changing legacy fields."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS word_translations (
            word_id       INTEGER NOT NULL,
            language_code TEXT NOT NULL,
            text          TEXT NOT NULL DEFAULT '',
            example       TEXT NOT NULL DEFAULT '',
            audio_url     TEXT NOT NULL DEFAULT '',
            updated_at    INTEGER,
            PRIMARY KEY (word_id, language_code)
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_word_translations_language
        ON word_translations(language_code);
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_languages (
            user_id       TEXT NOT NULL,
            language_code TEXT NOT NULL,
            position      INTEGER NOT NULL DEFAULT 0,
            is_primary    INTEGER NOT NULL DEFAULT 0,
            enabled       INTEGER NOT NULL DEFAULT 1,
            updated_at    INTEGER,
            PRIMARY KEY (user_id, language_code)
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_languages_order
        ON user_languages(user_id, enabled, position);
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS multilingual_meta (
            key        TEXT PRIMARY KEY,
            value      TEXT NOT NULL DEFAULT '',
            updated_at INTEGER
        );
    """)

    # Remove any rows left by versions that existed before the delete trigger.
    conn.execute("""
        DELETE FROM word_translations
        WHERE word_id NOT IN (SELECT id FROM words);
    """)

    _ensure_legacy_sync_triggers(conn)

    if backfill_legacy:
        marker = conn.execute(
            "SELECT 1 FROM multilingual_meta WHERE key = ?",
            (LEGACY_BACKFILL_MARKER,),
        ).fetchone()
        if not marker:
            backfill_legacy_translations(conn)
            conn.execute("""
                INSERT INTO multilingual_meta (key, value, updated_at)
                VALUES (?, 'done', ?)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value,
                    updated_at=excluded.updated_at
            """, (LEGACY_BACKFILL_MARKER, int(time.time() * 1000)))


def backfill_legacy_translations(conn: sqlite3.Connection) -> None:
    """Copy legacy NL/EN/RU data into normalized rows without overwriting newer rows."""
    cols = _table_columns(conn, "words")
    if "id" not in cols:
        return

    for code, (text_col, example_col, audio_col) in LEGACY_COLUMN_MAP.items():
        if text_col not in cols:
            continue
        example_expr = f"COALESCE({example_col}, '')" if example_col in cols else "''"
        audio_expr = f"COALESCE({audio_col}, '')" if audio_col in cols else "''"
        updated_expr = "updated_at" if "updated_at" in cols else "NULL"
        conn.execute(f"""
            INSERT OR IGNORE INTO word_translations
                (word_id, language_code, text, example, audio_url, updated_at)
            SELECT
                id,
                ?,
                COALESCE({text_col}, ''),
                {example_expr},
                {audio_expr},
                {updated_expr}
            FROM words
            WHERE COALESCE({text_col}, '') != ''
               OR {example_expr} != ''
               OR {audio_expr} != '';
        """, (code,))


def get_word_translations(conn: sqlite3.Connection, word_id: int) -> Dict[str, Dict[str, Any]]:
    ensure_multilingual_schema(conn, backfill_legacy=True)
    rows = conn.execute("""
        SELECT language_code, text, example, audio_url, updated_at
        FROM word_translations
        WHERE word_id = ?
        ORDER BY language_code
    """, (int(word_id),)).fetchall()
    return {
        str(row["language_code"]): {
            "text": row["text"] or "",
            "example": row["example"] or "",
            "audio_url": row["audio_url"] or "",
            "updated_at": row["updated_at"],
        }
        for row in rows
    }


def get_translations_for_word_ids(
    conn: sqlite3.Connection,
    word_ids: Sequence[int],
) -> Dict[int, Dict[str, Dict[str, Any]]]:
    ids = [int(value) for value in word_ids]
    if not ids:
        return {}
    ensure_multilingual_schema(conn, backfill_legacy=True)
    marks = ",".join("?" for _ in ids)
    rows = conn.execute(f"""
        SELECT word_id, language_code, text, example, audio_url, updated_at
        FROM word_translations
        WHERE word_id IN ({marks})
        ORDER BY word_id, language_code
    """, ids).fetchall()
    result: Dict[int, Dict[str, Dict[str, Any]]] = {word_id: {} for word_id in ids}
    for row in rows:
        result.setdefault(int(row["word_id"]), {})[str(row["language_code"])] = {
            "text": row["text"] or "",
            "example": row["example"] or "",
            "audio_url": row["audio_url"] or "",
            "updated_at": row["updated_at"],
        }
    return result


def upsert_word_translation(
    conn: sqlite3.Connection,
    word_id: int,
    language_code: str,
    *,
    text: str = "",
    example: str = "",
    audio_url: str = "",
    sync_legacy: bool = True,
) -> None:
    code = str(language_code or "").strip().lower()
    if not is_supported_language(code):
        raise ValueError(f"unsupported_language:{code}")

    ensure_multilingual_schema(conn, backfill_legacy=True)
    now_ms = int(time.time() * 1000)
    conn.execute("""
        INSERT INTO word_translations
            (word_id, language_code, text, example, audio_url, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(word_id, language_code) DO UPDATE SET
            text=excluded.text,
            example=excluded.example,
            audio_url=excluded.audio_url,
            updated_at=excluded.updated_at
    """, (int(word_id), code, str(text or ""), str(example or ""), str(audio_url or ""), now_ms))

    # Keep the old interface working while the front end migrates to translations[].
    if sync_legacy and code in LEGACY_COLUMN_MAP:
        text_col, example_col, audio_col = LEGACY_COLUMN_MAP[code]
        conn.execute(
            f"UPDATE words SET {text_col}=?, {example_col}=?, {audio_col}=?, updated_at=? WHERE id=?",
            (str(text or ""), str(example or ""), str(audio_url or ""), now_ms, int(word_id)),
        )


def normalize_language_codes(codes: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for raw in codes:
        code = str(raw or "").strip().lower()
        if not code or code in seen:
            continue
        if code not in LANGUAGE_BY_CODE:
            raise ValueError(f"unsupported_language:{code}")
        seen.add(code)
        result.append(code)
    return result


def set_user_languages(conn: sqlite3.Connection, user_id: str, codes: Iterable[str]) -> List[str]:
    normalized = normalize_language_codes(codes)
    if len(normalized) < MIN_PARALLEL_LANGUAGES:
        raise ValueError(f"minimum_languages:{MIN_PARALLEL_LANGUAGES}")

    ensure_multilingual_schema(conn, backfill_legacy=True)
    now_ms = int(time.time() * 1000)
    uid = str(user_id)
    conn.execute("DELETE FROM user_languages WHERE user_id = ?", (uid,))
    conn.executemany("""
        INSERT INTO user_languages
            (user_id, language_code, position, is_primary, enabled, updated_at)
        VALUES (?, ?, ?, ?, 1, ?)
    """, [
        (uid, code, position, 1 if position == 0 else 0, now_ms)
        for position, code in enumerate(normalized)
    ])
    return normalized


def get_user_languages(conn: sqlite3.Connection, user_id: str) -> List[str]:
    ensure_multilingual_schema(conn, backfill_legacy=True)
    rows = conn.execute("""
        SELECT language_code
        FROM user_languages
        WHERE user_id = ? AND enabled = 1
        ORDER BY position, language_code
    """, (str(user_id),)).fetchall()
    if not rows:
        return list(DEFAULT_USER_LANGUAGES)
    return [str(row["language_code"]) for row in rows]
