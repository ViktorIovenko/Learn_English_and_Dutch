# LearnWords Android App

Android приложение на Kotlin для изучения слов (NL/EN/RU и другие языки).

## Нативный вход через Telegram

Кнопка Telegram и привязка Telegram в настройках используют исходный SDK Telegram
из модуля `telegram-login` (версия и MIT-лицензия указаны внутри модуля).
Автоматический переход в браузер отключён. Если Telegram недоступен, пользователь
может повторить попытку или выбрать email/Google. PKCE verifier и полученный токен
сохраняются в зашифрованной текущей попытке, включая восстановление процесса.
Сервер проверяет подпись, issuer, audience, срок токена и соответствие попытке;
для нового пользователя применяется существующая регистрация со статусом `pending`.

Перед проверкой на телефоне в BotFather → Bot Settings → Login Widget необходимо
зарегистрировать Android package `app.parallellingvo` и SHA-256 сертификата подписи.
Публичный client ID по умолчанию — `8903357617`; его можно заменить переменной сборки
`TELEGRAM_CLIENT_ID`, согласованной с серверным `TELEGRAM_OIDC_CLIENT_ID`.
Callback: `https://app4151474097-login.tg.dev/tglogin` (Android App Link).
Адрес Native App выдан BotFather отдельно и не вычисляется из OAuth Client ID.
Для локальной debug-подписи SHA-256:
`A7:57:D6:DD:EB:90:0E:DC:0E:AD:7B:3F:99:E9:5A:2E:83:59:99:E0:1B:BC:16:9E:16:E8:16:EA:7F:CE:84:ED`.
Для Google Play требуется сертификат App Signing из Play Console, а не upload key.
GitHub Packages credentials не нужны: исходники SDK включены в проект.

## Функционал

- **Список уроков** — просмотр, скрытие, удаление уроков
- **Игра-скрэмбл** — собери слово из перемешанных букв
- **Сложные слова** — слова отмеченные звёздочкой
- **Управление словами** — добавление вручную, генерация по теме (облачный ИИ), база слов
- **Настройки языков** — выбор 2–4 языков с приоритетами
- **Подписка** — статус пробного периода и подписки
- **Поделиться** — создание и импорт ссылок на наборы слов
- **Оффлайн кэш** — Room DB для работы без интернета
- **Синхронизация прогресса** — очередь событий с синхронизацией при появлении сети

## Стек технологий

| Категория | Библиотека |
|---|---|
| Архитектура | MVVM + Repository |
| UI | Fragments + ViewBinding |
| Навигация | Navigation Component + BottomNav |
| Database | Room |
| Network | Retrofit 2 + OkHttp |
| Async | Kotlin Coroutines + StateFlow |
| Preferences | DataStore |
| Audio | MediaPlayer |
| Layout | FlexboxLayout (тайлы букв) |

## Настройка

### 1. Укажи URL сервера

Идентификатор приложения (`applicationId`): `app.parallellingvo`. Внутренний namespace исходников: `app.parallellingvo`.

В `app/build.gradle`:
```groovy
buildConfigField "String", "BASE_URL", '"https://app.parallellingvo.app/"'
```

Сохранённый адрес прежнего сервера автоматически заменяется на актуальный при чтении и сохранении настроек. Ссылки на аудио со старым доменом также переводятся на новый сервер.

### 2. Бэкенд: добавь поддержку Android-аутентификации

В `routes.py` добавь middleware, который принимает заголовок `X-Android-User-Id`:

```python
@app.before_request
def android_auth():
    android_user_id = request.headers.get('X-Android-User-Id')
    if android_user_id and 'user_id' not in session:
        session['user_id'] = android_user_id
        # Создай пользователя если не существует
        db.ensure_user(android_user_id)
```

### 3. Сборка

```bash
cd android
./gradlew assembleDebug
```

APK будет в `app/build/outputs/apk/debug/app-debug.apk`

## Структура проекта

```
android/
├── app/src/main/
│   ├── java/app/parallellingvo/
│   │   ├── MainActivity.kt
│   │   ├── ParallelLingvoApp.kt
│   │   ├── data/
│   │   │   ├── api/         # Retrofit + модели API
│   │   │   ├── db/          # Room DB + сущности + DAO
│   │   │   └── repository/  # AppRepository
│   │   ├── ui/
│   │   │   ├── auth/        # Экран входа
│   │   │   ├── lessons/     # Список уроков
│   │   │   ├── learn/       # Игра со словами
│   │   │   ├── upload/      # Добавление слов (4 вкладки)
│   │   │   ├── difficult/   # Сложные слова
│   │   │   ├── settings/    # Настройки языков
│   │   │   └── subscription/# Подписка
│   │   └── utils/           # PreferencesManager, AudioPlayer, Extensions
│   └── res/
│       ├── layout/          # XML разметки
│       ├── navigation/      # Nav Graph
│       ├── menu/            # Bottom navigation menu
│       └── values/          # Strings, Colors, Themes
└── build.gradle
```

## Экраны

| Экран | Описание |
|---|---|
| Auth | Ввод User ID и URL сервера |
| Lessons | Список уроков с кнопками Скрыть/Удалить |
| Learn | Игра: собери слово из перемешанных букв |
| Upload > Добавить | Ручной ввод + перевод через облачный ИИ |
| Upload > По теме | AI-генерация слов по теме (облачный ИИ) |
| Upload > База слов | Поиск, просмотр, удаление, генерация аудио |
| Upload > Поделиться | Создание и импорт share-ссылок |
| Сложные слова | Список помеченных слов |
| Языки | Выбор и сортировка языков |
| Подписка | Статус пробного периода |
