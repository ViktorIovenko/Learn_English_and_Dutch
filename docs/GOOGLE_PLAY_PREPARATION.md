# ParallelLingvo: подготовка Google Play

Дата: 2026-10-22. Package: `app.parallellingvo`.

Это локальная подготовка, не разрешение на публикацию. Production, Play Console,
настоящие подписки, ключи подписи и платежи в ходе работы не изменяются.

Подтверждено владельцем: аудитория — **дети и взрослые, семейное обучение**;
аккаунт Google Play Developer — **личный, создан 21 октября 2026 года**.
Следовательно, перед заявкой на production-доступ нужен closed test с минимум
12 участниками, подключёнными непрерывно не менее 14 дней. Это не обещание даты
публикации: отсчёт зависит от реального подключения участников и последующей проверки.

## Реализованные контракты

- `GET /api/subscription/google-play-config`: только Bearer. Возвращает реальные
  Product ID из конфигурации сервера и непрозрачный account ID для Google Play.
- `POST /api/subscription/verify_purchase`: только Bearer. Google
  `purchases.subscriptionsv2.get` определяет продукт, владельца, состояние и expiry.
  Клиент не назначает тариф, цену, срок и статус. После проверки владелец токена
  закрепляется в SQLite; token шифруется для последующей серверной синхронизации.
  `acknowledge` выполняется сервером после проверки, до выдачи доступа.
- Pending, paused, on-hold и expired не выдают доступ. Canceled сохраняет уже
  оплаченный срок, grace period сохраняет доступ согласно состоянию Google.
  Linked purchase supersedes старый токен. Повторная обработка не прибавляет срок.
- Ручные/другие действующие подписки и особые права admin автоматически не меняются.
  Конфликт провайдеров возвращает ошибку; перенос доступа требует решения владельца.
- `POST /api/subscription/sync`: повторная проверка ранее привязанных покупок.
- `POST /api/subscription/google-play-notifications`: Pub/Sub RTDN, обязательная
  проверка OIDC audience и service-account email. Уведомление само не выдаёт доступ:
  сервер снова запрашивает Google. Неизвестный токен ждёт авторизованного restore.
- `python -m app.google_play`: резервная серверная сверка всех известных токенов.
  Возвращает только счётчики, ненулевой exit status при ошибке (после настройки).
- Android: Billing 9.1.0, явные состояния оплаты/проверки, восстановление покупок
  через сервер, WorkManager с сетью и backoff; периодическая сверка каждые 15 минут.
  После переустановки токены вновь запрашиваются у Play, в WorkManager не сохраняются.
- `GET /api/account/deletion-challenge`, `POST /api/account/delete`: только
  собственный Bearer/веб-сеанс, короткоживущее подтверждение + `confirm=DELETE`,
  CSRF-защита веб-формы. Произвольный `user_id` в JSON не выбирает цель удаления.
- `/account/delete`: внешняя страница с входом и удалением без установки Android.
- Удаление очищает live DB: профиль, identities, credentials/reset links, настройки,
  прогресс, слова/личные уроки, MCP grants/codes, consent, семейные связи и другие
  связанные записи. Общий словарь, общий TTS-кэш и аккаунты членов семьи сохраняются.
  Отзываются старые Bearer и cookie-сессии, в том числе после повторной регистрации.
  На устройстве очищаются Room, кэш и preferences.
- Минимальные псевдонимные security fingerprints остаются для предотвращения
  повторного использования токенов. Это не бухгалтерские документы и не основание
  сохранять полные профили. Срок/основание хранения должен утвердить владелец.
- `/privacy`: черновик закрыт (404) до явного согласования и настройки оператора.
  Локальный просмотр без браузера доступен через Flask test client `TESTING=True`.
- Android auth token и pending auth verifier шифруются AES-GCM / Android Keystore;
  существующие plaintext значения мигрируют при чтении. При потере ключа нужен вход.
- Удалены широкие разрешения галереи; камера оставлена для QR, необязательна для
  установки. Backup отключён, cleartext запрещён, HTTP logging отключён.

## Настройки владельца: Google Play и backend

1. Play Console → убедиться в верификации developer account, стране, контактах и
   типе аккаунта. Создать/открыть приложение с package `app.parallellingvo`.
   Проверить, что это именно выбранный окончательный package: после публикации
   изменить его как обновление существующего приложения нельзя.
2. Monetize → Products → Subscriptions: выбрать **существующие** продукты и base
   plans либо самостоятельно утвердить их создание, периоды и цены. В коде нет
   придуманных Product ID/цен и нет автоматического создания продуктов.
3. Передать реальное соответствие Product ID тарифам сервера: JSON-объект
   `GOOGLE_PLAY_PRODUCTS_JSON`, где ключ — точный ID из Console, значение только
   `premium` или `family`. Все действующие старые продукты также должны быть
   представлены до окончания их обслуживания. Несколько тарифов в одном Product ID
   с разными base plans сейчас не поддержаны — согласовать отдельную карту base
   plan, если именно так уже устроена Console. Не переименовывать продукты вслепую.
4. В Google Cloud включить Google Play Android Developer API. Создать/выбрать
   сервисную identity и предоставить ей доступ к конкретному приложению в Play
   Console с правами просмотра подписок/покупок и управления заказами/подписками,
   необходимыми get/acknowledge. Использовать минимальные доступные права.
5. Предпочесть workload identity; для JSON credentials разместить существующий
   файл **вне репозитория**, задать `GOOGLE_APPLICATION_CREDENTIALS` абсолютным
   путём в окружении backend. JSON, токены, пароли и keystore не пересылать в чат.
   Используется уже имеющийся `google-auth` и requests, отдельный API client не нужен.
6. Убедиться, что `SECRET_KEY` — стабильный production secret, не `dev-key`.
   Шифрование серверных purchase tokens и revocation fingerprints зависит от него;
   смена ключа требует отдельной миграции, не делать её произвольно.
7. Покупки по умолчанию скрыты (`GOOGLE_PLAY_PURCHASES_ENABLED=0`). Включать `=1`
   только для согласованного тестового этапа после настройки credentials и продуктов.
8. Google Cloud Pub/Sub: создать/выбрать topic, дать Google Play publisher право
   публикации; в Play Console → Monetization setup подключить RTDN к этому topic.
   Подписку push настроить на HTTPS endpoint
   `/api/subscription/google-play-notifications` с OIDC. Настроить
   `GOOGLE_PLAY_RTDN_AUDIENCE` (точный audience push) и
   `GOOGLE_PLAY_RTDN_SERVICE_ACCOUNT` (email выбранной push identity).
   Разрешить Pub/Sub подписывать OIDC за эту identity штатными IAM-правами.
   Подтвердить доставку test notification и затем sandbox purchase notifications.
9. После разрешённого deployment настроить резервный timer/cron для
   `python -m app.google_play` в том же venv/config, например каждые 15 минут.
   Секреты передавать существующим механизмом окружения сервиса, не через аргументы.
   RTDN нужен для оперативных refund/revoke, timer — для восстановления пропусков.
10. Старые покупки без `obfuscatedExternalAccountId` не присваиваются первому
    предъявившему токен. Если такие покупки действительно существуют, согласовать
    миграцию по достоверным прежним данным. Автоматического небезопасного claim нет.

## Privacy Policy: решения до публикации

### Уточнение владельца и инфраструктурная проверка — 2026-10-26

- Оператор: Виктор Иовенко, Нидерланды; публичный контакт `info@parallellingvo.app`.
- Владелец подтвердил одобрение аккаунта Play Console и регистрацию package.
- Планируемые регионы: Европа, США, Канада, Австралия. Аудитория: семейное
  обучение, включая детей. Конкретные возрастные группы пока не определены.
- На Server 1 проверены метаданные работающих контейнеров: приложение использует
  `json-file` без заданной ротации; proxy — до трёх файлов по 20 MB. Это не сроки
  хранения в днях. Политику хранения нельзя считать реализованной.
- В проверенных system timers и root crontab не найдено application backup job.
  Provider snapshots, ручные копии и другие механизмы этим не исключаются.
- В production на момент проверки отсутствовали `app/account_privacy.py` и обе
  страницы; backend удаления требует отдельного точечного применения.
- Privacy остаётся закрытым черновиком до завершения retention, проверки
  фактических обработчиков/международной передачи и процедуры родительского
  согласия. Наличие семейной связи не доказывает возраст или согласие родителя.
- Для запроса удаления данных ребёнка указан контакт оператора; раскрытие или
  удаление чужого аккаунта требует проверки полномочий заявителя.
- SMTP host из проверенного startup environment/default конфигурации —
  `smtp.purelymail.com`. Секреты и `.env` не читались; startup environment не
  доказывает итоговые настройки, загруженные приложением после запуска.
- По прямой команде владельца 2026-10-26 удаление применено на Server 1:
  `app/account_privacy.py`, `app/auth_links.py`, обе страницы и точечная регистрация
  privacy/account endpoints в действующем production `app/routes.py`.
  Остальные локальные изменения `routes.py` не переносились. Проверены хэши всех
  пяти файлов в host deployment и контейнере; перезапущен только `learn-words`,
  контейнер остался running. Сборка образа не выполнялась. Резервные копии исходников:
  `/opt/learn-words/deploy-backups/account-delete-20261026T112928Z`.
  Полный local/production parity этим не подтверждается. Privacy approval не включён;
  не публиковать незавершённый Privacy. Пользовательское удаление не запускалось.

Черновик: `app/templates/privacy.html`. Требуется утвердить:

- юридического оператора, email privacy/support, применимые страны и дату действия;
- целевые возрасты, процедуру родительского согласия и пригодность providers;
- точные сроки инфраструктурных логов, резервных копий, security fingerprints,
  обязательной финансовой документации и порядок удаления из внешних providers;
- список реально включённых hosting/email/TTS/AI/MCP/advertising providers,
  договоры обработки и трансграничные гарантии;
- обоснование/срок сохранения общих словарных и pronunciation caches, правило для
  личного содержимого в них; если это персональные данные, нужен отдельный purge.

Текст содержит явно отмеченные нерешённые пункты. До их устранения он **не готов
как юридический документ**, даже если технический маршрут работает. После
согласования текста: настроить `PRIVACY_OPERATOR_NAME`, `PRIVACY_CONTACT_EMAIL`,
`PRIVACY_POLICY_APPROVED=1`. Самостоятельно это не включать.

План удаления резервных копий/внешних данных нельзя подтвердить локальным кодом.
Восстановление backup должно повторно применять tombstones/erasure records, чтобы
не вернуть удалённые аккаунты. Отмена Google Play подписки выполняется отдельно.

## Data safety: проект ответов для владельца

Заполнять по **публикуемой сборке и реальному production**, не по отключённым SDK.
Консоль не проверялась. Это inventory и предварительные ответы, не поданная форма.

| Категория | Что реально обрабатывается | Назначение / обязательность |
|---|---|---|
| Personal info: name, email, user IDs | профиль выбранного login provider, email-login, account ID | создание/управление аккаунтом; имя/email зависят от метода входа |
| Financial info: purchase history | Product ID, token, состояние/expiry и account binding | покупки/проверка доступа; только для покупки |
| App activity: app interactions | выполнение упражнений, прогресс, даты, цели, consent | обучение, семейные отчёты, работа сервиса |
| Other user-generated content | собственные уроки, слова, примеры, содержимое импорта | работа функций; по действию пользователя |
| Device or other IDs | внутренние user IDs/obfuscated account ID; не AAID/IMEI | аутентификация/защита покупок; уточнить категорию по текущей форме |
| Approximate location | страна для рекламного выбора, если production получает geo-header | условно: проверить фактически включённый proxy/рекламный режим |
| Diagnostics | технические ошибки, counters и серверные журналы | проверить фактический сбор hosting/proxy, сроки и состав |

Передача: Google auth/Play, Telegram, hosting/email/TTS, включённые AI providers,
согласованные MCP apps; Awin/advertiser hosts при рекламных запросах/переходах.
Не заявлять «не передаём данные», пока не оценены все эти потоки. Исключения формы
для service providers и передачи по инициативе пользователя применять только
после проверки условий Google. Сама передача IP на image host не исчезает из-за
отсутствия Authorization/cookies.

- Password хранится хэшем; не объявлять это сбором номера карты. Карту обрабатывает Play.
- Location/contacts/microphone/широкая галерея не запрашиваются Android-кодом.
- Camera используется QR scanner локально, кадры не отправляются backend этим потоком.
- Firebase Analytics, Crashlytics, AdMob и рекламный SDK не подключены в Gradle.
  Это не означает отсутствия серверных логов/affiliate tracking.
- «Encrypted in transit»: Android требует HTTPS; все активные server/provider URL
  и инфраструктуру владелец должен подтвердить перед ответом Yes.
- «Can users request deletion»: реализованы in-app и web paths; ответ Yes после
  разрешённого deployment и проверки публичной доступности.
- Privacy URL: `https://app.parallellingvo.app/privacy` после согласования.
- Deletion URL: `https://app.parallellingvo.app/account/delete` после deployment.

## Families и реклама

`child` и `pending` не получают live ads на сервере; ошибка/unknown account type
не должны расширять доступ к рекламе. Упражнения и family accounts сохраняются.
Существующие policy tests проверяют эти ограничения, consent и paid exclusions.

Выбор `standard` — **не проверка возраста**. Владелец подтвердил mixed audience:
дети и взрослые. До публикации нужно выбрать конкретные возрастные группы и страны,
подготовить нейтральную проверку возраста для рекламного потока, определить
требуемое родительское согласие и проверить допустимость Awin для этой аудитории.
Нейтральная проверка возраста/родительское согласие в этой задаче не реализованы:
порог возраста, страны и рекламная схема требуют отдельного решения владельца.
Это остаётся блокером выпуска с live-рекламой. Не переключать возрастную маркировку
ради обхода Families и не добавлять самостоятельно новый ad SDK/платные ограничения.

Предлагаемый вариант для согласования: выпуск с отключённой live-рекламой до
утверждения age/consent/provider потока. Настройки бизнеса этим документом не меняются.

## Подпись, OAuth, AAB

- `compileSdk=36`, `targetSdk=36`, `minSdk=24`; package сохранён.
- `versionCode=2`, `versionName=1.2` сохранены как исходные. Перед upload сверить
  Console: новый code должен быть больше всех ранее загруженных. Можно передать
  `PLAY_VERSION_CODE` и `PLAY_VERSION_NAME` для согласованного выпуска.
- Release не debuggable. Без signing variables bundle остаётся **unsigned**.
- Использовать существующий upload key. При сборке задать все четыре переменные:
  `PLAY_UPLOAD_STORE_FILE`, `PLAY_UPLOAD_STORE_PASSWORD`, `PLAY_UPLOAD_KEY_ALIAS`,
  `PLAY_UPLOAD_KEY_PASSWORD`. Только безопасное локальное окружение/secret manager;
  не вводить секреты в команды, сохраняемые в отчёте/истории. Альтернатива — Android
  Studio → Generate Signed App Bundle → выбрать существующий keystore.
- Ключи не создавались и не заменялись. Включить/проверить Play App Signing.
- В Google Cloud OAuth проверить Android client: package + **Play app-signing
  SHA-1**, не только upload/debug certificate. Web client ID, который backend
  возвращает для `requestIdToken`, должен принадлежать правильному проекту.
- `app/static/.well-known/assetlinks.json` уже содержит fingerprint. Сравнить его
  с **Play app-signing SHA-256**; не подменять неизвестным debug/upload сертификатом.
- Команда Gradle: `:app:bundleRelease :app:lintRelease --no-daemon --max-workers=2`.
  В checkout отсутствуют gradlew.bat/wrapper.jar: использовать установленный
  Gradle 9.3.1 и JDK 17+ (имеющийся Android Studio JBR подходит).
- Проверить итоговый AAB/сгенерированные split APK: manifest, отсутствие лишних
  permissions, signature, arm64/native `.so`, ELF LOAD alignment и ZIP alignment
  для 16 KB. Версия AGP сама по себе не подтверждает совместимость native SDK.
  Когда `.so` отсутствуют, ELF-проверка не нужна; отдельный device smoke всё равно нужен.

## Последовательность выпуска владельцем

1. Утвердить privacy/retention и возрастную аудиторию; передать реальные Product IDs
   и выбрать модель products/base plans без изменения существующих цен в коде.
2. Настроить API identity, RTDN и резервную сверку; согласовать deployment backend.
3. Получить подписанный AAB существующим ключом. Загрузить в **internal testing**.
4. Play Console → App content: Privacy, Data safety, Ads, Target audience, IARC
   rating, App access. Предоставить reviewer рабочий тестовый доступ к ограниченным
   функциям без реальной оплаты; не помещать реальные пароли в документацию.
5. Store listing: название/описания, support email, app icon, feature graphic,
   реальные screenshots поддерживаемых устройств и локалей. Их автоматически не создавали.
6. Настроить License testing/test accounts. Проверить только sandbox: purchase,
   pending→paid, cancel, renew, grace/hold, refund/revoke, restore after reinstall,
   restore after offline, конфликт другого app account, server timeout и retries.
7. Вручную проверить регистрацию email/Google/Telegram, обучение и offline queue,
   family/child flow, отсутствие рекламы у child/pending, управление подпиской,
   privacy link и удаление **специально созданного тестового** аккаунта с другого
   устройства/веб-сеанса. Существующие реальные аккаунты не удалять.
8. Проверить Google Play pre-launch report, Android 15/16 edge-to-edge, уведомления,
   QR permission отказ, поворот/возврат из оплаты, 16 KB устройство при native libs.
9. Для подтверждённого личного аккаунта от 2026-10-21: closed test минимум 12
   непрерывно участвующих testers 14 дней; затем заявка production access.
   Если участник выйдет и вернётся, его непрерывный срок начинается заново.
   Нужны реальные проверки приложения и обратная связь, а не только ожидание срока.
10. Только после устранения замечаний — отдельное разрешение на production release.

## Официальные источники

- https://developer.android.com/google/play/billing/migrate-gpblv9
- https://developer.android.com/google/play/billing/deprecation-faq
- https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2
- https://support.google.com/googleplay/android-developer/answer/13327111
- https://support.google.com/googleplay/android-developer/answer/10144311
- https://support.google.com/googleplay/android-developer/answer/14115180
- https://support.google.com/googleplay/android-developer/answer/9893335
- https://support.google.com/googleplay/android-developer/answer/14151465
- https://developer.android.com/guide/practices/page-sizes

Результаты конкретных запусков, список файлов, полный код и diff относительно
начала текущей задачи находятся в пакете отчёта `output/google-play-preparation-20261021/`.
