# Database map

Схема ниже извлечена из SQL в исходниках и production `sqlite_master`; строки пользователей не читаются.

Создание/миграции распределены между `run.py`, `db_init.py`, `app/routes.py`, `app/models.py`, `bot/db.py`, `bot/auth.py` и специализированными модулями. Это известное дублирование; менять схему следует только после проверки всех владельцев.

## `account_revocations`

- local: `app/account_privacy.py`:19.
- Колонки: `subject_hash` TEXT PRIMARY KEY, `generation` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_privacy.py:19` (migration, local), `app/account_privacy.py:24` (read, local), `app/account_privacy.py:26` (read, local), `app/account_privacy.py:99` (insert, local), `tests/test_android_auth.py:88` (insert, local).
- Связанные API файла-владельца: `/privacy`, `/account/delete`, `/api/account/deletion-challenge`, `/api/account/delete`.
- Telegram handlers файла-владельца: нет прямой связи.

## `ad_advertisers`

- local: `app/advertising/store.py`:96.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `awin_id` INTEGER UNIQUE, `name` TEXT NOT NULL, `membership_status` TEXT NOT NULL DEFAULT 'manual', `enabled` INTEGER NOT NULL DEFAULT 0, `countries` TEXT NOT NULL DEFAULT '[]', `languages` TEXT NOT NULL DEFAULT '[]', `topics` TEXT NOT NULL DEFAULT '[]', `primary_region` TEXT NOT NULL DEFAULT '', `valid_domains` TEXT NOT NULL DEFAULT '[]', `logo_url` TEXT NOT NULL DEFAULT '', `notes` TEXT NOT NULL DEFAULT '', `synced_at` INTEGER NOT NULL DEFAULT 0, `created_at` INTEGER NOT NULL DEFAULT 0.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/advertising/store.py:96` (migration, local), `app/advertising/store.py:114` (delete, local), `app/advertising/store.py:283` (read, local), `app/advertising/store.py:289` (read, local), `app/advertising/store.py:308` (update, local), `app/advertising/store.py:315` (insert, local), `app/advertising/store.py:331` (insert, local), `app/advertising/store.py:341` (read, local), `app/advertising/store.py:348` (update, local), `app/advertising/store.py:446` (read, local), `app/advertising/store.py:504` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `ad_api_log`

- local: `app/advertising/store.py`:156.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `at` INTEGER NOT NULL, `operation` TEXT NOT NULL, `http_status` INTEGER NOT NULL DEFAULT 0, `ok` INTEGER NOT NULL DEFAULT 0, `message` TEXT NOT NULL DEFAULT ''.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/advertising/store.py:156` (migration, local), `app/advertising/store.py:516` (insert, local), `app/advertising/store.py:518` (delete, local), `app/advertising/store.py:524` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `ad_consent`

- local: `app/advertising/store.py`:149.
- Колонки: `user_id` TEXT NOT NULL, `platform` TEXT NOT NULL, `status` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- local: `tests/test_play_release.py`:255.
- Колонки: `user_id` TEXT, `choice` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/advertising/store.py:149` (migration, local), `app/advertising/store.py:532` (read, local), `app/advertising/store.py:540` (insert, local), `docs/codex/ADVERTISING.md:23` (update, local), `tests/test_play_release.py:255` (migration, local), `tests/test_play_release.py:256` (insert, local), `tests/test_play_release.py:261` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `ad_creatives`

- local: `app/advertising/store.py`:112.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `advertiser_id` INTEGER NOT NULL REFERENCES ad_advertisers(id.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/advertising/store.py:112` (migration, local), `app/advertising/store.py:382` (read, local), `app/advertising/store.py:388` (read, local), `app/advertising/store.py:409` (update, local), `app/advertising/store.py:416` (migration, local), `app/advertising/store.py:426` (update, local), `app/advertising/store.py:433` (update, local), `app/advertising/store.py:446` (read, local), `app/advertising/store.py:484` (read, local), `app/advertising/store.py:503` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `ad_placements`

- local: `app/advertising/store.py`:87.
- Колонки: `key` TEXT PRIMARY KEY, `page` TEXT NOT NULL, `label` TEXT NOT NULL DEFAULT '', `enabled` INTEGER NOT NULL DEFAULT 0, `priority` INTEGER NOT NULL DEFAULT 50, `sizes` TEXT NOT NULL DEFAULT '{}', `builtin` INTEGER NOT NULL DEFAULT 0.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/advertising/store.py:87` (migration, local), `app/advertising/store.py:171` (insert, local), `app/advertising/store.py:232` (read, local), `app/advertising/store.py:245` (insert, local), `app/advertising/store.py:256` (delete, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `ad_settings`

- local: `app/advertising/store.py`:82.
- Колонки: `id` INTEGER PRIMARY KEY CHECK (id = 1.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/advertising/store.py:82` (migration, local), `app/advertising/store.py:166` (insert, local), `app/advertising/store.py:201` (read, local), `app/advertising/store.py:211` (update, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `ad_stats`

- local: `app/advertising/store.py`:137.
- Колонки: `day` TEXT NOT NULL, `placement` TEXT NOT NULL, `creative_id` INTEGER NOT NULL, `device` TEXT NOT NULL, `country` TEXT NOT NULL, `event` TEXT NOT NULL, `count` INTEGER NOT NULL DEFAULT 0.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/advertising/store.py:137` (migration, local), `app/advertising/store.py:470` (insert, local), `app/advertising/store.py:484` (read, local), `app/advertising/store.py:502` (read, local), `tests/test_advertising.py:545` (read, local), `tests/test_advertising.py:546` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `ai_gateway_settings`

- local: `app/ai_gateway.py`:106.
- Колонки: `id` INTEGER PRIMARY KEY CHECK(id=1.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/ai_gateway.py:49` (read, local), `app/ai_gateway.py:106` (migration, local), `app/ai_gateway.py:121` (insert, local), `tests/test_ai_gateway.py:74` (read, local).
- Связанные API файла-владельца: `/admin/ai`, `/api/admin/ai/settings`.
- Telegram handlers файла-владельца: нет прямой связи.

## `android_auth_flows`

- local: `app/android_auth.py`:30.
- Колонки: `id` TEXT PRIMARY KEY, `challenge` TEXT NOT NULL, `provider` TEXT NOT NULL, `created` INTEGER NOT NULL, `ip_hash` TEXT NOT NULL, `user_id` TEXT, `version` TEXT, `error` TEXT, `delivered` INTEGER.
- Индексы: `android_auth_ip` (ip_hash,created), `android_native_token` (native_token_hash).
- Чтение/запись/миграции: `app/android_auth.py:30` (migration, local), `app/android_auth.py:34` (migration, local), `app/android_auth.py:35` (read, local), `app/android_auth.py:38` (migration, local), `app/android_auth.py:39` (migration, local), `app/android_auth.py:108` (migration, local), `app/android_auth.py:115` (update, local), `app/android_auth.py:137` (migration, local), `app/android_auth.py:143` (update, local), `app/android_auth.py:173` (migration, local), `app/android_auth.py:174` (migration, local), `app/android_auth.py:182` (migration, local), `app/android_auth.py:248` (read, local), `app/android_auth.py:254` (read, local), `app/android_auth.py:276` (update, local), `app/android_auth.py:297` (read, local), `app/android_auth.py:322` (update, local), `app/android_auth.py:324` (read, local), `app/android_auth.py:334` (update, local), `app/email_auth.py:227` (read, local), `app/email_auth.py:279` (update, local), `app/email_auth.py:282` (update, local), `app/email_auth.py:314` (update, local), `app/email_auth.py:381` (update, local), `tests/test_android_auth.py:116` (update, local), `tests/test_android_auth.py:136` (migration, local), `tests/test_telegram_native.py:124` (update, local), `tests/test_telegram_native.py:127` (migration, local), `tests/test_telegram_native.py:135` (update, local), `tests/test_telegram_native.py:139` (update, local).
- Связанные API файла-владельца: `/api/auth/android/browser-link`, `/auth/android/browser`, `/api/auth/android/browser-session`, `/api/account/identities`, `/api/auth/android/start`, `/api/auth/telegram/native`, `/api/auth/android/exchange`, `/auth/android/return`.
- Telegram handlers файла-владельца: нет прямой связи.

## `android_browser_links`

- local: `app/android_auth.py`:40.
- Колонки: `ticket_hash` TEXT PRIMARY KEY, `user_id` TEXT NOT NULL, `expires` INTEGER NOT NULL, `version` TEXT, `generation` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/android_auth.py:40` (migration, local), `app/android_auth.py:57` (delete, local), `app/android_auth.py:58` (insert, local), `app/android_auth.py:84` (read, local), `app/android_auth.py:92` (delete, local), `tests/test_android_auth.py:78` (update, local).
- Связанные API файла-владельца: `/api/auth/android/browser-link`, `/auth/android/browser`, `/api/auth/android/browser-session`, `/api/account/identities`, `/api/auth/android/start`, `/api/auth/telegram/native`, `/api/auth/android/exchange`, `/auth/android/return`.
- Telegram handlers файла-владельца: нет прямой связи.

## `android_contracts`

- local: `tools/project_kb.py`:86.
- Колонки: `id` INTEGER PRIMARY KEY, `endpoint` TEXT, `http_method` TEXT, `android_file` TEXT, `android_symbol` TEXT, `request_model` TEXT, `response_model` TEXT, `auth_headers_json` TEXT, `backend_file` TEXT, `backend_handler` TEXT, `status` TEXT, `notes` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:86` (read, local), `tools/project_kb.py:86` (migration, local), `tools/project_kb.py:421` (insert, local), `tools/project_kb.py:427` (read, local), `tools/project_kb.py:430` (update, local), `tools/project_kb.py:432` (update, local), `tools/project_kb.py:452` (delete, local), `tools/project_kb.py:470` (read, local), `tools/project_kb.py:513` (read, local), `tools/project_kb.py:529` (read, local), `tools/project_kb.py:566` (read, local), `tools/project_kb.py:581` (delete, local), `tools/project_kb.py:717` (read, local), `tools/project_kb.py:828` (read, local), `tools/project_kb.py:835` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `app_schema_migrations`

- local: `app/account_types.py`:89.
- Колонки: `name` TEXT PRIMARY KEY, `applied_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `name` TEXT PRIMARY KEY, `applied_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_types.py:89` (migration, local), `app/account_types.py:95` (read, local), `app/account_types.py:110` (insert, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `audio_assets`

- local: `app/audio_gen.py`:153.
- Колонки: `cache_key` TEXT PRIMARY KEY, `request_json` TEXT NOT NULL, `url` TEXT NOT NULL, `file_hash` TEXT NOT NULL, `created_at` INTEGER NOT NULL, `last_used_at` INTEGER NOT NULL, `provenance` TEXT NOT NULL DEFAULT 'generated'.
- Индексы: `idx_audio_assets_url` (url).
- Чтение/запись/миграции: `app/audio_gen.py:153` (migration, local), `app/audio_gen.py:157` (migration, local), `app/audio_gen.py:179` (read, local), `app/audio_gen.py:198` (read, local), `app/audio_gen.py:200` (read, local), `app/audio_gen.py:229` (read, local), `app/audio_gen.py:261` (insert, local), `app/audio_gen.py:264` (update, local), `app/audio_gen.py:289` (read, local), `app/audio_gen.py:294` (read, local), `app/audio_gen.py:301` (read, local), `app/audio_gen.py:306` (delete, local), `tests/test_content_pipeline.py:348` (update, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `audio_legacy_rejections`

- local: `app/audio_gen.py`:158.
- Колонки: `url` TEXT PRIMARY KEY, `reason` TEXT NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/audio_gen.py:158` (migration, local), `app/audio_gen.py:177` (read, local), `app/audio_gen.py:192` (insert, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `auth_identities`

- local: `app/account_types.py`:17.
- Колонки: `provider` TEXT NOT NULL, `external_id` TEXT NOT NULL, `user_id` TEXT NOT NULL, `email` TEXT, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_db_migrations.py`:21.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT NOT NULL, `provider` TEXT NOT NULL, `subject` TEXT NOT NULL, `provider_user_id` TEXT, `email` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_google_account_link.py`:56.
- Колонки: `provider` TEXT NOT NULL, `external_id` TEXT NOT NULL, `user_id` TEXT NOT NULL, `email` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_registration_notifications.py`:33.
- Колонки: `provider` TEXT, `external_id` TEXT, `user_id` TEXT, `email` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_linking.py:12` (read, local), `app/account_linking.py:23` (read, local), `app/account_linking.py:36` (read, local), `app/account_linking.py:39` (read, local), `app/account_linking.py:43` (read, local), `app/account_linking.py:48` (read, local), `app/account_linking.py:53` (insert, local), `app/account_types.py:13` (read, local), `app/account_types.py:17` (migration, local), `app/account_types.py:29` (read, local), `app/account_types.py:33` (read, local), `app/account_types.py:37` (read, local), `app/account_types.py:44` (read, local), `app/account_types.py:64` (read, local), `app/account_types.py:69` (read, local), `app/account_types.py:71` (migration, local), `app/account_types.py:75` (read, local), `app/android_auth.py:130` (read, local), `app/android_auth.py:230` (insert, local), `app/email_auth.py:188` (read, local), `app/email_auth.py:322` (read, local), `app/email_auth.py:325` (read, local), `app/email_auth.py:331` (insert, local), `app/google_auth.py:51` (read, local), `app/google_auth.py:55` (read, local), `app/google_auth.py:59` (read, local), `app/google_auth.py:154` (read, local), `app/google_auth.py:165` (update, local), `app/google_auth.py:171` (read, local), `app/google_auth.py:183` (read, local).
- Связанные API файла-владельца: `/auth/telegram`, `/auth/telegram/callback`, `/auth/google`, `/auth/google/callback`, `/api/auth/google/config`, `/api/auth/google/verify`, `/api/auth/google/link`, `/api/auth/android/browser-link`, `/auth/android/browser`, `/api/auth/android/browser-session`, `/api/account/identities`, `/api/auth/android/start`, `/api/auth/telegram/native`, `/api/auth/android/exchange`, `/auth/android/return`, `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`.
- Telegram handlers файла-владельца: нет прямой связи.

## `auth_identities__canonical_new`

- local: `app/account_types.py`:49.
- Колонки: `provider` TEXT NOT NULL, `external_id` TEXT NOT NULL, `user_id` TEXT NOT NULL, `email` TEXT, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_types.py:47` (read, local), `app/account_types.py:49` (migration, local), `app/account_types.py:60` (insert, local), `app/account_types.py:71` (migration, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `child_goal_notifications`

- local: `app/routes.py`:514.
- Колонки: `child_user_id` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `local_date` TEXT NOT NULL, `message_id` INTEGER, `sent_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `child_user_id` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `local_date` TEXT NOT NULL, `message_id` INTEGER, `sent_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/routes.py:514` (migration, local), `app/routes.py:525` (read, local), `app/routes.py:530` (migration, local), `app/routes.py:673` (read, local), `app/routes.py:681` (insert, local), `app/routes.py:700` (update, local), `app/routes.py:722` (delete, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `child_lesson_priorities`

- local: `app/routes.py`:873.
- Колонки: `child_user_id` TEXT PRIMARY KEY, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `child_user_id` TEXT PRIMARY KEY, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_service.py:1019` (read, local), `app/mcp_service.py:1031` (delete, local), `app/mcp_service.py:1112` (delete, local), `app/mcp_service.py:1145` (insert, local), `app/mcp_service.py:1166` (delete, local), `app/routes.py:873` (migration, local), `app/routes.py:902` (read, local), `app/routes.py:940` (read, local), `app/routes.py:972` (delete, local), `app/routes.py:3518` (read, local), `app/routes.py:3533` (insert, local), `app/routes.py:3548` (delete, local), `app/routes.py:4217` (update, local), `tests/test_family_accounts.py:879` (read, local), `tests/test_family_accounts.py:969` (insert, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `child_lesson_priority_history`

- local: `app/routes.py`:883.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `started_at` INTEGER NOT NULL, `ended_at` INTEGER.
- Индексы: `idx_child_priority_history_child_started` (child_user_id, started_at DESC).
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `started_at` INTEGER NOT NULL, `ended_at` INTEGER.
- Индексы: `idx_child_priority_history_child_started` (child_user_id, started_at DESC).
- Чтение/запись/миграции: `app/mcp_service.py:1028` (update, local), `app/mcp_service.py:1116` (update, local), `app/mcp_service.py:1150` (update, local), `app/mcp_service.py:1153` (read, local), `app/mcp_service.py:1155` (insert, local), `app/mcp_service.py:1165` (update, local), `app/routes.py:883` (migration, local), `app/routes.py:896` (read, local), `app/routes.py:899` (insert, local), `app/routes.py:905` (read, local), `app/routes.py:976` (update, local), `app/routes.py:1228` (read, local), `app/routes.py:3527` (update, local), `app/routes.py:3542` (insert, local), `app/routes.py:4221` (update, local), `tests/test_family_accounts.py:567` (update, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `content_examples`

- local: `app/content_service.py`:52.
- Колонки: `fingerprint` TEXT PRIMARY KEY, `variant_id` INTEGER NOT NULL REFERENCES content_variants(id.
- Индексы: `idx_content_examples_variant` (variant_id,level).
- Чтение/запись/миграции: `app/content_service.py:52` (migration, local), `app/content_service.py:55` (migration, local), `app/content_service.py:106` (insert, local), `app/content_service.py:173` (read, local), `app/content_service.py:194` (read, local), `tests/test_content_pipeline.py:102` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `content_import_requests`

- local: `app/content_service.py`:61.
- Колонки: `user_id` TEXT NOT NULL, `request_key` TEXT NOT NULL, `request_hash` TEXT NOT NULL, `response_json` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/content_service.py:61` (migration, local), `app/content_service.py:302` (read, local), `app/content_service.py:367` (insert, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `content_migrations`

- local: `app/content_service.py`:39.
- Колонки: `name` TEXT PRIMARY KEY, `completed_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/content_service.py:39` (migration, local), `app/content_service.py:71` (read, local), `app/content_service.py:80` (insert, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `content_pending`

- local: `app/content_service.py`:58.
- Колонки: `request_key` TEXT PRIMARY KEY, `operation` TEXT NOT NULL, `request_json` TEXT NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/content_service.py:58` (migration, local), `app/content_service.py:128` (delete, local), `app/content_service.py:145` (insert, local), `app/content_service.py:149` (insert, local), `tests/test_content_pipeline.py:107` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `content_results`

- local: `app/content_service.py`:56.
- Колонки: `request_key` TEXT PRIMARY KEY, `operation` TEXT NOT NULL, `result_json` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/content_service.py:56` (migration, local), `app/content_service.py:121` (read, local), `app/content_service.py:126` (insert, local), `app/content_service.py:133` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `content_terms`

- local: `app/content_service.py`:44.
- Колонки: `variant_id` INTEGER NOT NULL REFERENCES content_variants(id.
- Индексы: `idx_content_terms_lookup` (language,text_key).
- Чтение/запись/миграции: `app/content_service.py:44` (migration, local), `app/content_service.py:47` (migration, local), `app/content_service.py:95` (insert, local), `app/content_service.py:162` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `content_translations`

- local: `app/content_service.py`:48.
- Колонки: `fingerprint` TEXT PRIMARY KEY, `source_language` TEXT NOT NULL, `source_key` TEXT NOT NULL, `target_language` TEXT NOT NULL, `target_text` TEXT NOT NULL, `sense` TEXT NOT NULL, `context` TEXT NOT NULL, `source` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/content_service.py:48` (migration, local), `app/content_service.py:100` (insert, local), `tests/test_content_pipeline.py:96` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `content_variants`

- local: `app/content_service.py`:40.
- Колонки: `id` INTEGER PRIMARY KEY, `fingerprint` TEXT NOT NULL UNIQUE, `sense` TEXT NOT NULL, `context` TEXT NOT NULL, `words_json` TEXT NOT NULL, `source` TEXT NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/content_service.py:40` (migration, local), `app/content_service.py:45` (read, local), `app/content_service.py:53` (read, local), `app/content_service.py:91` (migration, local), `app/content_service.py:93` (read, local), `app/content_service.py:162` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `database_tables`

- local: `tools/project_kb.py`:76.
- Колонки: `id` INTEGER PRIMARY KEY, `table_name` TEXT, `defined_in` TEXT, `definition_line` INTEGER, `columns_json` TEXT, `indexes_json` TEXT, `environment` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:65` (read, local), `tools/project_kb.py:76` (migration, local), `tools/project_kb.py:375` (insert, local), `tools/project_kb.py:450` (read, local), `tools/project_kb.py:451` (delete, local), `tools/project_kb.py:494` (read, local), `tools/project_kb.py:497` (read, local), `tools/project_kb.py:557` (read, local), `tools/project_kb.py:566` (read, local), `tools/project_kb.py:580` (delete, local), `tools/project_kb.py:649` (delete, local), `tools/project_kb.py:657` (insert, local), `tools/project_kb.py:714` (read, local), `tools/project_kb.py:827` (read, local), `tools/project_kb.py:835` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `database_usage`

- local: `tools/project_kb.py`:80.
- Колонки: `id` INTEGER PRIMARY KEY, `table_name` TEXT, `file_path` TEXT, `symbol_name` TEXT, `operation` TEXT, `line_number` INTEGER, `source_scope` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tools/project_kb.py:80` (migration, local), `tools/project_kb.py:384` (insert, local), `tools/project_kb.py:450` (read, local), `tools/project_kb.py:502` (read, local), `tools/project_kb.py:504` (read, local), `tools/project_kb.py:505` (read, local), `tools/project_kb.py:580` (delete, local), `tools/project_kb.py:820` (read, local), `tools/project_kb.py:827` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `deployment_routes`

- local: `tools/project_kb.py`:96.
- Колонки: `id` INTEGER PRIMARY KEY, `server_name` TEXT, `public_path` TEXT, `proxy_target` TEXT, `nginx_config_path` TEXT, `backend_service` TEXT, `notes` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tools/project_kb.py:96` (migration, local), `tools/project_kb.py:642` (delete, local), `tools/project_kb.py:648` (insert, local), `tools/project_kb.py:720` (read, local), `tools/project_kb.py:831` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `docs`

- local: `tools/project_kb.py`:109.
- Колонки: `id` INTEGER PRIMARY KEY, `key` TEXT UNIQUE, `title` TEXT, `content` TEXT, `source_path` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tools/project_kb.py:28` (read, local), `tools/project_kb.py:109` (migration, local), `tools/project_kb.py:117` (read, local), `tools/project_kb.py:123` (read, local), `tools/project_kb.py:129` (read, local), `tools/project_kb.py:131` (read, local), `tools/project_kb.py:133` (read, local), `tools/project_kb.py:135` (read, local), `tools/project_kb.py:183` (read, local), `tools/project_kb.py:471` (read, local), `tools/project_kb.py:483` (insert, local), `tools/project_kb.py:788` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `email_auth_attempts`

- local: `app/email_auth.py`:44.
- Колонки: `email_hash` TEXT NOT NULL, `ip_hash` TEXT NOT NULL, `kind` TEXT NOT NULL, `created` INTEGER NOT NULL.
- Индексы: `email_attempt_address` (email_hash,kind,created), `email_attempt_ip` (ip_hash,kind,created).
- Чтение/запись/миграции: `app/account_privacy.py:60` (read, local), `app/account_privacy.py:62` (delete, local), `app/email_auth.py:44` (migration, local), `app/email_auth.py:47` (migration, local), `app/email_auth.py:48` (migration, local), `app/email_auth.py:105` (migration, local), `app/email_auth.py:106` (migration, local), `app/email_auth.py:107` (read, local), `app/email_auth.py:111` (migration, local), `app/email_auth.py:115` (insert, local), `tests/test_email_auth.py:56` (delete, local).
- Связанные API файла-владельца: `/privacy`, `/account/delete`, `/api/account/deletion-challenge`, `/api/account/delete`.
- Telegram handlers файла-владельца: нет прямой связи.

## `email_auth_credentials`

- local: `app/email_auth.py`:37.
- Колонки: `user_id` TEXT PRIMARY KEY, `email` TEXT NOT NULL UNIQUE COLLATE NOCASE, `password_hash` TEXT NOT NULL, `version` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- local: `tests/test_play_release.py`:249.
- Колонки: `user_id` TEXT, `email` TEXT, `version` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_linking.py:47` (read, local), `app/account_linking.py:51` (insert, local), `app/android_auth.py:131` (read, local), `app/android_auth.py:315` (read, local), `app/android_auth.py:329` (read, local), `app/auth_links.py:22` (read, local), `app/email_auth.py:37` (migration, local), `app/email_auth.py:187` (read, local), `app/email_auth.py:239` (read, local), `app/email_auth.py:277` (read, local), `app/email_auth.py:372` (read, local), `app/email_auth.py:389` (insert, local), `app/email_auth.py:408` (read, local), `tests/test_account_linking.py:71` (read, local), `tests/test_account_linking.py:104` (read, local), `tests/test_account_linking.py:113` (read, local), `tests/test_account_linking.py:119` (insert, local), `tests/test_account_linking.py:121` (read, local), `tests/test_account_linking.py:128` (read, local), `tests/test_account_linking.py:181` (read, local), `tests/test_account_linking.py:187` (read, local), `tests/test_account_linking.py:198` (read, local), `tests/test_account_linking.py:204` (insert, local), `tests/test_android_auth.py:155` (update, local), `tests/test_email_auth.py:78` (read, local), `tests/test_play_release.py:249` (migration, local), `tests/test_play_release.py:250` (insert, local), `tests/test_play_release.py:261` (read, local).
- Связанные API файла-владельца: `/api/auth/android/browser-link`, `/auth/android/browser`, `/api/auth/android/browser-session`, `/api/account/identities`, `/api/auth/android/start`, `/api/auth/telegram/native`, `/api/auth/android/exchange`, `/auth/android/return`.
- Telegram handlers файла-владельца: нет прямой связи.

## `email_auth_links`

- local: `app/email_auth.py`:40.
- Колонки: `token_hash` TEXT PRIMARY KEY, `email` TEXT NOT NULL, `purpose` TEXT NOT NULL, `created` INTEGER NOT NULL, `consumed` INTEGER NOT NULL DEFAULT 0, `language` TEXT NOT NULL, `next_url` TEXT NOT NULL, `android` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- local: `tests/test_play_release.py`:251.
- Колонки: `email` TEXT, `token_hash` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_privacy.py:58` (read, local), `app/account_privacy.py:59` (delete, local), `app/email_auth.py:40` (migration, local), `app/email_auth.py:49` (read, local), `app/email_auth.py:51` (migration, local), `app/email_auth.py:194` (migration, local), `app/email_auth.py:195` (update, local), `app/email_auth.py:196` (migration, local), `app/email_auth.py:203` (update, local), `app/email_auth.py:211` (migration, local), `app/email_auth.py:283` (update, local), `app/email_auth.py:284` (migration, local), `app/email_auth.py:290` (update, local), `app/email_auth.py:316` (update, local), `app/email_auth.py:383` (update, local), `app/email_auth.py:392` (update, local), `tests/test_account_linking.py:126` (migration, local), `tests/test_email_auth.py:107` (migration, local), `tests/test_play_release.py:251` (migration, local), `tests/test_play_release.py:252` (insert, local), `tests/test_play_release.py:261` (read, local).
- Связанные API файла-владельца: `/privacy`, `/account/delete`, `/api/account/deletion-challenge`, `/api/account/delete`.
- Telegram handlers файла-владельца: нет прямой связи.

## `environment_snapshots`

- local: `tools/project_kb.py`:100.
- Колонки: `id` INTEGER PRIMARY KEY, `environment` TEXT, `git_branch` TEXT, `git_commit` TEXT, `git_dirty` INTEGER, `project_path` TEXT, `captured_at` TEXT, `tracked_files_json` TEXT, `entrypoints_json` TEXT, `schema_hash` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:136` (read, local), `tools/project_kb.py:100` (migration, local), `tools/project_kb.py:552` (insert, local), `tools/project_kb.py:659` (insert, local), `tools/project_kb.py:707` (read, local), `tools/project_kb.py:833` (read, local), `tools/project_kb.py:835` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `family_invitation_aliases`

- local: `app/family_invites.py`:16.
- Колонки: `short_code` TEXT PRIMARY KEY, `code` TEXT NOT NULL, `kind` TEXT NOT NULL, `expires_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_privacy.py:70` (read, local), `app/account_privacy.py:72` (delete, local), `app/family_invites.py:16` (migration, local), `app/family_invites.py:30` (delete, local), `app/family_invites.py:31` (read, local), `app/family_invites.py:38` (read, local), `app/family_invites.py:40` (insert, local), `app/family_invites.py:64` (read, local).
- Связанные API файла-владельца: `/privacy`, `/account/delete`, `/api/account/deletion-challenge`, `/api/account/delete`.
- Telegram handlers файла-владельца: нет прямой связи.

## `family_invitation_attempts`

- local: `app/family_invites.py`:22.
- Колонки: `user_id` TEXT PRIMARY KEY, `window_start` INTEGER NOT NULL, `count` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/family_invites.py:22` (migration, local), `app/family_invites.py:77` (delete, local), `app/family_invites.py:78` (insert, local), `app/family_invites.py:80` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `family_invitation_uses`

- local: `app/family_invites.py`:19.
- Колонки: `code` TEXT NOT NULL, `kind` TEXT NOT NULL, `user_id` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/family_invites.py:19` (migration, local), `app/family_invites.py:93` (read, local), `app/family_pairing.py:236` (read, local), `app/family_pairing.py:291` (insert, local), `app/family_pairing.py:392` (read, local), `app/family_pairing.py:450` (insert, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `family_invite_codes`

- local: `app/family_pairing.py`:129.
- Колонки: `code` TEXT PRIMARY KEY, `parent_user_id` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: `idx_family_invite_codes_parent` (parent_user_id).
- Чтение/запись/миграции: `app/family_pairing.py:129` (migration, local), `app/family_pairing.py:139` (read, local), `app/family_pairing.py:163` (delete, local), `app/family_pairing.py:171` (insert, local), `app/family_pairing.py:196` (read, local), `app/family_pairing.py:201` (delete, local), `app/family_pairing.py:243` (read, local), `app/family_pairing.py:249` (delete, local), `tests/test_family_universal.py:72` (update, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `family_lesson_assignments`

- local: `app/mcp_service.py`:192.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: `idx_family_lesson_assignments_child` (child_user_id, lesson).
- local: `app/routes.py`:793.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/content_service.py:333` (read, local), `app/content_service.py:334` (read, local), `app/content_service.py:336` (read, local), `app/mcp_service.py:192` (migration, local), `app/mcp_service.py:200` (read, local), `app/mcp_service.py:533` (read, local), `app/mcp_service.py:991` (read, local), `app/mcp_service.py:1009` (migration, local), `app/mcp_service.py:1011` (migration, local), `app/mcp_service.py:1041` (read, local), `app/mcp_service.py:1057` (update, local), `app/mcp_service.py:1108` (delete, local), `app/mcp_service.py:1128` (read, local), `app/mcp_service.py:1186` (read, local), `app/mcp_service.py:1210` (read, local), `app/mcp_service.py:1221` (update, local), `app/mcp_service.py:1233` (read, local), `app/mcp_service.py:1257` (migration, local), `app/mcp_service.py:1270` (read, local), `app/mcp_service.py:1676` (read, local), `app/mcp_service.py:2104` (migration, local), `app/routes.py:793` (migration, local), `app/routes.py:805` (read, local), `app/routes.py:918` (read, local), `app/routes.py:920` (migration, local), `app/routes.py:922` (migration, local), `app/routes.py:964` (read, local), `app/routes.py:968` (delete, local), `app/routes.py:1004` (read, local), `app/routes.py:1032` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `family_pairing_codes`

- local: `app/family_pairing.py`:72.
- Колонки: `code` TEXT PRIMARY KEY, `child_user_id` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: `idx_family_pairing_codes_child` (child_user_id).
- production: `/app/words.db sqlite_master`.
- Колонки: `code` TEXT PRIMARY KEY, `child_user_id` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: `idx_family_pairing_codes_child` (child_user_id).
- Чтение/запись/миграции: `app/family_pairing.py:72` (migration, local), `app/family_pairing.py:82` (read, local), `app/family_pairing.py:105` (delete, local), `app/family_pairing.py:113` (insert, local), `app/family_pairing.py:351` (read, local), `app/family_pairing.py:356` (delete, local), `app/family_pairing.py:399` (read, local), `app/family_pairing.py:405` (delete, local), `tests/test_family_pairing_bot.py:111` (update, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `files`

- local: `tools/project_kb.py`:60.
- Колонки: `path` TEXT NOT NULL, `source_scope` TEXT NOT NULL, `language` TEXT, `layer` TEXT, `purpose` TEXT, `size_bytes` INTEGER, `sha256` TEXT, `indexed_at` TEXT, `is_generated` INTEGER NOT NULL DEFAULT 0, `is_entrypoint` INTEGER NOT NULL DEFAULT 0.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:47` (delete, local), `tests/test_project_kb.py:49` (read, local), `tools/project_kb.py:60` (migration, local), `tools/project_kb.py:135` (read, local), `tools/project_kb.py:153` (read, local), `tools/project_kb.py:448` (read, local), `tools/project_kb.py:453` (insert, local), `tools/project_kb.py:468` (read, local), `tools/project_kb.py:550` (read, local), `tools/project_kb.py:551` (read, local), `tools/project_kb.py:553` (read, local), `tools/project_kb.py:566` (read, local), `tools/project_kb.py:571` (update, local), `tools/project_kb.py:573` (read, local), `tools/project_kb.py:576` (read, local), `tools/project_kb.py:577` (read, local), `tools/project_kb.py:580` (delete, local), `tools/project_kb.py:711` (read, local), `tools/project_kb.py:713` (read, local), `tools/project_kb.py:723` (update, local), `tools/project_kb.py:740` (read, local), `tools/project_kb.py:743` (read, local), `tools/project_kb.py:803` (update, local), `tools/project_kb.py:806` (read, local), `tools/project_kb.py:810` (update, local), `tools/project_kb.py:823` (read, local), `tools/project_kb.py:835` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `frontend_links`

- local: `tools/project_kb.py`:83.
- Колонки: `id` INTEGER PRIMARY KEY, `source_file` TEXT, `target_type` TEXT, `target_value` TEXT, `line_number` INTEGER, `source_scope` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tools/project_kb.py:83` (migration, local), `tools/project_kb.py:400` (insert, local), `tools/project_kb.py:450` (read, local), `tools/project_kb.py:514` (read, local), `tools/project_kb.py:535` (read, local), `tools/project_kb.py:536` (read, local), `tools/project_kb.py:580` (delete, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `google_play_purchases`

- local: `app/google_play.py`:56.
- Колонки: `token_hash` TEXT PRIMARY KEY, `user_id` TEXT, `token_cipher` TEXT NOT NULL, `product_id` TEXT NOT NULL, `state` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `acknowledged` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL, `superseded_by` TEXT, `checked_at_ns` INTEGER NOT NULL DEFAULT 0.
- Индексы: `play_purchase_user` (user_id).
- Чтение/запись/миграции: `app/account_privacy.py:73` (read, local), `app/account_privacy.py:74` (update, local), `app/google_play.py:56` (migration, local), `app/google_play.py:61` (read, local), `app/google_play.py:62` (migration, local), `app/google_play.py:63` (migration, local), `app/google_play.py:119` (read, local), `app/google_play.py:144` (read, local), `app/google_play.py:158` (read, local), `app/google_play.py:175` (read, local), `app/google_play.py:178` (insert, local), `app/google_play.py:186` (insert, local), `app/google_play.py:189` (update, local), `app/google_play.py:196` (read, local), `app/google_play.py:224` (read, local), `app/google_play.py:238` (read, local), `app/google_play.py:289` (read, local), `tests/test_play_release.py:76` (read, local), `tests/test_play_release.py:77` (read, local), `tests/test_play_release.py:169` (read, local), `tests/test_play_release.py:273` (update, local).
- Связанные API файла-владельца: `/api/subscription/sync`, `/api/subscription/google-play-notifications`, `/privacy`, `/account/delete`, `/api/account/deletion-challenge`, `/api/account/delete`.
- Telegram handlers файла-владельца: нет прямой связи.

## `google_tts_budget_monthly`

- local: `app/tts_usage.py`:80.
- Колонки: `user_id` TEXT NOT NULL, `period_key` TEXT NOT NULL, `characters` INTEGER NOT NULL DEFAULT 0, `blocked_requests` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_google_tts_budget_period` (period_key).
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT NOT NULL, `period_key` TEXT NOT NULL, `characters` INTEGER NOT NULL DEFAULT 0, `blocked_requests` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_google_tts_budget_period` (period_key).
- Чтение/запись/миграции: `app/tts_usage.py:80` (migration, local), `app/tts_usage.py:93` (read, local), `app/tts_usage.py:187` (read, local), `app/tts_usage.py:197` (read, local), `app/tts_usage.py:221` (insert, local), `app/tts_usage.py:240` (insert, local), `app/tts_usage.py:308` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `google_tts_limits`

- local: `app/tts_usage.py`:98.
- Колонки: `scope` TEXT PRIMARY KEY, `monthly_character_limit` INTEGER, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `scope` TEXT PRIMARY KEY, `monthly_character_limit` INTEGER, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_privacy.py:93` (read, local), `app/account_privacy.py:94` (delete, local), `app/tts_usage.py:98` (migration, local), `app/tts_usage.py:107` (insert, local), `app/tts_usage.py:126` (delete, local), `app/tts_usage.py:133` (insert, local), `app/tts_usage.py:146` (read, local).
- Связанные API файла-владельца: `/privacy`, `/account/delete`, `/api/account/deletion-challenge`, `/api/account/delete`.
- Telegram handlers файла-владельца: нет прямой связи.

## `google_tts_usage_monthly`

- local: `app/tts_usage.py`:62.
- Колонки: `user_id` TEXT NOT NULL, `period_key` TEXT NOT NULL, `successful_requests` INTEGER NOT NULL DEFAULT 0, `failed_requests` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_google_tts_usage_period` (period_key).
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT NOT NULL, `period_key` TEXT NOT NULL, `successful_requests` INTEGER NOT NULL DEFAULT 0, `failed_requests` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_google_tts_usage_period` (period_key).
- Чтение/запись/миграции: `app/tts_usage.py:62` (migration, local), `app/tts_usage.py:75` (read, local), `app/tts_usage.py:271` (insert, local), `app/tts_usage.py:300` (read, local), `app/tts_usage.py:394` (delete, local), `app/tts_usage.py:400` (delete, local), `tests/test_tts_usage.py:81` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `imports`

- local: `tools/project_kb.py`:69.
- Колонки: `id` INTEGER PRIMARY KEY, `source_file` TEXT, `target_module` TEXT, `imported_name` TEXT, `import_type` TEXT, `source_scope` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tools/project_kb.py:69` (migration, local), `tools/project_kb.py:288` (insert, local), `tools/project_kb.py:291` (insert, local), `tools/project_kb.py:450` (read, local), `tools/project_kb.py:580` (delete, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `kb_capabilities`

- local: `tools/project_kb.py`:241.
- Колонки: `name` TEXT PRIMARY KEY, `enabled` INTEGER.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:103` (read, local), `tools/project_kb.py:224` (migration, local), `tools/project_kb.py:225` (insert, local), `tools/project_kb.py:237` (migration, local), `tools/project_kb.py:238` (insert, local), `tools/project_kb.py:241` (migration, local), `tools/project_kb.py:242` (insert, local), `tools/project_kb.py:464` (read, local), `tools/project_kb.py:835` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_access_grants`

- local: `app/mcp_service.py`:164.
- Колонки: `token_hash` TEXT PRIMARY KEY, `client_id` TEXT NOT NULL, `user_id` TEXT NOT NULL, `resource` TEXT NOT NULL, `scopes` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `created_at` INTEGER NOT NULL, `last_used_at` INTEGER, `revoked_at` INTEGER.
- Индексы: `idx_mcp_grants_user` (user_id, revoked_at, expires_at).
- local: `tests/test_play_release.py`:253.
- Колонки: `user_id` TEXT, `token_hash` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_api.py:102` (read, local), `app/mcp_api.py:112` (update, local), `app/mcp_api.py:142` (read, local), `app/mcp_api.py:213` (update, local), `app/mcp_api.py:257` (migration, local), `app/mcp_api.py:303` (update, local), `app/mcp_api.py:305` (update, local), `app/mcp_api.py:539` (migration, local), `app/mcp_api.py:560` (update, local), `tests/test_play_release.py:253` (migration, local), `tests/test_play_release.py:254` (insert, local), `tests/test_play_release.py:261` (read, local).
- Связанные API файла-владельца: `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_admin_audit_log`

- local: `app/mcp_service.py`:214.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `created_at` INTEGER NOT NULL, `admin_user_id` TEXT NOT NULL, `target_user_id` TEXT NOT NULL, `action` TEXT NOT NULL, `old_value` TEXT NOT NULL, `new_value` TEXT NOT NULL, `request_id` TEXT NOT NULL DEFAULT ''.
- Индексы: `idx_mcp_admin_audit_created` (created_at DESC).
- Чтение/запись/миграции: `app/mcp_service.py:214` (migration, local), `app/mcp_service.py:224` (migration, local), `app/mcp_service.py:1331` (migration, local), `app/mcp_service.py:1538` (migration, local), `app/mcp_service.py:1554` (migration, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_audit_log`

- local: `app/mcp_service.py`:201.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `created_at` INTEGER NOT NULL, `request_id` TEXT NOT NULL, `client_hash` TEXT NOT NULL, `user_hash` TEXT NOT NULL, `operation` TEXT NOT NULL, `success` INTEGER NOT NULL, `error_code` TEXT, `duration_ms` INTEGER NOT NULL, `item_count` INTEGER NOT NULL DEFAULT 0.
- Индексы: `idx_mcp_audit_created_at` (created_at).
- local: `tests/test_play_release.py`:257.
- Колонки: `user_hash` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_privacy.py:95` (read, local), `app/account_privacy.py:98` (delete, local), `app/mcp_api.py:261` (migration, local), `app/mcp_api.py:624` (migration, local), `tests/test_play_release.py:257` (migration, local), `tests/test_play_release.py:258` (insert, local), `tests/test_play_release.py:261` (read, local).
- Связанные API файла-владельца: `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`, `/privacy`, `/account/delete`, `/api/account/deletion-challenge`, `/api/account/delete`.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_idempotency`

- local: `app/mcp_service.py`:183.
- Колонки: `user_id` TEXT NOT NULL, `operation` TEXT NOT NULL, `idempotency_key` TEXT NOT NULL, `request_hash` TEXT NOT NULL, `response_json` TEXT NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_service.py:183` (migration, local), `app/mcp_service.py:243` (read, local), `app/mcp_service.py:249` (migration, local), `tests/test_content_pipeline.py:239` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_oauth_clients`

- local: `app/mcp_service.py`:143.
- Колонки: `client_id` TEXT PRIMARY KEY, `client_name` TEXT NOT NULL DEFAULT '', `redirect_uris` TEXT NOT NULL, `created_at` INTEGER NOT NULL, `last_used_at` INTEGER, `revoked_at` INTEGER.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_api.py:113` (update, local), `app/mcp_api.py:142` (read, local), `app/mcp_api.py:253` (migration, local), `app/mcp_api.py:257` (migration, local), `app/mcp_api.py:302` (update, local), `app/mcp_api.py:349` (migration, local), `app/mcp_api.py:390` (read, local).
- Связанные API файла-владельца: `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_oauth_codes`

- local: `app/mcp_service.py`:151.
- Колонки: `code_hash` TEXT PRIMARY KEY, `client_id` TEXT NOT NULL, `user_id` TEXT NOT NULL, `redirect_uri` TEXT NOT NULL, `resource` TEXT NOT NULL, `scopes` TEXT NOT NULL, `code_challenge` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `used_at` INTEGER, `created_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_api.py:483` (insert, local), `app/mcp_api.py:518` (read, local), `app/mcp_api.py:535` (update, local).
- Связанные API файла-владельца: `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_user_settings`

- local: `app/mcp_service.py`:178.
- Колонки: `user_id` TEXT PRIMARY KEY, `enabled` INTEGER NOT NULL DEFAULT 1, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_api.py:79` (read, local), `app/mcp_api.py:196` (insert, local).
- Связанные API файла-владельца: `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`.
- Telegram handlers файла-владельца: нет прямой связи.

## `parent_child_links`

- local: `app/routes.py`:776.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `run.py`:149.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_family_pairing_bot.py`:251.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: `idx_parent_child_links_child` (child_user_id).
- Чтение/запись/миграции: `app/family_pairing.py:25` (read, local), `app/family_pairing.py:47` (read, local), `app/family_pairing.py:56` (read, local), `app/family_pairing.py:268` (read, local), `app/family_pairing.py:276` (read, local), `app/family_pairing.py:287` (insert, local), `app/family_pairing.py:307` (read, local), `app/family_pairing.py:325` (read, local), `app/family_pairing.py:424` (read, local), `app/family_pairing.py:432` (read, local), `app/family_pairing.py:446` (insert, local), `app/mcp_service.py:919` (read, local), `app/mcp_service.py:939` (read, local), `app/routes.py:654` (read, local), `app/routes.py:776` (migration, local), `app/routes.py:788` (read, local), `app/routes.py:842` (read, local), `app/routes.py:964` (read, local), `app/routes.py:1090` (read, local), `app/routes.py:1094` (read, local), `app/routes.py:1119` (read, local), `app/routes.py:1126` (read, local), `app/routes.py:1155` (read, local), `app/routes.py:1183` (read, local), `app/routes.py:1709` (read, local), `app/routes.py:2289` (read, local), `app/routes.py:2638` (read, local), `app/routes.py:3448` (read, local), `app/routes.py:3499` (read, local), `app/routes.py:3757` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `progress_events`

- local: `app/routes.py`:499.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `scope` TEXT, `event_type` TEXT, `event_ts` INTEGER, `payload` TEXT, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: `idx_progress_events_user_ts` (user_id, event_ts).
- local: `tests/test_project_kb.py`:60.
- Колонки: `id` INTEGER PRIMARY KEY, `user_id` TEXT.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `scope` TEXT, `event_type` TEXT, `event_ts` INTEGER, `payload` TEXT, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: `idx_progress_events_user_ts` (user_id, event_ts).
- Чтение/запись/миграции: `app/mcp_service.py:779` (read, local), `app/mcp_service.py:822` (read, local), `app/mcp_service.py:886` (insert, local), `app/mcp_service.py:1360` (read, local), `app/mcp_service.py:1512` (read, local), `app/mcp_service.py:1515` (read, local), `app/mcp_service.py:1700` (read, local), `app/routes.py:499` (migration, local), `app/routes.py:511` (read, local), `app/routes.py:588` (read, local), `app/routes.py:1197` (read, local), `app/routes.py:1205` (read, local), `app/routes.py:1448` (read, local), `app/routes.py:2265` (read, local), `app/routes.py:4017` (read, local), `app/routes.py:4593` (insert, local), `docs/MCP_CONNECTOR.md:47` (update, local), `tests/test_family_accounts.py:306` (insert, local), `tests/test_family_accounts.py:387` (insert, local), `tests/test_family_accounts.py:447` (insert, local), `tests/test_mcp_connector.py:422` (read, local), `tests/test_project_kb.py:58` (insert, local), `tests/test_project_kb.py:60` (migration, local), `tests/test_project_kb.py:65` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `reminder_state`

- local: `bot/reminder.py`:52.
- Колонки: `user_id` TEXT PRIMARY KEY, `last_msg_id` INTEGER, `last_sent_date` TEXT.
- Индексы: не найдены в этом определении.
- local: `run.py`:109.
- Колонки: `user_id` TEXT PRIMARY KEY, `last_msg_id` INTEGER, `last_sent_date` TEXT.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `last_msg_id` INTEGER, `last_sent_date` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `bot/reminder.py:52` (migration, local), `bot/reminder.py:89` (read, local), `bot/reminder.py:103` (insert, local), `docs/codex/ARCHITECTURE.md:18` (update, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: `/reminder_now`.

## `retained_progress`

- local: `tests/test_content_pipeline.py`:178.
- Колонки: `word_id` INTEGER, `score` INTEGER.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_content_pipeline.py:178` (migration, local), `tests/test_content_pipeline.py:180` (insert, local), `tests/test_content_pipeline.py:184` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `routes`

- local: `tools/project_kb.py`:72.
- Колонки: `id` INTEGER PRIMARY KEY, `route_type` TEXT, `method_or_trigger` TEXT, `route_or_command` TEXT, `handler` TEXT, `file_path` TEXT, `line_number` INTEGER, `auth_type` TEXT, `purpose` TEXT, `source_scope` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:52` (read, local), `tests/test_project_kb.py:64` (read, local), `tests/test_project_kb.py:70` (read, local), `tools/project_kb.py:72` (migration, local), `tools/project_kb.py:117` (read, local), `tools/project_kb.py:119` (read, local), `tools/project_kb.py:121` (update, local), `tools/project_kb.py:123` (read, local), `tools/project_kb.py:125` (read, local), `tools/project_kb.py:127` (read, local), `tools/project_kb.py:131` (read, local), `tools/project_kb.py:193` (read, local), `tools/project_kb.py:281` (insert, local), `tools/project_kb.py:348` (insert, local), `tools/project_kb.py:426` (read, local), `tools/project_kb.py:428` (read, local), `tools/project_kb.py:450` (read, local), `tools/project_kb.py:453` (insert, local), `tools/project_kb.py:469` (read, local), `tools/project_kb.py:492` (read, local), `tools/project_kb.py:504` (read, local), `tools/project_kb.py:505` (read, local), `tools/project_kb.py:512` (read, local), `tools/project_kb.py:524` (read, local), `tools/project_kb.py:566` (read, local), `tools/project_kb.py:580` (delete, local), `tools/project_kb.py:594` (read, local), `tools/project_kb.py:601` (read, local), `tools/project_kb.py:630` (read, local), `tools/project_kb.py:646` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `services`

- local: `tools/project_kb.py`:91.
- Колонки: `id` INTEGER PRIMARY KEY, `environment` TEXT, `service_name` TEXT, `service_type` TEXT, `working_directory` TEXT, `exec_start_redacted` TEXT, `user_name` TEXT, `group_name` TEXT, `environment_file_path` TEXT, `port` TEXT, `source_file` TEXT, `last_indexed_at` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:122` (read, local), `tests/test_project_kb.py:135` (read, local), `tools/project_kb.py:91` (migration, local), `tools/project_kb.py:594` (read, local), `tools/project_kb.py:599` (read, local), `tools/project_kb.py:642` (delete, local), `tools/project_kb.py:643` (read, local), `tools/project_kb.py:645` (insert, local), `tools/project_kb.py:672` (read, local), `tools/project_kb.py:719` (read, local), `tools/project_kb.py:811` (read, local), `tools/project_kb.py:829` (read, local), `tools/project_kb.py:830` (read, local), `tools/project_kb.py:835` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `shared_lesson_words`

- local: `app/routes.py`:812.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `parent_word_id` INTEGER NOT NULL, `child_word_id` INTEGER NOT NULL UNIQUE, `created_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/routes.py:809` (read, local), `app/routes.py:812` (migration, local), `app/routes.py:825` (read, local), `app/routes.py:829` (read, local), `app/routes.py:864` (insert, local), `app/routes.py:2665` (read, local), `app/routes.py:2676` (delete, local), `app/routes.py:2716` (insert, local), `app/routes.py:2976` (read, local), `app/routes.py:2985` (read, local), `app/routes.py:4150` (read, local), `app/routes.py:4160` (read, local), `app/routes.py:4190` (update, local), `tests/test_family_accounts.py:790` (read, local), `tests/test_family_accounts.py:818` (read, local), `tests/test_family_accounts.py:822` (read, local), `tests/test_family_accounts.py:885` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `shared_word_sets`

- local: `app/routes.py`:1899.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `token` TEXT NOT NULL UNIQUE, `owner_user_id` TEXT NOT NULL, `title` TEXT NOT NULL, `lesson` TEXT, `payload` TEXT NOT NULL, `created_at` INTEGER NOT NULL, `expires_at` INTEGER, `import_count` INTEGER NOT NULL DEFAULT 0, `max_imports` INTEGER.
- Индексы: `idx_shared_word_sets_token` (token).
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `token` TEXT NOT NULL UNIQUE, `owner_user_id` TEXT NOT NULL, `title` TEXT NOT NULL, `lesson` TEXT, `payload` TEXT NOT NULL, `created_at` INTEGER NOT NULL, `expires_at` INTEGER, `import_count` INTEGER NOT NULL DEFAULT 0, `max_imports` INTEGER.
- Индексы: `idx_shared_word_sets_token` (token).
- Чтение/запись/миграции: `app/routes.py:1899` (migration, local), `app/routes.py:1914` (read, local), `app/routes.py:2403` (read, local), `app/routes.py:2517` (read, local), `app/routes.py:2521` (insert, local), `app/routes.py:2749` (read, local), `app/routes.py:2835` (update, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `symbols`

- local: `tools/project_kb.py`:65.
- Колонки: `id` INTEGER PRIMARY KEY, `name` TEXT, `symbol_type` TEXT, `signature` TEXT, `file_path` TEXT, `line_start` INTEGER, `line_end` INTEGER, `docstring` TEXT, `parent_symbol` TEXT, `source_scope` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:45` (read, local), `tests/test_project_kb.py:48` (delete, local), `tests/test_project_kb.py:63` (read, local), `tools/project_kb.py:65` (migration, local), `tools/project_kb.py:271` (insert, local), `tools/project_kb.py:275` (insert, local), `tools/project_kb.py:332` (insert, local), `tools/project_kb.py:450` (read, local), `tools/project_kb.py:467` (read, local), `tools/project_kb.py:566` (read, local), `tools/project_kb.py:580` (delete, local), `tools/project_kb.py:818` (read, local), `tools/project_kb.py:821` (read, local), `tools/project_kb.py:824` (read, local), `tools/project_kb.py:835` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `task_routes`

- local: `tools/project_kb.py`:105.
- Колонки: `id` INTEGER PRIMARY KEY, `topic` TEXT UNIQUE, `keywords` TEXT, `primary_files_json` TEXT, `secondary_files_json` TEXT, `excluded_paths_json` TEXT, `recommended_checks_json` TEXT, `environment_scope` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `docs/codex/TASK_ROUTING.md:19` (read, local), `tools/project_kb.py:105` (migration, local), `tools/project_kb.py:113` (read, local), `tools/project_kb.py:472` (read, local), `tools/project_kb.py:543` (read, local), `tools/project_kb.py:544` (insert, local), `tools/project_kb.py:765` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `translation_token_usage`

- local: `app/translation_usage.py`:11.
- Колонки: `user_id` TEXT PRIMARY KEY, `successful_requests` INTEGER NOT NULL DEFAULT 0, `failed_requests` INTEGER NOT NULL DEFAULT 0, `prompt_tokens` INTEGER NOT NULL DEFAULT 0, `completion_tokens` INTEGER NOT NULL DEFAULT 0, `total_tokens` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `successful_requests` INTEGER NOT NULL DEFAULT 0, `failed_requests` INTEGER NOT NULL DEFAULT 0, `prompt_tokens` INTEGER NOT NULL DEFAULT 0, `completion_tokens` INTEGER NOT NULL DEFAULT 0, `total_tokens` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/translation_usage.py:11` (migration, local), `app/translation_usage.py:49` (insert, local), `app/translation_usage.py:79` (read, local), `app/translation_usage.py:122` (delete, local), `app/translation_usage.py:125` (delete, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_daily_goals`

- local: `app/routes.py`:543.
- Колонки: `user_id` TEXT PRIMARY KEY, `goal_value` INTEGER NOT NULL, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_family_pairing_bot.py`:257.
- Колонки: `user_id` TEXT PRIMARY KEY, `goal_value` INTEGER NOT NULL, `updated_at` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_family_universal.py`:78.
- Колонки: `user_id` TEXT PRIMARY KEY, `goal_value` INTEGER NOT NULL, `updated_at` TEXT.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `goal_value` INTEGER NOT NULL, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/family_pairing.py:65` (read, local), `app/family_pairing.py:66` (delete, local), `app/mcp_service.py:316` (insert, local), `app/routes.py:543` (migration, local), `app/routes.py:560` (read, local), `app/routes.py:4418` (insert, local), `tests/test_family_pairing_bot.py:257` (migration, local), `tests/test_family_pairing_bot.py:263` (insert, local), `tests/test_family_pairing_bot.py:307` (read, local), `tests/test_family_universal.py:78` (migration, local), `tests/test_family_universal.py:79` (insert, local), `tests/test_family_universal.py:89` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_language_preferences`

- local: `app/routes.py`:735.
- Колонки: `user_id` TEXT NOT NULL, `priority` INTEGER NOT NULL, `lang_code` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_language_preferences_user` (user_id, priority).
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT NOT NULL, `priority` INTEGER NOT NULL, `lang_code` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_language_preferences_user` (user_id, priority).
- Чтение/запись/миграции: `app/content_service.py:337` (read, local), `app/content_service.py:339` (read, local), `app/mcp_service.py:289` (delete, local), `app/mcp_service.py:291` (insert, local), `app/mcp_service.py:1399` (read, local), `app/routes.py:735` (migration, local), `app/routes.py:746` (read, local), `app/routes.py:1844` (read, local), `app/routes.py:3897` (delete, local), `app/routes.py:3899` (insert, local), `docs/MCP_CONNECTOR.md:49` (read, local), `tests/test_content_pipeline.py:46` (insert, local), `tests/test_family_accounts.py:418` (insert, local), `tests/test_family_accounts.py:478` (insert, local), `tests/test_family_accounts.py:676` (insert, local), `tests/test_family_accounts.py:683` (insert, local), `tests/test_mcp_connector.py:76` (insert, local), `tests/test_mcp_lesson_flow.py:86` (insert, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_lessons`

- local: `app/models.py`:20.
- Колонки: `user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `hidden` INTEGER NOT NULL DEFAULT 0, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `app/routes.py`:989.
- Колонки: `user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `hidden` INTEGER NOT NULL DEFAULT 0, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `hidden` INTEGER NOT NULL DEFAULT 0, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, `updated_at_ts` INTEGER.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_service.py:586` (insert, local), `app/mcp_service.py:729` (delete, local), `app/mcp_service.py:744` (read, local), `app/mcp_service.py:750` (read, local), `app/mcp_service.py:758` (update, local), `app/mcp_service.py:928` (read, local), `app/mcp_service.py:929` (read, local), `app/mcp_service.py:1438` (read, local), `app/mcp_service.py:1475` (read, local), `app/mcp_service.py:2037` (read, local), `app/mcp_service.py:2042` (insert, local), `app/mcp_service.py:2069` (delete, local), `app/models.py:20` (migration, local), `app/models.py:28` (read, local), `app/models.py:30` (migration, local), `app/models.py:32` (update, local), `app/models.py:72` (read, local), `app/models.py:141` (insert, local), `app/routes.py:989` (migration, local), `app/routes.py:1006` (read, local), `app/routes.py:1026` (read, local), `app/routes.py:1034` (read, local), `app/routes.py:4109` (read, local), `app/routes.py:4119` (read, local), `app/routes.py:4200` (read, local), `app/routes.py:4205` (insert, local), `app/routes.py:4213` (delete, local), `app/routes.py:4234` (delete, local), `app/routes.py:4294` (delete, local), `app/routes.py:4653` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_settings`

- local: `app/routes.py`:759.
- Колонки: `user_id` TEXT PRIMARY KEY, `detected_ui_language` TEXT, `ui_language_override` TEXT, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- local: `bot/onboarding.py`:489.
- Колонки: `user_id` TEXT PRIMARY KEY, `detected_ui_language` TEXT, `ui_language_override` TEXT, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `detected_ui_language` TEXT, `ui_language_override` TEXT, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/routes.py:759` (migration, local), `app/routes.py:1487` (insert, local), `app/routes.py:1505` (read, local), `app/routes.py:1542` (insert, local), `bot/i18n.py:20` (read, local), `bot/onboarding.py:489` (migration, local), `bot/onboarding.py:504` (insert, local), `bot/onboarding.py:518` (read, local), `bot/onboarding.py:534` (insert, local), `tests/test_family_accounts.py:425` (insert, local), `tests/test_family_accounts.py:485` (insert, local), `tests/test_telegram_onboarding.py:87` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_subscriptions`

- local: `app/routes.py`:1555.
- Колонки: `user_id` TEXT PRIMARY KEY, `status` TEXT NOT NULL DEFAULT 'trial', `trial_started_at` INTEGER NOT NULL, `trial_ends_at` INTEGER NOT NULL, `current_period_ends_at` INTEGER, `provider` TEXT, `provider_customer_id` TEXT, `provider_subscription_id` TEXT, `cancel_at_period_end` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_subscriptions_status` (status, trial_ends_at, current_period_ends_at).
- local: `tests/test_google_account_link.py`:68.
- Колонки: `user_id` TEXT PRIMARY KEY, `status` TEXT NOT NULL DEFAULT 'trial'.
- Индексы: не найдены в этом определении.
- local: `tests/test_plans.py`:279.
- Колонки: `user_id` TEXT PRIMARY KEY, `status` TEXT NOT NULL DEFAULT 'trial', `trial_started_at` INTEGER NOT NULL, `trial_ends_at` INTEGER NOT NULL, `current_period_ends_at` INTEGER, `provider` TEXT, `provider_customer_id` TEXT, `provider_subscription_id` TEXT, `cancel_at_period_end` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `status` TEXT NOT NULL DEFAULT 'trial', `trial_started_at` INTEGER NOT NULL, `trial_ends_at` INTEGER NOT NULL, `current_period_ends_at` INTEGER, `provider` TEXT, `provider_customer_id` TEXT, `provider_subscription_id` TEXT, `cancel_at_period_end` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_subscriptions_status` (status, trial_ends_at, current_period_ends_at).
- Чтение/запись/миграции: `app/google_auth.py:269` (read, local), `app/google_auth.py:290` (read, local), `app/google_auth.py:294` (delete, local), `app/google_auth.py:298` (update, local), `app/google_play.py:148` (read, local), `app/google_play.py:169` (read, local), `app/google_play.py:203` (insert, local), `app/google_play.py:214` (update, local), `app/mcp_service.py:1320` (read, local), `app/mcp_service.py:1322` (insert, local), `app/mcp_service.py:1328` (read, local), `app/mcp_service.py:1329` (update, local), `app/mcp_service.py:1345` (read, local), `app/mcp_service.py:1513` (read, local), `app/routes.py:1555` (migration, local), `app/routes.py:1570` (read, local), `app/routes.py:1572` (read, local), `app/routes.py:1575` (migration, local), `app/routes.py:1605` (read, local), `app/routes.py:1612` (insert, local), `app/routes.py:1617` (read, local), `app/routes.py:1674` (read, local), `app/routes.py:2275` (read, local), `app/routes.py:4822` (read, local), `app/routes.py:5031` (insert, local), `app/routes.py:5061` (update, local), `tests/test_advertising.py:113` (insert, local), `tests/test_advertising.py:335` (read, local), `tests/test_google_account_link.py:68` (migration, local), `tests/test_google_account_link.py:77` (insert, local).
- Связанные API файла-владельца: `/api/subscription/sync`, `/api/subscription/google-play-notifications`, `/auth/google`, `/auth/google/callback`, `/api/auth/google/config`, `/api/auth/google/verify`, `/api/auth/google/link`, `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_word_flags`

- local: `app/routes.py`:486.
- Колонки: `user_id` TEXT NOT NULL, `word_id` INTEGER NOT NULL, `difficult` INTEGER NOT NULL DEFAULT 1.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT NOT NULL, `word_id` INTEGER NOT NULL, `difficult` INTEGER NOT NULL DEFAULT 1.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_service.py:460` (read, local), `app/mcp_service.py:485` (read, local), `app/mcp_service.py:521` (read, local), `app/mcp_service.py:552` (read, local), `app/mcp_service.py:665` (delete, local), `app/mcp_service.py:692` (insert, local), `app/mcp_service.py:732` (delete, local), `app/mcp_service.py:1274` (read, local), `app/mcp_service.py:1438` (read, local), `app/mcp_service.py:1455` (update, local), `app/mcp_service.py:1531` (read, local), `app/mcp_service.py:1732` (read, local), `app/mcp_service.py:2072` (delete, local), `app/routes.py:486` (migration, local), `app/routes.py:923` (read, local), `app/routes.py:928` (migration, local), `app/routes.py:930` (migration, local), `app/routes.py:3036` (read, local), `app/routes.py:3058` (delete, local), `app/routes.py:3967` (read, local), `app/routes.py:4282` (delete, local), `app/routes.py:4345` (read, local), `app/routes.py:4446` (read, local), `app/routes.py:4471` (read, local), `app/routes.py:4493` (read, local), `app/routes.py:4535` (insert, local), `app/routes.py:4541` (insert, local), `bot/upload.py:388` (insert, local), `tools/project_kb.py:125` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: `/upload_words`, `filters.Regex(upload_words_pattern)`, `filters.Regex(r"^(Добавить слова|Импортировать слова)$")`, `filters.Document.ALL & (~filters.COMMAND)`, `filters.Regex(confirm_pattern)`, `filters.Regex(cancel_pattern)`.

## `users`

- local: `bot/auth.py`:69.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `bot/db.py`:136.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `bot/reminder.py`:59.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `run.py`:56.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_account_linking.py`:33.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER, `auth_provider` TEXT, `account_type` TEXT, `created_at` TEXT DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_advertising.py`:59.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_android_auth.py`:28.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER, `auth_provider` TEXT, `account_type` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_content_pipeline.py`:35.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER DEFAULT 1, `account_type` TEXT DEFAULT 'standard'.
- Индексы: не найдены в этом определении.
- local: `tests/test_db_migrations.py`:11.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_email_auth.py`:30.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER, `auth_provider` TEXT, `account_type` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_family_accounts.py`:124.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_family_pairing_bot.py`:242.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `account_type` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- local: `tests/test_google_account_link.py`:43.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'standard', `auth_provider` TEXT DEFAULT 'telegram', `google_id` TEXT, `google_email` TEXT.
- Индексы: `u_users_google_id` (google_id).
- local: `tests/test_mcp_connector.py`:44.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'standard', `google_id` TEXT, `google_email` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_mcp_lesson_flow.py`:54.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'standard', `google_id` TEXT, `google_email` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_plans.py`:36.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_play_release.py`:31.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER DEFAULT 1, `account_type` TEXT DEFAULT 'standard', `created_at` TEXT DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_registration_notifications.py`:27.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER DEFAULT 1, `account_type` TEXT DEFAULT 'pending', `created_at` TEXT DEFAULT CURRENT_TIMESTAMP, `auth_provider` TEXT, `google_id` TEXT, `google_email` TEXT, `photo_url` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_telegram_native.py`:32.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER, `account_type` TEXT, `auth_provider` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_telegram_onboarding.py`:30.
- Колонки: `user_id` TEXT PRIMARY KEY, `account_type` TEXT NOT NULL DEFAULT 'pending'.
- Индексы: не найдены в этом определении.
- local: `tests/test_tts_usage.py`:257.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `account_type` TEXT DEFAULT 'standard', `is_active` INTEGER DEFAULT 1, `created_at` TEXT.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, `auth_provider` TEXT DEFAULT 'telegram', `google_id` TEXT, `account_type` TEXT NOT NULL DEFAULT 'standard'.
- Индексы: `u_users_google_id` (google_id).
- Чтение/запись/миграции: `app/account_linking.py:34` (read, local), `app/account_linking.py:43` (read, local), `app/account_linking.py:44` (read, local), `app/account_privacy.py:48` (read, local), `app/account_privacy.py:84` (read, local), `app/account_types.py:24` (delete, local), `app/account_types.py:56` (delete, local), `app/account_types.py:80` (read, local), `app/account_types.py:81` (read, local), `app/account_types.py:84` (migration, local), `app/account_types.py:103` (update, local), `app/account_types.py:117` (update, local), `app/android_auth.py:55` (read, local), `app/android_auth.py:88` (read, local), `app/android_auth.py:128` (read, local), `app/android_auth.py:176` (read, local), `app/android_auth.py:328` (read, local), `app/email_auth.py:237` (read, local), `app/email_auth.py:317` (read, local), `app/email_auth.py:330` (insert, local), `app/email_auth.py:386` (read, local), `app/email_auth.py:409` (read, local), `app/family_invites.py:96` (read, local), `app/family_pairing.py:42` (read, local), `app/family_pairing.py:64` (update, local), `app/family_pairing.py:77` (delete, local), `app/family_pairing.py:99` (read, local), `app/family_pairing.py:134` (delete, local), `app/family_pairing.py:157` (read, local), `app/family_pairing.py:197` (read, local).
- Связанные API файла-владельца: `/api/subscription/sync`, `/api/subscription/google-play-notifications`, `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`, `/auth/google`, `/auth/google/callback`, `/api/auth/google/config`, `/api/auth/google/verify`, `/api/auth/google/link`, `/api/auth/android/browser-link`, `/auth/android/browser`, `/api/auth/android/browser-session`, `/api/account/identities`, `/api/auth/android/start`, `/api/auth/telegram/native`, `/api/auth/android/exchange`, `/auth/android/return`, `/privacy`, `/account/delete`, `/api/account/deletion-challenge`.
- Telegram handlers файла-владельца: `/start`, `/open`, `/family`, `r"^onboarding:(?:language|language_keep|language_change|account`, `r"^family_link:(?:confirm|cancel`, `r"^family_join:(?:confirm|cancel`, `filters.Regex(learn_words_pattern)`, `filters.TEXT & (~filters.COMMAND) & exclude_import_btns`, `/reminder_now`.

## `users_new`

- local: `bot/auth.py`:88.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'standard', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `bot/auth.py:88` (migration, local), `bot/auth.py:114` (migration, local), `bot/auth.py:121` (migration, local), `bot/auth.py:126` (migration, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: `/start`, `/open`, `/family`, `r"^onboarding:(?:language|language_keep|language_change|account`, `r"^family_link:(?:confirm|cancel`, `r"^family_join:(?:confirm|cancel`, `filters.Regex(learn_words_pattern)`, `filters.TEXT & (~filters.COMMAND) & exclude_import_btns`.

## `words`

- local: `db_init.py`:22.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT NOT NULL DEFAULT '', `status` TEXT NOT NULL DEFAULT 'user', `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `updated_at` INTEGER.
- Индексы: `idx_words_lesson` (lesson), `idx_words_user_lesson` (user_id, lesson), `u_words_user_lesson_number` (user_id, lesson, number).
- local: `run.py`:67.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT NOT NULL DEFAULT '', `status` TEXT NOT NULL DEFAULT 'user', `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `updated_at` INTEGER.
- Индексы: `idx_words_lesson` (lesson), `idx_words_user_lesson` (user_id, lesson), `u_words_user_lesson_number` (user_id, lesson, number).
- local: `tests/test_account_linking.py`:38.
- Колонки: `user_id` TEXT, `word` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_advertising.py`:65.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `lesson` TEXT, `number` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_content_pipeline.py`:30.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `status` TEXT DEFAULT 'user', `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `difficult` INTEGER DEFAULT 0, `updated_at` INTEGER.
- Индексы: `u_words_user_lesson_number` (user_id,lesson,number).
- local: `tests/test_family_accounts.py`:41.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `lesson` TEXT, `number` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_google_account_link.py`:63.
- Колонки: `id` INTEGER PRIMARY KEY, `user_id` TEXT NOT NULL, `lesson` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_mcp_connector.py`:50.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT NOT NULL, `status` TEXT NOT NULL DEFAULT 'user', `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `difficult` INTEGER DEFAULT 0, `updated_at` INTEGER.
- Индексы: `u_words_user_lesson_number` (user_id,lesson,number).
- local: `tests/test_mcp_lesson_flow.py`:60.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT NOT NULL, `status` TEXT NOT NULL DEFAULT 'user', `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `difficult` INTEGER DEFAULT 0, `updated_at` INTEGER.
- Индексы: `u_words_user_lesson_number` (user_id,lesson,number).
- local: `tests/test_plans.py`:42.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `lesson` TEXT, `number` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_play_release.py`:33.
- Колонки: `id` INTEGER PRIMARY KEY, `user_id` TEXT, `lesson` TEXT, `number` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_project_kb.py`:130.
- Колонки: `id` INTEGER PRIMARY KEY, `nl` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_tts_usage.py`:273.
- Колонки: `id` INTEGER PRIMARY KEY, `user_id` TEXT, `status` TEXT, `lesson` TEXT, `number` INTEGER, `difficult` INTEGER DEFAULT 0, `updated_at` INTEGER.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `difficult` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER, `user_id` TEXT, `status` TEXT NOT NULL DEFAULT 'user', `de` TEXT, `ex_de` TEXT, `audio_de` TEXT, `it` TEXT, `ex_it` TEXT, `audio_it` TEXT, `fr` TEXT, `ex_fr` TEXT, `audio_fr` TEXT.
- Индексы: `idx_words_lesson` (lesson), `idx_words_user_lesson` (user_id, lesson), `u_words_user_lesson_number` (user_id, lesson, number).
- Чтение/запись/миграции: `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:11` (read, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:78` (read, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:81` (read, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:84` (read, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:87` (read, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:90` (read, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:94` (insert, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:99` (update, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:103` (update, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:122` (delete, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:125` (delete, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:128` (read, local), `android/app/src/main/java/app/parallellingvo/data/db/AppDatabase.kt:226` (migration, local), `app/account_privacy.py:63` (read, local), `app/account_privacy.py:64` (read, local), `app/account_privacy.py:68` (delete, local), `app/account_privacy.py:84` (read, local), `app/audio_gen.py:159` (read, local), `app/audio_gen.py:163` (migration, local), `app/audio_gen.py:165` (migration, local), `app/audio_gen.py:174` (read, local), `app/audio_gen.py:186` (read, local), `app/audio_gen.py:218` (read, local), `app/audio_gen.py:263` (update, local), `app/audio_gen.py:298` (read, local), `app/content_service.py:3` (read, local), `app/content_service.py:65` (read, local), `app/content_service.py:70` (migration, local), `app/content_service.py:73` (read, local), `app/content_service.py:84` (read, local).
- Связанные API файла-владельца: `/privacy`, `/account/delete`, `/api/account/deletion-challenge`, `/api/account/delete`, `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/word-database`, `/settings/mcp`, `/settings`, `/account-type`, `/.well-known/assetlinks.json`, `/family/connect`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`.
- Telegram handlers файла-владельца: `/upload_words`, `filters.Regex(upload_words_pattern)`, `filters.Regex(r"^(Добавить слова|Импортировать слова)$")`, `filters.Document.ALL & (~filters.COMMAND)`, `filters.Regex(confirm_pattern)`, `filters.Regex(cancel_pattern)`.
