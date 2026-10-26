"""Who may see which kind of ad. Pure functions, no I/O.

The decision is made on the server from the real subscription state; nothing
the client sends (plan, flags, headers) can widen it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.advertising.store import MODE_LIVE, MODE_OFF, MODE_PREVIEW

SERVE_NONE = "none"
SERVE_DEMO = "demo"   # local mock-ups, no external request, no tracking
SERVE_LIVE = "live"   # real Awin material, Free + consent only

CONSENT_GRANTED = "granted"
CONSENT_DENIED = "denied"
CONSENT_UNKNOWN = "unknown"

# Subscription states that really mean "Free": the 14-day trial ended and
# nothing was bought (owner decision 2026-10-09: then Free with ads on every
# client). Child profiles exist only under a paid plan and never see ads.
# A lapsed paid subscription ("expired") is opt-in via settings; any unknown
# state never shows ads.
FREE_STATUSES = frozenset({"trial_expired"})
LAPSED_PAID_STATUSES = frozenset({"expired"})


@dataclass(frozen=True)
class Viewer:
    user_id: str
    is_admin: bool = False          # real ADMIN_IDS membership, not the preview
    preview_plan: str = ""          # admin-only tariff simulation from the session
    real_plan: str = "free"         # app.plans tariff incl. Family inheritance
    subscription_status: str = ""   # effective user_subscriptions status
    account_type: str = "standard"  # standard / child / pending
    ui_language: str = "en"
    channel: str = "session"        # "session" (web / Mini App) or "app" (Android Bearer)


@dataclass(frozen=True)
class Decision:
    serve: str
    reason: str
    needs_consent: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {"serve": self.serve, "reason": self.reason, "needs_consent": self.needs_consent}


def decide(
    viewer: Viewer | None,
    settings: dict[str, Any],
    *,
    platform: str,
    consent: str,
    live_allowed: bool,
) -> Decision:
    if viewer is None or not viewer.user_id:
        return Decision(SERVE_NONE, "anonymous")
    mode = settings.get("mode", MODE_OFF)

    if viewer.is_admin:
        # The admin keeps full access; ads only appear while simulating Free
        # (or with admin_demo_always), in every mode (also OFF), and always as local mock-ups with no real
        # impression, link or external request. Nobody else is affected.
        if viewer.preview_plan == "free":
            return Decision(SERVE_DEMO, "admin_free_simulation")
        if viewer.preview_plan:
            return Decision(SERVE_NONE, "paid_plan")
        # Opt-in setting so an admin can look at every slot (also on Android,
        # which has no browser-session tariff preview) without simulating Free.
        if settings.get("admin_demo_always"):
            return Decision(SERVE_DEMO, "admin_demo_always")
        return Decision(SERVE_NONE, "admin_full_access")

    if mode == MODE_OFF:
        return Decision(SERVE_NONE, "mode_off")

    if mode == MODE_PREVIEW:
        return Decision(SERVE_NONE, "preview_admin_only")
    if mode != MODE_LIVE or not live_allowed:
        return Decision(SERVE_NONE, "live_not_allowed")

    # Children: no ads until a legal review approves it (also not for
    # pending accounts that have not chosen a type yet).
    if viewer.account_type == "child":
        return Decision(SERVE_NONE, "child_account")
    if viewer.account_type != "standard":
        return Decision(SERVE_NONE, "account_type")
    if viewer.real_plan != "free":
        return Decision(SERVE_NONE, "paid_plan")
    status = viewer.subscription_status
    if status not in FREE_STATUSES and not (
        status in LAPSED_PAID_STATUSES and settings.get("lapsed_paid_as_free")
    ):
        return Decision(SERVE_NONE, "status_not_free")
    if platform not in (settings.get("live_platforms") or []):
        return Decision(SERVE_NONE, "platform_disabled")
    if consent == CONSENT_DENIED:
        return Decision(SERVE_NONE, "consent_denied")
    if consent != CONSENT_GRANTED:
        return Decision(SERVE_NONE, "consent_required", needs_consent=True)
    return Decision(SERVE_LIVE, "free_plan")


def consent_relevant(viewer: Viewer | None, settings: dict[str, Any], live_allowed: bool) -> bool:
    """Whether the consent controls make sense for this viewer at all."""
    if viewer is None or settings.get("mode") != MODE_LIVE or not live_allowed:
        return False
    probe = decide(viewer, settings, platform="web", consent=CONSENT_UNKNOWN, live_allowed=True)
    return probe.needs_consent
