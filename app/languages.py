"""ParallelLingvo supported learning-language catalog.

The application data model must not depend on one database column per language.
This registry defines the initial launch catalog while the normalized translation
schema can support additional BCP-47/ISO language codes later without a schema
redesign.
"""

from __future__ import annotations

from typing import Dict, List


LANGUAGES: List[Dict[str, object]] = [
    # European languages
    {"code": "en", "name": "English", "native_name": "English", "region": "Europe", "rtl": False},
    {"code": "nl", "name": "Dutch", "native_name": "Nederlands", "region": "Europe", "rtl": False},
    {"code": "de", "name": "German", "native_name": "Deutsch", "region": "Europe", "rtl": False},
    {"code": "fr", "name": "French", "native_name": "Français", "region": "Europe", "rtl": False},
    {"code": "es", "name": "Spanish", "native_name": "Español", "region": "Europe", "rtl": False},
    {"code": "it", "name": "Italian", "native_name": "Italiano", "region": "Europe", "rtl": False},
    {"code": "pt", "name": "Portuguese", "native_name": "Português", "region": "Europe", "rtl": False},
    {"code": "pl", "name": "Polish", "native_name": "Polski", "region": "Europe", "rtl": False},
    {"code": "ru", "name": "Russian", "native_name": "Русский", "region": "Europe", "rtl": False},
    {"code": "uk", "name": "Ukrainian", "native_name": "Українська", "region": "Europe", "rtl": False},
    {"code": "cs", "name": "Czech", "native_name": "Čeština", "region": "Europe", "rtl": False},
    {"code": "sk", "name": "Slovak", "native_name": "Slovenčina", "region": "Europe", "rtl": False},
    {"code": "hu", "name": "Hungarian", "native_name": "Magyar", "region": "Europe", "rtl": False},
    {"code": "ro", "name": "Romanian", "native_name": "Română", "region": "Europe", "rtl": False},
    {"code": "bg", "name": "Bulgarian", "native_name": "Български", "region": "Europe", "rtl": False},
    {"code": "hr", "name": "Croatian", "native_name": "Hrvatski", "region": "Europe", "rtl": False},
    {"code": "sr", "name": "Serbian", "native_name": "Српски", "region": "Europe", "rtl": False},
    {"code": "bs", "name": "Bosnian", "native_name": "Bosanski", "region": "Europe", "rtl": False},
    {"code": "sl", "name": "Slovenian", "native_name": "Slovenščina", "region": "Europe", "rtl": False},
    {"code": "el", "name": "Greek", "native_name": "Ελληνικά", "region": "Europe", "rtl": False},
    {"code": "sv", "name": "Swedish", "native_name": "Svenska", "region": "Europe", "rtl": False},
    {"code": "no", "name": "Norwegian", "native_name": "Norsk", "region": "Europe", "rtl": False},
    {"code": "da", "name": "Danish", "native_name": "Dansk", "region": "Europe", "rtl": False},
    {"code": "fi", "name": "Finnish", "native_name": "Suomi", "region": "Europe", "rtl": False},
    {"code": "et", "name": "Estonian", "native_name": "Eesti", "region": "Europe", "rtl": False},
    {"code": "lv", "name": "Latvian", "native_name": "Latviešu", "region": "Europe", "rtl": False},
    {"code": "lt", "name": "Lithuanian", "native_name": "Lietuvių", "region": "Europe", "rtl": False},
    {"code": "is", "name": "Icelandic", "native_name": "Íslenska", "region": "Europe", "rtl": False},
    {"code": "ga", "name": "Irish", "native_name": "Gaeilge", "region": "Europe", "rtl": False},
    {"code": "sq", "name": "Albanian", "native_name": "Shqip", "region": "Europe", "rtl": False},
    {"code": "mk", "name": "Macedonian", "native_name": "Македонски", "region": "Europe", "rtl": False},
    {"code": "tr", "name": "Turkish", "native_name": "Türkçe", "region": "Europe", "rtl": False},
    {"code": "mt", "name": "Maltese", "native_name": "Malti", "region": "Europe", "rtl": False},
    {"code": "be", "name": "Belarusian", "native_name": "Беларуская", "region": "Europe", "rtl": False},
    {"code": "rm", "name": "Romansh", "native_name": "Rumantsch", "region": "Europe", "rtl": False},
    {"code": "ka", "name": "Georgian", "native_name": "ქართული", "region": "Europe", "rtl": False},
    {"code": "hy", "name": "Armenian", "native_name": "Հայերեն", "region": "Europe", "rtl": False},
    {"code": "az", "name": "Azerbaijani", "native_name": "Azərbaycan dili", "region": "Europe", "rtl": False},

    # Major world languages
    {"code": "zh", "name": "Chinese (Mandarin)", "native_name": "中文（普通话）", "region": "World", "rtl": False},
    {"code": "ja", "name": "Japanese", "native_name": "日本語", "region": "World", "rtl": False},
    {"code": "ko", "name": "Korean", "native_name": "한국어", "region": "World", "rtl": False},
    {"code": "ar", "name": "Arabic", "native_name": "العربية", "region": "World", "rtl": True},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी", "region": "World", "rtl": False},
    {"code": "id", "name": "Indonesian", "native_name": "Bahasa Indonesia", "region": "World", "rtl": False},
    {"code": "vi", "name": "Vietnamese", "native_name": "Tiếng Việt", "region": "World", "rtl": False},
]

LANGUAGE_BY_CODE: Dict[str, Dict[str, object]] = {
    str(language["code"]): language for language in LANGUAGES
}

SUPPORTED_LANGUAGE_CODES = tuple(LANGUAGE_BY_CODE.keys())
LEGACY_LANGUAGE_CODES = ("nl", "en", "ru")
DEFAULT_USER_LANGUAGES = ("nl", "en", "ru")
MIN_PARALLEL_LANGUAGES = 3


def is_supported_language(code: str) -> bool:
    return str(code or "").strip().lower() in LANGUAGE_BY_CODE


def get_language(code: str) -> Dict[str, object] | None:
    return LANGUAGE_BY_CODE.get(str(code or "").strip().lower())


def public_language_catalog() -> List[Dict[str, object]]:
    """Return a JSON-safe copy used by API clients."""
    return [dict(language) for language in LANGUAGES]
