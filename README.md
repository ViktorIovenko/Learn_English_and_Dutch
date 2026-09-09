# ParallelLingvo

ParallelLingvo is a multilingual vocabulary-learning platform designed for learning three or more languages in one connected flow.

## Production domains

- Public website and blog: `https://parallellingvo.app/`
- Learning application: `https://app.parallellingvo.app/`
- Legacy application hostname: `https://learn.iovenko.eu/` (redirect only after migration)

## Main components

- Static public website and blog for SEO/AI indexing
- Flask web application and API
- Telegram Mini App
- Telegram bot
- Google OIDC login
- Telegram OIDC login
- SQLite vocabulary/progress storage
- Multilingual translation model that is not limited to fixed language pairs

## Authentication direction

The application is moving away from browser-controlled `?uid=` / `X-User-Id` identity. Production authentication is server-verified and session-based:

- Google OIDC -> ParallelLingvo account -> Flask session
- Telegram OIDC -> ParallelLingvo account -> Flask session
- Telegram Mini App -> verified Telegram `initData` -> existing account

Existing Telegram numeric user IDs are preserved where possible so existing learning data remains attached during migration.

## Deployment

See `docs/APP_DOMAIN_MIGRATION.md` for the app-domain, TLS, Google login, Telegram bot, Telegram OIDC, and migration checklist.

## Project structure

- `app/` — Flask application, API, templates, auth
- `bot/` — Telegram bot
- `website/` — static public website and blog
- `nginx/` — public-site, app-domain, and legacy-domain nginx configs
- `docs/` — deployment and product documentation
- `docker-compose.eu.yml` — application service
- `docker-compose.website.yml` — static public website service
