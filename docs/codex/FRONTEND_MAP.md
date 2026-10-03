# Frontend map

HTML-шаблоны рендерятся Flask, используют общие функции `base.html`; IndexedDB и Service Worker обеспечивают offline-first работу.

## `app/static/audio_worker.js`

- api: `/api/audio/ensure` (`app/static/audio_worker.js:21`).
- global: `AudioWorker` (`app/static/audio_worker.js:36`).

## `app/static/idb.js`

- indexeddb_store: `name` (`app/static/idb.js:21`).
- global: `LocalDB` (`app/static/idb.js:130`).

## `app/static/learn.js`

- global: `__LEARN_BOOTED__` (`app/static/learn.js:11`).
- global: `updateChildGoalOptimistic` (`app/static/learn.js:721`).
- api: `/api/words/${current.id}` (`app/static/learn.js:890`).
- api: `/api/lessons/set_hidden` (`app/static/learn.js:960`).
- api: `/api/words/${current.id}` (`app/static/learn.js:1089`).

## `app/static/sync.js`

- api: `/api/progress/sync` (`app/static/sync.js:4`).

## `app/static/upload.js`

- api: `/api/user_lessons` (`app/static/upload.js:9`).
- api: `/api/me` (`app/static/upload.js:43`).
- api: `/api/translate/word` (`app/static/upload.js:122`).
- api: `/api/generate/topic` (`app/static/upload.js:133`).
- api: `/api/translate/language` (`app/static/upload.js:144`).
- api: `/api/import-words` (`app/static/upload.js:562`).
- api: `/api/mcp/user` (`app/static/upload.js:906`).
- api: `/api/mcp/user` (`app/static/upload.js:920`).
- api: `/api/mcp/user/revoke-all` (`app/static/upload.js:938`).
- api: `/api/share/source_lessons` (`app/static/upload.js:977`).
- api: `/api/user_lessons/rename` (`app/static/upload.js:1038`).
- api: `/api/words/${wordId}` (`app/static/upload.js:1246`).
- api: `/api/words/${word.id}` (`app/static/upload.js:1320`).
- api: `/api/share/assign_child` (`app/static/upload.js:1439`).
- api: `/api/share/create` (`app/static/upload.js:1482`).
- api: `/api/words?` (`app/static/upload.js:1553`).
- api: `/api/words/duplicates` (`app/static/upload.js:1586`).
- api: `/api/words/${wordId}` (`app/static/upload.js:1694`).
- api: `/api/words/${wordId}` (`app/static/upload.js:1815`).
- api: `/api/words/${wordId}` (`app/static/upload.js:1837`).
- api: `/api/parse-file` (`app/static/upload.js:1963`).
- api: `/api/import-words` (`app/static/upload.js:2036`).

## `app/templates/account_type.html`

- api: `/api/account/type` (`app/templates/account_type.html:49`).

## `app/templates/admin_users.html`

- api: `/api/me` (`app/templates/admin_users.html:156`).

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
- global: `updateChildGoalOptimistic` (`app/templates/base.html:543`).
- api: `/api/child-learning/status?tz_offset=${tzOffset}` (`app/templates/base.html:558`).
- api: `/api/daily-goal` (`app/templates/base.html:582`).
- template_script: `{{ url_for(` (`app/templates/base.html:870`).
- template_script: `{{ url_for(` (`app/templates/base.html:871`).
- service_worker: `/sw.js` (`app/templates/base.html:875`).

## `app/templates/difficult.html`

- template_style: `{{ url_for(` (`app/templates/difficult.html:4`).
- template_script: `{{ url_for(` (`app/templates/difficult.html:62`).
- template_script: `{{ url_for(` (`app/templates/difficult.html:63`).

## `app/templates/family_link.html`

- api: `/api/family/link` (`app/templates/family_link.html:28`).

## `app/templates/index.html`

- api: `/api/learning/streak?tz_offset=${offset}` (`app/templates/index.html:219`).
- api: `/api/user_lessons` (`app/templates/index.html:494`).
- api: `/api/user_lessons/delete` (`app/templates/index.html:575`).
- api: `/api/lesson_words?lesson=${encodeURIComponent(lessonTitle)}` (`app/templates/index.html:639`).
- api: `/api/lessons` (`app/templates/index.html:670`).
- api: `/api/lessons` (`app/templates/index.html:689`).
- api: `/api/lessons/set_hidden` (`app/templates/index.html:771`).

## `app/templates/learn.html`

- template_style: `{{ url_for(` (`app/templates/learn.html:4`).
- global: `LESSON_TITLE` (`app/templates/learn.html:97`).
- global: `LEARN_I18N` (`app/templates/learn.html:98`).
- template_script: `{{ url_for(` (`app/templates/learn.html:107`).
- template_script: `{{ url_for(` (`app/templates/learn.html:109`).
- api: `/api/lesson_words?lesson=` (`app/templates/learn.html:143`).

## `app/templates/mcp_consent.html`

- template_style: `{{ url_for(` (`app/templates/mcp_consent.html:9`).

## `app/templates/parent_dashboard.html`

- api: `/api/family/children/${encodeURIComponent(selectedChildId)}/lesson-words?lesson=${encodeURIComponent(lesson)}` (`app/templates/parent_dashboard.html:298`).
- api: `/api/family/children/${encodeURIComponent(childId)}` (`app/templates/parent_dashboard.html:323`).
- api: `/api/family/children/${encodeURIComponent(child.user_id)}/priority-lesson` (`app/templates/parent_dashboard.html:339`).
- api: `/api/family/dashboard?days=${periodSelect.value}&tz_offset=${offset}` (`app/templates/parent_dashboard.html:362`).

## `app/templates/settings.html`

- api: `/api/user-languages` (`app/templates/settings.html:274`).
- api: `/api/ui-language` (`app/templates/settings.html:275`).
- api: `/api/daily-goal` (`app/templates/settings.html:297`).
- api: `/api/family/pairing-code` (`app/templates/settings.html:349`).
- api: `/api/family/invite-code` (`app/templates/settings.html:359`).
- api: `/api/family` (`app/templates/settings.html:370`).
- api: `/api/user-languages` (`app/templates/settings.html:462`).
- api: `/api/user-languages/missing-words?languages=${encodeURIComponent(languages.join(` (`app/templates/settings.html:503`).
- api: `/api/translate/word` (`app/templates/settings.html:514`).
- api: `/api/words/${item.id}` (`app/templates/settings.html:527`).
- api: `/api/daily-goal` (`app/templates/settings.html:548`).
- api: `/api/ui-language` (`app/templates/settings.html:564`).
- api: `/api/mcp/user` (`app/templates/settings.html:592`).
- api: `/api/mcp/user` (`app/templates/settings.html:619`).
- api: `/api/mcp/user/revoke-all` (`app/templates/settings.html:653`).

## `app/templates/share.html`

- api: `/api/share/` (`app/templates/share.html:117`).

## `app/templates/subscription.html`

- api: `/api/subscription` (`app/templates/subscription.html:88`).

## `app/templates/upload.html`

- api: `/api/me` (`app/templates/upload.html:481`).
- global: `PUBLIC_BASE_URL` (`app/templates/upload.html:821`).
- template_script: `{{ url_for(` (`app/templates/upload.html:824`).

## Offline flow

`idb.js` открывает IndexedDB/stores → действия без сети попадают в outbox → `sync.js` отправляет progress в `/api/progress/sync` → `/api/sync/updates?since=...` возвращает delta → локальные stores обновляются. `sw.js` обслуживает кэш shell/static; `audio_worker.js` координирует аудиокэш.
