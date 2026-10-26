"""Cross-origin guard for /api/admin/*.

The admin UI is served by the main site (parallellingvo.app) while the data
and every admin operation stay in this Flask app. Browsers call
/api/admin/* from that site with the normal session cookie, so this module:

* answers CORS only for the exact origins in Config.ADMIN_SITE_ORIGINS
  (never "*"), and rejects any other foreign Origin outright;
* requires a JSON body for every state-changing request (cross-site forms
  cannot send one without a CORS preflight);
* requires the per-session admin CSRF token for cross-origin changes.

Admin rights themselves are still checked by each route (_require_admin /
_admin_viewer); this guard only decides which origins may talk to them.
"""
from __future__ import annotations

import secrets
from urllib.parse import urlsplit

from flask import Flask, current_app, g, jsonify, request, session

from config import Config

CSRF_SESSION_KEY = "admin_csrf"
CSRF_HEADER = "X-CSRF-Token"
_SAFE_METHODS = ("GET", "HEAD")


def allowed_origins() -> set[str]:
    return set(getattr(Config, "ADMIN_SITE_ORIGINS", ()) or ())


def csrf_token() -> str:
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def csrf_valid() -> bool:
    token = session.get(CSRF_SESSION_KEY) or ""
    supplied = request.headers.get(CSRF_HEADER) or ""
    return bool(token and supplied) and secrets.compare_digest(token, supplied)


def platform_token_ok() -> bool:
    configured = str(getattr(Config, "AI_PLATFORM_ADMIN_TOKEN", "") or "").strip()
    authorization = str(request.headers.get("Authorization") or "").strip()
    supplied = authorization[7:].strip() if authorization.lower().startswith("bearer ") else ""
    return bool(configured and supplied) and secrets.compare_digest(supplied, configured)


def _foreign_origin() -> str:
    """The request Origin when it is not this app's own host, else ""."""
    origin = request.headers.get("Origin")
    if not origin:
        return ""
    try:
        if urlsplit(origin).netloc == request.host:
            return ""
    except ValueError:
        pass
    return origin


def origin_verified() -> bool:
    """True when the guard accepted a cross-origin change (origin + CSRF)."""
    return bool(g.get("admin_origin_verified"))


def _deny(status: int, error: str):
    return jsonify({"ok": False, "error": error}), status


def _guard():
    if not request.path.startswith("/api/admin/"):
        return None
    origin = _foreign_origin()
    if origin and origin not in allowed_origins():
        return _deny(403, "origin_not_allowed")
    if request.method == "OPTIONS":
        if not origin:
            return None
        response = current_app.response_class(status=204)
        response.headers["Access-Control-Allow-Methods"] = "GET, POST"
        response.headers["Access-Control-Allow-Headers"] = f"Content-Type, {CSRF_HEADER}"
        response.headers["Access-Control-Max-Age"] = "600"
        return response
    if request.method in _SAFE_METHODS:
        return None
    if platform_token_ok():
        return None  # server-to-server, no browser cookies involved
    if not request.is_json:
        return _deny(400, "bad_request")
    if origin:
        if not csrf_valid():
            return _deny(403, "csrf_failed")
        g.admin_origin_verified = True
    return None


def _cors(response):
    if not request.path.startswith("/api/admin/"):
        return response
    response.headers["Cache-Control"] = "no-store"
    origin = _foreign_origin()
    if origin and origin in allowed_origins():
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers.add("Vary", "Origin")
    return response


def init_admin_api(app: Flask) -> None:
    app.before_request(_guard)
    app.after_request(_cors)
