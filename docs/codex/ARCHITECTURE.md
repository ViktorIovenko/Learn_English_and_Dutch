# Architecture

## Runtime and request paths

```text
systemd/docker runtime -> learn-words container -> python run.py
                                              |-> Flask :7001
                                              `-> Telegram polling
Nginx learn.iovenko.eu -> http://learn-words:7001 -> Flask blueprint
Telegram Mini App/Web -> templates + JS -> Flask JSON API -> /app/words.db
Android -> Retrofit -> same Flask JSON API -> /app/words.db
```

Production is Docker Compose under `/opt/learn-words`; shared Nginx config is mounted from `/opt/proxy/nginx/conf.d`. Persistent paths are `/opt/learn-words/data/words.db`, `/opt/learn-words/data/audio` and `/opt/learn-words/data/bot_persistence.pkl`. Do not read/copy their contents.

## Data flows

- Telegram: handlers registered from `bot/*`; registration/user navigation writes SQLite through bot DB helpers. Reminder jobs read user/reminder metadata and update `reminder_state`.
- Mini App: Flask renders `app/templates`; shared `base.html` establishes auth/API helpers; page scripts call routes in `app/routes.py`.
- Offline-first: `idb.js` owns IndexedDB stores; `sync.js` queues progress in outbox, POSTs to `/api/progress/sync`, then requests `/api/sync/updates` and applies deltas. `sw.js` caches the application shell; `audio_worker.js` coordinates audio work.
- Android auth: `ApiClient.kt` sends `X-User-Id`, `X-Client: android`, and device language; login endpoints establish/return the user contract. Retrofit declarations and matching backend handlers are in `ANDROID_API.md`.
- Imports: Telegram documents → `bot/upload.py`; browser upload/generation → `app/static/upload.js`; Android upload → repository/Retrofit. Backend validation/persistence ends in `words`.
- Audio: `/api/audio/ensure` and `app/audio_gen.py` generate/reuse files; production audio is a bind-mounted directory, not indexed.
- Nginx terminates public HTTP(S) and proxies `/` to the container. Docker, not a host Flask systemd unit, is the observed application runtime.
