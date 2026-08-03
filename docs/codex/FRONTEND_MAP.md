# Frontend map

HTML-шаблоны рендерятся Flask, используют общие функции `base.html`; IndexedDB и Service Worker обеспечивают offline-first работу.

## `app/static/audio_worker.js`

- api: `/api/audio/ensure` (`app/static/audio_worker.js:20`).
- global: `AudioWorker` (`app/static/audio_worker.js:35`).

## `app/static/idb.js`

- indexeddb_store: `name` (`app/static/idb.js:21`).
- global: `LocalDB` (`app/static/idb.js:130`).

## `app/static/learn.js`

- global: `__LEARN_BOOTED__` (`app/static/learn.js:11`).
- global: `updateChildGoalOptimistic` (`app/static/learn.js:568`).
- api: `/api/words/${current.id}` (`app/static/learn.js:737`).
- api: `/api/lessons/set_hidden` (`app/static/learn.js:807`).
- api: `/api/words/${current.id}` (`app/static/learn.js:936`).

## `app/static/sync.js`

- api: `/api/progress/sync` (`app/static/sync.js:4`).

## `app/static/upload.js`

- api: `/api/me` (`app/static/upload.js:23`).
- api: `/api/translate/word` (`app/static/upload.js:107`).
- api: `/api/generate/topic` (`app/static/upload.js:118`).
- api: `/api/translate/language` (`app/static/upload.js:129`).
- api: `/api/import-words` (`app/static/upload.js:642`).
- api: `/api/words/nl-list` (`app/static/upload.js:794`).
- api: `/api/share/source_lessons` (`app/static/upload.js:1072`).
- api: `/api/words/${wordId}` (`app/static/upload.js:1251`).
- api: `/api/words/${word.id}` (`app/static/upload.js:1376`).
- api: `/api/share/assign_child` (`app/static/upload.js:1495`).
- api: `/api/share/create` (`app/static/upload.js:1538`).
- api: `/api/words?` (`app/static/upload.js:1609`).
- api: `/api/words/duplicates` (`app/static/upload.js:1642`).
- api: `/api/words/${wordId}` (`app/static/upload.js:1750`).
- api: `/api/words/${wordId}` (`app/static/upload.js:1871`).
- api: `/api/words/${wordId}` (`app/static/upload.js:1893`).
- api: `/api/parse-file` (`app/static/upload.js:2017`).
- api: `/api/import-words` (`app/static/upload.js:2088`).

## `app/templates/account_type.html`

- api: `/api/account/type` (`app/templates/account_type.html:49`).

## `app/templates/admin_users.html`

- api: `/api/me` (`app/templates/admin_users.html:156`).

## `app/templates/base.html`

- template_script: `https://telegram.org/js/telegram-web-app.js` (`app/templates/base.html:8`).
- template_style: `{{ url_for(` (`app/templates/base.html:9`).
- global: `I18N` (`app/templates/base.html:54`).
- global: `_HELLO_NAME_` (`app/templates/base.html:76`).
- global: `USER_ID` (`app/templates/base.html:86`).
- global: `IDB_KEY_PREFIX` (`app/templates/base.html:87`).
- global: `apiFetch` (`app/templates/base.html:88`).
- api: `/api/auth/login_webapp` (`app/templates/base.html:166`).
- api: `/api/me` (`app/templates/base.html:177`).
- global: `_HELLO_NAME_` (`app/templates/base.html:195`).
- global: `updateChildGoalOptimistic` (`app/templates/base.html:267`).
- api: `/api/child-learning/status?tz_offset=${tzOffset}` (`app/templates/base.html:282`).
- api: `/api/daily-goal` (`app/templates/base.html:306`).
- template_script: `{{ url_for(` (`app/templates/base.html:594`).
- template_script: `{{ url_for(` (`app/templates/base.html:595`).
- service_worker: `/sw.js` (`app/templates/base.html:599`).

## `app/templates/difficult.html`

- template_style: `{{ url_for(` (`app/templates/difficult.html:4`).
- template_script: `{{ url_for(` (`app/templates/difficult.html:62`).
- template_script: `{{ url_for(` (`app/templates/difficult.html:63`).

## `app/templates/family_link.html`

- api: `/api/family/link` (`app/templates/family_link.html:28`).

## `app/templates/index.html`

- api: `/api/learning/streak?tz_offset=${offset}` (`app/templates/index.html:215`).
- api: `/api/user_lessons` (`app/templates/index.html:490`).
- api: `/api/user_lessons/delete` (`app/templates/index.html:571`).
- api: `/api/lesson_words?lesson=${encodeURIComponent(lessonTitle)}` (`app/templates/index.html:635`).
- api: `/api/lessons` (`app/templates/index.html:666`).
- api: `/api/lessons` (`app/templates/index.html:685`).
- api: `/api/lessons/set_hidden` (`app/templates/index.html:766`).

## `app/templates/learn.html`

- template_style: `{{ url_for(` (`app/templates/learn.html:4`).
- global: `LESSON_TITLE` (`app/templates/learn.html:97`).
- global: `LEARN_I18N` (`app/templates/learn.html:98`).
- template_script: `{{ url_for(` (`app/templates/learn.html:107`).
- template_script: `{{ url_for(` (`app/templates/learn.html:109`).
- api: `/api/lesson_words?lesson=` (`app/templates/learn.html:143`).

## `app/templates/parent_dashboard.html`

- api: `/api/family/children/${encodeURIComponent(childId)}` (`app/templates/parent_dashboard.html:263`).
- api: `/api/family/children/${encodeURIComponent(child.user_id)}/priority-lesson` (`app/templates/parent_dashboard.html:279`).
- api: `/api/family/dashboard?days=${periodSelect.value}&tz_offset=${offset}` (`app/templates/parent_dashboard.html:300`).

## `app/templates/settings.html`

- api: `/api/user-languages` (`app/templates/settings.html:198`).
- api: `/api/ui-language` (`app/templates/settings.html:199`).
- api: `/api/daily-goal` (`app/templates/settings.html:221`).
- api: `/api/family/pairing-code` (`app/templates/settings.html:248`).
- api: `/api/family` (`app/templates/settings.html:259`).
- api: `/api/user-languages` (`app/templates/settings.html:317`).
- api: `http://localhost:11434/api/chat` (`app/templates/settings.html:385`).
- api: `/api/user-languages/missing-words?languages=${encodeURIComponent(languages.join(` (`app/templates/settings.html:403`).
- api: `/api/words/${item.id}` (`app/templates/settings.html:419`).
- api: `/api/daily-goal` (`app/templates/settings.html:440`).
- api: `/api/ui-language` (`app/templates/settings.html:456`).

## `app/templates/share.html`

- api: `/api/share/` (`app/templates/share.html:117`).

## `app/templates/subscription.html`

- api: `/api/subscription` (`app/templates/subscription.html:88`).

## `app/templates/upload.html`

- api: `/api/me` (`app/templates/upload.html:363`).
- global: `PUBLIC_BASE_URL` (`app/templates/upload.html:700`).
- template_script: `{{ url_for(` (`app/templates/upload.html:703`).

## Offline flow

`idb.js` открывает IndexedDB/stores → действия без сети попадают в outbox → `sync.js` отправляет progress в `/api/progress/sync` → `/api/sync/updates?since=...` возвращает delta → локальные stores обновляются. `sw.js` обслуживает кэш shell/static; `audio_worker.js` координирует аудиокэш.
