# ParallelLingvo public website

This folder contains the static public website for ParallelLingvo. It is separated from the learning application so the public marketing and blog content can be indexed without Telegram authentication or client-side application state.

## Production URLs

- Public website: `https://parallellingvo.app/`
- Learning application: `https://learn.iovenko.eu/`

## Supported website languages

ParallelLingvo is presented in 11 supported learning languages:

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

The canonical locale mapping is stored in `website/locales.json`.

Every localized landing page is server-delivered HTML. The header uses a responsive globe language dropdown rather than eleven separate navigation buttons. Landing-page alternatives use reciprocal `hreflang` metadata and all locale URLs are included in `sitemap.xml`.

## Learning-language positioning

The product is positioned around choosing three or more languages from the supported set and connecting the translations to the same vocabulary concept. Do not describe ParallelLingvo as limited to only EN/NL/RU.

## Blog localization

The current editorial blog and its three existing articles have localized English, Dutch and Russian versions:

- `/blog/...`
- `/nl/blog/...`
- `/ru/blog/...`

The blog index uses the same global 11-language dropdown. For a language whose blog translation does not exist yet, the dropdown returns the visitor to that language's localized product landing page rather than linking to a nonexistent article.

Additional blog translations can be added independently. Do not publish hreflang URLs for article translations that do not yet exist.

## AI/search discoverability

The site includes:

- semantic server-delivered HTML
- separate crawlable landing URLs for all 11 languages
- Schema.org JSON-LD with language metadata
- canonical URLs and hreflang alternatives
- `robots.txt` for search and AI crawlers
- multilingual `sitemap.xml`
- `feed.xml`
- `/llms.txt`
- `/llms-full.txt`
- favicon and ParallelLingvo brand assets

## Deployment

The static site runs as an isolated Nginx container on the same external Docker network as the existing application.

Start it with:

```bash
docker compose -f docker-compose.website.yml up -d
```

Production reverse-proxy configuration:

```text
nginx/parallellingvo.conf
```

It serves:

```text
parallellingvo.app
www.parallellingvo.app
```

`www.parallellingvo.app` redirects to `https://parallellingvo.app`.

The existing learning application at `learn.iovenko.eu` must remain untouched.

## Checks after deployment

```bash
curl -I https://parallellingvo.app/
curl -I https://parallellingvo.app/nl/
curl -I https://parallellingvo.app/ru/
curl -I https://parallellingvo.app/de/
curl -I https://parallellingvo.app/fr/
curl -I https://parallellingvo.app/es/
curl -I https://parallellingvo.app/it/
curl -I https://parallellingvo.app/pt/
curl -I https://parallellingvo.app/pl/
curl -I https://parallellingvo.app/zh/
curl -I https://parallellingvo.app/ja/
curl -A "OAI-SearchBot" -I https://parallellingvo.app/
curl -A "Claude-SearchBot" -I https://parallellingvo.app/
curl -A "PerplexityBot" -I https://parallellingvo.app/
curl https://parallellingvo.app/robots.txt
curl https://parallellingvo.app/llms.txt
curl https://parallellingvo.app/sitemap.xml
```

All public pages should return HTTP 200 without login, CAPTCHA or JavaScript challenges.

## Content workflow

For every new marketing page:

1. Add localized HTML under the appropriate locale URL.
2. Keep the 11-language dropdown consistent.
3. Add reciprocal landing-page `hreflang` links.
4. Add the localized URL to `sitemap.xml`.
5. Keep visible content and Schema.org language metadata consistent.
6. Update `llms.txt` when the page is important for product discovery.

For blog content, only add a locale to hreflang when that translated article actually exists.
