# LearnWords Android App

Android приложение на Kotlin для изучения слов (NL/EN/RU и другие языки).

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

В `app/build.gradle`:
```groovy
buildConfigField "String", "BASE_URL", '"https://your-server.com/"'
```

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
│   ├── java/com/learnwords/app/
│   │   ├── MainActivity.kt
│   │   ├── LearnWordsApp.kt
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
