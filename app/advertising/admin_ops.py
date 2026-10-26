"""Admin operations on ad settings shared by /admin/ads and the MCP connector.

Callers check admin rights themselves (browser session or MCP ``ads.admin``
scope + live admin check); this module only validates and stores.
"""
from __future__ import annotations

import re
from typing import Any

from config import Config
from app.advertising import awin, store

MAX_PER_PAGE_LIMIT = 4


class AdsAdminError(Exception):
    def __init__(self, code: str, status: int = 400, **details: Any):
        super().__init__(code)
        self.code = code
        self.status = status
        self.details = details


def settings_values(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a partial settings update; LIVE keeps all of its guards."""
    values: dict[str, Any] = {}
    if data.get("mode") is not None:
        mode = str(data["mode"])
        if mode not in store.MODES:
            raise AdsAdminError("invalid_mode")
        if mode == store.MODE_LIVE:
            # LIVE is never reached automatically: env permission, Awin
            # credentials and an explicit typed confirmation are all required.
            if not Config.ADS_LIVE_ALLOWED:
                raise AdsAdminError("live_not_allowed_by_env", 409)
            if not awin.AwinClient().configured:
                raise AdsAdminError("awin_not_configured", 409)
            if data.get("confirm") != "LIVE":
                raise AdsAdminError("confirmation_required", 409)
        values["mode"] = mode
    if data.get("max_per_page") is not None:
        try:
            values["max_per_page"] = max(0, min(int(data["max_per_page"]), MAX_PER_PAGE_LIMIT))
        except (TypeError, ValueError):
            raise AdsAdminError("invalid_max_per_page")
    if data.get("live_platforms") is not None:
        values["live_platforms"] = [p for p in data["live_platforms"] or [] if p in store.PLATFORMS]
    for flag in ("lapsed_paid_as_free", "demo_creatives", "admin_demo_always"):
        if data.get(flag) is not None:
            values[flag] = bool(data[flag])
    if data.get("preferred_topics") is not None:
        raw = data["preferred_topics"]
        items = raw if isinstance(raw, list) else re.split(r"[\s,;]+", str(raw))
        values["preferred_topics"] = list(dict.fromkeys(
            str(v).strip().lower() for v in items if str(v).strip().lower() in store.TOPICS
        ))
    return values


def update_settings(data: dict[str, Any]) -> dict[str, Any]:
    return store.save_settings(settings_values(data))


def update_placements(
    keys: list[str] | None,
    *,
    enabled: bool | None = None,
    priority: int | None = None,
) -> list[dict[str, Any]]:
    """Switch existing placements on/off (``keys`` empty/None = all of them)."""
    existing = {p["key"]: p for p in store.list_placements()}
    wanted = [str(k).strip().lower() for k in (keys or []) if str(k).strip()]
    unknown = [k for k in wanted if k not in existing]
    if unknown:
        raise AdsAdminError("unknown_placement", 404, unknown=unknown, known=sorted(existing))
    for key in wanted or list(existing):
        item = dict(existing[key])
        if enabled is not None:
            item["enabled"] = bool(enabled)
        if priority is not None:
            item["priority"] = int(priority)
        store.upsert_placement(item)
    return store.list_placements()


def set_creative_enabled(creative_id: int, enabled: bool) -> dict[str, Any]:
    if not store.get_creative(int(creative_id)):
        raise AdsAdminError("not_found", 404)
    store.set_creative_enabled(int(creative_id), bool(enabled))
    return store.get_creative(int(creative_id)) or {}


def summary() -> dict[str, Any]:
    """Compact state for an assistant: no raw creative code, no API log."""
    client = awin.AwinClient()
    return {
        "settings": store.get_settings(),
        "live_allowed_by_env": bool(Config.ADS_LIVE_ALLOWED),
        "awin_configured": client.configured,
        "placements": store.list_placements(),
        "advertisers": [
            {k: a.get(k) for k in ("id", "name", "awin_id", "enabled", "membership_status")}
            for a in store.list_advertisers()
        ],
        "creatives": [
            {k: c.get(k) for k in ("id", "advertiser_id", "name", "kind", "width", "height", "enabled", "preview_only")}
            for c in store.list_creatives()
        ],
        "constants": {
            "modes": list(store.MODES), "platforms": list(store.PLATFORMS),
            "topics": list(store.TOPICS), "max_per_page_limit": MAX_PER_PAGE_LIMIT,
        },
    }
