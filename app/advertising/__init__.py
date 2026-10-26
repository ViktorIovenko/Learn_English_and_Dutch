"""Advertising (Awin) for the Free plan.

Isolated from app/routes.py: routes.py only registers the module and supplies
a read-only viewer description (see ``init_advertising``). Modes:

* OFF     – default; no script, no request, nothing rendered.
* PREVIEW – local demo banners for the admin's Free simulation only.
* LIVE    – approved Awin material for Free users with consent; requires
            ADS_LIVE_ALLOWED=1, Awin credentials and an explicit admin switch.
"""
from __future__ import annotations

from typing import Callable

from flask import Flask

from app.advertising.policy import Viewer
from app.advertising.views import ads_bp, set_viewer_provider, template_context


def init_advertising(app: Flask, viewer_provider: Callable[[], Viewer | None]) -> None:
    set_viewer_provider(viewer_provider)
    app.register_blueprint(ads_bp)
    app.context_processor(template_context)


__all__ = ["Viewer", "init_advertising"]
