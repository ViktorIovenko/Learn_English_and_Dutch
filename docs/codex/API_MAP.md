# API and Telegram map

Строки и методы получены автоматически. Авторизация эвристически определяется по коду около handler; перед изменением контракта откройте handler и соответствующий DTO/consumer.

## `GET /auth/google`

- Handler: `login` — `app/google_auth.py:339`.
- Назначение: Backend file: google_auth.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/google/callback`

- Handler: `callback` — `app/google_auth.py:360`.
- Назначение: Backend file: google_auth.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/auth/google/config`

- Handler: `android_google_config` — `app/google_auth.py:412`.
- Назначение: Return the public OAuth audience needed by Android Google Sign-In..
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/google/verify`

- Handler: `verify_android_token` — `app/google_auth.py:420`.
- Назначение: Android sends:  { "id_token": "<JWT from Google Sign-In SDK>" }
Returns:        { "ok": true, "user_id": "g_<sub>", "email": ..., "name": ... }.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/mcp/user`

- Handler: `mcp_user_status` — `app/mcp_api.py:126`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/mcp_connector.js`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/mcp/user`

- Handler: `mcp_user_toggle` — `app/mcp_api.py:182`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/mcp_connector.js`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/mcp/user/revoke-all`

- Handler: `mcp_user_revoke_all` — `app/mcp_api.py:202`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/mcp_connector.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/mcp`

- Handler: `mcp_admin_page` — `app/mcp_api.py:242`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /admin/mcp/revoke`

- Handler: `mcp_admin_revoke` — `app/mcp_api.py:288`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /.well-known/oauth-authorization-server`

- Handler: `oauth_metadata` — `app/mcp_api.py:310`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /oauth/register`

- Handler: `oauth_register` — `app/mcp_api.py:330`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET,POST /oauth/authorize`

- Handler: `oauth_authorize` — `app/mcp_api.py:406`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /oauth/token`

- Handler: `oauth_token` — `app/mcp_api.py:499`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /oauth/revoke`

- Handler: `oauth_revoke` — `app/mcp_api.py:552`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/internal/mcp/resolve`

- Handler: `internal_mcp_resolve` — `app/mcp_api.py:564`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/internal/mcp/execute`

- Handler: `internal_mcp_execute` — `app/mcp_api.py:575`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/internal/mcp/health`

- Handler: `internal_mcp_health` — `app/mcp_api.py:631`.
- Назначение: Backend file: mcp_api.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /sw.js`

- Handler: `service_worker` — `app/routes.py:1792`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /`

- Handler: `home` — `app/routes.py:1800`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`, `app/static/family_invite.js`, `app/static/learn.js`, `app/static/upload.js`, `app/templates/account_type.html`, `app/templates/family_link.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lessons`

- Handler: `lessons_alias` — `app/routes.py:1813`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lesson/<int:lesson_id>`

- Handler: `lesson_page` — `app/routes.py:1826`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /learn`

- Handler: `learn_page` — `app/routes.py:1831`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /difficult`

- Handler: `difficult_page` — `app/routes.py:1842`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /upload`

- Handler: `upload_page` — `app/routes.py:1847`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /word-database`

- Handler: `word_database_page` — `app/routes.py:1870`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /settings/mcp`

- Handler: `mcp_connector_page` — `app/routes.py:1880`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /settings`

- Handler: `settings_page` — `app/routes.py:1890`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /account-type`

- Handler: `account_type_page` — `app/routes.py:1900`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /.well-known/assetlinks.json`

- Handler: `android_app_links` — `app/routes.py:1909`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /family/connect`

- Handler: `family_link_page` — `app/routes.py:1914`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /family/link`

- Handler: `family_link_page` — `app/routes.py:1915`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /parent`

- Handler: `parent_dashboard_page` — `app/routes.py:1947`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /subscription`

- Handler: `subscription_page` — `app/routes.py:1956`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/subscription.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/users`

- Handler: `admin_users_page` — `app/routes.py:1961`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /share/<token>`

- Handler: `share_page` — `app/routes.py:2153`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/create`

- Handler: `api_share_create` — `app/routes.py:2217`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/share/source_lessons`

- Handler: `api_share_source_lessons` — `app/routes.py:2296`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/assign_child`

- Handler: `api_share_assign_child` — `app/routes.py:2373`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/<token>/import`

- Handler: `api_share_import` — `app/routes.py:2496`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/import-words`

- Handler: `api_import_words` — `app/routes.py:2600`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words`

- Handler: `api_get_words` — `app/routes.py:2617`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/static/upload.js`, `app/static/word_database.js`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/words/<int:word_id>`

- Handler: `api_update_word` — `app/routes.py:2677`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/words/<int:word_id>`

- Handler: `api_delete_word` — `app/routes.py:2811`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/nl-list`

- Handler: `api_words_nl_list` — `app/routes.py:2825`.
- Назначение: Lightweight list of all NL words for the current user (used for deduplication)..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/duplicates`

- Handler: `api_words_duplicates` — `app/routes.py:2839`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/word_database.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/parse-file`

- Handler: `api_parse_file` — `app/routes.py:2877`.
- Назначение: Parse uploaded CSV or Excel file, return rows as JSON for preview..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android`

- Handler: `login_android` — `app/routes.py:2977`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android_token`

- Handler: `login_android_token` — `app/routes.py:2988`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_link`

- Handler: `login_link` — `app/routes.py:3000`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /android-auth`

- Handler: `android_auth_redirect` — `app/routes.py:3012`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_webapp`

- Handler: `login_webapp` — `app/routes.py:3025`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/me`

- Handler: `api_me` — `app/routes.py:3057`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/templates/admin_users.html`, `app/templates/base.html`, `app/templates/upload.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/account/type`

- Handler: `api_account_type_save` — `app/routes.py:3101`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: telegram init data/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/account_type.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family`

- Handler: `api_family_status` — `app/routes.py:3129`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`, `app/templates/family_link.html`, `app/templates/parent_dashboard.html`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/learning/streak`

- Handler: `api_learning_streak` — `app/routes.py:3137`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/dashboard`

- Handler: `api_family_dashboard` — `app/routes.py:3155`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/parent_dashboard.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/children/<child_user_id>/lesson-words`

- Handler: `api_family_child_lesson_words` — `app/routes.py:3181`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/family/children/<child_user_id>/priority-lesson`

- Handler: `api_family_set_priority_lesson` — `app/routes.py:3236`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-code`

- Handler: `api_family_pairing_code` — `app/routes.py:3323`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/invitation/preview`

- Handler: `api_family_invitation` — `app/routes.py:3334`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/invitation/accept`

- Handler: `api_family_invitation` — `app/routes.py:3335`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/family_invite.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-qr.png`

- Handler: `api_family_pairing_qr` — `app/routes.py:3359`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/invite-code`

- Handler: `api_family_invite_code` — `app/routes.py:3401`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/invite-qr.png`

- Handler: `api_family_invite_qr` — `app/routes.py:3412`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/join`

- Handler: `api_family_join` — `app/routes.py:3439`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/link`

- Handler: `api_family_link` — `app/routes.py:3456`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/family/children/<child_user_id>`

- Handler: `api_family_unlink_child` — `app/routes.py:3517`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/subscription`

- Handler: `api_subscription_get` — `app/routes.py:3536`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/subscription.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/subscription/verify_purchase`

- Handler: `api_verify_purchase` — `app/routes.py:3566`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/language-options`

- Handler: `api_language_options` — `app/routes.py:3610`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages`

- Handler: `api_user_languages_get` — `app/routes.py:3617`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user-languages`

- Handler: `api_user_languages_save` — `app/routes.py:3633`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages/missing-words`

- Handler: `api_user_languages_missing_words` — `app/routes.py:3674`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ui-language`

- Handler: `api_ui_language_get` — `app/routes.py:3712`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/ui-language`

- Handler: `api_ui_language_save` — `app/routes.py:3721`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons`

- Handler: `api_lessons` — `app/routes.py:3843`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user_lessons`

- Handler: `api_user_lessons` — `app/routes.py:3874`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user_lessons/rename`

- Handler: `api_user_lessons_rename` — `app/routes.py:3884`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user_lessons/delete`

- Handler: `api_user_lessons_delete` — `app/routes.py:3999`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/lessons/set_hidden`

- Handler: `api_lessons_set_hidden` — `app/routes.py:4073`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lesson_words`

- Handler: `api_lesson_words_by_title` — `app/routes.py:4087`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`, `app/templates/learn.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/child-learning/status`

- Handler: `api_child_learning_status` — `app/routes.py:4131`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/daily-goal`

- Handler: `api_daily_goal_get` — `app/routes.py:4160`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/daily-goal`

- Handler: `api_daily_goal_save` — `app/routes.py:4168`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons/<int:lesson_id>/words`

- Handler: `api_lesson_words` — `app/routes.py:4193`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/difficult_words_user`

- Handler: `api_difficult_words_user` — `app/routes.py:4232`.
- Назначение: Персональный список:
  - слова из words, у которых user_word_flags.difficult=1 для текущего пользователя
  (кастомные слова удалены).
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/difficult/user_set`

- Handler: `api_difficult_user_set` — `app/routes.py:4273`.
- Назначение: Body: {word_id: int, difficult: 0|1}.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/progress/sync`

- Handler: `api_progress_sync` — `app/routes.py:4314`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/sync.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/sync/updates`

- Handler: `api_sync_updates` — `app/routes.py:4375`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/audio/ensure`

- Handler: `api_audio_ensure` — `app/routes.py:4469`.
- Назначение: Body: { ids: [int,...], langs: ["nl","en","ru"] }
Для каждого id создаёт недостающие MP3, обновляет ссылки в words.audio_*.
Возвращает { ok: true, items: [ {ok,id,nl,en,ru}, ... ] }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/next_lesson`

- Handler: `api_next_lesson` — `app/routes.py:4491`.
- Назначение: Возвращает следующий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, next: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/prev_lesson`

- Handler: `api_prev_lesson` — `app/routes.py:4509`.
- Назначение: Возвращает предыдущий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, prev: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/users`

- Handler: `api_admin_users` — `app/routes.py:4551`.
- Назначение: Список всех пользователей с их статусом подписки. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/limit`

- Handler: `api_admin_set_tts_usage_limit` — `app/routes.py:4644`.
- Назначение: Sets the global or per-user monthly TTS character limit..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/reset`

- Handler: `api_admin_reset_tts_usage` — `app/routes.py:4687`.
- Назначение: Сбрасывает месячный Google TTS-счётчик одного пользователя или всех пользователей..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/translation_usage/reset`

- Handler: `api_admin_reset_translation_usage` — `app/routes.py:4723`.
- Назначение: Сбрасывает накопительную статистику токенов одного пользователя или всех..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/grant_access`

- Handler: `api_admin_grant_access` — `app/routes.py:4754`.
- Назначение: Выдаёт пользователю безлимитный доступ (100 лет). Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/revoke_access`

- Handler: `api_admin_revoke_access` — `app/routes.py:4787`.
- Назначение: Отзывает безлимитный доступ — переводит пользователя в истёкший trial. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/unlink_family`

- Handler: `api_admin_unlink_family` — `app/routes.py:4813`.
- Назначение: Remove one exact adult-child relationship. Only for admins..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/delete_user`

- Handler: `api_admin_delete_user` — `app/routes.py:4845`.
- Назначение: Полностью удаляет пользователя и его данные, чтобы он мог зарегистрироваться заново..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ai/status`

- Handler: `api_ai_status` — `app/routes.py:4942`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/word`

- Handler: `api_translate_word` — `app/routes.py:4950`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/static/word_database.js`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/generate/topic`

- Handler: `api_generate_topic` — `app/routes.py:4983`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/language`

- Handler: `api_translate_language` — `app/routes.py:5016`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/status`

- Handler: `auth_status` — `app/routes.py:5059`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/logout`

- Handler: `auth_logout` — `app/routes.py:5078`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/debug/whoami`

- Handler: `api_debug_whoami` — `app/routes.py:5097`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/telegram`

- Handler: `login` — `app/telegram_oauth.py:119`.
- Назначение: Backend file: telegram_oauth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/telegram/callback`

- Handler: `callback` — `app/telegram_oauth.py:135`.
- Назначение: Backend file: telegram_oauth.py.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

# Telegram handlers

- `command /start` → `start_cmd` (`bot/auth.py:971`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /open` → `open_cmd` (`bot/auth.py:972`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /family` → `family_cmd` (`bot/auth.py:973`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `callback r"^onboarding:(?:language|language_keep|language_change|account` → `onboarding_callback` (`bot/auth.py:974`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `callback r"^family_link:(?:confirm|cancel` → `family_link_callback` (`bot/auth.py:978`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `callback r"^family_join:(?:confirm|cancel` → `family_join_callback` (`bot/auth.py:982`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(learn_words_pattern)` → `open_cmd` (`bot/auth.py:989`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.TEXT & (~filters.COMMAND) & exclude_import_btns` → `on_text` (`bot/auth.py:993`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /reminder_now` → `_cmd_reminder_now` (`bot/reminder.py:264`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /upload_words` → `cmd_upload_words` (`bot/upload.py:435`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(upload_words_pattern)` → `cmd_upload_words` (`bot/upload.py:436`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(r"^(Добавить слова|Импортировать слова)$")` → `cmd_upload_words` (`bot/upload.py:437`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Document.ALL & (~filters.COMMAND)` → `on_csv_document` (`bot/upload.py:438`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(r"(?i)^(импортировать как есть)$")` → `on_confirm_import_all` (`bot/upload.py:439`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(r"(?i)^(отменить импорт)$")` → `on_cancel_import` (`bot/upload.py:440`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
