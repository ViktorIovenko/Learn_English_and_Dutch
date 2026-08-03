from __future__ import annotations

import sqlite3
import time
from typing import Any


def ensure_translation_usage_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS translation_token_usage (
            user_id TEXT PRIMARY KEY,
            successful_requests INTEGER NOT NULL DEFAULT 0,
            failed_requests INTEGER NOT NULL DEFAULT 0,
            prompt_tokens INTEGER NOT NULL DEFAULT 0,
            completion_tokens INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL
        )
        """
    )


def _token_count(value: Any) -> int:
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0


def record_translation_usage(
    conn: sqlite3.Connection,
    user_id: str | None,
    *,
    successful: bool,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
) -> None:
    ensure_translation_usage_schema(conn)
    prompt = _token_count(prompt_tokens)
    completion = _token_count(completion_tokens)
    total = _token_count(total_tokens)
    if total == 0 and (prompt or completion):
        total = prompt + completion

    conn.execute(
        """
        INSERT INTO translation_token_usage (
            user_id, successful_requests, failed_requests,
            prompt_tokens, completion_tokens, total_tokens, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            successful_requests = successful_requests + excluded.successful_requests,
            failed_requests = failed_requests + excluded.failed_requests,
            prompt_tokens = prompt_tokens + excluded.prompt_tokens,
            completion_tokens = completion_tokens + excluded.completion_tokens,
            total_tokens = total_tokens + excluded.total_tokens,
            updated_at = excluded.updated_at
        """,
        (
            str(user_id or ""),
            1 if successful else 0,
            0 if successful else 1,
            prompt,
            completion,
            total,
            int(time.time() * 1000),
        ),
    )


def get_translation_usage_snapshot(conn: sqlite3.Connection) -> dict[str, Any]:
    ensure_translation_usage_schema(conn)
    rows = conn.execute(
        """
        SELECT user_id, successful_requests, failed_requests,
               prompt_tokens, completion_tokens, total_tokens
        FROM translation_token_usage
        """
    ).fetchall()

    by_user: dict[str, dict[str, int]] = {}
    summary = {
        "successful_requests": 0,
        "failed_requests": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    for row in rows:
        if isinstance(row, sqlite3.Row):
            values = {key: _token_count(row[key]) for key in summary}
            user_id = str(row["user_id"])
        else:
            user_id = str(row[0])
            values = {
                "successful_requests": _token_count(row[1]),
                "failed_requests": _token_count(row[2]),
                "prompt_tokens": _token_count(row[3]),
                "completion_tokens": _token_count(row[4]),
                "total_tokens": _token_count(row[5]),
            }
        by_user[user_id] = values
        for key, value in values.items():
            summary[key] += value

    return {
        "scope": "lifetime",
        **summary,
        "by_user": by_user,
    }


def reset_translation_usage(
    conn: sqlite3.Connection,
    *,
    user_id: str | None = None,
) -> int:
    ensure_translation_usage_schema(conn)
    if user_id is None:
        cursor = conn.execute("DELETE FROM translation_token_usage")
    else:
        cursor = conn.execute(
            "DELETE FROM translation_token_usage WHERE user_id = ?",
            (str(user_id),),
        )
    return max(int(cursor.rowcount or 0), 0)
