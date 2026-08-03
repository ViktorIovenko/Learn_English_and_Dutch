# Flask/backend scope

Начинай с `../docs/codex/API_MAP.md` или `DATABASE.md`, затем открывай конкретный handler. `routes.py` содержит страницы, API, sync и часть migrations; schema также распределена по `../run.py`, `../db_init.py`, `models.py`, `../bot/db.py` и специализированным модулям. При изменении API проверь Web/Telegram Mini App и Android contract. Не читай SQLite data и `.env`.
