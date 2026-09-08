# ParallelLingvo public website

This folder contains the static public website for ParallelLingvo. It is separated from the learning application so the public marketing and blog content can be indexed without Telegram authentication or client-side application state.

## Production URLs

- Public website: `https://parallellingvo.app/`
- Learning application: `https://learn.iovenko.eu/`

## Supported languages

The current application data model supports three vocabulary languages, and the public website mirrors the same set:

- English (`en`) — `/`
- Nederlands (`nl`) — `/nl/`
- Русский (`ru`) — `/ru/`

The canonical locale mapping is also documented in `website/locales.json`.

Every localized page is server-delivered HTML. Language alternatives use `hreflang`, and the multilingual URLs are included in `sitemap.xml`.

## Blog localization

Each blog article has English, Dutch and Russian HTML versions:

- `/blog/...`
- `/nl/blog/...`
- `/ru/blog/...`

When adding a new public article, create all three language versions and add their hreflang relationships to the page and sitemap.

## AI/search discoverability

The site includes:

- semantic server-delivered HTML
- separate crawlable URLs for EN/NL/RU
- Schema.org JSON-LD
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
curl -I https://parallellingvo.app/blog/
curl -I https://parallellingvo.app/nl/blog/
curl -I https://parallellingvo.app/ru/blog/
curl -A "OAI-SearchBot" -I https://parallellingvo.app/
curl -A "Claude-SearchBot" -I https://parallellingvo.app/
curl -A "PerplexityBot" -I https://parallellingvo.app/
curl https://parallellingvo.app/robots.txt
curl https://parallellingvo.app/llms.txt
curl https://parallellingvo.app/sitemap.xml
```

All public pages should return HTTP 200 without login, CAPTCHA or JavaScript challenges.

## Content workflow

For every new marketing page or blog article:

1. Create the English version.
2. Create the Dutch version under `/nl/`.
3. Create the Russian version under `/ru/`.
4. Add reciprocal `hreflang` links to all versions.
5. Add all localized URLs to `sitemap.xml`.
6. Keep visible content and Schema.org language metadata consistent.
7. Update `llms.txt` when the page is important for product discovery.
