from __future__ import annotations

import sqlite3


ACCOUNT_TYPE_MIGRATION = "20260704_existing_accounts_to_standard"
VALID_ACCOUNT_TYPES = ("pending", "child", "standard")


def migrate_auth_identities(conn: sqlite3.Connection) -> None:
    """Upgrade the legacy provider/subject identity table in place."""
    table_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='auth_identities'"
    ).fetchone()
    if not table_exists:
        conn.execute("""
            CREATE TABLE auth_identities (
                provider TEXT NOT NULL,
                external_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                email TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (provider, external_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_identities_user "
            "ON auth_identities(user_id)"
        )
        return

    columns = {row[1] for row in conn.execute("PRAGMA table_info(auth_identities)")}
    if {"provider", "external_id", "user_id"}.issubset(columns):
        return
    if not {"provider", "user_id"}.issubset(columns):
        raise RuntimeError("Unsupported legacy auth_identities schema")

    external_source = next(
        (column for column in ("subject", "provider_user_id") if column in columns),
        None,
    )
    if not external_source:
        raise RuntimeError("Legacy auth_identities has no external identity column")
    email_source = "email" if "email" in columns else "NULL"

    conn.execute("DROP TABLE IF EXISTS auth_identities__canonical_new")
    conn.execute("""
        CREATE TABLE auth_identities__canonical_new (
            provider TEXT NOT NULL,
            external_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            email TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (provider, external_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    conn.execute(f"""
        INSERT OR IGNORE INTO auth_identities__canonical_new (
            provider, external_id, user_id, email
        )
        SELECT provider, {external_source}, user_id, {email_source}
        FROM auth_identities
        WHERE COALESCE(provider, '') <> ''
          AND COALESCE({external_source}, '') <> ''
          AND COALESCE(user_id, '') <> ''
    """)
    conn.execute("DROP TABLE auth_identities")
    conn.execute(
        "ALTER TABLE auth_identities__canonical_new RENAME TO auth_identities"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_auth_identities_user "
        "ON auth_identities(user_id)"
    )


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
