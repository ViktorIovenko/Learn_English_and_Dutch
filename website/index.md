# ParallelLingvo

> ParallelLingvo is a multilingual vocabulary learning application with an initial catalog of 45 learning languages. Learners can choose three or more languages and keep vocabulary, translations, pronunciation and learning progress connected in one learning flow.

## Learning languages

The launch catalog covers major European languages plus selected major world languages. The backend is language-agnostic, so additional languages can be added without changing the database schema.

The authoritative catalog is maintained in `app/languages.py`.

## What ParallelLingvo does

- Organizes vocabulary into lessons.
- Connects one vocabulary concept with forms in three or more selected languages.
- Starts with a 45-language learning catalog.
- Stores translations in normalized `word_translations` records instead of one column per language.
- Provides pronunciation audio.
- Lets users mark difficult words for extra review.
- Tracks learning activity and progress at word level.
- Uses a mobile-first web interface and Telegram Mini App access.

## How multilingual learning works

Instead of creating separate bilingual decks, ParallelLingvo organizes vocabulary around one concept. The learner chooses three or more supported languages, and the corresponding translations remain connected to the same learning item.

## Current localized website interfaces

- English: https://parallellingvo.app/
- Nederlands: https://parallellingvo.app/nl/
- Русский: https://parallellingvo.app/ru/
- Deutsch: https://parallellingvo.app/de/
- Français: https://parallellingvo.app/fr/
- Español: https://parallellingvo.app/es/
- Italiano: https://parallellingvo.app/it/
- Português: https://parallellingvo.app/pt/
- Polski: https://parallellingvo.app/pl/
- 中文（普通话）: https://parallellingvo.app/zh/
- 日本語: https://parallellingvo.app/ja/

Website-interface localization is separate from the number of languages that can be learned in the application.

## Platforms

- Public website: https://parallellingvo.app/
- Telegram / web application: https://app.parallellingvo.app/
- iOS application: planned.
- Android application: planned.

## Account access

The public site is designed for account registration and sign-in through Google and Telegram. The authentication endpoints are prepared for backend integration.

## Blog

The editorial blog currently has localized English, Dutch and Russian content:

- English: https://parallellingvo.app/blog/
- Nederlands: https://parallellingvo.app/nl/blog/
- Русский: https://parallellingvo.app/ru/blog/

Project repository: https://github.com/ViktorIovenko/Learn_English_and_Dutch
