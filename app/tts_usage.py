from __future__ import annotations

import sqlite3
import time
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_TTS_USAGE_TIMEZONE = "Europe/Amsterdam"
DEFAULT_GLOBAL_TTS_CHARACTER_LIMIT = 500_000
GLOBAL_LIMIT_SCOPE = "__global__"


class TtsUsageLimitExceeded(RuntimeError):
    def __init__(
        self,
        *,
        scope: str,
        limit: int,
        used: int,
        requested: int,
    ) -> None:
        super().__init__("tts_monthly_character_limit_reached")
        self.scope = scope
        self.limit = int(limit)
        self.used = int(used)
        self.requested = int(requested)


def _timezone(timezone_name: str | None = None) -> ZoneInfo:
    name = str(timezone_name or DEFAULT_TTS_USAGE_TIMEZONE).strip() or DEFAULT_TTS_USAGE_TIMEZONE
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def usage_period(
    *,
    now: datetime | None = None,
    timezone_name: str | None = None,
) -> dict[str, Any]:
    tz = _timezone(timezone_name)
    current = now.astimezone(tz) if now is not None else datetime.now(tz)
    period_start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period_start.month == 12:
        next_reset = period_start.replace(year=period_start.year + 1, month=1)
    else:
        next_reset = period_start.replace(month=period_start.month + 1)
    return {
        "key": period_start.strftime("%Y-%m"),
        "timezone": getattr(tz, "key", str(tz)),
        "started_at": int(period_start.timestamp() * 1000),
        "next_reset_at": int(next_reset.timestamp() * 1000),
    }


def ensure_tts_usage_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS google_tts_usage_monthly (
            user_id TEXT NOT NULL,
            period_key TEXT NOT NULL,
            successful_requests INTEGER NOT NULL DEFAULT 0,
            failed_requests INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL,
            PRIMARY KEY (user_id, period_key)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_google_tts_usage_period
        ON google_tts_usage_monthly(period_key)
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS google_tts_budget_monthly (
            user_id TEXT NOT NULL,
            period_key TEXT NOT NULL,
            characters INTEGER NOT NULL DEFAULT 0,
            blocked_requests INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL,
            PRIMARY KEY (user_id, period_key)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_google_tts_budget_period
        ON google_tts_budget_monthly(period_key)
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS google_tts_limits (
            scope TEXT PRIMARY KEY,
            monthly_character_limit INTEGER,
            updated_at INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO google_tts_limits (
            scope, monthly_character_limit, updated_at
        ) VALUES (?, ?, ?)
        """,
        (GLOBAL_LIMIT_SCOPE, DEFAULT_GLOBAL_TTS_CHARACTER_LIMIT, int(time.time() * 1000)),
    )


def set_tts_character_limit(
    conn: sqlite3.Connection,
    *,
    user_id: str | None = None,
    monthly_character_limit: int | None,
) -> None:
    ensure_tts_usage_schema(conn)
    scope = GLOBAL_LIMIT_SCOPE if user_id is None else f"user:{str(user_id)}"
    if monthly_character_limit is None:
        if user_id is None:
            raise ValueError("global limit cannot be unlimited")
        conn.execute("DELETE FROM google_tts_limits WHERE scope = ?", (scope,))
        return
    limit = int(monthly_character_limit)
    if limit <= 0:
        raise ValueError("monthly_character_limit must be positive")
    conn.execute(
        """
        INSERT INTO google_tts_limits (scope, monthly_character_limit, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(scope) DO UPDATE SET
            monthly_character_limit = excluded.monthly_character_limit,
            updated_at = excluded.updated_at
        """,
        (scope, limit, int(time.time() * 1000)),
    )


def _limits(conn: sqlite3.Connection) -> tuple[int, dict[str, int]]:
    ensure_tts_usage_schema(conn)
    rows = conn.execute(
        "SELECT scope, monthly_character_limit FROM google_tts_limits"
    ).fetchall()
    global_limit = DEFAULT_GLOBAL_TTS_CHARACTER_LIMIT
    by_user: dict[str, int] = {}
    for row in rows:
        scope = str(row["scope"] if isinstance(row, sqlite3.Row) else row[0])
        raw_limit = row["monthly_character_limit"] if isinstance(row, sqlite3.Row) else row[1]
        if raw_limit is None:
            continue
        limit = max(int(raw_limit), 0)
        if scope == GLOBAL_LIMIT_SCOPE:
            global_limit = limit
        elif scope.startswith("user:"):
            by_user[scope[5:]] = limit
    return global_limit, by_user


def reserve_tts_characters(
    conn: sqlite3.Connection,
    user_id: str | None,
    *,
    characters: int,
    now: datetime | None = None,
    timezone_name: str | None = None,
) -> dict[str, int | str | None]:
    requested = max(int(characters or 0), 0)
    if requested == 0:
        return {"characters": 0, "scope": None}

    if conn.in_transaction:
        conn.commit()
    conn.execute("BEGIN IMMEDIATE")
    try:
        ensure_tts_usage_schema(conn)
        period = usage_period(now=now, timezone_name=timezone_name)
        global_limit, user_limits = _limits(conn)
        uid = str(user_id or "")
        global_used = int(
            conn.execute(
                """
                SELECT COALESCE(SUM(characters), 0)
                FROM google_tts_budget_monthly
                WHERE period_key = ?
                """,
                (period["key"],),
            ).fetchone()[0]
            or 0
        )
        user_row = conn.execute(
            """
            SELECT characters
            FROM google_tts_budget_monthly
            WHERE period_key = ? AND user_id = ?
            """,
            (period["key"], uid),
        ).fetchone()
        user_used = int((user_row[0] if user_row else 0) or 0)
        user_limit = user_limits.get(uid)

        blocked_scope = None
        blocked_limit = 0
        blocked_used = 0
        if global_used + requested > global_limit:
            blocked_scope = "global"
            blocked_limit = global_limit
            blocked_used = global_used
        elif user_limit is not None and user_used + requested > user_limit:
            blocked_scope = "user"
            blocked_limit = user_limit
            blocked_used = user_used

        timestamp = int(time.time() * 1000)
        if blocked_scope:
            conn.execute(
                """
                INSERT INTO google_tts_budget_monthly (
                    user_id, period_key, characters, blocked_requests, updated_at
                ) VALUES (?, ?, 0, 1, ?)
                ON CONFLICT(user_id, period_key) DO UPDATE SET
                    blocked_requests = blocked_requests + 1,
                    updated_at = excluded.updated_at
                """,
                (uid, period["key"], timestamp),
            )
            conn.commit()
            raise TtsUsageLimitExceeded(
                scope=blocked_scope,
                limit=blocked_limit,
                used=blocked_used,
                requested=requested,
            )

        conn.execute(
            """
            INSERT INTO google_tts_budget_monthly (
                user_id, period_key, characters, blocked_requests, updated_at
            ) VALUES (?, ?, ?, 0, ?)
            ON CONFLICT(user_id, period_key) DO UPDATE SET
                characters = characters + excluded.characters,
                updated_at = excluded.updated_at
            """,
            (uid, period["key"], requested, timestamp),
        )
        conn.commit()
        return {"characters": requested, "scope": "user", "period_key": period["key"]}
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise


def record_tts_request(
    conn: sqlite3.Connection,
    user_id: str | None,
    *,
    successful: bool,
    now: datetime | None = None,
    timezone_name: str | None = None,
) -> None:
    ensure_tts_usage_schema(conn)
    period = usage_period(now=now, timezone_name=timezone_name)
    successful_increment = 1 if successful else 0
    failed_increment = 0 if successful else 1
    conn.execute(
        """
        INSERT INTO google_tts_usage_monthly (
            user_id, period_key, successful_requests, failed_requests, updated_at
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, period_key) DO UPDATE SET
            successful_requests = successful_requests + excluded.successful_requests,
            failed_requests = failed_requests + excluded.failed_requests,
            updated_at = excluded.updated_at
        """,
        (
            str(user_id or ""),
            period["key"],
            successful_increment,
            failed_increment,
            int(time.time() * 1000),
        ),
    )


def get_tts_usage_snapshot(
    conn: sqlite3.Connection,
    *,
    now: datetime | None = None,
    timezone_name: str | None = None,
) -> dict[str, Any]:
    ensure_tts_usage_schema(conn)
    period = usage_period(now=now, timezone_name=timezone_name)
    rows = conn.execute(
        """
        SELECT user_id, successful_requests, failed_requests
        FROM google_tts_usage_monthly
        WHERE period_key = ?
        """,
        (period["key"],),
    ).fetchall()
    budget_rows = conn.execute(
        """
        SELECT user_id, characters, blocked_requests
        FROM google_tts_budget_monthly
        WHERE period_key = ?
        """,
        (period["key"],),
    ).fetchall()
    global_limit, user_limits = _limits(conn)

    by_user: dict[str, dict[str, int]] = {}
    successful_requests = 0
    failed_requests = 0
    for row in rows:
        user_id = str(row["user_id"] if isinstance(row, sqlite3.Row) else row[0])
        successful = int(
            (row["successful_requests"] if isinstance(row, sqlite3.Row) else row[1]) or 0
        )
        failed = int((row["failed_requests"] if isinstance(row, sqlite3.Row) else row[2]) or 0)
        by_user[user_id] = {
            "successful_requests": successful,
            "failed_requests": failed,
            "total_requests": successful + failed,
        }
        successful_requests += successful
        failed_requests += failed

    characters = 0
    blocked_requests = 0
    for row in budget_rows:
        user_id = str(row["user_id"] if isinstance(row, sqlite3.Row) else row[0])
        used_characters = int(
            (row["characters"] if isinstance(row, sqlite3.Row) else row[1]) or 0
        )
        blocked = int(
            (row["blocked_requests"] if isinstance(row, sqlite3.Row) else row[2]) or 0
        )
        item = by_user.setdefault(
            user_id,
            {"successful_requests": 0, "failed_requests": 0, "total_requests": 0},
        )
        item["characters"] = used_characters
        item["blocked_requests"] = blocked
        characters += used_characters
        blocked_requests += blocked

    all_user_ids = set(by_user) | set(user_limits)
    for user_id in all_user_ids:
        item = by_user.setdefault(
            user_id,
            {"successful_requests": 0, "failed_requests": 0, "total_requests": 0},
        )
        item.setdefault("characters", 0)
        item.setdefault("blocked_requests", 0)
        user_limit = user_limits.get(user_id)
        item["character_limit"] = user_limit
        item["characters_remaining"] = (
            max(user_limit - int(item["characters"]), 0)
            if user_limit is not None
            else None
        )

    return {
        **period,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "total_requests": successful_requests + failed_requests,
        "characters": characters,
        "blocked_requests": blocked_requests,
        "character_limit": global_limit,
        "characters_remaining": max(global_limit - characters, 0),
        "limit_percent": min(round((characters / global_limit) * 100, 2), 100.0)
        if global_limit
        else 100.0,
        "by_user": by_user,
    }


def reset_tts_usage(
    conn: sqlite3.Connection,
    *,
    user_id: str | None = None,
    now: datetime | None = None,
    timezone_name: str | None = None,
) -> int:
    ensure_tts_usage_schema(conn)
    period = usage_period(now=now, timezone_name=timezone_name)
    if user_id is None:
        cursor = conn.execute(
            "DELETE FROM google_tts_usage_monthly WHERE period_key = ?",
            (period["key"],),
        )
    else:
        cursor = conn.execute(
            """
            DELETE FROM google_tts_usage_monthly
            WHERE period_key = ? AND user_id = ?
            """,
            (period["key"], str(user_id)),
        )
    return max(int(cursor.rowcount or 0), 0)
