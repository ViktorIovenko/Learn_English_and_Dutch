from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Callable

from config import Config
from app import models


READ_SCOPE = "learning.read"
WRITE_SCOPE = "learning.write"
LEARNING_SCOPES = (READ_SCOPE, WRITE_SCOPE)
FAMILY_READ_SCOPE = "family.read"
FAMILY_WRITE_SCOPE = "family.write"
CONNECTOR_SCOPES = (*LEARNING_SCOPES, FAMILY_READ_SCOPE, FAMILY_WRITE_SCOPE)
FILES_SCOPE = "learning.files"
SUBSCRIPTIONS_ADMIN_SCOPE = "subscriptions.admin"
USERS_ADMIN_SCOPE = "users.admin"
ANALYTICS_ADMIN_SCOPE = "analytics.admin"
ALL_SCOPES = (
    READ_SCOPE,
    WRITE_SCOPE,
    FAMILY_READ_SCOPE,
    FAMILY_WRITE_SCOPE,
    FILES_SCOPE,
    SUBSCRIPTIONS_ADMIN_SCOPE,
    USERS_ADMIN_SCOPE,
    ANALYTICS_ADMIN_SCOPE,
)

MAX_PAGE_SIZE = 100
MAX_WORDS_PER_WRITE = 100
MAX_PROGRESS_ITEMS = 100
# A child keeps only the newest N assigned lessons active; older ones are
# archived (assignment kept, words/progress/difficult flags untouched).
MAX_ACTIVE_CHILD_LESSONS = 5
# Upper bound on provider calls a single "complete" scenario may make so the
# gateway request stays within its timeout; the caller re-runs for the rest.
MAX_CLOUD_FILLS_PER_CALL = 12
# Values that look like a template placeholder or serialisation garbage
# rather than a real translation/example.
CORRUPT_VALUE_MARKERS = {"null", "none", "undefined", "nan", "n/a", "-", "?", "...", "todo", "tbd", "[object object]"}


class McpServiceError(Exception):
    def __init__(self, code: str, message: str, *, status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


@dataclass(frozen=True)
class Operation:
    scope: str
    handler: Callable[[str, dict[str, Any]], Any]
    admin_only: bool = False


def _conn() -> sqlite3.Connection:
    from app.content_db import connect
    conn = connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _routes():
    # Lazy import avoids a cycle while app.routes registers the MCP blueprint.
    from app import routes
    return routes


def _is_admin(user_id: str) -> bool:
    return bool(_routes()._is_admin_user_id(user_id))


def _is_child_account(user_id: str) -> bool:
    return _routes()._account_context(user_id)["account_type"] == "child"


def _bounded_limit(params: dict[str, Any], default: int = 50) -> int:
    try:
        return max(1, min(MAX_PAGE_SIZE, int(params.get("limit", default))))
    except (TypeError, ValueError):
        raise McpServiceError("INVALID_LIMIT", "limit must be an integer")


def _cursor(params: dict[str, Any]) -> int:
    try:
        return max(0, int(params.get("cursor") or 0))
    except (TypeError, ValueError):
        raise McpServiceError("INVALID_CURSOR", "cursor must be a non-negative integer")


def _lesson_title(params: dict[str, Any], key: str = "lesson_title") -> str:
    title = " ".join(str(params.get(key) or params.get("lesson") or "").split())
    if not title:
        raise McpServiceError("LESSON_REQUIRED", "lesson title is required")
    if _value_problem(title, max_length=200) is not None:
        raise McpServiceError("INVALID_LESSON_TITLE", "supply a meaningful lesson title")
    if len(title) > 200:
        raise McpServiceError("LESSON_TOO_LONG", "lesson title is too long")
    return title


def _word_languages() -> list[str]:
    with _conn() as conn:
        cols = {str(row["name"]) for row in conn.execute("PRAGMA table_info(words)")}
    return sorted(code for code in _routes().LANGUAGE_CODES if code in cols)


def _serialize_word(row: sqlite3.Row | dict[str, Any], user_id: str) -> dict[str, Any]:
    data = dict(row)
    result = {
        "id": int(data["id"]),
        "lesson": str(data.get("lesson") or ""),
        "number": str(data.get("number") or ""),
        "difficult": bool(data.get("difficult")),
    }
    for language in _word_languages():
        result[language] = str(data.get(language) or "")
        result[f"ex_{language}"] = str(data.get(f"ex_{language}") or "")
    result.update({key: str(data.get(key) or "") for key in ("content_sense","content_context","example_level")})
    result["editable"] = str(data.get("user_id") or "") == user_id
    return result


def ensure_mcp_schema() -> None:
    with _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS mcp_oauth_clients (
                client_id TEXT PRIMARY KEY,
                client_name TEXT NOT NULL DEFAULT '',
                redirect_uris TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                last_used_at INTEGER,
                revoked_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS mcp_oauth_codes (
                code_hash TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                redirect_uri TEXT NOT NULL,
                resource TEXT NOT NULL,
                scopes TEXT NOT NULL,
                code_challenge TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                used_at INTEGER,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(client_id) REFERENCES mcp_oauth_clients(client_id)
            );
            CREATE TABLE IF NOT EXISTS mcp_access_grants (
                token_hash TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                resource TEXT NOT NULL,
                scopes TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                last_used_at INTEGER,
                revoked_at INTEGER,
                FOREIGN KEY(client_id) REFERENCES mcp_oauth_clients(client_id)
            );
            CREATE INDEX IF NOT EXISTS idx_mcp_grants_user
                ON mcp_access_grants(user_id, revoked_at, expires_at);
            CREATE TABLE IF NOT EXISTS mcp_user_settings (
                user_id TEXT PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 1,
                updated_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS mcp_idempotency (
                user_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                response_json TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                PRIMARY KEY(user_id, operation, idempotency_key)
            );
            CREATE TABLE IF NOT EXISTS family_lesson_assignments (
                parent_user_id TEXT NOT NULL,
                child_user_id  TEXT NOT NULL,
                lesson         TEXT NOT NULL,
                created_at     INTEGER NOT NULL,
                PRIMARY KEY (parent_user_id, child_user_id, lesson)
            );
            CREATE INDEX IF NOT EXISTS idx_family_lesson_assignments_child
                ON family_lesson_assignments(child_user_id, lesson);
            CREATE TABLE IF NOT EXISTS mcp_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at INTEGER NOT NULL,
                request_id TEXT NOT NULL,
                client_hash TEXT NOT NULL,
                user_hash TEXT NOT NULL,
                operation TEXT NOT NULL,
                success INTEGER NOT NULL,
                error_code TEXT,
                duration_ms INTEGER NOT NULL,
                item_count INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_mcp_audit_created_at ON mcp_audit_log(created_at);
            CREATE TABLE IF NOT EXISTS mcp_admin_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at INTEGER NOT NULL,
                admin_user_id TEXT NOT NULL,
                target_user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                old_value TEXT NOT NULL,
                new_value TEXT NOT NULL,
                request_id TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_mcp_admin_audit_created ON mcp_admin_audit_log(created_at DESC);
            """
        )
        _routes()._ensure_family_assignment_archive_columns(conn)
        conn.commit()


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _idempotent(user_id: str, operation: str, params: dict[str, Any], callback: Callable[[], Any]) -> Any:
    key = str(params.get("idempotency_key") or "").strip()
    if not key or len(key)>128:
        raise McpServiceError("IDEMPOTENCY_KEY_REQUIRED","a valid idempotency_key is required")
    payload = {k:v for k,v in params.items() if k!="idempotency_key"}
    request_digest = token_hash(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":")))
    from app.content_db import transaction
    with transaction(Config.DB_PATH) as conn:
        existing = conn.execute("SELECT request_hash,response_json FROM mcp_idempotency WHERE user_id=? AND operation=? AND idempotency_key=?",(user_id,operation,key)).fetchone()
        if existing:
            if existing["request_hash"]!=request_digest:
                raise McpServiceError("IDEMPOTENCY_CONFLICT","idempotency_key was already used with different input",status=409)
            return json.loads(existing["response_json"])
        response = callback()
        conn.execute("INSERT INTO mcp_idempotency(user_id,operation,idempotency_key,request_hash,response_json,created_at) VALUES(?,?,?,?,?,?)",(user_id,operation,key,request_digest,json.dumps(response,ensure_ascii=False),int(time.time())))
        return response


def _me_get(user_id: str, _params: dict[str, Any]) -> dict[str, Any]:
    routes = _routes()
    with _conn() as conn:
        row = conn.execute(
            "SELECT username, first_name, last_name, account_type FROM users WHERE user_id=? AND COALESCE(is_active,1)=1",
            (user_id,),
        ).fetchone()
    if not row:
        raise McpServiceError("USER_NOT_FOUND", "user was not found", status=404)
    return {
        "display_name": routes._format_user_name(row),
        "account_type": str(row["account_type"] or "standard"),
        "is_admin": _is_admin(user_id),
        "subscription": routes._get_subscription(user_id),
    }


def _languages_get(user_id: str, _params: dict[str, Any]) -> dict[str, Any]:
    routes = _routes()
    return {"selected": routes._get_user_languages(user_id), "available": routes.LANGUAGE_OPTIONS}


def _languages_update(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    routes = _routes()
    raw = params.get("languages")
    if not isinstance(raw, list):
        raise McpServiceError("INVALID_LANGUAGES", "languages must be a list")
    languages = list(dict.fromkeys(str(item or "").strip().lower() for item in raw if str(item or "").strip()))
    if not 3 <= len(languages) <= 5:
        raise McpServiceError("INVALID_LANGUAGES", "choose between 3 and 5 languages")
    unsupported = [code for code in languages if code not in routes.LANGUAGE_CODES]
    if unsupported:
        raise McpServiceError("UNSUPPORTED_LANGUAGE", "one or more languages are unsupported", details={"languages": unsupported})
    now_ms = int(time.time() * 1000)
    with _conn() as conn:
        routes._ensure_word_language_columns(conn, languages)
        conn.execute("DELETE FROM user_language_preferences WHERE user_id=?", (user_id,))
        conn.executemany(
            "INSERT INTO user_language_preferences(user_id,priority,lang_code,updated_at) VALUES(?,?,?,?)",
            [(user_id, index + 1, code, now_ms) for index, code in enumerate(languages)],
        )
        conn.commit()
    return _languages_get(user_id, {})


def _settings_get(user_id: str, _params: dict[str, Any]) -> dict[str, Any]:
    routes = _routes()
    return {"daily_goal": routes._daily_goal_settings(user_id), "ui_language": routes._get_ui_language(user_id)}


def _settings_update(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    routes = _routes()
    changed: dict[str, Any] = {}
    if "daily_goal" in params:
        settings = routes._daily_goal_settings(user_id)
        try:
            value = int(params["daily_goal"])
        except (TypeError, ValueError):
            raise McpServiceError("INVALID_GOAL", "daily_goal must be an integer")
        if not settings["minimum"] <= value <= settings["maximum"]:
            raise McpServiceError("GOAL_OUT_OF_RANGE", "daily_goal is outside the allowed range")
        with _conn() as conn:
            conn.execute(
                "INSERT INTO user_daily_goals(user_id,goal_value,updated_at) VALUES(?,?,CURRENT_TIMESTAMP) "
                "ON CONFLICT(user_id) DO UPDATE SET goal_value=excluded.goal_value,updated_at=CURRENT_TIMESTAMP",
                (user_id, value),
            )
            conn.commit()
        changed["daily_goal"] = routes._daily_goal_settings(user_id)
    if "ui_language" in params:
        language = str(params["ui_language"] or "").strip().lower()
        if language and language not in routes.LANGUAGE_CODES:
            raise McpServiceError("UNSUPPORTED_LANGUAGE", "ui_language is not supported")
        changed["ui_language"] = routes._save_ui_language_override(user_id, language or None)
    if not changed:
        raise McpServiceError("NO_VALID_FIELDS", "no supported settings were supplied")
    return changed


def _subscription_get(user_id: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _routes()._get_subscription(user_id)


def _ai_status(_user_id: str, _params: dict[str, Any]) -> dict[str, Any]:
    from app import ai_platform
    return {"cloud_available": ai_platform.is_configured()}


def _translate_word(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    from app import ai_platform
    word = str(params.get("word") or "").strip()
    language = str(params.get("from_lang") or "nl").strip().lower()
    level = str(params.get("level") or "A2").strip()[:10]
    known_ru = str(params.get("known_ru") or "").strip() or None
    if not word or len(word) > 500:
        raise McpServiceError("WORD_REQUIRED", "a bounded word value is required")
    if language not in _routes().LANGUAGE_CODES:
        raise McpServiceError("UNSUPPORTED_LANGUAGE", "from_lang is not supported")
    try:
        result, usage = ai_platform.translate_word(word,language,params.get("level",""),known_ru,supplied=params.get("supplied"),languages=params.get("languages") or _requirements_for(user_id)["languages"],sense=str(params.get("sense") or ""),context=str(params.get("context") or ""))
    except ai_platform.AiPlatformError as exc:
        _routes()._record_translation_request_usage(user_id, successful=False, usage=exc.usage)
        raise McpServiceError("AI_PROVIDER_ERROR", "translation provider failed", status=502)
    if getattr(usage,"provider_calls",1) or getattr(usage,"total_tokens",0):
        _routes()._record_translation_request_usage(user_id,successful=True,usage=usage)
    return result


def _generate_topic_words(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    from app import ai_platform
    topic = str(params.get("topic") or "").strip()
    language = str(params.get("language") or "nl").strip().lower()
    level = str(params.get("level") or "A2").strip()[:10]
    try:
        count = max(1, min(50, int(params.get("count") or 10)))
    except (TypeError, ValueError):
        raise McpServiceError("INVALID_COUNT", "count must be an integer")
    existing = params.get("existing_words") if isinstance(params.get("existing_words"), list) else []
    existing = [str(item)[:500] for item in existing[:150]]
    if not topic or len(topic) > 500:
        raise McpServiceError("TOPIC_REQUIRED", "a bounded topic is required")
    if language not in _routes().LANGUAGE_CODES:
        raise McpServiceError("UNSUPPORTED_LANGUAGE", "language is not supported")
    try:
        words, usage = ai_platform.suggest_topic_words(topic, language, level, count, existing)
    except ai_platform.AiPlatformError as exc:
        _routes()._record_translation_request_usage(user_id, successful=False, usage=exc.usage)
        raise McpServiceError("AI_PROVIDER_ERROR", "word generation provider failed", status=502)
    if getattr(usage,"provider_calls",1) or getattr(usage,"total_tokens",0):
        _routes()._record_translation_request_usage(user_id,successful=True,usage=usage)
    return {"words": words}


def _translate_language(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    from app import ai_platform
    source_word = str(params.get("source_word") or "").strip()
    source_sentence = str(params.get("source_sentence") or "").strip()
    source_name = str(params.get("source_language") or "").strip()
    target_name = str(params.get("target_language") or "").strip()
    if not source_word or not target_name or len(source_word) > 500 or len(source_sentence) > 2000:
        raise McpServiceError("INVALID_TRANSLATION_INPUT", "source_word and target_language are required and bounded")
    try:
        result, usage = ai_platform.translate_language(source_word,source_sentence,source_name,target_name,supplied=params.get("supplied"),sense=str(params.get("sense") or ""),context=str(params.get("context") or ""))
    except ai_platform.AiPlatformError as exc:
        _routes()._record_translation_request_usage(user_id, successful=False, usage=exc.usage)
        raise McpServiceError("AI_PROVIDER_ERROR", "translation provider failed", status=502)
    if getattr(usage,"provider_calls",1) or getattr(usage,"total_tokens",0):
        _routes()._record_translation_request_usage(user_id,successful=True,usage=usage)
    return result


def _audio_ensure(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    from app.audio_gen import ensure_audio_for_ids
    raw_ids = params.get("word_ids")
    if not isinstance(raw_ids, list) or not 1 <= len(raw_ids) <= 25:
        raise McpServiceError("INVALID_WORD_IDS", "word_ids must contain 1 to 25 integers")
    try:
        word_ids = list(dict.fromkeys(int(value) for value in raw_ids))
    except (TypeError, ValueError):
        raise McpServiceError("INVALID_WORD_IDS", "word_ids must contain integers")
    languages = list(dict.fromkeys(str(value).lower() for value in (params.get("languages") or ["nl", "en", "ru"])))
    if any(language not in _routes().LANGUAGE_CODES for language in languages):
        raise McpServiceError("UNSUPPORTED_LANGUAGE", "one or more languages are unsupported")
    with _conn() as conn:
        qmarks = ",".join("?" for _ in word_ids)
        owned = int(conn.execute(
            f"SELECT COUNT(*) FROM words WHERE id IN ({qmarks}) AND (user_id=? OR status='test')",
            [*word_ids, user_id],
        ).fetchone()[0])
    if owned != len(word_ids):
        raise McpServiceError("WORD_NOT_FOUND", "one or more words were not found", status=404)
    result = ensure_audio_for_ids(Config.DB_PATH, word_ids, languages, user_id=user_id)
    if result.get("limit_reached"):
        raise McpServiceError("TTS_LIMIT_REACHED", "text-to-speech usage limit was reached", status=429)
    return result


def _lessons_list(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    include_hidden = bool(params.get("include_hidden", False))
    lessons = _routes().get_visible_lessons_for_user(user_id)
    if not include_hidden:
        lessons = [item for item in lessons if not bool(item.get("hidden"))]
    return {"items": lessons[:MAX_PAGE_SIZE], "truncated": len(lessons) > MAX_PAGE_SIZE}


def _lesson_get(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    title = _lesson_title(params)
    lessons = _routes().get_visible_lessons_for_user(user_id)
    lesson = next((item for item in lessons if str(item.get("lesson") or "") == title), None)
    if not lesson:
        raise McpServiceError("LESSON_NOT_FOUND", "lesson was not found", status=404)
    return lesson


def _lesson_words(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    title = _lesson_title(params)
    limit, cursor = _bounded_limit(params), _cursor(params)
    with _conn() as conn:
        owner_id = _routes()._child_lesson_owner(conn, user_id, title)
        if not owner_id:
            raise McpServiceError("LESSON_NOT_FOUND", "lesson was not found or has no words", status=404)
        rows = conn.execute(
            """
            SELECT w.*, COALESCE(f.difficult,0) AS difficult
            FROM words w LEFT JOIN user_word_flags f ON f.word_id=w.id AND f.user_id=?
            WHERE (w.user_id=? OR w.status='test') AND w.lesson=? AND w.id>?
            ORDER BY w.id LIMIT ?
            """,
            (user_id, owner_id, title, cursor, limit + 1),
        ).fetchall()
    if not rows:
        raise McpServiceError("LESSON_NOT_FOUND", "lesson was not found or has no words", status=404)
    page = rows[:limit]
    return {
        "items": [_serialize_word(row, user_id) for row in page],
        "next_cursor": int(page[-1]["id"]) if len(rows) > limit else None,
        "truncated": len(rows) > limit,
    }


def _word_get(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        word_id = int(params.get("word_id"))
    except (TypeError, ValueError):
        raise McpServiceError("WORD_ID_REQUIRED", "word_id must be an integer")
    with _conn() as conn:
        _assert_word_access(conn, user_id, word_id, allow_test=True)
        row = conn.execute(
            "SELECT w.*, COALESCE(f.difficult,0) AS difficult FROM words w "
            "LEFT JOIN user_word_flags f ON f.word_id=w.id AND f.user_id=? "
            "WHERE w.id=?",
            (user_id, word_id),
        ).fetchone()
    if not row:
        raise McpServiceError("WORD_NOT_FOUND", "word was not found", status=404)
    return _serialize_word(row, user_id)


def _assert_word_access(conn: sqlite3.Connection, user_id: str, word_id: int, *, allow_test: bool = False) -> None:
    row = conn.execute("SELECT user_id,status,lesson FROM words WHERE id=?", (word_id,)).fetchone()
    if not row:
        raise McpServiceError("WORD_NOT_FOUND", "word was not found", status=404)
    assigned_owner = _routes()._child_lesson_owner(conn, user_id, str(row["lesson"] or ""))
    if str(row["user_id"]) != user_id and str(row["user_id"]) != assigned_owner and not (allow_test and str(row["status"]) == "test"):
        raise McpServiceError("FORBIDDEN", "word belongs to another user", status=403)


def _words_search(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    query = str(params.get("query") or "").strip()
    if not query:
        raise McpServiceError("QUERY_REQUIRED", "query is required")
    limit = _bounded_limit(params, 25)
    lesson = str(params.get("lesson_title") or "").strip()
    languages = _word_languages()
    where = ["(w.user_id=? OR w.status='test')"]
    values: list[Any] = [user_id]
    if lesson:
        where.append("w.lesson=?")
        values.append(lesson)
    text_filter = " OR ".join(["w.lesson LIKE ?", *[f'w."{lang}" LIKE ?' for lang in languages]])
    where.append(f"({text_filter})")
    values.extend([f"%{query}%"] * (len(languages) + 1))
    with _conn() as conn:
        rows = conn.execute(
            "SELECT w.*, COALESCE(f.difficult,0) AS difficult FROM words w "
            "LEFT JOIN user_word_flags f ON f.word_id=w.id AND f.user_id=? WHERE "
            + " AND ".join(where) + " ORDER BY w.id DESC LIMIT ?",
            [user_id, *values, limit],
        ).fetchall()
    return {"items": [_serialize_word(row, user_id) for row in rows]}


# Words a user may hold a difficult flag on: their own, shared test words, or
# a parent's canonical words assigned to them (active or archived — an
# archived lesson must not lose its difficult words).
_VISIBLE_WORD_SQL = (
    "(w.user_id=? OR w.status='test' OR EXISTS ("
    "SELECT 1 FROM family_lesson_assignments a "
    "WHERE a.child_user_id=? AND a.parent_user_id=w.user_id AND a.lesson=w.lesson))"
)


def _difficult_rows(conn: sqlite3.Connection, flag_user_id: str, *, owner_ids: list[str] | None, lesson: str, cursor: int, limit: int) -> list[sqlite3.Row]:
    where = ["f.user_id=?", "f.difficult=1", "w.id>?"]
    values: list[Any] = [flag_user_id, cursor]
    if owner_ids is None:
        where.append(_VISIBLE_WORD_SQL)
        values.extend([flag_user_id, flag_user_id])
    else:
        where.append("w.user_id IN (" + ",".join("?" for _ in owner_ids) + ")")
        values.extend(owner_ids)
    if lesson:
        where.append("w.lesson=?")
        values.append(lesson)
    return conn.execute(
        "SELECT w.*, 1 AS difficult, COALESCE(f.source,'manual') AS flag_source, f.updated_at AS flag_updated_at "
        "FROM words w JOIN user_word_flags f ON f.word_id=w.id WHERE "
        + " AND ".join(where) + " ORDER BY w.id LIMIT ?",
        [*values, limit + 1],
    ).fetchall()


def _difficult_page(rows: list[sqlite3.Row], user_id: str, limit: int) -> dict[str, Any]:
    page = rows[:limit]
    items = []
    for row in page:
        item = _serialize_word(row, user_id)
        item["difficult"] = True
        item["difficult_source"] = str(row["flag_source"] or "manual")
        item["difficult_updated_at"] = int(row["flag_updated_at"]) if row["flag_updated_at"] is not None else None
        items.append(item)
    return {"items": items, "next_cursor": int(page[-1]["id"]) if len(rows) > limit else None}


def _difficult_words(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    limit, cursor = _bounded_limit(params, 50), _cursor(params)
    lesson = str(params.get("lesson_title") or "").strip()
    with _conn() as conn:
        rows = _difficult_rows(conn, user_id, owner_ids=None, lesson=lesson, cursor=cursor, limit=limit)
    return _difficult_page(rows, user_id, limit)


def _lesson_create(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    title = _lesson_title(params, "title")
    def create() -> dict[str, Any]:
        models.ensure_user_tables(Config.DB_PATH)
        with _conn() as conn:
            if conn.execute("SELECT 1 FROM words WHERE user_id=? AND lesson=?", (user_id, title)).fetchone():
                raise McpServiceError("LESSON_EXISTS", "lesson already exists", status=409)
            conn.execute(
                "INSERT INTO user_lessons(user_id,lesson,hidden,updated_at,updated_at_ts) VALUES(?,?,0,CURRENT_TIMESTAMP,?) "
                "ON CONFLICT(user_id,lesson) DO NOTHING",
                (user_id, title, int(time.time() * 1000)),
            )
            conn.commit()
        return {"lesson": title, "created": True}
    return _idempotent(user_id, "lesson_create", params, create)


def _words_add(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    title = _lesson_title(params)
    words = params.get("words")
    if not isinstance(words, list) or not 1 <= len(words) <= MAX_WORDS_PER_WRITE:
        raise McpServiceError("INVALID_WORDS", f"words must contain 1 to {MAX_WORDS_PER_WRITE} items")
    def add() -> dict[str, Any]:
        from app.content_service import import_words
        try:
            result=import_words(Config.DB_PATH,user_id,[{"lesson":title,"words":words,"languages":_requirements_for(user_id)["languages"]}],source="mcp")
        except ValueError as exc:
            raise McpServiceError("WORD_VALIDATION_FAILED",str(exc)) from exc
        return {"lesson":title,"created":result["imported"],"updated":0,"skipped":0,"errors":[],"ids":result["ids"],"pending":result["pending"]}
    return _idempotent(user_id, "words_add", params, add)


def _insert_words(user_id: str, title: str, words: list[Any]) -> int:
    """All clients share one importer and one reusable content catalog."""
    from app.content_service import import_words
    try:
        result=import_words(Config.DB_PATH,user_id,[{"lesson":title,"words":words,"languages":_requirements_for(user_id)["languages"]}],source="mcp")
    except ValueError as exc:
        raise McpServiceError("WORD_VALIDATION_FAILED",str(exc)) from exc
    return result["imported"]


def _word_update(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        word_id = int(params.get("word_id"))
    except (TypeError, ValueError):
        raise McpServiceError("WORD_ID_REQUIRED", "word_id must be an integer")
    fields = params.get("fields")
    if not isinstance(fields, dict):
        raise McpServiceError("INVALID_FIELDS", "fields must be an object")
    from app.content_db import transaction
    from app.content_service import ensure_schema
    with transaction(Config.DB_PATH) as conn:
        ensure_schema(conn)
    for alias, column in (("sense","content_sense"),("context","content_context"),("level","example_level")):
        if alias in fields:
            fields[column]=fields.pop(alias)
    allowed = {"lesson", "number", "content_sense", "content_context", "example_level", *(_word_languages()), *{f"ex_{lang}" for lang in _word_languages()}}
    updates = {key: str(value or "").strip() for key, value in fields.items() if key in allowed}
    if not updates:
        raise McpServiceError("NO_VALID_FIELDS", "no supported word fields were supplied")
    with _conn() as conn:
        _assert_word_access(conn, user_id, word_id)
        old=dict(conn.execute("SELECT * FROM words WHERE id=?",(word_id,)).fetchone())
        from app.content_service import prepare_edit
        updates=prepare_edit(old,updates)
        updates["updated_at"] = int(time.time() * 1000)
        conn.execute(
            "UPDATE words SET " + ",".join(f'"{key}"=?' for key in updates) + " WHERE id=? AND user_id=?",
            [*updates.values(), word_id, user_id],
        )
        conn.commit()
    from app.content_service import remember_word_ids
    remember_word_ids(Config.DB_PATH,[word_id],source="mcp")
    return _word_get(user_id, {"word_id": word_id})


def _word_delete(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    if params.get("confirm") is not True:
        raise McpServiceError("CONFIRMATION_REQUIRED", "confirm=true is required")
    try:
        word_id = int(params.get("word_id"))
    except (TypeError, ValueError):
        raise McpServiceError("WORD_ID_REQUIRED", "word_id must be an integer")
    with _conn() as conn:
        _assert_word_access(conn, user_id, word_id)
        cursor = conn.execute("DELETE FROM words WHERE id=? AND user_id=?", (word_id, user_id))
        conn.execute("DELETE FROM user_word_flags WHERE user_id=? AND word_id=?", (user_id, word_id))
        conn.commit()
    if not cursor.rowcount:
        raise McpServiceError("WORD_NOT_FOUND", "word was not found", status=404)
    return {"deleted": True, "word_id": word_id}


def _word_ids(params: dict[str, Any], key: str = "word_ids") -> list[int]:
    raw_ids = params.get(key)
    if not isinstance(raw_ids, list) or not 1 <= len(raw_ids) <= MAX_PROGRESS_ITEMS:
        raise McpServiceError("INVALID_WORD_IDS", f"{key} must be a bounded non-empty list")
    try:
        return list(dict.fromkeys(int(value) for value in raw_ids))
    except (TypeError, ValueError):
        raise McpServiceError("INVALID_WORD_IDS", f"{key} must contain integers")


def _difficult_source(params: dict[str, Any]) -> str:
    source = str(params.get("source") or "manual").strip().lower()
    if source not in {"manual", "auto_errors", "parent"}:
        raise McpServiceError("INVALID_SOURCE", "source must be manual, auto_errors or parent")
    return source


def _write_difficult_flags(conn: sqlite3.Connection, flag_user_id: str, word_ids: list[int], difficult: bool, source: str) -> None:
    now_ms = int(time.time() * 1000)
    conn.executemany(
        "INSERT INTO user_word_flags(user_id,word_id,difficult,source,updated_at) VALUES(?,?,?,?,?) "
        "ON CONFLICT(user_id,word_id) DO UPDATE SET difficult=excluded.difficult,source=excluded.source,updated_at=excluded.updated_at",
        [(flag_user_id, word_id, 1 if difficult else 0, source, now_ms) for word_id in word_ids],
    )


def _set_difficult(user_id: str, params: dict[str, Any], difficult: bool) -> dict[str, Any]:
    """Per-user difficult flag on words the user may see (own, test, or a
    parent's lesson assigned to this child). The flag never leaks to other
    users of the same canonical word."""
    word_ids = _word_ids(params)
    source = _difficult_source(params)
    with _conn() as conn:
        for word_id in word_ids:
            _assert_word_access(conn, user_id, word_id, allow_test=True)
        _write_difficult_flags(conn, user_id, word_ids, difficult, source)
        conn.commit()
    return {"updated": len(word_ids), "difficult": difficult, "word_ids": word_ids, "source": source}


def _words_mark_difficult(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    return _set_difficult(user_id, params, bool(params.get("difficult")))


def _lesson_hidden(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    title = _lesson_title(params)
    models.set_lesson_hidden(Config.DB_PATH, user_id, title, 1 if bool(params.get("hidden")) else 0)
    return {"lesson": title, "hidden": bool(params.get("hidden"))}


def _lesson_delete(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    if params.get("confirm") is not True:
        raise McpServiceError("CONFIRMATION_REQUIRED", "confirm=true is required")
    title = _lesson_title(params)
    with _conn() as conn:
        ids = [int(row[0]) for row in conn.execute("SELECT id FROM words WHERE user_id=? AND lesson=?", (user_id, title))]
        cursor = conn.execute("DELETE FROM words WHERE user_id=? AND lesson=?", (user_id, title))
        conn.execute("DELETE FROM user_lessons WHERE user_id=? AND lesson=?", (user_id, title))
        if ids:
            qmarks = ",".join("?" for _ in ids)
            conn.execute(f"DELETE FROM user_word_flags WHERE user_id=? AND word_id IN ({qmarks})", [user_id, *ids])
        conn.commit()
    if not cursor.rowcount:
        raise McpServiceError("LESSON_NOT_FOUND", "lesson was not found", status=404)
    return {"deleted": True, "lesson": title, "deleted_words": cursor.rowcount}


def _lesson_rename(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    old_title = _lesson_title(params)
    new_title = _lesson_title(params, "new_title")
    with _conn() as conn:
        old_exists = conn.execute(
            "SELECT 1 FROM words WHERE user_id=? AND lesson=? UNION SELECT 1 FROM user_lessons WHERE user_id=? AND lesson=?",
            (user_id, old_title, user_id, old_title),
        ).fetchone()
        if not old_exists:
            raise McpServiceError("LESSON_NOT_FOUND", "lesson was not found", status=404)
        if conn.execute(
            "SELECT 1 FROM words WHERE user_id=? AND lesson=? UNION SELECT 1 FROM user_lessons WHERE user_id=? AND lesson=?",
            (user_id, new_title, user_id, new_title),
        ).fetchone():
            raise McpServiceError("LESSON_EXISTS", "target lesson already exists", status=409)
        cursor = conn.execute(
            "UPDATE words SET lesson=?,updated_at=? WHERE user_id=? AND lesson=?",
            (new_title, int(time.time() * 1000), user_id, old_title),
        )
        conn.execute("UPDATE user_lessons SET lesson=? WHERE user_id=? AND lesson=?", (new_title, user_id, old_title))
        conn.commit()
    return {"lesson": new_title, "renamed_words": cursor.rowcount}


def _navigation(user_id: str, params: dict[str, Any], *, previous: bool) -> dict[str, Any]:
    current = str(params.get("current_lesson") or "").strip()
    fn = models.get_prev_lesson_title if previous else models.get_next_lesson_title
    title = fn(Config.DB_PATH, current, user_id)
    return {"lesson": title}


def _progress_summary(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        days = max(1, min(90, int(params.get("days", 7))))
    except (TypeError, ValueError):
        raise McpServiceError("INVALID_PERIOD", "days must be between 1 and 90")
    since = int(time.time() * 1000) - days * 86400000
    lesson = str(params.get("lesson_title") or "").strip()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT event_type,payload,event_ts FROM progress_events WHERE user_id=? AND (CASE WHEN event_ts<100000000000 THEN event_ts*1000 ELSE event_ts END)>=? ORDER BY event_ts",
            (user_id, since),
        ).fetchall()
    correct = wrong = 0
    active_lessons: set[str] = set()
    for row in rows:
        try:
            payload = json.loads(row["payload"] or "{}")
        except (TypeError, json.JSONDecodeError):
            payload = {}
        state = payload.get("state") if isinstance(payload, dict) else {}
        event_lesson = str((state or {}).get("lesson") or "")
        if lesson and event_lesson != lesson:
            continue
        if event_lesson:
            active_lessons.add(event_lesson)
        event_type = str(row["event_type"] or payload.get("type") or "")
        reason = str((state or {}).get("reason") or "")
        if event_type == "word_correct" or reason == "answer_ok":
            correct += 1
        elif event_type == "word_wrong" or reason == "answer_wrong":
            wrong += 1
    return {"days": days, "correct": correct, "wrong": wrong, "attempts": correct + wrong, "active_lessons": sorted(active_lessons)}


def _progress_words(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    title = _lesson_title(params)
    limit, cursor = _bounded_limit(params, 50), _cursor(params)
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM words WHERE lesson=? AND (user_id=? OR status='test') AND id>? ORDER BY id LIMIT ?",
            (title, user_id, cursor, limit + 1),
        ).fetchall()
        if not rows:
            owned_lesson = conn.execute(
                "SELECT 1 FROM words WHERE lesson=? AND (user_id=? OR status='test') LIMIT 1",
                (title, user_id),
            ).fetchone()
            if not owned_lesson:
                raise McpServiceError("LESSON_NOT_FOUND", "lesson was not found", status=404)
        page = rows[:limit]
        word_ids = {int(row["id"]) for row in page}
        events = conn.execute(
            "SELECT event_type,event_ts,payload FROM progress_events WHERE user_id=? AND scope='learn' ORDER BY event_ts DESC,id DESC LIMIT 5000",
            (user_id,),
        ).fetchall()
    stats = {word_id: {"attempts": 0, "correct": 0, "wrong": 0, "last_attempt_at": None} for word_id in word_ids}
    for event in events:
        try:
            payload = json.loads(event["payload"] or "{}")
            state = payload.get("state") if isinstance(payload, dict) else {}
            word_id = int((state or {}).get("word_id"))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        if word_id not in stats:
            continue
        item = stats[word_id]
        item["attempts"] += 1
        if item["last_attempt_at"] is None:
            item["last_attempt_at"] = int(event["event_ts"] or 0)
        reason = str((state or {}).get("reason") or "")
        if event["event_type"] == "word_correct" or reason == "answer_ok":
            item["correct"] += 1
        elif event["event_type"] == "word_wrong" or reason == "answer_wrong":
            item["wrong"] += 1
    items = [{**_serialize_word(row, user_id), "progress": stats[int(row["id"])]} for row in page]
    return {"items": items, "next_cursor": int(page[-1]["id"]) if len(rows) > limit else None, "events_window": 5000}


def _learning_recommendation(user_id: str, _params: dict[str, Any]) -> dict[str, Any]:
    difficult = _difficult_words(user_id, {"limit": 20, "cursor": 0})["items"]
    if difficult:
        return {"action": "review_difficult", "lesson": difficult[0].get("lesson"), "word_count": len(difficult), "reason": "difficult_words_pending"}
    lessons = _lessons_list(user_id, {"include_hidden": False})["items"]
    if lessons:
        return {"action": "continue_lesson", "lesson": lessons[0].get("lesson"), "reason": "next_visible_lesson"}
    return {"action": "create_lesson", "lesson": None, "reason": "no_visible_lessons"}


def _progress_record_many(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    items = params.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_PROGRESS_ITEMS:
        raise McpServiceError("INVALID_PROGRESS", "items must be a bounded non-empty list")
    def record() -> dict[str, Any]:
        return _store_progress_items(user_id, items)
    return _idempotent(user_id, "progress_record_many", params, record)


def _store_progress_items(user_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    """Write events using the shared progress event contract."""
    now_ms = int(time.time() * 1000)
    rows = []
    with _conn() as conn:
        for index, item in enumerate(items):
            if not isinstance(item, dict) or str(item.get("result") or "") not in {"correct", "wrong", "learned"}:
                raise McpServiceError("INVALID_PROGRESS", f"invalid progress item at index {index}")
            try:
                word_id = int(item.get("word_id"))
            except (TypeError, ValueError):
                raise McpServiceError("INVALID_PROGRESS", f"invalid word_id at index {index}")
            _assert_word_access(conn, user_id, word_id, allow_test=True)
            word = conn.execute("SELECT lesson FROM words WHERE id=?", (word_id,)).fetchone()
            result = str(item["result"])
            event_type = "word_correct" if result in {"correct", "learned"} else "word_wrong"
            event_ts = int(item.get("occurred_at") or now_ms)
            payload = {"scope": "learn", "type": event_type, "ts": event_ts, "state": {"word_id": word_id, "lesson": word["lesson"], "reason": "answer_ok" if event_type == "word_correct" else "answer_wrong"}}
            rows.append((user_id, "learn", event_type, event_ts, json.dumps(payload, ensure_ascii=False)))
        conn.executemany("INSERT INTO progress_events(user_id,scope,event_type,event_ts,payload) VALUES(?,?,?,?,?)", rows)
        conn.commit()
    return {"stored": len(rows)}


def _family_status(user_id: str, _params: dict[str, Any]) -> dict[str, Any]:
    return _routes()._family_status(user_id)


def _family_children(user_id: str, _params: dict[str, Any]) -> dict[str, Any]:
    status = _routes()._family_status(user_id)
    return {"items": status.get("children", [])}


def _family_child_languages_get(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
    return {"child_user_id": child_id, **_languages_get(child_id, {})}


def _family_child_languages_update(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
    result = _languages_update(child_id, {"languages": params.get("languages")})
    return {"child_user_id": child_id, **result}


def _linked_child(conn: sqlite3.Connection, parent_user_id: str, child_user_id: str) -> None:
    if not child_user_id:
        raise McpServiceError("CHILD_REQUIRED", "child_user_id is required")
    if not conn.execute(
        "SELECT 1 FROM parent_child_links WHERE parent_user_id=? AND child_user_id=?",
        (parent_user_id, child_user_id),
    ).fetchone():
        raise McpServiceError("CHILD_NOT_LINKED", "child is not linked to this parent", status=403)


def _owned_lesson(conn: sqlite3.Connection, parent_user_id: str, lesson: str) -> None:
    if conn.execute("SELECT 1 FROM words WHERE user_id=? AND lesson=?", (parent_user_id, lesson)).fetchone():
        return
    table = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_lessons'").fetchone()
    if table and conn.execute("SELECT 1 FROM user_lessons WHERE user_id=? AND lesson=?", (parent_user_id, lesson)).fetchone():
        return
    raise McpServiceError("LESSON_NOT_FOUND", "lesson was not found", status=404)


def _family_child_progress(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    if not child_id:
        raise McpServiceError("CHILD_REQUIRED", "child_user_id is required")
    with _conn() as conn:
        linked = conn.execute("SELECT 1 FROM parent_child_links WHERE parent_user_id=? AND child_user_id=?", (user_id, child_id)).fetchone()
    if not linked:
        raise McpServiceError("CHILD_NOT_LINKED", "child is not linked to this parent", status=403)
    try:
        days = int(params.get("days", 7))
    except (TypeError, ValueError):
        days = 7
    if days not in {7, 30, 90}:
        raise McpServiceError("INVALID_PERIOD", "days must be 7, 30 or 90")
    dashboard = _routes()._family_dashboard_data(user_id, days, 0)
    child = next((item for item in dashboard.get("children", []) if str(item.get("user_id")) == child_id), None)
    if not child:
        raise McpServiceError("CHILD_NOT_LINKED", "child is not linked to this parent", status=403)
    return child


def _family_child_progress_record(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    item = {key: params.get(key) for key in ("word_id", "result", "occurred_at")}
    return _family_child_progress_record_many(user_id, {
        "child_user_id": child_id,
        "items": [item],
        "idempotency_key": params.get("idempotency_key"),
        "_single": True,
    })


def _family_child_progress_record_many(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    if not child_id or child_id == user_id:
        raise McpServiceError("CHILD_REQUIRED", "child_user_id must identify a linked child")
    items = params.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_PROGRESS_ITEMS:
        raise McpServiceError("INVALID_PROGRESS", "items must be a bounded non-empty list")
    # Resolve through the same visible child list exposed to the parent, then
    # re-check the authoritative link before writing.
    visible_children = _family_children(user_id, {}).get("items", [])
    if child_id not in {str(child.get("user_id")) for child in visible_children}:
        raise McpServiceError("CHILD_NOT_LINKED", "child is not linked to this parent", status=403)
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise McpServiceError("INVALID_PROGRESS", f"invalid progress item at index {index}")
            try:
                word_id = int(item.get("word_id"))
            except (TypeError, ValueError):
                raise McpServiceError("INVALID_PROGRESS", f"invalid word_id at index {index}")
            word = conn.execute("SELECT user_id,lesson FROM words WHERE id=?", (word_id,)).fetchone()
            if not word:
                raise McpServiceError("WORD_NOT_FOUND", "word was not found", status=404)
            assigned = conn.execute(
                "SELECT 1 FROM family_lesson_assignments WHERE parent_user_id=? AND child_user_id=? AND lesson=?",
                (user_id, child_id, str(word["lesson"] or "")),
            ).fetchone()
            if str(word["user_id"]) != user_id or not assigned:
                raise McpServiceError("FORBIDDEN", "word is not available to this child through an assigned lesson", status=403)
    def record() -> dict[str, Any]:
        return _store_progress_items(child_id, items)
    result = _idempotent(user_id, "family_child_progress_record_many", params, record)
    if params.get("_single"):
        return {"stored": True, "child_user_id": child_id, "word_id": int(items[0]["word_id"]), "occurred_at": int(items[0].get("occurred_at") or time.time() * 1000)}
    return {"stored": result["stored"], "child_user_id": child_id}


def _activate_assignment(conn: sqlite3.Connection, parent_id: str, child_id: str, lesson: str) -> None:
    """Insert or re-activate an assignment; an archived one comes back as the
    newest active lesson."""
    now_ms = int(time.time() * 1000)
    conn.execute(
        "INSERT INTO family_lesson_assignments(parent_user_id,child_user_id,lesson,created_at,activated_at,archived_at) VALUES(?,?,?,?,?,NULL) "
        "ON CONFLICT(parent_user_id,child_user_id,lesson) DO UPDATE SET "
        "activated_at=CASE WHEN family_lesson_assignments.archived_at IS NULL THEN COALESCE(family_lesson_assignments.activated_at,family_lesson_assignments.created_at) ELSE excluded.activated_at END, "
        "archived_at=NULL",
        (parent_id, child_id, lesson, now_ms, now_ms),
    )


def _priority_lesson(conn: sqlite3.Connection, parent_id: str, child_id: str) -> str:
    row = conn.execute(
        "SELECT lesson FROM child_lesson_priorities WHERE child_user_id=? AND parent_user_id=?",
        (child_id, parent_id),
    ).fetchone()
    return str(row["lesson"]) if row else ""


def _clear_priority(conn: sqlite3.Connection, parent_id: str, child_id: str) -> bool:
    now_ms = int(time.time() * 1000)
    conn.execute(
        "UPDATE child_lesson_priority_history SET ended_at=? WHERE child_user_id=? AND parent_user_id=? AND ended_at IS NULL",
        (now_ms, child_id, parent_id),
    )
    cursor = conn.execute("DELETE FROM child_lesson_priorities WHERE child_user_id=? AND parent_user_id=?", (child_id, parent_id))
    return bool(cursor.rowcount)


def _enforce_active_limit(conn: sqlite3.Connection, parent_id: str, child_id: str, keep: int = MAX_ACTIVE_CHILD_LESSONS) -> list[str]:
    """Archive everything beyond the newest *keep* active assignments of this
    child. The priority lesson is pinned: it always stays active and counts
    toward the limit, so it can never be archived by automatic cleanup."""
    keep = max(1, min(MAX_PAGE_SIZE, int(keep)))
    rows = conn.execute(
        "SELECT lesson FROM family_lesson_assignments WHERE parent_user_id=? AND child_user_id=? AND archived_at IS NULL "
        "ORDER BY COALESCE(activated_at,created_at) DESC, lesson",
        (parent_id, child_id),
    ).fetchall()
    active = [str(row["lesson"]) for row in rows]
    priority = _priority_lesson(conn, parent_id, child_id)
    kept: list[str] = [priority] if priority in active else []
    for lesson in active:
        if len(kept) >= keep:
            break
        if lesson not in kept:
            kept.append(lesson)
    to_archive = [lesson for lesson in active if lesson not in kept]
    if to_archive:
        now_ms = int(time.time() * 1000)
        conn.executemany(
            "UPDATE family_lesson_assignments SET archived_at=? WHERE parent_user_id=? AND child_user_id=? AND lesson=? AND archived_at IS NULL",
            [(now_ms, parent_id, child_id, lesson) for lesson in to_archive],
        )
    return to_archive


def _family_child_lesson_assign(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    lesson = _lesson_title(params)
    def assign() -> dict[str, Any]:
        with _conn() as conn:
            _linked_child(conn, user_id, child_id)
            _owned_lesson(conn, user_id, lesson)
            _require_complete_assignment(user_id, lesson, child_id)
            _activate_assignment(conn, user_id, child_id, lesson)
            if _routes()._child_lesson_owner(conn, child_id, lesson) != user_id:
                raise McpServiceError("ASSIGNMENT_NOT_VISIBLE", "assigned lesson is not visible to the child", status=409)
            archived = _enforce_active_limit(conn, user_id, child_id)
            conn.commit()
        return {"child_user_id": child_id, "lesson": lesson, "assigned": True, "archived": archived, "active_limit": MAX_ACTIVE_CHILD_LESSONS}
    return _idempotent(user_id, "family_child_lesson_assign", params, assign)


def _family_children_lesson_assign(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_ids = list(dict.fromkeys(str(value or "").strip() for value in (params.get("child_user_ids") or []) if str(value or "").strip()))
    if not child_ids or len(child_ids) > MAX_PROGRESS_ITEMS:
        raise McpServiceError("INVALID_CHILDREN", "child_user_ids must be a bounded non-empty list")
    lesson = _lesson_title(params)
    def assign() -> dict[str, Any]:
        archived: dict[str, list[str]] = {}
        with _conn() as conn:
            _owned_lesson(conn, user_id, lesson)
            for child_id in child_ids:
                _linked_child(conn, user_id, child_id)
                _require_complete_assignment(user_id, lesson, child_id)
            for child_id in child_ids:
                _activate_assignment(conn, user_id, child_id, lesson)
                if _routes()._child_lesson_owner(conn, child_id, lesson) != user_id:
                    raise McpServiceError("ASSIGNMENT_NOT_VISIBLE", "assigned lesson is not visible to a child", status=409)
                archived[child_id] = _enforce_active_limit(conn, user_id, child_id)
            conn.commit()
        return {"child_user_ids": child_ids, "lesson": lesson, "assigned": len(child_ids), "archived": archived, "active_limit": MAX_ACTIVE_CHILD_LESSONS}
    return _idempotent(user_id, "family_children_lesson_assign", params, assign)


def _family_child_lesson_unassign(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    lesson = _lesson_title(params)
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
        cursor = conn.execute(
            "DELETE FROM family_lesson_assignments WHERE parent_user_id=? AND child_user_id=? AND lesson=?",
            (user_id, child_id, lesson),
        )
        conn.execute(
            "DELETE FROM child_lesson_priorities WHERE child_user_id=? AND parent_user_id=? AND lesson=?",
            (child_id, user_id, lesson),
        )
        conn.execute(
            "UPDATE child_lesson_priority_history SET ended_at=? WHERE child_user_id=? AND parent_user_id=? AND lesson=? AND ended_at IS NULL",
            (int(time.time() * 1000), child_id, user_id, lesson),
        )
        conn.commit()
    return {"child_user_id": child_id, "lesson": lesson, "unassigned": bool(cursor.rowcount)}


def _family_priority_set(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    title = _lesson_title(params)
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
        assignment = conn.execute("SELECT archived_at FROM family_lesson_assignments WHERE parent_user_id=? AND child_user_id=? AND lesson=?", (user_id, child_id, title)).fetchone()
        if not assignment or _routes()._child_lesson_owner(conn, child_id, title) != user_id:
            raise McpServiceError("LESSON_NOT_ASSIGNED", "lesson is not assigned to this child", status=404)
        restored = False
        if assignment["archived_at"] is not None:
            # A priority lesson must be active; bring it back before pinning.
            _activate_assignment(conn, user_id, child_id, title)
            restored = True
        _pin_priority(conn, user_id, child_id, title)
        archived = _enforce_active_limit(conn, user_id, child_id) if restored else []
        conn.commit()
    return {"child_user_id": child_id, "lesson": title, "restored": restored, "archived": archived}


def _pin_priority(conn: sqlite3.Connection, parent_id: str, child_id: str, title: str) -> None:
    now_ms = int(time.time() * 1000)
    conn.execute(
        "INSERT INTO child_lesson_priorities(child_user_id,lesson,parent_user_id,updated_at) VALUES(?,?,?,?) "
        "ON CONFLICT(child_user_id) DO UPDATE SET lesson=excluded.lesson,parent_user_id=excluded.parent_user_id,updated_at=excluded.updated_at",
        (child_id, title, parent_id, now_ms),
    )
    conn.execute(
        "UPDATE child_lesson_priority_history SET ended_at=? WHERE child_user_id=? AND parent_user_id=? AND ended_at IS NULL AND lesson<>?",
        (now_ms, child_id, parent_id, title),
    )
    if not conn.execute("SELECT 1 FROM child_lesson_priority_history WHERE child_user_id=? AND parent_user_id=? AND lesson=? AND ended_at IS NULL", (child_id, parent_id, title)).fetchone():
        conn.execute(
            "INSERT INTO child_lesson_priority_history(child_user_id,lesson,parent_user_id,started_at,ended_at) VALUES(?,?,?,?,NULL)",
            (child_id, title, parent_id, now_ms),
        )


def _family_child_priority_clear(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
        now_ms = int(time.time() * 1000)
        conn.execute("UPDATE child_lesson_priority_history SET ended_at=? WHERE child_user_id=? AND parent_user_id=? AND ended_at IS NULL", (now_ms, child_id, user_id))
        cursor = conn.execute("DELETE FROM child_lesson_priorities WHERE child_user_id=? AND parent_user_id=?", (child_id, user_id))
        conn.commit()
    return {"child_user_id": child_id, "cleared": bool(cursor.rowcount)}


def _family_child_lessons(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    status = str(params.get("status") or "active").strip().lower()
    if status not in {"active", "archived", "all"}:
        raise McpServiceError("INVALID_STATUS", "status must be active, archived or all")
    where = ["a.parent_user_id=?", "a.child_user_id=?"]
    if status == "active":
        where.append("a.archived_at IS NULL")
    elif status == "archived":
        where.append("a.archived_at IS NOT NULL")
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
        priority = _priority_lesson(conn, user_id, child_id)
        rows = conn.execute(
            "SELECT a.lesson,a.created_at,a.activated_at,a.archived_at,COUNT(w.id) AS words_count,MAX(w.id) AS upload_order "
            "FROM family_lesson_assignments a LEFT JOIN words w ON w.user_id=a.parent_user_id AND w.lesson=a.lesson "
            "WHERE " + " AND ".join(where) + " GROUP BY a.lesson ORDER BY COALESCE(a.activated_at,a.created_at) DESC,a.lesson",
            (user_id, child_id),
        ).fetchall()
    items = []
    for row in rows:
        items.append({
            "lesson": str(row["lesson"]),
            "words_count": int(row["words_count"] or 0),
            "upload_order": int(row["upload_order"] or 0),
            "assigned_at": int(row["created_at"] or 0),
            "activated_at": int(row["activated_at"] or row["created_at"] or 0),
            "archived_at": int(row["archived_at"]) if row["archived_at"] is not None else None,
            "status": "archived" if row["archived_at"] is not None else "active",
            "is_priority": str(row["lesson"]) == priority,
        })
    return {"child_user_id": child_id, "status": status, "priority_lesson": priority or None, "active_limit": MAX_ACTIVE_CHILD_LESSONS, "languages": _routes()._get_user_languages(child_id), "items": items}


def _family_child_lesson_archive(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    lesson = _lesson_title(params)
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
        row = conn.execute("SELECT archived_at FROM family_lesson_assignments WHERE parent_user_id=? AND child_user_id=? AND lesson=?", (user_id, child_id, lesson)).fetchone()
        if not row:
            raise McpServiceError("LESSON_NOT_ASSIGNED", "lesson is not assigned to this child", status=404)
        priority_cleared = False
        if _priority_lesson(conn, user_id, child_id) == lesson:
            # Manual archive of the priority lesson: release the priority
            # first so it never points at an inactive lesson.
            priority_cleared = _clear_priority(conn, user_id, child_id)
        already = row["archived_at"] is not None
        if not already:
            conn.execute(
                "UPDATE family_lesson_assignments SET archived_at=? WHERE parent_user_id=? AND child_user_id=? AND lesson=?",
                (int(time.time() * 1000), user_id, child_id, lesson),
            )
        conn.commit()
    return {"child_user_id": child_id, "lesson": lesson, "archived": True, "already_archived": already, "priority_cleared": priority_cleared}


def _family_child_lesson_restore(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    lesson = _lesson_title(params)
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
        row = conn.execute("SELECT archived_at FROM family_lesson_assignments WHERE parent_user_id=? AND child_user_id=? AND lesson=?", (user_id, child_id, lesson)).fetchone()
        if not row:
            raise McpServiceError("LESSON_NOT_ASSIGNED", "lesson is not assigned to this child", status=404)
        was_archived = row["archived_at"] is not None
        _activate_assignment(conn, user_id, child_id, lesson)
        if _routes()._child_lesson_owner(conn, child_id, lesson) != user_id:
            raise McpServiceError("ASSIGNMENT_NOT_VISIBLE", "restored lesson is not visible to the child", status=409)
        archived = _enforce_active_limit(conn, user_id, child_id)
        conn.commit()
    return {"child_user_id": child_id, "lesson": lesson, "restored": was_archived, "active": True, "archived": archived, "active_limit": MAX_ACTIVE_CHILD_LESSONS}


def _family_child_lessons_cleanup(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    try:
        keep = int(params.get("keep") or MAX_ACTIVE_CHILD_LESSONS)
    except (TypeError, ValueError):
        raise McpServiceError("INVALID_KEEP", "keep must be an integer")
    if not 1 <= keep <= MAX_ACTIVE_CHILD_LESSONS:
        raise McpServiceError("INVALID_KEEP", f"keep must be between 1 and {MAX_ACTIVE_CHILD_LESSONS}")
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
        archived = _enforce_active_limit(conn, user_id, child_id, keep)
        active = [str(row[0]) for row in conn.execute(
            "SELECT lesson FROM family_lesson_assignments WHERE parent_user_id=? AND child_user_id=? AND archived_at IS NULL ORDER BY COALESCE(activated_at,created_at) DESC,lesson",
            (user_id, child_id),
        )]
        conn.commit()
    return {"child_user_id": child_id, "keep": keep, "archived": archived, "active": active}


def _family_child_lesson_words(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    lesson = _lesson_title(params)
    limit, cursor = _bounded_limit(params, 50), _cursor(params)
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
        if not conn.execute("SELECT 1 FROM family_lesson_assignments WHERE parent_user_id=? AND child_user_id=? AND lesson=?", (user_id, child_id, lesson)).fetchone():
            raise McpServiceError("LESSON_NOT_ASSIGNED", "lesson is not assigned to this child", status=404)
        rows = conn.execute(
            "SELECT w.*,COALESCE(f.difficult,0) AS difficult FROM words w "
            "LEFT JOIN user_word_flags f ON f.user_id=? AND f.word_id=w.id "
            "WHERE w.user_id=? AND w.lesson=? AND w.id>? ORDER BY w.id LIMIT ?",
            (child_id, user_id, lesson, cursor, limit + 1),
        ).fetchall()
    page = rows[:limit]
    return {"child_user_id": child_id, "lesson": lesson, "items": [_serialize_word(row, child_id) for row in page], "next_cursor": int(page[-1]["id"]) if len(rows) > limit else None}


def _subscriptions_list(_user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    limit, cursor = _bounded_limit(params, 50), _cursor(params)
    search = str(params.get("search") or "").strip().lower()
    status_filter = str(params.get("status") or "").strip().lower()
    provider_filter = str(params.get("provider") or "").strip().lower()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT u.rowid AS cursor_id,u.user_id,u.username,u.first_name,u.last_name,u.account_type,COALESCE(u.is_active,1) AS is_active,u.google_email FROM users u WHERE u.rowid>? ORDER BY u.rowid LIMIT ?",
            (cursor, MAX_PAGE_SIZE + 1),
        ).fetchall()
        items = []
        for row in rows:
            summary = _admin_user_summary(conn, row)
            subscription = summary["subscription"]
            haystack = " ".join([summary["user_id"], summary["display_name"], summary["email"]]).lower()
            if search and search not in haystack:
                continue
            if status_filter and status_filter not in {str(subscription["status"]).lower(), "unlimited" if subscription["is_unlimited"] else "", "manual" if subscription["manual_access"] else ""}:
                continue
            if provider_filter and provider_filter != str(subscription["provider"]).lower():
                continue
            items.append({"_cursor": int(row["cursor_id"]), "user_id": summary["user_id"], "display_name": summary["display_name"], "email": summary["email"], **subscription})
    page = items[:limit]
    return {"items": [{key: value for key, value in item.items() if key != "_cursor"} for item in page], "next_cursor": int(page[-1]["_cursor"]) if len(rows) > limit else None}


def _subscription_access(user_id: str, params: dict[str, Any], *, grant: bool) -> dict[str, Any]:
    target = str(params.get("user_id") or "").strip()
    if not target:
        raise McpServiceError("USER_REQUIRED", "user_id is required")
    if params.get("confirm") is not True:
        raise McpServiceError("CONFIRMATION_REQUIRED", "confirm=true is required")
    now_ms = int(time.time() * 1000)
    with _conn() as conn:
        if not conn.execute("SELECT 1 FROM users WHERE user_id=?", (target,)).fetchone():
            raise McpServiceError("USER_NOT_FOUND", "user was not found", status=404)
        if grant:
            expires = now_ms + 100 * 365 * 86400000
            previous = conn.execute("SELECT status,current_period_ends_at,provider FROM user_subscriptions WHERE user_id=?", (target,)).fetchone()
            conn.execute(
                "INSERT INTO user_subscriptions(user_id,status,trial_started_at,trial_ends_at,current_period_ends_at,provider,updated_at) "
                "VALUES(?,'active',?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET status='active',current_period_ends_at=excluded.current_period_ends_at,provider='manual',updated_at=excluded.updated_at",
                (target, now_ms, now_ms, expires, "manual", now_ms),
            )
        else:
            expires = None
            previous = conn.execute("SELECT status,current_period_ends_at,provider FROM user_subscriptions WHERE user_id=?", (target,)).fetchone()
            conn.execute("UPDATE user_subscriptions SET status='trial',current_period_ends_at=NULL,provider=NULL,updated_at=? WHERE user_id=?", (now_ms, target))
        conn.execute(
            "INSERT INTO mcp_admin_audit_log(created_at,admin_user_id,target_user_id,action,old_value,new_value) VALUES(?,?,?,?,?,?)",
            (
                now_ms, user_id, target, "subscription_manual_grant" if grant else "subscription_manual_revoke",
                json.dumps(dict(previous) if previous else {}, sort_keys=True),
                json.dumps({"status": "active" if grant else "trial", "provider": "manual" if grant else None, "expires_at": expires}, sort_keys=True),
            ),
        )
        conn.commit()
    return {"user_id": target, "granted": grant, "expires_at": expires, "changed_by": user_id}


def _admin_subscription_snapshot(conn: sqlite3.Connection, user_id: str, *, is_admin: bool) -> dict[str, Any]:
    if is_admin:
        return {"configured": True, "status": "active", "raw_status": "active", "access": True, "provider": "admin", "is_unlimited": True, "manual_access": True, "current_period_ends_at": None}
    row = conn.execute("SELECT status,trial_started_at,trial_ends_at,current_period_ends_at,provider,cancel_at_period_end FROM user_subscriptions WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        return {"configured": True, "status": "not_started", "raw_status": None, "access": False, "provider": "", "is_unlimited": False, "manual_access": False, "current_period_ends_at": None}
    now_ms = int(time.time() * 1000)
    raw_status = str(row["status"] or "trial")
    trial_end = int(row["trial_ends_at"] or 0)
    period_end = int(row["current_period_ends_at"]) if row["current_period_ends_at"] is not None else None
    access = (raw_status == "trial" and trial_end > now_ms) or (raw_status == "active" and (period_end is None or period_end > now_ms))
    status = raw_status if access else ("trial_expired" if raw_status == "trial" else "expired" if raw_status == "active" else raw_status)
    unlimited = bool(access and period_end and period_end > now_ms + 10 * 365 * 86400000)
    return {"configured": True, "status": status, "raw_status": raw_status, "access": access, "provider": str(row["provider"] or ""), "trial_started_at": int(row["trial_started_at"] or 0), "trial_ends_at": trial_end, "current_period_ends_at": period_end, "cancel_at_period_end": bool(row["cancel_at_period_end"]), "is_unlimited": unlimited, "manual_access": str(row["provider"] or "") == "manual" and unlimited}


def _admin_activity(conn: sqlite3.Connection, user_id: str, days: int, lesson_title: str = "") -> dict[str, Any]:
    since = int(time.time() * 1000) - days * 86400000
    rows = conn.execute("SELECT event_type,event_ts,payload FROM progress_events WHERE user_id=? AND event_ts>=? ORDER BY event_ts", (user_id, since)).fetchall()
    correct = wrong = 0
    active_days: set[str] = set()
    active_lessons: set[str] = set()
    last_activity_at: int | None = None
    daily: dict[str, dict[str, int]] = {}
    for row in rows:
        try:
            payload = json.loads(row["payload"] or "{}")
        except (TypeError, json.JSONDecodeError):
            payload = {}
        state = payload.get("state") if isinstance(payload, dict) else {}
        lesson = str((state or {}).get("lesson") or "")
        if lesson_title and lesson != lesson_title:
            continue
        event_ts = int(row["event_ts"] or 0)
        if event_ts:
            day = time.strftime("%Y-%m-%d", time.gmtime(event_ts / 1000))
            active_days.add(day)
            bucket = daily.setdefault(day, {"correct": 0, "wrong": 0})
            last_activity_at = max(last_activity_at or 0, event_ts)
        else:
            bucket = {"correct": 0, "wrong": 0}
        if lesson:
            active_lessons.add(lesson)
        event_type = str(row["event_type"] or payload.get("type") or "")
        reason = str((state or {}).get("reason") or "")
        if event_type == "word_correct" or reason == "answer_ok":
            correct += 1
            if event_ts: bucket["correct"] += 1
        elif event_type == "word_wrong" or reason == "answer_wrong":
            wrong += 1
            if event_ts: bucket["wrong"] += 1
    return {"days": days, "attempts": correct + wrong, "correct": correct, "wrong": wrong, "accuracy": (correct / (correct + wrong)) if correct + wrong else None, "active_days": len(active_days), "last_activity_at": last_activity_at, "lessons_active": sorted(active_lessons), "study_minutes": None, "learned": None, "progress_by_day": [{"day": day, **daily[day]} for day in sorted(daily)]}


def _admin_user_summary(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    user_id = str(row["user_id"])
    is_admin = _is_admin(user_id)
    languages = [str(item[0]) for item in conn.execute("SELECT lang_code FROM user_language_preferences WHERE user_id=? ORDER BY priority", (user_id,)).fetchall()]
    lessons = int(conn.execute("SELECT COUNT(DISTINCT lesson) FROM words WHERE user_id=? AND COALESCE(lesson,'')<>''", (user_id,)).fetchone()[0])
    words = int(conn.execute("SELECT COUNT(*) FROM words WHERE user_id=?", (user_id,)).fetchone()[0])
    activity = _admin_activity(conn, user_id, 365)
    return {"user_id": user_id, "display_name": _routes()._format_user_name(row), "email": str(row["google_email"] or ""), "account_type": str(row["account_type"] or "standard"), "is_active": bool(row["is_active"]), "is_admin": is_admin, "created_at": None, "last_active_at": activity["last_activity_at"], "subscription": _admin_subscription_snapshot(conn, user_id, is_admin=is_admin), "selected_languages": languages, "lessons_count": lessons, "words_count": words}


def _admin_users_list(_user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    limit, cursor = _bounded_limit(params, 50), _cursor(params)
    search = str(params.get("search") or "").strip()
    account_status = str(params.get("status") or "").strip().lower()
    subscription_status = str(params.get("subscription_status") or "").strip().lower()
    with _conn() as conn:
        where = ["u.rowid>?"]
        values: list[Any] = [cursor]
        if search:
            where.append("(u.user_id LIKE ? OR u.username LIKE ? OR u.first_name LIKE ? OR u.last_name LIKE ? OR COALESCE(u.google_email,'') LIKE ?)")
            values.extend([f"%{search}%"] * 5)
        if account_status in {"active", "inactive"}:
            where.append("COALESCE(u.is_active,1)=?")
            values.append(1 if account_status == "active" else 0)
        rows = conn.execute("SELECT u.rowid AS cursor_id,u.user_id,u.username,u.first_name,u.last_name,u.account_type,COALESCE(u.is_active,1) AS is_active,u.google_email FROM users u WHERE " + " AND ".join(where) + " ORDER BY u.rowid LIMIT ?", [*values, limit + 1]).fetchall()
        page = rows[:limit]
        items = [_admin_user_summary(conn, row) for row in page]
    if subscription_status:
        items = [item for item in items if subscription_status in {str(item["subscription"]["status"]), str(item["subscription"]["provider"]), "unlimited" if item["subscription"]["is_unlimited"] else ""}]
    return {"items": items, "next_cursor": int(page[-1]["cursor_id"]) if len(rows) > limit else None}


def _admin_user_get(_user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    target = str(params.get("user_id") or "").strip()
    if not target:
        raise McpServiceError("USER_REQUIRED", "user_id is required")
    models.ensure_user_tables(Config.DB_PATH)
    with _conn() as conn:
        row = conn.execute("SELECT user_id,username,first_name,last_name,account_type,COALESCE(is_active,1) AS is_active,google_email FROM users WHERE user_id=?", (target,)).fetchone()
        if not row:
            raise McpServiceError("USER_NOT_FOUND", "user was not found", status=404)
        summary = _admin_user_summary(conn, row)
        summary["learning"] = {"ui_language": _routes()._get_ui_language(target), "daily_goal": _routes()._daily_goal_settings(target), "difficult_words": int(conn.execute("SELECT COUNT(*) FROM user_word_flags WHERE user_id=? AND difficult=1", (target,)).fetchone()[0]), "visible_lessons": int(conn.execute("SELECT COUNT(DISTINCT w.lesson) FROM words w LEFT JOIN user_lessons l ON l.user_id=w.user_id AND l.lesson=w.lesson WHERE w.user_id=? AND COALESCE(l.hidden,0)=0", (target,)).fetchone()[0]), "hidden_lessons": int(conn.execute("SELECT COUNT(DISTINCT lesson) FROM user_lessons WHERE user_id=? AND hidden=1", (target,)).fetchone()[0])}
        summary["activity"] = _admin_activity(conn, target, 30)
    return summary


def _admin_user_progress(_user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    target = str(params.get("user_id") or "").strip()
    if not target:
        raise McpServiceError("USER_REQUIRED", "user_id is required")
    try:
        days = max(1, min(365, int(params.get("days", 30))))
    except (TypeError, ValueError):
        raise McpServiceError("INVALID_PERIOD", "days must be between 1 and 365")
    with _conn() as conn:
        if not conn.execute("SELECT 1 FROM users WHERE user_id=?", (target,)).fetchone():
            raise McpServiceError("USER_NOT_FOUND", "user was not found", status=404)
        result = _admin_activity(conn, target, days, str(params.get("lesson_title") or "").strip())
        result.update({"user_id": target, "total_words": int(conn.execute("SELECT COUNT(*) FROM words WHERE user_id=?", (target,)).fetchone()[0]), "difficult_words_count": int(conn.execute("SELECT COUNT(*) FROM user_word_flags WHERE user_id=? AND difficult=1", (target,)).fetchone()[0])})
    return result


def _admin_user_lessons(_user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    target = str(params.get("user_id") or "").strip()
    if not target:
        raise McpServiceError("USER_REQUIRED", "user_id is required")
    limit, cursor = _bounded_limit(params, 50), _cursor(params)
    include_hidden = bool(params.get("include_hidden", False))
    models.ensure_user_tables(Config.DB_PATH)
    with _conn() as conn:
        if not conn.execute("SELECT 1 FROM users WHERE user_id=?", (target,)).fetchone():
            raise McpServiceError("USER_NOT_FOUND", "user was not found", status=404)
        where = ["w.user_id=?", "MAX(w.id)>?"]
        values: list[Any] = [target, cursor]
        if not include_hidden:
            where.append("COALESCE(l.hidden,0)=0")
        rows = conn.execute(
            "SELECT w.lesson,MAX(w.id) AS cursor_id,COUNT(*) AS word_count,COALESCE(l.hidden,0) AS hidden "
            "FROM words w LEFT JOIN user_lessons l ON l.user_id=w.user_id AND l.lesson=w.lesson "
            "WHERE w.user_id=? GROUP BY w.lesson HAVING " + " AND ".join(where[1:]) + " ORDER BY cursor_id LIMIT ?",
            [*values, limit + 1],
        ).fetchall()
    page = rows[:limit]
    return {"items": [{"lesson": str(row["lesson"] or ""), "word_count": int(row["word_count"]), "hidden": bool(row["hidden"]), "order": int(row["cursor_id"])} for row in page], "next_cursor": int(page[-1]["cursor_id"]) if len(rows) > limit else None}


def _admin_user_words_search(_user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    target = str(params.get("user_id") or "").strip()
    query = str(params.get("query") or "").strip()
    if not target or not query:
        raise McpServiceError("USER_AND_QUERY_REQUIRED", "user_id and query are required")
    limit = _bounded_limit(params, 25)
    lesson = str(params.get("lesson_title") or "").strip()
    languages = _word_languages()
    with _conn() as conn:
        if not conn.execute("SELECT 1 FROM users WHERE user_id=?", (target,)).fetchone():
            raise McpServiceError("USER_NOT_FOUND", "user was not found", status=404)
        filter_sql = " OR ".join([f'w."{lang}" LIKE ?' for lang in languages])
        where = ["w.user_id=?", f"({filter_sql})"]
        values: list[Any] = [target, *[f"%{query}%"] * len(languages)]
        if lesson:
            where.append("w.lesson=?")
            values.append(lesson)
        rows = conn.execute("SELECT w.*,0 AS difficult FROM words w WHERE " + " AND ".join(where) + " ORDER BY w.id DESC LIMIT ?", [*values, limit]).fetchall()
    return {"items": [_serialize_word(row, target) for row in rows]}


def _admin_analytics_summary(_user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        days = max(1, min(365, int(params.get("days", 30))))
    except (TypeError, ValueError):
        raise McpServiceError("INVALID_PERIOD", "days must be between 1 and 365")
    since = int(time.time() * 1000) - days * 86400000
    with _conn() as conn:
        users = [str(row[0]) for row in conn.execute("SELECT user_id FROM users").fetchall()]
        active_users = int(conn.execute("SELECT COUNT(DISTINCT user_id) FROM progress_events WHERE event_ts>=?", (since,)).fetchone()[0])
        subscription_rows = conn.execute("SELECT status,provider,current_period_ends_at FROM user_subscriptions").fetchall()
        attempts = correct = wrong = 0
        for row in conn.execute("SELECT event_type,payload FROM progress_events WHERE event_ts>=?", (since,)).fetchall():
            try:
                payload = json.loads(row["payload"] or "{}")
            except (TypeError, json.JSONDecodeError):
                payload = {}
            reason = str(((payload.get("state") or {}) if isinstance(payload, dict) else {}).get("reason") or "")
            if row["event_type"] == "word_correct" or reason == "answer_ok":
                correct += 1
            elif row["event_type"] == "word_wrong" or reason == "answer_wrong":
                wrong += 1
        attempts = correct + wrong
        providers: dict[str, int] = {}
        for row in subscription_rows:
            provider = str(row["provider"] or "none")
            providers[provider] = providers.get(provider, 0) + 1
        manual_unlimited = sum(1 for row in subscription_rows if str(row["provider"] or "") == "manual" and int(row["current_period_ends_at"] or 0) > int(time.time() * 1000) + 10 * 365 * 86400000)
        result = {"days": days, "users": {"total_users": len(users), "active_users": active_users, "admins": sum(1 for user_id in users if _is_admin(user_id)), "users_with_subscription": sum(1 for row in subscription_rows if str(row["status"] or "") == "active"), "users_without_subscription": max(0, len(users) - len(subscription_rows))}, "subscriptions": {"active": sum(1 for row in subscription_rows if str(row["status"] or "") == "active"), "trials": sum(1 for row in subscription_rows if str(row["status"] or "") == "trial"), "manual_unlimited": manual_unlimited, "provider_breakdown": providers}, "learning": {"total_lessons": int(conn.execute("SELECT COUNT(*) FROM (SELECT DISTINCT user_id,lesson FROM words WHERE COALESCE(lesson,'')<>'')").fetchone()[0]), "total_words": int(conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]), "total_attempts": attempts, "correct_answers": correct, "wrong_answers": wrong, "difficult_words": int(conn.execute("SELECT COUNT(*) FROM user_word_flags WHERE difficult=1").fetchone()[0]), "active_learners": active_users, "average_attempts_per_active_user": (attempts / active_users) if active_users else None}}
    return result


def _admin_audit_log_list(_user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    limit, cursor = _bounded_limit(params, 50), _cursor(params)
    with _conn() as conn:
        rows = conn.execute("SELECT id,created_at,admin_user_id,target_user_id,action,old_value,new_value,request_id FROM mcp_admin_audit_log WHERE id>? ORDER BY id DESC LIMIT ?", (cursor, limit + 1)).fetchall()
    page = rows[:limit]
    return {"items": [{"id": int(row["id"]), "created_at": int(row["created_at"]), "admin_user_id": str(row["admin_user_id"]), "target_user_id": str(row["target_user_id"]), "action": str(row["action"]), "old_value": json.loads(row["old_value"]), "new_value": json.loads(row["new_value"]), "request_id": str(row["request_id"])} for row in page], "next_cursor": int(page[-1]["id"]) if len(rows) > limit else None}


def _admin_users_search(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    query = str(params.get("query") or "").strip()
    if not query:
        raise McpServiceError("QUERY_REQUIRED", "query is required")
    return _admin_users_list(user_id, {"search": query, "limit": params.get("limit", 25), "cursor": params.get("cursor", 0)})


def _admin_analytics_users(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    result = _admin_users_list(user_id, {"limit": params.get("limit", 50), "cursor": params.get("cursor", 0), "search": params.get("search", "")})
    mode = str(params.get("sort") or "active").lower()
    if mode == "inactive":
        result["items"].sort(key=lambda item: item["last_active_at"] or 0)
    else:
        result["items"].sort(key=lambda item: item["last_active_at"] or 0, reverse=True)
    return result


# ---------------------------------------------------------------------------
# Difficult words for a linked child (parent-managed) and error-based candidates
# ---------------------------------------------------------------------------

def _family_child_difficult_words_list(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    limit, cursor = _bounded_limit(params, 50), _cursor(params)
    lesson = str(params.get("lesson_title") or "").strip()
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
        rows = _difficult_rows(conn, child_id, owner_ids=[user_id, child_id], lesson=lesson, cursor=cursor, limit=limit)
    result = _difficult_page(rows, child_id, limit)
    for item, row in zip(result["items"], rows):
        item["owner_user_id"] = str(row["user_id"])
    return {"child_user_id": child_id, **result}


def _family_child_difficult_set(user_id: str, params: dict[str, Any], difficult: bool) -> dict[str, Any]:
    """A parent flags words for one linked child only: the parent's canonical
    words assigned to that child (active or archived) or the child's own words."""
    child_id = str(params.get("child_user_id") or "").strip()
    word_ids = _word_ids(params)
    source = str(params.get("source") or "parent")
    params = {**params, "source": source}
    source = _difficult_source(params)
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
        qmarks = ",".join("?" for _ in word_ids)
        rows = {int(row["id"]): row for row in conn.execute(f"SELECT id,user_id,lesson FROM words WHERE id IN ({qmarks})", word_ids)}
        for word_id in word_ids:
            row = rows.get(word_id)
            if not row:
                raise McpServiceError("WORD_NOT_FOUND", "one or more words were not found", status=404, details={"word_id": word_id})
            owner = str(row["user_id"])
            if owner == child_id:
                continue
            assigned = owner == user_id and conn.execute(
                "SELECT 1 FROM family_lesson_assignments WHERE parent_user_id=? AND child_user_id=? AND lesson=?",
                (user_id, child_id, str(row["lesson"] or "")),
            ).fetchone()
            if not assigned:
                raise McpServiceError("FORBIDDEN", "word is not assigned to this child", status=403, details={"word_id": word_id})
        _write_difficult_flags(conn, child_id, word_ids, difficult, source)
        conn.commit()
    return {"child_user_id": child_id, "updated": len(word_ids), "difficult": difficult, "word_ids": word_ids, "source": source}


def _difficult_candidates(target_user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Words the target user keeps getting wrong. Read-only: the caller decides
    whether to turn them into difficult flags (source=auto_errors)."""
    try:
        days = max(1, min(365, int(params.get("days", 30))))
        min_wrong = max(1, min(100, int(params.get("min_wrong", 2))))
    except (TypeError, ValueError):
        raise McpServiceError("INVALID_PERIOD", "days and min_wrong must be integers")
    limit = _bounded_limit(params, 50)
    lesson = str(params.get("lesson_title") or "").strip()
    since = int(time.time() * 1000) - days * 86400000
    stats: dict[int, dict[str, Any]] = {}
    with _conn() as conn:
        events = conn.execute(
            "SELECT event_type,event_ts,payload FROM progress_events WHERE user_id=? AND scope='learn' "
            "AND (CASE WHEN event_ts<100000000000 THEN event_ts*1000 ELSE event_ts END)>=? ORDER BY event_ts DESC LIMIT 5000",
            (target_user_id, since),
        ).fetchall()
        for event in events:
            try:
                payload = json.loads(event["payload"] or "{}")
                state = payload.get("state") if isinstance(payload, dict) else {}
                word_id = int((state or {}).get("word_id"))
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            item = stats.setdefault(word_id, {"attempts": 0, "correct": 0, "wrong": 0, "last_wrong_at": None})
            item["attempts"] += 1
            reason = str((state or {}).get("reason") or "")
            event_ts = int(event["event_ts"] or 0)
            if event["event_type"] == "word_correct" or reason == "answer_ok":
                item["correct"] += 1
            elif event["event_type"] == "word_wrong" or reason == "answer_wrong":
                item["wrong"] += 1
                item["last_wrong_at"] = max(item["last_wrong_at"] or 0, event_ts)
        candidates = sorted((wid for wid, st in stats.items() if st["wrong"] >= min_wrong), key=lambda wid: (-stats[wid]["wrong"], wid))
        items: list[dict[str, Any]] = []
        for chunk_start in range(0, len(candidates), 100):
            chunk = candidates[chunk_start:chunk_start + 100]
            qmarks = ",".join("?" for _ in chunk)
            where = [f"w.id IN ({qmarks})", _VISIBLE_WORD_SQL]
            values: list[Any] = [target_user_id, *chunk, target_user_id, target_user_id]
            if lesson:
                where.append("w.lesson=?")
                values.append(lesson)
            rows = conn.execute(
                "SELECT w.*, COALESCE(f.difficult,0) AS difficult FROM words w "
                "LEFT JOIN user_word_flags f ON f.word_id=w.id AND f.user_id=? WHERE " + " AND ".join(where),
                values,
            ).fetchall()
            by_id = {int(row["id"]): row for row in rows}
            for word_id in chunk:
                row = by_id.get(word_id)
                if row is None:
                    continue
                item = _serialize_word(row, target_user_id)
                item.update({"errors": stats[word_id], "already_difficult": bool(row["difficult"])})
                items.append(item)
            if len(items) >= limit:
                break
    items = items[:limit]
    return {
        "user_id": target_user_id, "days": days, "min_wrong": min_wrong, "events_window": 5000,
        "items": items,
        "suggested_word_ids": [item["id"] for item in items if not item["already_difficult"]],
    }


def _difficult_words_candidates(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    return _difficult_candidates(user_id, params)


def _family_child_difficult_words_candidates(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    child_id = str(params.get("child_user_id") or "").strip()
    with _conn() as conn:
        _linked_child(conn, user_id, child_id)
    return {"child_user_id": child_id, **_difficult_candidates(child_id, params)}


# ---------------------------------------------------------------------------
# Per-user lesson requirements, validation and completion
# ---------------------------------------------------------------------------

def _requirements_for(user_id: str) -> dict[str, Any]:
    """What a lesson must contain for *this* user, read from their live
    language settings. Nothing is hardcoded and nobody else's languages are
    consulted."""
    languages = [str(item["code"]) for item in _routes()._get_user_languages(user_id)]
    if not languages:
        raise McpServiceError("LANGUAGES_NOT_CONFIGURED", "the user has no learning languages configured", status=409, details={"user_id": user_id})
    with _conn() as conn:
        _routes()._ensure_word_language_columns(conn, languages)
        conn.commit()
    return {
        "user_id": user_id,
        "languages": languages,
        "primary_language": languages[0],
        # Translations for every studied language; examples in every studied
        # language as well (the primary one plus the en/ru translations of the
        # example are the minimum and are always part of this list when the
        # user studies them).
        "required_translation_languages": languages,
        "required_example_languages": languages,
    }


def _value_problem(value: Any, *, max_length: int) -> str | None:
    text = str(value or "").strip()
    if not text:
        return "empty"
    if len(text) > max_length:
        return "too_long"
    if "�" in text:
        return "encoding"
    lowered = text.lower()
    if lowered in CORRUPT_VALUE_MARKERS or lowered.strip("[]{}()\"' ") in CORRUPT_VALUE_MARKERS:
        return "placeholder"
    if (text[0] in "{[" and text[-1] in "}]") or "[object object]" in lowered:
        return "garbage"
    return None


def _require_complete_words(words: list[Any], requirements: dict[str, Any]) -> None:
    missing = []
    for index, word in enumerate(words):
        if not isinstance(word, dict):
            raise McpServiceError("INVALID_WORDS", "each word must be an object")
        for language in requirements["languages"]:
            for field, limit in ((language, 500), (f"ex_{language}", 1000)):
                reason = _value_problem(word.get(field), max_length=limit)
                if reason:
                    missing.append({"index": index, "field": field, "reason": reason})
    if missing:
        raise McpServiceError(
            "LESSON_INCOMPLETE", "nothing was added; supply all translations and example sentences for the required languages and retry",
            status=422, details={"saved": False, "user_id": requirements["user_id"], "required_languages": requirements["languages"], "missing_fields": missing},
        )


def _require_complete_assignment(owner_id: str, title: str, child_id: str) -> None:
    validation = _validate_lesson(owner_id, title, _requirements_for(child_id))
    if validation["status"] != "COMPLETE":
        raise McpServiceError(
            "LESSON_INCOMPLETE", "lesson was not assigned; use lesson_assign_complete with the missing translations and examples",
            status=422, details={"assigned": False, "validation": validation},
        )


def _lesson_rows(conn: sqlite3.Connection, owner_id: str, title: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM words WHERE user_id=? AND lesson=? ORDER BY id", (owner_id, title)).fetchall()


def _validate_lesson(owner_id: str, title: str, requirements: dict[str, Any]) -> dict[str, Any]:
    with _conn() as conn:
        rows = _lesson_rows(conn, owner_id, title)
        columns = {str(row["name"]) for row in conn.execute("PRAGMA table_info(words)")}
    issues: list[str] = []
    if not title.strip():
        issues.append("EMPTY_TITLE")
    if not rows:
        issues.append("NO_WORDS")
    missing_fields: list[dict[str, Any]] = []
    problem_words: list[dict[str, Any]] = []
    missing_languages: set[str] = set()
    complete = 0
    for row in rows:
        data = dict(row)
        word_missing: list[str] = []
        word_corrupt: list[str] = []
        for language in requirements["required_translation_languages"]:
            field = language
            problem = _value_problem(data.get(field) if field in columns else "", max_length=500)
            if problem:
                (word_missing if problem == "empty" else word_corrupt).append(field)
                missing_languages.add(language)
                missing_fields.append({"word_id": int(data["id"]), "number": str(data.get("number") or ""), "field": field, "language": language, "kind": "translation", "reason": problem})
        for language in requirements["required_example_languages"]:
            field = f"ex_{language}"
            problem = _value_problem(data.get(field) if field in columns else "", max_length=1000)
            if problem:
                (word_missing if problem == "empty" else word_corrupt).append(field)
                missing_languages.add(language)
                missing_fields.append({"word_id": int(data["id"]), "number": str(data.get("number") or ""), "field": field, "language": language, "kind": "example", "reason": problem})
        if word_missing or word_corrupt:
            problem_words.append({"word_id": int(data["id"]), "number": str(data.get("number") or ""), "missing": word_missing, "corrupted": word_corrupt})
        else:
            complete += 1
    status = "COMPLETE" if rows and not issues and not problem_words else "INCOMPLETE"
    return {
        "status": status,
        "lesson": title,
        "owner_user_id": owner_id,
        "user_id": requirements["user_id"],
        "required_languages": list(requirements["required_translation_languages"]),
        "required_example_languages": list(requirements["required_example_languages"]),
        "primary_language": requirements["primary_language"],
        "word_count": len(rows),
        "complete_word_count": complete,
        "issues": issues,
        "missing_languages": sorted(missing_languages),
        "missing_fields": missing_fields[:500],
        "missing_fields_truncated": len(missing_fields) > 500,
        "problem_words": problem_words[:MAX_PAGE_SIZE],
    }


def _validate_lesson_for_user(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    title = _lesson_title(params)
    child_id = str(params.get("child_user_id") or "").strip()
    with _conn() as conn:
        if child_id:
            _linked_child(conn, user_id, child_id)
            _owned_lesson(conn, user_id, title)
            owner_id, target = user_id, child_id
        else:
            owner_id = _routes()._child_lesson_owner(conn, user_id, title) or ""
            if not owner_id:
                _owned_lesson(conn, user_id, title)
                owner_id = user_id
            target = user_id
    return _validate_lesson(owner_id, title, _requirements_for(target))


def _apply_word_fills(owner_id: str, title: str, word_fills: Any) -> dict[str, Any]:
    """Apply caller-supplied translations/examples, but only into empty
    fields — existing data is never regenerated or overwritten here."""
    if word_fills is None:
        return {"applied": 0, "skipped_existing": 0, "ignored": []}
    if not isinstance(word_fills, list) or len(word_fills) > MAX_WORDS_PER_WRITE:
        raise McpServiceError("INVALID_WORD_FILLS", f"word_fills must be a list of at most {MAX_WORDS_PER_WRITE} items")
    routes = _routes()
    requested: set[str] = set()
    for item in word_fills:
        if isinstance(item, dict) and isinstance(item.get("fields"), dict):
            for key in item["fields"]:
                code = str(key).lower().removeprefix("ex_")
                if code in routes.LANGUAGE_CODES:
                    requested.add(code)
    applied = skipped = 0
    ignored: list[dict[str, Any]] = []
    with _conn() as conn:
        if requested:
            routes._ensure_word_language_columns(conn, requested)
        columns = {str(row["name"]) for row in conn.execute("PRAGMA table_info(words)")}
        allowed = {column for column in columns if column in routes.LANGUAGE_CODES or (column.startswith("ex_") and column[3:] in routes.LANGUAGE_CODES)}
        for index, item in enumerate(word_fills):
            if not isinstance(item, dict) or not isinstance(item.get("fields"), dict):
                ignored.append({"index": index, "reason": "invalid_item"})
                continue
            try:
                word_id = int(item.get("word_id"))
            except (TypeError, ValueError):
                ignored.append({"index": index, "reason": "invalid_word_id"})
                continue
            row = conn.execute("SELECT * FROM words WHERE id=? AND user_id=? AND lesson=?", (word_id, owner_id, title)).fetchone()
            if not row:
                ignored.append({"index": index, "word_id": word_id, "reason": "not_in_lesson"})
                continue
            current = dict(row)
            updates: dict[str, str] = {}
            for key, value in item["fields"].items():
                field = str(key).lower()
                if field not in allowed:
                    ignored.append({"index": index, "word_id": word_id, "field": field, "reason": "unsupported_field"})
                    continue
                text = str(value or "").strip()[:1000 if field.startswith("ex_") else 500]
                if not text:
                    continue
                if _value_problem(current.get(field), max_length=1000) is None:
                    skipped += 1
                    continue
                updates[field] = text
            if updates:
                conn.execute(
                    "UPDATE words SET " + ",".join(f'"{key}"=?' for key in updates) + ",updated_at=? WHERE id=?",
                    [*updates.values(), int(time.time() * 1000), word_id],
                )
                from app.content_service import ensure_schema, remember
                ensure_schema(conn)
                remember(conn,{**current,**updates},source="mcp")
                applied += len(updates)
        conn.commit()
    return {"applied": applied, "skipped_existing": skipped, "ignored": ignored[:50]}


def _cloud_fill(acting_user_id: str, owner_id: str, title: str, requirements: dict[str, Any]) -> dict[str, Any]:
    """Resolve all still-missing translations/examples through the same service
    used by imports, including primary-language examples and cache-only fills.
    """
    from app import ai_platform
    from app.content_db import transaction
    from app.content_service import ensure_schema, resolve
    routes = _routes()
    report = {"cloud_available": ai_platform.is_configured(), "calls": 0, "filled_fields": 0, "failed": 0, "truncated": False}
    languages = list(dict.fromkeys([*requirements["required_translation_languages"], *requirements["required_example_languages"]]))
    with _conn() as conn:
        rows = [dict(row) for row in _lesson_rows(conn,owner_id,title)]
    for data in rows:
        if report["calls"] >= MAX_CLOUD_FILLS_PER_CALL:
            report["truncated"] = True
            break
        try:
            with transaction(Config.DB_PATH) as conn:
                ensure_schema(conn)
                result = resolve(conn,data,languages,examples=True,allow_provider=True,source="fill")
                updates = {}
                for language in languages:
                    for field in (language,f"ex_{language}"):
                        if _value_problem(data.get(field),max_length=1000) is not None and _value_problem(result.get(field),max_length=1000) is None:
                            updates[field] = str(result[field]).strip()
                if updates:
                    conn.execute("UPDATE words SET " + ",".join(f'"{key}"=?' for key in updates) + ",updated_at=? WHERE id=? AND user_id=?",[*updates.values(),int(time.time()*1000),int(data["id"]),owner_id])
                report["filled_fields"] += len(updates)
                report["calls"] += result["provider_calls"]
                if result["provider_calls"]:
                    report["cloud_available"] = True
                    routes._record_translation_request_usage(acting_user_id,successful=True,usage=ai_platform.TokenUsage.from_payload(result.get("usage")))
        except (ValueError,RuntimeError,ai_platform.AiPlatformError):
            report["failed"] += 1
    return report


def _complete_lesson(acting_user_id: str, owner_id: str, title: str, requirements: dict[str, Any], params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate → fill only what is missing → validate again."""
    before = _validate_lesson(owner_id, title, requirements)
    fill: dict[str, Any] = {"needed": before["status"] != "COMPLETE", "word_fills": {"applied": 0, "skipped_existing": 0, "ignored": []}, "cloud": {"cloud_available": None, "calls": 0, "filled_fields": 0, "failed": 0, "truncated": False}}
    if before["status"] == "COMPLETE":
        return before, fill
    fill["word_fills"] = _apply_word_fills(owner_id, title, params.get("word_fills"))
    after = _validate_lesson(owner_id, title, requirements)
    if after["status"] != "COMPLETE" and params.get("use_cloud", True) is not False:
        fill["cloud"] = _cloud_fill(acting_user_id, owner_id, title, requirements)
        after = _validate_lesson(owner_id, title, requirements)
    fill["missing_before"] = len(before["missing_fields"])
    fill["missing_after"] = len(after["missing_fields"])
    return after, fill


def _lesson_create_complete(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Create a lesson for the authenticated user only: their languages, all
    translations and examples, validation. Nobody else is consulted or
    assigned; INCOMPLETE lessons are always rolled back."""
    title = _lesson_title(params, "title")
    words = params.get("words")
    if not isinstance(words, list) or not 1 <= len(words) <= MAX_WORDS_PER_WRITE:
        raise McpServiceError("INVALID_WORDS", f"words must contain 1 to {MAX_WORDS_PER_WRITE} items")
    def create() -> dict[str, Any]:
        requirements = _requirements_for(user_id)
        models.ensure_user_tables(Config.DB_PATH)
        with _conn() as conn:
            if conn.execute(
                "SELECT 1 FROM words WHERE user_id=? AND lesson=? UNION SELECT 1 FROM user_lessons WHERE user_id=? AND lesson=?",
                (user_id, title, user_id, title),
            ).fetchone():
                raise McpServiceError("LESSON_EXISTS", "lesson already exists", status=409)
            conn.execute(
                "INSERT INTO user_lessons(user_id,lesson,hidden,updated_at,updated_at_ts) VALUES(?,?,0,CURRENT_TIMESTAMP,?) "
                "ON CONFLICT(user_id,lesson) DO NOTHING",
                (user_id, title, int(time.time() * 1000)),
            )
            conn.commit()
        try:
            created = _insert_words(user_id, title, words)
            validation, fill = _complete_lesson(user_id, user_id, title, requirements, params)
        except Exception:
            _discard_lesson(user_id, title)
            raise
        if validation["status"] != "COMPLETE":
            _discard_lesson(user_id, title)
            raise McpServiceError(
                "LESSON_INCOMPLETE",
                "lesson is incomplete for this user and was not saved; supply the missing fields and retry",
                status=422,
                details={"saved": False, "validation": validation, "fill": fill},
            )
        return {"lesson": title, "status": validation["status"], "saved": True, "created_words": created, "user_id": user_id, "validation": validation, "fill": fill}
    return _idempotent(user_id, "lesson_create_complete", params, create)


def _discard_lesson(user_id: str, title: str) -> None:
    with _conn() as conn:
        ids = [int(row[0]) for row in conn.execute("SELECT id FROM words WHERE user_id=? AND lesson=?", (user_id, title))]
        conn.execute("DELETE FROM words WHERE user_id=? AND lesson=?", (user_id, title))
        conn.execute("DELETE FROM user_lessons WHERE user_id=? AND lesson=?", (user_id, title))
        if ids:
            qmarks = ",".join("?" for _ in ids)
            conn.execute(f"DELETE FROM user_word_flags WHERE word_id IN ({qmarks})", ids)
        conn.commit()


def _lesson_assign_complete(user_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Assign an existing canonical lesson to one linked child: read only that
    child's languages, add only the data the lesson still lacks for them,
    validate for the child, then assign (priority + last-5 rule)."""
    child_id = str(params.get("child_user_id") or "").strip()
    title = _lesson_title(params)
    set_priority = params.get("set_priority") is True
    def assign() -> dict[str, Any]:
        with _conn() as conn:
            _linked_child(conn, user_id, child_id)
            _owned_lesson(conn, user_id, title)
        requirements = _requirements_for(child_id)
        validation, fill = _complete_lesson(user_id, user_id, title, requirements, params)
        if validation["status"] != "COMPLETE":
            raise McpServiceError(
                "LESSON_INCOMPLETE",
                "lesson is incomplete for this child and was not assigned; supply the missing fields and retry",
                status=422,
                details={"assigned": False, "child_user_id": child_id, "validation": validation, "fill": fill},
            )
        with _conn() as conn:
            _activate_assignment(conn, user_id, child_id, title)
            if _routes()._child_lesson_owner(conn, child_id, title) != user_id:
                raise McpServiceError("ASSIGNMENT_NOT_VISIBLE", "assigned lesson is not visible to the child", status=409)
            if set_priority:
                _pin_priority(conn, user_id, child_id, title)
            archived = _enforce_active_limit(conn, user_id, child_id)
            active = [str(row[0]) for row in conn.execute(
                "SELECT lesson FROM family_lesson_assignments WHERE parent_user_id=? AND child_user_id=? AND archived_at IS NULL ORDER BY COALESCE(activated_at,created_at) DESC,lesson",
                (user_id, child_id),
            )]
            conn.commit()
        return {
            "child_user_id": child_id, "lesson": title, "assigned": True, "status": validation["status"],
            "priority_set": set_priority, "archived": archived, "active_lessons": active, "active_limit": MAX_ACTIVE_CHILD_LESSONS,
            "validation": validation, "fill": fill,
        }
    return _idempotent(user_id, "lesson_assign_complete", params, assign)


# Operations that act on the caller's own data by default but may target a
# linked child through child_user_id; the family scope is then required too.
CHILD_OPTIONAL_OPERATIONS = {"validate_lesson_for_user": FAMILY_READ_SCOPE}


OPERATIONS: dict[str, Operation] = {
    "me_get": Operation(READ_SCOPE, _me_get),
    "my_languages_get": Operation(READ_SCOPE, _languages_get),
    "my_languages_update": Operation(WRITE_SCOPE, _languages_update),
    "my_learning_settings_get": Operation(READ_SCOPE, _settings_get),
    "my_learning_settings_update": Operation(WRITE_SCOPE, _settings_update),
    "subscription_get": Operation(READ_SCOPE, _subscription_get),
    "ai_status": Operation(READ_SCOPE, _ai_status),
    "translate_word": Operation(WRITE_SCOPE, _translate_word),
    "generate_topic_words": Operation(WRITE_SCOPE, _generate_topic_words),
    "translate_language": Operation(WRITE_SCOPE, _translate_language),
    "audio_ensure": Operation(WRITE_SCOPE, _audio_ensure),
    "lessons_list": Operation(READ_SCOPE, _lessons_list),
    "lesson_get": Operation(READ_SCOPE, _lesson_get),
    "lesson_words_list": Operation(READ_SCOPE, _lesson_words),
    "difficult_words_list": Operation(READ_SCOPE, _difficult_words),
    "words_search": Operation(READ_SCOPE, _words_search),
    "word_get": Operation(READ_SCOPE, _word_get),
    "next_lesson_get": Operation(READ_SCOPE, lambda uid, p: _navigation(uid, p, previous=False)),
    "previous_lesson_get": Operation(READ_SCOPE, lambda uid, p: _navigation(uid, p, previous=True)),
    "lesson_create": Operation(WRITE_SCOPE, _lesson_create),
    "lesson_rename": Operation(WRITE_SCOPE, _lesson_rename),
    "lesson_set_hidden": Operation(WRITE_SCOPE, _lesson_hidden),
    "lesson_delete": Operation(WRITE_SCOPE, _lesson_delete),
    "words_add": Operation(WRITE_SCOPE, _words_add),
    "lesson_import_file": Operation(FILES_SCOPE, _words_add),
    "word_update": Operation(WRITE_SCOPE, _word_update),
    "word_delete": Operation(WRITE_SCOPE, _word_delete),
    "words_mark_difficult": Operation(WRITE_SCOPE, _words_mark_difficult),
    "difficult_words_add": Operation(WRITE_SCOPE, lambda uid, p: _set_difficult(uid, p, True)),
    "difficult_words_remove": Operation(WRITE_SCOPE, lambda uid, p: _set_difficult(uid, p, False)),
    "difficult_words_candidates_get": Operation(READ_SCOPE, _difficult_words_candidates),
    "validate_lesson_for_user": Operation(READ_SCOPE, _validate_lesson_for_user),
    "lesson_create_complete": Operation(WRITE_SCOPE, _lesson_create_complete),
    "progress_summary": Operation(READ_SCOPE, _progress_summary),
    "progress_words_get": Operation(READ_SCOPE, _progress_words),
    "learning_recommendation_get": Operation(READ_SCOPE, _learning_recommendation),
    "progress_record_many": Operation(WRITE_SCOPE, _progress_record_many),
    "family_status_get": Operation(FAMILY_READ_SCOPE, _family_status),
    "family_children_list": Operation(FAMILY_READ_SCOPE, _family_children),
    "family_child_languages_get": Operation(FAMILY_READ_SCOPE, _family_child_languages_get),
    "family_child_languages_update": Operation(FAMILY_WRITE_SCOPE, _family_child_languages_update),
    "family_child_progress_get": Operation(FAMILY_READ_SCOPE, _family_child_progress),
    "family_child_progress_record": Operation(FAMILY_WRITE_SCOPE, _family_child_progress_record),
    "family_child_progress_record_many": Operation(FAMILY_WRITE_SCOPE, _family_child_progress_record_many),
    "family_child_lessons_list": Operation(FAMILY_READ_SCOPE, _family_child_lessons),
    "family_child_lesson_words_list": Operation(FAMILY_READ_SCOPE, _family_child_lesson_words),
    "family_child_lesson_assign": Operation(FAMILY_WRITE_SCOPE, _family_child_lesson_assign),
    "family_children_lesson_assign": Operation(FAMILY_WRITE_SCOPE, _family_children_lesson_assign),
    "family_child_lesson_unassign": Operation(FAMILY_WRITE_SCOPE, _family_child_lesson_unassign),
    "family_child_priority_lesson_set": Operation(FAMILY_WRITE_SCOPE, _family_priority_set),
    "family_child_priority_lesson_clear": Operation(FAMILY_WRITE_SCOPE, _family_child_priority_clear),
    "family_child_active_lessons_list": Operation(FAMILY_READ_SCOPE, lambda uid, p: _family_child_lessons(uid, {**p, "status": "active"})),
    "family_child_archived_lessons_list": Operation(FAMILY_READ_SCOPE, lambda uid, p: _family_child_lessons(uid, {**p, "status": "archived"})),
    "family_child_lesson_archive": Operation(FAMILY_WRITE_SCOPE, _family_child_lesson_archive),
    "family_child_lesson_restore": Operation(FAMILY_WRITE_SCOPE, _family_child_lesson_restore),
    "family_child_lessons_cleanup": Operation(FAMILY_WRITE_SCOPE, _family_child_lessons_cleanup),
    "family_child_difficult_words_list": Operation(FAMILY_READ_SCOPE, _family_child_difficult_words_list),
    "family_child_difficult_words_add": Operation(FAMILY_WRITE_SCOPE, lambda uid, p: _family_child_difficult_set(uid, p, True)),
    "family_child_difficult_words_remove": Operation(FAMILY_WRITE_SCOPE, lambda uid, p: _family_child_difficult_set(uid, p, False)),
    "family_child_difficult_words_candidates_get": Operation(FAMILY_READ_SCOPE, _family_child_difficult_words_candidates),
    "lesson_assign_complete": Operation(FAMILY_WRITE_SCOPE, _lesson_assign_complete),
    "subscriptions_list": Operation(SUBSCRIPTIONS_ADMIN_SCOPE, _subscriptions_list, admin_only=True),
    "subscription_grant_access": Operation(SUBSCRIPTIONS_ADMIN_SCOPE, lambda uid, p: _subscription_access(uid, p, grant=True), admin_only=True),
    "subscription_revoke_access": Operation(SUBSCRIPTIONS_ADMIN_SCOPE, lambda uid, p: _subscription_access(uid, p, grant=False), admin_only=True),
    "users_list": Operation(USERS_ADMIN_SCOPE, _admin_users_list, admin_only=True),
    "users_search": Operation(USERS_ADMIN_SCOPE, _admin_users_search, admin_only=True),
    "admin_user_get": Operation(USERS_ADMIN_SCOPE, _admin_user_get, admin_only=True),
    "admin_user_progress_get": Operation(ANALYTICS_ADMIN_SCOPE, _admin_user_progress, admin_only=True),
    "admin_user_lessons_list": Operation(USERS_ADMIN_SCOPE, _admin_user_lessons, admin_only=True),
    "admin_user_words_search": Operation(USERS_ADMIN_SCOPE, _admin_user_words_search, admin_only=True),
    "admin_analytics_summary": Operation(ANALYTICS_ADMIN_SCOPE, _admin_analytics_summary, admin_only=True),
    "admin_analytics_users": Operation(ANALYTICS_ADMIN_SCOPE, _admin_analytics_users, admin_only=True),
    "admin_audit_log_list": Operation(SUBSCRIPTIONS_ADMIN_SCOPE, _admin_audit_log_list, admin_only=True),
}


def execute(operation_name: str, user_id: str, scopes: list[str], params: dict[str, Any]) -> Any:
    operation = OPERATIONS.get(operation_name)
    if not operation:
        raise McpServiceError("OPERATION_NOT_ALLOWED", "operation is not allowed", status=404)
    if operation.scope not in scopes:
        raise McpServiceError("INSUFFICIENT_SCOPE", f"scope {operation.scope} is required", status=403)
    if operation_name == "lesson_import_file" and WRITE_SCOPE not in scopes:
        raise McpServiceError("INSUFFICIENT_SCOPE", f"scope {WRITE_SCOPE} is also required", status=403)
    if operation.admin_only and not _is_admin(user_id):
        raise McpServiceError("ADMIN_REQUIRED", "superuser access is required", status=403)
    # Family scope exists so a parent's connector can read/manage a linked
    # child's learning data — never the other way round. Re-checked live
    # (not just at consent time) so a child account can't use family.read to
    # learn who their parent is, even from a token granted before this
    # account became a child, or before this check existed.
    if operation.scope in (FAMILY_READ_SCOPE, FAMILY_WRITE_SCOPE) and _is_child_account(user_id):
        raise McpServiceError("FAMILY_SCOPE_NOT_AVAILABLE", "family scope is only available to a parent account", status=403)
    child_scope = CHILD_OPTIONAL_OPERATIONS.get(operation_name)
    if child_scope and str(params.get("child_user_id") or "").strip():
        if child_scope not in scopes:
            raise McpServiceError("INSUFFICIENT_SCOPE", f"scope {child_scope} is required for child_user_id", status=403)
        if _is_child_account(user_id):
            raise McpServiceError("FAMILY_SCOPE_NOT_AVAILABLE", "family scope is only available to a parent account", status=403)
    return operation.handler(user_id, params)
