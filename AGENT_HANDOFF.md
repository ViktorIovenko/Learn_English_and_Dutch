# Agent handoff — ParallelLingvo migration

Continue on branch `feature/landing-blog`.

The repository is prepared for `app.parallellingvo.app`, secure session-based login, Google OIDC, modern Telegram OIDC, Telegram Mini App `initData` auth, a new branded Telegram bot, and legacy-domain redirect.

Read first:

```text
docs/APP_DOMAIN_MIGRATION.md
```

## Authentication architecture

There are two official Telegram entry points and both must remain supported:

```text
Website -> Telegram OpenID Connect -> Flask session -> app
```

and:

```text
Telegram bot -> Mini App -> verified initData -> Flask session -> app
```

The website `/auth/telegram` route must use modern Telegram OpenID Connect (Authorization Code flow with PKCE), not redirect to the bot chat.

The Mini App must continue to authenticate with signed Telegram `initData` verified using `TELEGRAM_BOT_TOKEN`.

Both flows must resolve a Telegram account to the same numeric Telegram user id so existing lessons/progress remain available.

## BotFather configuration already chosen by the owner

### Login Widget -> OpenID Connect Login

```text
Redirect URI:
https://app.parallellingvo.app/auth/telegram/callback

Trusted Origins:
https://parallellingvo.app
https://app.parallellingvo.app

Signing algorithm:
RS256
```

The server needs:

```env
TELEGRAM_OIDC_CLIENT_ID=...
TELEGRAM_OIDC_CLIENT_SECRET=...
```

Do not commit either value.

The application requests `openid profile telegram:bot_access` and intentionally does not request the phone number.

### Mini App

```text
Main App URL: https://app.parallellingvo.app/
Menu Button URL: https://app.parallellingvo.app/
```

Keep Same-Origin Restriction enabled.

## Remaining work

1. On production, confirm `app.parallellingvo.app` resolves to `204.168.186.69`.
2. Issue/install the Let's Encrypt certificate expected by `nginx/app.parallellingvo.conf`.
3. Enable the new nginx vhost and validate/reload nginx.
4. Update server `.env` from `.env.example`.
5. Tell the owner the exact production `.env`/secret-store location where the new branded bot token must be placed as `TELEGRAM_BOT_TOKEN`.
6. Put the new bot username in `TELEGRAM_BOT_USERNAME`.
7. Put BotFather OpenID Connect Client ID/Secret into the production `.env`.
8. The owner will indicate where the existing Google credentials are stored; use those rather than creating new credentials without asking.
9. Configure Google callback `https://app.parallellingvo.app/auth/google/callback`.
10. Rebuild the `learn-words` container because `Authlib` is required.
11. Search remaining `website/` files for `learn.iovenko.eu` and replace direct application links with `https://app.parallellingvo.app/` while preserving public-site canonical URLs.
12. Run the end-to-end tests in `docs/APP_DOMAIN_MIGRATION.md`.

## Important constraints

- Do not reintroduce `?uid=` or browser-controlled `X-User-Id` authentication.
- Keep `ALLOW_LEGACY_UID_AUTH=0` in production.
- Telegram website login uses validated OIDC ID tokens.
- Telegram Mini App login uses validated `initData`.
- Do not substitute one Telegram mechanism for the other.
- Do not delete/migrate existing learning data during this deployment.
- Existing Telegram numeric `users.user_id` values are intentionally preserved.
- Google-only users use provider-neutral internal ids (`u_<uuid>`).
- Public website remains static; the learning application lives on the app subdomain.
- Never commit `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OIDC_CLIENT_SECRET`, `GOOGLE_CLIENT_SECRET`, or `FLASK_SECRET`.
