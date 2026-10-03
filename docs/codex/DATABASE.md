# Database map

Схема ниже извлечена из SQL в исходниках и production `sqlite_master`; строки пользователей не читаются.

Создание/миграции распределены между `run.py`, `db_init.py`, `app/routes.py`, `app/models.py`, `bot/db.py`, `bot/auth.py` и специализированными модулями. Это известное дублирование; менять схему следует только после проверки всех владельцев.

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
- local: `run.py`:128.
- Колонки: `provider` TEXT NOT NULL, `external_id` TEXT NOT NULL, `user_id` TEXT NOT NULL, `email` TEXT, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: `idx_auth_identities_user` (user_id).
- local: `tests/test_db_migrations.py`:21.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT NOT NULL, `provider` TEXT NOT NULL, `subject` TEXT NOT NULL, `provider_user_id` TEXT, `email` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_google_account_link.py`:54.
- Колонки: `provider` TEXT NOT NULL, `external_id` TEXT NOT NULL, `user_id` TEXT NOT NULL, `email` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_types.py:13` (read, local), `app/account_types.py:17` (migration, local), `app/account_types.py:29` (read, local), `app/account_types.py:33` (read, local), `app/account_types.py:37` (read, local), `app/account_types.py:44` (read, local), `app/account_types.py:64` (read, local), `app/account_types.py:69` (read, local), `app/account_types.py:71` (migration, local), `app/account_types.py:75` (read, local), `app/google_auth.py:47` (read, local), `app/google_auth.py:51` (read, local), `app/google_auth.py:55` (read, local), `app/google_auth.py:92` (read, local), `app/google_auth.py:101` (update, local), `app/google_auth.py:124` (insert, local), `app/google_auth.py:143` (read, local), `app/google_auth.py:151` (read, local), `app/google_auth.py:161` (read, local), `app/google_auth.py:198` (update, local), `app/google_auth.py:213` (insert, local), `app/routes.py:3000` (insert, local), `run.py:128` (migration, local), `run.py:138` (migration, local), `run.py:140` (insert, local), `run.py:145` (insert, local), `tests/test_db_migrations.py:21` (migration, local), `tests/test_db_migrations.py:35` (insert, local), `tests/test_db_migrations.py:43` (read, local), `tests/test_db_migrations.py:47` (read, local).
- Связанные API файла-владельца: `/auth/google`, `/auth/google/callback`, `/api/auth/google/config`, `/api/auth/google/verify`, `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `auth_identities__canonical_new`

- local: `app/account_types.py`:49.
- Колонки: `provider` TEXT NOT NULL, `external_id` TEXT NOT NULL, `user_id` TEXT NOT NULL, `email` TEXT, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/account_types.py:47` (read, local), `app/account_types.py:49` (migration, local), `app/account_types.py:60` (insert, local), `app/account_types.py:71` (migration, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `child_goal_notifications`

- local: `app/routes.py`:485.
- Колонки: `child_user_id` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `local_date` TEXT NOT NULL, `message_id` INTEGER, `sent_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `child_user_id` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `local_date` TEXT NOT NULL, `message_id` INTEGER, `sent_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/routes.py:485` (migration, local), `app/routes.py:496` (read, local), `app/routes.py:501` (migration, local), `app/routes.py:641` (read, local), `app/routes.py:649` (insert, local), `app/routes.py:668` (update, local), `app/routes.py:690` (delete, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: нет прямой связи.

## `child_lesson_priorities`

- local: `app/routes.py`:841.
- Колонки: `child_user_id` TEXT PRIMARY KEY, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `child_user_id` TEXT PRIMARY KEY, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_service.py:1011` (read, local), `app/mcp_service.py:1023` (delete, local), `app/mcp_service.py:1104` (delete, local), `app/mcp_service.py:1137` (insert, local), `app/mcp_service.py:1158` (delete, local), `app/routes.py:841` (migration, local), `app/routes.py:870` (read, local), `app/routes.py:908` (read, local), `app/routes.py:940` (delete, local), `app/routes.py:3225` (read, local), `app/routes.py:3240` (insert, local), `app/routes.py:3255` (delete, local), `app/routes.py:3923` (update, local), `app/routes.py:4832` (delete, local), `tests/test_family_accounts.py:876` (read, local), `tests/test_family_accounts.py:964` (insert, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: нет прямой связи.

## `child_lesson_priority_history`

- local: `app/routes.py`:851.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `started_at` INTEGER NOT NULL, `ended_at` INTEGER.
- Индексы: `idx_child_priority_history_child_started` (child_user_id, started_at DESC).
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `parent_user_id` TEXT NOT NULL, `started_at` INTEGER NOT NULL, `ended_at` INTEGER.
- Индексы: `idx_child_priority_history_child_started` (child_user_id, started_at DESC).
- Чтение/запись/миграции: `app/mcp_service.py:1020` (update, local), `app/mcp_service.py:1108` (update, local), `app/mcp_service.py:1142` (update, local), `app/mcp_service.py:1145` (read, local), `app/mcp_service.py:1147` (insert, local), `app/mcp_service.py:1157` (update, local), `app/routes.py:851` (migration, local), `app/routes.py:864` (read, local), `app/routes.py:867` (insert, local), `app/routes.py:873` (read, local), `app/routes.py:944` (update, local), `app/routes.py:1196` (read, local), `app/routes.py:3234` (update, local), `app/routes.py:3249` (insert, local), `app/routes.py:3927` (update, local), `app/routes.py:4840` (delete, local), `tests/test_family_accounts.py:564` (update, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
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

## `environment_snapshots`

- local: `tools/project_kb.py`:100.
- Колонки: `id` INTEGER PRIMARY KEY, `environment` TEXT, `git_branch` TEXT, `git_commit` TEXT, `git_dirty` INTEGER, `project_path` TEXT, `captured_at` TEXT, `tracked_files_json` TEXT, `entrypoints_json` TEXT, `schema_hash` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `tests/test_project_kb.py:136` (read, local), `tools/project_kb.py:100` (migration, local), `tools/project_kb.py:552` (insert, local), `tools/project_kb.py:659` (insert, local), `tools/project_kb.py:707` (read, local), `tools/project_kb.py:833` (read, local), `tools/project_kb.py:835` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `family_invite_codes`

- local: `app/family_pairing.py`:93.
- Колонки: `code` TEXT PRIMARY KEY, `parent_user_id` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: `idx_family_invite_codes_parent` (parent_user_id).
- Чтение/запись/миграции: `app/family_pairing.py:93` (migration, local), `app/family_pairing.py:103` (read, local), `app/family_pairing.py:125` (delete, local), `app/family_pairing.py:133` (insert, local), `app/family_pairing.py:158` (read, local), `app/family_pairing.py:163` (delete, local), `app/family_pairing.py:202` (read, local), `app/family_pairing.py:208` (delete, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `family_lesson_assignments`

- local: `app/mcp_service.py`:187.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: `idx_family_lesson_assignments_child` (child_user_id, lesson).
- local: `app/routes.py`:761.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/content_service.py:333` (read, local), `app/content_service.py:334` (read, local), `app/content_service.py:336` (read, local), `app/mcp_service.py:187` (migration, local), `app/mcp_service.py:195` (read, local), `app/mcp_service.py:525` (read, local), `app/mcp_service.py:983` (read, local), `app/mcp_service.py:1001` (migration, local), `app/mcp_service.py:1003` (migration, local), `app/mcp_service.py:1033` (read, local), `app/mcp_service.py:1049` (update, local), `app/mcp_service.py:1100` (delete, local), `app/mcp_service.py:1120` (read, local), `app/mcp_service.py:1178` (read, local), `app/mcp_service.py:1202` (read, local), `app/mcp_service.py:1213` (update, local), `app/mcp_service.py:1225` (read, local), `app/mcp_service.py:1249` (migration, local), `app/mcp_service.py:1262` (read, local), `app/mcp_service.py:1589` (read, local), `app/mcp_service.py:2016` (migration, local), `app/routes.py:761` (migration, local), `app/routes.py:773` (read, local), `app/routes.py:886` (read, local), `app/routes.py:888` (migration, local), `app/routes.py:890` (migration, local), `app/routes.py:932` (read, local), `app/routes.py:936` (delete, local), `app/routes.py:972` (read, local), `app/routes.py:1000` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: нет прямой связи.

## `family_pairing_codes`

- local: `app/family_pairing.py`:38.
- Колонки: `code` TEXT PRIMARY KEY, `child_user_id` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: `idx_family_pairing_codes_child` (child_user_id).
- production: `/app/words.db sqlite_master`.
- Колонки: `code` TEXT PRIMARY KEY, `child_user_id` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: `idx_family_pairing_codes_child` (child_user_id).
- Чтение/запись/миграции: `app/family_pairing.py:38` (migration, local), `app/family_pairing.py:48` (read, local), `app/family_pairing.py:69` (delete, local), `app/family_pairing.py:77` (insert, local), `app/family_pairing.py:303` (read, local), `app/family_pairing.py:308` (delete, local), `app/family_pairing.py:346` (read, local), `app/family_pairing.py:352` (delete, local), `tests/test_family_pairing_bot.py:110` (update, local).
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
- Чтение/запись/миграции: `app/routes.py:4869` (delete, local), `app/tts_usage.py:98` (migration, local), `app/tts_usage.py:107` (insert, local), `app/tts_usage.py:126` (delete, local), `app/tts_usage.py:133` (insert, local), `app/tts_usage.py:146` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
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

- local: `app/mcp_service.py`:159.
- Колонки: `token_hash` TEXT PRIMARY KEY, `client_id` TEXT NOT NULL, `user_id` TEXT NOT NULL, `resource` TEXT NOT NULL, `scopes` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `created_at` INTEGER NOT NULL, `last_used_at` INTEGER, `revoked_at` INTEGER.
- Индексы: `idx_mcp_grants_user` (user_id, revoked_at, expires_at).
- Чтение/запись/миграции: `app/mcp_api.py:102` (read, local), `app/mcp_api.py:112` (update, local), `app/mcp_api.py:138` (read, local), `app/mcp_api.py:209` (update, local), `app/mcp_api.py:253` (migration, local), `app/mcp_api.py:299` (update, local), `app/mcp_api.py:301` (update, local), `app/mcp_api.py:512` (migration, local), `app/mcp_api.py:533` (update, local).
- Связанные API файла-владельца: `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_admin_audit_log`

- local: `app/mcp_service.py`:209.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `created_at` INTEGER NOT NULL, `admin_user_id` TEXT NOT NULL, `target_user_id` TEXT NOT NULL, `action` TEXT NOT NULL, `old_value` TEXT NOT NULL, `new_value` TEXT NOT NULL, `request_id` TEXT NOT NULL DEFAULT ''.
- Индексы: `idx_mcp_admin_audit_created` (created_at DESC).
- Чтение/запись/миграции: `app/mcp_service.py:209` (migration, local), `app/mcp_service.py:219` (migration, local), `app/mcp_service.py:1323` (migration, local), `app/mcp_service.py:1530` (migration, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_audit_log`

- local: `app/mcp_service.py`:196.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `created_at` INTEGER NOT NULL, `request_id` TEXT NOT NULL, `client_hash` TEXT NOT NULL, `user_hash` TEXT NOT NULL, `operation` TEXT NOT NULL, `success` INTEGER NOT NULL, `error_code` TEXT, `duration_ms` INTEGER NOT NULL, `item_count` INTEGER NOT NULL DEFAULT 0.
- Индексы: `idx_mcp_audit_created_at` (created_at).
- Чтение/запись/миграции: `app/mcp_api.py:257` (migration, local), `app/mcp_api.py:597` (migration, local).
- Связанные API файла-владельца: `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_idempotency`

- local: `app/mcp_service.py`:178.
- Колонки: `user_id` TEXT NOT NULL, `operation` TEXT NOT NULL, `idempotency_key` TEXT NOT NULL, `request_hash` TEXT NOT NULL, `response_json` TEXT NOT NULL, `created_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_service.py:178` (migration, local), `app/mcp_service.py:238` (read, local), `app/mcp_service.py:244` (migration, local), `tests/test_content_pipeline.py:239` (read, local).
- Связанные API файла-владельца: проверять по handler.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_oauth_clients`

- local: `app/mcp_service.py`:138.
- Колонки: `client_id` TEXT PRIMARY KEY, `client_name` TEXT NOT NULL DEFAULT '', `redirect_uris` TEXT NOT NULL, `created_at` INTEGER NOT NULL, `last_used_at` INTEGER, `revoked_at` INTEGER.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_api.py:113` (update, local), `app/mcp_api.py:138` (read, local), `app/mcp_api.py:249` (migration, local), `app/mcp_api.py:253` (migration, local), `app/mcp_api.py:298` (update, local), `app/mcp_api.py:345` (migration, local), `app/mcp_api.py:386` (read, local).
- Связанные API файла-владельца: `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_oauth_codes`

- local: `app/mcp_service.py`:146.
- Колонки: `code_hash` TEXT PRIMARY KEY, `client_id` TEXT NOT NULL, `user_id` TEXT NOT NULL, `redirect_uri` TEXT NOT NULL, `resource` TEXT NOT NULL, `scopes` TEXT NOT NULL, `code_challenge` TEXT NOT NULL, `expires_at` INTEGER NOT NULL, `used_at` INTEGER, `created_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_api.py:456` (insert, local), `app/mcp_api.py:491` (read, local), `app/mcp_api.py:508` (update, local).
- Связанные API файла-владельца: `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`.
- Telegram handlers файла-владельца: нет прямой связи.

## `mcp_user_settings`

- local: `app/mcp_service.py`:173.
- Колонки: `user_id` TEXT PRIMARY KEY, `enabled` INTEGER NOT NULL DEFAULT 1, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_api.py:79` (read, local), `app/mcp_api.py:192` (insert, local).
- Связанные API файла-владельца: `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`.
- Telegram handlers файла-владельца: нет прямой связи.

## `parent_child_links`

- local: `app/routes.py`:744.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `run.py`:159.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_family_pairing_bot.py`:158.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: `idx_parent_child_links_child` (child_user_id).
- Чтение/запись/миграции: `app/family_pairing.py:30` (read, local), `app/family_pairing.py:227` (read, local), `app/family_pairing.py:233` (read, local), `app/family_pairing.py:240` (insert, local), `app/family_pairing.py:259` (read, local), `app/family_pairing.py:277` (read, local), `app/family_pairing.py:371` (read, local), `app/family_pairing.py:377` (read, local), `app/family_pairing.py:384` (insert, local), `app/mcp_service.py:911` (read, local), `app/mcp_service.py:931` (read, local), `app/routes.py:625` (read, local), `app/routes.py:744` (migration, local), `app/routes.py:756` (read, local), `app/routes.py:810` (read, local), `app/routes.py:932` (read, local), `app/routes.py:1058` (read, local), `app/routes.py:1062` (read, local), `app/routes.py:1087` (read, local), `app/routes.py:1094` (read, local), `app/routes.py:1123` (read, local), `app/routes.py:1151` (read, local), `app/routes.py:2003` (read, local), `app/routes.py:2358` (read, local), `app/routes.py:3158` (read, local), `app/routes.py:3206` (read, local), `app/routes.py:3431` (read, local), `app/routes.py:3437` (read, local), `app/routes.py:3443` (insert, local), `app/routes.py:3466` (delete, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: нет прямой связи.

## `progress_events`

- local: `app/routes.py`:470.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `scope` TEXT, `event_type` TEXT, `event_ts` INTEGER, `payload` TEXT, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: `idx_progress_events_user_ts` (user_id, event_ts).
- local: `tests/test_project_kb.py`:60.
- Колонки: `id` INTEGER PRIMARY KEY, `user_id` TEXT.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `scope` TEXT, `event_type` TEXT, `event_ts` INTEGER, `payload` TEXT, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: `idx_progress_events_user_ts` (user_id, event_ts).
- Чтение/запись/миграции: `app/mcp_service.py:771` (read, local), `app/mcp_service.py:814` (read, local), `app/mcp_service.py:878` (insert, local), `app/mcp_service.py:1352` (read, local), `app/mcp_service.py:1504` (read, local), `app/mcp_service.py:1507` (read, local), `app/mcp_service.py:1613` (read, local), `app/routes.py:470` (migration, local), `app/routes.py:482` (read, local), `app/routes.py:559` (read, local), `app/routes.py:1165` (read, local), `app/routes.py:1173` (read, local), `app/routes.py:1416` (read, local), `app/routes.py:1979` (read, local), `app/routes.py:3723` (read, local), `app/routes.py:4299` (insert, local), `app/routes.py:4851` (read, local), `docs/MCP_CONNECTOR.md:44` (update, local), `tests/test_family_accounts.py:303` (insert, local), `tests/test_family_accounts.py:384` (insert, local), `tests/test_family_accounts.py:444` (insert, local), `tests/test_mcp_connector.py:349` (read, local), `tests/test_project_kb.py:58` (insert, local), `tests/test_project_kb.py:60` (migration, local), `tests/test_project_kb.py:65` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: нет прямой связи.

## `reminder_state`

- local: `bot/reminder.py`:50.
- Колонки: `user_id` TEXT PRIMARY KEY, `last_msg_id` INTEGER, `last_sent_date` TEXT.
- Индексы: не найдены в этом определении.
- local: `run.py`:109.
- Колонки: `user_id` TEXT PRIMARY KEY, `last_msg_id` INTEGER, `last_sent_date` TEXT.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `last_msg_id` INTEGER, `last_sent_date` TEXT.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `bot/reminder.py:50` (migration, local), `bot/reminder.py:87` (read, local), `bot/reminder.py:101` (insert, local), `docs/codex/ARCHITECTURE.md:18` (update, local).
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

- local: `app/routes.py`:780.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `parent_user_id` TEXT NOT NULL, `child_user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `parent_word_id` INTEGER NOT NULL, `child_word_id` INTEGER NOT NULL UNIQUE, `created_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/routes.py:777` (read, local), `app/routes.py:780` (migration, local), `app/routes.py:793` (read, local), `app/routes.py:797` (read, local), `app/routes.py:832` (insert, local), `app/routes.py:2385` (read, local), `app/routes.py:2396` (delete, local), `app/routes.py:2436` (insert, local), `app/routes.py:2696` (read, local), `app/routes.py:2705` (read, local), `app/routes.py:3856` (read, local), `app/routes.py:3866` (read, local), `app/routes.py:3896` (update, local), `tests/test_family_accounts.py:787` (read, local), `tests/test_family_accounts.py:815` (read, local), `tests/test_family_accounts.py:819` (read, local), `tests/test_family_accounts.py:882` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: нет прямой связи.

## `shared_word_sets`

- local: `app/routes.py`:1685.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `token` TEXT NOT NULL UNIQUE, `owner_user_id` TEXT NOT NULL, `title` TEXT NOT NULL, `lesson` TEXT, `payload` TEXT NOT NULL, `created_at` INTEGER NOT NULL, `expires_at` INTEGER, `import_count` INTEGER NOT NULL DEFAULT 0, `max_imports` INTEGER.
- Индексы: `idx_shared_word_sets_token` (token).
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `token` TEXT NOT NULL UNIQUE, `owner_user_id` TEXT NOT NULL, `title` TEXT NOT NULL, `lesson` TEXT, `payload` TEXT NOT NULL, `created_at` INTEGER NOT NULL, `expires_at` INTEGER, `import_count` INTEGER NOT NULL DEFAULT 0, `max_imports` INTEGER.
- Индексы: `idx_shared_word_sets_token` (token).
- Чтение/запись/миграции: `app/routes.py:1685` (migration, local), `app/routes.py:1700` (read, local), `app/routes.py:2123` (read, local), `app/routes.py:2237` (read, local), `app/routes.py:2241` (insert, local), `app/routes.py:2469` (read, local), `app/routes.py:2555` (update, local), `app/routes.py:4859` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
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

- local: `app/routes.py`:514.
- Колонки: `user_id` TEXT PRIMARY KEY, `goal_value` INTEGER NOT NULL, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `goal_value` INTEGER NOT NULL, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_service.py:311` (insert, local), `app/routes.py:514` (migration, local), `app/routes.py:531` (read, local), `app/routes.py:4124` (insert, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_language_preferences`

- local: `app/routes.py`:703.
- Колонки: `user_id` TEXT NOT NULL, `priority` INTEGER NOT NULL, `lang_code` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_language_preferences_user` (user_id, priority).
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT NOT NULL, `priority` INTEGER NOT NULL, `lang_code` TEXT NOT NULL, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_language_preferences_user` (user_id, priority).
- Чтение/запись/миграции: `app/content_service.py:337` (read, local), `app/content_service.py:339` (read, local), `app/mcp_service.py:284` (delete, local), `app/mcp_service.py:286` (insert, local), `app/mcp_service.py:1391` (read, local), `app/routes.py:703` (migration, local), `app/routes.py:714` (read, local), `app/routes.py:1630` (read, local), `app/routes.py:3603` (delete, local), `app/routes.py:3605` (insert, local), `app/routes.py:4852` (read, local), `docs/MCP_CONNECTOR.md:46` (read, local), `tests/test_content_pipeline.py:46` (insert, local), `tests/test_family_accounts.py:415` (insert, local), `tests/test_family_accounts.py:475` (insert, local), `tests/test_family_accounts.py:673` (insert, local), `tests/test_family_accounts.py:680` (insert, local), `tests/test_mcp_connector.py:71` (insert, local), `tests/test_mcp_lesson_flow.py:84` (insert, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_lessons`

- local: `app/models.py`:20.
- Колонки: `user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `hidden` INTEGER NOT NULL DEFAULT 0, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `app/routes.py`:957.
- Колонки: `user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `hidden` INTEGER NOT NULL DEFAULT 0, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT NOT NULL, `lesson` TEXT NOT NULL, `hidden` INTEGER NOT NULL DEFAULT 0, `updated_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, `updated_at_ts` INTEGER.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_service.py:578` (insert, local), `app/mcp_service.py:721` (delete, local), `app/mcp_service.py:736` (read, local), `app/mcp_service.py:742` (read, local), `app/mcp_service.py:750` (update, local), `app/mcp_service.py:920` (read, local), `app/mcp_service.py:921` (read, local), `app/mcp_service.py:1430` (read, local), `app/mcp_service.py:1467` (read, local), `app/mcp_service.py:1949` (read, local), `app/mcp_service.py:1954` (insert, local), `app/mcp_service.py:1981` (delete, local), `app/models.py:20` (migration, local), `app/models.py:28` (read, local), `app/models.py:30` (migration, local), `app/models.py:32` (update, local), `app/models.py:72` (read, local), `app/models.py:141` (insert, local), `app/routes.py:957` (migration, local), `app/routes.py:974` (read, local), `app/routes.py:994` (read, local), `app/routes.py:1002` (read, local), `app/routes.py:3815` (read, local), `app/routes.py:3825` (read, local), `app/routes.py:3906` (read, local), `app/routes.py:3911` (insert, local), `app/routes.py:3919` (delete, local), `app/routes.py:3940` (delete, local), `app/routes.py:4000` (delete, local), `app/routes.py:4359` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_settings`

- local: `app/routes.py`:727.
- Колонки: `user_id` TEXT PRIMARY KEY, `detected_ui_language` TEXT, `ui_language_override` TEXT, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- local: `bot/onboarding.py`:439.
- Колонки: `user_id` TEXT PRIMARY KEY, `detected_ui_language` TEXT, `ui_language_override` TEXT, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `detected_ui_language` TEXT, `ui_language_override` TEXT, `updated_at` INTEGER NOT NULL.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/routes.py:727` (migration, local), `app/routes.py:1455` (insert, local), `app/routes.py:1473` (read, local), `app/routes.py:1510` (insert, local), `app/routes.py:4853` (read, local), `bot/onboarding.py:439` (migration, local), `bot/onboarding.py:454` (insert, local), `bot/onboarding.py:468` (read, local), `bot/onboarding.py:484` (insert, local), `tests/test_family_accounts.py:422` (insert, local), `tests/test_family_accounts.py:482` (insert, local), `tests/test_telegram_onboarding.py:87` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_subscriptions`

- local: `app/routes.py`:1523.
- Колонки: `user_id` TEXT PRIMARY KEY, `status` TEXT NOT NULL DEFAULT 'trial', `trial_started_at` INTEGER NOT NULL, `trial_ends_at` INTEGER NOT NULL, `current_period_ends_at` INTEGER, `provider` TEXT, `provider_customer_id` TEXT, `provider_subscription_id` TEXT, `cancel_at_period_end` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_subscriptions_status` (status, trial_ends_at, current_period_ends_at).
- local: `tests/test_google_account_link.py`:66.
- Колонки: `user_id` TEXT PRIMARY KEY, `status` TEXT NOT NULL DEFAULT 'trial'.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT PRIMARY KEY, `status` TEXT NOT NULL DEFAULT 'trial', `trial_started_at` INTEGER NOT NULL, `trial_ends_at` INTEGER NOT NULL, `current_period_ends_at` INTEGER, `provider` TEXT, `provider_customer_id` TEXT, `provider_subscription_id` TEXT, `cancel_at_period_end` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER NOT NULL.
- Индексы: `idx_user_subscriptions_status` (status, trial_ends_at, current_period_ends_at).
- Чтение/запись/миграции: `app/google_auth.py:161` (read, local), `app/google_auth.py:182` (read, local), `app/google_auth.py:186` (delete, local), `app/google_auth.py:190` (update, local), `app/mcp_service.py:1312` (read, local), `app/mcp_service.py:1314` (insert, local), `app/mcp_service.py:1320` (read, local), `app/mcp_service.py:1321` (update, local), `app/mcp_service.py:1337` (read, local), `app/mcp_service.py:1505` (read, local), `app/routes.py:1523` (migration, local), `app/routes.py:1538` (read, local), `app/routes.py:1567` (read, local), `app/routes.py:1574` (insert, local), `app/routes.py:1579` (read, local), `app/routes.py:1989` (read, local), `app/routes.py:4509` (read, local), `app/routes.py:4714` (insert, local), `app/routes.py:4743` (update, local), `app/routes.py:4854` (read, local), `tests/test_google_account_link.py:66` (migration, local), `tests/test_google_account_link.py:75` (insert, local), `tests/test_google_account_link.py:142` (insert, local), `tests/test_google_account_link.py:170` (read, local).
- Связанные API файла-владельца: `/auth/google`, `/auth/google/callback`, `/api/auth/google/config`, `/api/auth/google/verify`, `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`.
- Telegram handlers файла-владельца: нет прямой связи.

## `user_word_flags`

- local: `app/routes.py`:457.
- Колонки: `user_id` TEXT NOT NULL, `word_id` INTEGER NOT NULL, `difficult` INTEGER NOT NULL DEFAULT 1.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `user_id` TEXT NOT NULL, `word_id` INTEGER NOT NULL, `difficult` INTEGER NOT NULL DEFAULT 1.
- Индексы: не найдены в этом определении.
- Чтение/запись/миграции: `app/mcp_service.py:452` (read, local), `app/mcp_service.py:477` (read, local), `app/mcp_service.py:513` (read, local), `app/mcp_service.py:544` (read, local), `app/mcp_service.py:657` (delete, local), `app/mcp_service.py:684` (insert, local), `app/mcp_service.py:724` (delete, local), `app/mcp_service.py:1266` (read, local), `app/mcp_service.py:1430` (read, local), `app/mcp_service.py:1447` (update, local), `app/mcp_service.py:1523` (read, local), `app/mcp_service.py:1645` (read, local), `app/mcp_service.py:1984` (delete, local), `app/routes.py:457` (migration, local), `app/routes.py:891` (read, local), `app/routes.py:896` (migration, local), `app/routes.py:898` (migration, local), `app/routes.py:2756` (read, local), `app/routes.py:2778` (delete, local), `app/routes.py:3673` (read, local), `app/routes.py:3988` (delete, local), `app/routes.py:4051` (read, local), `app/routes.py:4152` (read, local), `app/routes.py:4177` (read, local), `app/routes.py:4199` (read, local), `app/routes.py:4241` (insert, local), `app/routes.py:4247` (insert, local), `app/routes.py:4812` (delete, local), `app/routes.py:4849` (read, local), `bot/upload.py:383` (insert, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: `/upload_words`, `filters.Regex(upload_words_pattern)`, `filters.Regex(r"^(Добавить слова|Импортировать слова)$")`, `filters.Document.ALL & (~filters.COMMAND)`, `filters.Regex(r"(?i)^(импортировать как есть)$")`, `filters.Regex(r"(?i)^(отменить импорт)$")`.

## `users`

- local: `bot/auth.py`:61.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `bot/db.py`:136.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `bot/reminder.py`:57.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `run.py`:56.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'pending', `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_content_pipeline.py`:35.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER DEFAULT 1, `account_type` TEXT DEFAULT 'standard'.
- Индексы: не найдены в этом определении.
- local: `tests/test_db_migrations.py`:11.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_family_accounts.py`:121.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `created_at` TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP.
- Индексы: не найдены в этом определении.
- local: `tests/test_family_pairing_bot.py`:149.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `account_type` TEXT NOT NULL.
- Индексы: не найдены в этом определении.
- local: `tests/test_google_account_link.py`:41.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'standard', `auth_provider` TEXT DEFAULT 'telegram', `google_id` TEXT, `google_email` TEXT.
- Индексы: `u_users_google_id` (google_id).
- local: `tests/test_mcp_connector.py`:39.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'standard', `google_id` TEXT, `google_email` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_mcp_lesson_flow.py`:52.
- Колонки: `user_id` TEXT PRIMARY KEY, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `account_type` TEXT NOT NULL DEFAULT 'standard', `google_id` TEXT, `google_email` TEXT.
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
- Чтение/запись/миграции: `app/account_types.py:24` (delete, local), `app/account_types.py:56` (delete, local), `app/account_types.py:80` (read, local), `app/account_types.py:81` (read, local), `app/account_types.py:84` (migration, local), `app/account_types.py:103` (update, local), `app/account_types.py:117` (update, local), `app/family_pairing.py:25` (read, local), `app/family_pairing.py:43` (delete, local), `app/family_pairing.py:63` (read, local), `app/family_pairing.py:98` (delete, local), `app/family_pairing.py:119` (read, local), `app/family_pairing.py:159` (read, local), `app/family_pairing.py:189` (read, local), `app/family_pairing.py:218` (read, local), `app/family_pairing.py:260` (read, local), `app/family_pairing.py:278` (read, local), `app/family_pairing.py:304` (read, local), `app/family_pairing.py:333` (read, local), `app/family_pairing.py:362` (read, local), `app/google_auth.py:29` (read, local), `app/google_auth.py:33` (migration, local), `app/google_auth.py:36` (migration, local), `app/google_auth.py:38` (migration, local), `app/google_auth.py:41` (read, local), `app/google_auth.py:44` (update, local), `app/google_auth.py:48` (read, local), `app/google_auth.py:52` (read, local), `app/google_auth.py:56` (read, local), `app/google_auth.py:97` (update, local).
- Связанные API файла-владельца: `/api/mcp/user`, `/api/mcp/user/revoke-all`, `/admin/mcp`, `/admin/mcp/revoke`, `/.well-known/oauth-authorization-server`, `/oauth/register`, `/oauth/authorize`, `/oauth/token`, `/oauth/revoke`, `/api/internal/mcp/resolve`, `/api/internal/mcp/execute`, `/api/internal/mcp/health`, `/auth/google`, `/auth/google/callback`, `/api/auth/google/config`, `/api/auth/google/verify`, `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`.
- Telegram handlers файла-владельца: `/reminder_now`, `/start`, `/open`, `/family`, `r"^onboarding:(?:language|language_keep|language_change|account`, `r"^family_link:(?:confirm|cancel`, `filters.Regex(learn_words_pattern)`, `filters.TEXT & (~filters.COMMAND) & exclude_import_btns`.

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
- local: `run.py`:67.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT NOT NULL DEFAULT '', `status` TEXT NOT NULL DEFAULT 'user', `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `updated_at` INTEGER.
- Индексы: `idx_words_lesson` (lesson), `idx_words_user_lesson` (user_id, lesson), `u_words_user_lesson_number` (user_id, lesson, number).
- local: `tests/test_content_pipeline.py`:30.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `status` TEXT DEFAULT 'user', `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `difficult` INTEGER DEFAULT 0, `updated_at` INTEGER.
- Индексы: `u_words_user_lesson_number` (user_id,lesson,number).
- local: `tests/test_family_accounts.py`:39.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT, `lesson` TEXT, `number` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_google_account_link.py`:61.
- Колонки: `id` INTEGER PRIMARY KEY, `user_id` TEXT NOT NULL, `lesson` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_mcp_connector.py`:45.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT NOT NULL, `status` TEXT NOT NULL DEFAULT 'user', `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `difficult` INTEGER DEFAULT 0, `updated_at` INTEGER.
- Индексы: `u_words_user_lesson_number` (user_id,lesson,number).
- local: `tests/test_mcp_lesson_flow.py`:58.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `user_id` TEXT NOT NULL, `status` TEXT NOT NULL DEFAULT 'user', `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `difficult` INTEGER DEFAULT 0, `updated_at` INTEGER.
- Индексы: `u_words_user_lesson_number` (user_id,lesson,number).
- local: `tests/test_project_kb.py`:130.
- Колонки: `id` INTEGER PRIMARY KEY, `nl` TEXT.
- Индексы: не найдены в этом определении.
- local: `tests/test_tts_usage.py`:273.
- Колонки: `id` INTEGER PRIMARY KEY, `user_id` TEXT, `status` TEXT, `lesson` TEXT, `number` INTEGER, `difficult` INTEGER DEFAULT 0, `updated_at` INTEGER.
- Индексы: не найдены в этом определении.
- production: `/app/words.db sqlite_master`.
- Колонки: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `lesson` TEXT, `number` TEXT, `nl` TEXT, `en` TEXT, `ru` TEXT, `ex_nl` TEXT, `ex_en` TEXT, `ex_ru` TEXT, `audio_nl` TEXT, `audio_en` TEXT, `audio_ru` TEXT, `difficult` INTEGER NOT NULL DEFAULT 0, `updated_at` INTEGER, `user_id` TEXT, `status` TEXT NOT NULL DEFAULT 'user', `de` TEXT, `ex_de` TEXT, `audio_de` TEXT, `it` TEXT, `ex_it` TEXT, `audio_it` TEXT, `fr` TEXT, `ex_fr` TEXT, `audio_fr` TEXT.
- Индексы: `idx_words_lesson` (lesson), `idx_words_user_lesson` (user_id, lesson), `u_words_user_lesson_number` (user_id, lesson, number).
- Чтение/запись/миграции: `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:11` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:78` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:81` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:84` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:87` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:90` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:94` (insert, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:99` (update, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:103` (update, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:122` (delete, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:125` (delete, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:128` (read, local), `android/app/src/main/java/com/learnwords/app/data/db/AppDatabase.kt:226` (migration, local), `app/audio_gen.py:159` (read, local), `app/audio_gen.py:163` (migration, local), `app/audio_gen.py:165` (migration, local), `app/audio_gen.py:174` (read, local), `app/audio_gen.py:186` (read, local), `app/audio_gen.py:218` (read, local), `app/audio_gen.py:263` (update, local), `app/audio_gen.py:298` (read, local), `app/content_service.py:3` (read, local), `app/content_service.py:65` (read, local), `app/content_service.py:70` (migration, local), `app/content_service.py:73` (read, local), `app/content_service.py:84` (read, local), `app/content_service.py:85` (read, local), `app/content_service.py:89` (read, local), `app/content_service.py:92` (read, local), `app/content_service.py:94` (read, local).
- Связанные API файла-владельца: `/sw.js`, `/`, `/lessons`, `/lesson/<int:lesson_id>`, `/learn`, `/difficult`, `/upload`, `/settings`, `/account-type`, `/family/link`, `/parent`, `/subscription`, `/admin/users`, `/share/<token>`, `/api/share/create`, `/api/share/source_lessons`, `/api/share/assign_child`, `/api/share/<token>/import`, `/api/import-words`, `/api/words`, `/api/words/<int:word_id>`, `/api/words/nl-list`, `/api/words/duplicates`, `/api/parse-file`, `/api/auth/login_android`, `/api/auth/login_android_token`, `/api/auth/login_link`, `/android-auth`, `/api/auth/login_webapp`, `/api/me`.
- Telegram handlers файла-владельца: `/upload_words`, `filters.Regex(upload_words_pattern)`, `filters.Regex(r"^(Добавить слова|Импортировать слова)$")`, `filters.Document.ALL & (~filters.COMMAND)`, `filters.Regex(r"(?i)^(импортировать как есть)$")`, `filters.Regex(r"(?i)^(отменить импорт)$")`.
