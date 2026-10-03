# ЗАДАЧА: production MCP-коннектор для Learn English & Dutch

## 1. Цель

Добавить к приложению Learn English & Dutch полноценный MCP-коннектор, который можно подключить в ChatGPT по публичному адресу:

`https://learn.iovenko.eu/mcp`

Коннектор должен позволять авторизованному пользователю работать **только со своими** уроками, словами, языками и прогрессом через естественные команды ChatGPT.

Примеры ожидаемого результата:

- «Покажи мои уроки и сколько слов осталось выучить».
- «Покажи сложные слова из урока Travel».
- «Создай урок Restaurant и добавь эти 20 слов на английском, нидерландском и русском».
- «Отметь эти слова как изученные».
- «Покажи прогресс моего ребёнка за неделю» — только для подтверждённого родителя и связанного ребёнка.
- «Импортируй созданный тобой CSV в новый урок» — через ChatGPT file reference, без ручного base64 и без локального filesystem path.

Это должна быть production-функция существующего приложения, а не отдельная демонстрация и не прямой доступ ChatGPT к SQLite.

## 2. Подтверждённый контекст проекта

- Основной web/API backend — Flask, entry point `run.py`, маршруты и бизнес-логика находятся преимущественно в `app/routes.py` и `app/models.py`.
- Production работает на Server 1: `204.168.186.69`, каталог `/opt/learn-words`.
- Публичный домен — `https://learn.iovenko.eu`.
- Штатный deployment — `deploy-changed.ps1`; полный infrastructure deployment — `deploy.ps1` или существующий режим `-IncludeInfrastructure` после проверки текущего скрипта.
- Production Compose сейчас содержит сервис `learn-words`, постоянную SQLite-базу и audio volume.
- Пользователь может входить через Telegram или Google. После входа приложение хранит внутренний `user_id`; все MCP-операции должны выполняться от имени этого пользователя.
- Существуют персональные уроки/слова, progress sync, difficult words, языковые настройки, account types и parent-child links.
- API одновременно используется Web/Telegram Mini App и Android. MCP не должен менять существующие API-контракты несовместимым способом.

Перед реализацией обязательно выполнить workflow из корневого `AGENTS.md` и запросить `.codex/project_kb.sqlite` через `tools/project_kb.py`.

## 3. Главные архитектурные требования

Использовать разделение:

```text
ChatGPT
  -> HTTPS Streamable HTTP MCP
  -> отдельный mcp-gateway
  -> типизированный internal API LearnWords
  -> существующие service/model functions
  -> SQLite и существующие provider integrations
```

### 3.1. MCP gateway

Создать отдельный Python-пакет, например:

```text
mcp_gateway/
  server.py
  tools.py
  client.py
  oauth.py
  config.py
  context.py
  models.py
  state.py
```

Gateway должен:

- использовать актуальный официальный Python MCP SDK;
- предоставлять Streamable HTTP endpoint `/mcp`;
- работать отдельным непривилегированным контейнером;
- не иметь volume с `words.db`, audio, Telegram persistence или `.env` основного приложения;
- не получать Google secret, Telegram bot token, AI Platform keys или административные токены;
- знать только internal API URL, собственный internal secret, OAuth-конфигурацию и Redis URL;
- обращаться к бизнес-логике только через фиксированный internal API;
- передавать `X-Request-ID` по всей цепочке;
- возвращать ограниченный структурированный результат.

Не импортировать `app/routes.py` и не открывать SQLite непосредственно из gateway.

### 3.2. Internal API

Добавить закрытый endpoint, например:

`POST /api/internal/mcp/execute`

Он должен принимать только запросы от gateway с отдельным `MCP_INTERNAL_TOKEN` и выполнять операцию из фиксированного allowlist.

Пример внутреннего envelope:

```json
{
  "operation": "lessons_list",
  "params": {},
  "user_id": "server-derived-user-id",
  "scopes": ["learning.read"],
  "client_id": "hashed-client-id",
  "request_id": "uuid"
}
```

Ответ всех операций:

```json
{
  "ok": true,
  "data": {},
  "warnings": [],
  "truncated": false,
  "error": null
}
```

Ошибка:

```json
{
  "ok": false,
  "data": null,
  "warnings": [],
  "truncated": false,
  "error": {
    "code": "LESSON_NOT_FOUND",
    "message": "Lesson was not found",
    "retryable": false,
    "details": {}
  }
}
```

Не возвращать traceback, SQL, секреты, cookies или внутренние filesystem paths.

## 4. Авторизация пользователя

Для публичного ChatGPT-коннектора реализовать OAuth Authorization Code + PKCE.

Обязательный flow:

1. ChatGPT начинает OAuth на `learn.iovenko.eu`.
2. Если пользователь не вошёл в LearnWords, он проходит существующий Google/Telegram login.
3. Страница consent показывает приложение, запрашиваемые MCP permissions и текущий LearnWords-профиль.
4. После подтверждения создаётся одноразовый короткоживущий authorization code.
5. Gateway выдаёт opaque access token с ограниченными scopes.
6. На каждом MCP-вызове gateway серверным способом определяет `user_id` из access grant.

Запрещено:

- принимать `user_id` от ChatGPT как доверенный идентификатор;
- использовать Flask session cookie как MCP bearer token;
- использовать Google access token или Telegram данные напрямую как MCP token;
- выдавать одному пользователю данные другого пользователя;
- автоматически выдавать admin scope существующему администратору без отдельного consent и server-side policy.

Access tokens хранить только в безопасной форме: предпочтительно opaque random token + hash в server-side storage. Нужны expiry, revoke и client binding. Authorization code должен быть одноразовым и короткоживущим.

Добавить OAuth endpoints и metadata, необходимые актуальному ChatGPT/MCP client. Перед кодированием перепроверить актуальные требования в официальной документации OpenAI и MCP SDK: названия metadata и клиентский контракт могут меняться.

## 5. Permission groups и scopes

Права проверяются server-side, а не только скрываются в интерфейсе.

Предлагаемые scopes:

| Группа | Scope | Назначение |
|---|---|---|
| Overview | `learning.read` | профиль, capabilities, уроки, слова, прогресс |
| Learning write | `learning.write` | создание/редактирование уроков и слов, запись прогресса |
| Family read | `family.read` | статус семьи и статистика только связанных детей |
| Family write | `family.write` | приоритетный урок и другие явно разрешённые parent actions |
| Files | `learning.files` | импорт файла, полученного через ChatGPT runtime |
| Admin | `learning.admin` | не включать в первый production этап |

По умолчанию выдавать только `learning.read`. Остальные группы пользователь включает явно на consent/admin-странице.

## 6. Предлагаемый каталог MCP tools

Не переносить каждый Flask route один в один. Инструменты должны отражать пользовательские действия и переиспользовать существующие функции.

### 6.1. System и discovery

- `system_info()` — имя коннектора, версия, protocol/runtime metadata.
- `system_health()` — дешёвая проверка gateway/internal API/DB без пользовательских данных.
- `system_capabilities()` — поддерживаемые языки, операции и лимиты.
- `permissions_get()` — выданные текущему подключению scopes.

### 6.2. Текущий пользователь

- `me_get()` — безопасный профиль без OAuth identifiers и секретов.
- `my_languages_get()` — выбранные языки и доступные языки.
- `my_learning_settings_get()` — учебные настройки, необходимые ChatGPT.
- `my_learning_settings_update(...)` — только allowlisted настройки.

### 6.3. Уроки и слова: read

- `lessons_list(include_hidden=false)`.
- `lesson_get(lesson_id | lesson_title)`.
- `lesson_words_list(lesson_id | lesson_title, limit, cursor)`.
- `difficult_words_list(lesson_id?, limit, cursor)`.
- `words_search(query, lesson_id?, limit)`.
- `word_get(word_id)`.
- `next_lesson_get(current_lesson_id?)`.
- `previous_lesson_get(current_lesson_id?)`.

Все списки должны иметь server-side limit и cursor/pagination. Не отдавать всю базу одним вызовом.

### 6.4. Уроки и слова: write

- `lesson_create(title, languages, idempotency_key)`.
- `lesson_rename(lesson_id, title)`.
- `lesson_set_hidden(lesson_id, hidden)`.
- `lesson_delete(lesson_id, confirm=false)` — destructive, обязательно `confirm=true`.
- `words_add(lesson_id, words[], idempotency_key)`.
- `word_update(word_id, fields)` — только разрешённые поля.
- `word_delete(word_id, confirm=false)`.
- `words_mark_difficult(word_ids, difficult)`.

Для `words_add`:

- ограничить число элементов за вызов;
- проверять длину и языковые поля;
- нормализовать только существующими правилами проекта;
- возвращать created/updated/skipped/duplicates/errors по каждому слову;
- не создавать частично повреждённый урок при ошибке;
- использовать idempotency key для защиты от повторного вызова ChatGPT.

### 6.5. Прогресс

- `progress_summary(days=7, lesson_id?)`.
- `progress_words_get(lesson_id, limit, cursor)`.
- `progress_record(word_id, result, occurred_at?, idempotency_key)`.
- `progress_record_many(items[], idempotency_key)`.
- `learning_recommendation_get()` — детерминированная рекомендация из существующего прогресса, без отдельного скрытого AI-вызова.

Не придумывать новую модель прогресса. Переиспользовать существующий progress sync/SRS contract, чтобы Web, Telegram Mini App и Android видели одинаковое состояние.

### 6.6. Family

- `family_status_get()`.
- `family_children_list()`.
- `family_child_progress_get(child_user_id, days=7)`.
- `family_child_lessons_list(child_user_id)`.
- `family_child_priority_lesson_set(child_user_id, lesson_id)`.

Каждый family tool обязан повторно проверять `parent_child_links` server-side. Сам факт знания `child_user_id` не даёт доступ.

Pair/unlink через MCP не добавлять в первый этап. Если их добавят позднее, операции должны требовать явное подтверждение и отдельный scope.

### 6.7. ChatGPT file upload

Добавить отдельный инструмент, например:

```text
lesson_import_file(
    file: FILE,
    lesson_title?: string,
    dry_run: boolean = true,
    idempotency_key?: string
)
```

Для ChatGPT Apps/MCP file workflow объявить file parameter через актуальную metadata SDK. На момент составления задания в Python MCP gateway Public_bot использовалось:

```python
meta={"openai/fileParams": ["file"]}
```

Перед реализацией перепроверить это в актуальной официальной документации OpenAI.

Требования:

- ChatGPT передаёт runtime file reference; пользователь не кодирует файл в base64;
- не принимать произвольный локальный путь строкой;
- принимать только HTTPS download reference, переданный runtime;
- SSRF protection, проверка redirect targets, DNS/IP, timeout и size limit;
- MIME проверять по содержимому, а не только имени/Content-Type;
- первый вызов по умолчанию `dry_run=true`: показать lesson title, языки, количество строк, duplicates и validation errors;
- запись выполняется отдельным подтверждённым вызовом;
- исходный файл после обработки удалять, если он не нужен продукту;
- поддерживаемые типы для первого этапа лучше ограничить UTF-8 CSV и JSON; XLSX добавлять только при наличии безопасного существующего parser и тестов.

Старый/структурированный путь `words_add` должен оставаться основным. File upload — дополнительный удобный вариант.

## 7. MCP resources и prompts

Полезные read-only resources:

- `learn://me`
- `learn://lessons`
- `learn://lessons/{lesson_id}`
- `learn://progress/summary`
- `learn://family/status`

Resources не должны обходить scope checks и pagination.

Полезные prompts:

- `create_vocabulary_lesson(topic, languages, word_count)` — сначала подготовить preview, не записывать без команды пользователя.
- `review_difficult_words(lesson_id?)` — получить сложные слова и провести учебную сессию.
- `analyze_learning_progress(days=7)` — прочитать статистику и объяснить её без изменения данных.

## 8. Переиспользование существующей логики

Нельзя создавать параллельную модель уроков/слов/прогресса только для MCP.

Нужно:

1. Найти существующие функции, которые используют Web/Android/Telegram.
2. При необходимости вынести минимальную общую service-функцию из Flask handler.
3. Оставить route как тонкий HTTP adapter.
4. Вызывать ту же service-функцию из internal MCP operation.
5. Добавить точечные тесты на одинаковое поведение.

Особенно проверить:

- user ownership каждого lesson/word;
- test/shared words против персональных words;
- язык и доступные language columns;
- progress sync timestamps и конфликт разрешения;
- hidden lessons;
- duplicates и numbering;
- parent/child authorization;
- account type ограничения;
- поведение Web, Telegram Mini App и Android после MCP-записи.

## 9. Хранилище состояния MCP

Не смешивать OAuth/MCP state с Telegram persistence.

Предусмотреть отдельные сущности:

- OAuth clients;
- authorization codes;
- hashed access tokens/grants;
- consented scopes;
- per-client permission groups;
- idempotency records;
- MCP audit log;
- revoked/expired grants.

Короткоживущее OAuth/rate-limit состояние рекомендуется хранить в отдельном Redis-контейнере. Если часть долговременного состояния хранится в SQLite, миграция должна быть явной, идемпотентной и резервируемой штатным способом проекта.

Audit log должен содержать только:

- timestamp;
- request ID;
- hashed client ID;
- internal user ID либо его безопасный stable hash;
- tool/operation;
- success/error code;
- duration;
- bounded counts.

Не записывать тексты всех слов, OAuth tokens, cookies, Google claims, Telegram payloads и секреты.

## 10. Безопасность

Обязательные ограничения:

- typed allowlist операций;
- server-side scopes;
- user identity только из OAuth grant;
- запрет arbitrary SQL;
- запрет shell/PowerShell/SSH/docker exec tools;
- запрет произвольного чтения/записи файлов;
- запрет выдачи `.env`, БД, audio paths и логов;
- no Docker socket;
- non-root gateway container;
- read-only filesystem, где возможно;
- bounded request/output size;
- rate limits per client/user;
- timeouts на internal/external requests;
- redaction ошибок и логов;
- SSRF protection для file references;
- destructive annotations и `confirm=true`;
- idempotency для всех создающих/массовых write операций;
- одинаковая проверка ownership внутри каждой business operation, даже если gateway уже авторизовал scope.

Internal API token не является пользовательской авторизацией. Он только подтверждает, что запрос пришёл от gateway; `user_id` и scopes должны происходить из проверенного OAuth grant.

## 11. Compose и production deployment

Предлагаемая production-схема:

```text
learn-words
mcp-gateway
mcp-redis
proxy-nginx (существующий внешний proxy)
```

Добавить внутреннюю сеть, например `learn_mcp_internal`:

- `learn-words` доступен gateway по internal URL;
- `mcp-gateway` доступен nginx;
- `mcp-redis` доступен только gateway;
- gateway не получает volume основного приложения;
- Redis не публикует порт наружу.

Nginx должен проксировать:

- `/mcp`;
- OAuth authorization/token/revoke endpoints;
- необходимые `/.well-known/...` metadata endpoints.

Настроить корректные body/time limits для Streamable HTTP, но не увеличивать их без ограничений.

Deployment scripts должны:

- доставлять `mcp_gateway/` и его Dockerfile/requirements;
- доставлять только необходимые backend changes;
- не перезаписывать production DB/audio/persistence;
- rebuild/recreate только `learn-words`, `mcp-gateway` и при необходимости `mcp-redis`;
- проверять status только этих сервисов;
- не перезапускать весь сервер или unrelated containers.

## 12. Административная страница

Добавить operator-only раздел в существующую админку:

- connector name/version/URL;
- copyable MCP URL;
- OAuth issuer/status;
- gateway/internal API/Redis health;
- permission groups и default state;
- список клиентов без tokens;
- last used, expiry, revoked state;
- revoke client/grant с подтверждением;
- bounded tool usage/error counts;
- icon preview/download, если коннектору нужен icon;
- build revision/created/version/source labels.

Нельзя показывать access tokens, internal token, Google secret, Telegram token, полные IP/UA или пользовательские слова.

## 13. Тесты

### 13.1. Unit

- tool schema и annotations;
- permission mapping;
- ownership для lesson/word/progress;
- parent-child checks;
- pagination/limits;
- idempotency;
- destructive confirmation;
- error envelope/redaction;
- file MIME/size/SSRF/path rejection;
- OAuth code single-use, expiry, PKCE и revoke.

### 13.2. Integration

- gateway -> internal API с корректным scope;
- отказ без internal token;
- отказ при выключенной permission group;
- отказ доступа к чужому lesson/child;
- создание урока видно существующему Web/API/Android contract;
- progress write читается существующим progress endpoint;
- file dry-run ничего не записывает;
- повтор idempotency key не создаёт дубликаты.

### 13.3. Production protocol verification

Недостаточно увидеть healthy container или Python registry.

После deployment выполнить реальный внешний OAuth-authenticated protocol flow:

```text
initialize
-> tools/list
-> resources/list
-> representative read call
-> representative reversible write call
-> read-after-write
-> cleanup
```

Проверить, что `tools/list` с публичного endpoint действительно содержит все заявленные tools и актуальные schemas. Отдельно проверить disabled group и revoke.

После изменения tool schema ChatGPT может использовать кеш старого коннектора. Для финальной проверки удалить/переподключить коннектор в ChatGPT и открыть новый чат.

### 13.4. Реальные пользовательские сценарии

После технических проверок пользователь вручную проверяет в ChatGPT:

1. Показать свои уроки.
2. Показать прогресс и сложные слова.
3. Создать небольшой тестовый урок через `words_add`.
4. Повторить запрос и убедиться, что idempotency не создала дубль.
5. Импортировать ChatGPT-generated CSV через file parameter сначала в dry-run.
6. Подтвердить импорт и увидеть урок в Web/Android.
7. Для parent account прочитать только связанного ребёнка.
8. Удалить тестовый урок с явным подтверждением.

Не выполнять браузерную/визуальную проверку автоматически без прямой просьбы пользователя.

## 14. Критерии готовности

Задача считается выполненной только если:

- MCP доступен на `https://learn.iovenko.eu/mcp`;
- OAuth + PKCE связывает ChatGPT с правильным LearnWords user;
- scopes реально проверяются server-side;
- gateway изолирован от DB, секретов и Docker socket;
- отсутствуют arbitrary shell/SQL/filesystem tools;
- заявленный tool catalog виден через реальный публичный `tools/list`;
- основные read/write tools используют существующую бизнес-логику;
- Web/Telegram Mini App/Android видят изменения согласованно;
- parent не может читать несвязанного child;
- write tools защищены idempotency, limits и ownership;
- file upload работает через ChatGPT file reference без ручного base64/path;
- тесты и production smoke checks прошли;
- production использует новую версию файлов и нужные контейнеры пересозданы;
- документация содержит URL, scopes, tools, deployment, revoke и troubleshooting;
- секреты и пользовательские данные не попали в Git, логи или отчёт.

## 15. Что не считать завершением

Не считать задачу готовой, если выполнено только одно из следующего:

- создан локальный MCP server без deployment;
- добавлены tools, но нет OAuth identity binding;
- `mcp-gateway` healthy, но внешний `tools/list` не проверен;
- tools напрямую читают SQLite или доверяют входному `user_id`;
- permission groups существуют только в UI;
- изменения видны только Web, но ломают Android/Telegram contract;
- file tool принимает обычный filesystem path;
- ChatGPT всё ещё видит старую схему после deployment;
- выполнены mocks, но не проверен реальный public protocol;
- production работает со старым image/container.

## 16. Рекомендуемая последовательность реализации

1. Прочитать `AGENTS.md`, запросить project KB и зафиксировать карту существующих service/API функций.
2. Согласовать точный MVP tool catalog и scopes; не начинать с admin tools.
3. Вынести минимальные общие service functions без широкого refactoring.
4. Реализовать typed internal API и тесты ownership.
5. Реализовать отдельный gateway и tool schemas.
6. Реализовать OAuth/PKCE, grants, scopes и revoke.
7. Добавить Redis/state, rate limits, audit и redaction.
8. Добавить file workflow с dry-run.
9. Добавить Compose/nginx/deployment изменения.
10. Выполнить focused tests.
11. Задеплоить штатным способом на Server 1.
12. Проверить hashes/build labels/status и публичный OAuth MCP protocol.
13. Переподключить коннектор в ChatGPT и передать ручные сценарии пользователю.

## 17. Обязательный итоговый отчёт исполнителя

После реализации предоставить:

1. список изменённых файлов;
2. полный список tools/resources/prompts;
3. permission groups и scopes;
4. описание OAuth identity binding;
5. перечень переиспользованных service functions;
6. миграции/новые таблицы без секретов и пользовательских данных;
7. результаты focused tests;
8. результат публичного `initialize -> tools/list`;
9. production deployment method, hashes/revision и service status;
10. что проверено технически и что оставлено пользователю для ручной проверки;
11. известные ограничения и следующий безопасный этап.

## 18. Практические уроки из предыдущих MCP-коннекторов

- Наличие функции в исходниках или registry не доказывает, что ChatGPT видит её: проверять публичный `tools/list`.
- ChatGPT может кешировать schema: после изменения tools иногда требуется удалить и заново подключить connector.
- Gateway должен быть transport/auth adapter, а не второй backend с копией бизнес-логики.
- User identity нельзя принимать параметром инструмента.
- Permission UI без server-side enforcement не является защитой.
- Для write tools обязательны idempotency и per-item results.
- Для file upload нужен настоящий runtime file parameter; base64 и пользовательский публичный URL не являются удобным file workflow.
- MIME, размер и содержимое проверяются до передачи в бизнес-логику.
- Deployment должен пересоздать именно изменённые сервисы; совпадение локального кода не означает обновление production.
- Healthy container не заменяет реальный OAuth-authenticated end-to-end вызов.
- Тестовые записи должны быть явно помечены и удалены после smoke-test.
