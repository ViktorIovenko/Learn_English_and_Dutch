"""Canonical content, missing-only provider calls and per-user lesson records.

User words/progress keep their existing IDs. The catalog contains immutable
variants, never user IDs or lesson names. Supplied values always win.
"""
from contextlib import closing
import hashlib
import json
import time
import unicodedata

from config import Config
from app.content_db import connect, transaction
from app.content_providers import LANGUAGES, adapter, language_code


def normalized(value):
    return " ".join(unicodedata.normalize("NFC", str(value or "")).split()).casefold()


def clean(value):
    return unicodedata.normalize("NFC", str(value or "")).strip()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _valid(value):
    return bool(clean(value)) and normalized(value) not in {"null", "none", "undefined", "nan", "n/a", "-", "?", "...", "todo", "tbd", "[object object]"}


def ensure_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS content_migrations(name TEXT PRIMARY KEY, completed_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS content_variants(
            id INTEGER PRIMARY KEY, fingerprint TEXT NOT NULL UNIQUE,
            sense TEXT NOT NULL, context TEXT NOT NULL, words_json TEXT NOT NULL,
            source TEXT NOT NULL, created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS content_terms(
            variant_id INTEGER NOT NULL REFERENCES content_variants(id), language TEXT NOT NULL,
            text_key TEXT NOT NULL, PRIMARY KEY(variant_id,language));
        CREATE INDEX IF NOT EXISTS idx_content_terms_lookup ON content_terms(language,text_key);
        CREATE TABLE IF NOT EXISTS content_translations(
            fingerprint TEXT PRIMARY KEY, source_language TEXT NOT NULL, source_key TEXT NOT NULL,
            target_language TEXT NOT NULL, target_text TEXT NOT NULL,
            sense TEXT NOT NULL, context TEXT NOT NULL, source TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS content_examples(
            fingerprint TEXT PRIMARY KEY, variant_id INTEGER NOT NULL REFERENCES content_variants(id),
            level TEXT NOT NULL, examples_json TEXT NOT NULL, source TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_content_examples_variant ON content_examples(variant_id,level);
        CREATE TABLE IF NOT EXISTS content_results(
            request_key TEXT PRIMARY KEY, operation TEXT NOT NULL, result_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS content_pending(
            request_key TEXT PRIMARY KEY, operation TEXT NOT NULL, request_json TEXT NOT NULL,
            created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS content_import_requests(
            user_id TEXT NOT NULL, request_key TEXT NOT NULL, request_hash TEXT NOT NULL,
            response_json TEXT NOT NULL, PRIMARY KEY(user_id,request_key));
    """)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(words)")}
    if not columns:
        return
    for column in ("content_sense", "content_context", "example_level"):
        if column not in columns:
            conn.execute(f"ALTER TABLE words ADD COLUMN {column} TEXT NOT NULL DEFAULT ''")
    if not conn.execute("SELECT 1 FROM content_migrations WHERE name='legacy_words_v1'").fetchone():
        # Additive, streaming backfill; never delete or renumber user records.
        cursor = conn.execute("SELECT * FROM words ORDER BY id")
        while True:
            batch = cursor.fetchmany(250)
            if not batch:
                break
            for row in batch:
                remember(conn, dict(row), source="legacy")
        conn.execute("INSERT INTO content_migrations VALUES('legacy_words_v1',?)", (int(time.time()),))


def remember(conn, item, source="import"):
    words = {lang: clean(item.get(lang)) for lang in LANGUAGES if _valid(item.get(lang))}
    if not words:
        return
    sense = normalized(item.get("sense") or item.get("content_sense"))
    context = normalized(item.get("context") or item.get("content_context"))
    identity = {"words": {lang: normalized(text) for lang, text in words.items()}, "sense": sense, "context": context}
    fingerprint = digest(identity)
    conn.execute("INSERT OR IGNORE INTO content_variants(fingerprint,sense,context,words_json,source,created_at) VALUES(?,?,?,?,?,?)",
                 (fingerprint, sense, context, canonical(words), source, int(time.time())))
    variant_id = conn.execute("SELECT id FROM content_variants WHERE fingerprint=?", (fingerprint,)).fetchone()[0]
    for lang, text in words.items():
        conn.execute("INSERT OR IGNORE INTO content_terms VALUES(?,?,?)", (variant_id, lang, normalized(text)))
        for target, translated in words.items():
            if target == lang:
                continue
            key = digest([lang, normalized(text), target, normalized(translated), sense, context])
            conn.execute("INSERT OR IGNORE INTO content_translations VALUES(?,?,?,?,?,?,?,?)",
                         (key, lang, normalized(text), target, translated, sense, context, source))
    examples = {f"ex_{lang}": clean(item.get(f"ex_{lang}")) for lang in words if _valid(item.get(f"ex_{lang}"))}
    if examples:
        level = clean(item.get("level") or item.get("example_level")).upper()
        key = digest([fingerprint, level, examples])
        conn.execute("INSERT OR IGNORE INTO content_examples VALUES(?,?,?,?,?)", (key, variant_id, level, canonical(examples), source))
        # Exact sentence translation is a different cache from word translation.
        for src in words:
            if f"ex_{src}" not in examples:
                continue
            for target in words:
                if src == target or f"ex_{target}" not in examples:
                    continue
                request = {"text": examples[f"ex_{src}"], "source_language": src, "target_language": target, "sense": sense, "context": context}
                _store_result(conn, "translate_sentence", request, {"text": examples[f"ex_{target}"]})


def _store_result(conn, operation, request, result):
    result = {key: value for key, value in result.items() if key != "_usage"}
    key = digest([operation, request])
    existing = conn.execute("SELECT result_json FROM content_results WHERE request_key=?", (key,)).fetchone()
    if existing and json.loads(existing[0]) != result:
        # Conflicting translations are retained as an ambiguous result; never
        # silently select the first sentence translation.
        result = {"ambiguous": True}
    conn.execute("INSERT INTO content_results VALUES(?,?,?) ON CONFLICT(request_key) DO UPDATE SET result_json=excluded.result_json",
                 (key, operation, canonical(result)))
    conn.execute("DELETE FROM content_pending WHERE request_key=?", (key,))


def _request(conn, operation, request, allow_provider=True):
    key = digest([operation, request])
    row = conn.execute("SELECT result_json FROM content_results WHERE request_key=?", (key,)).fetchone()
    if row:
        return json.loads(row[0]), 0
    provider = adapter(operation) if allow_provider else None
    if provider:
        result = provider(**request, request_key=key)
        if not isinstance(result, dict):
            raise ValueError("provider must return an object")
        valid = (_valid(result.get("text")) if operation in ("translate_word", "translate_sentence")
                 else any(_valid(result.get(f"ex_{lang}")) for lang in LANGUAGES) if operation == "generate_examples"
                 else isinstance(result.get("words"), list) and bool(result["words"]))
        if not valid:
            conn.execute("INSERT OR IGNORE INTO content_pending VALUES(?,?,?,?)", (key, operation, canonical(request), int(time.time())))
            return result, 1
        _store_result(conn, operation, request, result)
        return result, 1
    conn.execute("INSERT OR IGNORE INTO content_pending VALUES(?,?,?,?)", (key, operation, canonical(request), int(time.time())))
    return {}, 0


def reuse(conn, item, languages=None):
    result = dict(item)
    words = {lang: clean(item.get(lang)) for lang in LANGUAGES if _valid(item.get(lang))}
    if not words:
        return result, []
    sense = normalized(item.get("sense") or item.get("content_sense"))
    context = normalized(item.get("context") or item.get("content_context"))
    candidates = {}
    for lang, text in words.items():
        for row in conn.execute("SELECT v.* FROM content_terms t JOIN content_variants v ON v.id=t.variant_id WHERE t.language=? AND t.text_key=? AND v.sense=? AND v.context=?",
                                (lang, normalized(text), sense, context)):
            candidate = json.loads(row["words_json"])
            if all(lang not in candidate or normalized(candidate[lang]) == normalized(text) for lang, text in words.items()):
                candidates[row["id"]] = (dict(row), candidate)
    supplied_examples = {key: clean(value) for key, value in item.items() if key.startswith("ex_") and _valid(value)}
    if supplied_examples:
        matching = {}
        for variant_id, pair in candidates.items():
            if len(pair[1]) < 2:
                continue
            for row in conn.execute("SELECT examples_json FROM content_examples WHERE variant_id=?", (variant_id,)):
                bundle = json.loads(row[0])
                if all(bundle.get(key) == text for key, text in supplied_examples.items()):
                    matching[variant_id] = pair
        if matching:
            candidates = matching
    ambiguous = []
    for lang in languages or LANGUAGES:
        if _valid(result.get(lang)):
            continue
        values = {normalized(data[lang]): data[lang] for _, data in candidates.values() if data.get(lang)}
        if len(values) == 1:
            result[lang] = next(iter(values.values()))
        elif len(values) > 1:
            ambiguous.append(lang)
    # Reuse one aligned example bundle, never mix unrelated source sentences.
    level = clean(item.get("level") or item.get("example_level")).upper()
    bundles = []
    for row, data in candidates.values():
        if any(_valid(result.get(lang)) and normalized(result[lang]) != normalized(text) for lang, text in data.items()):
            continue
        for example in conn.execute("SELECT * FROM content_examples WHERE variant_id=? AND (?='' OR level=?)", (row["id"], level, level)):
            bundle = json.loads(example["examples_json"])
            supplied = {key: clean(value) for key, value in item.items() if key.startswith("ex_") and _valid(value)}
            if all(key in bundle and clean(bundle[key]) == value for key, value in supplied.items()):
                bundles.append((example["fingerprint"], bundle))
    if bundles and not ambiguous:
        _, bundle = sorted(bundles, key=lambda pair: (-len(pair[1]), pair[0]))[0]
        for key, text in bundle.items():
            if not _valid(result.get(key)):
                result[key] = text
    return result, ambiguous


def resolve(conn, item, languages=None, examples=True, allow_provider=False, source="import"):
    languages = list(dict.fromkeys(language_code(lang) for lang in (languages or LANGUAGES)))
    remember(conn, item, source)
    result, ambiguous = reuse(conn, item, languages)
    calls = 0
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    source_lang = language_code(item.get("source_language")) if item.get("source_language") else next((lang for lang in LANGUAGES if _valid(result.get(lang))), None)
    if not source_lang:
        raise ValueError("at least one word language is required")
    missing_words = [lang for lang in languages if not _valid(result.get(lang))]
    for lang in missing_words:
        if lang in ambiguous:
            continue  # A caller must disambiguate by sense/context/known translation.
        request = {"text": result[source_lang], "source_language": source_lang, "target_language": lang,
                   "sense": normalized(item.get("sense") or item.get("content_sense")),
                   "context": normalized(item.get("context") or item.get("content_context"))}
        generated, count = _request(conn, "translate_word", request, allow_provider)
        calls += count
        for key in usage:
            usage[key] += max(0, int((generated.get("_usage") or {}).get(key, 0))) if count else 0
        if _valid(generated.get("text")):
            result[lang] = clean(generated["text"])
    remember(conn, result, source)
    result, _ = reuse(conn, result, languages)
    missing_examples = [lang for lang in languages if _valid(result.get(lang)) and not _valid(result.get(f"ex_{lang}"))] if examples else []
    if missing_examples and not ambiguous:
        # The adapter sees only missing languages, and receives any existing
        # aligned sentences so it can translate rather than replace them.
        request = {"words": {lang: result[lang] for lang in languages if _valid(result.get(lang))},
                   "languages": missing_examples, "examples": {lang: result[f"ex_{lang}"] for lang in languages if _valid(result.get(f"ex_{lang}"))},
                   "level": clean(item.get("level") or item.get("example_level")).upper(),
                   "sense": normalized(item.get("sense") or item.get("content_sense")),
                   "context": normalized(item.get("context") or item.get("content_context"))}
        generated, count = _request(conn, "generate_examples", request, allow_provider)
        calls += count
        for key in usage:
            usage[key] += max(0, int((generated.get("_usage") or {}).get(key, 0))) if count else 0
        for lang in missing_examples:
            if _valid(generated.get(f"ex_{lang}")) and _valid(result.get(lang)):
                result[f"ex_{lang}"] = clean(generated[f"ex_{lang}"])
    remember(conn, result, source)
    missing = [lang for lang in languages if not _valid(result.get(lang))]
    if examples:
        missing += [f"ex_{lang}" for lang in languages if not _valid(result.get(f"ex_{lang}"))]
    return {**result, "missing_fields": missing, "ambiguous_languages": ambiguous, "provider_calls": calls, "usage": usage,
            "content_status": "ambiguous" if ambiguous else "pending" if missing else "complete"}


def resolve_word(word, source_language, languages=("nl", "en", "ru"), level="", supplied=None, sense="", context="", examples=True, allow_provider=True):
    source_language = language_code(source_language)
    if not _valid(word) or len(clean(word)) > 500:
        raise ValueError("a word of at most 500 characters is required")
    item = dict(supplied or {})
    item.update({source_language: clean(word), "source_language": source_language, "level": level, "sense": sense, "context": context})
    with transaction(Config.DB_PATH) as conn:
        ensure_schema(conn)
        return resolve(conn, item, languages, examples, allow_provider)


def translate_language(source_word, source_sentence, source_language, target_language, supplied=None, sense="", context="", allow_provider=True):
    src, target = language_code(source_language), language_code(target_language)
    if not _valid(source_word) or len(clean(source_word)) > 500 or len(clean(source_sentence)) > 1000:
        raise ValueError("word or sentence is too long or empty")
    item = {src: clean(source_word), "source_language": src, "sense": sense, "context": context, **(supplied or {})}
    if source_sentence:
        item[f"ex_{src}"] = clean(source_sentence)
    with transaction(Config.DB_PATH) as conn:
        ensure_schema(conn)
        result = resolve(conn, item, [src, target], examples=False, allow_provider=allow_provider)
        sentence = clean(item.get(f"ex_{target}"))
        if source_sentence and not sentence:
            request = {"text": clean(source_sentence), "source_language": src, "target_language": target, "sense": normalized(sense), "context": normalized(context)}
            generated, calls = _request(conn, "translate_sentence", request, allow_provider)
            sentence = clean(generated.get("text"))
            result["provider_calls"] += calls
            for key in result["usage"]:
                result["usage"][key] += max(0, int((generated.get("_usage") or {}).get(key, 0))) if calls else 0
            if sentence:
                remember(conn, {**result, f"ex_{src}": source_sentence, f"ex_{target}": sentence}, "translation")
        missing = ([] if result.get(target) else ["word"]) + (["sentence"] if source_sentence and not sentence else [])
        return {"word": result.get(target, ""), "sentence": sentence, "missing_fields": missing,
                "provider_calls": result["provider_calls"], "usage": result["usage"], "content_status": "pending" if missing else "complete"}


def import_words(db_path, user_id, lessons, *, source="import", idempotency_key=None, allow_provider=True):
    if not str(user_id or ""):
        raise ValueError("user_id is required")
    if not isinstance(lessons, list) or not lessons:
        raise ValueError("lessons must be a non-empty list")
    if idempotency_key is not None and (not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 128):
        raise ValueError("idempotency_key must contain 1 to 128 characters")
    request_hash = digest(lessons)
    with transaction(db_path) as conn:
        ensure_schema(conn)
        if idempotency_key:
            receipt = conn.execute("SELECT * FROM content_import_requests WHERE user_id=? AND request_key=?", (str(user_id), idempotency_key)).fetchone()
            if receipt:
                if receipt["request_hash"] != request_hash:
                    raise ValueError("idempotency_conflict")
                return json.loads(receipt["response_json"])
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(words)")}
        for lang in LANGUAGES:
            for field in (lang, f"ex_{lang}", f"audio_{lang}"):
                if field not in columns:
                    conn.execute(f'ALTER TABLE words ADD COLUMN "{field}" TEXT')
        if "updated_at" not in columns:
            conn.execute("ALTER TABLE words ADD COLUMN updated_at INTEGER")
        if "status" not in columns:
            conn.execute("ALTER TABLE words ADD COLUMN status TEXT NOT NULL DEFAULT 'user'")
        row = conn.execute("SELECT MAX(CAST(substr(number,1,instr(number||'.','.')-1) AS INTEGER)) FROM words WHERE user_id=?", (str(user_id),)).fetchone()
        next_lesson = int(row[0] or 0) + 1
        imported, ids, pending = 0, [], []
        for lesson in lessons:
            title = clean(lesson.get("lesson") or lesson.get("title")) if isinstance(lesson, dict) else ""
            items = lesson.get("words") if isinstance(lesson, dict) else None
            if not title or len(title) > 200 or not isinstance(items, list) or not items:
                raise ValueError("a lesson title and words are required")
            existing = conn.execute("SELECT number FROM words WHERE user_id=? AND lesson=?", (str(user_id), title)).fetchall()
            numbers = [str(row[0] or "").split(".", 1) for row in existing]
            prefixes = [int(parts[0]) for parts in numbers if parts[0].isdigit() and int(parts[0]) > 0]
            lesson_number = min(prefixes) if prefixes else next_lesson
            word_offset = max([len(existing), *[int(parts[1]) for parts in numbers if len(parts) == 2 and parts[1].isdigit()]])
            if not prefixes:
                next_lesson += 1
            preferred = []
            target_users = [str(user_id)]
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='family_lesson_assignments'").fetchone():
                assignment_columns = {row["name"] for row in conn.execute("PRAGMA table_info(family_lesson_assignments)")}
                active = " AND archived_at IS NULL" if "archived_at" in assignment_columns else ""
                target_users += [row[0] for row in conn.execute("SELECT child_user_id FROM family_lesson_assignments WHERE parent_user_id=? AND lesson=?" + active, (str(user_id), title))]
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_language_preferences'").fetchone():
                for target_user in target_users:
                    preferred += [row[0] for row in conn.execute("SELECT lang_code FROM user_language_preferences WHERE user_id=? ORDER BY priority", (target_user,))]
            for index, item in enumerate(items, 1):
                if not isinstance(item, dict) or not any(_valid(item.get(lang)) for lang in LANGUAGES):
                    raise ValueError("at least one word language is required")
                if len(clean(item.get("sense") or item.get("content_sense"))) > 200 or len(clean(item.get("context") or item.get("content_context"))) > 1000 or len(clean(item.get("level") or item.get("example_level"))) > 10:
                    raise ValueError("sense, context or level is too long")
                for lang in LANGUAGES:
                    if len(clean(item.get(lang))) > 500 or len(clean(item.get(f"ex_{lang}"))) > 1000:
                        raise ValueError("word or example is too long")
                requested = list(dict.fromkeys([*(lesson.get("languages") or []), *preferred])) or ["nl", "en", "ru"]
                result = resolve(conn, item, requested, examples=True, allow_provider=allow_provider, source=source)
                fields = ["user_id", "status", "lesson", "number", "content_sense", "content_context", "example_level", "updated_at"]
                values = [str(user_id), "user", title, f"{lesson_number}.{word_offset + index}", normalized(item.get("sense") or item.get("content_sense")), normalized(item.get("context") or item.get("content_context")), clean(item.get("level") or item.get("example_level")).upper(), int(time.time() * 1000)]
                for lang in LANGUAGES:
                    fields.extend([lang, f"ex_{lang}", f"audio_{lang}"])
                    # Existing audio URLs are retained only for exact same text,
                    # validated later by the audio service. Imports cannot forge
                    # a text/audio association from an arbitrary URL.
                    values.extend([clean(result.get(lang)), clean(result.get(f"ex_{lang}")), ""])
                cursor = conn.execute(f"INSERT INTO words({','.join(fields)}) VALUES({','.join('?' for _ in fields)})", values)
                ids.append(cursor.lastrowid)
                if result["missing_fields"]:
                    pending.append({"id": cursor.lastrowid, "missing_fields": result["missing_fields"], "ambiguous_languages": result["ambiguous_languages"]})
                imported += 1
        response = {"ok": True, "count": imported, "imported": imported, "skipped": 0, "ids": ids, "pending": pending}
        if len(lessons) == 1:
            response["lesson"] = clean(lessons[0].get("lesson") or lessons[0].get("title"))
        if idempotency_key:
            conn.execute("INSERT INTO content_import_requests VALUES(?,?,?,?)", (str(user_id), idempotency_key, request_hash, canonical(response)))
        return response


def remember_word_ids(db_path, ids, source="edit"):
    if not ids:
        return
    with transaction(db_path) as conn:
        ensure_schema(conn)
        for row in conn.execute(f"SELECT * FROM words WHERE id IN ({','.join('?' for _ in ids)})", list(ids)):
            remember(conn, dict(row), source)


def prepare_edit(current, updates):
    """Common invalidation policy for Web and MCP; never overwrite examples
    supplied as part of the same edit. Old catalog variants remain reusable.
    """
    result = dict(updates)
    for lang in LANGUAGES:
        if lang in result and clean(current.get(lang)) != clean(result[lang]):
            result[f"audio_{lang}"] = ""
            result.setdefault(f"ex_{lang}", "")
    return result
