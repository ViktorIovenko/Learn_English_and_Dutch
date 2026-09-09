from __future__ import annotations

import secrets
import sqlite3
import uuid
from typing import Any

from authlib.integrations.flask_client import OAuth
from authlib.integrations.base_client.errors import OAuthError
from flask import Blueprint, current_app, jsonify, redirect, request, session, url_for

from config import Config


auth = Blueprint("auth", __name__, url_prefix="/auth")
oauth = OAuth()


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_auth_schema() -> None:
    """Create provider identities without changing the existing users table."""
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_identities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                subject TEXT NOT NULL,
                provider_user_id TEXT,
                email TEXT,
                email_verified INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider, subject)
            );
            """
        )
        c.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_auth_identities_user
            ON auth_identities(user_id);
            """
        )
        c.commit()


def _user_exists(user_id: str) -> bool:
    with _conn() as c:
        return bool(c.execute("SELECT 1 FROM users WHERE user_id=?", (str(user_id),)).fetchone())


def _upsert_user(user_id: str, claims: dict[str, Any]) -> None:
    username = str(claims.get("preferred_username") or "").strip()
    first_name = str(claims.get("given_name") or "").strip()
    last_name = str(claims.get("family_name") or "").strip()

    # Some providers only return a single display name.
    if not first_name:
        display_name = str(claims.get("name") or "").strip()
        if display_name:
            first_name = display_name

    with _conn() as c:
        c.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, is_active)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                username=CASE WHEN excluded.username<>'' THEN excluded.username ELSE users.username END,
                first_name=CASE WHEN excluded.first_name<>'' THEN excluded.first_name ELSE users.first_name END,
                last_name=CASE WHEN excluded.last_name<>'' THEN excluded.last_name ELSE users.last_name END,
                is_active=1
            """,
            (str(user_id), username, first_name, last_name),
        )
        c.commit()


def _identity_user(provider: str, subject: str) -> str | None:
    with _conn() as c:
        row = c.execute(
            "SELECT user_id FROM auth_identities WHERE provider=? AND subject=?",
            (provider, subject),
        ).fetchone()
    return str(row["user_id"]) if row else None


def _insert_identity(user_id: str, provider: str, subject: str, claims: dict[str, Any]) -> str:
    provider_user_id = str(claims.get("id") or claims.get("sub") or "")
    email = str(claims.get("email") or "").strip()
    email_verified = 1 if bool(claims.get("email_verified")) else 0

    try:
        with _conn() as c:
            c.execute(
                """
                INSERT INTO auth_identities
                    (user_id, provider, subject, provider_user_id, email, email_verified)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, provider, subject, provider_user_id, email, email_verified),
            )
            c.commit()
        return user_id
    except sqlite3.IntegrityError:
        # A simultaneous login may have created the identity first.
        existing = _identity_user(provider, subject)
        if existing:
            return existing
        raise


def _touch_identity(provider: str, subject: str, claims: dict[str, Any]) -> None:
    provider_user_id = str(claims.get("id") or claims.get("sub") or "")
    email = str(claims.get("email") or "").strip()
    email_verified = 1 if bool(claims.get("email_verified")) else 0
    with _conn() as c:
        c.execute(
            """
            UPDATE auth_identities
            SET provider_user_id=?, email=?, email_verified=?, last_login_at=CURRENT_TIMESTAMP
            WHERE provider=? AND subject=?
            """,
            (provider_user_id, email, email_verified, provider, subject),
        )
        c.commit()


def _resolve_account(provider: str, claims: dict[str, Any]) -> str:
    subject = str(claims.get("sub") or "").strip()
    if not subject:
        raise ValueError(f"{provider} did not return an OIDC subject")

    existing = _identity_user(provider, subject)
    if existing:
        _upsert_user(existing, claims)
        _touch_identity(provider, subject, claims)
        return existing

    # If a logged-in user explicitly starts another provider flow, link the
    # new identity to the current ParallelLingvo account instead of creating a duplicate.
    current_uid = str(session.get("user_id") or session.get("tg_user_id") or "").strip()
    if current_uid and _user_exists(current_uid):
        _upsert_user(current_uid, claims)
        return _insert_identity(current_uid, provider, subject, claims)

    if provider == "telegram":
        # Existing installations historically used Telegram's numeric user id as users.user_id.
        # Preserve that id so existing lessons/progress remain attached to the same account.
        telegram_id = str(claims.get("id") or "").strip()
        user_id = telegram_id if telegram_id else f"u_{uuid.uuid4().hex}"
    else:
        # New non-Telegram accounts get a provider-neutral internal id.
        user_id = f"u_{uuid.uuid4().hex}"

    _upsert_user(user_id, claims)
    return _insert_identity(user_id, provider, subject, claims)


def _login_session(user_id: str, provider: str) -> None:
    session.clear()
    session["user_id"] = str(user_id)

    # Temporary compatibility bridge: existing API helpers read tg_user_id first.
    # It contains the internal ParallelLingvo user id here, not necessarily a Telegram id.
    session["tg_user_id"] = str(user_id)
    session["auth_provider"] = provider
    session.permanent = True


def _safe_next_url(raw: str | None) -> str:
    app_base = str(current_app.config.get("APP_BASE_URL") or Config.APP_BASE_URL).rstrip("/")
    if not raw:
        return app_base + "/"

    value = str(raw).strip()
    if value.startswith("/") and not value.startswith("//"):
        return app_base + value
    if value == app_base or value.startswith(app_base + "/"):
        return value
    return app_base + "/"


def _provider_client(provider: str):
    client = oauth.create_client(provider)
    if client is None:
        return None
    return client


def _start_oidc(provider: str, callback_endpoint: str):
    client = _provider_client(provider)
    if client is None:
        return jsonify(
            {
                "ok": False,
                "error": f"{provider} login is not configured on the server yet",
            }
        ), 503

    nonce = secrets.token_urlsafe(32)
    session[f"oauth_nonce:{provider}"] = nonce
    session[f"oauth_next:{provider}"] = _safe_next_url(request.args.get("next"))
    redirect_uri = url_for(callback_endpoint, _external=True)
    return client.authorize_redirect(redirect_uri, nonce=nonce)


def _finish_oidc(provider: str):
    client = _provider_client(provider)
    if client is None:
        return jsonify({"ok": False, "error": f"{provider} login is not configured"}), 503

    nonce = session.pop(f"oauth_nonce:{provider}", None)
    next_url = session.pop(f"oauth_next:{provider}", None)

    try:
        token = client.authorize_access_token()
        claims = token.get("userinfo")
        if not claims:
            claims = client.parse_id_token(token, nonce=nonce)
        claims = dict(claims or {})
        user_id = _resolve_account(provider, claims)
    except OAuthError as exc:
        current_app.logger.warning("%s OAuth error: %s", provider, exc)
        return jsonify({"ok": False, "error": "OAuth login failed"}), 400
    except Exception:
        current_app.logger.exception("%s login callback failed", provider)
        return jsonify({"ok": False, "error": "Login callback failed"}), 400

    _login_session(user_id, provider)
    return redirect(_safe_next_url(next_url))


@auth.get("/google")
def google_login():
    return _start_oidc("google", "auth.google_callback")


@auth.get("/google/callback")
def google_callback():
    return _finish_oidc("google")


@auth.get("/telegram")
def telegram_login():
    username = str(Config.BOT_USERNAME or "").strip().lstrip("@")
    if not username:
        return jsonify({"ok": False, "error": "Telegram bot is not configured on the server yet"}), 503
    return redirect(f"https://t.me/{username}?startapp=login")


@auth.get("/telegram/callback")
def telegram_callback():
    return _finish_oidc("telegram")


@auth.get("/logout")
def logout():
    session.clear()
    site_base = str(current_app.config.get("SITE_BASE_URL") or Config.SITE_BASE_URL).rstrip("/")
    return redirect(site_base + "/")


@auth.get("/status")
def auth_status():
    user_id = str(session.get("user_id") or session.get("tg_user_id") or "").strip()
    return jsonify(
        {
            "ok": True,
            "authenticated": bool(user_id),
            "user_id": user_id or None,
            "provider": session.get("auth_provider"),
        }
    )


def init_app(app) -> None:
    ensure_auth_schema()

    # Authlib providers are only registered when credentials exist. This keeps
    # deployments bootable while BotFather/Google credentials are still being configured.
    oauth.init_app(app)

    if app.config.get("GOOGLE_CLIENT_ID") and app.config.get("GOOGLE_CLIENT_SECRET"):
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    if app.config.get("TELEGRAM_OIDC_CLIENT_ID") and app.config.get("TELEGRAM_OIDC_CLIENT_SECRET"):
        oauth.register(
            name="telegram",
            client_id=app.config["TELEGRAM_OIDC_CLIENT_ID"],
            client_secret=app.config["TELEGRAM_OIDC_CLIENT_SECRET"],
            server_metadata_url="https://oauth.telegram.org/.well-known/openid-configuration",
            client_kwargs={
                "scope": "openid profile",
                "code_challenge_method": "S256",
            },
        )

    @app.before_request
    def disable_legacy_user_header():
        # The previous browser client could choose its own X-User-Id via ?uid=.
        # Never trust that on the public application unless explicitly enabled for migration.
        if not app.config.get("ALLOW_LEGACY_UID_AUTH", False):
            request.environ.pop("HTTP_X_USER_ID", None)

    app.register_blueprint(auth)
