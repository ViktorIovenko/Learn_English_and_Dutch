# Task routing

| Task | Read first | Then if needed | Usually skip |
|---|---|---|---|
| Telegram registration | `bot/auth.py`, `bot/onboarding.py`, `config.py` | `run.py`, `bot/db.py`, `users` | frontend |
| Word import | `bot/upload.py`, `app/static/upload.js` | `app/routes.py`, Android `ApiService.kt` | reminders |
| Learning | `app/static/learn.js`, `app/templates/learn.html` | `app/routes.py`, `app/models.py` | systemd/Nginx |
| Offline sync | `app/static/sync.js`, `app/static/idb.js` | sync handlers, Android repository | reminders |
| Android API | `ANDROID_API.md`, `ApiService.kt` | DTO, Flask handler, tables | unrelated templates |
| Difficult words | `app/static/difficult.js` | `app/routes.py`, Android difficult UI | reminders |
| Audio | `app/audio_gen.py`, `audio_worker.js` | Android audio/cache, `config.py` | bot auth |
| Reminders | `bot/reminder.py` | `run.py`, runtime service | frontend |
| Database change | `DATABASE.md` | every table owner/consumer | unrelated JS |
| Family accounts | `app/account_types.py`, `app/family_pairing.py` | family routes, Android parent UI, bot onboarding | audio |
| Subscription/admin | relevant `app/routes.py` handler | Android DTO/UI, usage modules | learning UI |
| Production error | `DEPLOYMENT.md`, `PRODUCTION_SNAPSHOT.md` | target service logs, Nginx, handler | whole repo |
| Deployment | `DEPLOYMENT.md`, root `AGENTS.md` | changed files and focused tests | unrelated modules |

Canonical machine routing lives in SQLite table `task_routes`; use `python tools/project_kb.py files-for "<task>"` first.
