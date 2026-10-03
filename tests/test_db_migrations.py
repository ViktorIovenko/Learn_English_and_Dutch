import sqlite3
import unittest

from app.account_types import migrate_account_types, migrate_auth_identities


class DatabaseMigrationTests(unittest.TestCase):
    def test_legacy_auth_identity_and_user_schema_are_upgraded(self):
        connection = sqlite3.connect(":memory:")
        connection.execute("""
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE auth_identities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                subject TEXT NOT NULL,
                provider_user_id TEXT,
                email TEXT,
                UNIQUE(provider, subject)
            )
        """)
        connection.execute(
            "INSERT INTO users (user_id) VALUES ('123')"
        )
        connection.execute("""
            INSERT INTO auth_identities (user_id, provider, subject, provider_user_id)
            VALUES ('123', 'telegram', '123', '123')
        """)

        migrate_auth_identities(connection)
        migrate_account_types(connection)

        identity_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(auth_identities)")
        }
        user_columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        identity = connection.execute(
            "SELECT provider, external_id, user_id FROM auth_identities"
        ).fetchone()

        self.assertIn("external_id", identity_columns)
        self.assertIn("account_type", user_columns)
        self.assertEqual(("telegram", "123", "123"), identity)


if __name__ == "__main__":
    unittest.main()
