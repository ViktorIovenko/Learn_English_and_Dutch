# Production snapshot

Проверено: `2026-08-03T13:22:01+00:00`. Снимок содержит только обезличенные метаданные.

## Git и размещение

- Local: `C:\Users\ioven\Documents\Visual studio\Python\Learn_English_and_Dutch`, branch `master`, commit `849046dfe54e80c25d6fa3b72e4e893c0f3b330e`, dirty: `true`.
- Production: `/opt/learn-words`, branch `unavailable`, commit `unavailable`, dirty: `unknown`.
- Production Git SHA недоступен, если каталог развёртывания не содержит `.git`; идентичность файлов тогда определяется только по SHA-256.

## Runtime

- `learn-words-learn-words-1`: docker, working directory `/app`, port `7001`.

## Nginx

- `https://learn.iovenko.eu/` → `http://learn-words:7001` (`/opt/proxy/nginx/conf.d/learn.conf`).

## Расхождения

- Основные файлы с отличающимся SHA-256: не обнаружены среди проверенных файлов.
- Production schema: 21 таблиц; содержимое строк не читалось.
- В production есть runtime/data-каталоги, которые намеренно не индексировались.
