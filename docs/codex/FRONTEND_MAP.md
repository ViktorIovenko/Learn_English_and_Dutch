# Frontend map

HTML-шаблоны рендерятся Flask, используют общие функции `base.html`; IndexedDB и Service Worker обеспечивают offline-first работу.

## `app/static/audio_worker.js`

- api: `/api/audio/ensure` (`app/static/audio_worker.js:21`).
- global: `AudioWorker` (`app/static/audio_worker.js:36`).

## `app/static/family_invite.js`

- global: `FamilyInvitation` (`app/static/family_invite.js:35`).
- api: `/api/family/invitation/preview` (`app/static/family_invite.js:87`).
- api: `/api/family/invitation/accept` (`app/static/family_invite.js:122`).

## `app/static/idb.js`

- indexeddb_store: `name` (`app/static/idb.js:21`).
- global: `LocalDB` (`app/static/idb.js:130`).

## `app/static/learn.js`

- global: `__LEARN_BOOTED__` (`app/static/learn.js:11`).
- global: `updateChildGoalOptimistic` (`app/static/learn.js:721`).
- api: `/api/words/${current.id}` (`app/static/learn.js:890`).
- api: `/api/lessons/set_hidden` (`app/static/learn.js:960`).
- api: `/api/words/${current.id}` (`app/static/learn.js:1089`).

## `app/static/mcp_connector.js`

- api: `/api/mcp/user` (`app/static/mcp_connector.js:169`).
- api: `/api/mcp/user` (`app/static/mcp_connector.js:183`).
- api: `/api/mcp/user/revoke-all` (`app/static/mcp_connector.js:201`).

## `app/static/sync.js`

- api: `/api/progress/sync` (`app/static/sync.js:4`).

## `app/static/upload.js`

- api: `/api/user_lessons` (`app/static/upload.js:8`).
- api: `/api/me` (`app/static/upload.js:42`).
- api: `/api/translate/word` (`app/static/upload.js:121`).
- api: `/api/generate/topic` (`app/static/upload.js:132`).
- api: `/api/translate/language` (`app/static/upload.js:143`).
- api: `/api/import-words` (`app/static/upload.js:561`).
- api: `/api/share/source_lessons` (`app/static/upload.js:772`).
- api: `/api/user_lessons/rename` (`app/static/upload.js:833`).
- api: `/api/words/${wordId}` (`app/static/upload.js:1041`).
- api: `/api/words/${word.id}` (`app/static/upload.js:1115`).
- api: `/api/share/assign_child` (`app/static/upload.js:1234`).
- api: `/api/share/create` (`app/static/upload.js:1277`).
- api: `/api/parse-file` (`app/static/upload.js:1355`).
- api: `/api/import-words` (`app/static/upload.js:1428`).

## `app/static/word_database.js`

- api: `/api/translate/word` (`app/static/word_database.js:21`).
- api: `/api/words?` (`app/static/word_database.js:66`).
- api: `/api/words/duplicates` (`app/static/word_database.js:99`).
- api: `/api/words/${wordId}` (`app/static/word_database.js:216`).
- api: `/api/words/${wordId}` (`app/static/word_database.js:332`).

## `app/templates/account_type.html`

- api: `/api/account/type` (`app/templates/account_type.html:49`).

## `app/templates/admin_users.html`

- api: `/api/me` (`app/templates/admin_users.html:137`).

## `app/templates/base.html`

- template_script: `https://telegram.org/js/telegram-web-app.js` (`app/templates/base.html:8`).
- template_style: `https://fonts.googleapis.com` (`app/templates/base.html:19`).
- template_style: `https://fonts.gstatic.com` (`app/templates/base.html:20`).
- template_style: `https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&display=swap` (`app/templates/base.html:21`).
- template_style: `{{ url_for(` (`app/templates/base.html:131`).
- template_style: `{{ url_for(` (`app/templates/base.html:132`).
- global: `AUTH_GATE_ENABLED` (`app/templates/base.html:227`).
- global: `I18N` (`app/templates/base.html:228`).
- global: `_HELLO_NAME_` (`app/templates/base.html:290`).
- global: `USER_ID` (`app/templates/base.html:301`).
- global: `IDB_KEY_PREFIX` (`app/templates/base.html:302`).
- global: `apiFetch` (`app/templates/base.html:303`).
- api: `/api/auth/login_webapp` (`app/templates/base.html:419`).
- api: `/api/auth/login_link` (`app/templates/base.html:431`).
- api: `/auth/status` (`app/templates/base.html:448`).
- api: `/api/me` (`app/templates/base.html:461`).
- global: `_HELLO_NAME_` (`app/templates/base.html:482`).
- global: `updateChildGoalOptimistic` (`app/templates/base.html:544`).
- api: `/api/child-learning/status?tz_offset=${tzOffset}` (`app/templates/base.html:559`).
- api: `/api/daily-goal` (`app/templates/base.html:583`).
- template_script: `{{ url_for(` (`app/templates/base.html:871`).
- template_script: `{{ url_for(` (`app/templates/base.html:872`).
- service_worker: `/sw.js` (`app/templates/base.html:876`).

## `app/templates/difficult.html`

- template_style: `{{ url_for(` (`app/templates/difficult.html:4`).
- template_script: `{{ url_for(` (`app/templates/difficult.html:62`).
- template_script: `{{ url_for(` (`app/templates/difficult.html:63`).

## `app/templates/family_invite.html`

- template_style: `{{ url_for(` (`app/templates/family_invite.html:3`).
- global: `FAMILY_BOT_USERNAME` (`app/templates/family_invite.html:7`).
- template_script: `{{ url_for(` (`app/templates/family_invite.html:8`).

## `app/templates/family_link.html`

- api: `/api/family/link` (`app/templates/family_link.html:28`).

## `app/templates/index.html`

- api: `/api/learning/streak?tz_offset=${offset}` (`app/templates/index.html:190`).
- api: `/api/user_lessons` (`app/templates/index.html:465`).
- api: `/api/user_lessons/delete` (`app/templates/index.html:546`).
- api: `/api/lesson_words?lesson=${encodeURIComponent(lessonTitle)}` (`app/templates/index.html:610`).
- api: `/api/lessons` (`app/templates/index.html:641`).
- api: `/api/lessons` (`app/templates/index.html:660`).
- api: `/api/lessons/set_hidden` (`app/templates/index.html:741`).

## `app/templates/learn.html`

- template_style: `{{ url_for(` (`app/templates/learn.html:4`).
- global: `LESSON_TITLE` (`app/templates/learn.html:97`).
- global: `LEARN_I18N` (`app/templates/learn.html:98`).
- template_script: `{{ url_for(` (`app/templates/learn.html:107`).
- template_script: `{{ url_for(` (`app/templates/learn.html:109`).
- api: `/api/lesson_words?lesson=` (`app/templates/learn.html:143`).

## `app/templates/mcp_connector.html`

- template_style: `{{ url_for(` (`app/templates/mcp_connector.html:3`).
- template_script: `{{ url_for(` (`app/templates/mcp_connector.html:39`).

## `app/templates/mcp_consent.html`

- template_style: `{{ url_for(` (`app/templates/mcp_consent.html:9`).

## `app/templates/parent_dashboard.html`

- api: `/api/family/children/${encodeURIComponent(selectedChildId)}/lesson-words?lesson=${encodeURIComponent(lesson)}` (`app/templates/parent_dashboard.html:326`).
- api: `/api/family/children/${encodeURIComponent(childId)}` (`app/templates/parent_dashboard.html:351`).
- api: `/api/family/children/${encodeURIComponent(child.user_id)}/priority-lesson` (`app/templates/parent_dashboard.html:367`).
- api: `/api/family/dashboard?days=${periodSelect.value}&tz_offset=${offset}` (`app/templates/parent_dashboard.html:390`).

## `app/templates/settings.html`

- template_style: `{{ url_for(` (`app/templates/settings.html:3`).
- template_script: `{{ url_for(` (`app/templates/settings.html:146`).
- api: `/api/user-languages` (`app/templates/settings.html:266`).
- api: `/api/ui-language` (`app/templates/settings.html:267`).
- api: `/api/daily-goal` (`app/templates/settings.html:289`).
- api: `/api/family/pairing-code` (`app/templates/settings.html:341`).
- api: `/api/family/invite-code` (`app/templates/settings.html:352`).
- api: `/api/family` (`app/templates/settings.html:364`).
- api: `/api/user-languages` (`app/templates/settings.html:468`).
- api: `/api/user-languages/missing-words?languages=${encodeURIComponent(languages.join(` (`app/templates/settings.html:509`).
- api: `/api/translate/word` (`app/templates/settings.html:520`).
- api: `/api/words/${item.id}` (`app/templates/settings.html:533`).
- api: `/api/daily-goal` (`app/templates/settings.html:554`).
- api: `/api/ui-language` (`app/templates/settings.html:570`).
- api: `/api/mcp/user` (`app/templates/settings.html:602`).
- api: `/api/mcp/user` (`app/templates/settings.html:616`).
- api: `/api/mcp/user` (`app/templates/settings.html:621`).

## `app/templates/share.html`

- api: `/api/share/` (`app/templates/share.html:117`).

## `app/templates/subscription.html`

- api: `/api/subscription` (`app/templates/subscription.html:196`).

## `app/templates/upload.html`

- api: `/api/me` (`app/templates/upload.html:354`).
- global: `PUBLIC_BASE_URL` (`app/templates/upload.html:603`).
- template_script: `{{ url_for(` (`app/templates/upload.html:606`).

## `app/templates/word_database.html`

- template_style: `{{ url_for(` (`app/templates/word_database.html:3`).
- template_script: `{{ url_for(` (`app/templates/word_database.html:77`).

## Offline flow

`idb.js` открывает IndexedDB/stores → действия без сети попадают в outbox → `sync.js` отправляет progress в `/api/progress/sync` → `/api/sync/updates?since=...` возвращает delta → локальные stores обновляются. `sw.js` обслуживает кэш shell/static; `audio_worker.js` координирует аудиокэш.
