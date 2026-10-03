# app/audio_gen.py
# [ИЗМЕНЕНО v7.7]
# - Content-addressed audio shared across users and lessons.
# - Генерация ТОЛЬКО для явно переданных id
# - [НОВОЕ] Максимизация громкости: компрессия + пик-нормализация до -0.1 dBFS

from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Iterable
import hashlib
import json
import os
import uuid
import unicodedata
from app.content_db import transaction
from app.content_providers import LANGUAGES, tts_provider
from app.resource_lock import resource_lock
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
    conn = sqlite3.connect(db_path, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def _tts_make(text: str, lang: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tts_provider().synthesize(text,lang,out_path)


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


def _existing_audio_path(url: str) -> Path | None:
    raw=str(url or "").split("?",1)[0].lstrip("/")
    if not raw.startswith("static/audio/"):
        return None
    target=(AUDIO_ROOT/raw[len("static/audio/"):]).resolve()
    if AUDIO_ROOT.resolve() not in target.parents:
        return None
    return target if target.is_file() and target.stat().st_size>500 else None


def _file_hash(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle,"sha256").hexdigest()


def _identity(text,lang):
    parameters=dict(tts_provider().identity)
    parameters["postprocessing"]={key:getattr(Config,key,None) for key in (
        "AUDIO_MAXIMIZE","AUDIO_COMP_THRESHOLD_DBFS","AUDIO_COMP_RATIO",
        "AUDIO_COMP_ATTACK_MS","AUDIO_COMP_RELEASE_MS","AUDIO_PEAK_DBFS","AUDIO_MP3_BITRATE")}
    parameters["processing_version"]="1"
    parameters["text"]=unicodedata.normalize("NFC",text).strip()
    parameters["language"]=lang
    request=json.dumps(parameters,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(request.encode("utf-8")).hexdigest(),request


def _ensure_audio_schema(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS audio_assets(
        cache_key TEXT PRIMARY KEY,request_json TEXT NOT NULL,url TEXT NOT NULL,
        file_hash TEXT NOT NULL,created_at INTEGER NOT NULL,last_used_at INTEGER NOT NULL,
        provenance TEXT NOT NULL DEFAULT 'generated')""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audio_assets_url ON audio_assets(url)")
    conn.execute("CREATE TABLE IF NOT EXISTS audio_legacy_rejections(url TEXT PRIMARY KEY,reason TEXT NOT NULL,created_at INTEGER NOT NULL)")
    columns={row["name"] for row in conn.execute("PRAGMA table_info(words)")}
    for lang in LANGUAGES:
        for col in (lang,f"ex_{lang}",f"audio_{lang}"):
            if col not in columns:
                conn.execute(f'ALTER TABLE words ADD COLUMN "{col}" TEXT')
    if "updated_at" not in columns:
        conn.execute("ALTER TABLE words ADD COLUMN updated_at INTEGER")


def _legacy_path(conn,text,lang):
    # Only associations already stored in the DB may be adopted. Never infer
    # text from truncated filenames. Reject URLs referenced by different texts
    # or languages (old filename collisions cannot be trusted).
    if tts_provider().identity.get("provider") != "gtts":
        return None
    rows=conn.execute(f'SELECT "{lang}","audio_{lang}" FROM words WHERE "{lang}"=? AND "audio_{lang}" IS NOT NULL AND "audio_{lang}"!=?', (text, "")).fetchall()
    urls=[row[f"audio_{lang}"] for row in rows if unicodedata.normalize("NFC",str(row[lang] or "")).strip()==text]
    for url in dict.fromkeys(urls):
        if conn.execute("SELECT 1 FROM audio_legacy_rejections WHERE url=?", (url,)).fetchone():
            continue
        if conn.execute("SELECT 1 FROM audio_assets WHERE url=?", (url,)).fetchone() or str(url).startswith("/static/audio/cache/"):
            continue
        path=_existing_audio_path(url)
        if not path:
            continue
        safe=True
        for code in LANGUAGES:
            references=conn.execute(f'SELECT "{code}" FROM words WHERE "audio_{code}"=?',(url,)).fetchall()
            if any(code!=lang or unicodedata.normalize("NFC",str(row[code] or "")).strip()!=text for row in references):
                safe=False
                break
        if safe:
            return url,path
        conn.execute("INSERT OR IGNORE INTO audio_legacy_rejections VALUES(?,?,?)", (url, "conflicting_text_or_language", int(time.time())))
    return None


def is_cached_audio(db_path,url):
    with closing(_connect(db_path)) as conn:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='audio_assets'").fetchone():
            return False
        return bool(conn.execute("SELECT 1 FROM audio_assets WHERE url=?",(url,)).fetchone())


def ensure_audio_for_ids(db_path,ids,langs,user_id=None):
    ids=list(dict.fromkeys(int(i) for i in (ids or []) if str(i).isdigit()))
    langs=list(dict.fromkeys(str(x).strip().lower() for x in (langs or ["nl","en","ru"]) if str(x).strip().lower() in SUPPORTED_LANGS))
    if not ids or not langs:
        return {"ok":True,"items":[],"generated":0,"skipped":0,"blocked":0}
    with transaction(db_path) as conn:
        _ensure_audio_schema(conn)
    generated=skipped=blocked=0
    items=[]
    for wid in ids:
        output={}; errors=[]
        for lang in langs:
            with closing(_connect(db_path)) as conn:
                where="id=?" + (" AND (user_id=? OR status='test')" if user_id else "")
                params=[wid,str(user_id)] if user_id else [wid]
                row=conn.execute(f'SELECT * FROM words WHERE {where}',params).fetchone()
            if not row:
                continue
            text=unicodedata.normalize("NFC",str(row[lang] or "")).strip()
            if not text:
                output[lang]=""
                continue
            key,request=_identity(text,lang)
            try:
                with resource_lock(AUDIO_ROOT/".locks"/(key+".lock")):
                    with closing(_connect(db_path)) as conn:
                        asset=conn.execute("SELECT * FROM audio_assets WHERE cache_key=?",(key,)).fetchone()
                        path=_existing_audio_path(asset["url"]) if asset else None
                        if path and asset["request_json"]==request and _file_hash(path)==asset["file_hash"]:
                            url=asset["url"]
                            skipped+=1
                        else:
                            # Never adopt an altered managed-cache file as legacy.
                            legacy=_legacy_path(conn,text,lang) if not asset else None
                            if legacy:
                                url,path=legacy
                                skipped+=1
                                provenance="legacy_db_association"
                            else:
                                reserve_tts_characters(conn,user_id,characters=len(text),timezone_name=Config.TTS_USAGE_TIMEZONE)
                                path=AUDIO_ROOT/"cache"/lang/key[:2]/(key+".mp3")
                                path.parent.mkdir(parents=True,exist_ok=True)
                                temporary=path.with_name(key+"."+uuid.uuid4().hex+".tmp.mp3")
                                try:
                                    _tts_make(text,lang,temporary)
                                    _maximize_loudness(temporary)
                                    if not temporary.is_file() or temporary.stat().st_size<=500:
                                        raise RuntimeError("TTS returned an empty or invalid audio file")
                                    os.replace(temporary,path)
                                    record_tts_request(conn,user_id,successful=True,timezone_name=Config.TTS_USAGE_TIMEZONE)
                                except Exception:
                                    record_tts_request(conn,user_id,successful=False,timezone_name=Config.TTS_USAGE_TIMEZONE)
                                    raise
                                finally:
                                    temporary.unlink(missing_ok=True)
                                url="/static/audio/"+path.relative_to(AUDIO_ROOT).as_posix()
                                generated+=1
                                provenance="generated"
                            conn.execute("INSERT INTO audio_assets VALUES(?,?,?,?,?,?,?) ON CONFLICT(cache_key) DO UPDATE SET request_json=excluded.request_json,url=excluded.url,file_hash=excluded.file_hash,last_used_at=excluded.last_used_at,provenance=excluded.provenance",(key,request,url,_file_hash(path),int(time.time()),int(time.time()),provenance))
                        # An edit racing TTS must not attach the old text's audio.
                        updated = conn.execute(f'UPDATE words SET "audio_{lang}"=?,updated_at=? WHERE {where} AND "{lang}"=?',[url,int(time.time()*1000),*params,row[lang]])
                        conn.execute("UPDATE audio_assets SET last_used_at=? WHERE cache_key=?",(int(time.time()),key))
                        conn.commit()
                        output[lang] = url if updated.rowcount else ""
                        if not updated.rowcount:
                            errors.append({"lang": lang, "error": "word_changed_retry"})
            except TtsUsageLimitExceeded as exc:
                blocked+=1
                output[lang]=""
                errors.append({"lang":lang,"error":"tts_monthly_character_limit_reached","scope":exc.scope,"limit":exc.limit,"used":exc.used,"requested":exc.requested})
            except Exception as exc:
                with transaction(db_path) as conn:
                    record_tts_request(conn,user_id,successful=False,timezone_name=Config.TTS_USAGE_TIMEZONE)
                output[lang]=""
                errors.append({"lang":lang,"error":str(exc)})
        if output or errors:
            items.append({"id":wid,**output,"ok":not errors,"errors":errors})
    return {"ok":blocked==0 and all(item["ok"] for item in items),"items":items,"generated":generated,"skipped":skipped,"blocked":blocked,"limit_reached":blocked>0,"error":"tts_monthly_character_limit_reached" if blocked else None}


def cleanup_unused_audio(db_path,older_than_seconds=30*86400):
    """Explicit maintenance only; retain reusable assets by default.
    Check every existing audio language under the generation lock before GC.
    """
    with transaction(db_path) as conn:
        _ensure_audio_schema(conn)
        assets=[dict(row) for row in conn.execute("SELECT * FROM audio_assets WHERE last_used_at<?",(int(time.time())-older_than_seconds,))]
    deleted=0
    for asset in assets:
        with resource_lock(AUDIO_ROOT/".locks"/(asset["cache_key"]+".lock")):
            with transaction(db_path) as conn:
                current=conn.execute("SELECT * FROM audio_assets WHERE cache_key=?",(asset["cache_key"],)).fetchone()
                if not current or current["last_used_at"]>=int(time.time())-older_than_seconds:
                    continue
                where=" OR ".join(f'"audio_{lang}"=?' for lang in LANGUAGES)
                if conn.execute(f"SELECT 1 FROM words WHERE {where} LIMIT 1",[current["url"]]*len(LANGUAGES)).fetchone():
                    continue
                # Another parameter identity may share adopted legacy audio.
                if conn.execute("SELECT 1 FROM audio_assets WHERE url=? AND cache_key!=?",(current["url"],asset["cache_key"])).fetchone():
                    continue
                path=_existing_audio_path(current["url"])
                if path:
                    path.unlink()
                conn.execute("DELETE FROM audio_assets WHERE cache_key=?",(asset["cache_key"],))
                deleted+=1
    return deleted
