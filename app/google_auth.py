# app/google_auth.py
# Google OAuth 2.0 — web flow (authlib) + Android ID-token verify
#
# Web flow:  GET /auth/google  →  Google  →  GET /auth/google/callback
# Android:   POST /api/auth/google/verify   { "id_token": "..." }
#
# GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env.
# Authorized redirect URI to register in Google Cloud Console:
#   https://<your-domain>/auth/google/callback

import sqlite3
import logging
from flask import (
    Blueprint, redirect, url_for, session,
    request, jsonify, current_app,
)
from authlib.integrations.flask_client import OAuth
from config import Config

log = logging.getLogger(__name__)

google_bp = Blueprint("google_auth", __name__)
_oauth = OAuth()


def init_google_oauth(app):
    """Call once from init_app(). No-op if credentials are missing."""
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

def _find_or_create_google_user(google_id: str, email: str, name: str) -> str | None:
    """Return user_id (string) for a Google user, creating the record if new."""
    user_id = f"g_{google_id}"
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            # Existing Google user?
            row = conn.execute(
                "SELECT user_id FROM users WHERE google_id = ?", (google_id,)
            ).fetchone()
            if row:
                return row["user_id"]
            # New user — insert
            first_name = name.split()[0] if name else email
            last_name = " ".join(name.split()[1:]) if name and " " in name else ""
            conn.execute(
                """
                INSERT INTO users
                    (user_id, username, first_name, last_name, is_active, auth_provider, google_id)
                VALUES (?, ?, ?, ?, 1, 'google', ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    google_id      = excluded.google_id,
                    auth_provider  = 'google',
                    is_active      = 1
                """,
                (user_id, email, first_name, last_name, google_id),
            )
            conn.commit()
            log.info("New Google user created: %s (%s)", user_id, email)
            return user_id
        finally:
            conn.close()
    except Exception:
        log.exception("Failed to find/create Google user %s", google_id)
        return None


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
    next_url = request.args.get("next", "/upload")
    session["google_next"] = next_url
    redirect_uri = url_for("google_auth.callback", _external=True)
    return _oauth.google.authorize_redirect(redirect_uri)


@google_bp.get("/auth/google/callback")
def callback():
    if not Config.GOOGLE_CLIENT_ID:
        return redirect("/upload?error=google_auth_disabled")
    try:
        token = _oauth.google.authorize_access_token()
        user_info = token.get("userinfo") or {}
    except Exception:
        log.exception("Google OAuth callback error")
        return redirect("/upload?error=google_auth_failed")

    google_id = user_info.get("sub", "")
    email = user_info.get("email", "")
    name = user_info.get("name", "")

    if not google_id:
        return redirect("/upload?error=google_no_sub")

    user_id = _find_or_create_google_user(google_id, email, name)
    if not user_id:
        return redirect("/upload?error=google_db_error")

    _set_google_session(user_id, email, name)
    next_url = session.pop("google_next", "/upload")
    return redirect(next_url)


# ── Android: verify ID token ──────────────────────────────────────────────────

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

    user_id = _find_or_create_google_user(google_id, email, name)
    if not user_id:
        return jsonify({"ok": False, "error": "user_creation_failed"}), 500

    return jsonify({
        "ok": True,
        "user_id": user_id,
        "email": email,
        "name": name,
        "auth_provider": "google",
    })
