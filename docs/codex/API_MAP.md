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
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/account/delete`

- Handler: `delete_account` — `app/account_privacy.py:149`.
- Назначение: Backend file: account_privacy.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ads/page`

- Handler: `api_ads_page` — `app/advertising/views.py:156`.
- Назначение: Backend file: views.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/ads.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ads/consent`

- Handler: `api_ads_consent_get` — `app/advertising/views.py:188`.
- Назначение: Backend file: views.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/ads.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/ads/consent`

- Handler: `api_ads_consent_set` — `app/advertising/views.py:196`.
- Назначение: Backend file: views.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/ads.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/ads/event`

- Handler: `api_ads_event` — `app/advertising/views.py:218`.
- Назначение: Anonymous aggregated counters for LIVE material only..
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/ads`

- Handler: `admin_ads_page` — `app/advertising/views.py:254`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/ads/state`

- Handler: `api_admin_ads_state` — `app/advertising/views.py:283`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/ads/simulate`

- Handler: `api_admin_ads_simulate` — `app/advertising/views.py:290`.
- Назначение: What a Free user would get, as mock-ups (no external request)..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/settings`

- Handler: `api_admin_ads_settings` — `app/advertising/views.py:309`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/placements`

- Handler: `api_admin_ads_placement_save` — `app/advertising/views.py:321`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/placements/<key>/delete`

- Handler: `api_admin_ads_placement_delete` — `app/advertising/views.py:347`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/advertisers`

- Handler: `api_admin_ads_advertiser_save` — `app/advertising/views.py:357`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/creatives`

- Handler: `api_admin_ads_creative_save` — `app/advertising/views.py:392`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/creatives/<int:creative_id>/enabled`

- Handler: `api_admin_ads_creative_enabled` — `app/advertising/views.py:448`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/import-preview`

- Handler: `api_admin_ads_import_preview` — `app/advertising/views.py:459`.
- Назначение: Load the bundled read-only Awin check (candidates, preview copy, slots)..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/awin/sync`

- Handler: `api_admin_ads_awin_sync` — `app/advertising/views.py:479`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/awin/check/<int:advertiser_id>`

- Handler: `api_admin_ads_awin_check` — `app/advertising/views.py:498`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/awin/link`

- Handler: `api_admin_ads_awin_link` — `app/advertising/views.py:517`.
- Назначение: Explicit admin action: create a tracking link for an approved programme..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ads/awin/report`

- Handler: `api_admin_ads_awin_report` — `app/advertising/views.py:552`.
- Назначение: Backend file: views.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/ai`

- Handler: `admin_ai_page` — `app/ai_gateway.py:261`.
- Назначение: Backend file: ai_gateway.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ai/settings`

- Handler: `admin_ai_save` — `app/ai_gateway.py:270`.
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
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
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
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
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
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/google/verify`

- Handler: `verify_android_token` — `app/google_auth.py:428`.
- Назначение: Android sends:  { "id_token": "<JWT from Google Sign-In SDK>" }
Returns:        { "ok": true, "user_id": "g_<sub>", "email": ..., "name": ... }.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/google/link`

- Handler: `verify_android_token` — `app/google_auth.py:429`.
- Назначение: Android sends:  { "id_token": "<JWT from Google Sign-In SDK>" }
Returns:        { "ok": true, "user_id": "g_<sub>", "email": ..., "name": ... }.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/subscription/sync`

- Handler: `sync_play_subscriptions` — `app/google_play.py:247`.
- Назначение: Backend file: google_play.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
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
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/mcp/user`

- Handler: `mcp_user_toggle` — `app/mcp_api.py:184`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/mcp_connector.js`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
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

- Handler: `service_worker` — `app/routes.py:1990`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /`

- Handler: `home` — `app/routes.py:1998`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`, `app/static/mcp_connector.js`, `app/static/sync.js`, `app/static/word_database.js`, `app/templates/account_type.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lessons`

- Handler: `lessons_alias` — `app/routes.py:2011`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lesson/<int:lesson_id>`

- Handler: `lesson_page` — `app/routes.py:2024`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /learn`

- Handler: `learn_page` — `app/routes.py:2029`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /difficult`

- Handler: `difficult_page` — `app/routes.py:2040`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /upload`

- Handler: `upload_page` — `app/routes.py:2045`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /word-database`

- Handler: `word_database_page` — `app/routes.py:2068`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /settings/mcp`

- Handler: `mcp_connector_page` — `app/routes.py:2078`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /settings`

- Handler: `settings_page` — `app/routes.py:2088`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /account-type`

- Handler: `account_type_page` — `app/routes.py:2098`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /.well-known/assetlinks.json`

- Handler: `android_app_links` — `app/routes.py:2107`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /family/connect`

- Handler: `family_link_page` — `app/routes.py:2112`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /family/link`

- Handler: `family_link_page` — `app/routes.py:2113`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /parent`

- Handler: `parent_dashboard_page` — `app/routes.py:2168`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /subscription`

- Handler: `subscription_page` — `app/routes.py:2177`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/users`

- Handler: `admin_users_page` — `app/routes.py:2183`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /share/<token>`

- Handler: `share_page` — `app/routes.py:2375`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/create`

- Handler: `api_share_create` — `app/routes.py:2439`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/share/source_lessons`

- Handler: `api_share_source_lessons` — `app/routes.py:2518`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/assign_child`

- Handler: `api_share_assign_child` — `app/routes.py:2595`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/<token>/import`

- Handler: `api_share_import` — `app/routes.py:2718`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/import-words`

- Handler: `api_import_words` — `app/routes.py:2822`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words`

- Handler: `api_get_words` — `app/routes.py:2839`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/static/upload.js`, `app/static/word_database.js`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/words/<int:word_id>`

- Handler: `api_update_word` — `app/routes.py:2899`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/words/<int:word_id>`

- Handler: `api_delete_word` — `app/routes.py:3033`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/nl-list`

- Handler: `api_words_nl_list` — `app/routes.py:3047`.
- Назначение: Lightweight list of all NL words for the current user (used for deduplication)..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/duplicates`

- Handler: `api_words_duplicates` — `app/routes.py:3061`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/word_database.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/parse-file`

- Handler: `api_parse_file` — `app/routes.py:3099`.
- Назначение: Parse uploaded CSV or Excel file, return rows as JSON for preview..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android`

- Handler: `login_android` — `app/routes.py:3199`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android_token`

- Handler: `login_android_token` — `app/routes.py:3210`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_link`

- Handler: `login_link` — `app/routes.py:3222`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /android-auth`

- Handler: `android_auth_redirect` — `app/routes.py:3234`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_webapp`

- Handler: `login_webapp` — `app/routes.py:3247`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/me`

- Handler: `api_me` — `app/routes.py:3281`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/templates/admin_users.html`, `app/templates/base.html`, `app/templates/upload.html`, `output/deploy-ai-admin-20261022/app/templates/admin_users.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/account/type`

- Handler: `api_account_type_save` — `app/routes.py:3327`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: telegram init data/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/account_type.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family`

- Handler: `api_family_status` — `app/routes.py:3355`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`, `app/templates/family_link.html`, `app/templates/parent_dashboard.html`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/learning/streak`

- Handler: `api_learning_streak` — `app/routes.py:3363`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/dashboard`

- Handler: `api_family_dashboard` — `app/routes.py:3381`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/parent_dashboard.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/children/<child_user_id>/lesson-words`

- Handler: `api_family_child_lesson_words` — `app/routes.py:3410`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/family/children/<child_user_id>/priority-lesson`

- Handler: `api_family_set_priority_lesson` — `app/routes.py:3468`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-code`

- Handler: `api_family_pairing_code` — `app/routes.py:3558`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/invitation/preview`

- Handler: `api_family_invitation` — `app/routes.py:3569`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/invitation/accept`

- Handler: `api_family_invitation` — `app/routes.py:3570`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-qr.png`

- Handler: `api_family_pairing_qr` — `app/routes.py:3601`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/invite-code`

- Handler: `api_family_invite_code` — `app/routes.py:3646`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/invite-qr.png`

- Handler: `api_family_invite_qr` — `app/routes.py:3657`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/join`

- Handler: `api_family_join` — `app/routes.py:3684`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/link`

- Handler: `api_family_link` — `app/routes.py:3701`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/family/children/<child_user_id>`

- Handler: `api_family_unlink_child` — `app/routes.py:3767`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/subscription`

- Handler: `api_subscription_get` — `app/routes.py:3786`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/subscription/google-play-config`

- Handler: `api_google_play_config` — `app/routes.py:3794`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/subscription/verify_purchase`

- Handler: `api_verify_purchase` — `app/routes.py:3809`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/language-options`

- Handler: `api_language_options` — `app/routes.py:3826`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages`

- Handler: `api_user_languages_get` — `app/routes.py:3833`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user-languages`

- Handler: `api_user_languages_save` — `app/routes.py:3849`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages/missing-words`

- Handler: `api_user_languages_missing_words` — `app/routes.py:3890`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ui-language`

- Handler: `api_ui_language_get` — `app/routes.py:3928`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/ui-language`

- Handler: `api_ui_language_save` — `app/routes.py:3937`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons`

- Handler: `api_lessons` — `app/routes.py:4059`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user_lessons`

- Handler: `api_user_lessons` — `app/routes.py:4090`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user_lessons/rename`

- Handler: `api_user_lessons_rename` — `app/routes.py:4100`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user_lessons/delete`

- Handler: `api_user_lessons_delete` — `app/routes.py:4215`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/lessons/set_hidden`

- Handler: `api_lessons_set_hidden` — `app/routes.py:4289`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lesson_words`

- Handler: `api_lesson_words_by_title` — `app/routes.py:4303`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`, `app/templates/learn.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/child-learning/status`

- Handler: `api_child_learning_status` — `app/routes.py:4347`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/daily-goal`

- Handler: `api_daily_goal_get` — `app/routes.py:4376`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/daily-goal`

- Handler: `api_daily_goal_save` — `app/routes.py:4384`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons/<int:lesson_id>/words`

- Handler: `api_lesson_words` — `app/routes.py:4409`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/difficult_words_user`

- Handler: `api_difficult_words_user` — `app/routes.py:4448`.
- Назначение: Персональный список:
  - слова из words, у которых user_word_flags.difficult=1 для текущего пользователя
  (кастомные слова удалены).
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/difficult/user_set`

- Handler: `api_difficult_user_set` — `app/routes.py:4489`.
- Назначение: Body: {word_id: int, difficult: 0|1}.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/progress/sync`

- Handler: `api_progress_sync` — `app/routes.py:4530`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/sync.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/sync/updates`

- Handler: `api_sync_updates` — `app/routes.py:4591`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/audio/ensure`

- Handler: `api_audio_ensure` — `app/routes.py:4685`.
- Назначение: Body: { ids: [int,...], langs: ["nl","en","ru"] }
Для каждого id создаёт недостающие MP3, обновляет ссылки в words.audio_*.
Возвращает { ok: true, items: [ {ok,id,nl,en,ru}, ... ] }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/next_lesson`

- Handler: `api_next_lesson` — `app/routes.py:4707`.
- Назначение: Возвращает следующий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, next: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/prev_lesson`

- Handler: `api_prev_lesson` — `app/routes.py:4725`.
- Назначение: Возвращает предыдущий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, prev: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/users`

- Handler: `api_admin_users` — `app/routes.py:4767`.
- Назначение: Список всех пользователей с их статусом подписки. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/limit`

- Handler: `api_admin_set_tts_usage_limit` — `app/routes.py:4860`.
- Назначение: Sets the global or per-user monthly TTS character limit..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/reset`

- Handler: `api_admin_reset_tts_usage` — `app/routes.py:4903`.
- Назначение: Сбрасывает месячный Google TTS-счётчик одного пользователя или всех пользователей..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/translation_usage/reset`

- Handler: `api_admin_reset_translation_usage` — `app/routes.py:4939`.
- Назначение: Сбрасывает накопительную статистику токенов одного пользователя или всех..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/grant_access`

- Handler: `api_admin_grant_access` — `app/routes.py:4970`.
- Назначение: Выдаёт пользователю безлимитный доступ (100 лет). Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/revoke_access`

- Handler: `api_admin_revoke_access` — `app/routes.py:5008`.
- Назначение: Отзывает безлимитный доступ — переводит пользователя в истёкший trial. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/unlink_family`

- Handler: `api_admin_unlink_family` — `app/routes.py:5035`.
- Назначение: Remove one exact adult-child relationship. Only for admins..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/delete_user`

- Handler: `api_admin_delete_user` — `app/routes.py:5067`.
- Назначение: Полностью удаляет пользователя и его данные, чтобы он мог зарегистрироваться заново..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/plan-preview`

- Handler: `api_admin_plan_preview_get` — `app/routes.py:5114`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/admin_users.html`, `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/plan-preview`

- Handler: `api_admin_plan_preview_set` — `app/routes.py:5122`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/admin_users.html`, `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ai/status`

- Handler: `api_ai_status` — `app/routes.py:5144`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/word`

- Handler: `api_translate_word` — `app/routes.py:5157`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/static/word_database.js`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/generate/topic`

- Handler: `api_generate_topic` — `app/routes.py:5191`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/language`

- Handler: `api_translate_language` — `app/routes.py:5227`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/status`

- Handler: `auth_status` — `app/routes.py:5271`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/logout`

- Handler: `auth_logout` — `app/routes.py:5290`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/debug/whoami`

- Handler: `api_debug_whoami` — `app/routes.py:5309`.
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

## `GET /admin/ai`

- Handler: `admin_ai_page` — `output/deploy-ai-admin-20261022/app/ai_gateway.py:261`.
- Назначение: Project file: ai_gateway.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/ai/settings`

- Handler: `admin_ai_save` — `output/deploy-ai-admin-20261022/app/ai_gateway.py:270`.
- Назначение: Project file: ai_gateway.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /sw.js`

- Handler: `service_worker` — `output/deploy-ai-admin-20261022/app/routes.py:1781`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /`

- Handler: `home` — `output/deploy-ai-admin-20261022/app/routes.py:1789`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`, `app/static/mcp_connector.js`, `app/static/sync.js`, `app/static/word_database.js`, `app/templates/account_type.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lessons`

- Handler: `lessons_alias` — `output/deploy-ai-admin-20261022/app/routes.py:1802`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lesson/<int:lesson_id>`

- Handler: `lesson_page` — `output/deploy-ai-admin-20261022/app/routes.py:1815`.
- Назначение: Project file: routes.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /learn`

- Handler: `learn_page` — `output/deploy-ai-admin-20261022/app/routes.py:1820`.
- Назначение: Project file: routes.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /difficult`

- Handler: `difficult_page` — `output/deploy-ai-admin-20261022/app/routes.py:1831`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /upload`

- Handler: `upload_page` — `output/deploy-ai-admin-20261022/app/routes.py:1836`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /settings`

- Handler: `settings_page` — `output/deploy-ai-admin-20261022/app/routes.py:1853`.
- Назначение: Project file: routes.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /account-type`

- Handler: `account_type_page` — `output/deploy-ai-admin-20261022/app/routes.py:1863`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /family/link`

- Handler: `family_link_page` — `output/deploy-ai-admin-20261022/app/routes.py:1872`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /parent`

- Handler: `parent_dashboard_page` — `output/deploy-ai-admin-20261022/app/routes.py:1898`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /subscription`

- Handler: `subscription_page` — `output/deploy-ai-admin-20261022/app/routes.py:1907`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/users`

- Handler: `admin_users_page` — `output/deploy-ai-admin-20261022/app/routes.py:1912`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /share/<token>`

- Handler: `share_page` — `output/deploy-ai-admin-20261022/app/routes.py:2104`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/create`

- Handler: `api_share_create` — `output/deploy-ai-admin-20261022/app/routes.py:2168`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/share/source_lessons`

- Handler: `api_share_source_lessons` — `output/deploy-ai-admin-20261022/app/routes.py:2247`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/assign_child`

- Handler: `api_share_assign_child` — `output/deploy-ai-admin-20261022/app/routes.py:2324`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/<token>/import`

- Handler: `api_share_import` — `output/deploy-ai-admin-20261022/app/routes.py:2447`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/import-words`

- Handler: `api_import_words` — `output/deploy-ai-admin-20261022/app/routes.py:2551`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words`

- Handler: `api_get_words` — `output/deploy-ai-admin-20261022/app/routes.py:2606`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/static/upload.js`, `app/static/word_database.js`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/words/<int:word_id>`

- Handler: `api_update_word` — `output/deploy-ai-admin-20261022/app/routes.py:2664`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/words/<int:word_id>`

- Handler: `api_delete_word` — `output/deploy-ai-admin-20261022/app/routes.py:2787`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/nl-list`

- Handler: `api_words_nl_list` — `output/deploy-ai-admin-20261022/app/routes.py:2801`.
- Назначение: Lightweight list of all NL words for the current user (used for deduplication)..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/duplicates`

- Handler: `api_words_duplicates` — `output/deploy-ai-admin-20261022/app/routes.py:2815`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/word_database.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/parse-file`

- Handler: `api_parse_file` — `output/deploy-ai-admin-20261022/app/routes.py:2853`.
- Назначение: Parse uploaded CSV or Excel file, return rows as JSON for preview..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android`

- Handler: `login_android` — `output/deploy-ai-admin-20261022/app/routes.py:2953`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android_token`

- Handler: `login_android_token` — `output/deploy-ai-admin-20261022/app/routes.py:2964`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_link`

- Handler: `login_link` — `output/deploy-ai-admin-20261022/app/routes.py:2976`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /android-auth`

- Handler: `android_auth_redirect` — `output/deploy-ai-admin-20261022/app/routes.py:2988`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_webapp`

- Handler: `login_webapp` — `output/deploy-ai-admin-20261022/app/routes.py:3001`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/me`

- Handler: `api_me` — `output/deploy-ai-admin-20261022/app/routes.py:3033`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/templates/admin_users.html`, `app/templates/base.html`, `app/templates/upload.html`, `output/deploy-ai-admin-20261022/app/templates/admin_users.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/account/type`

- Handler: `api_account_type_save` — `output/deploy-ai-admin-20261022/app/routes.py:3077`.
- Назначение: Project file: routes.py.
- Авторизация: telegram init data/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/account_type.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family`

- Handler: `api_family_status` — `output/deploy-ai-admin-20261022/app/routes.py:3105`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`, `app/templates/family_link.html`, `app/templates/parent_dashboard.html`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/learning/streak`

- Handler: `api_learning_streak` — `output/deploy-ai-admin-20261022/app/routes.py:3113`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/dashboard`

- Handler: `api_family_dashboard` — `output/deploy-ai-admin-20261022/app/routes.py:3131`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/parent_dashboard.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/children/<child_user_id>/lesson-words`

- Handler: `api_family_child_lesson_words` — `output/deploy-ai-admin-20261022/app/routes.py:3157`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/family/children/<child_user_id>/priority-lesson`

- Handler: `api_family_set_priority_lesson` — `output/deploy-ai-admin-20261022/app/routes.py:3212`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-code`

- Handler: `api_family_pairing_code` — `output/deploy-ai-admin-20261022/app/routes.py:3301`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-qr.png`

- Handler: `api_family_pairing_qr` — `output/deploy-ai-admin-20261022/app/routes.py:3312`.
- Назначение: Project file: routes.py.
- Авторизация: telegram init data/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/invite-code`

- Handler: `api_family_invite_code` — `output/deploy-ai-admin-20261022/app/routes.py:3359`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/invite-qr.png`

- Handler: `api_family_invite_qr` — `output/deploy-ai-admin-20261022/app/routes.py:3370`.
- Назначение: Project file: routes.py.
- Авторизация: telegram init data/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/join`

- Handler: `api_family_join` — `output/deploy-ai-admin-20261022/app/routes.py:3400`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/link`

- Handler: `api_family_link` — `output/deploy-ai-admin-20261022/app/routes.py:3417`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/family/children/<child_user_id>`

- Handler: `api_family_unlink_child` — `output/deploy-ai-admin-20261022/app/routes.py:3473`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/subscription`

- Handler: `api_subscription_get` — `output/deploy-ai-admin-20261022/app/routes.py:3492`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/subscription/verify_purchase`

- Handler: `api_verify_purchase` — `output/deploy-ai-admin-20261022/app/routes.py:3522`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/language-options`

- Handler: `api_language_options` — `output/deploy-ai-admin-20261022/app/routes.py:3589`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages`

- Handler: `api_user_languages_get` — `output/deploy-ai-admin-20261022/app/routes.py:3596`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user-languages`

- Handler: `api_user_languages_save` — `output/deploy-ai-admin-20261022/app/routes.py:3612`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages/missing-words`

- Handler: `api_user_languages_missing_words` — `output/deploy-ai-admin-20261022/app/routes.py:3653`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ui-language`

- Handler: `api_ui_language_get` — `output/deploy-ai-admin-20261022/app/routes.py:3691`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/ui-language`

- Handler: `api_ui_language_save` — `output/deploy-ai-admin-20261022/app/routes.py:3700`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons`

- Handler: `api_lessons` — `output/deploy-ai-admin-20261022/app/routes.py:3822`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user_lessons`

- Handler: `api_user_lessons` — `output/deploy-ai-admin-20261022/app/routes.py:3853`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user_lessons/rename`

- Handler: `api_user_lessons_rename` — `output/deploy-ai-admin-20261022/app/routes.py:3863`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user_lessons/delete`

- Handler: `api_user_lessons_delete` — `output/deploy-ai-admin-20261022/app/routes.py:3978`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/lessons/set_hidden`

- Handler: `api_lessons_set_hidden` — `output/deploy-ai-admin-20261022/app/routes.py:4052`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lesson_words`

- Handler: `api_lesson_words_by_title` — `output/deploy-ai-admin-20261022/app/routes.py:4066`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`, `app/templates/learn.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/child-learning/status`

- Handler: `api_child_learning_status` — `output/deploy-ai-admin-20261022/app/routes.py:4110`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/daily-goal`

- Handler: `api_daily_goal_get` — `output/deploy-ai-admin-20261022/app/routes.py:4139`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/daily-goal`

- Handler: `api_daily_goal_save` — `output/deploy-ai-admin-20261022/app/routes.py:4147`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons/<int:lesson_id>/words`

- Handler: `api_lesson_words` — `output/deploy-ai-admin-20261022/app/routes.py:4172`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/difficult_words_user`

- Handler: `api_difficult_words_user` — `output/deploy-ai-admin-20261022/app/routes.py:4211`.
- Назначение: Персональный список:
  - слова из words, у которых user_word_flags.difficult=1 для текущего пользователя
  (кастомные слова удалены).
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/difficult/user_set`

- Handler: `api_difficult_user_set` — `output/deploy-ai-admin-20261022/app/routes.py:4252`.
- Назначение: Body: {word_id: int, difficult: 0|1}.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/progress/sync`

- Handler: `api_progress_sync` — `output/deploy-ai-admin-20261022/app/routes.py:4293`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/sync.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/sync/updates`

- Handler: `api_sync_updates` — `output/deploy-ai-admin-20261022/app/routes.py:4354`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/audio/ensure`

- Handler: `api_audio_ensure` — `output/deploy-ai-admin-20261022/app/routes.py:4448`.
- Назначение: Body: { ids: [int,...], langs: ["nl","en","ru"] }
Для каждого id создаёт недостающие MP3, обновляет ссылки в words.audio_*.
Возвращает { ok: true, items: [ {ok,id,nl,en,ru}, ... ] }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/next_lesson`

- Handler: `api_next_lesson` — `output/deploy-ai-admin-20261022/app/routes.py:4470`.
- Назначение: Возвращает следующий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, next: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/prev_lesson`

- Handler: `api_prev_lesson` — `output/deploy-ai-admin-20261022/app/routes.py:4488`.
- Назначение: Возвращает предыдущий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, prev: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/users`

- Handler: `api_admin_users` — `output/deploy-ai-admin-20261022/app/routes.py:4530`.
- Назначение: Список всех пользователей с их статусом подписки. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/limit`

- Handler: `api_admin_set_tts_usage_limit` — `output/deploy-ai-admin-20261022/app/routes.py:4623`.
- Назначение: Sets the global or per-user monthly TTS character limit..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/reset`

- Handler: `api_admin_reset_tts_usage` — `output/deploy-ai-admin-20261022/app/routes.py:4666`.
- Назначение: Сбрасывает месячный Google TTS-счётчик одного пользователя или всех пользователей..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/translation_usage/reset`

- Handler: `api_admin_reset_translation_usage` — `output/deploy-ai-admin-20261022/app/routes.py:4702`.
- Назначение: Сбрасывает накопительную статистику токенов одного пользователя или всех..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/grant_access`

- Handler: `api_admin_grant_access` — `output/deploy-ai-admin-20261022/app/routes.py:4733`.
- Назначение: Выдаёт пользователю безлимитный доступ (100 лет). Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/revoke_access`

- Handler: `api_admin_revoke_access` — `output/deploy-ai-admin-20261022/app/routes.py:4766`.
- Назначение: Отзывает безлимитный доступ — переводит пользователя в истёкший trial. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/unlink_family`

- Handler: `api_admin_unlink_family` — `output/deploy-ai-admin-20261022/app/routes.py:4792`.
- Назначение: Remove one exact adult-child relationship. Only for admins..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/delete_user`

- Handler: `api_admin_delete_user` — `output/deploy-ai-admin-20261022/app/routes.py:4824`.
- Назначение: Полностью удаляет пользователя и его данные, чтобы он мог зарегистрироваться заново..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ai/status`

- Handler: `api_ai_status` — `output/deploy-ai-admin-20261022/app/routes.py:4922`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/word`

- Handler: `api_translate_word` — `output/deploy-ai-admin-20261022/app/routes.py:4930`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/static/word_database.js`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/generate/topic`

- Handler: `api_generate_topic` — `output/deploy-ai-admin-20261022/app/routes.py:4959`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/language`

- Handler: `api_translate_language` — `output/deploy-ai-admin-20261022/app/routes.py:4991`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/status`

- Handler: `auth_status` — `output/deploy-ai-admin-20261022/app/routes.py:5032`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/logout`

- Handler: `auth_logout` — `output/deploy-ai-admin-20261022/app/routes.py:5051`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/debug/whoami`

- Handler: `api_debug_whoami` — `output/deploy-ai-admin-20261022/app/routes.py:5070`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /privacy`

- Handler: `privacy_page` — `output/google-play-preparation-20261021/sources/app/account_privacy.py:124`.
- Назначение: Project file: account_privacy.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /account/delete`

- Handler: `deletion_page` — `output/google-play-preparation-20261021/sources/app/account_privacy.py:136`.
- Назначение: Project file: account_privacy.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/account/deletion-challenge`

- Handler: `deletion_challenge` — `output/google-play-preparation-20261021/sources/app/account_privacy.py:142`.
- Назначение: Project file: account_privacy.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/account/delete`

- Handler: `delete_account` — `output/google-play-preparation-20261021/sources/app/account_privacy.py:149`.
- Назначение: Project file: account_privacy.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/subscription/sync`

- Handler: `sync_play_subscriptions` — `output/google-play-preparation-20261021/sources/app/google_play.py:247`.
- Назначение: Project file: google_play.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/subscription/google-play-notifications`

- Handler: `play_notifications` — `output/google-play-preparation-20261021/sources/app/google_play.py:259`.
- Назначение: Project file: google_play.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /sw.js`

- Handler: `service_worker` — `output/google-play-preparation-20261021/sources/app/routes.py:1978`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /`

- Handler: `home` — `output/google-play-preparation-20261021/sources/app/routes.py:1986`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`, `app/static/mcp_connector.js`, `app/static/sync.js`, `app/static/word_database.js`, `app/templates/account_type.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lessons`

- Handler: `lessons_alias` — `output/google-play-preparation-20261021/sources/app/routes.py:1999`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lesson/<int:lesson_id>`

- Handler: `lesson_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2012`.
- Назначение: Project file: routes.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /learn`

- Handler: `learn_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2017`.
- Назначение: Project file: routes.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /difficult`

- Handler: `difficult_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2028`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /upload`

- Handler: `upload_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2033`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /word-database`

- Handler: `word_database_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2056`.
- Назначение: Project file: routes.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /settings/mcp`

- Handler: `mcp_connector_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2066`.
- Назначение: Project file: routes.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /settings`

- Handler: `settings_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2076`.
- Назначение: Project file: routes.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /account-type`

- Handler: `account_type_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2086`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /.well-known/assetlinks.json`

- Handler: `android_app_links` — `output/google-play-preparation-20261021/sources/app/routes.py:2095`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /family/connect`

- Handler: `family_link_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2100`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /family/link`

- Handler: `family_link_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2101`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /parent`

- Handler: `parent_dashboard_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2156`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /subscription`

- Handler: `subscription_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2165`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/users`

- Handler: `admin_users_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2171`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /share/<token>`

- Handler: `share_page` — `output/google-play-preparation-20261021/sources/app/routes.py:2363`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/create`

- Handler: `api_share_create` — `output/google-play-preparation-20261021/sources/app/routes.py:2427`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/share/source_lessons`

- Handler: `api_share_source_lessons` — `output/google-play-preparation-20261021/sources/app/routes.py:2506`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/assign_child`

- Handler: `api_share_assign_child` — `output/google-play-preparation-20261021/sources/app/routes.py:2583`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/<token>/import`

- Handler: `api_share_import` — `output/google-play-preparation-20261021/sources/app/routes.py:2706`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/import-words`

- Handler: `api_import_words` — `output/google-play-preparation-20261021/sources/app/routes.py:2810`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words`

- Handler: `api_get_words` — `output/google-play-preparation-20261021/sources/app/routes.py:2827`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/static/upload.js`, `app/static/word_database.js`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/words/<int:word_id>`

- Handler: `api_update_word` — `output/google-play-preparation-20261021/sources/app/routes.py:2887`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/words/<int:word_id>`

- Handler: `api_delete_word` — `output/google-play-preparation-20261021/sources/app/routes.py:3021`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/nl-list`

- Handler: `api_words_nl_list` — `output/google-play-preparation-20261021/sources/app/routes.py:3035`.
- Назначение: Lightweight list of all NL words for the current user (used for deduplication)..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/duplicates`

- Handler: `api_words_duplicates` — `output/google-play-preparation-20261021/sources/app/routes.py:3049`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/word_database.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/parse-file`

- Handler: `api_parse_file` — `output/google-play-preparation-20261021/sources/app/routes.py:3087`.
- Назначение: Parse uploaded CSV or Excel file, return rows as JSON for preview..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android`

- Handler: `login_android` — `output/google-play-preparation-20261021/sources/app/routes.py:3187`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android_token`

- Handler: `login_android_token` — `output/google-play-preparation-20261021/sources/app/routes.py:3198`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_link`

- Handler: `login_link` — `output/google-play-preparation-20261021/sources/app/routes.py:3210`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /android-auth`

- Handler: `android_auth_redirect` — `output/google-play-preparation-20261021/sources/app/routes.py:3222`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_webapp`

- Handler: `login_webapp` — `output/google-play-preparation-20261021/sources/app/routes.py:3235`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/me`

- Handler: `api_me` — `output/google-play-preparation-20261021/sources/app/routes.py:3267`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/templates/admin_users.html`, `app/templates/base.html`, `app/templates/upload.html`, `output/deploy-ai-admin-20261022/app/templates/admin_users.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/account/type`

- Handler: `api_account_type_save` — `output/google-play-preparation-20261021/sources/app/routes.py:3313`.
- Назначение: Project file: routes.py.
- Авторизация: telegram init data/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/account_type.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family`

- Handler: `api_family_status` — `output/google-play-preparation-20261021/sources/app/routes.py:3341`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`, `app/templates/family_link.html`, `app/templates/parent_dashboard.html`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/learning/streak`

- Handler: `api_learning_streak` — `output/google-play-preparation-20261021/sources/app/routes.py:3349`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/dashboard`

- Handler: `api_family_dashboard` — `output/google-play-preparation-20261021/sources/app/routes.py:3367`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/parent_dashboard.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/children/<child_user_id>/lesson-words`

- Handler: `api_family_child_lesson_words` — `output/google-play-preparation-20261021/sources/app/routes.py:3396`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/family/children/<child_user_id>/priority-lesson`

- Handler: `api_family_set_priority_lesson` — `output/google-play-preparation-20261021/sources/app/routes.py:3454`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-code`

- Handler: `api_family_pairing_code` — `output/google-play-preparation-20261021/sources/app/routes.py:3544`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/invitation/preview`

- Handler: `api_family_invitation` — `output/google-play-preparation-20261021/sources/app/routes.py:3555`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/invitation/accept`

- Handler: `api_family_invitation` — `output/google-play-preparation-20261021/sources/app/routes.py:3556`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-qr.png`

- Handler: `api_family_pairing_qr` — `output/google-play-preparation-20261021/sources/app/routes.py:3587`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/invite-code`

- Handler: `api_family_invite_code` — `output/google-play-preparation-20261021/sources/app/routes.py:3632`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/invite-qr.png`

- Handler: `api_family_invite_qr` — `output/google-play-preparation-20261021/sources/app/routes.py:3643`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/join`

- Handler: `api_family_join` — `output/google-play-preparation-20261021/sources/app/routes.py:3670`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/link`

- Handler: `api_family_link` — `output/google-play-preparation-20261021/sources/app/routes.py:3687`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/family/children/<child_user_id>`

- Handler: `api_family_unlink_child` — `output/google-play-preparation-20261021/sources/app/routes.py:3753`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/subscription`

- Handler: `api_subscription_get` — `output/google-play-preparation-20261021/sources/app/routes.py:3772`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/subscription/google-play-config`

- Handler: `api_google_play_config` — `output/google-play-preparation-20261021/sources/app/routes.py:3780`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/subscription/verify_purchase`

- Handler: `api_verify_purchase` — `output/google-play-preparation-20261021/sources/app/routes.py:3795`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/language-options`

- Handler: `api_language_options` — `output/google-play-preparation-20261021/sources/app/routes.py:3812`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages`

- Handler: `api_user_languages_get` — `output/google-play-preparation-20261021/sources/app/routes.py:3819`.
- Назначение: Project file: routes.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user-languages`

- Handler: `api_user_languages_save` — `output/google-play-preparation-20261021/sources/app/routes.py:3835`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages/missing-words`

- Handler: `api_user_languages_missing_words` — `output/google-play-preparation-20261021/sources/app/routes.py:3876`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ui-language`

- Handler: `api_ui_language_get` — `output/google-play-preparation-20261021/sources/app/routes.py:3914`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/ui-language`

- Handler: `api_ui_language_save` — `output/google-play-preparation-20261021/sources/app/routes.py:3923`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons`

- Handler: `api_lessons` — `output/google-play-preparation-20261021/sources/app/routes.py:4045`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user_lessons`

- Handler: `api_user_lessons` — `output/google-play-preparation-20261021/sources/app/routes.py:4076`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user_lessons/rename`

- Handler: `api_user_lessons_rename` — `output/google-play-preparation-20261021/sources/app/routes.py:4086`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user_lessons/delete`

- Handler: `api_user_lessons_delete` — `output/google-play-preparation-20261021/sources/app/routes.py:4201`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/lessons/set_hidden`

- Handler: `api_lessons_set_hidden` — `output/google-play-preparation-20261021/sources/app/routes.py:4275`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lesson_words`

- Handler: `api_lesson_words_by_title` — `output/google-play-preparation-20261021/sources/app/routes.py:4289`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`, `app/templates/learn.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/child-learning/status`

- Handler: `api_child_learning_status` — `output/google-play-preparation-20261021/sources/app/routes.py:4333`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/daily-goal`

- Handler: `api_daily_goal_get` — `output/google-play-preparation-20261021/sources/app/routes.py:4362`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/daily-goal`

- Handler: `api_daily_goal_save` — `output/google-play-preparation-20261021/sources/app/routes.py:4370`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons/<int:lesson_id>/words`

- Handler: `api_lesson_words` — `output/google-play-preparation-20261021/sources/app/routes.py:4395`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/difficult_words_user`

- Handler: `api_difficult_words_user` — `output/google-play-preparation-20261021/sources/app/routes.py:4434`.
- Назначение: Персональный список:
  - слова из words, у которых user_word_flags.difficult=1 для текущего пользователя
  (кастомные слова удалены).
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/difficult/user_set`

- Handler: `api_difficult_user_set` — `output/google-play-preparation-20261021/sources/app/routes.py:4475`.
- Назначение: Body: {word_id: int, difficult: 0|1}.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/progress/sync`

- Handler: `api_progress_sync` — `output/google-play-preparation-20261021/sources/app/routes.py:4516`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/sync.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/sync/updates`

- Handler: `api_sync_updates` — `output/google-play-preparation-20261021/sources/app/routes.py:4577`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/audio/ensure`

- Handler: `api_audio_ensure` — `output/google-play-preparation-20261021/sources/app/routes.py:4671`.
- Назначение: Body: { ids: [int,...], langs: ["nl","en","ru"] }
Для каждого id создаёт недостающие MP3, обновляет ссылки в words.audio_*.
Возвращает { ok: true, items: [ {ok,id,nl,en,ru}, ... ] }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/next_lesson`

- Handler: `api_next_lesson` — `output/google-play-preparation-20261021/sources/app/routes.py:4693`.
- Назначение: Возвращает следующий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, next: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/prev_lesson`

- Handler: `api_prev_lesson` — `output/google-play-preparation-20261021/sources/app/routes.py:4711`.
- Назначение: Возвращает предыдущий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, prev: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/users`

- Handler: `api_admin_users` — `output/google-play-preparation-20261021/sources/app/routes.py:4753`.
- Назначение: Список всех пользователей с их статусом подписки. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/limit`

- Handler: `api_admin_set_tts_usage_limit` — `output/google-play-preparation-20261021/sources/app/routes.py:4846`.
- Назначение: Sets the global or per-user monthly TTS character limit..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/reset`

- Handler: `api_admin_reset_tts_usage` — `output/google-play-preparation-20261021/sources/app/routes.py:4889`.
- Назначение: Сбрасывает месячный Google TTS-счётчик одного пользователя или всех пользователей..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/translation_usage/reset`

- Handler: `api_admin_reset_translation_usage` — `output/google-play-preparation-20261021/sources/app/routes.py:4925`.
- Назначение: Сбрасывает накопительную статистику токенов одного пользователя или всех..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/grant_access`

- Handler: `api_admin_grant_access` — `output/google-play-preparation-20261021/sources/app/routes.py:4956`.
- Назначение: Выдаёт пользователю безлимитный доступ (100 лет). Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/revoke_access`

- Handler: `api_admin_revoke_access` — `output/google-play-preparation-20261021/sources/app/routes.py:4994`.
- Назначение: Отзывает безлимитный доступ — переводит пользователя в истёкший trial. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/unlink_family`

- Handler: `api_admin_unlink_family` — `output/google-play-preparation-20261021/sources/app/routes.py:5021`.
- Назначение: Remove one exact adult-child relationship. Only for admins..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/delete_user`

- Handler: `api_admin_delete_user` — `output/google-play-preparation-20261021/sources/app/routes.py:5053`.
- Назначение: Полностью удаляет пользователя и его данные, чтобы он мог зарегистрироваться заново..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/plan-preview`

- Handler: `api_admin_plan_preview_get` — `output/google-play-preparation-20261021/sources/app/routes.py:5100`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/admin_users.html`, `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/plan-preview`

- Handler: `api_admin_plan_preview_set` — `output/google-play-preparation-20261021/sources/app/routes.py:5108`.
- Назначение: Project file: routes.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/admin_users.html`, `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ai/status`

- Handler: `api_ai_status` — `output/google-play-preparation-20261021/sources/app/routes.py:5130`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/word`

- Handler: `api_translate_word` — `output/google-play-preparation-20261021/sources/app/routes.py:5143`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/static/word_database.js`, `app/templates/settings.html`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/generate/topic`

- Handler: `api_generate_topic` — `output/google-play-preparation-20261021/sources/app/routes.py:5177`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `output/google-play-preparation-20261021/sources/android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`, `android/app/src/main/java/app/parallellingvo/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/language`

- Handler: `api_translate_language` — `output/google-play-preparation-20261021/sources/app/routes.py:5213`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/status`

- Handler: `auth_status` — `output/google-play-preparation-20261021/sources/app/routes.py:5257`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/logout`

- Handler: `auth_logout` — `output/google-play-preparation-20261021/sources/app/routes.py:5276`.
- Назначение: Project file: routes.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/debug/whoami`

- Handler: `api_debug_whoami` — `output/google-play-preparation-20261021/sources/app/routes.py:5295`.
- Назначение: Project file: routes.py.
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
