# app/audio_gen.py
# [ИЗМЕНЕНО v7.7]
# - Имя файла: <слово>_<lang>.mp3, папки: static/audio/<lang>/<lesson>/
# - Генерация ТОЛЬКО для явно переданных id
# - [НОВОЕ] Максимизация громкости: компрессия + пик-нормализация до -0.1 dBFS

from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Iterable
from gtts import gTTS  # pip install gTTS==2.5.1
import time
from config import Config
import traceback
import sys
import warnings
import shutil
from contextlib import closing
from app.tts_usage import (
    TtsUsageLimitExceeded,
    record_tts_request,
    reserve_tts_characters,
)

# pydub для пост-обработки (и ffmpeg в PATH)
warnings.filterwarnings(
    "ignore",
    message=r"Couldn't find ffmpeg or avconv.*",
    category=RuntimeWarning,
    module=r"pydub\.utils",
)
warnings.filterwarnings(
    "ignore",
    message=r"Couldn't find ffprobe or avprobe.*",
    category=RuntimeWarning,
    module=r"pydub\.utils",
)
try:
    from pydub import AudioSegment, effects  # pip install pydub==0.25.1
    _HAS_PYDUB = True
    _HAS_FFMPEG = bool(shutil.which("ffmpeg") or shutil.which("avconv"))
    _HAS_FFPROBE = bool(shutil.which("ffprobe") or shutil.which("avprobe"))
except Exception:
    _HAS_PYDUB = False
    _HAS_FFMPEG = False
    _HAS_FFPROBE = False

APP_DIR = Path(__file__).resolve().parent
AUDIO_ROOT = APP_DIR / "static" / "audio"
AUDIO_ROOT.mkdir(parents=True, exist_ok=True)
SUPPORTED_LANGS = {"nl", "en", "ru", "de", "fr", "es", "it", "pt", "pl", "uk"}


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _lesson_slug(s: str) -> str:
    s = (s or "").strip().replace("/", "_").replace("\\", "_")
    return "".join(ch if ch.isalnum() or ch in "-_ ." else "_" for ch in s)[:60] or "lesson"


def _filename_from_text(text: str, lang: str) -> str:
    base = (text or "").strip()
    safe = "".join(ch if ch.isalnum() else "_" for ch in base).strip("_")
    safe = safe[:60] or "word"
    return f"{safe}_{lang}.mp3"


def _tts_make(text: str, lang: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # tld='com' — фикс ошибки translate.google.en
    tts = gTTS(text=text, lang=lang, slow=False, tld="com")
    tts.save(str(out_path))


# -------------------- Пост-обработка громкости --------------------
def _peak_normalize(seg: "AudioSegment", target_dbfs: float) -> "AudioSegment":
    """
    Поднять уровень так, чтобы пиковое значение было ровно target_dbfs.
    """
    # В новых pydub есть seg.max_dBFS; если нет — effects.normalize + подстройка
    try:
        peak = seg.max_dBFS  # самый высокий пик в dBFS (отрицательное число)
        gain = target_dbfs - peak
        return seg.apply_gain(gain)
    except Exception:
        # fallback: нормализация RMS, затем чуть добить до target_dbfs
        seg = effects.normalize(seg)
        try:
            peak = seg.max_dBFS
            gain = target_dbfs - peak
            return seg.apply_gain(gain)
        except Exception:
            return seg


def _maximize_loudness(mp3_path: Path) -> None:
    """
    Максимально громко: компрессия динамического диапазона + пиковая нормализация.
    Экспорт с высоким битрейтом.
    """
    if not _HAS_PYDUB or not _HAS_FFMPEG or not _HAS_FFPROBE or not Config.AUDIO_MAXIMIZE:
        return
    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        return

    try:
        seg = AudioSegment.from_file(mp3_path)

        # 1) Лёгкий лимит/компрессия (threshold ближе к 0 — агрессивнее)
        seg = effects.compress_dynamic_range(
            seg,
            threshold=Config.AUDIO_COMP_THRESHOLD_DBFS,  # dBFS
            ratio=Config.AUDIO_COMP_RATIO,               # 6:1 по умолчанию
            attack=Config.AUDIO_COMP_ATTACK_MS,          # мс
            release=Config.AUDIO_COMP_RELEASE_MS         # мс
        )

        # 2) Пиковая нормализация до -0.1 dBFS (или что задано в конфиге)
        seg = _peak_normalize(seg, float(Config.AUDIO_PEAK_DBFS))

        # 3) Экспорт
        seg.export(mp3_path, format="mp3", bitrate=Config.AUDIO_MP3_BITRATE)
    except Exception:
        print("[AUDIO] maximize loudness failed:", file=sys.stderr)
        traceback.print_exc()


def _pick_word_text(row_dict: Dict[str, Any], lang: str) -> str:
    return (row_dict.get(lang) or row_dict.get(f"{lang}_word") or row_dict.get(f"translation_{lang}") or "").strip()


def _audio_url(lang: str, lesson_slug: str, fname: str) -> str:
    return f"/static/audio/{lang}/{lesson_slug}/{fname}"


def _existing_audio_path(url: str) -> Path | None:
    """Resolve only an existing URL inside app/static/audio."""
    raw = str(url or "").split("?", 1)[0].lstrip("/")
    if not raw.startswith("static/audio/"):
        return None
    target = (APP_DIR / raw).resolve()
    audio_root = AUDIO_ROOT.resolve()
    if target != audio_root and audio_root not in target.parents:
        return None
    return target if target.is_file() and target.stat().st_size > 500 else None


def ensure_audio_for_ids(db_path: str, ids: Iterable[int], langs: Iterable[str], user_id: str | None = None) -> Dict[str, Any]:
    """
    Создаёт MP3 только для указанных id и языков.
    Возвращает { ok: true, items: [ {id, nl, en, ru, ok}, ... ] }
    """
    ids = [int(i) for i in (ids or []) if str(i).isdigit()]
    langs = [str(x).strip().lower() for x in (langs or ["nl", "en", "ru"]) if str(x).strip().lower() in SUPPORTED_LANGS]
    if not ids or not langs:
        return {"ok": True, "items": []}

    items: List[Dict[str, Any]] = []
    generated = 0
    skipped = 0
    blocked = 0

    now_ms = int(time.time() * 1000)
    with closing(_connect(db_path)) as c:
        cols = [r["name"] for r in c.execute("PRAGMA table_info(words)")]
        if "updated_at" not in cols:
            c.execute("ALTER TABLE words ADD COLUMN updated_at INTEGER;")
            c.execute("UPDATE words SET updated_at = (strftime('%s','now') * 1000) WHERE updated_at IS NULL;")
            cols.append("updated_at")
        for lang in langs:
            for col in (lang, f"ex_{lang}", f"audio_{lang}"):
                if col not in cols:
                    c.execute(f"ALTER TABLE words ADD COLUMN {col} TEXT;")
                    cols.append(col)
        qmarks = ",".join("?" * len(ids))
        if user_id:
            where = f"(user_id = ? OR status = 'test') AND id IN ({qmarks})"
            params = [str(user_id)] + ids
        else:
            where = f"id IN ({qmarks})"
            params = ids
        select_cols = ",\n                   ".join(
            f"COALESCE({lang},'') AS {lang}, COALESCE(audio_{lang},'') AS audio_{lang}"
            for lang in langs
        )
        rows = c.execute(
            f"""
            SELECT id, lesson,
                   {select_cols}
            FROM words WHERE {where}
            """,
            params,
        ).fetchall()

        for r in rows:
            d = dict(r)
            wid = int(d["id"])
            lesson_slug = _lesson_slug(str(d.get("lesson") or "lesson"))

            out_per_lang = {lang: d.get(f"audio_{lang}") or "" for lang in langs}
            row_errors: list[dict[str, Any]] = []

            for lang in langs:
                try:
                    text = _pick_word_text(d, lang)
                    if not text:
                        out_per_lang[lang] = ""
                        continue

                    stored_url = str(d.get(f"audio_{lang}") or "")
                    if _existing_audio_path(stored_url):
                        out_per_lang[lang] = stored_url
                        skipped += 1
                        continue

                    fname = _filename_from_text(text, lang)
                    out_dir = AUDIO_ROOT / lang / lesson_slug
                    out_path = out_dir / fname

                    if out_path.exists() and out_path.stat().st_size > 500:
                        out_per_lang[lang] = _audio_url(lang, lesson_slug, fname)
                        skipped += 1
                    else:
                        reserve_tts_characters(
                            c,
                            user_id,
                            characters=len(text),
                            timezone_name=Config.TTS_USAGE_TIMEZONE,
                        )
                        print(f"[TTS] Generate one: id={wid} {lang} -> {out_path}")
                        try:
                            _tts_make(text, lang, out_path)
                        except Exception:
                            try:
                                record_tts_request(
                                    c,
                                    user_id,
                                    successful=False,
                                    timezone_name=Config.TTS_USAGE_TIMEZONE,
                                )
                            except Exception:
                                print("[TTS][USAGE] failed to record unsuccessful request", file=sys.stderr)
                                traceback.print_exc()
                            raise
                        else:
                            try:
                                record_tts_request(
                                    c,
                                    user_id,
                                    successful=True,
                                    timezone_name=Config.TTS_USAGE_TIMEZONE,
                                )
                            except Exception:
                                print("[TTS][USAGE] failed to record successful request", file=sys.stderr)
                                traceback.print_exc()
                        # >>> Максимизация громкости
                        _maximize_loudness(out_path)
                        out_per_lang[lang] = _audio_url(lang, lesson_slug, fname)
                        generated += 1

                except TtsUsageLimitExceeded as exc:
                    blocked += 1
                    row_errors.append({
                        "lang": lang,
                        "error": "tts_monthly_character_limit_reached",
                        "scope": exc.scope,
                        "limit": exc.limit,
                        "used": exc.used,
                        "requested": exc.requested,
                    })
                    print(
                        f"[TTS][LIMIT] id={wid} lang={lang} "
                        f"scope={exc.scope} used={exc.used} limit={exc.limit}",
                        file=sys.stderr,
                    )
                    out_per_lang[lang] = ""
                except Exception as e:
                    print(f"[TTS][ERROR] id={wid} lang={lang}: {e}", file=sys.stderr)
                    traceback.print_exc()
                    row_errors.append({"lang": lang, "error": str(e)})
                    out_per_lang[lang] = ""

            if user_id:
                set_clause = ", ".join([f"audio_{lang}=?" for lang in langs] + ["updated_at=?"])
                c.execute(
                    f"UPDATE words SET {set_clause} WHERE id=? AND (user_id=? OR status='test')",
                    [out_per_lang.get(lang, "") for lang in langs] + [now_ms, wid, str(user_id)],
                )
            else:
                set_clause = ", ".join([f"audio_{lang}=?" for lang in langs] + ["updated_at=?"])
                c.execute(
                    f"UPDATE words SET {set_clause} WHERE id=?",
                    [out_per_lang.get(lang, "") for lang in langs] + [now_ms, wid],
                )

            items.append({
                "id": wid,
                **out_per_lang,
                "ok": not row_errors,
                "errors": row_errors,
            })

        c.commit()

    return {
        "ok": blocked == 0,
        "items": items,
        "generated": generated,
        "skipped": skipped,
        "blocked": blocked,
        "limit_reached": blocked > 0,
        "error": "tts_monthly_character_limit_reached" if blocked else None,
    }
