from __future__ import annotations

import re
import string
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from app.i18n import LEGACY_RU_TRANSLATIONS, SUPPORTED_UI_LANGUAGES, TRANSLATIONS


ROOT = Path(__file__).resolve().parents[1]
ANDROID_RES = ROOT / "android" / "app" / "src" / "main" / "res"
ANDROID_PLACEHOLDER = re.compile(r"%\d+\$[a-zA-Z]|%[a-zA-Z]")


def _format_fields(value: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(value) if name}


def _android_resources(path: Path) -> tuple[set[str], dict[str, str]]:
    root = ET.parse(path).getroot()
    names = {element.attrib["name"] for element in root if element.attrib.get("name")}
    strings = {
        element.attrib["name"]: element.text or ""
        for element in root
        if element.tag == "string" and element.attrib.get("name")
    }
    return names, strings


class UiLocalizationTests(unittest.TestCase):
    def test_web_catalogs_are_complete_and_keep_placeholders(self):
        english = TRANSLATIONS["en"]
        expected_keys = set(english)
        self.assertEqual(set(SUPPORTED_UI_LANGUAGES), set(TRANSLATIONS))
        for language in SUPPORTED_UI_LANGUAGES:
            with self.subTest(language=language):
                catalog = TRANSLATIONS[language]
                self.assertEqual(expected_keys, set(catalog))
                for key, source in english.items():
                    self.assertEqual(_format_fields(source), _format_fields(catalog[key]), key)

    def test_legacy_web_catalogs_cover_the_same_phrases(self):
        self.assertEqual(set(SUPPORTED_UI_LANGUAGES), set(LEGACY_RU_TRANSLATIONS))
        expected = set(LEGACY_RU_TRANSLATIONS["ru"])
        self.assertTrue(expected)
        for language in SUPPORTED_UI_LANGUAGES:
            with self.subTest(language=language):
                self.assertEqual(expected, set(LEGACY_RU_TRANSLATIONS[language]))

    def test_android_locales_are_complete_and_keep_placeholders(self):
        base_names, base_strings = _android_resources(ANDROID_RES / "values" / "strings.xml")
        for language in SUPPORTED_UI_LANGUAGES:
            if language == "en":
                continue
            path = ANDROID_RES / f"values-{language}" / "strings.xml"
            with self.subTest(language=language):
                names, strings = _android_resources(path)
                self.assertEqual(base_names, names)
                for key, source in base_strings.items():
                    self.assertEqual(
                        sorted(ANDROID_PLACEHOLDER.findall(source)),
                        sorted(ANDROID_PLACEHOLDER.findall(strings[key])),
                        key,
                    )


if __name__ == "__main__":
    unittest.main()
