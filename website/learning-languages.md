# ParallelLingvo learning languages

ParallelLingvo starts with a 45-language learning catalog. This list is for learning content; website-interface localization is managed separately.

## Europe

English, Nederlands, Deutsch, Français, Español, Italiano, Português, Polski, Русский, Українська, Čeština, Slovenčina, Magyar, Română, Български, Hrvatski, Српски, Bosanski, Slovenščina, Ελληνικά, Svenska, Norsk, Dansk, Suomi, Eesti, Latviešu, Lietuvių, Íslenska, Gaeilge, Shqip, Македонски, Türkçe, Malti, Беларуская, Rumantsch, ქართული, Հայերեն, Azərbaycan dili.

## Major world languages

中文（普通话）, 日本語, 한국어, العربية, हिन्दी, Bahasa Indonesia, Tiếng Việt.

## Product rule

Users select at least three languages and can attach any number of supported language forms to one vocabulary concept.

The application source of truth is `app/languages.py`. Adding another language should normally require only catalog/UI/provider metadata, not a new database column.
