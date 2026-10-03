from __future__ import annotations

import uuid
from typing import Any

import httpx

from mcp_gateway import config


class InternalApiError(RuntimeError):
    def __init__(self, payload: dict[str, Any], status_code: int):
        error = payload.get("error") if isinstance(payload, dict) else None
        message = error.get("message") if isinstance(error, dict) else "internal API request failed"
        super().__init__(str(message))
        self.payload = payload
        self.status_code = status_code


def _headers(access_token: str, request_id: str | None = None) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {config.INTERNAL_TOKEN}",
        "X-MCP-Access-Token": access_token,
        "X-Request-ID": request_id or str(uuid.uuid4()),
    }


async def resolve_token(access_token: str) -> dict[str, Any] | None:
    if not config.INTERNAL_TOKEN:
        return None
    try:
        async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{config.INTERNAL_API_URL}/api/internal/mcp/resolve",
                headers=_headers(access_token),
            )
        data = response.json()
    except (httpx.HTTPError, ValueError):
        return None
    if response.status_code != 200 or not data.get("ok"):
        return None
    return data.get("grant")


async def execute(access_token: str, operation: str, params: dict[str, Any] | None = None, *, timeout: float | None = None) -> dict[str, Any]:
    request_id = str(uuid.uuid4())
    async with httpx.AsyncClient(timeout=timeout or config.REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"{config.INTERNAL_API_URL}/api/internal/mcp/execute",
            headers=_headers(access_token, request_id),
            json={"operation": operation, "params": params or {}, "request_id": request_id},
        )
    try:
        payload = response.json()
    except ValueError:
        payload = {"ok": False, "error": {"code": "BAD_INTERNAL_RESPONSE", "message": "internal API returned invalid JSON"}}
    if response.status_code >= 400 or not payload.get("ok"):
        raise InternalApiError(payload, response.status_code)
    return payload


async def health() -> dict[str, Any]:
    if not config.INTERNAL_TOKEN:
        return {"ok": False, "internal_api": "not_configured"}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                f"{config.INTERNAL_API_URL}/api/internal/mcp/health",
                headers={"Authorization": f"Bearer {config.INTERNAL_TOKEN}"},
            )
        return {"ok": response.status_code == 200, "internal_api": "ok" if response.status_code == 200 else "error"}
    except httpx.HTTPError:
        return {"ok": False, "internal_api": "unreachable"}
