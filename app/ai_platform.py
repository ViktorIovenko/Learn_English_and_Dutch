"""Клиент облачной генерации слов через AI Platform (runtime/chat).

Алгоритм такой же, как раньше делался напрямую в Ollama (см. upload.js /
OllamaConfig.kt), только system prompt теперь статически хранится в AI
Platform под соответствующим профилем (ключ AI_PLATFORM_API_KEY_<TASK>
привязан к одному профилю), а сюда передаётся только динамическая часть.
"""

import json
import re
from dataclasses import dataclass

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
    return bool(Config.AI_PLATFORM_BASE_URL)


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


def translate_word(
    word: str,
    from_lang: str,
    level: str = "A2",
    known_ru: str | None = None,
) -> tuple[dict, TokenUsage]:
    lang_label = LANG_LABELS.get(from_lang, from_lang)
    lines = [
        f'Word: "{word}"',
        f"Source language: {lang_label}",
        f"CEFR level: {level}",
    ]
    if known_ru:
        lines.append(f'Known Russian translation (copy exactly, do not retranslate): "{known_ru}"')
    message = "\n".join(lines)

    runtime = _call_runtime_chat(Config.AI_PLATFORM_API_KEY_TRANSLATE_WORD, message)
    try:
        parsed = _extract_json(runtime.content)
    except AiPlatformError as exc:
        raise AiPlatformError(str(exc), usage=runtime.usage) from exc
    if isinstance(parsed, list):
        parsed = parsed[0] if parsed else {}
    if not isinstance(parsed, dict):
        raise AiPlatformError(
            "Облако вернуло неожиданный формат ответа для перевода слова",
            usage=runtime.usage,
        )
    return parsed, runtime.usage


def suggest_topic_words(
    topic: str,
    lang: str,
    level: str,
    count: int,
    existing_words: list[str],
) -> tuple[list[str], TokenUsage]:
    lang_label = LANG_LABELS.get(lang, lang)
    lines = [
        f'Topic: "{topic}"',
        f"Target language: {lang_label}",
        f"CEFR level: {level}",
        f"Word count: {count}",
    ]
    if existing_words:
        avoid = ", ".join(existing_words[:150])
        lines.append(f"Words already known (do not repeat): {avoid}")
    message = "\n".join(lines)

    runtime = _call_runtime_chat(Config.AI_PLATFORM_API_KEY_SUGGEST_TOPIC_WORDS, message)
    try:
        parsed = _extract_json(runtime.content)
    except AiPlatformError as exc:
        raise AiPlatformError(str(exc), usage=runtime.usage) from exc
    if isinstance(parsed, dict):
        values = list(parsed.values())
        parsed = [item for sub in values if isinstance(sub, list) for item in sub]
    if not isinstance(parsed, list):
        raise AiPlatformError(
            "Облако вернуло неожиданный формат ответа для подбора слов",
            usage=runtime.usage,
        )
    words = [w for w in parsed if isinstance(w, str) and w.strip()]
    return words, runtime.usage


def translate_language(
    source_word: str,
    source_sentence: str,
    source_lang_name: str,
    target_lang_name: str,
) -> tuple[dict, TokenUsage]:
    message = (
        f"Source language: {source_lang_name}\n"
        f"Target language: {target_lang_name}\n"
        f'Source word: "{source_word}"\n'
        f'Source sentence: "{source_sentence}"'
    )

    runtime = _call_runtime_chat(Config.AI_PLATFORM_API_KEY_TRANSLATE_LANGUAGE, message)
    try:
        parsed = _extract_json(runtime.content)
    except AiPlatformError as exc:
        raise AiPlatformError(str(exc), usage=runtime.usage) from exc
    if not isinstance(parsed, dict) or (not parsed.get("word") and not parsed.get("sentence")):
        raise AiPlatformError("Облако не вернуло слово и предложение", usage=runtime.usage)
    return (
        {
            "word": str(parsed.get("word") or "").strip(),
            "sentence": str(parsed.get("sentence") or "").strip(),
        },
        runtime.usage,
    )
