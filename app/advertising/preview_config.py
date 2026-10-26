"""Import of the read-only Awin check (schema parallellingvo.awin.preview.v1).

Creates candidate advertisers with their real Awin membership status and
preview-only text material from the supplied (unofficial) copy. Nothing here
can make material LIVE: preview copy is flagged ``preview_only``, no link is
created and the mode is never set to LIVE.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.advertising import store

SCHEMA = "parallellingvo.awin.preview.v1"
BUNDLED = Path(__file__).with_name("data") / "awin_preview_v1.json"

# Topic hints for relevance ranking (editable in the admin panel).
_TOPIC_HINTS = {8177: ["education"], 9243: ["books"], 32301: ["language", "education"], 18785: ["software"]}


def _membership(value: Any) -> str:
    status = str(value or "").strip().lower().replace(" ", "")
    return status if status in store.MEMBERSHIP else "manual"


def load_bundled() -> dict[str, Any]:
    return json.loads(BUNDLED.read_text(encoding="utf-8"))


def import_preview_config(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("unsupported_schema")
    if data.get("production_enabled") or data.get("real_tracking_enabled"):
        raise ValueError("preview_config_must_not_enable_production")

    placements = {p["key"]: p for p in store.list_placements()}
    for slot in data.get("ad_slots") or []:
        key = str(slot.get("id") or "")
        formats = [f for f in slot.get("supported_formats") or [] if f in store.SIZES]
        if key not in placements or not formats:
            continue
        wide = [f for f in formats if store.SIZES[f][0] > 320]
        narrow = [f for f in formats if store.SIZES[f][0] <= 320]
        sizes = {"phone": narrow, "tablet": wide or narrow, "desktop": wide or narrow}
        store.upsert_placement({**placements[key], "sizes": sizes})

    existing = {a["awin_id"]: a for a in store.list_advertisers() if a["awin_id"]}
    creatives = store.list_creatives()
    imported = []
    for item in data.get("candidate_advertisers") or []:
        try:
            awin_id = int(item["advertiser_id"])
        except (KeyError, TypeError, ValueError):
            continue
        region = str(item.get("target_region") or "").upper()[:2]
        notes = (f"Awin check {data.get('source', '')}: EPC {item.get('epc_from_awin')}, "
                 f"CR {item.get('conversion_rate_from_awin_percent')}%, site {item.get('website', '')}; "
                 f"official creative: {'yes' if item.get('official_creative_available') else 'no'}")
        current = existing.get(awin_id)
        advertiser_id = store.save_advertiser({
            "id": current["id"] if current else None,
            "name": str(item.get("name") or f"Awin {awin_id}")[:200],
            "awin_id": awin_id,
            # Enabled only so the admin preview can show it; LIVE additionally
            # needs membership "joined" and non-preview official material.
            "enabled": True,
            "countries": current["countries"] if current and current["countries"] else ([region] if region else []),
            "languages": current["languages"] if current else [],
            "topics": current["topics"] if current and current["topics"] else _TOPIC_HINTS.get(awin_id, []),
            "notes": notes[:500],
            "membership_status": _membership(item.get("membership_status")),
        })
        headline = str(item.get("preview_headline_ru") or "").strip()[:80]
        if headline:
            same = next((c for c in creatives if c["advertiser_id"] == advertiser_id and c["preview_only"]), None)
            store.save_creative({
                "id": same["id"] if same else None,
                "advertiser_id": advertiser_id, "name": f"Preview · {item.get('name', '')}"[:200], "kind": "text",
                "headline": headline, "body": str(item.get("preview_description_ru") or "").strip()[:160],
                "cta": "", "languages": ["ru"], "enabled": True, "preview_only": True,
            })
        imported.append(awin_id)

    if store.get_settings()["mode"] == store.MODE_OFF and str(data.get("mode", "")).lower() == store.MODE_PREVIEW:
        store.save_settings({"mode": store.MODE_PREVIEW})
    return {"imported": imported, "mode": store.get_settings()["mode"]}
