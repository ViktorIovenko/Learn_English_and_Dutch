from __future__ import annotations

import secrets
import sqlite3
import time
from contextlib import closing
from typing import Any


PAIRING_CODE_TTL_SECONDS = 10 * 60
MAX_PARENTS_PER_CHILD = 5


def _connect(db_path: str) -> sqlite3.Connection:
    from app.content_db import connect
    conn = connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _is_effectively_child(conn: sqlite3.Connection, user_id: str, account_type: str | None) -> bool:
    """True if account_type says 'child', or the user is already linked as a
    child under a parent — mirrors the override in routes.py's
    _account_context(), which treats an existing link as authoritative over a
    possibly stale users.account_type column (missing row, bad migration, etc.).
    """
    if account_type == "child":
        return True
    return bool(conn.execute(
        "SELECT 1 FROM parent_child_links WHERE child_user_id=?",
        (str(user_id),),
    ).fetchone())


def ensure_pairing_code_schema(db_path: str) -> None:
    with closing(_connect(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS family_pairing_codes (
                code TEXT PRIMARY KEY,
                child_user_id TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (child_user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_family_pairing_codes_child
            ON family_pairing_codes(child_user_id)
        """)
        from app.family_invites import ensure_invitation_schema
        ensure_invitation_schema(conn)
        conn.commit()


def create_pairing_code(
    db_path: str,
    child_user_id: str | int,
    ttl_seconds: int = PAIRING_CODE_TTL_SECONDS,
) -> str:
    ensure_pairing_code_schema(db_path)
    child_id = str(child_user_id)
    now = int(time.time())
    with closing(_connect(db_path)) as conn:
        child = conn.execute(
            "SELECT account_type FROM users WHERE user_id=?",
            (child_id,),
        ).fetchone()
        if not child or not _is_effectively_child(conn, child_id, child["account_type"]):
            raise ValueError("child_account_required")
        conn.execute(
            "DELETE FROM family_pairing_codes WHERE expires_at < ?",
            (now,),
        )
        while True:
            code = secrets.token_urlsafe(18)
            try:
                conn.execute(
                    """
                    INSERT INTO family_pairing_codes (
                        code, child_user_id, expires_at, created_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (code, child_id, now + max(60, int(ttl_seconds)), now),
                )
                break
            except sqlite3.IntegrityError:
                continue
        conn.commit()
    return code


def ensure_invite_code_schema(db_path: str) -> None:
    with closing(_connect(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS family_invite_codes (
                code TEXT PRIMARY KEY,
                parent_user_id TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (parent_user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_family_invite_codes_parent
            ON family_invite_codes(parent_user_id)
        """)
        from app.family_invites import ensure_invitation_schema
        ensure_invitation_schema(conn)
        conn.commit()


def create_invite_code(
    db_path: str,
    parent_user_id: str | int,
    ttl_seconds: int = PAIRING_CODE_TTL_SECONDS,
) -> str:
    """Reverse of create_pairing_code: a standard (parent) account invites a child."""
    ensure_invite_code_schema(db_path)
    parent_id = str(parent_user_id)
    now = int(time.time())
    with closing(_connect(db_path)) as conn:
        parent = conn.execute(
            "SELECT account_type FROM users WHERE user_id=?",
            (parent_id,),
        ).fetchone()
        if not parent or parent["account_type"] != "standard":
            raise ValueError("parent_account_required")
        conn.execute(
            "DELETE FROM family_invite_codes WHERE expires_at < ?",
            (now,),
        )
        while True:
            code = secrets.token_urlsafe(18)
            try:
                conn.execute(
                    """
                    INSERT INTO family_invite_codes (
                        code, parent_user_id, expires_at, created_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (code, parent_id, now + max(60, int(ttl_seconds)), now),
                )
                break
            except sqlite3.IntegrityError:
                continue
        conn.commit()
    return code


def invite_code_details(db_path: str, code: str) -> dict[str, Any] | None:
    ensure_invite_code_schema(db_path)
    now = int(time.time())
    with closing(_connect(db_path)) as conn:
        row = conn.execute("""
            SELECT
                ic.parent_user_id,
                ic.expires_at,
                u.username,
                u.first_name,
                u.last_name,
                u.account_type
            FROM family_invite_codes ic
            JOIN users u ON u.user_id = ic.parent_user_id
            WHERE ic.code=? AND ic.expires_at>=?
        """, (str(code), now)).fetchone()
        if not row or row["account_type"] != "standard":
            conn.execute("DELETE FROM family_invite_codes WHERE expires_at < ?", (now,))
            conn.commit()
            return None
    parent_id = str(row["parent_user_id"])
    display_name = " ".join(
        part for part in (row["first_name"], row["last_name"]) if part
    ).strip() or (f"@{row['username']}" if row["username"] else parent_id)
    return {
        "parent_user_id": parent_id,
        "parent_display_name": display_name,
        "expires_at": int(row["expires_at"]),
    }


def link_child_with_invite_code(
    db_path: str,
    child_user_id: str | int,
    code: str,
) -> dict[str, Any]:
    """Reverse of link_parent_with_pairing_code: a child accepts a parent's invite."""
    ensure_invite_code_schema(db_path)
    child_id = str(child_user_id)
    now = int(time.time())
    with closing(_connect(db_path)) as conn:
        conn.execute("BEGIN IMMEDIATE")
        child = conn.execute(
            "SELECT account_type FROM users WHERE user_id=?",
            (child_id,),
        ).fetchone()
        if not child:
            return {"ok": False, "error": "child_account_not_found"}
        if child["account_type"] == "pending":
            return {"ok": False, "error": "account_type_required"}
        if not _is_effectively_child(conn, child_id, child["account_type"]):
            return {"ok": False, "error": "parent_cannot_be_child"}

        used = conn.execute("SELECT user_id FROM family_invitation_uses WHERE code=? AND kind=?", (str(code), "invite")).fetchone()
        if used and used[0] != child_id:
            return {"ok": False, "error": "invalid_or_expired_pairing_code"}

        invite = conn.execute(
            """
            SELECT parent_user_id
            FROM family_invite_codes
            WHERE code=? AND expires_at>=?
            """,
            (str(code), now),
        ).fetchone()
        if not invite:
            conn.execute("DELETE FROM family_invite_codes WHERE expires_at < ?", (now,))
            conn.commit()
            return {"ok": False, "error": "invalid_or_expired_pairing_code"}

        parent_id = str(invite["parent_user_id"])
        if parent_id == child_id:
            return {"ok": False, "error": "cannot_link_self"}
        parent = conn.execute(
            """
            SELECT user_id, username, first_name, last_name, account_type
            FROM users WHERE user_id=?
            """,
            (parent_id,),
        ).fetchone()
        if not parent or parent["account_type"] != "standard":
            return {"ok": False, "error": "parent_account_not_found"}

        existing = conn.execute(
            """
            SELECT 1 FROM parent_child_links
            WHERE parent_user_id=? AND child_user_id=?
            """,
            (parent_id, child_id),
        ).fetchone()
        if used and not existing:
            return {"ok": False, "error": "invalid_or_expired_pairing_code"}
        parents_count = int(conn.execute(
            "SELECT COUNT(*) FROM parent_child_links WHERE child_user_id=?",
            (child_id,),
        ).fetchone()[0])
        if not existing and parents_count >= MAX_PARENTS_PER_CHILD:
            return {"ok": False, "error": "parent_limit_reached"}

        conn.execute("""
            INSERT INTO parent_child_links (parent_user_id, child_user_id)
            VALUES (?, ?)
            ON CONFLICT(parent_user_id, child_user_id) DO NOTHING
        """, (parent_id, child_id))
        conn.execute("INSERT OR IGNORE INTO family_invitation_uses VALUES (?, ?, ?)", (str(code), "invite", child_id))
        conn.commit()
        display_name = " ".join(
            part for part in (parent["first_name"], parent["last_name"]) if part
        ).strip() or (f"@{parent['username']}" if parent["username"] else parent_id)
        return {
            "ok": True,
            "parent_user_id": parent_id,
            "parent_display_name": display_name,
        }


def linked_parents(db_path: str, child_user_id: str | int) -> list[dict[str, str]]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute("""
            SELECT u.user_id, u.username, u.first_name, u.last_name
            FROM parent_child_links l
            JOIN users u ON u.user_id = l.parent_user_id
            WHERE l.child_user_id=?
            ORDER BY COALESCE(u.first_name, ''), COALESCE(u.username, ''), u.user_id
        """, (str(child_user_id),)).fetchall()
    result: list[dict[str, str]] = []
    for row in rows:
        name = " ".join(
            part for part in (row["first_name"], row["last_name"]) if part
        ).strip() or (f"@{row['username']}" if row["username"] else str(row["user_id"]))
        result.append({"user_id": str(row["user_id"]), "display_name": name})
    return result


def linked_children(db_path: str, parent_user_id: str | int) -> list[dict[str, str]]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute("""
            SELECT u.user_id, u.username, u.first_name, u.last_name
            FROM parent_child_links l
            JOIN users u ON u.user_id = l.child_user_id
            WHERE l.parent_user_id=?
            ORDER BY COALESCE(u.first_name, ''), COALESCE(u.username, ''), u.user_id
        """, (str(parent_user_id),)).fetchall()
    result: list[dict[str, str]] = []
    for row in rows:
        name = " ".join(
            part for part in (row["first_name"], row["last_name"]) if part
        ).strip() or (f"@{row['username']}" if row["username"] else str(row["user_id"]))
        result.append({"user_id": str(row["user_id"]), "display_name": name})
    return result


def pairing_code_details(db_path: str, code: str) -> dict[str, Any] | None:
    ensure_pairing_code_schema(db_path)
    now = int(time.time())
    with closing(_connect(db_path)) as conn:
        row = conn.execute("""
            SELECT
                pc.child_user_id,
                pc.expires_at,
                u.username,
                u.first_name,
                u.last_name,
                u.account_type
            FROM family_pairing_codes pc
            JOIN users u ON u.user_id = pc.child_user_id
            WHERE pc.code=? AND pc.expires_at>=?
        """, (str(code), now)).fetchone()
        if not row or not _is_effectively_child(conn, row["child_user_id"], row["account_type"]):
            conn.execute("DELETE FROM family_pairing_codes WHERE expires_at < ?", (now,))
            conn.commit()
            return None
    child_id = str(row["child_user_id"])
    display_name = " ".join(
        part for part in (row["first_name"], row["last_name"]) if part
    ).strip() or (f"@{row['username']}" if row["username"] else child_id)
    return {
        "child_user_id": child_id,
        "child_display_name": display_name,
        "expires_at": int(row["expires_at"]),
    }


def link_parent_with_pairing_code(
    db_path: str,
    parent_user_id: str | int,
    code: str,
) -> dict[str, Any]:
    ensure_pairing_code_schema(db_path)
    parent_id = str(parent_user_id)
    now = int(time.time())
    with closing(_connect(db_path)) as conn:
        conn.execute("BEGIN IMMEDIATE")
        parent = conn.execute(
            "SELECT account_type FROM users WHERE user_id=?",
            (parent_id,),
        ).fetchone()
        if not parent:
            return {"ok": False, "error": "parent_account_not_found"}
        if parent["account_type"] == "pending":
            return {"ok": False, "error": "account_type_required"}
        if parent["account_type"] != "standard":
            return {"ok": False, "error": "child_cannot_be_parent"}

        used = conn.execute("SELECT user_id FROM family_invitation_uses WHERE code=? AND kind=?", (str(code), "family")).fetchone()
        if used and used[0] != parent_id:
            return {"ok": False, "error": "invalid_or_expired_pairing_code"}

        pairing = conn.execute(
            """
            SELECT child_user_id
            FROM family_pairing_codes
            WHERE code=? AND expires_at>=?
            """,
            (str(code), now),
        ).fetchone()
        if not pairing:
            conn.execute("DELETE FROM family_pairing_codes WHERE expires_at < ?", (now,))
            conn.commit()
            return {"ok": False, "error": "invalid_or_expired_pairing_code"}

        child_id = str(pairing["child_user_id"])
        if child_id == parent_id:
            return {"ok": False, "error": "cannot_link_self"}
        child = conn.execute(
            """
            SELECT user_id, username, first_name, last_name, account_type
            FROM users WHERE user_id=?
            """,
            (child_id,),
        ).fetchone()
        if not child or not _is_effectively_child(conn, child_id, child["account_type"]):
            return {"ok": False, "error": "child_account_not_found"}

        existing = conn.execute(
            """
            SELECT 1 FROM parent_child_links
            WHERE parent_user_id=? AND child_user_id=?
            """,
            (parent_id, child_id),
        ).fetchone()
        if used and not existing:
            return {"ok": False, "error": "invalid_or_expired_pairing_code"}
        parents_count = int(conn.execute(
            "SELECT COUNT(*) FROM parent_child_links WHERE child_user_id=?",
            (child_id,),
        ).fetchone()[0])
        if not existing and parents_count >= MAX_PARENTS_PER_CHILD:
            return {"ok": False, "error": "parent_limit_reached"}

        conn.execute("""
            INSERT INTO parent_child_links (parent_user_id, child_user_id)
            VALUES (?, ?)
            ON CONFLICT(parent_user_id, child_user_id) DO NOTHING
        """, (parent_id, child_id))
        conn.execute("INSERT OR IGNORE INTO family_invitation_uses VALUES (?, ?, ?)", (str(code), "family", parent_id))
        conn.commit()
        display_name = " ".join(
            part for part in (child["first_name"], child["last_name"]) if part
        ).strip() or (f"@{child['username']}" if child["username"] else child_id)
        return {
            "ok": True,
            "child_user_id": child_id,
            "child_display_name": display_name,
        }
