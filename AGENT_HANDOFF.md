# Agent handoff — ParallelLingvo migration

Continue on branch `feature/landing-blog`.

The repository has already been prepared for `app.parallellingvo.app`, secure session-based login, Google OIDC, Telegram OIDC, a new branded Telegram bot, and legacy-domain redirect.

Read first:

```text
docs/APP_DOMAIN_MIGRATION.md
```

## Website redesign — done (2026-09-11)

`website/` was fully replaced with a new design and redeployed to production (`https://parallellingvo.app/`, served by the `parallellingvo-learnword-site-1` container from `/opt/parallellingvo/website` on `204.168.186.69`). Notes for whoever touches the site next:

- Only `en` (site root) and `ru` (`/ru/`) locales exist now. The old `de/es/fr/it/ja/nl/pl/pt/zh` locale folders and their CSS/JS (`base.css`, `brand.css`, `landing.css`, `i18n.css`, `responsive.css`, `locale-demo.js`, `session.js`, `locales.json`) are gone — the new design is self-contained in `website/assets/` (`styles.css`, `main.js` for theme/dropdown, `home.js` for the homepage's interactive widgets, `blog.js` for the blog index).
- The blog currently has one real article (`parallel-method`) instead of the old three. **To add a new post or a translation**: write `website/content/blog/<slug>.json` (see the existing file for the shape — `locales.en`/`locales.ru`, each with title/body/tags/etc.), then run `node tools/build-blog.mjs` from inside `website/`. It regenerates the article HTML pages, `assets/blog.js`'s article list, `sitemap.xml`, `feed.xml`, and `llms.txt`/`llms-full.txt` from those JSON files — don't hand-edit those generated blocks.
- `robots.txt`, `llms.txt`, `llms-full.txt`, `sitemap.xml`, `feed.xml` were rewritten for AI/LLM crawler indexing (GPTBot, ClaudeBot, PerplexityBot, etc. explicitly allowed).
- `nginx/learnword-site.conf` still has an old `sub_filter 'LearnWord' 'ParallelLingvo'` branding-compatibility hack; it's inert against the new markup (nothing matches it anymore) and safe to delete next time that file is touched, but wasn't removed in this pass.
- Deploy method used: `tar` the `website/` folder (excluding `content/` and `tools/`, which are source-only) and extract it over `/opt/parallellingvo/website` on the server, then `docker restart parallellingvo-learnword-site-1` (a bind-mount over a `rm -rf`'d-and-recreated directory doesn't pick up changes without a restart — always restart after replacing the whole folder).

## Remaining work (pre-existing app-domain migration checklist)

1. On the production server, confirm `app.parallellingvo.app` resolves to `204.168.186.69`.
2. Issue/install the Let's Encrypt certificate expected by `nginx/app.parallellingvo.conf`.
3. Enable the new nginx vhost and validate/reload nginx.
4. Update the server `.env` from `.env.example` and rebuild the `learn-words` container because `Authlib` was added.
5. Create/configure the new ParallelLingvo Telegram bot and put its token in `TELEGRAM_BOT_TOKEN`.
6. Configure BotFather Mini App URL as `https://app.parallellingvo.app/`.
7. Configure Telegram Login/OIDC allowed URLs and put the BotFather OIDC client id/secret into the server `.env`.
8. Configure Google OAuth/OIDC and the callback `https://app.parallellingvo.app/auth/google/callback`.
9. Run end-to-end tests listed in `docs/APP_DOMAIN_MIGRATION.md` before merging/deploying.

Note: `app.parallellingvo.app` already resolves and is serving traffic in production (confirmed while working on the item above), so items 1-3 may already be satisfied — verify rather than assume, this list wasn't re-audited end-to-end during the website work.

## Next phase: backend

Frontend/website work is done for now. Next up is backend work on the Flask app (`Learn_English_and_Dutch` repo — the actual application code, separate from this `website/` static site).

## Important constraints

- Do not reintroduce `?uid=` or browser-controlled `X-User-Id` authentication.
- Keep `ALLOW_LEGACY_UID_AUTH=0` in production.
- Do not delete/migrate existing user learning data during this deployment.
- Existing Telegram numeric `users.user_id` values are intentionally preserved for compatibility.
- Google-only users use provider-neutral internal ids (`u_<uuid>`).
- Public website remains static; the learning application lives on the app subdomain.
