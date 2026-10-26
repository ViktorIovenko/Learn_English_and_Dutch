# Advertising (Awin) — `app/advertising/`

Isolated Flask module; `app/routes.py` only registers it (`init_advertising(app, _ads_viewer)`)
and supplies a read-only viewer (real plan, subscription status, account type, admin preview).

| File | Role |
|---|---|
| `store.py` | SQLite tables `ad_settings`, `ad_placements`, `ad_advertisers`, `ad_creatives`, `ad_stats` (aggregated, no user id), `ad_api_log` |
| `policy.py` | Who gets what: `decide()` → `none` / `demo` / `live` + reason |
| `selection.py` | Placement budget, device sizes, ranking country → language → topic → valid material |
| `creatives.py` | Awin "My Creative" parser (only `<a><img>` on Awin hosts), demo banners, 10-language labels/consent text |
| `awin.py` | Publisher API client: `programmes`, `programmedetails`, `linkbuilder/generate`, `reports/creative` |
| `preview_config.py` + `data/awin_preview_v1.json` | Import of the read-only Awin check (candidates, preview-only copy, slot formats) |
| `admin_ops.py` | Validation/updates shared by `/admin/ads` and the MCP `ads.admin` tools |
| `views.py` | `/api/ads/page`, `/api/ads/consent`, `/api/ads/event`, `/admin/ads`, `/api/admin/ads/*`, template context |
| `static/ads.js`, `templates/_ad_slot.html`, `templates/admin_ads.html` | Client renderer (DOM only), empty hidden slot, admin page |

## Rules
- Modes: `off` (default; no script, no request) · `preview` (admin Free simulation only, local mock-ups) · `live`.
- LIVE needs `ADS_LIVE_ALLOWED=1`, `AWIN_API_TOKEN`, and admin POST `{"mode":"live","confirm":"LIVE"}`. Nothing switches automatically.
- Owner decision 2026-10-09: when the 14-day trial ends without a purchase the user is Free and sees ads on every client (web, Telegram Mini App, Android). Child profiles exist only under a paid plan → never ads.
- LIVE serves only: standard (non-child) account, plan `free`, status `trial_expired` (`expired` only with `lapsed_paid_as_free`), platform in `live_platforms` (default `web`, `telegram`, `android`), consent granted, no `Sec-GPC: 1`.
- Consent: web/Mini App — first-party cookie `pl_ads_consent=v1:granted|denied`; Android (Bearer, no cookies) — table `ad_consent(user_id, platform, status, updated_at)`.
- LIVE material: creative enabled, not `preview_only`, advertiser enabled + `membership_status=joined` + Awin id + click URL on `awin1.com`/`tidd.ly`.
- Web only (`platform=web`, not Mini App/Android): `dashboard_between` is a row of banners, one per lesson-grid column (client sends `columns`, max 3); the row counts as one placement in `max_per_page`, its cells always differ.
- `admin_demo_always` (default off): administrators see mock-ups in every enabled slot without the Free simulation (web, Mini App, Android); users are not affected.
- MCP: scope `ads.admin` (admin only) — see `docs/MCP_CONNECTOR.md`.
- Android is identified by its signed Bearer token (platform forced to `android`, never from a parameter); the legacy `X-User-Id` header is never trusted. Admin tools need the browser session. Admin always sees mock-ups (no real image, link, impression).
- Android client: `ui/ads/AdBannerController.kt` on the lessons screen (`dashboard_bottom`, own row above the buttons). Banner images are fetched by a separate OkHttp client without token, user id or cookies; a click opens the Awin link in the browser. No ad SDK.
- Nothing personal is sent to Awin; `clickref` may only be a placement key.

## Env
`ADS_LIVE_ALLOWED`, `AWIN_PUBLISHER_ID` (default 3118768), `AWIN_API_TOKEN`, `AWIN_API_BASE`, `AWIN_API_TIMEOUT`,
`ADS_COUNTRY_HEADER` (e.g. `CF-IPCountry` from a trusted proxy), `AWIN_EXTRA_IMAGE_HOSTS`.

Tests: `tests/test_advertising.py`.
