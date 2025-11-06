# app/audio_service.py
# [v1.0] Генерация MP3 c помощью gTTS. Папка создаётся автоматически.

from __future__ import annotations
import os
import logging
from typing import Optional

try:
    from gtts import gTTS  # pip install gTTS==2.5.1
    _HAS_GTTS = True
except Exception:
    _HAS_GTTS = False

log = logging.getLogger(__name__)

# Карта языков (ключ в БД/фронте -> код для TTS)
LANG_MAP = {
    "nl": "nl",
    "en": "en",
    "ru": "ru",
}

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def synthesize_to_mp3(text: str, lang_code: str, out_path: str) -> bool:
    """
    Делает MP3-файл по указанному тексту и языку. Возвращает True/False.
    """
    if not text or not text.strip():
        log.warning("[TTS] empty text, skip")
        return False

    if not _HAS_GTTS:
        log.error("[TTS] gTTS is not installed. Add gTTS==2.5.1 to requirements.txt")
        return False

    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        ensure_dir(os.path.dirname(out_path))
        tts.save(out_path)
        return True
    except Exception as e:
        log.exception("[TTS] gTTS synthesize failed: %s", e)
        return False


def build_filename(word_id: int, lang: str) -> str:
    # Имя файла: w<ID>_<lang>.mp3
    return f"w{int(word_id)}_{lang}.mp3"
