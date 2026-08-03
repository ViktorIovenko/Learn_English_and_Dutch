# Database map

Схема ниже извлечена из SQL в исходниках и production `sqlite_master`; строки пользователей не читаются.

Создание/миграции распределены между `run.py`, `db_init.py`, `app/routes.py`, `app/models.py`, `bot/db.py`, `bot/auth.py` и специализированными модулями. Это известное дублирование; менять схему следует только после проверки всех владельцев.

## `android_contracts`

- local: `tools/project_kb.py`:86.
- Колонки: `id` INTEGER PRIMARY KEY, `endpoint` TEXT, `http_method` TEXT, `android_file` TEXT, `android_symbol` TEXT, `request_model` TEXT, `response_model` TEXT, `auth_headers_json` TEXT, `backend_file` TEXT, `backend_handler` TEXT, `status` TEXT, `notes` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:86` (read, local), `tools/project_kb.py:86` (migration, local), `tools/project_kb.py:418` (insert, local), `tools/project_kb.py:424` (read, local), `tools/project_kb.py:427` (update, local), `tools/project_kb.py:429` (update, local), `tools/project_kb.py:449` (delete, local), `tools/project_kb.py:467` (read, local), `tools/project_kb.py:510` (read, local), `tools/project_kb.py:526` (read, local), `tools/project_kb.py:563` (read, local), `tools/project_kb.py:578` (delete, local), `tools/project_kb.py:712` (read, local), `tools/project_kb.py:823` (read, local), `tools/project_kb.py:830` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `app_schema_migrations`

- local: `app/account_types.py`:20.
- Колонки: `name` TEXT PRIMARY KEY, `applied_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `name` TEXT PRIMARY KEY, `applied_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_types.py:20` (migration, local), `app/account_types.py:26` (read, local), `app/account_types.py:41` (insert, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `child_goal_notifications`

- local: `app/routes.py`:454.
- Колонки: `child_user_id` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `local_date` TEXT NOT NULL, `message_id` INTEGER, `sent_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `child_user_id` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `local_date` TEXT NOT NULL, `message_id` INTEGER, `sent_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/routes.py:454` (migration, local), `app/routes.py:465` (read, local), `app/routes.py:470` (migration, local), `app/routes.py:610` (read, local), `app/routes.py:618` (insert, local), `app/routes.py:637` (update, local), `app/routes.py:659` (delete, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: нет прямой связи.

## `child_lesson_priorities`

- local: `app/routes.py`:725.
- Колонки: `child_user_id` TEXT PRIMARY KEY, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `child_user_id` TEXT PRIMARY KEY, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/routes.py:725` (migration, local), `app/routes.py:754` (read, local), `app/routes.py:771` (read, local), `app/routes.py:2820` (read, local), `app/routes.py:2835` (insert, local), `app/routes.py:2850` (delete, local), `app/routes.py:4211` (delete, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: нет прямой связи.

## `child_lesson_priority_history`

- local: `app/routes.py`:735.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `started_at` INTEGER NOT NULL, `ended_at` INTEGER.
- Индексы: `idx_child_priority_history_child_started` (child_user_id, started_at DESC).
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `started_at` INTEGER NOT NULL, `ended_at` INTEGER.
- Индексы: `idx_child_priority_history_child_started` (child_user_id, started_at DESC).
- Чтение/запись/миграции: `app/routes.py:735` (migration, local), `app/routes.py:748` (read, local), `app/routes.py:751` (insert, local), `app/routes.py:757` (read, local), `app/routes.py:936` (read, local), `app/routes.py:2829` (update, local), `app/routes.py:2844` (insert, local), `app/routes.py:4219` (delete, local), `tests/test_family_accounts.py:523` (update, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: нет прямой связи.

## `database_tables`

- local: `tools/project_kb.py`:76.
- Колонки: `id` INTEGER PRIMARY KEY, `table_name` TEXT, `defined_in` TEXT, `definition_line` INTEGER, `columns_json` TEXT, `indexes_json` TEXT, `environment` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:65` (read, local), `tools/project_kb.py:76` (migration, local), `tools/project_kb.py:372` (insert, local), `tools/project_kb.py:447` (read, local), `tools/project_kb.py:448` (delete, local), `tools/project_kb.py:491` (read, local), `tools/project_kb.py:494` (read, local), `tools/project_kb.py:554` (read, local), `tools/project_kb.py:563` (read, local), `tools/project_kb.py:577` (delete, local), `tools/project_kb.py:646` (delete, local), `tools/project_kb.py:654` (insert, local), `tools/project_kb.py:709` (read, local), `tools/project_kb.py:822` (read, local), `tools/project_kb.py:830` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `database_usage`

- local: `tools/project_kb.py`:80.
- Колонки: `id` INTEGER PRIMARY KEY, `table_name` TEXT, `file_path` TEXT, `symbol_name` TEXT, `operation` TEXT, `line_number` INTEGER, `source_scope` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tools/project_kb.py:80` (migration, local), `tools/project_kb.py:381` (insert, local), `tools/project_kb.py:447` (read, local), `tools/project_kb.py:499` (read, local), `tools/project_kb.py:501` (read, local), `tools/project_kb.py:502` (read, local), `tools/project_kb.py:577` (delete, local), `tools/project_kb.py:815` (read, local), `tools/project_kb.py:822` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `deployment_routes`

- local: `tools/project_kb.py`:96.
- Колонки: `id` INTEGER PRIMARY KEY, `server_name` TEXT, `public_path` TEXT, `proxy_target` TEXT, `nginx_config_path` TEXT, `backend_service` TEXT, `notes` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tools/project_kb.py:96` (migration, local), `tools/project_kb.py:639` (delete, local), `tools/project_kb.py:645` (insert, local), `tools/project_kb.py:715` (read, local), `tools/project_kb.py:826` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `docs`

- local: `tools/project_kb.py`:109.
- Колонки: `id` INTEGER PRIMARY KEY, `key` TEXT UNIQUE, `title` TEXT, `content` TEXT, `source_path` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tools/project_kb.py:28` (read, local), `tools/project_kb.py:109` (migration, local), `tools/project_kb.py:123` (read, local), `tools/project_kb.py:129` (read, local), `tools/project_kb.py:131` (read, local), `tools/project_kb.py:133` (read, local), `tools/project_kb.py:135` (read, local), `tools/project_kb.py:183` (read, local), `tools/project_kb.py:468` (read, local), `tools/project_kb.py:480` (insert, local), `tools/project_kb.py:783` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `environment_snapshots`

- local: `tools/project_kb.py`:100.
- Колонки: `id` INTEGER PRIMARY KEY, `environment` TEXT, `git_branch` TEXT, `git_commit` TEXT, `git_dirty` INTEGER, `project_path` TEXT, `captured_at` TEXT, `tracked_files_json` TEXT, `entrypoints_json` TEXT, `schema_hash` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:136` (read, local), `tools/project_kb.py:100` (migration, local), `tools/project_kb.py:549` (insert, local), `tools/project_kb.py:656` (insert, local), `tools/project_kb.py:702` (read, local), `tools/project_kb.py:828` (read, local), `tools/project_kb.py:830` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `family_pairing_codes`

- local: `app/family_pairing.py`:23.
- Колонки: `code` TEXT PRIMARY KEY, `child_user_id` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: `idx_family_pairing_codes_child` (child_user_id).
- production: `/app/words.db sqlite_master`.
- Колонки: `code` TEXT PRIMARY KEY, `child_user_id` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: `idx_family_pairing_codes_child` (child_user_id).
- Чтение/запись/миграции: `app/family_pairing.py:23` (migration, local), `app/family_pairing.py:33` (read, local), `app/family_pairing.py:54` (delete, local), `app/family_pairing.py:62` (insert, local), `app/family_pairing.py:105` (read, local), `app/family_pairing.py:110` (delete, local), `app/family_pairing.py:148` (read, local), `app/family_pairing.py:154` (delete, local), `tests/test_family_pairing_bot.py:110` (update, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `files`

- local: `tools/project_kb.py`:60.
- Колонки: `path` TEXT NOT NULL, `source_scope` TEXT NOT NULL, `language` TEXT, `layer` TEXT, `purpose` TEXT, `size_bytes` INTEGER, `sha256` TEXT, `indexed_at` TEXT, `is_generated` INTEGER NOT NULL DEFAULT 0, `is_entrypoint` INTEGER NOT NULL DEFAULT 0.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:47` (delete, local), `tests/test_project_kb.py:49` (read, local), `tools/project_kb.py:60` (migration, local), `tools/project_kb.py:135` (read, local), `tools/project_kb.py:153` (read, local), `tools/project_kb.py:445` (read, local), `tools/project_kb.py:450` (insert, local), `tools/project_kb.py:465` (read, local), `tools/project_kb.py:547` (read, local), `tools/project_kb.py:548` (read, local), `tools/project_kb.py:550` (read, local), `tools/project_kb.py:563` (read, local), `tools/project_kb.py:568` (update, local), `tools/project_kb.py:570` (read, local), `tools/project_kb.py:573` (read, local), `tools/project_kb.py:574` (read, local), `tools/project_kb.py:577` (delete, local), `tools/project_kb.py:706` (read, local), `tools/project_kb.py:708` (read, local), `tools/project_kb.py:718` (update, local), `tools/project_kb.py:735` (read, local), `tools/project_kb.py:738` (read, local), `tools/project_kb.py:798` (update, local), `tools/project_kb.py:801` (read, local), `tools/project_kb.py:805` (update, local), `tools/project_kb.py:818` (read, local), `tools/project_kb.py:830` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `frontend_links`

- local: `tools/project_kb.py`:83.
- Колонки: `id` INTEGER PRIMARY KEY, `source_file` TEXT, `target_type` TEXT, `target_value` TEXT, `line_number` INTEGER, `source_scope` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tools/project_kb.py:83` (migration, local), `tools/project_kb.py:397` (insert, local), `tools/project_kb.py:447` (read, local), `tools/project_kb.py:511` (read, local), `tools/project_kb.py:532` (read, local), `tools/project_kb.py:533` (read, local), `tools/project_kb.py:577` (delete, local).
- Связанные API файла-владельца: проверять по handler.
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
- Чтение/запись/миграции: `app/routes.py:4248` (delete, local), `app/tts_usage.py:98` (migration, local), `app/tts_usage.py:107` (insert, local), `app/tts_usage.py:126` (delete, local), `app/tts_usage.py:133` (insert, local), `app/tts_usage.py:146` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
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
- Чтение/запись/миграции: `tools/project_kb.py:69` (migration, local), `tools/project_kb.py:285` (insert, local), `tools/project_kb.py:288` (insert, local), `tools/project_kb.py:447` (read, local), `tools/project_kb.py:577` (delete, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `kb_capabilities`

- local: `tools/project_kb.py`:238.
- Колонки: `name` TEXT PRIMARY KEY, `enabled` INTEGER.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:103` (read, local), `tools/project_kb.py:221` (migration, local), `tools/project_kb.py:222` (insert, local), `tools/project_kb.py:234` (migration, local), `tools/project_kb.py:235` (insert, local), `tools/project_kb.py:238` (migration, local), `tools/project_kb.py:239` (insert, local), `tools/project_kb.py:461` (read, local), `tools/project_kb.py:830` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `parent_child_links`

- local: `app/routes.py`:710.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `run.py`:126.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_family_pairing_bot.py`:158.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: `idx_parent_child_links_child` (child_user_id).
- Чтение/запись/миграции: `app/family_pairing.py:79` (read, local), `app/family_pairing.py:173` (read, local), `app/family_pairing.py:179` (read, local), `app/family_pairing.py:186` (insert, local), `app/routes.py:594` (read, local), `app/routes.py:710` (migration, local), `app/routes.py:722` (read, local), `app/routes.py:808` (read, local), `app/routes.py:828` (read, local), `app/routes.py:835` (read, local), `app/routes.py:864` (read, local), `app/routes.py:891` (read, local), `app/routes.py:1721` (read, local), `app/routes.py:2067` (read, local), `app/routes.py:2801` (read, local), `app/routes.py:2948` (read, local), `app/routes.py:2954` (read, local), `app/routes.py:2960` (insert, local), `app/routes.py:2983` (delete, local), `app/routes.py:3905` (read, local), `app/routes.py:4158` (delete, local), `app/routes.py:4203` (delete, local), `tests/test_family_accounts.py:244` (insert, local), `tests/test_family_accounts.py:312` (insert, local), `tests/test_family_accounts.py:489` (insert, local), `tests/test_family_accounts.py:577` (insert, local), `tests/test_family_accounts.py:720` (insert, local), `tests/test_family_accounts.py:739` (insert, local), `tests/test_family_accounts.py:761` (read, local), `tests/test_family_pairing_bot.py:64` (migration, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: нет прямой связи.

## `progress_events`

- local: `app/routes.py`:439.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `scope` TEXT, `event_type` TEXT, `event_ts` INTEGER, `payload` TEXT, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: `idx_progress_events_user_ts` (user_id, event_ts).
- local: `tests/test_project_kb.py`:60.
- Колонки: `id` INTEGER PRIMARY KEY, `user_id` TEXT.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `scope` TEXT, `event_type` TEXT, `event_ts` INTEGER, `payload` TEXT, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: `idx_progress_events_user_ts` (user_id, event_ts).
- Чтение/запись/миграции: `app/routes.py:439` (migration, local), `app/routes.py:451` (read, local), `app/routes.py:528` (read, local), `app/routes.py:905` (read, local), `app/routes.py:913` (read, local), `app/routes.py:1146` (read, local), `app/routes.py:1697` (read, local), `app/routes.py:3249` (read, local), `app/routes.py:3688` (insert, local), `app/routes.py:4230` (read, local), `tests/test_family_accounts.py:272` (insert, local), `tests/test_family_accounts.py:353` (insert, local), `tests/test_family_accounts.py:413` (insert, local), `tests/test_project_kb.py:58` (insert, local), `tests/test_project_kb.py:60` (migration, local), `tests/test_project_kb.py:65` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: нет прямой связи.

## `reminder_state`

- local: `bot/reminder.py`:51.
- Колонки: `user_id` TEXT PRIMARY KEY, `last_msg_id` INTEGER, `last_sent_date` TEXT.
- Индексы: не найдены в этом определении.
- local: `run.py`:101.
- Колонки: `user_id` TEXT PRIMARY KEY, `last_msg_id` INTEGER, `last_sent_date` TEXT.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `last_msg_id` INTEGER, `last_sent_date` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `bot/reminder.py:51` (migration, local), `bot/reminder.py:88` (read, local), `bot/reminder.py:102` (insert, local), `docs/codex/ARCHITECTURE.md:18` (update, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: `/reminder_now`.

## `routes`

- local: `tools/project_kb.py`:72.
- Колонки: `id` INTEGER PRIMARY KEY, `route_type` TEXT, `method_or_trigger` TEXT, `route_or_command` TEXT, `handler` TEXT, `file_path` TEXT, `line_number` INTEGER, `auth_type` TEXT, `purpose` TEXT, `source_scope` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:52` (read, local), `tests/test_project_kb.py:64` (read, local), `tests/test_project_kb.py:70` (read, local), `tools/project_kb.py:72` (migration, local), `tools/project_kb.py:117` (read, local), `tools/project_kb.py:119` (read, local), `tools/project_kb.py:121` (update, local), `tools/project_kb.py:123` (read, local), `tools/project_kb.py:125` (read, local), `tools/project_kb.py:127` (read, local), `tools/project_kb.py:131` (read, local), `tools/project_kb.py:193` (read, local), `tools/project_kb.py:278` (insert, local), `tools/project_kb.py:345` (insert, local), `tools/project_kb.py:423` (read, local), `tools/project_kb.py:425` (read, local), `tools/project_kb.py:447` (read, local), `tools/project_kb.py:450` (insert, local), `tools/project_kb.py:466` (read, local), `tools/project_kb.py:489` (read, local), `tools/project_kb.py:501` (read, local), `tools/project_kb.py:502` (read, local), `tools/project_kb.py:509` (read, local), `tools/project_kb.py:521` (read, local), `tools/project_kb.py:563` (read, local), `tools/project_kb.py:577` (delete, local), `tools/project_kb.py:591` (read, local), `tools/project_kb.py:598` (read, local), `tools/project_kb.py:627` (read, local), `tools/project_kb.py:643` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `services`

- local: `tools/project_kb.py`:91.
- Колонки: `id` INTEGER PRIMARY KEY, `environment` TEXT, `service_name` TEXT, `service_type` TEXT, `working_directory` TEXT, `exec_start_redacted` TEXT, `user_name` TEXT, `group_name` TEXT, `environment_file_path` TEXT, `port` TEXT, `source_file` TEXT, `last_indexed_at` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:122` (read, local), `tests/test_project_kb.py:135` (read, local), `tools/project_kb.py:91` (migration, local), `tools/project_kb.py:591` (read, local), `tools/project_kb.py:596` (read, local), `tools/project_kb.py:639` (delete, local), `tools/project_kb.py:640` (read, local), `tools/project_kb.py:642` (insert, local), `tools/project_kb.py:667` (read, local), `tools/project_kb.py:714` (read, local), `tools/project_kb.py:806` (read, local), `tools/project_kb.py:824` (read, local), `tools/project_kb.py:825` (read, local), `tools/project_kb.py:830` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `shared_word_sets`

- local: `app/routes.py`:1408.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `token` TEXT NOT NULL UNIQUE, `owner_user_id` TEXT NOT NULL, `title` TEXT NOT NULL, `lesson` TEXT, `payload` TEXT NOT NULL, `created_at` INTEGER NOT NULL, `expires_at` INTEGER, `import_count` INTEGER NOT NULL DEFAULT 0, `max_imports` INTEGER.
- Индексы: `idx_shared_word_sets_token` (token).
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `token` TEXT NOT NULL UNIQUE, `owner_user_id` TEXT NOT NULL, `title` TEXT NOT NULL, `lesson` TEXT, `payload` TEXT NOT NULL, `created_at` INTEGER NOT NULL, `expires_at` INTEGER, `import_count` INTEGER NOT NULL DEFAULT 0, `max_imports` INTEGER.
- Индексы: `idx_shared_word_sets_token` (token).
- Чтение/запись/миграции: `app/routes.py:1408` (migration, local), `app/routes.py:1423` (read, local), `app/routes.py:1841` (read, local), `app/routes.py:1955` (read, local), `app/routes.py:1959` (insert, local), `app/routes.py:2150` (read, local), `app/routes.py:2236` (update, local), `app/routes.py:4238` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: нет прямой связи.

## `symbols`

- local: `tools/project_kb.py`:65.
- Колонки: `id` INTEGER PRIMARY KEY, `name` TEXT, `symbol_type` TEXT, `signature` TEXT, `file_path` TEXT, `line_start` INTEGER, `line_end` INTEGER, `docstring` TEXT, `parent_symbol` TEXT, `source_scope` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:45` (read, local), `tests/test_project_kb.py:48` (delete, local), `tests/test_project_kb.py:63` (read, local), `tools/project_kb.py:65` (migration, local), `tools/project_kb.py:268` (insert, local), `tools/project_kb.py:272` (insert, local), `tools/project_kb.py:329` (insert, local), `tools/project_kb.py:447` (read, local), `tools/project_kb.py:464` (read, local), `tools/project_kb.py:563` (read, local), `tools/project_kb.py:577` (delete, local), `tools/project_kb.py:813` (read, local), `tools/project_kb.py:816` (read, local), `tools/project_kb.py:819` (read, local), `tools/project_kb.py:830` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `task_routes`

- local: `tools/project_kb.py`:105.
- Колонки: `id` INTEGER PRIMARY KEY, `topic` TEXT UNIQUE, `keywords` TEXT, `primary_files_json` TEXT, `secondary_files_json` TEXT, `excluded_paths_json` TEXT, `recommended_checks_json` TEXT, `environment_scope` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `docs/codex/TASK_ROUTING.md:19` (read, local), `tools/project_kb.py:105` (migration, local), `tools/project_kb.py:113` (read, local), `tools/project_kb.py:469` (read, local), `tools/project_kb.py:540` (read, local), `tools/project_kb.py:541` (insert, local), `tools/project_kb.py:760` (read, local).
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

- local: `app/routes.py`:483.
- Колонки: `user_id` TEXT PRIMARY KEY, `goal_value` INTEGER NOT NULL, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `goal_value` INTEGER NOT NULL, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/routes.py:483` (migration, local), `app/routes.py:500` (read, local), `app/routes.py:3525` (insert, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_language_preferences`

- local: `app/routes.py`:672.
- Колонки: `user_id` TEXT NOT NULL, `priority` INTEGER NOT NULL, `lang_code` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_language_preferences_user` (user_id, priority).
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT NOT NULL, `priority` INTEGER NOT NULL, `lang_code` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_language_preferences_user` (user_id, priority).
- Чтение/запись/миграции: `app/routes.py:672` (migration, local), `app/routes.py:683` (read, local), `app/routes.py:1353` (read, local), `app/routes.py:3141` (delete, local), `app/routes.py:3143` (insert, local), `app/routes.py:4231` (read, local), `tests/test_family_accounts.py:384` (insert, local), `tests/test_family_accounts.py:444` (insert, local), `tests/test_family_accounts.py:595` (insert, local), `tests/test_family_accounts.py:602` (insert, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_lessons`

- local: `app/models.py`:19.
- Колонки: `user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `hidden` INTEGER NOT NULL DEFAULT 0, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `hidden` INTEGER NOT NULL DEFAULT 0, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, `updated_at_ts` INTEGER.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/models.py:19` (migration, local), `app/models.py:27` (read, local), `app/models.py:29` (migration, local), `app/models.py:31` (update, local), `app/models.py:70` (read, local), `app/models.py:138` (insert, local), `app/routes.py:3340` (read, local), `app/routes.py:3350` (delete, local), `app/routes.py:3406` (delete, local), `app/routes.py:3748` (read, local), `app/routes.py:3752` (read, local), `app/routes.py:3755` (read, local), `app/routes.py:3777` (read, local), `app/routes.py:3794` (read, local), `app/routes.py:4229` (read, local), `tests/test_family_accounts.py:472` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_settings`

- local: `app/routes.py`:696.
- Колонки: `user_id` TEXT PRIMARY KEY, `detected_ui_language` TEXT, `ui_language_override` TEXT, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- local: `bot/onboarding.py`:439.
- Колонки: `user_id` TEXT PRIMARY KEY, `detected_ui_language` TEXT, `ui_language_override` TEXT, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `detected_ui_language` TEXT, `ui_language_override` TEXT, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/routes.py:696` (migration, local), `app/routes.py:1185` (insert, local), `app/routes.py:1203` (read, local), `app/routes.py:1233` (insert, local), `app/routes.py:4232` (read, local), `bot/onboarding.py:439` (migration, local), `bot/onboarding.py:454` (insert, local), `bot/onboarding.py:468` (read, local), `bot/onboarding.py:484` (insert, local), `tests/test_family_accounts.py:391` (insert, local), `tests/test_family_accounts.py:451` (insert, local), `tests/test_telegram_onboarding.py:87` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_subscriptions`

- local: `app/routes.py`:1246.
- Колонки: `user_id` TEXT PRIMARY KEY, `status` TEXT NOT NULL DEFAULT 'trial', `trial_started_at` INTEGER NOT NULL, `trial_ends_at` INTEGER NOT NULL, `current_period_ends_at` INTEGER, `provider` TEXT, `provider_customer_id` TEXT, `provider_subscription_id` TEXT, `cancel_at_period_end` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_subscriptions_status` (status, trial_ends_at, current_period_ends_at).
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `status` TEXT NOT NULL DEFAULT 'trial', `trial_started_at` INTEGER NOT NULL, `trial_ends_at` INTEGER NOT NULL, `current_period_ends_at` INTEGER, `provider` TEXT, `provider_customer_id` TEXT, `provider_subscription_id` TEXT, `cancel_at_period_end` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_subscriptions_status` (status, trial_ends_at, current_period_ends_at).
- Чтение/запись/миграции: `app/routes.py:1246` (migration, local), `app/routes.py:1261` (read, local), `app/routes.py:1290` (read, local), `app/routes.py:1297` (insert, local), `app/routes.py:1302` (read, local), `app/routes.py:1707` (read, local), `app/routes.py:3046` (insert, local), `app/routes.py:3898` (read, local), `app/routes.py:4103` (insert, local), `app/routes.py:4132` (update, local), `app/routes.py:4233` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_word_flags`

- local: `app/routes.py`:426.
- Колонки: `user_id` TEXT NOT NULL, `word_id` INTEGER NOT NULL, `difficult` INTEGER NOT NULL DEFAULT 1.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT NOT NULL, `word_id` INTEGER NOT NULL, `difficult` INTEGER NOT NULL DEFAULT 1.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/routes.py:426` (migration, local), `app/routes.py:2429` (read, local), `app/routes.py:2449` (delete, local), `app/routes.py:3211` (read, local), `app/routes.py:3398` (delete, local), `app/routes.py:3454` (read, local), `app/routes.py:3550` (read, local), `app/routes.py:3575` (read, local), `app/routes.py:3596` (read, local), `app/routes.py:3631` (insert, local), `app/routes.py:3637` (insert, local), `app/routes.py:4199` (delete, local), `app/routes.py:4228` (read, local), `bot/upload.py:408` (insert, local), `tools/project_kb.py:125` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: `/upload_words`, `filters.Regex(upload_words_pattern)`, `filters.Regex(r"^(Добавить слова|Импортировать слова)$")`, `filters.Document.ALL & (~filters.COMMAND)`, `filters.Regex(r"(?i)^(импортировать как есть)$")`, `filters.Regex(r"(?i)^(отменить импорт)$")`.

## `users`

- local: `bot/auth.py`:61.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `bot/db.py`:136.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `bot/reminder.py`:58.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `run.py`:48.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_family_accounts.py`:90.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_family_pairing_bot.py`:149.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `account_type` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- local: `tests/test_telegram_onboarding.py`:30.
- Колонки: `user_id` TEXT PRIMARY KEY, `account_type` TEXT NOT NULL DEFAULT 'pending'.
- Индексы: не найдены в этом определении.
- local: `tests/test_tts_usage.py`:252.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `account_type` TEXT DEFAULT 'standard', `is_active` INTEGER DEFAULT 1, `created_at` TEXT.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, `auth_provider` TEXT DEFAULT 'telegram', `google_id` TEXT, `account_type` TEXT NOT NULL DEFAULT 'standard'.
- Индексы: `u_users_google_id` (google_id).
- Чтение/запись/миграции: `app/account_types.py:11` (read, local), `app/account_types.py:12` (read, local), `app/account_types.py:15` (migration, local), `app/account_types.py:34` (update, local), `app/account_types.py:48` (update, local), `app/family_pairing.py:28` (delete, local), `app/family_pairing.py:48` (read, local), `app/family_pairing.py:80` (read, local), `app/family_pairing.py:106` (read, local), `app/family_pairing.py:135` (read, local), `app/family_pairing.py:164` (read, local), `app/google_auth.py:52` (read, local), `app/google_auth.py:61` (insert, local), `app/routes.py:260` (read, local), `app/routes.py:277` (read, local), `app/routes.py:354` (read, local), `app/routes.py:356` (insert, local), `app/routes.py:377` (read, local), `app/routes.py:379` (insert, local), `app/routes.py:589` (read, local), `app/routes.py:595` (read, local), `app/routes.py:716` (delete, local), `app/routes.py:717` (delete, local), `app/routes.py:730` (delete, local), `app/routes.py:731` (delete, local), `app/routes.py:742` (delete, local), `app/routes.py:743` (delete, local), `app/routes.py:804` (read, local), `app/routes.py:829` (read, local), `app/routes.py:836` (read, local).
- Связанные API файла-владельца: `/auth/google`, `/auth/google/callback`, `/api/auth/google/verify`, `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`.
- Telegram handlers файла-владельца: `/start`, `/open`, `/family`, `r"^onboarding:(?:language|language_keep|language_change|account`, `r"^family_link:(?:confirm|cancel`, `filters.Regex(learn_words_pattern)`, `filters.TEXT & (~filters.COMMAND) & exclude_import_btns`, `/reminder_now`.

## `users_new`

- local: `bot/auth.py`:80.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'standard', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `bot/auth.py:80` (migration, local), `bot/auth.py:106` (migration, local), `bot/auth.py:113` (migration, local), `bot/auth.py:118` (migration, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: `/start`, `/open`, `/family`, `r"^onboarding:(?:language|language_keep|language_change|account`, `r"^family_link:(?:confirm|cancel`, `filters.Regex(learn_words_pattern)`, `filters.TEXT & (~filters.COMMAND) & exclude_import_btns`.

## `words`

- local: `db_init.py`:22.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT NOT NULL DEFAULT '', `status` TEXT NOT NULL DEFAULT 'user', `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `updated_at` INTEGER.
- Индексы: `idx_words_lesson` (lesson), `idx_words_user_lesson` (user_id, lesson), `u_words_user_lesson_number` (user_id, lesson, number).
- local: `run.py`:59.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT NOT NULL DEFAULT '', `status` TEXT NOT NULL DEFAULT 'user', `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `updated_at` INTEGER.
- Индексы: `idx_words_lesson` (lesson), `idx_words_user_lesson` (user_id, lesson), `u_words_user_lesson_number` (user_id, lesson, number).
- local: `tests/test_family_accounts.py`:39.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `lesson` TEXT, `number` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_project_kb.py`:130.
- Колонки: `id` INTEGER PRIMARY KEY, `nl` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_tts_usage.py`:268.
- Колонки: `id` INTEGER PRIMARY KEY, `user_id` TEXT, `status` TEXT, `lesson` TEXT, `number` INTEGER, `difficult` INTEGER DEFAULT 0, `updated_at` INTEGER.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `difficult` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER, `user_id` TEXT, `status` TEXT NOT NULL DEFAULT 'user', `de` TEXT, `ex_de` TEXT, `audio_de` TEXT, `it` TEXT, `ex_it` TEXT, `audio_it` TEXT, `fr` TEXT, `ex_fr` TEXT, `audio_fr` TEXT.
- Индексы: `idx_words_lesson` (lesson), `idx_words_user_lesson` (user_id, lesson), `u_words_user_lesson_number` (user_id, lesson, number).
- Чтение/запись/миграции: `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:11` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:77` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:80` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:83` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:86` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:89` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:93` (insert, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:98` (update, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:102` (update, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:121` (delete, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:124` (delete, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:127` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:225` (migration, local), `app/audio_gen.py:169` (read, local), `app/audio_gen.py:171` (migration, local), `app/audio_gen.py:172` (update, local), `app/audio_gen.py:177` (migration, local), `app/audio_gen.py:194` (read, local), `app/audio_gen.py:290` (update, local), `app/audio_gen.py:296` (update, local), `app/models.py:46` (read, local), `app/models.py:62` (read, local), `app/models.py:111` (read, local), `app/models.py:167` (read, local), `app/routes.py:116` (read, local), `app/routes.py:120` (migration, local), `app/routes.py:125` (read, local), `app/routes.py:400` (read, local), `app/routes.py:401` (read, local), `app/routes.py:403` (migration, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`, `/api/account/type`.
- Telegram handlers файла-владельца: `/upload_words`, `filters.Regex(upload_words_pattern)`, `filters.Regex(r"^(Добавить слова|Импортировать слова)$")`, `filters.Document.ALL & (~filters.COMMAND)`, `filters.Regex(r"(?i)^(импортировать как есть)$")`, `filters.Regex(r"(?i)^(отменить импорт)$")`.
