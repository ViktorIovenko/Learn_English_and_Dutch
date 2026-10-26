"""Tariff model (Free / Premium / Family) and the admin preview switch.

The real entitlement of a user is derived from the existing
``user_subscriptions`` row, admin IDs and family links; nothing here writes
to the database. The admin preview lives only in the admin's own Flask
session, so it never changes real rights, subscriptions or other users.
"""
from __future__ import annotations

from typing import Any

from config import Config

PLAN_FREE = "free"
PLAN_PREMIUM = "premium"
PLAN_FAMILY = "family"
PLAN_ADMIN = "admin"
PREVIEW_PLANS = (PLAN_FREE, PLAN_PREMIUM, PLAN_FAMILY)

MAX_FAMILY_CHILDREN = 4

PREVIEW_SESSION_KEY = "plan_preview"
PREVIEW_ADS_SESSION_KEY = "plan_preview_ads"

# Single feature matrix shared by the server checks, /api/me and the UI.
PLANS: dict[str, dict[str, Any]] = {
    PLAN_FREE: {
        "price_eur": 0,
        "learning": True,
        "manual_words": True,
        "exercises": True,
        "mcp": True,
        "ads": True,
        "ai_paid": False,
        "family": False,
        "max_children": 0,
    },
    PLAN_PREMIUM: {
        "price_eur": 4.99,
        "learning": True,
        "manual_words": True,
        "exercises": True,
        "mcp": True,
        "ads": False,
        "ai_paid": True,
        "family": False,
        "max_children": 0,
    },
    PLAN_FAMILY: {
        "price_eur": 9.99,
        "learning": True,
        "manual_words": True,
        "exercises": True,
        "mcp": True,
        "ads": False,
        "ai_paid": True,
        "family": True,
        "max_children": MAX_FAMILY_CHILDREN,
    },
}
PLANS[PLAN_ADMIN] = {**PLANS[PLAN_FAMILY], "max_children": None}


def ai_daily_limit(plan: str) -> int | None:
    """Configured daily paid-AI request limit; None means unlimited (admin)."""
    if plan == PLAN_ADMIN:
        return None
    return {
        PLAN_FREE: Config.AI_DAILY_LIMIT_FREE,
        PLAN_PREMIUM: Config.AI_DAILY_LIMIT_PREMIUM,
        PLAN_FAMILY: Config.AI_DAILY_LIMIT_FAMILY,
    }.get(plan, 0)


def plan_from_subscription(subscription: dict[str, Any]) -> str:
    """Map the stored subscription state to a tariff without changing it."""
    if subscription.get("is_admin"):
        return PLAN_ADMIN
    status = subscription.get("status")
    if status == "active":
        return PLAN_FAMILY if subscription.get("plan") == PLAN_FAMILY else PLAN_PREMIUM
    if status == "trial":
        # The existing 14-day trial unlocks Premium; when it ends the user
        # stays on Free and keeps all learning data and progress.
        return PLAN_PREMIUM
    return PLAN_FREE


def preview_plan(session: Any, is_real_admin: bool) -> str:
    """Return the previewed plan, honoured only for a real admin session."""
    if not is_real_admin:
        return ""
    value = str(session.get(PREVIEW_SESSION_KEY) or "")
    return value if value in PREVIEW_PLANS else ""


def set_preview(session: Any, plan: str, show_ads: bool | None = None) -> None:
    if plan in PREVIEW_PLANS:
        session[PREVIEW_SESSION_KEY] = plan
        if show_ads is not None:
            session[PREVIEW_ADS_SESSION_KEY] = bool(show_ads)
        else:
            session.setdefault(PREVIEW_ADS_SESSION_KEY, True)
    else:
        session.pop(PREVIEW_SESSION_KEY, None)
        session.pop(PREVIEW_ADS_SESSION_KEY, None)


def enforced(preview: str) -> bool:
    """Tariff limits apply in admin preview, or globally once enabled."""
    return bool(preview) or bool(Config.ENFORCE_PLAN_LIMITS)


def entitlements(plan: str, *, preview: str = "", preview_ads: bool = False) -> dict[str, Any]:
    """Public, serialisable description of what the effective plan allows."""
    effective = preview or plan
    features = dict(PLANS.get(effective, PLANS[PLAN_FREE]))
    if preview:
        ads_visible = bool(features["ads"] and preview_ads)
    else:
        ads_visible = bool(features["ads"] and Config.ADS_ENABLED)
    return {
        "plan": effective,
        "real_plan": plan,
        "preview": preview or None,
        "enforced": enforced(preview),
        "features": features,
        "ads_visible": ads_visible,
        "ads_mode": "preview" if ads_visible else "off",
        "paid_ai_globally_enabled": bool(Config.PAID_AI_ENABLED),
        "paid_ai_available": bool(Config.PAID_AI_ENABLED and features["ai_paid"]),
        "ai_daily_limit": ai_daily_limit(effective),
        "upgrade_to": (
            PLAN_PREMIUM if effective == PLAN_FREE
            else PLAN_FAMILY if effective == PLAN_PREMIUM
            else None
        ),
    }
