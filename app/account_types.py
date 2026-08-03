from __future__ import annotations

import sqlite3


ACCOUNT_TYPE_MIGRATION = "20260704_existing_accounts_to_standard"
VALID_ACCOUNT_TYPES = ("pending", "child", "standard")


def migrate_account_types(conn: sqlite3.Connection) -> None:
    """Normalize legacy users once without affecting future registrations."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "account_type" not in columns:
        conn.execute(
            "ALTER TABLE users ADD COLUMN account_type "
            "TEXT NOT NULL DEFAULT 'standard'"
        )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_schema_migrations (
            name TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    applied = conn.execute(
        "SELECT 1 FROM app_schema_migrations WHERE name=?",
        (ACCOUNT_TYPE_MIGRATION,),
    ).fetchone()
    if not applied:
        # At deployment time `pending` means an old account for which no role
        # was selected. New registrations remain pending because the marker is
        # stored before they are created.
        conn.execute("""
            UPDATE users
            SET account_type='standard'
            WHERE account_type IS NULL
               OR TRIM(account_type)=''
               OR account_type NOT IN ('child', 'standard')
        """)
        conn.execute(
            "INSERT INTO app_schema_migrations (name) VALUES (?)",
            (ACCOUNT_TYPE_MIGRATION,),
        )
    else:
        # Keep repairing malformed values, but preserve legitimate pending
        # rows created by the new Telegram onboarding flow.
        conn.execute("""
            UPDATE users
            SET account_type='standard'
            WHERE account_type IS NULL
               OR TRIM(account_type)=''
               OR account_type NOT IN ('pending', 'child', 'standard')
        """)
    conn.commit()
