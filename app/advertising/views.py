"""HTTP layer of the advertising module (Flask blueprint)."""
from __future__ import annotations

import re
import time
from datetime import date, timedelta
from typing import Any, Callable
from urllib.parse import urlsplit

from flask import Blueprint, jsonify, render_template, request, session

from config import Config
from app.advertising import admin_ops, awin, policy, selection, store
from app.advertising import creatives as cr
from app.advertising.policy import Viewer

ads_bp = Blueprint("ads", __name__)

CONSENT_COOKIE = "pl_ads_consent"
CONSENT_VERSION = "v1"
CONSENT_MAX_AGE = 180 * 24 * 60 * 60
EVENT_WINDOW_S = 600
EVENT_LIMIT = 60
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{2,40}$")

_viewer_provider: Callable[[], Viewer | None] = lambda: None


def set_viewer_provider(provider: Callable[[], Viewer | None]) -> None:
    global _viewer_provider
    _viewer_provider = provider


def current_viewer() -> Viewer | None:
    try:
        return _viewer_provider()
    except Exception:
        return None


# ----------------------------------------------------------------- helpers

def read_consent(viewer: Viewer | None = None) -> str:
    if viewer is not None and viewer.channel == "app":
        # Native app: no cookies, the in-app choice is stored server-side.
        status = store.get_consent(viewer.user_id, "android")
        return status if status in (policy.CONSENT_GRANTED, policy.CONSENT_DENIED) else policy.CONSENT_UNKNOWN
    # Global Privacy Control is an explicit opt-out signal.
    if request.headers.get("Sec-GPC") == "1":
        return policy.CONSENT_DENIED
    raw = str(request.cookies.get(CONSENT_COOKIE) or "")
    version, _, value = raw.partition(":")
    if version == CONSENT_VERSION and value in (policy.CONSENT_GRANTED, policy.CONSENT_DENIED):
        return value
    return policy.CONSENT_UNKNOWN


def request_country(viewer: Viewer | None) -> str:
    if viewer and viewer.is_admin:
        override = str(request.args.get("country") or "").strip().upper()
        if len(override) == 2 and override.isalpha():
            return override
    header = str(Config.ADS_COUNTRY_HEADER or "").strip()
    if header:
        value = str(request.headers.get(header) or "").strip().upper()
        if len(value) == 2 and value.isalpha() and value not in ("XX", "T1"):
            return value
    for value, _quality in request.accept_languages:
        parts = value.replace("_", "-").split("-")
        if len(parts) >= 2 and len(parts[1]) == 2 and parts[1].isalpha():
            return parts[1].upper()
    return ""


def request_language(viewer: Viewer) -> str:
    if viewer.is_admin:
        override = str(request.args.get("lang") or "").strip().lower()
        if override:
            return cr.lang(override)
    return cr.lang(viewer.ui_language)


def request_platform(viewer: Viewer | None = None) -> str:
    # The native app is identified by its Bearer login, never by a parameter.
    if viewer is not None and viewer.channel == "app":
        return "android"
    value = str(request.args.get("platform") or "web").strip().lower()
    return value if value in ("web", "telegram") else "web"


def _decision(viewer: Viewer | None, platform: str, settings: dict[str, Any] | None = None) -> policy.Decision:
    return policy.decide(
        viewer, settings or store.get_settings(),
        platform=platform, consent=read_consent(viewer), live_allowed=bool(Config.ADS_LIVE_ALLOWED),
    )


def _same_origin() -> bool:
    origin = request.headers.get("Origin")
    return not origin or urlsplit(origin).netloc == request.host


def _admin_viewer() -> Viewer | None:
    viewer = current_viewer()
    # Admin tools only through the browser session, never the app token.
    return viewer if viewer and viewer.is_admin and viewer.channel == "session" else None


def _admin_write_guard():
    """Real admin session, JSON body and same origin (blocks cross-site forms)."""
    if not _admin_viewer():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if not request.is_json or not _same_origin():
        return jsonify({"ok": False, "error": "bad_request"}), 400
    return None


def _countries(values: Any) -> list[str]:
    result = [str(v).strip().upper() for v in (values or []) if str(v).strip()]
    return list(dict.fromkeys(v for v in result if len(v) == 2 and v.isalpha()))


def _languages(values: Any) -> list[str]:
    result = [str(v).strip().lower() for v in (values or []) if str(v).strip()]
    return list(dict.fromkeys(v for v in result if len(v) == 2 and v.isalpha()))


def _topics(values: Any) -> list[str]:
    return list(dict.fromkeys(str(v).strip().lower() for v in (values or []) if str(v).strip().lower() in store.TOPICS))


def _split(value: Any) -> list[str]:
    if isinstance(value, list):
        return value
    return [part for part in re.split(r"[\s,;]+", str(value or "")) if part]


def _date(value: Any) -> str:
    value = str(value or "").strip()
    return value if re.match(r"^\d{4}-\d{2}-\d{2}$", value) else ""


# ------------------------------------------------------------- public API

def _row_columns(platform: str) -> int:
    """Banner row width between lesson cards: only the web version, as many
    columns as the client's lesson grid shows (capped by selection)."""
    if platform != "web":
        return 1
    try:
        return int(request.args.get("columns") or 1)
    except (TypeError, ValueError):
        return 1


@ads_bp.get("/api/ads/page")
def api_ads_page():
    viewer = current_viewer()
    if viewer is None:
        return jsonify({"ok": False, "error": "auth_required"}), 401
    settings = store.get_settings()
    mode = settings["mode"]
    platform = request_platform(viewer)
    decision = _decision(viewer, platform, settings)
    payload: dict[str, Any] = {"ok": True, "mode": mode, "decision": decision.as_dict(), "slots": []}
    language = request_language(viewer)
    if decision.needs_consent:
        title, text, accept, decline = cr.CONSENT_TEXT[language]
        payload["consent_prompt"] = {"title": title, "text": text, "accept": accept, "decline": decline}
    if decision.serve == policy.SERVE_NONE:
        return jsonify(payload)
    page = str(request.args.get("page") or "").strip().lower()
    requested = [k for k in str(request.args.get("placements") or "").split(",") if k]
    payload["slots"] = selection.build_page(
        serve=decision.serve,
        placements=store.list_placements(page or None),
        requested=requested,
        device=request.args.get("device", ""),
        country=request_country(viewer),
        language=language,
        settings=settings,
        candidates=store.creative_candidates(),
        row_columns=_row_columns(platform),
    )
    return jsonify(payload)


@ads_bp.get("/api/ads/consent")
def api_ads_consent_get():
    viewer = current_viewer()
    if viewer is None:
        return jsonify({"ok": False, "error": "auth_required"}), 401
    return jsonify({"ok": True, "consent": read_consent(viewer), "gpc": request.headers.get("Sec-GPC") == "1"})


@ads_bp.post("/api/ads/consent")
def api_ads_consent_set():
    viewer = current_viewer()
    if viewer is None:
        return jsonify({"ok": False, "error": "auth_required"}), 401
    if not request.is_json or not _same_origin():
        return jsonify({"ok": False, "error": "bad_request"}), 400
    choice = str((request.get_json(silent=True) or {}).get("choice") or "")
    if choice not in (policy.CONSENT_GRANTED, policy.CONSENT_DENIED):
        return jsonify({"ok": False, "error": "invalid_choice"}), 400
    if viewer.channel == "app":
        store.save_consent(viewer.user_id, "android", choice)
        return jsonify({"ok": True, "consent": choice})
    response = jsonify({"ok": True, "consent": choice})
    # Remembering the user's choice is strictly necessary; nothing else is set.
    response.set_cookie(
        CONSENT_COOKIE, f"{CONSENT_VERSION}:{choice}", max_age=CONSENT_MAX_AGE,
        httponly=True, samesite="Lax", secure=request.is_secure,
    )
    return response


@ads_bp.post("/api/ads/event")
def api_ads_event():
    """Anonymous aggregated counters for LIVE material only."""
    viewer = current_viewer()
    if viewer is None or not _same_origin():
        return ("", 204)
    data = request.get_json(silent=True, force=True) or {}
    event = str(data.get("event") or "")
    placement = str(data.get("placement") or "")
    try:
        creative_id = int(data.get("creative_id"))
    except (TypeError, ValueError):
        return ("", 204)
    if event not in ("impression", "click"):
        return ("", 204)
    if _decision(viewer, request_platform(viewer)).serve != policy.SERVE_LIVE:
        return ("", 204)  # never count previews, admins or paid users
    if placement not in {p["key"] for p in store.list_placements() if p["enabled"]}:
        return ("", 204)
    creative = next((c for c in store.creative_candidates() if c["id"] == creative_id), None)
    if not creative or not selection.live_ready(creative):
        return ("", 204)
    now = int(time.time())
    window = session.get("ads_ev") or [now, 0]
    if now - int(window[0]) > EVENT_WINDOW_S:
        window = [now, 0]
    if int(window[1]) >= EVENT_LIMIT:
        return ("", 204)
    session["ads_ev"] = [int(window[0]), int(window[1]) + 1]
    store.record_event(placement, creative_id, selection.normalize_device(data.get("device", "")),
                       request_country(None), event)
    return ("", 204)


# -------------------------------------------------------------- admin page

@ads_bp.get("/admin/ads")
def admin_ads_page():
    if not _admin_viewer():
        return render_template("admin_ads.html", title="Реклама", hide_timer=True, denied=True), 403
    return render_template("admin_ads.html", title="Реклама", hide_timer=True, denied=False)


def _admin_state() -> dict[str, Any]:
    client = awin.AwinClient()
    viewer = _admin_viewer()
    return {
        "ok": True,
        "settings": store.get_settings(),
        "live_allowed": bool(Config.ADS_LIVE_ALLOWED),
        "awin": {"configured": client.configured, "publisher_id": client.publisher_id},
        "preview_plan": viewer.preview_plan if viewer else "",
        "placements": store.list_placements(),
        "advertisers": store.list_advertisers(),
        "creatives": store.list_creatives(),
        "stats": store.stats_summary(30),
        "api_log": store.api_log(50),
        "constants": {
            "sizes": list(store.SIZES), "devices": list(store.DEVICES), "topics": list(store.TOPICS),
            "platforms": list(store.PLATFORMS), "kinds": list(store.KINDS), "modes": list(store.MODES),
            "membership": list(store.MEMBERSHIP), "report_regions": list(awin.REPORT_REGIONS),
        },
    }


@ads_bp.get("/api/admin/ads/state")
def api_admin_ads_state():
    if not _admin_viewer():
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    return jsonify(_admin_state())


@ads_bp.get("/api/admin/ads/simulate")
def api_admin_ads_simulate():
    """What a Free user would get, as mock-ups (no external request)."""
    viewer = _admin_viewer()
    if not viewer:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    settings = store.get_settings()
    plan = str(request.args.get("plan") or "free")
    if plan != "free":
        return jsonify({"ok": True, "mode": settings["mode"], "plan": plan, "slots": []})
    page = str(request.args.get("page") or "dashboard")
    slots = selection.build_page(
        serve=policy.SERVE_DEMO, placements=store.list_placements(page), requested=[],
        device=request.args.get("device", ""), country=request_country(viewer),
        language=request_language(viewer), settings=settings, candidates=store.creative_candidates(),
    )
    return jsonify({"ok": True, "mode": settings["mode"], "plan": plan, "slots": slots})


@ads_bp.post("/api/admin/ads/settings")
def api_admin_ads_settings():
    denied = _admin_write_guard()
    if denied:
        return denied
    try:
        admin_ops.update_settings(request.get_json(silent=True) or {})
    except admin_ops.AdsAdminError as exc:
        return jsonify({"ok": False, "error": exc.code}), exc.status
    return jsonify(_admin_state())


@ads_bp.post("/api/admin/ads/placements")
def api_admin_ads_placement_save():
    denied = _admin_write_guard()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    key = str(data.get("key") or "").strip().lower()
    if not _KEY_RE.match(key):
        return jsonify({"ok": False, "error": "invalid_key"}), 400
    existing = {p["key"]: p for p in store.list_placements()}
    page = str(data.get("page") or existing.get(key, {}).get("page") or "").strip().lower()
    if not _KEY_RE.match(page):
        return jsonify({"ok": False, "error": "invalid_page"}), 400
    sizes_in = data.get("sizes") or {}
    sizes = {d: [s for s in (sizes_in.get(d) or []) if s in store.SIZES] for d in store.DEVICES}
    try:
        priority = int(data.get("priority", 50))
    except (TypeError, ValueError):
        priority = 50
    store.upsert_placement({
        "key": key, "page": page, "label": str(data.get("label") or key)[:80],
        "enabled": bool(data.get("enabled")), "priority": priority, "sizes": sizes,
    })
    return jsonify(_admin_state())


@ads_bp.post("/api/admin/ads/placements/<key>/delete")
def api_admin_ads_placement_delete(key: str):
    denied = _admin_write_guard()
    if denied:
        return denied
    if not store.delete_placement(key):
        return jsonify({"ok": False, "error": "builtin_or_missing"}), 400
    return jsonify(_admin_state())


@ads_bp.post("/api/admin/ads/advertisers")
def api_admin_ads_advertiser_save():
    denied = _admin_write_guard()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()[:200]
    if not name:
        return jsonify({"ok": False, "error": "name_required"}), 400
    awin_id = data.get("awin_id")
    try:
        awin_id = int(awin_id) if awin_id not in (None, "") else None
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid_awin_id"}), 400
    current = store.get_advertiser(int(data["id"])) if data.get("id") else None
    if data.get("id") and not current:
        return jsonify({"ok": False, "error": "not_found"}), 404
    # Membership comes from the Awin API; manually only "manual" can be set,
    # so nothing becomes LIVE-eligible without a verified "joined" state.
    membership = current["membership_status"] if current else "manual"
    if current and awin_id != current["awin_id"]:
        membership = "manual"
    try:
        advertiser_id = store.save_advertiser({
            "id": data.get("id"), "name": name, "awin_id": awin_id, "enabled": bool(data.get("enabled")),
            "countries": _countries(_split(data.get("countries"))),
            "languages": _languages(_split(data.get("languages"))),
            "topics": _topics(_split(data.get("topics"))), "notes": str(data.get("notes") or "")[:500],
            "membership_status": membership,
        })
    except Exception:
        return jsonify({"ok": False, "error": "duplicate_awin_id"}), 409
    return jsonify({**_admin_state(), "advertiser_id": advertiser_id})


@ads_bp.post("/api/admin/ads/creatives")
def api_admin_ads_creative_save():
    denied = _admin_write_guard()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    try:
        advertiser_id = int(data.get("advertiser_id"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "advertiser_required"}), 400
    if not store.get_advertiser(advertiser_id):
        return jsonify({"ok": False, "error": "advertiser_not_found"}), 404
    kind = str(data.get("kind") or "")
    if kind not in store.KINDS:
        return jsonify({"ok": False, "error": "invalid_kind"}), 400
    item: dict[str, Any] = {
        "id": data.get("id"), "advertiser_id": advertiser_id, "kind": kind,
        "name": str(data.get("name") or "").strip()[:200] or kind,
        "countries": _countries(_split(data.get("countries"))),
        "languages": _languages(_split(data.get("languages"))),
        "topics": _topics(_split(data.get("topics"))),
        "enabled": bool(data.get("enabled")),
        "preview_only": bool(data.get("preview_only")),
        "starts_on": _date(data.get("starts_on")), "ends_on": _date(data.get("ends_on")),
    }
    try:
        if kind == "awin_html":
            parsed = cr.parse_awin_creative(data.get("raw_code", ""))
            item.update(parsed, raw_code=str(data.get("raw_code"))[:5000])
        else:
            item["click_url"] = cr.click_url(data["click_url"]) if data.get("click_url") else ""
            if kind == "image_link":
                item["image_url"] = cr.image_url(data.get("image_url", ""))
                item["width"], item["height"] = data.get("width"), data.get("height")
                item["alt"] = str(data.get("alt") or "")[:200]
            else:
                item["headline"] = str(data.get("headline") or "").strip()[:80]
                item["body"] = str(data.get("body") or "").strip()[:160]
                item["cta"] = str(data.get("cta") or "").strip()[:30]
                if not item["headline"]:
                    return jsonify({"ok": False, "error": "headline_required"}), 400
    except cr.CreativeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    if kind != "text":
        try:
            width, height = int(item.get("width") or 0), int(item.get("height") or 0)
        except (TypeError, ValueError):
            width = height = 0
        if not cr.size_key(width, height):
            return jsonify({"ok": False, "error": "unsupported_size",
                            "supported": list(store.SIZES)}), 400
        item["width"], item["height"] = width, height
    creative_id = store.save_creative(item)
    return jsonify({**_admin_state(), "creative_id": creative_id})


@ads_bp.post("/api/admin/ads/creatives/<int:creative_id>/enabled")
def api_admin_ads_creative_enabled(creative_id: int):
    denied = _admin_write_guard()
    if denied:
        return denied
    if not store.get_creative(creative_id):
        return jsonify({"ok": False, "error": "not_found"}), 404
    store.set_creative_enabled(creative_id, bool((request.get_json(silent=True) or {}).get("enabled")))
    return jsonify(_admin_state())


@ads_bp.post("/api/admin/ads/import-preview")
def api_admin_ads_import_preview():
    """Load the bundled read-only Awin check (candidates, preview copy, slots)."""
    denied = _admin_write_guard()
    if denied:
        return denied
    from app.advertising import preview_config
    try:
        result = preview_config.import_preview_config(preview_config.load_bundled())
    except (OSError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({**_admin_state(), **result})


# ------------------------------------------------------------ Awin actions

def _awin_error(exc: awin.AwinError):
    return jsonify({"ok": False, "error": exc.code, "http_status": exc.http_status, "detail": exc.detail}), 502


@ads_bp.post("/api/admin/ads/awin/sync")
def api_admin_ads_awin_sync():
    denied = _admin_write_guard()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    relationship = str(data.get("relationship") or "joined")
    try:
        programmes = awin.AwinClient().programmes(relationship, str(data.get("country") or ""))
    except awin.AwinError as exc:
        return _awin_error(exc)
    synced = 0
    for programme in programmes:
        if isinstance(programme, dict) and str(programme.get("id") or "").isdigit():
            store.upsert_awin_programme(programme, relationship)
            synced += 1
    return jsonify({**_admin_state(), "synced": synced})


@ads_bp.post("/api/admin/ads/awin/check/<int:advertiser_id>")
def api_admin_ads_awin_check(advertiser_id: int):
    denied = _admin_write_guard()
    if denied:
        return denied
    advertiser = store.get_advertiser(advertiser_id)
    if not advertiser or not advertiser["awin_id"]:
        return jsonify({"ok": False, "error": "awin_id_required"}), 400
    try:
        details = awin.AwinClient().programme_details(int(advertiser["awin_id"]))
    except awin.AwinError as exc:
        return _awin_error(exc)
    status = awin.membership_from_details(details)
    if status:
        store.set_membership(advertiser_id, status)
    return jsonify({**_admin_state(), "membership_status": status or "unknown",
                    "kpi": details.get("kpi") or {}})


@ads_bp.post("/api/admin/ads/awin/link")
def api_admin_ads_awin_link():
    """Explicit admin action: create a tracking link for an approved programme."""
    denied = _admin_write_guard()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    try:
        advertiser = store.get_advertiser(int(data.get("advertiser_id")))
    except (TypeError, ValueError):
        advertiser = None
    if not advertiser or not advertiser["awin_id"]:
        return jsonify({"ok": False, "error": "awin_id_required"}), 400
    if advertiser["membership_status"] != "joined":
        return jsonify({"ok": False, "error": "programme_not_joined"}), 409
    destination = str(data.get("destination_url") or "").strip()
    if destination and not destination.startswith("https://"):
        return jsonify({"ok": False, "error": "destination_must_be_https"}), 400
    clickref = str(data.get("clickref") or "").strip().lower()
    try:
        result = awin.AwinClient().generate_link(int(advertiser["awin_id"]), destination, clickref)
    except awin.AwinError as exc:
        return _awin_error(exc)
    try:
        url = cr.click_url(result["url"])
    except cr.CreativeError:
        return jsonify({"ok": False, "error": "unexpected_link_host"}), 502
    creative_id = data.get("creative_id")
    if creative_id:
        if not store.get_creative(int(creative_id)):
            return jsonify({"ok": False, "error": "creative_not_found"}), 404
        store.set_creative_click_url(int(creative_id), url)
    return jsonify({**_admin_state(), "url": url})


@ads_bp.post("/api/admin/ads/awin/report")
def api_admin_ads_awin_report():
    denied = _admin_write_guard()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    end = _date(data.get("end")) or date.today().isoformat()
    start = _date(data.get("start")) or (date.today() - timedelta(days=30)).isoformat()
    try:
        rows = awin.AwinClient().creative_report(start, end, str(data.get("region") or "NL").upper())
    except awin.AwinError as exc:
        return _awin_error(exc)
    keys = ("creativeId", "creativeName", "advertiserName", "region", "currency", "impressions", "clicks",
            "totalNo", "totalValue", "totalComm")
    return jsonify({"ok": True, "rows": [{k: row.get(k) for k in keys} for row in rows[:500]]})


# ------------------------------------------------------- template context

def template_context() -> dict[str, Any]:
    """Load the client script only when this viewer could get something.

    In OFF mode (and for paid users, children, admins outside Free
    simulation) no ad script is loaded and no ad request is made.
    """
    flags = {"ads_client_enabled": False, "ads_consent_ui": False}
    if request.method != "GET" or request.path.startswith("/api/"):
        return flags
    try:
        settings = store.get_settings()
        viewer = current_viewer()
        if viewer is None:
            return flags
        # OFF: nothing for users; admins get only their own mock-ups (policy decides).
        if settings["mode"] == store.MODE_OFF and not viewer.is_admin:
            return flags
        decision = _decision(viewer, "web", settings)
        live_allowed = bool(Config.ADS_LIVE_ALLOWED)
        telegram = _decision(viewer, "telegram", settings)
        flags["ads_client_enabled"] = bool(
            decision.serve != policy.SERVE_NONE or decision.needs_consent
            # Telegram may be enabled while web is not; the client reports it.
            or telegram.serve != policy.SERVE_NONE or telegram.needs_consent
        )
        flags["ads_consent_ui"] = (
            policy.consent_relevant(viewer, settings, live_allowed)
            or (settings["mode"] == store.MODE_LIVE and read_consent(viewer) != policy.CONSENT_UNKNOWN
                and not viewer.is_admin)
        )
        if flags["ads_consent_ui"]:
            title, text, accept, decline = cr.CONSENT_TEXT[cr.lang(viewer.ui_language)]
            flags["ads_consent_text"] = {"title": title, "text": text, "accept": accept, "decline": decline}
    except Exception:
        return {"ads_client_enabled": False, "ads_consent_ui": False}
    return flags
