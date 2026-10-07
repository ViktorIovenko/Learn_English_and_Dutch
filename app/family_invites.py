"""Platform-independent family invitation transport and replay protection."""
import secrets
import time
from contextlib import closing
from urllib.parse import parse_qs, urlencode, urlsplit

from config import Config
from app.family_pairing import (
    _connect, invite_code_details, pairing_code_details,
    link_child_with_invite_code, link_parent_with_pairing_code, _is_effectively_child,
)


def ensure_invitation_schema(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS family_invitation_aliases (
        short_code TEXT PRIMARY KEY, code TEXT NOT NULL, kind TEXT NOT NULL,
        expires_at INTEGER NOT NULL, UNIQUE(code, kind))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS family_invitation_uses (
        code TEXT NOT NULL, kind TEXT NOT NULL, user_id TEXT NOT NULL,
        PRIMARY KEY(code, kind))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS family_invitation_attempts (
        user_id TEXT PRIMARY KEY, window_start INTEGER NOT NULL, count INTEGER NOT NULL)""")


def invitation_payload(code, kind):
    details = (invite_code_details if kind == "invite" else pairing_code_details)(Config.DB_PATH, code)
    with closing(_connect(Config.DB_PATH)) as conn:
        ensure_invitation_schema(conn)
        conn.execute("DELETE FROM family_invitation_aliases WHERE expires_at < ?", (int(time.time()),))
        row = conn.execute("SELECT short_code FROM family_invitation_aliases WHERE code=? AND kind=?", (code, kind)).fetchone()
        if row:
            short_code = row[0]
        else:
            alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
            while True:
                short_code = "".join(secrets.choice(alphabet) for _ in range(10))
                if not conn.execute("SELECT 1 FROM family_invitation_aliases WHERE short_code=?", (short_code,)).fetchone():
                    break
            conn.execute("INSERT INTO family_invitation_aliases VALUES (?, ?, ?, ?)",
                         (short_code, code, kind, details["expires_at"]))
        conn.commit()
    base = Config.APP_BASE_URL.rstrip("/")
    return {"code": code, "kind": kind, "short_code": short_code,
            "url": base + "/family/connect?" + urlencode({"code": code, "kind": kind}),
            "expires_in": max(0, details["expires_at"] - int(time.time()))}


def resolve_invitation(value, kind=""):
    value = str(value or "").strip()
    kind = str(kind or "")
    if len(value) > 512:
        return "", ""
    if value.startswith("https://"):
        parsed = urlsplit(value)
        if parsed.hostname not in {urlsplit(Config.APP_BASE_URL).hostname, urlsplit(Config.PUBLIC_BASE_URL).hostname}:
            return "", ""
        query = parse_qs(parsed.query)
        value = query.get("code", [""])[0]
        kind = query.get("kind", [kind])[0]
    short = value.upper().replace("-", "").replace(" ", "")
    with closing(_connect(Config.DB_PATH)) as conn:
        ensure_invitation_schema(conn)
        row = conn.execute("SELECT code, kind FROM family_invitation_aliases WHERE short_code=? AND expires_at>=?",
                           (short, int(time.time()))).fetchone()
        conn.commit()
    if row:
        return row[0], row[1]
    return (value, kind) if kind in {"family", "invite"} else ("", "")


def allow_invitation_attempt(user_id):
    now = int(time.time())
    with closing(_connect(Config.DB_PATH)) as conn:
        ensure_invitation_schema(conn)
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("DELETE FROM family_invitation_attempts WHERE window_start < ?", (now - 600,))
        conn.execute("""INSERT INTO family_invitation_attempts VALUES (?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET count=count+1""", (str(user_id), now))
        count = conn.execute("SELECT count FROM family_invitation_attempts WHERE user_id=?", (str(user_id),)).fetchone()[0]
        conn.commit()
    return count <= 30


def preview_invitation(user_id, value, kind=""):
    code, kind = resolve_invitation(value, kind)
    if not code:
        return {"ok": False, "error": "invalid_or_expired_pairing_code"}
    details = (invite_code_details if kind == "invite" else pairing_code_details)(Config.DB_PATH, code)
    if not details:
        return {"ok": False, "error": "invalid_or_expired_pairing_code"}
    with closing(_connect(Config.DB_PATH)) as conn:
        used = conn.execute("SELECT user_id FROM family_invitation_uses WHERE code=? AND kind=?", (code, kind)).fetchone()
        if used and used[0] != str(user_id):
            return {"ok": False, "error": "invalid_or_expired_pairing_code"}
        user = conn.execute("SELECT account_type, first_name, username FROM users WHERE user_id=?", (str(user_id),)).fetchone()
        is_child = bool(user and _is_effectively_child(conn, user_id, user["account_type"]))
    required = "child" if kind == "invite" else "standard"
    if not user or (not is_child if required == "child" else user["account_type"] != "standard" or is_child):
        return {"ok": False, "error": "child_account_required" if kind == "invite" else "parent_account_required"}
    target = details["parent_user_id" if kind == "invite" else "child_user_id"]
    if target == str(user_id):
        return {"ok": False, "error": "cannot_link_self"}
    return {"ok": True, "code": code, "kind": kind,
            "display_name": details["parent_display_name" if kind == "invite" else "child_display_name"],
            "account_name": " · ".join(dict.fromkeys(part for part in (user["first_name"], user["username"]) if part)) or str(user_id)}


def accept_invitation(user_id, value, kind=""):
    preview = preview_invitation(user_id, value, kind)
    if not preview["ok"]:
        return preview
    linker = link_child_with_invite_code if preview["kind"] == "invite" else link_parent_with_pairing_code
    return linker(Config.DB_PATH, user_id, preview["code"])
