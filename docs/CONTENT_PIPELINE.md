# Shared word content pipeline

## Runtime ownership

`app/content_service.py` owns catalog lookup, caller-supplied content, missing
fields, provider dispatch and insertion of user word records. Web and installed
Android clients use `/api/import-words`; Telegram's `bulk_upsert_words` is now a
compatibility entry point into the same importer. MCP uses that importer inside
its existing operation layer. No client must search for duplicates first.

User word IDs, lesson membership, progress, flags and family assignments remain
in their existing tables. Intentional repetitions append new user word records.
The catalog stores no user IDs or lesson names.

## Catalog and meanings

* `content_variants`: immutable sets of aligned language variants, qualified by
  optional `sense` and `context`. Stable fingerprints deduplicate identical sets.
* `content_terms`: indexed language + Unicode-normalized word lookup.
* `content_translations`: unique directional word translation facts.
* `content_examples`: aligned sentence bundles linked to a variant and optional
  declared CEFR level. Sentences from unrelated examples are never mixed.
* `content_results`: exact sentence translations and provider operation results.
* `content_pending`: diagnostic registry of missing operations, not an autonomous
  job queue. A future worker MUST call the resolver again before dispatch, since
  later imports or MCP requests may already have supplied the result.
* `content_import_requests`: per-user import retry receipts.
* `content_migrations`: additive legacy backfill marker.

Existing translations constrain candidate variants. Conflicting candidates are
reported through `ambiguous_languages`; the server does not select the first
translation or pay a provider to guess a meaning. Explicit semantic context
must match; a lesson title is never substituted for semantic context. A matching
supplied sentence can also select an already-known aligned variant. The system
does not infer meanings using semantic AI classification.

Unclassified legacy examples can be reused when no specific CEFR level is
requested. An explicitly requested level requires a matching declared level.
Provided translations/examples always take priority and are published to the
catalog, including from ordinary edits and MCP word fills. Changing a word
invalidates its audio and its example unless a replacement example is supplied
in the same edit. Existing catalog variants remain immutable.

## HTTP contract

Canonical import request:

```json
{
  "lessons": [{"lesson": "Travel", "words": [{"nl": "afstappen", "ru": "слезть"}]}],
  "idempotency_key": "stable-unique-key-for-this-import"
}
```

Response contains `ok`, `imported`, `skipped`, `count` (legacy Web alias), `ids`
and `pending` (word IDs, missing fields, ambiguous languages). A single-lesson
response also contains `lesson`. Deliberate repetitions are imported, not
counted as skipped. Installed Android `{lesson, words}` requests remain accepted;
the updated Android DTO sends the canonical `lessons` contract.

`/api/translate/word` keeps `word`, `from_lang`, `level`, `known_ru` and adds
`supplied`, `languages`, `sense`, `context`, `examples`. Successful resolution can
return partial data with `content_status: pending` and `missing_fields`; it never
pretends that an unconfigured service generated content.

`/api/translate/language` keeps its existing source-word/source-sentence language
fields and adds `supplied`, `sense`, `context`. Word translation and exact
sentence translation use separate tasks/caches. A missing sentence is not
replaced with an unrelated cached example.

`/api/words/<id>` also accepts semantic `sense`, `context`, `level`, stored as
`content_sense`, `content_context`, `example_level`. Existing word readers expose
these metadata when available. No API URL or authentication flow was replaced.

## MCP

`words_add` and `lesson_import_file` accept partial data. Agents supply the
content they already have; the server fills suitable shared data, appends user
records and reports remaining gaps. No preliminary catalog, example or audio
lookup is required. Imported and edited MCP content feeds the same catalog.

`lesson_create_complete` / `lesson_assign_complete` retain their explicit
COMPLETE contract: server reuse/fill happens before validation; incomplete
creation is rolled back. Active child language requirements are determined on
the server, including when any client appends to an already assigned lesson.

MCP creates/progress writes still require an idempotency key. All side effects
and the existing `mcp_idempotency` response receipt commit in one SQLite
transaction. BEGIN IMMEDIATE serializes concurrent deliveries across workers.
Callbacks borrow that connection; legacy helpers cannot commit it prematurely.
Failure rolls back both content/user changes and the receipt. Same key + same
payload returns the stored response; same key + changed payload is a conflict.
A deliberate repeat uses a new key. A client must retain its key across a retry.

## Audio

`audio_assets` stores the full synthesis identity, SHA-256 key, URL, SHA-256 of
the actual file, timestamps and provenance. Identity includes full NFC text,
language, provider/version, voice, synthesis settings and audio processing
settings/version. Cache filenames contain the hash; no lesson directory or
truncated word is used. A change of voice or processing settings gives a new key.

Generation is guarded by an OS file lock, released automatically if a process
exits. Locks work on Windows (msvcrt) and Linux (flock). Output is first written
to a unique temporary MP3, checked, processed, then atomically renamed. Every
reuse validates the identity and file hash. Updating the word concurrently
cannot attach old-text audio to the changed word.

Legacy audio is adopted only via a consistent DB text/language/URL association,
never by filename. URLs shared by conflicting texts/languages are rejected.
`audio_legacy_rejections` retains rejected associations so repairing one user
record cannot make a previously detected legacy collision appear safe again.
Legacy provenance does not prove historic voice settings or the spoken content
of an old MP3; those files have no original synthesis metadata. New files have
an explicit manifest. Managed cache files cannot be adopted under another
voice identity or after integrity validation fails.

Normal word deletion/editing preserves shared cached assets. Cleanup checks
references for all ten supported languages. `cleanup_unused_audio` is an explicit
maintenance operation, not automatically scheduled: it deletes only expired,
unreferenced cache entries under the same generation lock. Default retention is
30 days; ongoing references prevent deletion. Deleting unused cache content may
require a future TTS call if the text is requested again.

The existing gTTS implementation is retained behind the TTS adapter boundary;
no new paid TTS provider/key was selected. Quota and successful/failed-request
accounting remain in the existing usage tables.

## Migration and deployment

Migration only adds catalog/cache tables and the three metadata columns on
`words`. A streaming one-time backfill publishes existing words/examples;
existing rows, IDs, numbers, progress and assignments are untouched. No duplicate
cleanup or user-row deletion is performed. Missing dynamic language/audio
columns are added when needed by the existing storage contract.

Before future deployment, compare production Git state / changed-file hashes,
make a consistent DB backup, and explicitly migrate:

```text
python tools/migrate_content.py --db <actual-runtime-database-path>
```

The command creates an SQLite-consistent `.bak`, migrates transactionally and
checks that the number of user words stayed unchanged. Without explicit
migration, the same additive catalog initialization occurs on the first content
request; for large production databases prefer the explicit maintenance step.
The migration command was not run against production.

Restart only the appropriate backend after deploying Python changes; serve the
updated client assets through the normal project process. Android needs a
separate authorized build/release. This refactor does not deploy or restart.

## Future service adapters

No translation/example service is enabled by default. Configure separate Python
modules through `CONTENT_TRANSLATION_PROVIDER_MODULE`,
`CONTENT_EXAMPLE_PROVIDER_MODULE`, `CONTENT_TOPIC_PROVIDER_MODULE`, and
`CONTENT_TTS_PROVIDER_MODULE`; `CONTENT_PROVIDER_MODULE` is an optional shared
module fallback. Store future keys in server environment/secret configuration,
never in JavaScript, Android or MCP input.

Adapters implement independent keyword-callable operations:

* `translate_word(text, source_language, target_language, sense, context,
  request_key) -> {"text": "..."}`
* `translate_sentence(...) -> {"text": "..."}` with exact source sentence.
* `generate_examples(words, languages, examples, level, sense, context,
  request_key) -> {"ex_nl": "...", ...}` for missing languages only, preserving
  any supplied aligned examples.
* `suggest_words(topic, language, level, count, request_key) -> {"words": [...]}`.
* TTS module exports `provider` with a complete JSON-serializable `identity` and
  `synthesize(text, language, path)`.

Content adapter responses can include `_usage` with prompt/completion/total
tokens. Usage is counted only for provider calls; cache entries never replay
token charges. Empty provider output is not cached as complete content. Transport
timeouts, retries and vendor response parsing belong in the adapter. Forward
`request_key` as provider idempotency key when supported: a local transaction
cannot alone guarantee exactly-once billing if a process dies after a remote
service accepts a request but before its response is persisted.

Resolution currently serializes catalog writes/provider fill under a SQLite
write transaction for correctness. Adapters should use bounded timeouts; before
high-volume production traffic, measure contention with the chosen service.

## Verification boundaries

Profile tests use temporary databases and mocked providers/TTS. They cover
cross-user/lesson reuse, MCP partial and complete contracts, retry/concurrency,
rollback, translation ambiguity, exact sentence reuse, provider-call counts,
legacy row preservation, audio identity/integrity, parallel generation and GC
references in non-baseline languages. No browser, local server, real paid API,
production runtime, Linux deployment or Android build was exercised.
