import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from config import Config
from bot import auth as bot_auth
from app.account_types import migrate_account_types
from app.family_pairing import (
    create_pairing_code,
    link_parent_with_pairing_code,
    linked_parents,
)


class AccountTypeMigrationTest(unittest.TestCase):
    def test_existing_pending_users_become_standard_only_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "accounts.db")
            with closing(sqlite3.connect(db_path)) as conn:
                conn.execute("""
                    CREATE TABLE users (
                        user_id TEXT PRIMARY KEY,
                        account_type TEXT
                    )
                """)
                conn.execute("INSERT INTO users VALUES ('existing', 'pending')")
                migrate_account_types(conn)
                self.assertEqual(
                    "standard",
                    conn.execute(
                        "SELECT account_type FROM users WHERE user_id='existing'"
                    ).fetchone()[0],
                )

                conn.execute("INSERT INTO users VALUES ('new', 'pending')")
                conn.execute("INSERT INTO users VALUES ('broken', '')")
                migrate_account_types(conn)
                rows = dict(conn.execute(
                    "SELECT user_id, account_type FROM users WHERE user_id IN ('new', 'broken')"
                ).fetchall())
                self.assertEqual("pending", rows["new"])
                self.assertEqual("standard", rows["broken"])


class TelegramFamilyPairingTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "family.db")
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    account_type TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE parent_child_links (
                    parent_user_id TEXT NOT NULL,
                    child_user_id TEXT NOT NULL,
                    PRIMARY KEY (parent_user_id, child_user_id)
                )
            """)
            conn.executemany(
                "INSERT INTO users VALUES (?, ?, ?, '', ?)",
                [
                    ("child", "child", "Kid", "child"),
                    ("parent", "parent", "Parent", "standard"),
                    ("other-child", "other", "Other", "child"),
                ],
            )
            conn.commit()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_short_telegram_code_links_regular_parent(self):
        code = create_pairing_code(self.db_path, "child")
        self.assertLessEqual(len("family_" + code), 64)

        result = link_parent_with_pairing_code(self.db_path, "parent", code)
        self.assertTrue(result["ok"])
        self.assertEqual("Kid", result["child_display_name"])
        with closing(sqlite3.connect(self.db_path)) as conn:
            link = conn.execute(
                "SELECT parent_user_id, child_user_id FROM parent_child_links"
            ).fetchone()
        self.assertEqual(("parent", "child"), link)
        self.assertEqual(
            [{"user_id": "parent", "display_name": "Parent"}],
            linked_parents(self.db_path, "child"),
        )

    def test_child_account_cannot_use_parent_link(self):
        code = create_pairing_code(self.db_path, "child")
        result = link_parent_with_pairing_code(self.db_path, "other-child", code)
        self.assertFalse(result["ok"])
        self.assertEqual("child_cannot_be_parent", result["error"])

    def test_expired_code_is_rejected(self):
        code = create_pairing_code(self.db_path, "child")
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                "UPDATE family_pairing_codes SET expires_at=0 WHERE code=?",
                (code,),
            )
            conn.commit()
        result = link_parent_with_pairing_code(self.db_path, "parent", code)
        self.assertFalse(result["ok"])
        self.assertEqual("invalid_or_expired_pairing_code", result["error"])

    def test_child_accepts_no_more_than_five_adults(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.executemany(
                "INSERT INTO users VALUES (?, ?, ?, '', 'standard')",
                [(f"parent-{index}", f"p{index}", f"Parent {index}") for index in range(1, 7)],
            )
            conn.commit()
        code = create_pairing_code(self.db_path, "child")
        first_code = code
        for index in range(1, 6):
            code = create_pairing_code(self.db_path, "child")
            if index == 1:
                first_code = code
            result = link_parent_with_pairing_code(
                self.db_path, f"parent-{index}", code
            )
            self.assertTrue(result["ok"])

        code = create_pairing_code(self.db_path, "child")
        rejected = link_parent_with_pairing_code(self.db_path, "parent-6", code)
        self.assertFalse(rejected["ok"])
        self.assertEqual("parent_limit_reached", rejected["error"])

        # Reopening the same link for an already connected adult is idempotent.
        repeated = link_parent_with_pairing_code(self.db_path, "parent-1", first_code)
        self.assertTrue(repeated["ok"])


class TelegramFamilyConfirmationTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "confirmation.db")
        self.original_db_path = Config.DB_PATH
        Config.DB_PATH = self.db_path
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    account_type TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE parent_child_links (
                    parent_user_id TEXT NOT NULL,
                    child_user_id TEXT NOT NULL,
                    PRIMARY KEY (parent_user_id, child_user_id)
                )
            """)
            conn.executemany(
                "INSERT INTO users VALUES (?, '', ?, '', ?)",
                [("child", "Kid", "child"), ("parent", "Parent", "standard")],
            )
            conn.commit()
        self.code = create_pairing_code(self.db_path, "child")
        self.user = SimpleNamespace(id="parent", language_code="en")
        self.chat = SimpleNamespace(send_message=AsyncMock())
        self.context = SimpleNamespace(
            user_data={"pending_family_code": self.code},
            args=[],
        )

    async def asyncTearDown(self):
        Config.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    async def test_link_is_created_only_after_confirmation_button(self):
        update = SimpleNamespace(
            effective_user=self.user,
            effective_chat=self.chat,
            callback_query=None,
        )
        shown = await bot_auth._show_pending_family_confirmation(update, self.context)
        self.assertTrue(shown)
        with closing(sqlite3.connect(self.db_path)) as conn:
            self.assertEqual(0, conn.execute(
                "SELECT COUNT(*) FROM parent_child_links"
            ).fetchone()[0])

        query = SimpleNamespace(
            data=f"family_link:confirm:{self.code}",
            answer=AsyncMock(),
            edit_message_text=AsyncMock(),
        )
        update.callback_query = query
        await bot_auth.family_link_callback(update, self.context)
        with closing(sqlite3.connect(self.db_path)) as conn:
            self.assertEqual(1, conn.execute(
                "SELECT COUNT(*) FROM parent_child_links"
            ).fetchone()[0])
        query.edit_message_text.assert_awaited()

    async def test_cancel_button_does_not_create_link(self):
        query = SimpleNamespace(
            data=f"family_link:cancel:{self.code}",
            answer=AsyncMock(),
            edit_message_text=AsyncMock(),
        )
        update = SimpleNamespace(
            effective_user=self.user,
            effective_chat=self.chat,
            callback_query=query,
        )
        await bot_auth.family_link_callback(update, self.context)
        with closing(sqlite3.connect(self.db_path)) as conn:
            self.assertEqual(0, conn.execute(
                "SELECT COUNT(*) FROM parent_child_links"
            ).fetchone()[0])


if __name__ == "__main__":
    unittest.main()
