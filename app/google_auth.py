# app/google_auth.py
# Google OAuth 2.0 — web flow (authlib) + Android ID-token verify
#
# Web flow:  GET /auth/google  →  Google  →  GET /auth/google/callback
# Android:   POST /api/auth/google/verify   { "id_token": "..." }
#
# GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env.
# Authorized redirect URI to register in Google Cloud Console:
#   https://<your-domain>/auth/google/callback

import json
import sqlite3
import logging
from urllib.parse import urlparse
from flask import (
    Blueprint, redirect, url_for, session,
    request, jsonify, current_app, Response,
)
from authlib.integrations.flask_client import OAuth
from config import Config

log = logging.getLogger(__name__)

google_bp = Blueprint("google_auth", __name__)
_oauth = OAuth()


def ensure_google_auth_schema() -> None:
    with sqlite3.connect(Config.DB_PATH) as conn:
        columns = {
            str(row[1]) for row in conn.execute("PRAGMA table_info(users)")
        }
        if "auth_provider" not in columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'telegram'"
            )
        if "google_id" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
        if "google_email" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN google_email TEXT")
        if "photo_url" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN photo_url TEXT")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS u_users_google_id "
            "ON users(google_id) WHERE google_id IS NOT NULL"
        )
        conn.execute("""
            UPDATE OR IGNORE users
            SET auth_provider='google',
                google_id=(
                    SELECT external_id FROM auth_identities
                    WHERE provider='google' AND user_id=users.user_id LIMIT 1
                ),
                google_email=(
                    SELECT email FROM auth_identities
                    WHERE provider='google' AND user_id=users.user_id LIMIT 1
                )
            WHERE EXISTS (
                SELECT 1 FROM auth_identities
                WHERE provider='google' AND user_id=users.user_id
            )
        """)


def _safe_next_url(value: str | None, default: str = "/upload") -> str:
    target = str(value or "").strip()
    return target if target.startswith("/") and not target.startswith("//") else default


def _origin_from_referrer(referrer: str | None) -> str | None:
    """Extract "scheme://host" from a Referer header value, if present."""
    if not referrer:
        return None
    try:
        parsed = urlparse(referrer)
    except ValueError:
        return None
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return None


def _popup_close_response(ok: bool, next_url: str = "/upload", error: str = "", target_origin: str | None = None) -> Response:
    """A tiny self-closing page used to finish a Google sign-in popup.

    The opener can be the marketing site (parallellingvo.app) or this app's
    own origin (app.parallellingvo.app) depending on where the popup was
    launched from — they are NOT the same origin, so postMessage's
    targetOrigin must be the opener's own origin, not this popup's.

    `target_origin` should be captured server-side from the Referer header
    when the popup was first opened (see login() below) — NOT re-derived
    from document.referrer here. By the time this page runs, the popup has
    bounced through accounts.google.com and back, so document.referrer
    reflects that last hop, not the original opener; postMessage to the
    wrong origin is silently dropped by the browser, which left the
    opener's UI stuck on "Sign up" after a successful login until the page
    was manually reloaded.
    """
    payload = json.dumps({
        "source": "parallellingvo-auth",
        "provider": "google",
        "ok": ok,
        "next": next_url,
        "error": error,
    })
    target_origin_json = json.dumps(target_origin) if target_origin else "null"
    html = f"""<!doctype html><html><body>
<script>
  (function() {{
    try {{
      if (window.opener) {{
        var targetOrigin = {target_origin_json} ||
          (document.referrer ? new URL(document.referrer).origin : window.location.origin);
        window.opener.postMessage({payload}, targetOrigin);
      }}
    }} catch (e) {{}}
    window.close();
  }})();
</script>
</body></html>"""
    return Response(html, mimetype="text/html")


def init_google_oauth(app):
    """Call once from init_app(). No-op if credentials are missing."""
    ensure_google_auth_schema()
    if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
        log.warning("GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not set — Google auth disabled")
        return
    _oauth.init_app(app)
    _oauth.register(
        name="google",
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


# ── helpers ──────────────────────────────────────────────────────────────────

def _find_or_create_google_user(google_id: str, email: str, name: str, photo_url: str = "") -> str | None:
    """Return user_id (string) for a Google user, creating the record if new."""
    user_id = f"g_{google_id}"
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(users)")}
            if "photo_url" not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN photo_url TEXT")
            row = conn.execute(
                "SELECT user_id FROM auth_identities WHERE provider='google' AND external_id=?",
                (google_id,),
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE users SET google_email = ?, "
                    "photo_url = CASE WHEN ? <> '' THEN ? ELSE photo_url END "
                    "WHERE user_id = ?",
                    (email, photo_url, photo_url, row["user_id"]),
                )
                conn.execute(
                    "UPDATE auth_identities SET email=? WHERE provider='google' AND external_id=?",
                    (email, google_id),
                )
                conn.commit()
                return row["user_id"]

            # No auth_identities row for this google_id yet. Before creating a
            # brand-new g_<id> account, check whether this verified Google
            # email already belongs to an existing user — e.g. someone who
            # linked Google to their Telegram account from the web Settings
            # page (see _link_google_user below). Google itself verifies the
            # email, so matching on it here is safe and avoids silently
            # splitting one person into two disconnected accounts (their real
            # account keeps its admin/subscription state instead of landing
            # on a fresh 'pending' account with none).
            if email:
                existing = conn.execute(
                    "SELECT user_id FROM users WHERE lower(google_email) = lower(?) "
                    "ORDER BY (user_id LIKE 'g\\_%' ESCAPE '\\') ASC, created_at ASC LIMIT 1",
                    (email,),
                ).fetchone()
                if existing:
                    matched_user_id = str(existing["user_id"])
                    conn.execute(
                        "INSERT INTO auth_identities (provider, external_id, user_id, email) "
                        "VALUES ('google', ?, ?, ?) "
                        "ON CONFLICT(provider, external_id) DO UPDATE SET "
                        "user_id=excluded.user_id, email=excluded.email",
                        (google_id, matched_user_id, email),
                    )
                    conn.execute(
                        "UPDATE users SET google_id = ?, google_email = ?, "
                        "photo_url = CASE WHEN ? <> '' THEN ? ELSE photo_url END "
                        "WHERE user_id = ?",
                        (google_id, email, photo_url, photo_url, matched_user_id),
                    )
                    conn.commit()
                    log.info("Google login matched existing account by email: %s -> %s", email, matched_user_id)
                    return matched_user_id

            # New user — insert
            first_name = name.split()[0] if name else email
            last_name = " ".join(name.split()[1:]) if name and " " in name else ""
            conn.execute(
                """
                INSERT INTO users
                    (user_id, username, first_name, last_name, is_active,
                     auth_provider, google_id, google_email, account_type, photo_url)
                VALUES (?, ?, ?, ?, 1, 'google', ?, ?, 'pending', ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    google_id      = excluded.google_id,
                    google_email   = excluded.google_email,
                    auth_provider  = 'google',
                    is_active      = 1,
                    photo_url      = CASE WHEN excluded.photo_url <> '' THEN excluded.photo_url ELSE photo_url END
                """,
                (user_id, email, first_name, last_name, google_id, email, photo_url),
            )
            conn.execute(
                "INSERT INTO auth_identities (provider, external_id, user_id, email) VALUES ('google', ?, ?, ?)",
                (google_id, user_id, email),
            )
            conn.commit()
            log.info("New Google user created: %s (%s)", user_id, email)
            return user_id
        finally:
            conn.close()
    except Exception:
        log.exception("Failed to find/create Google user %s", google_id)
        return None


def _link_google_user(user_id: str, google_id: str, email: str) -> str:
    """Link Google to an existing user without changing the user's identity."""
    try:
        with sqlite3.connect(Config.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            owner = conn.execute(
                "SELECT user_id FROM auth_identities WHERE provider='google' AND external_id=?", (google_id,)
            ).fetchone()
            if owner and str(owner["user_id"]) != str(user_id):
                source_user_id = str(owner["user_id"])
                source = conn.execute(
                    "SELECT auth_provider FROM users WHERE user_id=?", (source_user_id,)
                ).fetchone()
                source_has_telegram = conn.execute(
                    "SELECT 1 FROM auth_identities WHERE provider='telegram' AND user_id=?",
                    (source_user_id,),
                ).fetchone()
                if (
                    not source
                    or str(source["auth_provider"] or "") != "google"
                    or source_has_telegram
                ):
                    return "conflict"

                ignored_tables = {"auth_identities", "user_subscriptions", "users"}
                for table_row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ):
                    table = str(table_row["name"])
                    if table in ignored_tables:
                        continue
                    columns = {
                        str(column[1])
                        for column in conn.execute(f'PRAGMA table_info("{table}")')
                    }
                    if "user_id" not in columns:
                        continue
                    quoted_table = table.replace('"', '""')
                    if conn.execute(
                        f'SELECT 1 FROM "{quoted_table}" WHERE user_id=? LIMIT 1',
                        (source_user_id,),
                    ).fetchone():
                        return "conflict"

                target_subscription = conn.execute(
                    "SELECT 1 FROM user_subscriptions WHERE user_id=?", (str(user_id),)
                ).fetchone()
                if target_subscription:
                    conn.execute(
                        "DELETE FROM user_subscriptions WHERE user_id=?", (source_user_id,)
                    )
                else:
                    conn.execute(
                        "UPDATE user_subscriptions SET user_id=? WHERE user_id=?",
                        (str(user_id), source_user_id),
                    )
                conn.execute(
                    "UPDATE users SET google_id=NULL, google_email=NULL WHERE user_id=?",
                    (source_user_id,),
                )
                conn.execute(
                    "UPDATE auth_identities SET user_id=?, email=? "
                    "WHERE provider='google' AND external_id=?",
                    (str(user_id), email, google_id),
                )
                conn.execute("DELETE FROM users WHERE user_id=?", (source_user_id,))
            user = conn.execute(
                "SELECT user_id FROM users WHERE user_id = ?", (str(user_id),)
            ).fetchone()
            if not user:
                return "user_not_found"
            conn.execute(
                "UPDATE users SET google_id = ?, google_email = ? WHERE user_id = ?",
                (google_id, email, str(user_id)),
            )
            conn.execute(
                "INSERT INTO auth_identities (provider, external_id, user_id, email) "
                "VALUES ('google', ?, ?, ?) "
                "ON CONFLICT(provider, external_id) DO UPDATE SET "
                "user_id=excluded.user_id, email=excluded.email",
                (google_id, str(user_id), email),
            )
            conn.commit()
        return "linked"
    except sqlite3.IntegrityError:
        return "conflict"
    except Exception:
        log.exception("Failed to link Google account to user %s", user_id)
        return "error"


def _set_google_session(user_id: str, email: str, name: str) -> None:
    session["tg_user_id"] = user_id
    session["tg_username"] = email
    session["tg_first_name"] = name.split()[0] if name else email
    session["tg_last_name"] = " ".join(name.split()[1:]) if name and " " in name else ""
    session["is_auth"] = True
    session["auth_provider"] = "google"


# ── web OAuth routes ──────────────────────────────────────────────────────────

@google_bp.get("/auth/google")
def login():
    if not Config.GOOGLE_CLIENT_ID:
        return "Google auth not configured", 501
    next_url = _safe_next_url(request.args.get("next"))
    session["google_next"] = next_url
    session["google_popup"] = request.args.get("popup") == "1"
    session["google_popup_origin"] = _origin_from_referrer(request.referrer)
    if request.args.get("mode") == "link":
        user_id = str(session.get("tg_user_id") or "").strip()
        if not session.get("is_auth") or not user_id:
            return redirect("/upload?error=google_link_auth_required")
        session["google_mode"] = "link"
        session["google_link_user_id"] = user_id
    else:
        session.pop("google_mode", None)
        session.pop("google_link_user_id", None)
    redirect_uri = f"{Config.APP_BASE_URL.rstrip('/')}/auth/google/callback"
    return _oauth.google.authorize_redirect(redirect_uri)


@google_bp.get("/auth/google/callback")
def callback():
    popup = bool(session.pop("google_popup", False))
    popup_origin = session.pop("google_popup_origin", None)
    if not Config.GOOGLE_CLIENT_ID:
        if popup:
            return _popup_close_response(False, error="google_auth_disabled", target_origin=popup_origin)
        return redirect("/upload?error=google_auth_disabled")
    try:
        token = _oauth.google.authorize_access_token()
        user_info = token.get("userinfo") or {}
    except Exception:
        log.exception("Google OAuth callback error")
        if popup:
            return _popup_close_response(False, error="google_auth_failed", target_origin=popup_origin)
        return redirect("/upload?error=google_auth_failed")

    google_id = user_info.get("sub", "")
    email = user_info.get("email", "")
    name = user_info.get("name", "")
    picture = user_info.get("picture", "")

    if not google_id:
        if popup:
            return _popup_close_response(False, error="google_no_sub", target_origin=popup_origin)
        return redirect("/upload?error=google_no_sub")

    mode = session.pop("google_mode", "")
    link_user_id = str(session.pop("google_link_user_id", "") or "").strip()
    next_url = _safe_next_url(session.pop("google_next", "/upload"))
    if mode == "link":
        current_user_id = str(session.get("tg_user_id") or "").strip()
        if not session.get("is_auth") or not link_user_id or current_user_id != link_user_id:
            return redirect("/upload?tab=mcp&google_link=auth_required")
        result = _link_google_user(link_user_id, google_id, email)
        separator = "&" if "?" in next_url else "?"
        return redirect(f"{next_url}{separator}google_link={result}")

    user_id = _find_or_create_google_user(google_id, email, name, picture)
    if not user_id:
        if popup:
            return _popup_close_response(False, next_url=next_url, error="google_db_error", target_origin=popup_origin)
        return redirect("/upload?error=google_db_error")

    _set_google_session(user_id, email, name)
    if popup:
        return _popup_close_response(True, next_url=next_url, target_origin=popup_origin)
    return redirect(next_url)


# ── Android: verify ID token ──────────────────────────────────────────────────

@google_bp.get("/api/auth/google/config")
def android_google_config():
    """Return the public OAuth audience needed by Android Google Sign-In."""
    if not Config.GOOGLE_CLIENT_ID:
        return jsonify({"ok": False, "error": "google_auth_not_configured"}), 501
    return jsonify({"ok": True, "client_id": Config.GOOGLE_CLIENT_ID})


@google_bp.post("/api/auth/google/verify")
def verify_android_token():
    """
    Android sends:  { "id_token": "<JWT from Google Sign-In SDK>" }
    Returns:        { "ok": true, "user_id": "g_<sub>", "email": ..., "name": ... }
    """
    if not Config.GOOGLE_CLIENT_ID:
        return jsonify({"ok": False, "error": "google_auth_not_configured"}), 501

    data = request.get_json(silent=True) or {}
    id_token_str = (data.get("id_token") or "").strip()
    if not id_token_str:
        return jsonify({"ok": False, "error": "id_token_required"}), 400

    try:
        from google.oauth2 import id_token as _id_token
        from google.auth.transport import requests as _g_requests
        claims = _id_token.verify_oauth2_token(
            id_token_str,
            _g_requests.Request(),
            Config.GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        log.warning("Android Google token verification failed: %s", exc)
        return jsonify({"ok": False, "error": "invalid_token"}), 401

    google_id = claims.get("sub", "")
    email = claims.get("email", "")
    name = claims.get("name", "")
    picture = claims.get("picture", "")

    user_id = _find_or_create_google_user(google_id, email, name, picture)
    if not user_id:
        return jsonify({"ok": False, "error": "user_creation_failed"}), 500

    from app.auth_links import create_auth_token

    return jsonify({
        "ok": True,
        "user_id": user_id,
        "email": email,
        "name": name,
        "auth_provider": "google",
        "token": create_auth_token(user_id),
    })
