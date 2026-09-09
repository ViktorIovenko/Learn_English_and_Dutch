# Agent handoff — ParallelLingvo migration

Continue on branch `feature/landing-blog`.

The repository has already been prepared for `app.parallellingvo.app`, secure session-based login, Google OIDC, Telegram OIDC, a new branded Telegram bot, and legacy-domain redirect.

Read first:

```text
docs/APP_DOMAIN_MIGRATION.md
```

## Remaining work

1. On the production server, confirm `app.parallellingvo.app` resolves to `204.168.186.69`.
2. Issue/install the Let's Encrypt certificate expected by `nginx/app.parallellingvo.conf`.
3. Enable the new nginx vhost and validate/reload nginx.
4. Update the server `.env` from `.env.example` and rebuild the `learn-words` container because `Authlib` was added.
5. Create/configure the new ParallelLingvo Telegram bot and put its token in `TELEGRAM_BOT_TOKEN`.
6. Configure BotFather Mini App URL as `https://app.parallellingvo.app/`.
7. Configure Telegram Login/OIDC allowed URLs and put the BotFather OIDC client id/secret into the server `.env`.
8. Configure Google OAuth/OIDC and the callback `https://app.parallellingvo.app/auth/google/callback`.
9. Search all remaining files under `website/` for `learn.iovenko.eu` and replace direct application links with `https://app.parallellingvo.app/`. Do not change public-site canonical URLs that correctly point to `https://parallellingvo.app/`.
10. Run end-to-end tests listed in `docs/APP_DOMAIN_MIGRATION.md` before merging/deploying.

## Important constraints

- Do not reintroduce `?uid=` or browser-controlled `X-User-Id` authentication.
- Keep `ALLOW_LEGACY_UID_AUTH=0` in production.
- Do not delete/migrate existing user learning data during this deployment.
- Existing Telegram numeric `users.user_id` values are intentionally preserved for compatibility.
- Google-only users use provider-neutral internal ids (`u_<uuid>`).
- Public website remains static; the learning application lives on the app subdomain.
