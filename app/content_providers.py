"""Provider boundary. No translation/example service is enabled by default.

A configured module exposes translate_word, translate_sentence,
generate_examples and/or suggest_words callables accepting keyword arguments.
Results are plain dictionaries (suggest_words returns a list). TTS adapters
expose identity (all synthesis parameters) and synthesize(text, language, path).
"""
import importlib
from config import Config

LANGUAGES = ("nl", "en", "ru", "de", "fr", "es", "it", "pt", "pl", "uk")
LANG_NAMES = dict(zip(LANGUAGES, ("Dutch", "English", "Russian", "German", "French", "Spanish", "Italian", "Portuguese", "Polish", "Ukrainian")))


def language_code(value):
    value = str(value or "").strip().lower()
    for code, name in LANG_NAMES.items():
        if value in (code, name.lower()):
            return code
    raise ValueError("unsupported language")


def adapter(operation):
    setting = {"translate_word": "CONTENT_TRANSLATION_PROVIDER_MODULE", "translate_sentence": "CONTENT_TRANSLATION_PROVIDER_MODULE",
               "generate_examples": "CONTENT_EXAMPLE_PROVIDER_MODULE", "suggest_words": "CONTENT_TOPIC_PROVIDER_MODULE"}.get(operation, "CONTENT_PROVIDER_MODULE")
    module = getattr(Config, setting, "") or getattr(Config, "CONTENT_PROVIDER_MODULE", "")
    return getattr(importlib.import_module(module), operation, None) if module else None


def available(operation):
    return callable(adapter(operation))


class GttsProvider:
    # Preserve the already-used backend; no new service or API key is added.
    identity = {"provider": "gtts", "version": "1", "voice": "default", "slow": False, "tld": "com"}

    def synthesize(self, text, language, path):
        from gtts import gTTS
        gTTS(text=text, lang=language, slow=False, tld="com").save(str(path))


def tts_provider():
    module = getattr(Config, "CONTENT_TTS_PROVIDER_MODULE", "")
    return importlib.import_module(module).provider if module else GttsProvider()
