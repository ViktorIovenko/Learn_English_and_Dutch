"""Compatibility facade over the shared server content service.

Legacy runtime transport is retained for explicitly configured adapters only.
No external translation/example provider is enabled by default.
"""

import json
import re
from dataclasses import dataclass, replace

import requests

from config import Config

LANG_LABELS = {
    "nl": "Dutch",
    "en": "English",
    "ru": "Russian",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "uk": "Ukrainian",
}


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    provider_calls: int = 0

    @classmethod
    def from_payload(cls, payload: object) -> "TokenUsage":
        data = payload if isinstance(payload, dict) else {}

        def count(name: str) -> int:
            try:
                return max(int(data.get(name) or 0), 0)
            except (TypeError, ValueError):
                return 0

        prompt = count("prompt_tokens")
        completion = count("completion_tokens")
        total = count("total_tokens") or (prompt + completion)
        return cls(prompt_tokens=prompt, completion_tokens=completion, total_tokens=total)


@dataclass(frozen=True)
class RuntimeChatResult:
    content: str
    usage: TokenUsage


class AiPlatformError(Exception):
    def __init__(self, message: str, *, usage: TokenUsage | None = None):
        super().__init__(message)
        self.usage = usage or TokenUsage()


def is_configured() -> bool:
    from app.content_providers import available
    return any(available(operation) for operation in ("translate_word","translate_sentence","generate_examples","suggest_words"))

def _extract_json(raw: str):
    stripped = re.sub(r"```json\s*", "", raw)
    stripped = re.sub(r"```\s*", "", stripped).strip()

    array_start = stripped.find("[")
    object_start = stripped.find("{")

    if array_start != -1 and (object_start == -1 or array_start < object_start):
        end = stripped.rfind("]")
        candidate = stripped[array_start:end + 1] if end > array_start else stripped
    elif object_start != -1:
        end = stripped.rfind("}")
        candidate = stripped[object_start:end + 1] if end > object_start else stripped
    else:
        candidate = stripped

    try:
        return json.loads(candidate)
    except (TypeError, ValueError) as exc:
        raise AiPlatformError(f"Облако вернуло невалидный JSON: {exc}") from exc


def _call_runtime_chat(api_key: str, message: str, context: dict | None = None) -> RuntimeChatResult:
    if not Config.AI_PLATFORM_BASE_URL:
        raise AiPlatformError("AI_PLATFORM_BASE_URL не настроен")
    if not api_key:
        raise AiPlatformError("Ключ AI Platform для этой задачи не настроен")

    url = f"{Config.AI_PLATFORM_BASE_URL.rstrip('/')}/api/v1/runtime/chat"
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"message": message, "context": context or {}},
            timeout=Config.AI_PLATFORM_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise AiPlatformError(f"AI Platform недоступна: {exc}") from exc

    try:
        payload = response.json()
    except ValueError:
        payload = None

    usage = TokenUsage.from_payload(
        payload.get("usage") if isinstance(payload, dict) else None
    )
    if response.status_code == 401 or response.status_code == 403:
        raise AiPlatformError("AI Platform отклонила ключ доступа", usage=usage)
    if not response.ok:
        detail = payload.get("detail", "") if isinstance(payload, dict) else ""
        raise AiPlatformError(
            f"AI Platform вернула ошибку HTTP {response.status_code}: {detail}",
            usage=usage,
        )

    if not isinstance(payload, dict) or not isinstance(payload.get("content"), str):
        raise AiPlatformError("AI Platform вернула некорректный ответ", usage=usage)
    return RuntimeChatResult(
        content=payload["content"],
        usage=usage,
    )


def translate_word(word, from_lang, level="", known_ru=None, *, supplied=None, languages=None, sense="", context="", examples=True):
    from app.content_service import resolve_word
    values = dict(supplied or {})
    if known_ru:
        values["ru"] = known_ru
    try:
        result = resolve_word(word, from_lang, languages or ("nl", "en", "ru"), level, values, sense, context, examples)
    except (ValueError, RuntimeError) as exc:
        raise AiPlatformError(str(exc)) from exc
    return result, replace(TokenUsage.from_payload(result.get("usage")),provider_calls=result["provider_calls"])


def translate_language(source_word, source_sentence, source_lang_name, target_lang_name, *, supplied=None, sense="", context=""):
    from app.content_service import translate_language as resolve
    try:
        result = resolve(source_word, source_sentence, source_lang_name, target_lang_name, supplied, sense, context)
    except (ValueError, RuntimeError) as exc:
        raise AiPlatformError(str(exc)) from exc
    return result, replace(TokenUsage.from_payload(result.get("usage")),provider_calls=result["provider_calls"])


def suggest_topic_words(topic, lang, level, count, existing_words):
    from app.content_service import ensure_schema, _request
    from app.content_db import transaction
    from app.content_providers import language_code
    request = {"topic": str(topic).strip(), "language": language_code(lang), "level": level, "count": max(1,min(50,count))}
    with transaction(Config.DB_PATH) as conn:
        ensure_schema(conn)
        result, calls = _request(conn, "suggest_words", request)
    if not result:
        raise AiPlatformError("Подбор темы недоступен: внешний сервис ещё не подключён")
    words = result.get("words", [])
    if not isinstance(words,list):
        raise AiPlatformError("provider words must be a list")
    return [word for word in words if isinstance(word,str) and word.strip()], replace(TokenUsage.from_payload(result.get("_usage") if calls else {}),provider_calls=calls)
