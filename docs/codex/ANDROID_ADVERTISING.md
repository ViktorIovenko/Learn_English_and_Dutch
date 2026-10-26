# Android: реклама и предпросмотр тарифов

Изменения подготовлены локально 2026-10-26. Production, рекламный режим,
подписки и Google Play не изменялись. APK не собирался и не публиковался.

## Контракт и доступ

Используется существующий advertising API без новых рекламных таблиц,
SDK и WebView. DTO сопоставлены с `views.py` и `selection.render_slot()`:
`creative_id` может быть числом или строкой, поля имеют snake_case.
Добавлен GET `/api/ads/consent`; запись согласия возвращает свой DTO.

Free получает доступ по `plan_state.features.learning` / `subscription.access`.
`paid_access` описывает оплату, а не право учиться. При сетевой ошибке
сохранённая авторизация позволяет открывать локальный учебный контент.
Family, AI и реклама читают серверный `plan_state`, отдельной матрицы тарифов нет.
Платные AI-действия дополнительно проверяют `paid_ai_available` перед запросом.

## Предпросмотр администратора

Карточка настроек появляется после `/api/me: is_admin=true`. Она переключает
Free / Premium / Family, позволяет выйти и отключить рекламные места в Free.
Значения хранятся отдельно в DataStore и очищаются при выходе, смене аккаунта
и ответе `/api/me`, который больше не подтверждает администратора.

ApiClient передаёт `X-Admin-Plan-Preview` и `X-Admin-Preview-Ads` только
аутентифицированному HTTPS origin API. Смена режима отменяет старые запросы
через SessionBoundary и повторно запрашивает `/api/me`. Если сервер не
подтвердил режим, клиент восстанавливает предыдущее значение. Общий индикатор
ведёт в настройки; навигация Family обновляется без перезапуска приложения.

Backend принимает Android preview только при валидном Bearer, точном
`X-Client: android`, совпадении пользователя токена с проверяемым пользователем
и реальном членстве в ADMIN_IDS. Допустимы только free/premium/family.
Заголовок обычного пользователя или неизвестное значение игнорируется.
Браузер продолжает использовать свой session preview; фоновые вызовы его
не наследуют. Для Android `/api/me.is_admin` сохраняет реальные права, а
симуляция возвращается в существующем `plan_state` и `subscription`.
База подписок, семейные связи и Play Billing не изменяются.

## Размещения по анализу XML

| Экран | Схема | Причина |
|---|---|---|
| Lessons | Toolbar → RecyclerView → `dashboard_bottom` → действия → BottomNavigation | Существующий отдельный ряд; список уменьшается по constraints |
| Learn | Навигация урока → языки/прогресс → `lesson_bottom` → слово → ответ/буквы → Check/Previous/Next | Контент помещён в NestedScrollView; кнопки доступны прокруткой |
| Words/Upload | вкладки → ViewPager с весом 1 → `secondary_bottom` → BottomNavigation | Баннер занимает отдельный ряд, не накрывает содержимое |

`dashboard_top` и `dashboard_between` не добавлены: на этом этапе оставлено
одно размещение на списке, чтобы не отнимать место у уроков. Контроллер
поддерживает placeholder, если сервер возвращает его для подключённого места.
Настройки, Family/Parent, покупка, авторизация и выбор типа аккаунта не стали
рекламными поверхностями. Child блокируется на сервере и клиенте.

Размер определяется шириной контейнера и пропорцией width/height сервера.
Phone/tablet определяется через smallestScreenWidthDp с границей 600dp.
Проверка фактического размещения на устройствах остаётся ручной.

## Рендеринг и события

Общий AdBannerController обращается через AdvertisingRepository.
demo/mock/placeholder строятся локальными Android View, без URL и событий.
Только сочетание `mode=live`, `decision.serve=live`, `preview=false` и
допустимого пользователя разрешает image/text. Неизвестные render скрываются.
HTML не интерпретируется.

Изображения загружает Coil через отдельный OkHttp без токенов, cookies и
идентификаторов. HTTPS проверяется и на redirect; downgrade запрещён.
Ответ ограничен 1 MB, декодирование запрашивает уменьшенный размер;
постоянный и memory cache рекламных изображений отключены. Ошибка скрывает слот.

Consent показывается только при `needs_consent=true`, с title/text/accept/
decline сервера. Выбор сохраняется через POST consent; после согласия
повторяется запрос рекламы. Предпросмотр не требует согласия.

Impression отправляется после успешной загрузки и непрерывной секунды, когда
видно минимум половину баннера и окно имеет фокус. Дедупликация на creative /
placement хранится в SavedStateHandle навигационного экрана, включая rotation.
При уходе с экрана загрузка, изображение, dialog и отложенный impression
отменяются. Ошибки рекламы не блокируют обучение и не показывают сообщение.

Click отправляется после нажатия, затем серверный HTTPS URL открывается
через CustomTabsIntent. Ожидание события ограничено 1,5 секунды. URL с
credentials, без hostname и с другими схемами не открываются. Redirect Awin
не раскрывается вручную; рекламодатель не зашит в APK.

## Изменённые файлы этой задачи

Backend:

- `app/routes.py`: безопасный Android preview, его интеграция в plan_state,
  advertising viewer и реальный is_admin в Bearer-ответе me.
- `app/advertising/policy.py`: выключатель preview ads и приоритет запрета Child.
- `tests/test_advertising.py`: четыре теста Android preview и его границ.

Android (пути относительно `android/app/`):

- `build.gradle`: androidx.browser и Coil.
- `src/main/java/app/parallellingvo/MainActivity.kt`.
- `src/main/java/app/parallellingvo/data/api/{ApiClient,ApiService,ApiModels}.kt`.
- `src/main/java/app/parallellingvo/data/repository/{AppRepository,AdvertisingRepository}.kt`.
- `src/main/java/app/parallellingvo/ui/ads/{AdBannerController,AdRenderPolicy,AdsSessionViewModel}.kt`.
- `src/main/java/app/parallellingvo/ui/auth/AuthViewModel.kt`.
- `src/main/java/app/parallellingvo/ui/learn/{LearnFragment,LearnViewModel}.kt`.
- `src/main/java/app/parallellingvo/ui/lessons/LessonsFragment.kt`.
- `src/main/java/app/parallellingvo/ui/settings/LanguageSettingsFragment.kt`.
- `src/main/java/app/parallellingvo/ui/upload/{UploadFragment,UploadViewModel}.kt`.
- `src/main/java/app/parallellingvo/utils/PreferencesManager.kt`.
- `src/main/res/layout/{activity_main,fragment_language_settings,fragment_learn,fragment_upload,admin_plan_preview}.xml`.
- `src/main/res/{values,values-ru}/admin_preview_strings.xml`.
- `src/test/java/app/parallellingvo/ui/ads/AdvertisingContractTest.kt`.

В общей папке параллельно менялась веб-админка; её изменения не относятся к
этому списку и сохранены.

## Проверки и ручные действия

53 backend-теста `tests.test_advertising` и `tests.test_plans` прошли в venv.
Они используют временные БД и тестовый Flask client, без реальных Awin-запросов.
Подтверждены все три тарифа, неизменность подписок, игнорирование подделанных
заголовков, отсутствие LIVE URL / событий в preview и сохранение web preview.

9 тестовых методов AdvertisingContractTest прошли отдельно в JVM: исходники
ApiModels и AdRenderPolicy скомпилированы установленным Kotlin compiler и Gson.
Во временной копии тестов JUnit assertions заменены на kotlin.test, методы
вызваны напрямую. Временные файлы удалены. Gradle/JUnit runner не запускался;
это не проверка сборки всего Android приложения и не UI-тест.

Дополнительно проверены Python syntax, изменённые XML и whitespace diff.
Индекс проекта обновлён только для файлов этой задачи.

Для функциональной проверки нужны backend с этим кодом и новая локальная
сборка приложения. После их применения проверить вручную:

1. Admin: Free → Premium → Family → выход; индикатор, AI, Family и подписка
   должны соответствовать тарифу. В Family лимит — четыре ребёнка.
2. Free preview: все три подключённых размещения, выключатель мест; никаких
   внешних рекламных переходов. Premium/Family — без рекламы.
3. Logout и вход обычным пользователем: карточка и прошлый preview отсутствуют.
4. Обычный Free после trial: уроки, упражнения, прогресс и offline доступны.
   Child не видит баннеров. Реальный LIVE не включать ради проверки.
5. Телефон 320–360dp, landscape, tablet, увеличенный шрифт: Check, клавиатура
   букв и Previous/Next доступны; баннер не перекрывает навигацию.
6. Прокрутка, rotation, уход с экрана и отсутствие сети: нет повторных показов,
   пустых больших блоков и ошибок, мешающих обучению.
