# API and Telegram map

Строки и методы получены автоматически. Авторизация эвристически определяется по коду около handler; перед изменением контракта откройте handler и соответствующий DTO/consumer.

## `GET /auth/google`

- Handler: `login` — `app/google_auth.py:93`.
- Назначение: Backend file: google_auth.py.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /auth/google/callback`

- Handler: `callback` — `app/google_auth.py:103`.
- Назначение: Backend file: google_auth.py.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/google/verify`

- Handler: `verify_android_token` — `app/google_auth.py:132`.
- Назначение: Android sends:  { "id_token": "<JWT from Google Sign-In SDK>" }
Returns:        { "ok": true, "user_id": "g_<sub>", "email": ..., "name": ... }.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /sw.js`

- Handler: `service_worker` — `app/routes.py:1511`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /`

- Handler: `home` — `app/routes.py:1519`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`, `app/static/learn.js`, `app/static/sync.js`, `app/templates/account_type.html`, `app/templates/family_link.html`, `app/templates/parent_dashboard.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lessons`

- Handler: `lessons_alias` — `app/routes.py:1531`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /lesson/<int:lesson_id>`

- Handler: `lesson_page` — `app/routes.py:1543`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /learn`

- Handler: `learn_page` — `app/routes.py:1548`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /difficult`

- Handler: `difficult_page` — `app/routes.py:1559`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /upload`

- Handler: `upload_page` — `app/routes.py:1564`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /settings`

- Handler: `settings_page` — `app/routes.py:1581`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: public or handler-validated.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /account-type`

- Handler: `account_type_page` — `app/routes.py:1591`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /family/link`

- Handler: `family_link_page` — `app/routes.py:1600`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /parent`

- Handler: `parent_dashboard_page` — `app/routes.py:1626`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /subscription`

- Handler: `subscription_page` — `app/routes.py:1635`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/subscription.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /admin/users`

- Handler: `admin_users_page` — `app/routes.py:1640`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /share/<token>`

- Handler: `share_page` — `app/routes.py:1832`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/create`

- Handler: `api_share_create` — `app/routes.py:1896`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/share/source_lessons`

- Handler: `api_share_source_lessons` — `app/routes.py:1975`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/assign_child`

- Handler: `api_share_assign_child` — `app/routes.py:2043`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/share/<token>/import`

- Handler: `api_share_import` — `app/routes.py:2138`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/import-words`

- Handler: `api_import_words` — `app/routes.py:2242`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words`

- Handler: `api_get_words` — `app/routes.py:2297`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/words/<int:word_id>`

- Handler: `api_update_word` — `app/routes.py:2355`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/words/<int:word_id>`

- Handler: `api_delete_word` — `app/routes.py:2443`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/nl-list`

- Handler: `api_words_nl_list` — `app/routes.py:2457`.
- Назначение: Lightweight list of all NL words for the current user (used for deduplication)..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/words/duplicates`

- Handler: `api_words_duplicates` — `app/routes.py:2471`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/parse-file`

- Handler: `api_parse_file` — `app/routes.py:2509`.
- Назначение: Parse uploaded CSV or Excel file, return rows as JSON for preview..
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android`

- Handler: `login_android` — `app/routes.py:2609`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_android_token`

- Handler: `login_android_token` — `app/routes.py:2620`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /android-auth`

- Handler: `android_auth_redirect` — `app/routes.py:2632`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/auth/login_webapp`

- Handler: `login_webapp` — `app/routes.py:2643`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/me`

- Handler: `api_me` — `app/routes.py:2669`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`, `app/templates/admin_users.html`, `app/templates/base.html`, `app/templates/upload.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/account/type`

- Handler: `api_account_type_save` — `app/routes.py:2713`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: telegram init data/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/account_type.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family`

- Handler: `api_family_status` — `app/routes.py:2741`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`, `app/templates/parent_dashboard.html`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/learning/streak`

- Handler: `api_learning_streak` — `app/routes.py:2749`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/dashboard`

- Handler: `api_family_dashboard` — `app/routes.py:2767`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/parent_dashboard.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `PUT /api/family/children/<child_user_id>/priority-lesson`

- Handler: `api_family_set_priority_lesson` — `app/routes.py:2792`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-code`

- Handler: `api_family_pairing_code` — `app/routes.py:2878`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/family/pairing-qr.png`

- Handler: `api_family_pairing_qr` — `app/routes.py:2889`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: telegram init data/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/family/link`

- Handler: `api_family_link` — `app/routes.py:2919`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/family_link.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `DELETE /api/family/children/<child_user_id>`

- Handler: `api_family_unlink_child` — `app/routes.py:2975`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/subscription`

- Handler: `api_subscription_get` — `app/routes.py:2992`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/subscription.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/subscription/verify_purchase`

- Handler: `api_verify_purchase` — `app/routes.py:3022`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/language-options`

- Handler: `api_language_options` — `app/routes.py:3089`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages`

- Handler: `api_user_languages_get` — `app/routes.py:3096`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user-languages`

- Handler: `api_user_languages_save` — `app/routes.py:3112`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user-languages/missing-words`

- Handler: `api_user_languages_missing_words` — `app/routes.py:3153`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ui-language`

- Handler: `api_ui_language_get` — `app/routes.py:3191`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/ui-language`

- Handler: `api_ui_language_save` — `app/routes.py:3200`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons`

- Handler: `api_lessons` — `app/routes.py:3310`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/user_lessons`

- Handler: `api_user_lessons` — `app/routes.py:3340`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/user_lessons/delete`

- Handler: `api_user_lessons_delete` — `app/routes.py:3350`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/lessons/set_hidden`

- Handler: `api_lessons_set_hidden` — `app/routes.py:3420`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/learn.js`, `app/templates/index.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lesson_words`

- Handler: `api_lesson_words_by_title` — `app/routes.py:3434`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/index.html`, `app/templates/learn.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/child-learning/status`

- Handler: `api_child_learning_status` — `app/routes.py:3473`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/daily-goal`

- Handler: `api_daily_goal_get` — `app/routes.py:3502`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/daily-goal`

- Handler: `api_daily_goal_save` — `app/routes.py:3510`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/templates/base.html`, `app/templates/settings.html`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/lessons/<int:lesson_id>/words`

- Handler: `api_lesson_words` — `app/routes.py:3535`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/difficult_words_user`

- Handler: `api_difficult_words_user` — `app/routes.py:3571`.
- Назначение: Персональный список:
  - слова из words, у которых user_word_flags.difficult=1 для текущего пользователя
  (кастомные слова удалены).
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/difficult/user_set`

- Handler: `api_difficult_user_set` — `app/routes.py:3607`.
- Назначение: Body: {word_id: int, difficult: 0|1}.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/progress/sync`

- Handler: `api_progress_sync` — `app/routes.py:3645`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/sync.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/sync/updates`

- Handler: `api_sync_updates` — `app/routes.py:3705`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/audio/ensure`

- Handler: `api_audio_ensure` — `app/routes.py:3799`.
- Назначение: Body: { ids: [int,...], langs: ["nl","en","ru"] }
Для каждого id создаёт недостающие MP3, обновляет ссылки в words.audio_*.
Возвращает { ok: true, items: [ {ok,id,nl,en,ru}, ... ] }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/audio_worker.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/next_lesson`

- Handler: `api_next_lesson` — `app/routes.py:3821`.
- Назначение: Возвращает следующий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, next: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/prev_lesson`

- Handler: `api_prev_lesson` — `app/routes.py:3839`.
- Назначение: Возвращает предыдущий ВИДИМЫЙ урок относительно текущего названия.
Query: ?current=<lesson_title>
Ответ: { ok: true, prev: "<lesson>" } или { ok: false }.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/admin/users`

- Handler: `api_admin_users` — `app/routes.py:3881`.
- Назначение: Список всех пользователей с их статусом подписки. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/limit`

- Handler: `api_admin_set_tts_usage_limit` — `app/routes.py:3974`.
- Назначение: Sets the global or per-user monthly TTS character limit..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/tts_usage/reset`

- Handler: `api_admin_reset_tts_usage` — `app/routes.py:4017`.
- Назначение: Сбрасывает месячный Google TTS-счётчик одного пользователя или всех пользователей..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/translation_usage/reset`

- Handler: `api_admin_reset_translation_usage` — `app/routes.py:4053`.
- Назначение: Сбрасывает накопительную статистику токенов одного пользователя или всех..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/grant_access`

- Handler: `api_admin_grant_access` — `app/routes.py:4084`.
- Назначение: Выдаёт пользователю безлимитный доступ (100 лет). Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/revoke_access`

- Handler: `api_admin_revoke_access` — `app/routes.py:4117`.
- Назначение: Отзывает безлимитный доступ — переводит пользователя в истёкший trial. Только для админов..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/unlink_family`

- Handler: `api_admin_unlink_family` — `app/routes.py:4143`.
- Назначение: Remove one exact adult-child relationship. Only for admins..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/admin/delete_user`

- Handler: `api_admin_delete_user` — `app/routes.py:4173`.
- Назначение: Полностью удаляет пользователя и его данные, чтобы он мог зарегистрироваться заново..
- Авторизация: admin.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/ai/status`

- Handler: `api_ai_status` — `app/routes.py:4263`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/word`

- Handler: `api_translate_word` — `app/routes.py:4271`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/generate/topic`

- Handler: `api_generate_topic` — `app/routes.py:4300`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt`.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `POST /api/translate/language`

- Handler: `api_translate_language` — `app/routes.py:4332`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: authenticated user.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: `app/static/upload.js`.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

## `GET /api/debug/whoami`

- Handler: `api_debug_whoami` — `app/routes.py:4364`.
- Назначение: Flask pages, API, sync, database and audio orchestration.
- Авторизация: android headers/session.
- Request/response: определяется handler; JSON-схема не формализована Flask-декоратором, поэтому перед изменением читать функцию целиком.
- Frontend consumers: не найдены статически.
- Android consumers: нет подтверждённого Retrofit соответствия.
- Риск: изменения URL, метода, auth headers и JSON-полей требуют синхронной проверки Web/Telegram Mini App/Android.

# Telegram handlers

- `command /start` → `start_cmd` (`bot/auth.py:797`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /open` → `open_cmd` (`bot/auth.py:798`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /family` → `family_cmd` (`bot/auth.py:799`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `callback r"^onboarding:(?:language|language_keep|language_change|account` → `onboarding_callback` (`bot/auth.py:800`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `callback r"^family_link:(?:confirm|cancel` → `family_link_callback` (`bot/auth.py:804`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(learn_words_pattern)` → `open_cmd` (`bot/auth.py:811`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.TEXT & (~filters.COMMAND) & exclude_import_btns` → `on_text` (`bot/auth.py:815`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /reminder_now` → `_cmd_reminder_now` (`bot/reminder.py:266`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `command /upload_words` → `cmd_upload_words` (`bot/upload.py:460`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(upload_words_pattern)` → `cmd_upload_words` (`bot/upload.py:461`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(r"^(Добавить слова|Импортировать слова)$")` → `cmd_upload_words` (`bot/upload.py:462`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Document.ALL & (~filters.COMMAND)` → `on_csv_document` (`bot/upload.py:463`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(r"(?i)^(импортировать как есть)$")` → `on_confirm_import_all` (`bot/upload.py:464`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
- `message filters.Regex(r"(?i)^(отменить импорт)$")` → `on_cancel_import` (`bot/upload.py:465`); сценарий: Telegram handler; таблицы смотреть через `table`/`query`.
