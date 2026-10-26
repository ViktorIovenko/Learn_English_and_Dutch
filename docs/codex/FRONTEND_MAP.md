# Frontend map

HTML-шаблоны рендерятся Flask, используют общие функции `base.html`; IndexedDB и Service Worker обеспечивают offline-first работу.

## `app/static/ads.js`

- api: `/api/ads/consent` (`app/static/ads.js:34`).
- api: `/api/ads/page?` (`app/static/ads.js:190`).

## `app/static/audio_worker.js`

- api: `/api/audio/ensure` (`app/static/audio_worker.js:21`).
- global: `AudioWorker` (`app/static/audio_worker.js:36`).

## `app/static/family_invite.js`

- global: `FamilyInvitation` (`app/static/family_invite.js:36`).
- api: `/api/family/invitation/preview` (`app/static/family_invite.js:90`).
- api: `/api/family/invitation/accept` (`app/static/family_invite.js:127`).

## `app/static/idb.js`

- indexeddb_store: `name` (`app/static/idb.js:21`).
- global: `LocalDB` (`app/static/idb.js:130`).

## `app/static/learn.js`

- global: `__LEARN_BOOTED__` (`app/static/learn.js:11`).
- global: `updateChildGoalOptimistic` (`app/static/learn.js:742`).
- api: `/api/words/${current.id}` (`app/static/learn.js:911`).
- api: `/api/lessons/set_hidden` (`app/static/learn.js:981`).
- api: `/api/words/${current.id}` (`app/static/learn.js:1110`).

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
- api: `/api/translate/language` (`app/static/upload.js:144`).
- api: `/api/import-words` (`app/static/upload.js:562`).
- api: `/api/share/source_lessons` (`app/static/upload.js:773`).
- api: `/api/user_lessons/rename` (`app/static/upload.js:834`).
- api: `/api/words/${wordId}` (`app/static/upload.js:1042`).
- api: `/api/words/${word.id}` (`app/static/upload.js:1116`).
- api: `/api/share/assign_child` (`app/static/upload.js:1235`).
- api: `/api/share/create` (`app/static/upload.js:1278`).
- api: `/api/parse-file` (`app/static/upload.js:1356`).
- api: `/api/import-words` (`app/static/upload.js:1429`).

## `app/static/word_database.js`

- api: `/api/translate/word` (`app/static/word_database.js:21`).
- api: `/api/words?` (`app/static/word_database.js:66`).
- api: `/api/words/duplicates` (`app/static/word_database.js:99`).
- api: `/api/words/${wordId}` (`app/static/word_database.js:216`).
- api: `/api/words/${wordId}` (`app/static/word_database.js:332`).

## `app/templates/account_type.html`

- api: `/api/account/type` (`app/templates/account_type.html:49`).

## `app/templates/admin_ads.html`

- global: `__adsResize` (`app/templates/admin_ads.html:464`).

## `app/templates/admin_users.html`

- api: `/api/me` (`app/templates/admin_users.html:137`).
- api: `/api/admin/plan-preview` (`app/templates/admin_users.html:213`).

## `app/templates/android_browser_login.html`

- api: `/api/auth/android/browser-session` (`app/templates/android_browser_login.html:16`).

## `app/templates/base.html`

- template_script: `https://telegram.org/js/telegram-web-app.js` (`app/templates/base.html:8`).
- template_style: `https://fonts.googleapis.com` (`app/templates/base.html:28`).
- template_style: `https://fonts.gstatic.com` (`app/templates/base.html:29`).
- template_style: `https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&display=swap` (`app/templates/base.html:30`).
- template_style: `{{ url_for(` (`app/templates/base.html:140`).
- template_style: `{{ url_for(` (`app/templates/base.html:141`).
- global: `AUTH_GATE_ENABLED` (`app/templates/base.html:237`).
- global: `I18N` (`app/templates/base.html:238`).
- global: `_HELLO_NAME_` (`app/templates/base.html:300`).
- global: `USER_ID` (`app/templates/base.html:311`).
- global: `IDB_KEY_PREFIX` (`app/templates/base.html:312`).
- global: `apiFetch` (`app/templates/base.html:313`).
- api: `/api/auth/login_webapp` (`app/templates/base.html:427`).
- api: `/api/auth/login_link` (`app/templates/base.html:439`).
- api: `/auth/status` (`app/templates/base.html:456`).
- api: `/api/me` (`app/templates/base.html:469`).
- global: `PLAN_STATE` (`app/templates/base.html:484`).
- global: `_HELLO_NAME_` (`app/templates/base.html:502`).
- api: `/api/admin/plan-preview` (`app/templates/base.html:559`).
- global: `updateChildGoalOptimistic` (`app/templates/base.html:600`).
- api: `/api/child-learning/status?tz_offset=${tzOffset}` (`app/templates/base.html:615`).
- api: `/api/daily-goal` (`app/templates/base.html:639`).
- template_script: `{{ url_for(` (`app/templates/base.html:927`).
- template_script: `{{ url_for(` (`app/templates/base.html:928`).
- service_worker: `/sw.js` (`app/templates/base.html:932`).
- template_script: `{{ url_for(` (`app/templates/base.html:939`).

## `app/templates/difficult.html`

- template_style: `{{ url_for(` (`app/templates/difficult.html:4`).
- template_script: `{{ url_for(` (`app/templates/difficult.html:62`).
- template_script: `{{ url_for(` (`app/templates/difficult.html:63`).

## `app/templates/email_auth.html`

- api: `/api/auth/email/` (`app/templates/email_auth.html:53`).

## `app/templates/family_invite.html`

- template_style: `{{ url_for(` (`app/templates/family_invite.html:3`).
- global: `FAMILY_BOT_USERNAME` (`app/templates/family_invite.html:28`).
- template_script: `{{ url_for(` (`app/templates/family_invite.html:29`).

## `app/templates/family_link.html`

- api: `/api/family/link` (`app/templates/family_link.html:28`).

## `app/templates/index.html`

- api: `/api/learning/streak?tz_offset=${offset}` (`app/templates/index.html:194`).
- api: `/api/user_lessons` (`app/templates/index.html:469`).
- api: `/api/user_lessons/delete` (`app/templates/index.html:550`).
- api: `/api/lesson_words?lesson=${encodeURIComponent(lessonTitle)}` (`app/templates/index.html:614`).
- api: `/api/lessons` (`app/templates/index.html:645`).
- api: `/api/lessons` (`app/templates/index.html:664`).
- api: `/api/lessons/set_hidden` (`app/templates/index.html:745`).

## `app/templates/learn.html`

- template_style: `{{ url_for(` (`app/templates/learn.html:4`).
- global: `LESSON_TITLE` (`app/templates/learn.html:100`).
- global: `LEARN_I18N` (`app/templates/learn.html:101`).
- template_script: `{{ url_for(` (`app/templates/learn.html:110`).
- template_script: `{{ url_for(` (`app/templates/learn.html:112`).
- api: `/api/lesson_words?lesson=` (`app/templates/learn.html:146`).

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
- template_script: `{{ url_for(` (`app/templates/settings.html:249`).
- api: `/api/user-languages` (`app/templates/settings.html:414`).
- api: `/api/ui-language` (`app/templates/settings.html:415`).
- api: `/api/daily-goal` (`app/templates/settings.html:437`).
- api: `/api/family/pairing-code` (`app/templates/settings.html:489`).
- api: `/api/family/invite-code` (`app/templates/settings.html:500`).
- api: `/api/family` (`app/templates/settings.html:512`).
- api: `/api/user-languages` (`app/templates/settings.html:616`).
- api: `/api/user-languages/missing-words?languages=${encodeURIComponent(languages.join(` (`app/templates/settings.html:657`).
- api: `/api/translate/word` (`app/templates/settings.html:668`).
- api: `/api/words/${item.id}` (`app/templates/settings.html:681`).
- api: `/api/daily-goal` (`app/templates/settings.html:702`).
- api: `/api/ui-language` (`app/templates/settings.html:718`).
- api: `/api/mcp/user` (`app/templates/settings.html:750`).
- api: `/api/mcp/user` (`app/templates/settings.html:764`).
- api: `/api/mcp/user` (`app/templates/settings.html:769`).
- api: `/api/subscription` (`app/templates/settings.html:947`).
- global: `PLAN_STATE` (`app/templates/settings.html:949`).

## `app/templates/share.html`

- api: `/api/share/` (`app/templates/share.html:117`).

## `app/templates/upload.html`

- api: `/api/me` (`app/templates/upload.html:354`).
- global: `PUBLIC_BASE_URL` (`app/templates/upload.html:603`).
- template_script: `{{ url_for(` (`app/templates/upload.html:606`).

## `app/templates/word_database.html`

- template_style: `{{ url_for(` (`app/templates/word_database.html:3`).
- template_script: `{{ url_for(` (`app/templates/word_database.html:78`).

## `output/deploy-ai-admin-20261022/app/templates/admin_users.html`

- api: `/api/me` (`output/deploy-ai-admin-20261022/app/templates/admin_users.html:156`).

## Offline flow

`idb.js` открывает IndexedDB/stores → действия без сети попадают в outbox → `sync.js` отправляет progress в `/api/progress/sync` → `/api/sync/updates?since=...` возвращает delta → локальные stores обновляются. `sw.js` обслуживает кэш shell/static; `audio_worker.js` координирует аудиокэш.
