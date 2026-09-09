# ParallelLingvo public website

This folder contains the static public website for ParallelLingvo. It is separated from the learning application so marketing and blog content can be indexed without Telegram authentication or client-side state.

## Production URLs

- Public website: `https://parallellingvo.app/`
- Learning application: `https://app.parallellingvo.app/`
- Legacy application hostname: `https://learn.iovenko.eu/` (redirect only after migration)

## Learning languages vs website languages

ParallelLingvo has an initial **45-language learning catalog** defined in `app/languages.py`. The application stores language forms in normalized `word_translations` rows, so new learning languages can be added later without changing the `words` table schema.

The public website interface is currently localized in 11 languages:

- English (`en`) — `/`
- Nederlands (`nl`) — `/nl/`
- Русский (`ru`) — `/ru/`
- Deutsch (`de`) — `/de/`
- Français (`fr`) — `/fr/`
- Español (`es`) — `/es/`
- Italiano (`it`) — `/it/`
- Português (`pt`) — `/pt/`
- Polski (`pl`) — `/pl/`
- 中文（普通话） (`zh`) — `/zh/`
- 日本語 (`ja`) — `/ja/`

`website/locales.json` records both the website locale set and the 45 learning-language codes.

## Product positioning

- 45 learning languages at launch.
- Users choose at least 3 languages to learn in parallel.
- One vocabulary concept can contain translations in any number of selected languages.
- Do not describe ParallelLingvo as limited to EN/NL/RU or to the current number of website translations.

## Blog localization

The current editorial blog and its three existing articles have English, Dutch and Russian versions. Only publish hreflang URLs for translations that actually exist.

## AI/search discoverability

The site includes semantic server-delivered HTML, Schema.org JSON-LD, canonical URLs, hreflang, `robots.txt`, `sitemap.xml`, `feed.xml`, `llms.txt`, `llms-full.txt`, favicon and brand assets.

## Authentication handoff

The public website remains static. Login buttons use these paths:

- `/auth/google`
- `/auth/telegram`

The production nginx vhost redirects those paths to the corresponding routes on `https://app.parallellingvo.app`.

Direct application links should use:

```text
https://app.parallellingvo.app/
```

## Deployment

```bash
docker compose -f docker-compose.website.yml up -d
```

Production reverse proxy: `nginx/parallellingvo.conf`.

`www.parallellingvo.app` redirects to `https://parallellingvo.app`. The old `learn.iovenko.eu` hostname is retained only as a migration redirect to the new app hostname.

## Backend multilingual API

- `GET /api/languages`
- `GET /api/user_languages`
- `PUT /api/user_languages`
- `GET /api/words/<word_id>/translations`
- `PUT /api/words/<word_id>/translations`

Legacy NL/EN/RU columns remain during migration for backward compatibility.
