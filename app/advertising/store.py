"""SQLite storage of the advertising module.

Only advertising configuration and aggregated, anonymous counters live here:
no user id, no learning data and no request metadata is ever stored.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import closing
from datetime import date
from typing import Any

from config import Config

MODE_OFF = "off"
MODE_PREVIEW = "preview"
MODE_LIVE = "live"
MODES = (MODE_OFF, MODE_PREVIEW, MODE_LIVE)

DEVICES = ("phone", "tablet", "desktop")
SIZES: dict[str, tuple[int, int]] = {
    "320x50": (320, 50),
    "320x100": (320, 100),
    "300x250": (300, 250),
    "728x90": (728, 90),
    "970x250": (970, 250),
}
PLATFORMS = ("web", "telegram", "android")
KINDS = ("awin_html", "image_link", "text")
MEMBERSHIP = ("manual", "joined", "pending", "suspended", "rejected", "notjoined")
TOPICS = ("language", "education", "books", "travel", "kids", "software", "other")

DEFAULT_SETTINGS: dict[str, Any] = {
    "mode": MODE_OFF,
    "max_per_page": 1,
    # Owner decision 2026-10-09: Free ads on every client (web, Mini App, Android).
    "live_platforms": ["web", "telegram", "android"],
    # An expired *paid* subscription is not Free automatically.
    "lapsed_paid_as_free": False,
    "preferred_topics": ["language", "education", "books"],
    "demo_creatives": True,
    # Admins see mock-ups in every slot without the Free tariff simulation.
    "admin_demo_always": False,
}

# Initially only one demo banner per screen: the bottom slots are enabled,
# the top/between ones are prepared but switched off.
DEFAULT_PLACEMENTS: tuple[dict[str, Any], ...] = (
    {"key": "dashboard_top", "page": "dashboard", "label": "Под навигацией", "enabled": False, "priority": 20,
     "sizes": {"phone": ["320x100"], "tablet": ["728x90"], "desktop": ["728x90"]}},
    {"key": "dashboard_between", "page": "dashboard", "label": "Между блоками уроков", "enabled": False, "priority": 30,
     "sizes": {"phone": ["300x250", "320x100"], "tablet": ["300x250", "320x100"], "desktop": ["300x250"]}},
    {"key": "dashboard_bottom", "page": "dashboard", "label": "Низ главной", "enabled": True, "priority": 10,
     "sizes": {"phone": ["320x50"], "tablet": ["728x90"], "desktop": ["728x90"]}},
    {"key": "lesson_bottom", "page": "lesson", "label": "Под навигацией урока (маленький)", "enabled": True, "priority": 10,
     "sizes": {"phone": ["320x50"], "tablet": ["320x50"], "desktop": ["728x90"]}},
    {"key": "secondary_bottom", "page": "secondary", "label": "Низ второстепенных страниц", "enabled": True, "priority": 10,
     "sizes": {"phone": ["320x100", "320x50"], "tablet": ["728x90"], "desktop": ["728x90"]}},
)
BUILTIN_PLACEMENTS = tuple(item["key"] for item in DEFAULT_PLACEMENTS)

_schema_lock = threading.Lock()
_schema_ready: set[str] = set()


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    path = str(Config.DB_PATH)
    if path in _schema_ready:
        return
    with _schema_lock:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS ad_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL,
                updated_at INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS ad_placements (
                key TEXT PRIMARY KEY,
                page TEXT NOT NULL,
                label TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 0,
                priority INTEGER NOT NULL DEFAULT 50,
                sizes TEXT NOT NULL DEFAULT '{}',
                builtin INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS ad_advertisers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                awin_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                membership_status TEXT NOT NULL DEFAULT 'manual',
                enabled INTEGER NOT NULL DEFAULT 0,
                countries TEXT NOT NULL DEFAULT '[]',
                languages TEXT NOT NULL DEFAULT '[]',
                topics TEXT NOT NULL DEFAULT '[]',
                primary_region TEXT NOT NULL DEFAULT '',
                valid_domains TEXT NOT NULL DEFAULT '[]',
                logo_url TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                synced_at INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS ad_creatives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                advertiser_id INTEGER NOT NULL REFERENCES ad_advertisers(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                click_url TEXT NOT NULL DEFAULT '',
                image_url TEXT NOT NULL DEFAULT '',
                alt TEXT NOT NULL DEFAULT '',
                headline TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                cta TEXT NOT NULL DEFAULT '',
                raw_code TEXT NOT NULL DEFAULT '',
                countries TEXT NOT NULL DEFAULT '[]',
                languages TEXT NOT NULL DEFAULT '[]',
                topics TEXT NOT NULL DEFAULT '[]',
                enabled INTEGER NOT NULL DEFAULT 0,
                -- Unofficial copy for admin preview; never served in LIVE.
                preview_only INTEGER NOT NULL DEFAULT 0,
                starts_on TEXT NOT NULL DEFAULT '',
                ends_on TEXT NOT NULL DEFAULT '',
                created_at INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS ad_stats (
                day TEXT NOT NULL,
                placement TEXT NOT NULL,
                creative_id INTEGER NOT NULL,
                device TEXT NOT NULL,
                country TEXT NOT NULL,
                event TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (day, placement, creative_id, device, country, event)
            );
            -- Consent of app clients without cookies (Android). Web keeps
            -- the choice in its own first-party cookie only.
            CREATE TABLE IF NOT EXISTS ad_consent (
                user_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY (user_id, platform)
            );
            CREATE TABLE IF NOT EXISTS ad_api_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                at INTEGER NOT NULL,
                operation TEXT NOT NULL,
                http_status INTEGER NOT NULL DEFAULT 0,
                ok INTEGER NOT NULL DEFAULT 0,
                message TEXT NOT NULL DEFAULT ''
            );
        """)
        conn.execute(
            "INSERT OR IGNORE INTO ad_settings (id, data, updated_at) VALUES (1, ?, 0)",
            (json.dumps(DEFAULT_SETTINGS),),
        )
        for item in DEFAULT_PLACEMENTS:
            conn.execute(
                "INSERT OR IGNORE INTO ad_placements (key, page, label, enabled, priority, sizes, builtin) "
                "VALUES (?, ?, ?, ?, ?, ?, 1)",
                (item["key"], item["page"], item["label"], int(item["enabled"]), item["priority"],
                 json.dumps(item["sizes"])),
            )
        conn.commit()
        _schema_ready.add(path)


def reset_schema_cache() -> None:
    """Tests switch Config.DB_PATH between temporary databases."""
    _schema_ready.clear()


def _now() -> int:
    return int(time.time() * 1000)


def _loads(value: Any, default: Any) -> Any:
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError):
        return default
    return parsed if isinstance(parsed, type(default)) else default


# ---------------------------------------------------------------- settings

def get_settings() -> dict[str, Any]:
    with closing(connect()) as conn:
        row = conn.execute("SELECT data FROM ad_settings WHERE id = 1").fetchone()
    data = {**DEFAULT_SETTINGS, **_loads(row["data"] if row else "{}", {})}
    if data.get("mode") not in MODES:
        data["mode"] = MODE_OFF  # fail closed on a corrupted value
    return data


def save_settings(values: dict[str, Any]) -> dict[str, Any]:
    data = {**get_settings(), **values}
    with closing(connect()) as conn:
        conn.execute("UPDATE ad_settings SET data = ?, updated_at = ? WHERE id = 1", (json.dumps(data), _now()))
        conn.commit()
    return data


# -------------------------------------------------------------- placements

def _placement(row: sqlite3.Row) -> dict[str, Any]:
    sizes = _loads(row["sizes"], {})
    return {
        "key": row["key"],
        "page": row["page"],
        "label": row["label"],
        "enabled": bool(row["enabled"]),
        "priority": int(row["priority"]),
        "sizes": {device: [s for s in sizes.get(device, []) if s in SIZES] for device in DEVICES},
        "builtin": bool(row["builtin"]),
    }


def list_placements(page: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM ad_placements"
    params: tuple = ()
    if page:
        query += " WHERE page = ?"
        params = (page,)
    with closing(connect()) as conn:
        rows = conn.execute(query + " ORDER BY priority, key", params).fetchall()
    return [_placement(row) for row in rows]


def upsert_placement(item: dict[str, Any]) -> None:
    with closing(connect()) as conn:
        conn.execute("""
            INSERT INTO ad_placements (key, page, label, enabled, priority, sizes, builtin)
            VALUES (:key, :page, :label, :enabled, :priority, :sizes, 0)
            ON CONFLICT(key) DO UPDATE SET
                page = excluded.page, label = excluded.label, enabled = excluded.enabled,
                priority = excluded.priority, sizes = excluded.sizes
        """, {**item, "enabled": int(bool(item["enabled"])), "sizes": json.dumps(item["sizes"])})
        conn.commit()


def delete_placement(key: str) -> bool:
    with closing(connect()) as conn:
        cur = conn.execute("DELETE FROM ad_placements WHERE key = ? AND builtin = 0", (key,))
        conn.commit()
    return cur.rowcount > 0


# ------------------------------------------------------------- advertisers

def _advertiser(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "awin_id": row["awin_id"],
        "name": row["name"],
        "membership_status": row["membership_status"],
        "enabled": bool(row["enabled"]),
        "countries": _loads(row["countries"], []),
        "languages": _loads(row["languages"], []),
        "topics": _loads(row["topics"], []),
        "primary_region": row["primary_region"],
        "valid_domains": _loads(row["valid_domains"], []),
        "logo_url": row["logo_url"],
        "notes": row["notes"],
        "synced_at": int(row["synced_at"] or 0),
    }


def list_advertisers() -> list[dict[str, Any]]:
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM ad_advertisers ORDER BY name COLLATE NOCASE").fetchall()
    return [_advertiser(row) for row in rows]


def get_advertiser(advertiser_id: int) -> dict[str, Any] | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM ad_advertisers WHERE id = ?", (int(advertiser_id),)).fetchone()
    return _advertiser(row) if row else None


def save_advertiser(item: dict[str, Any]) -> int:
    """Insert or update an advertiser managed by the admin."""
    payload = {
        "name": item["name"],
        "awin_id": item.get("awin_id"),
        "enabled": int(bool(item.get("enabled"))),
        "countries": json.dumps(item.get("countries") or []),
        "languages": json.dumps(item.get("languages") or []),
        "topics": json.dumps(item.get("topics") or []),
        "notes": item.get("notes") or "",
        "membership_status": item.get("membership_status") or "manual",
    }
    with closing(connect()) as conn:
        if item.get("id"):
            conn.execute("""
                UPDATE ad_advertisers SET name=:name, awin_id=:awin_id, enabled=:enabled, countries=:countries,
                    languages=:languages, topics=:topics, notes=:notes, membership_status=:membership_status
                WHERE id=:id
            """, {**payload, "id": int(item["id"])})
            advertiser_id = int(item["id"])
        else:
            cur = conn.execute("""
                INSERT INTO ad_advertisers (name, awin_id, enabled, countries, languages, topics, notes,
                                            membership_status, created_at)
                VALUES (:name, :awin_id, :enabled, :countries, :languages, :topics, :notes, :membership_status, :now)
            """, {**payload, "now": _now()})
            advertiser_id = int(cur.lastrowid)
        conn.commit()
    return advertiser_id


def upsert_awin_programme(programme: dict[str, Any], relationship: str) -> int:
    """Store programme metadata from the Awin API; admin-set fields are kept."""
    awin_id = int(programme["id"])
    region = programme.get("primaryRegion") or {}
    domains = [d.get("domain") for d in programme.get("validDomains") or [] if isinstance(d, dict) and d.get("domain")]
    with closing(connect()) as conn:
        conn.execute("""
            INSERT INTO ad_advertisers (awin_id, name, membership_status, primary_region, valid_domains,
                                        logo_url, synced_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(awin_id) DO UPDATE SET
                name = excluded.name, membership_status = excluded.membership_status,
                primary_region = excluded.primary_region, valid_domains = excluded.valid_domains,
                logo_url = excluded.logo_url, synced_at = excluded.synced_at
        """, (awin_id, str(programme.get("name") or f"Awin {awin_id}")[:200], relationship,
              str(region.get("countryCode") or "")[:2].upper(), json.dumps(domains[:50]),
              str(programme.get("logoUrl") or "")[:500], _now(), _now()))
        row = conn.execute("SELECT id FROM ad_advertisers WHERE awin_id = ?", (awin_id,)).fetchone()
        conn.commit()
    return int(row["id"])


def set_membership(advertiser_id: int, status: str) -> None:
    with closing(connect()) as conn:
        conn.execute("UPDATE ad_advertisers SET membership_status = ?, synced_at = ? WHERE id = ?",
                     (status, _now(), int(advertiser_id)))
        conn.commit()


# --------------------------------------------------------------- creatives

def _creative(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "advertiser_id": int(row["advertiser_id"]),
        "name": row["name"],
        "kind": row["kind"],
        "width": row["width"],
        "height": row["height"],
        "click_url": row["click_url"],
        "image_url": row["image_url"],
        "alt": row["alt"],
        "headline": row["headline"],
        "body": row["body"],
        "cta": row["cta"],
        "raw_code": row["raw_code"],
        "countries": _loads(row["countries"], []),
        "languages": _loads(row["languages"], []),
        "topics": _loads(row["topics"], []),
        "enabled": bool(row["enabled"]),
        "preview_only": bool(row["preview_only"]),
        "starts_on": row["starts_on"],
        "ends_on": row["ends_on"],
    }


def list_creatives() -> list[dict[str, Any]]:
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM ad_creatives ORDER BY id DESC").fetchall()
    return [_creative(row) for row in rows]


def get_creative(creative_id: int) -> dict[str, Any] | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM ad_creatives WHERE id = ?", (int(creative_id),)).fetchone()
    return _creative(row) if row else None


_CREATIVE_FIELDS = ("advertiser_id", "name", "kind", "width", "height", "click_url", "image_url", "alt",
                    "headline", "body", "cta", "raw_code", "countries", "languages", "topics", "enabled",
                    "preview_only", "starts_on", "ends_on")


def save_creative(item: dict[str, Any]) -> int:
    payload = {key: item.get(key) for key in _CREATIVE_FIELDS}
    for key in ("countries", "languages", "topics"):
        payload[key] = json.dumps(payload[key] or [])
    for key in ("click_url", "image_url", "alt", "headline", "body", "cta", "raw_code", "starts_on", "ends_on"):
        payload[key] = payload[key] or ""
    payload["enabled"] = int(bool(payload["enabled"]))
    payload["preview_only"] = int(bool(payload["preview_only"]))
    payload["now"] = _now()
    with closing(connect()) as conn:
        if item.get("id"):
            sets = ", ".join(f"{key} = :{key}" for key in _CREATIVE_FIELDS)
            conn.execute(f"UPDATE ad_creatives SET {sets}, updated_at = :now WHERE id = :id",
                         {**payload, "id": int(item["id"])})
            creative_id = int(item["id"])
        else:
            columns = ", ".join(_CREATIVE_FIELDS)
            values = ", ".join(f":{key}" for key in _CREATIVE_FIELDS)
            cur = conn.execute(
                f"INSERT INTO ad_creatives ({columns}, created_at, updated_at) VALUES ({values}, :now, :now)",
                payload,
            )
            creative_id = int(cur.lastrowid)
        conn.commit()
    return creative_id


def set_creative_enabled(creative_id: int, enabled: bool) -> None:
    with closing(connect()) as conn:
        conn.execute("UPDATE ad_creatives SET enabled = ?, updated_at = ? WHERE id = ?",
                     (int(bool(enabled)), _now(), int(creative_id)))
        conn.commit()


def set_creative_click_url(creative_id: int, url: str) -> None:
    with closing(connect()) as conn:
        conn.execute("UPDATE ad_creatives SET click_url = ?, updated_at = ? WHERE id = ?",
                     (url, _now(), int(creative_id)))
        conn.commit()


def creative_candidates() -> list[dict[str, Any]]:
    """Creatives joined with their advertiser, for selection."""
    with closing(connect()) as conn:
        rows = conn.execute("""
            SELECT c.*, a.name AS advertiser_name, a.enabled AS advertiser_enabled,
                   a.membership_status AS advertiser_membership, a.countries AS advertiser_countries,
                   a.languages AS advertiser_languages, a.topics AS advertiser_topics,
                   a.primary_region AS advertiser_region, a.awin_id AS advertiser_awin_id
            FROM ad_creatives c JOIN ad_advertisers a ON a.id = c.advertiser_id
        """).fetchall()
    result = []
    for row in rows:
        item = _creative(row)
        item.update({
            "advertiser_name": row["advertiser_name"],
            "advertiser_enabled": bool(row["advertiser_enabled"]),
            "advertiser_membership": row["advertiser_membership"],
            "advertiser_countries": _loads(row["advertiser_countries"], []),
            "advertiser_languages": _loads(row["advertiser_languages"], []),
            "advertiser_topics": _loads(row["advertiser_topics"], []),
            "advertiser_region": row["advertiser_region"],
            "advertiser_awin_id": row["advertiser_awin_id"],
        })
        result.append(item)
    return result


# ------------------------------------------------------------------- stats

def record_event(placement: str, creative_id: int, device: str, country: str, event: str) -> None:
    with closing(connect()) as conn:
        conn.execute("""
            INSERT INTO ad_stats (day, placement, creative_id, device, country, event, count)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(day, placement, creative_id, device, country, event) DO UPDATE SET count = count + 1
        """, (date.today().isoformat(), placement, int(creative_id), device, country or "--", event))
        conn.commit()


def stats_summary(days: int = 30) -> list[dict[str, Any]]:
    since = date.fromordinal(date.today().toordinal() - max(1, int(days)) + 1).isoformat()
    with closing(connect()) as conn:
        rows = conn.execute("""
            SELECT s.placement, s.creative_id, COALESCE(c.name, '') AS creative_name,
                   SUM(CASE WHEN s.event = 'impression' THEN s.count ELSE 0 END) AS impressions,
                   SUM(CASE WHEN s.event = 'click' THEN s.count ELSE 0 END) AS clicks
            FROM ad_stats s LEFT JOIN ad_creatives c ON c.id = s.creative_id
            WHERE s.day >= ?
            GROUP BY s.placement, s.creative_id
            ORDER BY impressions DESC
        """, (since,)).fetchall()
    return [dict(row) for row in rows]


# ----------------------------------------------------------------- API log

def log_api(operation: str, ok: bool, http_status: int = 0, message: str = "") -> None:
    with closing(connect()) as conn:
        conn.execute("INSERT INTO ad_api_log (at, operation, http_status, ok, message) VALUES (?, ?, ?, ?, ?)",
                     (_now(), operation[:80], int(http_status or 0), int(bool(ok)), str(message or "")[:500]))
        conn.execute("DELETE FROM ad_api_log WHERE id NOT IN (SELECT id FROM ad_api_log ORDER BY id DESC LIMIT 200)")
        conn.commit()


def api_log(limit: int = 50) -> list[dict[str, Any]]:
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM ad_api_log ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
    return [dict(row) for row in rows]


# ----------------------------------------------------------------- consent

def get_consent(user_id: str, platform: str) -> str:
    with closing(connect()) as conn:
        row = conn.execute("SELECT status FROM ad_consent WHERE user_id = ? AND platform = ?",
                           (str(user_id), platform)).fetchone()
    return row["status"] if row else "unknown"


def save_consent(user_id: str, platform: str, status: str) -> None:
    with closing(connect()) as conn:
        conn.execute("""
            INSERT INTO ad_consent (user_id, platform, status, updated_at) VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, platform) DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at
        """, (str(user_id), platform, status, _now()))
        conn.commit()
