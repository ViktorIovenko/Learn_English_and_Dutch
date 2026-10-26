# API and Telegram map

Строки и методы получены автоматически. Авторизация эвристически определяется по коду около handler; перед изменением контракта откройте handler и соответствующий DTO/consumer.

## `GET /privacy`

- Handler: `privacy_page` — `app/account_privacy.py:124`.
- Назначение: Backend file: account_privacy.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /account/delete`

- Handler: `deletion_page` — `app/account_privacy.py:136`.
- Назначение: Backend file: account_privacy.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/account/deletion-challenge`

- Handler: `deletion_challenge` — `app/account_privacy.py:142`.
- Назначение: Backend file: account_privacy.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/account/delete`

- Handler: `delete_account` — `app/account_privacy.py:149`.
- Назначение: Backend file: account_privacy.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ads/page`

- Handler: `api_ads_page` — `app/advertising/views.py:162`.
- Назначение: Backend file: views.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/ads.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ads/consent`

- Handler: `api_ads_consent_get` — `app/advertising/views.py:194`.
- Назначение: Backend file: views.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/ads.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/ads/consent`

- Handler: `api_ads_consent_set` — `app/advertising/views.py:202`.
- Назначение: Backend file: views.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/ads.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/ads/event`

- Handler: `api_ads_event` — `app/advertising/views.py:224`.
- Назначение: Anonymous aggregated counters for LIVE material only..
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/ads`

- Handler: `admin_ads_page` — `app/advertising/views.py:260`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/ads/state`

- Handler: `api_admin_ads_state` — `app/advertising/views.py:291`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/ads/stats`

- Handler: `api_admin_ads_stats` — `app/advertising/views.py:298`.
- Назначение: Aggregated LIVE counters by advertiser/creative/placement/device/country..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/ads/simulate`

- Handler: `api_admin_ads_simulate` — `app/advertising/views.py:310`.
- Назначение: What a Free user would get, as mock-ups (no external request)..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/settings`

- Handler: `api_admin_ads_settings` — `app/advertising/views.py:329`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/placements`

- Handler: `api_admin_ads_placement_save` — `app/advertising/views.py:341`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/placements/<key>/delete`

- Handler: `api_admin_ads_placement_delete` — `app/advertising/views.py:367`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/advertisers`

- Handler: `api_admin_ads_advertiser_save` — `app/advertising/views.py:377`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/creatives`

- Handler: `api_admin_ads_creative_save` — `app/advertising/views.py:412`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/creatives/<int:creative_id>/enabled`

- Handler: `api_admin_ads_creative_enabled` — `app/advertising/views.py:468`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/import-preview`

- Handler: `api_admin_ads_import_preview` — `app/advertising/views.py:479`.
- Назначение: Load the bundled read-only Awin check (candidates, preview copy, slots)..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/awin/sync`

- Handler: `api_admin_ads_awin_sync` — `app/advertising/views.py:499`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/awin/check/<int:advertiser_id>`

- Handler: `api_admin_ads_awin_check` — `app/advertising/views.py:518`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/awin/link`

- Handler: `api_admin_ads_awin_link` — `app/advertising/views.py:537`.
- Назначение: Explicit admin action: create a tracking link for an approved programme..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/awin/report`

- Handler: `api_admin_ads_awin_report` — `app/advertising/views.py:572`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/ai`

- Handler: `admin_ai_page` — `app/ai_gateway.py:260`.
- Назначение: Backend file: ai_gateway.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/ai/settings`

- Handler: `admin_ai_get` — `app/ai_gateway.py:269`.
- Назначение: Backend file: ai_gateway.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ai/settings`

- Handler: `admin_ai_save` — `app/ai_gateway.py:280`.
- Назначение: Backend file: ai_gateway.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/android/browser-link`

- Handler: `create_browser_link` — `app/android_auth.py:45`.
- Назначение: Backend file: android_auth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/android/browser`

- Handler: `browser_link_page` — `app/android_auth.py:68`.
- Назначение: Backend file: android_auth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/android_browser_login.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/android/browser-session`

- Handler: `consume_browser_link` — `app/android_auth.py:74`.
- Назначение: Backend file: android_auth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/android_browser_login.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/account/identities`

- Handler: `identities` — `app/android_auth.py:121`.
- Назначение: Backend file: android_auth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/android/start`

- Handler: `start` — `app/android_auth.py:150`.
- Назначение: Backend file: android_auth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/telegram/native`

- Handler: `native_telegram` — `app/android_auth.py:235`.
- Назначение: Backend file: android_auth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/android/exchange`

- Handler: `exchange` — `app/android_auth.py:286`.
- Назначение: Backend file: android_auth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/android/return`

- Handler: `return_page` — `app/android_auth.py:339`.
- Назначение: Backend file: android_auth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/google`

- Handler: `login` — `app/google_auth.py:347`.
- Назначение: Backend file: google_auth.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/google/callback`

- Handler: `callback` — `app/google_auth.py:368`.
- Назначение: Backend file: google_auth.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/auth/google/config`

- Handler: `android_google_config` — `app/google_auth.py:420`.
- Назначение: Return the public OAuth audience needed by Android Google Sign-In..
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/google/verify`

- Handler: `verify_android_token` — `app/google_auth.py:428`.
- Назначение: Android sends:  { "id_token": "<JWT from Google Sign-In SDK>" }
Returns:        { "ok": true, "user_id": "g_<sub>", "email": ..., "name": ... }.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/google/link`

- Handler: `verify_android_token` — `app/google_auth.py:429`.
- Назначение: Android sends:  { "id_token": "<JWT from Google Sign-In SDK>" }
Returns:        { "ok": true, "user_id": "g_<sub>", "email": ..., "name": ... }.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/subscription/sync`

- Handler: `sync_play_subscriptions` — `app/google_play.py:247`.
- Назначение: Backend file: google_play.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/subscription/google-play-notifications`

- Handler: `play_notifications` — `app/google_play.py:259`.
- Назначение: Backend file: google_play.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/mcp/user`

- Handler: `mcp_user_status` — `app/mcp_api.py:124`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/mcp_connector.js`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/mcp/user`

- Handler: `mcp_user_toggle` — `app/mcp_api.py:184`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/mcp_connector.js`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/mcp/user/revoke-all`

- Handler: `mcp_user_revoke_all` — `app/mcp_api.py:204`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/mcp_connector.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/mcp`

- Handler: `mcp_admin_page` — `app/mcp_api.py:244`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /admin/mcp/revoke`

- Handler: `mcp_admin_revoke` — `app/mcp_api.py:290`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /.well-known/oauth-authorization-server`

- Handler: `oauth_metadata` — `app/mcp_api.py:312`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /oauth/register`

- Handler: `oauth_register` — `app/mcp_api.py:332`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET,POST /oauth/authorize`

- Handler: `oauth_authorize` — `app/mcp_api.py:408`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /oauth/token`

- Handler: `oauth_token` — `app/mcp_api.py:501`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /oauth/revoke`

- Handler: `oauth_revoke` — `app/mcp_api.py:554`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/internal/mcp/resolve`

- Handler: `internal_mcp_resolve` — `app/mcp_api.py:566`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/internal/mcp/execute`

- Handler: `internal_mcp_execute` — `app/mcp_api.py:577`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/internal/mcp/health`

- Handler: `internal_mcp_health` — `app/mcp_api.py:633`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /sw.js`

- Handler: `service_worker` — `app/routes.py:2005`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /`

- Handler: `home` — `app/routes.py:2013`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`, `app/static/mcp_connector.js`, `app/static/sync.js`, `app/static/word_database.js`, `app/templates/account_type.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lessons`

- Handler: `lessons_alias` — `app/routes.py:2026`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lesson/<int:lesson_id>`

- Handler: `lesson_page` — `app/routes.py:2039`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /learn`

- Handler: `learn_page` — `app/routes.py:2044`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /difficult`

- Handler: `difficult_page` — `app/routes.py:2055`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /upload`

- Handler: `upload_page` — `app/routes.py:2060`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /word-database`

- Handler: `word_database_page` — `app/routes.py:2083`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /settings/mcp`

- Handler: `mcp_connector_page` — `app/routes.py:2093`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /settings`

- Handler: `settings_page` — `app/routes.py:2103`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /account-type`

- Handler: `account_type_page` — `app/routes.py:2113`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /.well-known/assetlinks.json`

- Handler: `android_app_links` — `app/routes.py:2122`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /family/connect`

- Handler: `family_link_page` — `app/routes.py:2127`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /family/link`

- Handler: `family_link_page` — `app/routes.py:2128`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /parent`

- Handler: `parent_dashboard_page` — `app/routes.py:2183`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /subscription`

- Handler: `subscription_page` — `app/routes.py:2192`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/users`

- Handler: `admin_users_page` — `app/routes.py:2198`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /share/<token>`

- Handler: `share_page` — `app/routes.py:2394`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/create`

- Handler: `api_share_create` — `app/routes.py:2458`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/share/source_lessons`

- Handler: `api_share_source_lessons` — `app/routes.py:2537`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/assign_child`

- Handler: `api_share_assign_child` — `app/routes.py:2614`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/<token>/import`

- Handler: `api_share_import` — `app/routes.py:2737`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/import-words`

- Handler: `api_import_words` — `app/routes.py:2841`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words`

- Handler: `api_get_words` — `app/routes.py:2858`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/static/upload.js`, `app/static/word_database.js`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/words/<int:word_id>`

- Handler: `api_update_word` — `app/routes.py:2918`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/words/<int:word_id>`

- Handler: `api_delete_word` — `app/routes.py:3052`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/nl-list`

- Handler: `api_words_nl_list` — `app/routes.py:3066`.
- Назначение: Lightweight list of all NL words for the current user (used for deduplication)..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/duplicates`

- Handler: `api_words_duplicates` — `app/routes.py:3080`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/word_database.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/parse-file`

- Handler: `api_parse_file` — `app/routes.py:3118`.
- Назначение: Parse uploaded CSV or Excel file, return rows as JSON for preview..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android`

- Handler: `login_android` — `app/routes.py:3218`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android_token`

- Handler: `login_android_token` — `app/routes.py:3229`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_link`

- Handler: `login_link` — `app/routes.py:3241`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /android-auth`

- Handler: `android_auth_redirect` — `app/routes.py:3253`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_webapp`

- Handler: `login_webapp` — `app/routes.py:3266`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/me`

- Handler: `api_me` — `app/routes.py:3300`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/admin_users.html`, `app/templates/base.html`, `app/templates/upload.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/account/type`

- Handler: `api_account_type_save` — `app/routes.py:3346`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: telegram init data/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/account_type.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family`

- Handler: `api_family_status` — `app/routes.py:3374`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`, `app/templates/family_link.html`, `app/templates/parent_dashboard.html`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/learning/streak`

- Handler: `api_learning_streak` — `app/routes.py:3382`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/dashboard`

- Handler: `api_family_dashboard` — `app/routes.py:3400`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/parent_dashboard.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/children/<child_user_id>/lesson-words`

- Handler: `api_family_child_lesson_words` — `app/routes.py:3429`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/family/children/<child_user_id>/priority-lesson`

- Handler: `api_family_set_priority_lesson` — `app/routes.py:3487`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-code`

- Handler: `api_family_pairing_code` — `app/routes.py:3577`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/invitation/preview`

- Handler: `api_family_invitation` — `app/routes.py:3588`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/invitation/accept`

- Handler: `api_family_invitation` — `app/routes.py:3589`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-qr.png`

- Handler: `api_family_pairing_qr` — `app/routes.py:3620`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/invite-code`

- Handler: `api_family_invite_code` — `app/routes.py:3665`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/invite-qr.png`

- Handler: `api_family_invite_qr` — `app/routes.py:3676`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/join`

- Handler: `api_family_join` — `app/routes.py:3703`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/link`

- Handler: `api_family_link` — `app/routes.py:3720`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/family/children/<child_user_id>`

- Handler: `api_family_unlink_child` — `app/routes.py:3786`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/subscription`

- Handler: `api_subscription_get` — `app/routes.py:3805`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/subscription/google-play-config`

- Handler: `api_google_play_config` — `app/routes.py:3813`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/subscription/verify_purchase`

- Handler: `api_verify_purchase` — `app/routes.py:3828`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/language-options`

- Handler: `api_language_options` — `app/routes.py:3845`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages`

- Handler: `api_user_languages_get` — `app/routes.py:3852`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user-languages`

- Handler: `api_user_languages_save` — `app/routes.py:3868`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages/missing-words`

- Handler: `api_user_languages_missing_words` — `app/routes.py:3909`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ui-language`

- Handler: `api_ui_language_get` — `app/routes.py:3947`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/ui-language`

- Handler: `api_ui_language_save` — `app/routes.py:3956`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons`

- Handler: `api_lessons` — `app/routes.py:4078`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user_lessons`

- Handler: `api_user_lessons` — `app/routes.py:4109`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user_lessons/rename`

- Handler: `api_user_lessons_rename` — `app/routes.py:4119`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user_lessons/delete`

- Handler: `api_user_lessons_delete` — `app/routes.py:4234`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/lessons/set_hidden`

- Handler: `api_lessons_set_hidden` — `app/routes.py:4308`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lesson_words`

- Handler: `api_lesson_words_by_title` — `app/routes.py:4322`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`, `app/templates/learn.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/child-learning/status`

- Handler: `api_child_learning_status` — `app/routes.py:4366`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/daily-goal`

- Handler: `api_daily_goal_get` — `app/routes.py:4395`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/daily-goal`

- Handler: `api_daily_goal_save` — `app/routes.py:4403`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons/<int:lesson_id>/words`

- Handler: `api_lesson_words` — `app/routes.py:4428`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/difficult_words_user`

- Handler: `api_difficult_words_user` — `app/routes.py:4467`.
- Назначение: Персональный список:
  - слова из words, у которых user_word_flags.difficult=1 для текущего пользователя
  (кастомные слова удалены).
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/difficult/user_set`

- Handler: `api_difficult_user_set` — `app/routes.py:4508`.
- Назначение: Body: {word_id: int, difficult: 0|1}.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/progress/sync`

- Handler: `api_progress_sync` — `app/routes.py:4549`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/sync.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/sync/updates`

- Handler: `api_sync_updates` — `app/routes.py:4610`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/audio/ensure`

- Handler: `api_audio_ensure` — `app/routes.py:4704`.
- Назначение: Body: { ids: [int,...], langs: ["nl","en","ru"] }
Для каждого id создаёт недостающие MP3, обновляет ссылки в words.audio_*.
Возвращает { ok: true, items: [ {ok,id,nl,en,ru}, ... ] }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/next_lesson`

- Handler: `api_next_lesson` — `app/routes.py:4726`.
- Назначение: Возвращает следующий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, next: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/prev_lesson`

- Handler: `api_prev_lesson` — `app/routes.py:4744`.
- Назначение: Возвращает предыдущий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, prev: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/session`

- Handler: `api_admin_session` — `app/routes.py:4775`.
- Назначение: Admin shell bootstrap for the main site: who is signed in + CSRF token..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/overview`

- Handler: `api_admin_overview` — `app/routes.py:4796`.
- Назначение: Data of the General / Subscriptions / Costs tabs (former /admin/users page)..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/users`

- Handler: `api_admin_users` — `app/routes.py:4805`.
- Назначение: Список всех пользователей с их статусом подписки. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/limit`

- Handler: `api_admin_set_tts_usage_limit` — `app/routes.py:4898`.
- Назначение: Sets the global or per-user monthly TTS character limit..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/reset`

- Handler: `api_admin_reset_tts_usage` — `app/routes.py:4941`.
- Назначение: Сбрасывает месячный Google TTS-счётчик одного пользователя или всех пользователей..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/translation_usage/reset`

- Handler: `api_admin_reset_translation_usage` — `app/routes.py:4977`.
- Назначение: Сбрасывает накопительную статистику токенов одного пользователя или всех..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/grant_access`

- Handler: `api_admin_grant_access` — `app/routes.py:5008`.
- Назначение: Выдаёт пользователю безлимитный доступ (100 лет). Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/revoke_access`

- Handler: `api_admin_revoke_access` — `app/routes.py:5046`.
- Назначение: Отзывает безлимитный доступ — переводит пользователя в истёкший trial. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/unlink_family`

- Handler: `api_admin_unlink_family` — `app/routes.py:5073`.
- Назначение: Remove one exact adult-child relationship. Only for admins..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/delete_user`

- Handler: `api_admin_delete_user` — `app/routes.py:5105`.
- Назначение: Полностью удаляет пользователя и его данные, чтобы он мог зарегистрироваться заново..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/plan-preview`

- Handler: `api_admin_plan_preview_get` — `app/routes.py:5152`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/plan-preview`

- Handler: `api_admin_plan_preview_set` — `app/routes.py:5160`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ai/status`

- Handler: `api_ai_status` — `app/routes.py:5182`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/word`

- Handler: `api_translate_word` — `app/routes.py:5195`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/static/word_database.js`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/generate/topic`

- Handler: `api_generate_topic` — `app/routes.py:5229`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/language`

- Handler: `api_translate_language` — `app/routes.py:5265`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/status`

- Handler: `auth_status` — `app/routes.py:5309`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/logout`

- Handler: `auth_logout` — `app/routes.py:5332`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/debug/whoami`

- Handler: `api_debug_whoami` — `app/routes.py:5351`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/telegram`

- Handler: `login` — `app/telegram_oauth.py:123`.
- Назначение: Backend file: telegram_oauth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/telegram/callback`

- Handler: `callback` — `app/telegram_oauth.py:147`.
- Назначение: Backend file: telegram_oauth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

# Telegram handlers

- `command /start` → `start_cmd` (`bot/auth.py:1020`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /open` → `open_cmd` (`bot/auth.py:1021`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /family` → `family_cmd` (`bot/auth.py:1022`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `callback r"^onboarding:(?:language|language_keep|language_change|account` → `onboarding_callback` (`bot/auth.py:1023`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `callback r"^family_link:(?:confirm|cancel` → `family_link_callback` (`bot/auth.py:1027`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `callback r"^family_join:(?:confirm|cancel` → `family_join_callback` (`bot/auth.py:1031`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(learn_words_pattern)` → `open_cmd` (`bot/auth.py:1038`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.TEXT & (~filters.COMMAND) & exclude_import_btns` → `on_text` (`bot/auth.py:1042`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /reminder_now` → `_cmd_reminder_now` (`bot/reminder.py:269`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /upload_words` → `cmd_upload_words` (`bot/upload.py:442`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(upload_words_pattern)` → `cmd_upload_words` (`bot/upload.py:443`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(r"^(Добавить слова|Импортировать слова)$")` → `cmd_upload_words` (`bot/upload.py:444`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Document.ALL & (~filters.COMMAND)` → `on_csv_document` (`bot/upload.py:445`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(confirm_pattern)` → `on_confirm_import_all` (`bot/upload.py:446`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(cancel_pattern)` → `on_cancel_import` (`bot/upload.py:447`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
