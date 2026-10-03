# app/telegram_oauth.py
# "Log in with Telegram" via Telegram's OAuth 2.0 / OIDC provider (oauth.telegram.org).
#
# This is Telegram's browser-based login (BotFather → Bot Settings → Web Login /
# "Login Widget", which issues a numeric Client ID + Client Secret and a redirect
# URI allowlist) — distinct from the Mini App initData flow in app/telegram_auth.py,
# which only works inside the Telegram client itself. Use this route for the plain
# website: parallellingvo.app and app.parallellingvo.app.
#
# Web flow:  GET /auth/telegram  →  oauth.telegram.org  →  GET /auth/telegram/callback
#
# TELEGRAM_OIDC_CLIENT_ID and TELEGRAM_OIDC_CLIENT_SECRET must be set in .env.
# Redirect URI to register in BotFather's Login Widget settings:
#   https://<your-domain>/auth/telegram/callback

import json
import logging
from urllib.parse import urlencode, urlparse
from flask import Blueprint, redirect, session, request, Response
from authlib.integrations.flask_client import OAuth
from app.auth_links import create_auth_token
from config import Config

log = logging.getLogger(__name__)

telegram_oauth_bp = Blueprint("telegram_oauth", __name__)
_oauth = OAuth()

# Telegram publishes standard OIDC discovery, so authlib can pull the
# authorization/token/jwks endpoints (and validate the id_token) automatically,
# the same way app/google_auth.py does for Google.
_DISCOVERY_URL = "https://oauth.telegram.org/.well-known/openid-configuration"


def init_telegram_oauth(app):
    """Call once from init_app(). No-op if credentials are missing."""
    if not Config.TELEGRAM_OIDC_CLIENT_ID or not Config.TELEGRAM_OIDC_CLIENT_SECRET:
        log.warning("TELEGRAM_OIDC_CLIENT_ID / TELEGRAM_OIDC_CLIENT_SECRET not set — Telegram web login disabled")
        return
    _oauth.init_app(app)
    _oauth.register(
        name="telegram",
        client_id=Config.TELEGRAM_OIDC_CLIENT_ID,
        client_secret=Config.TELEGRAM_OIDC_CLIENT_SECRET,
        server_metadata_url=_DISCOVERY_URL,
        client_kwargs={
            "scope": "openid profile",
            "code_challenge_method": "S256",
        },
    )


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


def _android_deep_link(token: str = "", error: str = "") -> str:
    """learnwords://auth?... — consumed by MainActivity.handleTelegramAuthIntent,
    the same deep link the bot's /android-auth link produces (see bot/auth.py)."""
    params = {"server": Config.PUBLIC_BASE_URL.rstrip("/")}
    if token:
        params["auth"] = token
    if error:
        params["error"] = error
    return "learnwords://auth?" + urlencode(params)


def _popup_close_response(ok: bool, next_url: str = "/upload", error: str = "", target_origin: str | None = None) -> Response:
    """A tiny self-closing page used to finish a Telegram sign-in popup.

    `target_origin` should be the opener's origin, captured server-side from
    the Referer header when the popup was first opened (see login() below).
    document.referrer is NOT reliable here as a fallback: by the time this
    page runs, the popup has bounced through oauth.telegram.org and back, so
    document.referrer reflects that last hop (oauth.telegram.org), not the
    original opener — postMessage to the wrong origin is silently dropped by
    the browser, which left the opener's UI stuck on "Sign up" after a
    successful login until the page was manually reloaded.
    """
    payload = json.dumps({
        "source": "parallellingvo-auth",
        "provider": "telegram",
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


@telegram_oauth_bp.get("/auth/telegram")
def login():
    if not Config.TELEGRAM_OIDC_CLIENT_ID:
        return "Telegram login is not configured", 501
    next_url = _safe_next_url(request.args.get("next"))
    session["telegram_next"] = next_url
    session["telegram_popup"] = request.args.get("popup") == "1"
    session["telegram_popup_origin"] = _origin_from_referrer(request.referrer)
    # Set by the Android app (Custom Tabs / browser Intent to this URL) so the
    # callback below can hand a token back to the app via the learnwords://auth
    # deep link instead of setting a browser session cookie.
    session["telegram_android"] = request.args.get("android") == "1"
    redirect_uri = f"{Config.APP_BASE_URL.rstrip('/')}/auth/telegram/callback"
    return _oauth.telegram.authorize_redirect(redirect_uri)


@telegram_oauth_bp.get("/auth/telegram/callback")
def callback():
    popup = bool(session.pop("telegram_popup", False))
    popup_origin = session.pop("telegram_popup_origin", None)
    next_url = _safe_next_url(session.pop("telegram_next", "/upload"))
    android = bool(session.pop("telegram_android", False))
    if not Config.TELEGRAM_OIDC_CLIENT_ID:
        if android:
            return redirect(_android_deep_link(error="telegram_auth_disabled"))
        if popup:
            return _popup_close_response(False, error="telegram_auth_disabled", target_origin=popup_origin)
        return redirect("/upload?error=telegram_auth_disabled")

    try:
        token = _oauth.telegram.authorize_access_token()
        claims = token.get("userinfo") or {}
    except Exception:
        log.exception("Telegram OAuth callback error")
        if android:
            return redirect(_android_deep_link(error="telegram_auth_failed"))
        if popup:
            return _popup_close_response(False, error="telegram_auth_failed", target_origin=popup_origin)
        return redirect("/upload?error=telegram_auth_failed")

    # claims["sub"] is a large pairwise/opaque OIDC subject identifier — NOT
    # the Telegram account. claims["id"] is the actual numeric Telegram user
    # id, the same one the bot/Mini App login path keys users.user_id by;
    # using "sub" here silently created a brand-new duplicate account on
    # every login instead of matching the visitor's existing account.
    telegram_id = str(claims.get("id") or "").strip()
    if not telegram_id:
        if android:
            return redirect(_android_deep_link(error="telegram_no_id"))
        if popup:
            return _popup_close_response(False, next_url=next_url, error="telegram_no_id", target_origin=popup_origin)
        return redirect("/upload?error=telegram_no_id")

    preferred_username = str(claims.get("preferred_username") or "").strip()
    given_name = str(claims.get("given_name") or "").strip()
    family_name = str(claims.get("family_name") or "").strip()
    if not given_name:
        full_name = str(claims.get("name") or "").strip()
        if full_name:
            parts = full_name.split()
            given_name = parts[0]
            family_name = " ".join(parts[1:])

    user = {
        "id": telegram_id,
        "username": preferred_username,
        "first_name": given_name,
        "last_name": family_name,
    }

    # Reused so a Telegram OAuth login creates/updates the exact same kind of
    # row as the Mini App / bot login path (app/routes.py login_webapp).
    from app.routes import _upsert_user, _has_telegram_identity, _notify_admins_new_user, _conn

    if not _has_telegram_identity(user):
        if android:
            return redirect(_android_deep_link(error="telegram_name_or_username_required"))
        error_url = f"{next_url}{'&' if '?' in next_url else '?'}error=telegram_name_or_username_required"
        if popup:
            return _popup_close_response(False, next_url=next_url, error="telegram_name_or_username_required", target_origin=popup_origin)
        return redirect(error_url)

    if _upsert_user(user):
        _notify_admins_new_user(user)

    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO auth_identities (provider, external_id, user_id) VALUES ('telegram', ?, ?)",
            (telegram_id, telegram_id),
        )
        c.commit()

    if android:
        return redirect(_android_deep_link(token=create_auth_token(telegram_id)))

    session["tg_user_id"] = telegram_id
    session["tg_username"] = preferred_username
    session["tg_first_name"] = given_name
    session["tg_last_name"] = family_name
    session["is_auth"] = True
    session["auth_provider"] = "telegram"

    if popup:
        return _popup_close_response(True, next_url=next_url, target_origin=popup_origin)
    return redirect(next_url)
