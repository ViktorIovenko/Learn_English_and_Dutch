from __future__ import annotations

import base64
import hashlib
import json
import secrets
import sqlite3
import time
from urllib.parse import urlencode, urlparse
from urllib.request import Request as UrlRequest, urlopen

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session

from config import Config
from app.mcp_service import (
    ALL_SCOPES,
    ANALYTICS_ADMIN_SCOPE,
    CONNECTOR_SCOPES,
    FAMILY_READ_SCOPE,
    FAMILY_WRITE_SCOPE,
    READ_SCOPE,
    SUBSCRIPTIONS_ADMIN_SCOPE,
    USERS_ADMIN_SCOPE,
    McpServiceError,
    _conn,
    ensure_mcp_schema,
    execute,
    token_hash,
)


mcp_api = Blueprint("mcp_api", __name__)


def _issuer() -> str:
    return str(Config.MCP_ISSUER_URL or Config.PUBLIC_BASE_URL).rstrip("/")


def _resource() -> str:
    return str(Config.MCP_PUBLIC_URL or "").rstrip("/")


def _now() -> int:
    return int(time.time())


def _json_list(value: str) -> list[str]:
    try:
        result = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in result] if isinstance(result, list) else []


def _valid_redirect_uri(uri: str) -> bool:
    parsed = urlparse(str(uri or ""))
    return bool(
        (parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password)
        or (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"})
    )


def _oauth_error(error: str, description: str, status: int = 400):
    response = jsonify({"error": error, "error_description": description})
    response.status_code = status
    response.headers["Cache-Control"] = "no-store"
    return response


def _internal_authorized() -> bool:
    configured = str(Config.MCP_INTERNAL_TOKEN or "")
    authorization = str(request.headers.get("Authorization") or "")
    supplied = authorization[7:].strip() if authorization.lower().startswith("bearer ") else ""
    return bool(configured and supplied and secrets.compare_digest(configured, supplied))


def _user_mcp_enabled(user_id: str, *, connection=None) -> bool:
    owns_connection = connection is None
    conn = connection or _conn()
    try:
        row = conn.execute("SELECT enabled FROM mcp_user_settings WHERE user_id=?", (user_id,)).fetchone()
        return bool(row is None or row["enabled"])
    finally:
        if owns_connection:
            conn.close()


def _current_user_id() -> str:
    from app.routes import _session_user_id, _user_exists
    user_id = _session_user_id()
    return user_id if user_id and _user_exists(user_id) else ""


def _resolve_access_token(raw_token: str, *, touch: bool = True) -> dict | None:
    if not raw_token:
        return None
    ensure_mcp_schema()
    now = _now()
    digest = token_hash(raw_token)
    with _conn() as conn:
        row = conn.execute(
            """
            SELECT token_hash, client_id, user_id, resource, scopes, expires_at
            FROM mcp_access_grants
            WHERE token_hash=? AND revoked_at IS NULL AND expires_at>?
            """,
            (digest, now),
        ).fetchone()
        if not row or str(row["resource"]).rstrip("/") != _resource():
            return None
        if not _user_mcp_enabled(str(row["user_id"]), connection=conn):
            return None
        if touch:
            conn.execute("UPDATE mcp_access_grants SET last_used_at=? WHERE token_hash=?", (now, digest))
            conn.execute("UPDATE mcp_oauth_clients SET last_used_at=? WHERE client_id=?", (now, row["client_id"]))
            conn.commit()
    return {
        "client_id": str(row["client_id"]),
        "user_id": str(row["user_id"]),
        "resource": str(row["resource"]),
        "scopes": _json_list(row["scopes"]),
        "expires_at": int(row["expires_at"]),
    }


@mcp_api.get("/api/mcp/user")
def mcp_user_status():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "authentication_required"}), 401
    ensure_mcp_schema()
    now = _now()
    with _conn() as conn:
        enabled = _user_mcp_enabled(user_id, connection=conn)
        google_account = conn.execute(
            "SELECT google_id,google_email FROM users WHERE user_id=?", (user_id,)
        ).fetchone()
        rows = conn.execute(
            "SELECT g.client_id,g.scopes,g.created_at,g.last_used_at,g.expires_at,c.client_name "
            "FROM mcp_access_grants g LEFT JOIN mcp_oauth_clients c ON c.client_id=g.client_id "
            "WHERE g.user_id=? AND g.revoked_at IS NULL AND g.expires_at>? "
            "ORDER BY COALESCE(g.last_used_at,g.created_at) DESC LIMIT 20",
            (user_id, now),
        ).fetchall()
    clients = [{
        "client_name": str(row["client_name"] or "MCP client"),
        "scopes": _json_list(row["scopes"]),
        "created_at": int(row["created_at"]),
        "last_used_at": int(row["last_used_at"]) if row["last_used_at"] else None,
        "expires_at": int(row["expires_at"]),
    } for row in rows]
    connected = bool(clients)
    state = "connected" if enabled and connected else "paused" if connected else "ready" if enabled else "disabled"
    issuer = _issuer()
    return jsonify({
        "ok": True,
        "enabled": enabled,
        "connected": connected,
        "state": state,
        "connections": clients,
        "google_account": {
            "linked": bool(google_account and google_account["google_id"]),
            "email": str((google_account and google_account["google_email"]) or ""),
        },
        "connector": {
            "name": "ParallelLingvo",
            "description": "Ваш личный помощник ParallelLingvo в ИИ-ассистенте: уроки, слова, примеры и прогресс в одном диалоге.",
            "description_en": "Your personal ParallelLingvo assistant for lessons, vocabulary, examples and progress in your AI assistant.",
            "icon_url": f"{issuer}/static/mcp-icon-small.png",
            "hero_image_url": f"{issuer}/static/mcp-icon-large.png",
            "mcp_url": _resource(),
            "issuer": issuer,
            "transport": "Streamable HTTP",
            "authorization": "OAuth 2.1 + PKCE",
            "authorization_metadata": f"{issuer}/.well-known/oauth-authorization-server",
            "resource_metadata": f"{issuer}/.well-known/oauth-protected-resource/mcp",
            "version": Config.MCP_CONNECTOR_VERSION,
        },
    })


@mcp_api.post("/api/mcp/user")
def mcp_user_toggle():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "authentication_required"}), 401
    data = request.get_json(silent=True) or {}
    if not isinstance(data.get("enabled"), bool):
        return jsonify({"ok": False, "error": "enabled_must_be_boolean"}), 400
    ensure_mcp_schema()
    now = _now()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO mcp_user_settings(user_id,enabled,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET enabled=excluded.enabled,updated_at=excluded.updated_at",
            (user_id, int(data["enabled"]), now),
        )
        conn.commit()
    return jsonify({"ok": True, "enabled": data["enabled"]})


@mcp_api.post("/api/mcp/user/revoke-all")
def mcp_user_revoke_all():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "authentication_required"}), 401
    ensure_mcp_schema()
    now = _now()
    with _conn() as conn:
        cursor = conn.execute(
            "UPDATE mcp_access_grants SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL",
            (now, user_id),
        )
        conn.commit()
    return jsonify({"ok": True, "revoked": int(cursor.rowcount or 0)})


def _admin_user_id() -> str:
    from app.routes import _session_admin_user_id
    return _session_admin_user_id()


def _component_health() -> dict[str, str]:
    result = {"gateway": "error", "internal_api": "ok", "database": "ok", "redis": "unknown"}
    try:
        request_obj = UrlRequest("http://mcp-gateway:8000/health", headers={"Accept": "application/json"})
        with urlopen(request_obj, timeout=2) as response:
            payload = json.loads(response.read(16384).decode("utf-8"))
        result["gateway"] = "ok" if payload.get("ok") else "error"
        result["redis"] = str(payload.get("redis") or "unknown")
    except Exception:
        pass
    try:
        with _conn() as conn:
            conn.execute("SELECT 1").fetchone()
    except sqlite3.Error:
        result["internal_api"] = "error"
        result["database"] = "error"
    return result


@mcp_api.get("/admin/mcp")
def mcp_admin_page():
    admin_user_id = _admin_user_id()
    if not admin_user_id:
        return render_template("mcp_admin.html", title="MCP connector", access_denied=True), 403
    ensure_mcp_schema()
    now = _now()
    with _conn() as conn:
        clients = [dict(row) for row in conn.execute(
            "SELECT client_id,client_name,created_at,last_used_at,revoked_at FROM mcp_oauth_clients ORDER BY created_at DESC LIMIT 100"
        ).fetchall()]
        grants = [dict(row) for row in conn.execute(
            "SELECT g.token_hash,g.client_id,g.user_id,g.scopes,g.created_at,g.last_used_at,g.expires_at,g.revoked_at,c.client_name "
            "FROM mcp_access_grants g LEFT JOIN mcp_oauth_clients c ON c.client_id=g.client_id ORDER BY g.created_at DESC LIMIT 100"
        ).fetchall()]
        usage = [dict(row) for row in conn.execute(
            "SELECT operation,success,COUNT(*) AS calls,SUM(item_count) AS items,MAX(created_at) AS last_used_at "
            "FROM mcp_audit_log WHERE created_at>? GROUP BY operation,success ORDER BY calls DESC,operation LIMIT 100",
            (now - 7 * 86400,),
        ).fetchall()]
    for client in clients:
        client["client_id_short"] = str(client["client_id"])[:12] + "..."
    for grant in grants:
        grant["token_hash_short"] = str(grant["token_hash"])[:12] + "..."
        grant["user_hash"] = token_hash(str(grant.pop("user_id")))[:12]
        grant["scopes"] = _json_list(grant["scopes"])
    return render_template(
        "mcp_admin.html",
        title="MCP connector",
        access_denied=False,
        connector={
            "name": "ParallelLingvo", "version": Config.MCP_CONNECTOR_VERSION,
            "url": _resource(), "issuer": _issuer(),
            "revision": Config.MCP_BUILD_REVISION,
            "created": Config.MCP_BUILD_CREATED,
            "source": Config.MCP_BUILD_SOURCE,
        },
        health=_component_health(),
        scopes=list(ALL_SCOPES),
        clients=clients,
        grants=grants,
        usage=usage,
        now=now,
    )


@mcp_api.post("/admin/mcp/revoke")
def mcp_admin_revoke():
    if not _admin_user_id():
        return jsonify({"ok": False, "error": "admin_required"}), 403
    if str(request.form.get("confirm") or "") != "REVOKE":
        return jsonify({"ok": False, "error": "confirmation_required"}), 400
    kind = str(request.form.get("kind") or "")
    identifier = str(request.form.get("identifier") or "")
    now = _now()
    ensure_mcp_schema()
    with _conn() as conn:
        if kind == "client":
            conn.execute("UPDATE mcp_oauth_clients SET revoked_at=COALESCE(revoked_at,?) WHERE client_id=?", (now, identifier))
            conn.execute("UPDATE mcp_access_grants SET revoked_at=COALESCE(revoked_at,?) WHERE client_id=?", (now, identifier))
        elif kind == "grant":
            conn.execute("UPDATE mcp_access_grants SET revoked_at=COALESCE(revoked_at,?) WHERE token_hash=?", (now, identifier))
        else:
            return jsonify({"ok": False, "error": "invalid_target"}), 400
        conn.commit()
    return redirect("/admin/mcp?revoked=1")


@mcp_api.get("/.well-known/oauth-authorization-server")
def oauth_metadata():
    issuer = _issuer()
    response = jsonify({
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/oauth/authorize",
        "token_endpoint": f"{issuer}/oauth/token",
        "registration_endpoint": f"{issuer}/oauth/register",
        "revocation_endpoint": f"{issuer}/oauth/revoke",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "token_endpoint_auth_methods_supported": ["none"],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": list(ALL_SCOPES),
        "authorization_response_iss_parameter_supported": False,
    })
    response.headers["Cache-Control"] = "public, max-age=300"
    return response


@mcp_api.post("/oauth/register")
def oauth_register():
    ensure_mcp_schema()
    data = request.get_json(silent=True) or {}
    redirect_uris = data.get("redirect_uris") or []
    if not isinstance(redirect_uris, list) or not redirect_uris or len(redirect_uris) > 10:
        return _oauth_error("invalid_redirect_uri", "redirect_uris must be a non-empty list")
    cleaned = list(dict.fromkeys(str(uri).strip() for uri in redirect_uris))
    if any(not _valid_redirect_uri(uri) for uri in cleaned):
        return _oauth_error("invalid_redirect_uri", "redirect URI must use HTTPS")
    method = str(data.get("token_endpoint_auth_method") or "none")
    if method != "none":
        return _oauth_error("invalid_client_metadata", "only public PKCE clients are supported")
    client_id = secrets.token_urlsafe(32)
    client_name = str(data.get("client_name") or "MCP client")[:120]
    with _conn() as conn:
        conn.execute(
            "INSERT INTO mcp_oauth_clients(client_id,client_name,redirect_uris,created_at) VALUES(?,?,?,?)",
            (client_id, client_name, json.dumps(cleaned), _now()),
        )
        conn.commit()
    response = jsonify({
        "client_id": client_id,
        "client_id_issued_at": _now(),
        "client_name": client_name,
        "redirect_uris": cleaned,
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
    })
    response.status_code = 201
    response.headers["Cache-Control"] = "no-store"
    return response


def _authorization_request() -> tuple[dict | None, str | None]:
    values = request.values
    payload = {
        "response_type": str(values.get("response_type") or ""),
        "client_id": str(values.get("client_id") or ""),
        "redirect_uri": str(values.get("redirect_uri") or ""),
        "scope": str(values.get("scope") or " ".join(CONNECTOR_SCOPES)),
        "state": str(values.get("state") or ""),
        "code_challenge": str(values.get("code_challenge") or ""),
        "code_challenge_method": str(values.get("code_challenge_method") or ""),
        "resource": str(values.get("resource") or "").rstrip("/"),
    }
    if payload["response_type"] != "code":
        return None, "response_type must be code"
    if not payload["client_id"] or not payload["redirect_uri"]:
        return None, "client_id and redirect_uri are required"
    if payload["resource"] != _resource():
        return None, "resource does not match this MCP server"
    if payload["code_challenge_method"] != "S256" or len(payload["code_challenge"]) < 43:
        return None, "PKCE S256 is required"
    ensure_mcp_schema()
    with _conn() as conn:
        client = conn.execute(
            "SELECT client_name,redirect_uris FROM mcp_oauth_clients WHERE client_id=? AND revoked_at IS NULL",
            (payload["client_id"],),
        ).fetchone()
    if not client:
        return None, "unknown client_id"
    if payload["redirect_uri"] not in _json_list(client["redirect_uris"]):
        return None, "redirect_uri is not registered for this client"
    requested = list(dict.fromkeys(item for item in payload["scope"].split() if item))
    if any(scope not in ALL_SCOPES for scope in requested):
        return None, "one or more scopes are unsupported"
    payload["requested_scopes"] = list(dict.fromkeys([*CONNECTOR_SCOPES, *requested]))
    # Shown on the consent screen so a user can tell a spoofed/rogue
    # self-registered client from the real one before granting access.
    payload["client_name"] = str(client["client_name"] or "Unknown client")
    payload["redirect_origin"] = urlparse(payload["redirect_uri"]).netloc
    return payload, None


@mcp_api.route("/oauth/authorize", methods=["GET", "POST"])
def oauth_authorize():
    payload, error = _authorization_request()
    if error:
        return _oauth_error("invalid_request", error)
    assert payload is not None
    user_id = str(session.get("tg_user_id") or "").strip() if session.get("is_auth") else ""
    if user_id:
        from app.routes import _detect_browser_language, _update_detected_ui_language
        # This page is opened straight from ChatGPT/Claude in a plain browser
        # tab, so unlike the Mini App/Android client it never sent an
        # X-Device-Language header before; detect it here so the consent
        # screen (and this user's saved preference) follow their browser
        # locale automatically instead of defaulting to English.
        _update_detected_ui_language(user_id, _detect_browser_language())
    if not user_id:
        if request.method == "GET":
            # Both login links intentionally accept only local return paths.
            # Passing request.url here makes them fall back to /upload and lose
            # ChatGPT's one-time OAuth request after the user signs in.
            next_qs = urlencode({"next": request.full_path})
            return render_template(
                "mcp_consent.html",
                login_required=True,
                google_login_url="/auth/google?" + next_qs if Config.GOOGLE_CLIENT_ID else "",
                telegram_login_url="/auth/telegram?" + next_qs if Config.TELEGRAM_OIDC_CLIENT_ID else "",
                request_data=payload,
                scopes=[],
                is_admin=False,
            ), 401
        return _oauth_error("access_denied", "sign in to ParallelLingvo before granting access", 401)
    ensure_mcp_schema()
    if not _user_mcp_enabled(user_id):
        return _oauth_error("access_denied", "MCP connector is disabled in ParallelLingvo settings", 403)

    from app.routes import _account_context, _is_admin_user_id
    is_admin = _is_admin_user_id(user_id)
    # Family scope lets a parent's connector read/manage a linked child's data —
    # never the reverse, so a child account is never offered or granted it here
    # (execute() also re-checks this live on every call, not just at consent).
    is_child = _account_context(user_id)["account_type"] == "child"
    requested_scopes = payload["requested_scopes"]
    if not is_admin:
        requested_scopes = [scope for scope in requested_scopes if scope not in {SUBSCRIPTIONS_ADMIN_SCOPE, USERS_ADMIN_SCOPE, ANALYTICS_ADMIN_SCOPE}]
    if is_child:
        requested_scopes = [scope for scope in requested_scopes if scope not in {FAMILY_READ_SCOPE, FAMILY_WRITE_SCOPE}]
    if request.method == "GET":
        return render_template(
            "mcp_consent.html",
            login_required=False,
            google_login_url="",
            telegram_login_url="",
            request_data=payload,
            scopes=requested_scopes,
            is_admin=is_admin,
        )

    if str(request.form.get("decision") or "") != "allow":
        query = {"error": "access_denied"}
        if payload["state"]:
            query["state"] = payload["state"]
        return redirect(payload["redirect_uri"] + "?" + urlencode(query))
    selected = list(dict.fromkeys(request.form.getlist("granted_scope")))
    selected = [scope for scope in selected if scope in requested_scopes]
    selected = list(dict.fromkeys([*CONNECTOR_SCOPES, *selected]))
    if not is_admin:
        selected = [scope for scope in selected if scope not in {SUBSCRIPTIONS_ADMIN_SCOPE, USERS_ADMIN_SCOPE, ANALYTICS_ADMIN_SCOPE}]
    if is_child:
        selected = [scope for scope in selected if scope not in {FAMILY_READ_SCOPE, FAMILY_WRITE_SCOPE}]

    raw_code = secrets.token_urlsafe(48)
    now = _now()
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO mcp_oauth_codes(
                code_hash,client_id,user_id,redirect_uri,resource,scopes,
                code_challenge,expires_at,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                token_hash(raw_code), payload["client_id"], user_id,
                payload["redirect_uri"], payload["resource"], json.dumps(selected),
                payload["code_challenge"], now + int(Config.MCP_AUTH_CODE_TTL_SECONDS), now,
            ),
        )
        conn.commit()
    query = {"code": raw_code}
    if payload["state"]:
        query["state"] = payload["state"]
    return redirect(payload["redirect_uri"] + "?" + urlencode(query))


@mcp_api.post("/oauth/token")
def oauth_token():
    if str(request.form.get("grant_type") or "") != "authorization_code":
        return _oauth_error("unsupported_grant_type", "only authorization_code is supported")
    raw_code = str(request.form.get("code") or "")
    client_id = str(request.form.get("client_id") or "")
    redirect_uri = str(request.form.get("redirect_uri") or "")
    verifier = str(request.form.get("code_verifier") or "")
    resource = str(request.form.get("resource") or "").rstrip("/")
    if not all((raw_code, client_id, redirect_uri, verifier, resource)):
        return _oauth_error("invalid_request", "code, client_id, redirect_uri, code_verifier and resource are required")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii", "ignore")).digest()).rstrip(b"=").decode("ascii")
    now = _now()
    ensure_mcp_schema()
    with _conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM mcp_oauth_codes WHERE code_hash=? AND used_at IS NULL AND expires_at>?",
            (token_hash(raw_code), now),
        ).fetchone()
        if not row:
            conn.rollback()
            return _oauth_error("invalid_grant", "authorization code is invalid, expired or already used")
        if not (
            secrets.compare_digest(str(row["client_id"]), client_id)
            and secrets.compare_digest(str(row["redirect_uri"]), redirect_uri)
            and secrets.compare_digest(str(row["resource"]).rstrip("/"), resource)
            and secrets.compare_digest(str(row["code_challenge"]), challenge)
        ):
            conn.rollback()
            return _oauth_error("invalid_grant", "authorization code binding or PKCE verification failed")
        if not _user_mcp_enabled(str(row["user_id"]), connection=conn):
            conn.rollback()
            return _oauth_error("invalid_grant", "MCP connector is disabled for this user")
        conn.execute("UPDATE mcp_oauth_codes SET used_at=? WHERE code_hash=?", (now, row["code_hash"]))
        raw_token = secrets.token_urlsafe(48)
        expires_in = int(Config.MCP_ACCESS_TOKEN_TTL_SECONDS)
        conn.execute(
            "INSERT INTO mcp_access_grants(token_hash,client_id,user_id,resource,scopes,expires_at,created_at) VALUES(?,?,?,?,?,?,?)",
            (token_hash(raw_token), client_id, row["user_id"], resource, row["scopes"], now + expires_in, now),
        )
        conn.commit()
    response = jsonify({
        "access_token": raw_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "scope": " ".join(_json_list(row["scopes"])),
    })
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


@mcp_api.post("/oauth/revoke")
def oauth_revoke():
    raw_token = str(request.form.get("token") or "")
    if raw_token:
        ensure_mcp_schema()
        with _conn() as conn:
            conn.execute("UPDATE mcp_access_grants SET revoked_at=? WHERE token_hash=?", (_now(), token_hash(raw_token)))
            conn.commit()
    response = ("", 200)
    return response


@mcp_api.post("/api/internal/mcp/resolve")
def internal_mcp_resolve():
    if not _internal_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    raw_token = str(request.headers.get("X-MCP-Access-Token") or "")
    grant = _resolve_access_token(raw_token)
    if not grant:
        return jsonify({"ok": False, "error": "invalid_token"}), 401
    return jsonify({"ok": True, "grant": grant})


@mcp_api.post("/api/internal/mcp/execute")
def internal_mcp_execute():
    if not _internal_authorized():
        return jsonify({"ok": False, "data": None, "warnings": [], "truncated": False, "error": {"code": "UNAUTHORIZED", "message": "internal authentication failed", "retryable": False, "details": {}}}), 401
    raw_token = str(request.headers.get("X-MCP-Access-Token") or "")
    grant = _resolve_access_token(raw_token)
    if not grant:
        return jsonify({"ok": False, "data": None, "warnings": [], "truncated": False, "error": {"code": "INVALID_TOKEN", "message": "access token is invalid or expired", "retryable": False, "details": {}}}), 401
    data = request.get_json(silent=True) or {}
    operation = str(data.get("operation") or "")
    params = data.get("params") if isinstance(data.get("params"), dict) else {}
    request_id = str(data.get("request_id") or request.headers.get("X-Request-ID") or "")[:128]
    started = time.monotonic()
    success = False
    error_code = ""
    item_count = 0
    status = 200
    try:
        routes = __import__("app.routes", fromlist=["routes"])
        routes._ensure_schema()
        routes._ensure_progress_schema()
        routes._ensure_daily_goal_schema()
        routes._ensure_user_language_schema()
        routes._ensure_user_settings_schema()
        routes._ensure_family_schema()
        routes._ensure_subscription_schema()
        result = execute(operation, grant["user_id"], grant["scopes"], params)
        success = True
        if isinstance(result, dict):
            if isinstance(result.get("items"), list):
                item_count = len(result["items"])
            elif isinstance(result.get("stored"), int):
                item_count = result["stored"]
        payload = {"ok": True, "data": result, "warnings": [], "truncated": bool(isinstance(result, dict) and result.get("truncated")), "error": None}
    except McpServiceError as exc:
        error_code = exc.code
        status = exc.status
        payload = {"ok": False, "data": None, "warnings": [], "truncated": False, "error": {"code": exc.code, "message": exc.message, "retryable": False, "details": exc.details}}
    except Exception:
        current_app.logger.exception("MCP internal operation failed: %s", operation)
        error_code = "INTERNAL_ERROR"
        status = 500
        payload = {"ok": False, "data": None, "warnings": [], "truncated": False, "error": {"code": error_code, "message": "operation failed", "retryable": True, "details": {}}}
    duration_ms = int((time.monotonic() - started) * 1000)
    try:
        with _conn() as conn:
            conn.execute(
                "INSERT INTO mcp_audit_log(created_at,request_id,client_hash,user_hash,operation,success,error_code,duration_ms,item_count) VALUES(?,?,?,?,?,?,?,?,?)",
                (_now(), request_id, token_hash(grant["client_id"])[:16], token_hash(grant["user_id"])[:16], operation, int(success), error_code or None, duration_ms, item_count),
            )
            conn.commit()
    except Exception:
        current_app.logger.exception("Could not write bounded MCP audit record")
    return jsonify(payload), status


@mcp_api.get("/api/internal/mcp/health")
def internal_mcp_health():
    if not _internal_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    try:
        with _conn() as conn:
            conn.execute("SELECT 1").fetchone()
        return jsonify({"ok": True, "database": "ok"})
    except sqlite3.Error:
        return jsonify({"ok": False, "database": "error"}), 503
