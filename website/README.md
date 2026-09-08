# LearnWord public website

This folder contains the static public website for LearnWord. It is intentionally separated from the Telegram Mini App so the public site can be indexed without Telegram authentication or client-side application state.

## Public URLs

- Marketing website: `https://learnword.iovenko.eu/`
- Learning application: `https://learn.iovenko.eu/`

## AI/search discoverability

The site includes:

- semantic server-delivered HTML
- visible product and educational text
- Schema.org JSON-LD (`WebSite`, `SoftwareApplication`, `FAQPage`, `Article`, `Blog`)
- canonical URLs
- `robots.txt` that intentionally allows major search and AI crawlers
- `sitemap.xml`
- `feed.xml`
- `/llms.txt`
- `/llms-full.txt`
- Markdown alternatives for important pages using `rel="alternate" type="text/markdown"`
- `rel="describedby"` links to `/llms.txt`

## Deployment

The site runs as an isolated Nginx container on the same external Docker network as the existing application.

Start it with:

```bash
docker compose -f docker-compose.website.yml up -d
```

The reverse-proxy configuration is in:

```text
nginx/learnword.conf
```

Before enabling the HTTPS server block:

1. Create DNS for `learnword.iovenko.eu` pointing to the server.
2. Issue a Let's Encrypt certificate for `learnword.iovenko.eu`.
3. Start the `learnword-site` container.
4. Enable `nginx/learnword.conf` in the main reverse proxy and reload Nginx.

## Crawler checks after deployment

```bash
curl -I https://learnword.iovenko.eu/
curl -A "OAI-SearchBot" -I https://learnword.iovenko.eu/
curl -A "Claude-SearchBot" -I https://learnword.iovenko.eu/
curl -A "PerplexityBot" -I https://learnword.iovenko.eu/
curl https://learnword.iovenko.eu/robots.txt
curl https://learnword.iovenko.eu/llms.txt
curl https://learnword.iovenko.eu/sitemap.xml
```

All public pages should return HTTP 200 without login, JavaScript challenges or CAPTCHA.

## Cloudflare / WAF

If the domain is behind Cloudflare or another WAF, make sure verified search and AI crawlers are not challenged or blocked. A valid `robots.txt` alone is not enough if the WAF returns 403 or presents a JavaScript challenge.

## Content workflow

For each new blog article:

1. Add a crawlable HTML page under `website/blog/<slug>/index.html`.
2. Add a concise Markdown version at `website/blog/<slug>/index.md`.
3. Add the article to `website/blog/index.html` and `website/blog/index.md`.
4. Add the URL to `website/sitemap.xml`.
5. Add it to `website/feed.xml`.
6. Add high-value evergreen articles to `website/llms.txt`.
7. Keep structured data consistent with the visible article content.
