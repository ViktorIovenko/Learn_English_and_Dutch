# Project map

## Components and entrypoints

- `run.py`: process entrypoint; initializes SQLite, creates Flask app/thread and runs one Telegram polling loop.
- `app/routes.py`: Flask blueprint, pages, JSON API, sync, sharing, family, subscriptions, admin and audio orchestration.
- `bot/auth.py`, `bot/onboarding.py`, `bot/upload.py`, `bot/reminder.py`: Telegram registration/navigation, first-run locale, imports and reminders.
- `app/templates/` + `app/static/`: Telegram Mini App/Web UI, IndexedDB, outbox/delta sync, Service Worker and audio worker.
- `android/app/`: native Android client; Retrofit API, DTOs, Room cache/outbox, repositories, UI and alarm-based child reminder.
- `db_init.py`, `run.py`, `app/routes.py`, `app/models.py`, `bot/db.py` and feature modules: distributed SQLite definitions/migrations.

## Main flows

- Telegram update → registered handler under `bot/` → SQLite → message/WebApp link.
- Browser/Telegram Mini App → Flask route → SQLite and/or static assets → JSON/HTML.
- IndexedDB action → outbox → `/api/progress/sync` → `progress_events`; `/api/sync/updates` returns deltas.
- Android UI → `AppRepository` → Retrofit `ApiService` → Flask API → SQLite; Room provides offline cache/queue.
- Imports enter through `bot/upload.py` or `app/static/upload.js`/Android → `app/routes.py` → `words`; audio generation writes under mounted static audio storage.

## Environments

- Local source of truth: this Git checkout, including current uncommitted files.
- Production runtime: `/opt/learn-words`, Docker service `learn-words-learn-words-1`, SQLite bind mount and shared proxy Nginx.
- Exact API/table/Android catalogs are generated in the adjacent documents and `project_manifest.json`.
