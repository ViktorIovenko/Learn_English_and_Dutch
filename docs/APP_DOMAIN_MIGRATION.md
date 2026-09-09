# ParallelLingvo app-domain and authentication migration

This document is the deployment/agent handoff for moving the learning application from
`learn.iovenko.eu` to `app.parallellingvo.app` and enabling website login.

## Target architecture

- `https://parallellingvo.app/` — static public website, blog, SEO/AI pages.
- `https://app.parallellingvo.app/` — Flask learning application.
- `https://learn.iovenko.eu/` — legacy hostname, redirects permanently to the new app hostname.
- Google and Telegram login start from the public website and finish inside the app.
- Telegram Mini App also opens `https://app.parallellingvo.app/`.

## Prepared in the repository

1. `nginx/app.parallellingvo.conf` proxies `app.parallellingvo.app` to `learn-words:7001`.
2. `nginx/learn.conf` redirects the old application hostname to the new app hostname.
3. `nginx/parallellingvo.conf` redirects the static site's `/auth/google` and `/auth/telegram` buttons to the app.
4. `app/web_auth.py` adds Google OIDC and Telegram OIDC login.
5. `auth_identities` is created automatically and maps provider identities to the existing `users.user_id`.
6. Existing Telegram numeric user IDs are preserved when possible so old lessons/progress remain attached.
7. Browser-controlled `?uid=` / localStorage user identity / `X-User-Id` was removed from `app/templates/base.html`.
8. Page API requests wait for server-verified Telegram Mini App auth or the existing Flask session before they run.
9. `X-User-Id` is also stripped server-side by default as defense in depth.
10. `bot/auth.py` no longer creates Mini App URLs with `?uid=` and no longer contains the personal fallback password.
11. If `BOT_PASSWORD` is empty, the branded public Telegram bot registers new Telegram users automatically. If it is set, the old shared-password gate remains available.
12. `.env.example` lists the required production variables.

## Server steps still required

### 1. Confirm DNS

The DNS record must resolve:

```text
app.parallellingvo.app -> 204.168.186.69
```

Verify from the server or an external resolver before requesting the certificate.

### 2. Issue TLS certificate

Issue a Let's Encrypt certificate for:

```text
app.parallellingvo.app
```

The nginx config expects:

```text
/etc/letsencrypt/live/app.parallellingvo.app/fullchain.pem
/etc/letsencrypt/live/app.parallellingvo.app/privkey.pem
```

Do not enable/reload the HTTPS vhost before the certificate exists, otherwise nginx validation can fail.

### 3. Install nginx vhost

Copy/enable:

```text
nginx/app.parallellingvo.conf
```

Keep the public-site vhost and legacy redirect vhost enabled as well. Run nginx config validation before reload.

### 4. Update server `.env`

At minimum:

```env
SITE_BASE_URL=https://parallellingvo.app
APP_BASE_URL=https://app.parallellingvo.app
PUBLIC_BASE_URL=https://app.parallellingvo.app
ALLOW_LEGACY_UID_AUTH=0
FLASK_SECRET=<strong-random-secret>
```

For a public Telegram bot, leave `BOT_PASSWORD` empty. Set it only if a temporary invitation/password gate is intentionally required.

### 5. Rebuild the application container

`Authlib` was added to `requirements.txt`, therefore the Flask image/container must be rebuilt, not only restarted.

After start, verify:

```text
https://app.parallellingvo.app/auth/status
```

An anonymous browser should receive `authenticated: false`.

## Google login setup

Create an OAuth/OIDC web client for ParallelLingvo.

Use this redirect URI:

```text
https://app.parallellingvo.app/auth/google/callback
```

Set on the server:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

Then test:

```text
https://parallellingvo.app/auth/google
```

Expected result: Google login -> callback -> `https://app.parallellingvo.app/`.

## Telegram bot and Telegram Login setup

Create a new branded bot for ParallelLingvo. Do not reuse the old personal-name bot.

Recommended identity:

- Name: `ParallelLingvo`
- Username: a free username such as `ParallelLingvoBot` or similar
- Avatar: ParallelLingvo logo

Put the new bot credentials on the server:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_BOT_USERNAME=...
```

In BotFather configure the Mini App URL:

```text
https://app.parallellingvo.app/
```

For Telegram Login/OIDC, BotFather -> Login Widget must include allowed URLs for the site/app and callback, including:

```text
https://parallellingvo.app
https://app.parallellingvo.app
https://app.parallellingvo.app/auth/telegram/callback
```

Copy BotFather's OIDC credentials into:

```env
TELEGRAM_OIDC_CLIENT_ID=...
TELEGRAM_OIDC_CLIENT_SECRET=...
```

Telegram OIDC discovery:

```text
https://oauth.telegram.org/.well-known/openid-configuration
```

Then test:

```text
https://parallellingvo.app/auth/telegram
```

Expected result: Telegram login -> callback -> `https://app.parallellingvo.app/`.

## Existing Telegram users

Historically `users.user_id` is the Telegram numeric ID. The new auth layer intentionally keeps that id for a Telegram account when possible. This avoids moving existing word/progress records during the first migration.

New Google-only accounts receive provider-neutral ids such as:

```text
u_<uuid>
```

Provider mappings live in:

```text
auth_identities
```

Do not delete or rewrite existing `users`, `words`, progress, lesson, or translation data during deployment.

## Security status

Production must keep:

```env
ALLOW_LEGACY_UID_AUTH=0
```

The current frontend no longer uses `?uid=` or `X-User-Id`. The Flask middleware also removes a supplied `X-User-Id` header unless legacy mode is explicitly enabled.

## Remaining repository cleanup for the next agent

The public static website still contains some direct `https://learn.iovenko.eu/` links in the main/localized HTML pages. They are not a deployment blocker because `learn.iovenko.eu` now redirects to the new hostname, but replace them with:

```text
https://app.parallellingvo.app/
```

Search the entire `website/` tree, including localized pages, Markdown/LLM documents and any app buttons. Do not change canonical URLs for the public marketing pages themselves; those must remain on `https://parallellingvo.app/`.

After server credentials are available, the next agent must also run a real end-to-end test of:

1. anonymous `GET /auth/status`;
2. Google OIDC login and callback;
3. Telegram OIDC login and callback;
4. Telegram Mini App initData login with the new bot token;
5. loading lessons/progress for an existing Telegram user;
6. loading lessons/progress for a new Google-only user;
7. old `learn.iovenko.eu` redirect preserving paths/query strings;
8. logout and second login.

## Recommended deployment order

1. DNS resolves.
2. Issue TLS certificate.
3. Install/enable app nginx vhost.
4. Update `.env` domain values and `FLASK_SECRET`.
5. Rebuild application container.
6. Test app directly and `/auth/status`.
7. Test old-domain redirect.
8. Configure Google credentials and test Google login.
9. Create/configure new ParallelLingvo Telegram bot.
10. Configure Telegram OIDC and Mini App URL.
11. Test Telegram browser login and Telegram Mini App login.
12. Replace remaining `learn.iovenko.eu` references in `website/`.
