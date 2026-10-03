from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import AnyHttpUrl, BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from mcp.server import MCPServer
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from mcp_gateway import config
from mcp_gateway.client import InternalApiError, execute, health, resolve_token
from mcp_gateway.file_import import download_file, parse_words
from mcp_gateway.state import enforce_rate_limit, redis_health


READ = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False)
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True, open_world_hint=False)


class BackendTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        grant = await resolve_token(token)
        if not grant:
            return None
        return AccessToken(
            token=token,
            client_id=str(grant["client_id"]),
            scopes=list(grant.get("scopes") or []),
            expires_at=int(grant["expires_at"]),
            resource=str(grant.get("resource") or ""),
            subject=str(grant["user_id"]),
            claims={"user_id": str(grant["user_id"])},
        )


mcp = MCPServer(
    "ParallelLingvo",
    version=config.VERSION,
    instructions=(
        "Operate only on the authenticated user's ParallelLingvo data. Read before changing. "
        "Use idempotency keys for creates and progress writes. Deletions and subscription changes require confirm=true.\n"
        "\n"
        "MANDATORY LESSON RULES:\n"
        "Complete-lesson rules apply only to tools promising COMPLETE. words_add and lesson_import_file accept partial content and reuse the server catalog; do not make preliminary deduplication calls. A meaningful "
        "lesson title is mandatory; never infer it from a filename. Supply existing translations and examples as-is. "
        "The server finds reusable content and reports missing fields. Never make extra calls to search for duplicates, translations, examples or audio. "
        "For COMPLETE tools only, handle LESSON_INCOMPLETE by supplying its missing_fields and retry with a new key.\n"
        "1. Creating a lesson: identify the ONE user the current request is about (the authenticated user unless a "
        "linked child is explicitly named). Read ONLY that user's languages (my_languages_get). Fill every word with "
        "translations for all of that user's languages plus an example sentence in each of those languages "
        "(examples must keep one meaning across languages). Use lesson_create_complete, which validates "
        "(validate_lesson_for_user) and rolls back if INCOMPLETE. The lesson counts as created only after status "
        "is COMPLETE. Do NOT assign it to children or anyone else unless the request says so.\n"
        "2. Assigning an existing lesson to another user (a linked child): use lesson_assign_complete. It reads ONLY "
        "that child's languages, keeps existing translations/examples untouched, adds ONLY the missing ones "
        "(from word_fills you supply and/or the cloud provider), validates for that child and only then assigns, "
        "applying priority and the last-5-active-lessons rule. If it returns LESSON_INCOMPLETE, supply the listed "
        "missing_fields via word_fills and retry with a new idempotency_key.\n"
        "3. Never fetch or process languages of family members the current task does not concern. Do not pre-fill "
        "languages for users the lesson is not being created for or assigned to right now.\n"
        "4. Never tell the user a lesson is ready or assigned until the corresponding validation returned COMPLETE "
        "and the tool reported saved/assigned=true.\n"
        "5. Children keep at most 5 active assigned lessons; older ones are archived automatically (words, progress "
        "and difficult words are kept). The priority lesson is never archived automatically.\n"
        "6. Difficult words are personal per user; use difficult_words_* for the authenticated user and "
        "family_child_difficult_words_* for one linked child."
    ),
    token_verifier=BackendTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(config.ISSUER_URL),
        resource_server_url=AnyHttpUrl(config.PUBLIC_MCP_URL),
        required_scopes=["learning.read", "learning.write", "family.read", "family.write"],
        # Belt-and-suspenders: the internal API already refuses tokens minted
        # for a different resource, but have the SDK enforce RFC 8707
        # audience binding here too rather than silently trusting any token
        # this verifier accepts.
        validate_token_resource=True,
    ),
)


def _raw_token() -> str:
    token = get_access_token()
    if token is None:
        raise PermissionError("authentication required")
    return token.token


def _permissions() -> dict[str, Any]:
    token = get_access_token()
    return {"scopes": list(token.scopes if token else []), "client_id": token.client_id if token else None}


async def _call(operation: str, params: dict[str, Any] | None = None, *, long_running: bool = False) -> dict[str, Any]:
    raw_token = _raw_token()
    try:
        await enforce_rate_limit(raw_token)
        return await execute(raw_token, operation, params, timeout=config.LONG_REQUEST_TIMEOUT_SECONDS if long_running else None)
    except InternalApiError as exc:
        return exc.payload


class WordInput(BaseModel):
    """One word: translations per language code and example sentences as ex_<code>."""

    sense: str = Field(default="", max_length=200)
    context: str = Field(default="", max_length=1000)
    level: str = Field(default="", max_length=10)
    nl: str = Field(default="", max_length=500)
    en: str = Field(default="", max_length=500)
    ru: str = Field(default="", max_length=500)
    de: str = Field(default="", max_length=500)
    fr: str = Field(default="", max_length=500)
    es: str = Field(default="", max_length=500)
    it: str = Field(default="", max_length=500)
    pt: str = Field(default="", max_length=500)
    pl: str = Field(default="", max_length=500)
    uk: str = Field(default="", max_length=500)
    ex_nl: str = Field(default="", max_length=1000)
    ex_en: str = Field(default="", max_length=1000)
    ex_ru: str = Field(default="", max_length=1000)
    ex_de: str = Field(default="", max_length=1000)
    ex_fr: str = Field(default="", max_length=1000)
    ex_es: str = Field(default="", max_length=1000)
    ex_it: str = Field(default="", max_length=1000)
    ex_pt: str = Field(default="", max_length=1000)
    ex_pl: str = Field(default="", max_length=1000)
    ex_uk: str = Field(default="", max_length=1000)


class WordFill(BaseModel):
    """Missing translations/examples for one existing word; only empty fields are filled."""

    word_id: int
    fields: dict[str, str] = Field(description="Language code (e.g. 'it') or example key (e.g. 'ex_it') to value.")


class WordUpdateFields(BaseModel):
    """Editable word and example fields; an empty string explicitly clears a value."""

    sense: str | None = Field(default=None,max_length=200)
    context: str | None = Field(default=None,max_length=1000)
    level: str | None = Field(default=None,max_length=10)
    lesson: str | None = Field(default=None, max_length=200)
    number: str | None = Field(default=None, max_length=100)
    nl: str | None = Field(default=None, max_length=500)
    en: str | None = Field(default=None, max_length=500)
    ru: str | None = Field(default=None, max_length=500)
    de: str | None = Field(default=None, max_length=500)
    fr: str | None = Field(default=None, max_length=500)
    es: str | None = Field(default=None, max_length=500)
    it: str | None = Field(default=None, max_length=500)
    pt: str | None = Field(default=None, max_length=500)
    pl: str | None = Field(default=None, max_length=500)
    uk: str | None = Field(default=None, max_length=500)
    ex_nl: str | None = Field(default=None, max_length=1000)
    ex_en: str | None = Field(default=None, max_length=1000)
    ex_ru: str | None = Field(default=None, max_length=1000)
    ex_de: str | None = Field(default=None, max_length=1000)
    ex_fr: str | None = Field(default=None, max_length=1000)
    ex_es: str | None = Field(default=None, max_length=1000)
    ex_it: str | None = Field(default=None, max_length=1000)
    ex_pt: str | None = Field(default=None, max_length=1000)
    ex_pl: str | None = Field(default=None, max_length=1000)
    ex_uk: str | None = Field(default=None, max_length=1000)


class ProgressInput(BaseModel):
    word_id: int
    result: Literal["correct", "wrong", "learned"]
    occurred_at: int | None = None


class FamilyProgressInput(BaseModel):
    word_id: int
    result: Literal["correct", "wrong", "learned"]
    occurred_at: int | None = None


class OpenAIFile(BaseModel):
    download_url: str
    file_id: str
    mime_type: str | None = None
    file_name: str | None = None


@mcp.tool(title="Connector information", annotations=READ)
async def system_info() -> dict[str, Any]:
    """Return connector name, version and public MCP URL."""
    return {"name": "ParallelLingvo", "version": config.VERSION, "mcp_url": config.PUBLIC_MCP_URL, "transport": "streamable-http"}


@mcp.tool(title="Connector health", annotations=READ)
async def system_health() -> dict[str, Any]:
    """Check the gateway and its closed internal API without returning user data."""
    return {"gateway": "ok", "redis": await redis_health(), **await health()}


@mcp.tool(title="Connector capabilities", annotations=READ)
async def system_capabilities() -> dict[str, Any]:
    """List supported languages, limits and permission groups."""
    return {"languages": ["en", "nl", "ru", "de", "fr", "es", "it", "pt", "pl", "uk"], "max_page_size": 100, "max_words_per_write": 100, "file_types": ["text/csv", "application/json"]}


@mcp.tool(title="Current permissions", annotations=READ)
async def permissions_get() -> dict[str, Any]:
    """Return scopes granted to this connector connection."""
    return _permissions()


@mcp.tool(title="My profile", annotations=READ)
async def me_get() -> dict[str, Any]:
    """Get the authenticated ParallelLingvo profile and entitlement summary."""
    return await _call("me_get")


@mcp.tool(title="My languages", annotations=READ)
async def my_languages_get() -> dict[str, Any]:
    """Get selected and available learning languages."""
    return await _call("my_languages_get")


@mcp.tool(title="Update my languages", annotations=WRITE)
async def my_languages_update(languages: Annotated[list[str], Field(min_length=3, max_length=5)]) -> dict[str, Any]:
    """Set 3 to 5 supported learning languages in priority order."""
    return await _call("my_languages_update", {"languages": languages})


@mcp.tool(title="My learning settings", annotations=READ)
async def my_learning_settings_get() -> dict[str, Any]:
    """Get daily goal and interface language settings."""
    return await _call("my_learning_settings_get")


@mcp.tool(title="Update my learning settings", annotations=WRITE)
async def my_learning_settings_update(daily_goal: int | None = None, ui_language: str | None = None) -> dict[str, Any]:
    """Update allowlisted learning settings for the authenticated user."""
    params: dict[str, Any] = {}
    if daily_goal is not None:
        params["daily_goal"] = daily_goal
    if ui_language is not None:
        params["ui_language"] = ui_language
    return await _call("my_learning_settings_update", params)


@mcp.tool(title="My subscription", annotations=READ)
async def subscription_get() -> dict[str, Any]:
    """Get the authenticated user's current application entitlement."""
    return await _call("subscription_get")


@mcp.tool(title="AI feature status", annotations=READ)
async def ai_status() -> dict[str, Any]:
    """Check whether the application's cloud word helper is available."""
    return await _call("ai_status")


@mcp.tool(title="Translate a word", annotations=WRITE)
async def translate_word(word: str, from_lang: str = "nl", level: str = "A2", known_ru: str | None = None) -> dict[str, Any]:
    """Use the application's configured translation provider and account usage counters."""
    return await _call("translate_word", {"word": word, "from_lang": from_lang, "level": level, "known_ru": known_ru})


@mcp.tool(title="Suggest topic words", annotations=WRITE)
async def generate_topic_words(topic: str, language: str = "nl", level: str = "A2", count: Annotated[int, Field(ge=1, le=50)] = 10, existing_words: list[str] | None = None) -> dict[str, Any]:
    """Suggest a bounded list using the application's configured provider without saving it."""
    return await _call("generate_topic_words", {"topic": topic, "language": language, "level": level, "count": count, "existing_words": existing_words or []})


@mcp.tool(title="Translate into another lesson language", annotations=WRITE)
async def translate_language(source_word: str, target_language: str, source_sentence: str = "", source_language: str = "") -> dict[str, Any]:
    """Translate a word and optional example with the application's configured provider."""
    return await _call("translate_language", {"source_word": source_word, "source_sentence": source_sentence, "source_language": source_language, "target_language": target_language})


@mcp.tool(title="Generate missing word audio", annotations=WRITE)
async def audio_ensure(word_ids: Annotated[list[int], Field(min_length=1, max_length=25)], languages: list[str] | None = None) -> dict[str, Any]:
    """Generate missing audio for visible words using existing TTS limits and storage."""
    return await _call("audio_ensure", {"word_ids": word_ids, "languages": languages or ["nl", "en", "ru"]})


@mcp.tool(title="List lessons", annotations=READ)
async def lessons_list(include_hidden: bool = False) -> dict[str, Any]:
    """List the authenticated user's lessons and word counts."""
    return await _call("lessons_list", {"include_hidden": include_hidden})


@mcp.tool(title="Get lesson", annotations=READ)
async def lesson_get(lesson_title: str) -> dict[str, Any]:
    """Get one lesson owned by or available to the authenticated user."""
    return await _call("lesson_get", {"lesson_title": lesson_title})


@mcp.tool(title="List lesson words", annotations=READ)
async def lesson_words_list(lesson_title: str, limit: Annotated[int, Field(ge=1, le=100)] = 50, cursor: int = 0) -> dict[str, Any]:
    """List a bounded page of words from one lesson."""
    return await _call("lesson_words_list", {"lesson_title": lesson_title, "limit": limit, "cursor": cursor})


@mcp.tool(title="List difficult words", annotations=READ)
async def difficult_words_list(lesson_title: str | None = None, limit: Annotated[int, Field(ge=1, le=100)] = 50, cursor: int = 0) -> dict[str, Any]:
    """List difficult words for the authenticated user."""
    return await _call("difficult_words_list", {"lesson_title": lesson_title, "limit": limit, "cursor": cursor})


@mcp.tool(title="Search my words", annotations=READ)
async def words_search(query: str, lesson_title: str | None = None, limit: Annotated[int, Field(ge=1, le=100)] = 25) -> dict[str, Any]:
    """Search only words visible to the authenticated user."""
    return await _call("words_search", {"query": query, "lesson_title": lesson_title, "limit": limit})


@mcp.tool(title="Get word", annotations=READ)
async def word_get(word_id: int) -> dict[str, Any]:
    """Get one word after server-side ownership validation."""
    return await _call("word_get", {"word_id": word_id})


@mcp.tool(title="Get next lesson", annotations=READ)
async def next_lesson_get(current_lesson: str = "") -> dict[str, Any]:
    """Get the next visible lesson."""
    return await _call("next_lesson_get", {"current_lesson": current_lesson})


@mcp.tool(title="Get previous lesson", annotations=READ)
async def previous_lesson_get(current_lesson: str = "") -> dict[str, Any]:
    """Get the previous visible lesson."""
    return await _call("previous_lesson_get", {"current_lesson": current_lesson})


@mcp.tool(title="Create lesson", annotations=WRITE)
async def lesson_create(title: Annotated[str, Field(min_length=1, max_length=200)], idempotency_key: Annotated[str, Field(min_length=8, max_length=128)]) -> dict[str, Any]:
    """Create an empty personal lesson safely for later word additions."""
    return await _call("lesson_create", {"title": title, "idempotency_key": idempotency_key})


@mcp.tool(title="Rename lesson", annotations=WRITE)
async def lesson_rename(lesson_title: str, new_title: str) -> dict[str, Any]:
    """Rename an owned lesson."""
    return await _call("lesson_rename", {"lesson_title": lesson_title, "new_title": new_title})


@mcp.tool(title="Hide or show lesson", annotations=WRITE)
async def lesson_set_hidden(lesson_title: str, hidden: bool) -> dict[str, Any]:
    """Change visibility of one lesson for the authenticated user."""
    return await _call("lesson_set_hidden", {"lesson_title": lesson_title, "hidden": hidden})


@mcp.tool(title="Delete lesson", annotations=DESTRUCTIVE)
async def lesson_delete(lesson_title: str, confirm: bool = False) -> dict[str, Any]:
    """Delete an owned lesson and its words. Requires confirm=true."""
    return await _call("lesson_delete", {"lesson_title": lesson_title, "confirm": confirm})


@mcp.tool(title="Add words", annotations=WRITE)
async def words_add(lesson_title: str, words: Annotated[list[WordInput], Field(min_length=1, max_length=100)], idempotency_key: Annotated[str, Field(min_length=8, max_length=128)]) -> dict[str, Any]:
    """Append supplied words/translations/examples. The server reuses shared content and records missing fields; no preliminary lookup is needed. Same idempotency_key for retries, new key for deliberate repeats."""
    return await _call("words_add", {"lesson_title": lesson_title, "words": [word.model_dump() for word in words], "idempotency_key": idempotency_key})


@mcp.tool(title="Update word", annotations=WRITE)
async def word_update(word_id: int, fields: WordUpdateFields) -> dict[str, Any]:
    """Update an owned word or its example sentences; returns the current word."""
    return await _call("word_update", {"word_id": word_id, "fields": fields.model_dump(exclude_none=True)})


@mcp.tool(title="Delete word", annotations=DESTRUCTIVE)
async def word_delete(word_id: int, confirm: bool = False) -> dict[str, Any]:
    """Delete one owned word. Requires confirm=true."""
    return await _call("word_delete", {"word_id": word_id, "confirm": confirm})


@mcp.tool(title="Mark words difficult", annotations=WRITE)
async def words_mark_difficult(word_ids: Annotated[list[int], Field(min_length=1, max_length=100)], difficult: bool) -> dict[str, Any]:
    """Set or clear the difficult flag for visible words (low-level; prefer difficult_words_add/remove)."""
    return await _call("words_mark_difficult", {"word_ids": word_ids, "difficult": difficult})


@mcp.tool(title="Add my difficult words", annotations=WRITE)
async def difficult_words_add(word_ids: Annotated[list[int], Field(min_length=1, max_length=100)], source: Literal["manual", "auto_errors"] = "manual") -> dict[str, Any]:
    """Mark one or more visible words as difficult for the authenticated user only. Words stay in their lesson."""
    return await _call("difficult_words_add", {"word_ids": word_ids, "source": source})


@mcp.tool(title="Remove my difficult words", annotations=WRITE)
async def difficult_words_remove(word_ids: Annotated[list[int], Field(min_length=1, max_length=100)]) -> dict[str, Any]:
    """Clear the difficult flag on one or more words for the authenticated user only."""
    return await _call("difficult_words_remove", {"word_ids": word_ids})


@mcp.tool(title="My difficult-word candidates", annotations=READ)
async def difficult_words_candidates_get(days: Annotated[int, Field(ge=1, le=365)] = 30, min_wrong: Annotated[int, Field(ge=1, le=100)] = 2, lesson_title: str | None = None, limit: Annotated[int, Field(ge=1, le=100)] = 50) -> dict[str, Any]:
    """Words the authenticated user answered wrong at least min_wrong times; read-only input for difficult_words_add(source='auto_errors')."""
    return await _call("difficult_words_candidates_get", {"days": days, "min_wrong": min_wrong, "lesson_title": lesson_title, "limit": limit})


@mcp.tool(title="Validate lesson for a user", annotations=READ)
async def validate_lesson_for_user(lesson_title: str, child_user_id: str | None = None) -> dict[str, Any]:
    """Check lesson completeness against ONE user's live languages (the authenticated user, or one linked child). Returns COMPLETE/INCOMPLETE with missing fields."""
    return await _call("validate_lesson_for_user", {"lesson_title": lesson_title, "child_user_id": child_user_id})


@mcp.tool(title="Create complete lesson for me", annotations=WRITE)
async def lesson_create_complete(
    title: Annotated[str, Field(min_length=1, max_length=200)],
    words: Annotated[list[WordInput], Field(min_length=1, max_length=100)],
    idempotency_key: Annotated[str, Field(min_length=8, max_length=128)],
    use_cloud: bool = True,
) -> dict[str, Any]:
    """Create a lesson with a meaningful title and all translations/examples for the authenticated user's languages. Incomplete lessons are always rolled back; fill missing_fields and retry. Assigns nobody."""
    return await _call(
        "lesson_create_complete",
        {"title": title, "words": [word.model_dump() for word in words], "idempotency_key": idempotency_key, "use_cloud": use_cloud},
        long_running=True,
    )


@mcp.tool(title="Learning progress summary", annotations=READ)
async def progress_summary(days: Annotated[int, Field(ge=1, le=90)] = 7, lesson_title: str | None = None) -> dict[str, Any]:
    """Summarize learning attempts for a bounded period."""
    return await _call("progress_summary", {"days": days, "lesson_title": lesson_title})


@mcp.tool(title="Lesson word progress", annotations=READ)
async def progress_words_get(
    lesson_title: str,
    limit: Annotated[int, Field(ge=1, le=100)] = 50,
    cursor: int = 0,
) -> dict[str, Any]:
    """Get bounded per-word progress for one accessible lesson."""
    return await _call("progress_words_get", {"lesson_title": lesson_title, "limit": limit, "cursor": cursor})


@mcp.tool(title="Learning recommendation", annotations=READ)
async def learning_recommendation_get() -> dict[str, Any]:
    """Get a deterministic next learning action from current lessons and difficult words."""
    return await _call("learning_recommendation_get")


@mcp.tool(title="Record one progress result", annotations=WRITE)
async def progress_record(word_id: int, result: Literal["correct", "wrong", "learned"], idempotency_key: str, occurred_at: int | None = None) -> dict[str, Any]:
    """Record one result through the existing progress event contract."""
    return await _call("progress_record_many", {"items": [{"word_id": word_id, "result": result, "occurred_at": occurred_at}], "idempotency_key": idempotency_key})


@mcp.tool(title="Record many progress results", annotations=WRITE)
async def progress_record_many(items: Annotated[list[ProgressInput], Field(min_length=1, max_length=100)], idempotency_key: str) -> dict[str, Any]:
    """Record a bounded retry-safe batch through the existing progress event contract."""
    return await _call("progress_record_many", {"items": [item.model_dump() for item in items], "idempotency_key": idempotency_key})


@mcp.tool(title="Family status", annotations=READ)
async def family_status_get() -> dict[str, Any]:
    """Get family links visible to the authenticated account."""
    return await _call("family_status_get")


@mcp.tool(title="List my children", annotations=READ)
async def family_children_list() -> dict[str, Any]:
    """List only children linked to the authenticated parent."""
    return await _call("family_children_list")


@mcp.tool(title="Get child languages", annotations=READ)
async def family_child_languages_get(child_user_id: str) -> dict[str, Any]:
    """Get learning languages configured for one linked child."""
    return await _call("family_child_languages_get", {"child_user_id": child_user_id})


@mcp.tool(title="Update child languages", annotations=WRITE)
async def family_child_languages_update(child_user_id: str, languages: Annotated[list[str], Field(min_length=3, max_length=5)]) -> dict[str, Any]:
    """Update languages only for one linked child."""
    return await _call("family_child_languages_update", {"child_user_id": child_user_id, "languages": languages})


@mcp.tool(title="Child progress", annotations=READ)
async def family_child_progress_get(child_user_id: str, days: Literal[7, 30, 90] = 7) -> dict[str, Any]:
    """Get progress only for a child linked to the authenticated parent."""
    return await _call("family_child_progress_get", {"child_user_id": child_user_id, "days": days})


@mcp.tool(title="Record child progress", annotations=WRITE)
async def family_child_progress_record(child_user_id: str, word_id: int, result: Literal["correct", "wrong", "learned"], idempotency_key: str, occurred_at: int | None = None) -> dict[str, Any]:
    """Record one learning progress event for a child linked to the authenticated parent."""
    return await _call("family_child_progress_record", {"child_user_id": child_user_id, "word_id": word_id, "result": result, "occurred_at": occurred_at, "idempotency_key": idempotency_key})


@mcp.tool(title="Record child progress batch", annotations=WRITE)
async def family_child_progress_record_many(child_user_id: str, items: Annotated[list[FamilyProgressInput], Field(min_length=1, max_length=100)], idempotency_key: str) -> dict[str, Any]:
    """Record a retry-safe bounded batch of learning progress events for a child linked to the authenticated parent."""
    return await _call("family_child_progress_record_many", {"child_user_id": child_user_id, "items": [item.model_dump() for item in items], "idempotency_key": idempotency_key})


@mcp.tool(title="List child lessons", annotations=READ)
async def family_child_lessons_list(child_user_id: str, status: Literal["active", "archived", "all"] = "active") -> dict[str, Any]:
    """List assigned lessons (active by default, or archived/all) for a child linked to the authenticated parent."""
    return await _call("family_child_lessons_list", {"child_user_id": child_user_id, "status": status})


@mcp.tool(title="List child active lessons", annotations=READ)
async def family_child_active_lessons_list(child_user_id: str) -> dict[str, Any]:
    """The child's currently active assigned lessons (at most 5) with the priority flag."""
    return await _call("family_child_active_lessons_list", {"child_user_id": child_user_id})


@mcp.tool(title="List child archived lessons", annotations=READ)
async def family_child_archived_lessons_list(child_user_id: str) -> dict[str, Any]:
    """Lessons archived for this child by the last-5 rule or manually; words, progress and difficult flags are kept."""
    return await _call("family_child_archived_lessons_list", {"child_user_id": child_user_id})


@mcp.tool(title="Archive child lesson", annotations=WRITE)
async def family_child_lesson_archive(child_user_id: str, lesson_title: str) -> dict[str, Any]:
    """Move one assigned lesson to the child's archive without deleting anything; clears priority first if needed."""
    return await _call("family_child_lesson_archive", {"child_user_id": child_user_id, "lesson_title": lesson_title})


@mcp.tool(title="Restore child lesson from archive", annotations=WRITE)
async def family_child_lesson_restore(child_user_id: str, lesson_title: str) -> dict[str, Any]:
    """Return an archived lesson to the child's active list as the newest one; the last-5 rule may archive the oldest other lesson."""
    return await _call("family_child_lesson_restore", {"child_user_id": child_user_id, "lesson_title": lesson_title})


@mcp.tool(title="Clean up child active lessons", annotations=WRITE)
async def family_child_lessons_cleanup(child_user_id: str, keep: Annotated[int, Field(ge=1, le=5)] = 5) -> dict[str, Any]:
    """Archive everything beyond the newest `keep` active lessons of one child (priority lesson is always kept)."""
    return await _call("family_child_lessons_cleanup", {"child_user_id": child_user_id, "keep": keep})


@mcp.tool(title="List child difficult words", annotations=READ)
async def family_child_difficult_words_list(child_user_id: str, lesson_title: str | None = None, limit: Annotated[int, Field(ge=1, le=100)] = 50, cursor: int = 0) -> dict[str, Any]:
    """Difficult words of one linked child (their personal flags), including words from archived lessons."""
    return await _call("family_child_difficult_words_list", {"child_user_id": child_user_id, "lesson_title": lesson_title, "limit": limit, "cursor": cursor})


@mcp.tool(title="Add child difficult words", annotations=WRITE)
async def family_child_difficult_words_add(child_user_id: str, word_ids: Annotated[list[int], Field(min_length=1, max_length=100)], source: Literal["parent", "auto_errors"] = "parent") -> dict[str, Any]:
    """Mark words difficult for ONE linked child only (other children are unaffected)."""
    return await _call("family_child_difficult_words_add", {"child_user_id": child_user_id, "word_ids": word_ids, "source": source})


@mcp.tool(title="Remove child difficult words", annotations=WRITE)
async def family_child_difficult_words_remove(child_user_id: str, word_ids: Annotated[list[int], Field(min_length=1, max_length=100)]) -> dict[str, Any]:
    """Clear the difficult flag on words for ONE linked child only."""
    return await _call("family_child_difficult_words_remove", {"child_user_id": child_user_id, "word_ids": word_ids})


@mcp.tool(title="Child difficult-word candidates", annotations=READ)
async def family_child_difficult_words_candidates_get(child_user_id: str, days: Annotated[int, Field(ge=1, le=365)] = 30, min_wrong: Annotated[int, Field(ge=1, le=100)] = 2, lesson_title: str | None = None, limit: Annotated[int, Field(ge=1, le=100)] = 50) -> dict[str, Any]:
    """Words one linked child answered wrong at least min_wrong times; read-only input for family_child_difficult_words_add(source='auto_errors')."""
    return await _call("family_child_difficult_words_candidates_get", {"child_user_id": child_user_id, "days": days, "min_wrong": min_wrong, "lesson_title": lesson_title, "limit": limit})


@mcp.tool(title="List assigned child lesson words", annotations=READ)
async def family_child_lesson_words_list(child_user_id: str, lesson_title: str, limit: Annotated[int, Field(ge=1, le=100)] = 50, cursor: int = 0) -> dict[str, Any]:
    """Read the parent's canonical words assigned to one linked child, with that child's difficult flag."""
    return await _call("family_child_lesson_words_list", {"child_user_id": child_user_id, "lesson_title": lesson_title, "limit": limit, "cursor": cursor})


@mcp.tool(title="Assign lesson to child", annotations=WRITE)
async def family_child_lesson_assign(child_user_id: str, lesson_title: str, idempotency_key: Annotated[str, Field(min_length=8, max_length=128)]) -> dict[str, Any]:
    """Assign one of the parent's canonical lessons to a linked child without copying words."""
    return await _call("family_child_lesson_assign", {"child_user_id": child_user_id, "lesson_title": lesson_title, "idempotency_key": idempotency_key})


@mcp.tool(title="Assign lesson to several children", annotations=WRITE)
async def family_children_lesson_assign(child_user_ids: Annotated[list[str], Field(min_length=1, max_length=100)], lesson_title: str, idempotency_key: Annotated[str, Field(min_length=8, max_length=128)]) -> dict[str, Any]:
    """Assign one canonical parent lesson to several linked children without copying words."""
    return await _call("family_children_lesson_assign", {"child_user_ids": child_user_ids, "lesson_title": lesson_title, "idempotency_key": idempotency_key})


@mcp.tool(title="Assign complete lesson to child", annotations=WRITE)
async def lesson_assign_complete(
    child_user_id: str,
    lesson_title: str,
    idempotency_key: Annotated[str, Field(min_length=8, max_length=128)],
    set_priority: bool = False,
    word_fills: Annotated[list[WordFill] | None, Field(max_length=100)] = None,
    use_cloud: bool = True,
) -> dict[str, Any]:
    """Safe assignment of an existing lesson to ONE linked child: reads only that child's languages, adds only missing translations/examples (word_fills and/or cloud), validates for the child, then assigns, applies priority and the last-5 rule. Returns LESSON_INCOMPLETE with missing_fields instead of assigning an incomplete lesson."""
    return await _call(
        "lesson_assign_complete",
        {
            "child_user_id": child_user_id, "lesson_title": lesson_title, "idempotency_key": idempotency_key,
            "set_priority": set_priority, "word_fills": [fill.model_dump() for fill in (word_fills or [])], "use_cloud": use_cloud,
        },
        long_running=True,
    )


@mcp.tool(title="Unassign lesson from child", annotations=WRITE)
async def family_child_lesson_unassign(child_user_id: str, lesson_title: str) -> dict[str, Any]:
    """Remove one parent's lesson assignment from a linked child without deleting any words or progress."""
    return await _call("family_child_lesson_unassign", {"child_user_id": child_user_id, "lesson_title": lesson_title})


@mcp.tool(title="Set child priority lesson", annotations=WRITE)
async def family_child_priority_lesson_set(child_user_id: str, lesson_title: str) -> dict[str, Any]:
    """Set a priority lesson only for a linked child."""
    return await _call("family_child_priority_lesson_set", {"child_user_id": child_user_id, "lesson_title": lesson_title})


@mcp.tool(title="Clear child priority lesson", annotations=WRITE)
async def family_child_priority_lesson_clear(child_user_id: str) -> dict[str, Any]:
    """Clear the current priority lesson for a linked child."""
    return await _call("family_child_priority_lesson_clear", {"child_user_id": child_user_id})


@mcp.tool(
    title="Import lesson file",
    annotations=WRITE,
    meta={"openai/fileParams": ["file"]},
)
async def lesson_import_file(
    file: OpenAIFile,
    lesson_title: str | None = None,
    dry_run: bool = True,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Preview/import CSV/JSON. Requires a meaningful lesson title and all configured translations/examples. Preview returns words to complete with ChatGPT before words_add; incomplete imports save nothing."""
    content, _content_type = await download_file(file.download_url)
    title, words = parse_words(content, file_name=file.file_name or "", lesson_title=lesson_title or "")
    preview = {"lesson_title": title, "rows": len(words), "languages": sorted({key for word in words for key, value in word.items() if value and not key.startswith("ex_")}), "dry_run": dry_run}
    if dry_run:
        languages = await _call("my_languages_get", {})
        if not languages.get("ok"):
            return languages
        preview["words"] = words
        preview["requirements"] = languages["data"]
        return {"ok": True, "data": preview, "warnings": [], "truncated": False, "error": None}
    if not idempotency_key:
        return {"ok": False, "data": None, "warnings": [], "truncated": False, "error": {"code": "IDEMPOTENCY_KEY_REQUIRED", "message": "idempotency_key is required for import", "retryable": False, "details": {}}}
    return await _call("lesson_import_file", {"lesson_title": title, "words": words, "idempotency_key": idempotency_key})


@mcp.tool(title="List subscriptions", annotations=READ)
async def subscriptions_list(limit: Annotated[int, Field(ge=1, le=100)] = 50, cursor: int = 0, search: str = "", status: str = "", provider: str = "") -> dict[str, Any]:
    """Superuser-only list of application subscriptions. Requires subscriptions.admin consent."""
    return await _call("subscriptions_list", {"limit": limit, "cursor": cursor, "search": search, "status": status, "provider": provider})


@mcp.tool(title="Grant subscription access", annotations=DESTRUCTIVE)
async def subscription_grant_access(user_id: str, confirm: bool = False) -> dict[str, Any]:
    """Superuser-only grant of manual unlimited access. Requires explicit confirmation."""
    return await _call("subscription_grant_access", {"user_id": user_id, "confirm": confirm})


@mcp.tool(title="Revoke subscription access", annotations=DESTRUCTIVE)
async def subscription_revoke_access(user_id: str, confirm: bool = False) -> dict[str, Any]:
    """Superuser-only revocation of manual access. Requires explicit confirmation."""
    return await _call("subscription_revoke_access", {"user_id": user_id, "confirm": confirm})


@mcp.tool(title="List users", annotations=READ)
async def users_list(limit: Annotated[int, Field(ge=1, le=100)] = 50, cursor: int = 0, search: str = "", status: str = "", subscription_status: str = "") -> dict[str, Any]:
    """Superuser-only user directory. Requires users.admin consent."""
    return await _call("users_list", {"limit": limit, "cursor": cursor, "search": search, "status": status, "subscription_status": subscription_status})


@mcp.tool(title="Search users", annotations=READ)
async def users_search(query: Annotated[str, Field(min_length=1, max_length=200)], limit: Annotated[int, Field(ge=1, le=100)] = 25, cursor: int = 0) -> dict[str, Any]:
    """Superuser-only search by user ID, name, username or email."""
    return await _call("users_search", {"query": query, "limit": limit, "cursor": cursor})


@mcp.tool(title="Get user administration card", annotations=READ)
async def admin_user_get(user_id: str) -> dict[str, Any]:
    """Superuser-only account, subscription, learning and activity summary for one user."""
    return await _call("admin_user_get", {"user_id": user_id})


@mcp.tool(title="Get user learning progress", annotations=READ)
async def admin_user_progress_get(user_id: str, days: Annotated[int, Field(ge=1, le=365)] = 30, lesson_title: str = "") -> dict[str, Any]:
    """Superuser-only factual learning activity summary; unavailable metrics are null."""
    return await _call("admin_user_progress_get", {"user_id": user_id, "days": days, "lesson_title": lesson_title})


@mcp.tool(title="List user lessons", annotations=READ)
async def admin_user_lessons_list(user_id: str, include_hidden: bool = False, limit: Annotated[int, Field(ge=1, le=100)] = 50, cursor: int = 0) -> dict[str, Any]:
    """Superuser-only paginated lesson inventory for one user."""
    return await _call("admin_user_lessons_list", {"user_id": user_id, "include_hidden": include_hidden, "limit": limit, "cursor": cursor})


@mcp.tool(title="Search user words", annotations=READ)
async def admin_user_words_search(user_id: str, query: Annotated[str, Field(min_length=1, max_length=500)], lesson_title: str = "", limit: Annotated[int, Field(ge=1, le=100)] = 25) -> dict[str, Any]:
    """Superuser-only diagnostic read of another user's words; it never edits them."""
    return await _call("admin_user_words_search", {"user_id": user_id, "query": query, "lesson_title": lesson_title, "limit": limit})


@mcp.tool(title="Application analytics summary", annotations=READ)
async def admin_analytics_summary(days: Annotated[int, Field(ge=1, le=365)] = 30) -> dict[str, Any]:
    """Superuser-only aggregate application analytics. Requires analytics.admin consent."""
    return await _call("admin_analytics_summary", {"days": days})


@mcp.tool(title="Rank users by activity", annotations=READ)
async def admin_analytics_users(sort: Literal["active", "inactive"] = "active", limit: Annotated[int, Field(ge=1, le=100)] = 50, cursor: int = 0, search: str = "") -> dict[str, Any]:
    """Superuser-only paginated activity or inactivity ranking."""
    return await _call("admin_analytics_users", {"sort": sort, "limit": limit, "cursor": cursor, "search": search})


@mcp.tool(title="List admin audit log", annotations=READ)
async def admin_audit_log_list(limit: Annotated[int, Field(ge=1, le=100)] = 50, cursor: int = 0) -> dict[str, Any]:
    """Superuser-only audit log for administrative subscription changes."""
    return await _call("admin_audit_log_list", {"limit": limit, "cursor": cursor})


@mcp.resource("learn://me")
async def resource_me() -> dict[str, Any]:
    """Authenticated profile resource."""
    return await _call("me_get")


@mcp.resource("learn://lessons")
async def resource_lessons() -> dict[str, Any]:
    """Authenticated bounded lesson list resource."""
    return await _call("lessons_list", {"include_hidden": False})


@mcp.resource("learn://lessons/{lesson_title}")
async def resource_lesson(lesson_title: str) -> dict[str, Any]:
    """Authenticated lesson resource."""
    return await _call("lesson_get", {"lesson_title": lesson_title})


@mcp.resource("learn://progress/summary")
async def resource_progress() -> dict[str, Any]:
    """Authenticated seven-day progress resource."""
    return await _call("progress_summary", {"days": 7})


@mcp.resource("learn://family/status")
async def resource_family() -> dict[str, Any]:
    """Authenticated family status resource."""
    return await _call("family_status_get")


@mcp.prompt()
def create_vocabulary_lesson(topic: str, languages: str, word_count: int = 20) -> str:
    """Prepare a lesson preview before writing it."""
    return f"Read my_languages_get and prepare {word_count} vocabulary items about {topic} with a meaningful lesson title, translations and examples in ALL configured languages (including {languages}). Show a preview first; call lesson_create_complete once approved and report success only for COMPLETE."


@mcp.prompt()
def create_complete_lesson(title: str, word_count: int = 10) -> str:
    """Create a fully filled lesson for the authenticated user only."""
    return (
        f"Call my_languages_get, then prepare {word_count} words for the lesson '{title}' with translations and one "
        "example sentence (same meaning) in every language returned. Do not look up anyone else's languages. Call "
        "lesson_create_complete once approved; report the lesson as created only if status is COMPLETE."
    )


@mcp.prompt()
def assign_lesson_to_child(child_user_id: str, lesson_title: str) -> str:
    """Assign an existing lesson to one linked child safely."""
    return (
        f"Call family_child_languages_get for {child_user_id} only, then lesson_assign_complete for '{lesson_title}'. "
        "If it returns LESSON_INCOMPLETE, provide only the listed missing fields via word_fills and retry with a new "
        "idempotency_key. Report the lesson as assigned only when assigned=true."
    )


@mcp.prompt()
def review_difficult_words(lesson_title: str = "") -> str:
    """Start a review using the user's difficult words."""
    return f"Call difficult_words_list for {lesson_title or 'all lessons'}, then quiz the user one word at a time and record results only with approval."


@mcp.prompt()
def analyze_learning_progress(days: int = 7) -> str:
    """Read and explain progress without modifying it."""
    return f"Call progress_summary(days={days}) and explain the result concisely without changing any data."


@mcp.custom_route("/health", methods=["GET"])
async def gateway_health(_request: Request) -> Response:
    """Container health without user data or authentication."""
    result = await health()
    result["redis"] = await redis_health()
    result["ok"] = bool(result.get("ok") and result["redis"] == "ok")
    return JSONResponse(result, status_code=200 if result.get("ok") else 503)


security = TransportSecuritySettings(
    allowed_hosts=[config.ALLOWED_HOST, f"{config.ALLOWED_HOST}:*", "mcp-gateway", "mcp-gateway:*", "127.0.0.1", "localhost", "localhost:*"],
    allowed_origins=["https://chatgpt.com", "https://chat.openai.com"],
)
app = mcp.streamable_http_app(transport_security=security)
