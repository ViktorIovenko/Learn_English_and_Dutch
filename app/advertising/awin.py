"""Server-side client for the official Awin Publisher API.

Documented endpoints only (https://help.awin.com/apidocs):
  GET  /publishers/{id}/programmes?relationship=...&countryCode=...
  GET  /publishers/{id}/programmedetails?advertiserId=...&relationship=...
  POST /publishers/{id}/linkbuilder/generate
  GET  /publishers/{id}/reports/creative?startDate&endDate&region&timezone

The token comes from AWIN_API_TOKEN and is sent only in the Authorization
header (never in URLs or logs). Requests carry no user data: no user id,
words, learning statistics or personal information is ever sent to Awin.
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from typing import Any, Callable
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlencode

from config import Config
from app.advertising import store

RELATIONSHIPS = ("joined", "pending", "suspended", "rejected", "notjoined")
REPORT_REGIONS = ("AT", "AU", "BE", "BR", "CA", "CH", "DE", "DK", "ES", "FI", "FR", "GB", "IE", "IT",
                  "NL", "NO", "PL", "SE", "US")
_CLICKREF_RE = re.compile(r"^[a-z0-9_-]{1,50}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Awin allows 20 API calls per minute per user; stay below it locally.
RATE_LIMIT_PER_MINUTE = 18


class AwinError(Exception):
    def __init__(self, code: str, http_status: int = 0, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.http_status = http_status
        self.detail = detail


class AwinClient:
    def __init__(
        self,
        token: str | None = None,
        publisher_id: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        opener: Callable[..., Any] | None = None,
    ):
        self.token = (Config.AWIN_API_TOKEN if token is None else token).strip()
        self.publisher_id = str(Config.AWIN_PUBLISHER_ID if publisher_id is None else publisher_id).strip()
        self.base_url = (base_url or Config.AWIN_API_BASE).rstrip("/")
        self.timeout = timeout or Config.AWIN_API_TIMEOUT
        self._open = opener or urlrequest.urlopen

    _calls: deque = deque()
    _lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return bool(self.token and self.publisher_id.isdigit())

    def _throttle(self) -> None:
        now = time.monotonic()
        with AwinClient._lock:
            while AwinClient._calls and now - AwinClient._calls[0] > 60:
                AwinClient._calls.popleft()
            if len(AwinClient._calls) >= RATE_LIMIT_PER_MINUTE:
                raise AwinError("rate_limited_locally")
            AwinClient._calls.append(now)

    def _request(self, operation: str, method: str, path: str,
                 params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> Any:
        if not self.configured:
            store.log_api(operation, False, 0, "not_configured: AWIN_API_TOKEN / AWIN_PUBLISHER_ID")
            raise AwinError("not_configured")
        try:
            self._throttle()
        except AwinError as exc:
            store.log_api(operation, False, 0, exc.code)
            raise
        url = f"{self.base_url}/publishers/{self.publisher_id}{path}"
        if params:
            url += "?" + urlencode({k: v for k, v in params.items() if v not in (None, "")})
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urlrequest.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            **({"Content-Type": "application/json"} if data is not None else {}),
        })
        try:
            with self._open(req, timeout=self.timeout) as resp:
                status = getattr(resp, "status", 200)
                payload = json.loads(resp.read().decode("utf-8") or "null")
        except urlerror.HTTPError as exc:
            detail = self._error_detail(exc)
            store.log_api(operation, False, exc.code, detail)
            raise AwinError("http_error", exc.code, detail) from None
        except (urlerror.URLError, TimeoutError, OSError) as exc:
            store.log_api(operation, False, 0, f"network: {type(exc).__name__}")
            raise AwinError("network_error") from None
        except ValueError:
            store.log_api(operation, False, 0, "invalid_json")
            raise AwinError("invalid_response") from None
        store.log_api(operation, True, status, "")
        return payload

    def _error_detail(self, exc: urlerror.HTTPError) -> str:
        try:
            text = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            text = ""
        return text.replace(self.token, "***") if self.token else text

    # ---------------------------------------------------------------- calls

    def programmes(self, relationship: str = "joined", country_code: str = "") -> list[dict[str, Any]]:
        if relationship not in RELATIONSHIPS:
            raise AwinError("invalid_relationship")
        result = self._request("programmes", "GET", "/programmes", {
            "relationship": relationship,
            "countryCode": country_code.upper()[:2] if country_code else None,
        })
        return result if isinstance(result, list) else []

    def programme_details(self, advertiser_id: int, relationship: str = "any") -> dict[str, Any]:
        if relationship not in RELATIONSHIPS + ("any",):
            raise AwinError("invalid_relationship")
        result = self._request("programmedetails", "GET", "/programmedetails", {
            "advertiserId": int(advertiser_id), "relationship": relationship,
        })
        return result if isinstance(result, dict) else {}

    def generate_link(self, advertiser_id: int, destination_url: str = "",
                      clickref: str = "", shorten: bool = False) -> dict[str, Any]:
        body: dict[str, Any] = {"advertiserId": int(advertiser_id), "shorten": bool(shorten)}
        if destination_url:
            body["destinationUrl"] = destination_url
        if clickref:
            # Only a placement key may be used as clickref, never user data.
            if not _CLICKREF_RE.match(clickref):
                raise AwinError("invalid_clickref")
            body["parameters"] = {"clickref": clickref}
        result = self._request("linkbuilder", "POST", "/linkbuilder/generate", body=body)
        if not isinstance(result, dict) or not result.get("url"):
            store.log_api("linkbuilder", False, 0, "no_url_in_response")
            raise AwinError("invalid_response")
        return result

    def creative_report(self, start: str, end: str, region: str, timezone: str = "UTC") -> list[dict[str, Any]]:
        if not (_DATE_RE.match(start or "") and _DATE_RE.match(end or "")):
            raise AwinError("invalid_dates")
        if region not in REPORT_REGIONS:
            raise AwinError("invalid_region")
        result = self._request("report_creative", "GET", "/reports/creative", {
            "startDate": start, "endDate": end, "region": region, "timezone": timezone,
        })
        return result if isinstance(result, list) else []


def membership_from_details(details: dict[str, Any]) -> str:
    info = details.get("programmeInfo") or {}
    status = str(info.get("membershipStatus") or "").strip().lower().replace(" ", "")
    return status if status in RELATIONSHIPS else ""
