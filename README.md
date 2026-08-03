# Learn English & Dutch 🇬🇧🇳🇱

A Telegram-based language learning project that combines a **Telegram bot** and a **Telegram Mini App (Web App)** for studying English and Dutch vocabulary.

The main goal of the project is to provide a fast, simple, and scalable way to practice words, track learning progress, and support **offline-first usage** on mobile devices.

---

## Key Features

- 🤖 Telegram bot for navigation and interaction
- 🌐 Telegram Mini App (Web App) for a rich learning interface
- 📚 Vocabulary-based learning (EN ↔ NL / RU)
- ✅ Progress tracking per word
- ⚡ Fast startup and smooth UX

### Planned / In Progress
- 📦 Offline-first support using IndexedDB
- 🔄 Progress synchronization when internet is available
- 🔊 Audio caching for offline practice
- 🧠 Spaced Repetition System (SRS)

---

## AI Platform usage dashboard

AI Platform reads the existing admin usage endpoints server-to-server. Configure
the same long random secret in both services:

- LearnWords: `AI_PLATFORM_ADMIN_TOKEN`
- AI Platform: `LEARN_WORDS_ADMIN_TOKEN`

AI Platform also accepts `LEARN_WORDS_BASE_URL` (for example the internal
container URL or `https://learn.iovenko.eu`). The service token is limited to
reading usage, changing TTS limits, and resetting TTS/translation counters; it
does not authorize subscription or user-management actions.

## Project Structure

## Codex project knowledge base

The metadata-only Codex index maps files, symbols, Flask/Telegram routes,
SQLite schema ownership, frontend links, Android contracts and production
runtime metadata without storing source code, secrets or user rows.

```bash
python tools/project_kb.py build
python tools/project_kb.py update
python tools/project_kb.py update --files app/routes.py app/static/sync.js
python tools/project_kb.py server-scan --ssh-host root@204.168.186.69 --ssh-key "$HOME/Desktop/id_ed25519"
python tools/project_kb.py compare-environments
python tools/project_kb.py android-api "/api/progress/sync"
```

The generated SQLite file is `.codex/project_kb.sqlite` and is ignored by Git.
Server scanning is an explicit, read-only command; it stores only redacted
runtime/schema metadata and never reads `.env`, production logs or user data.

