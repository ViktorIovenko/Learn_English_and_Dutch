from __future__ import annotations

import hashlib
import time

from redis.asyncio import Redis

from mcp_gateway import config


_redis = Redis.from_url(config.REDIS_URL, decode_responses=True, socket_timeout=2)


async def enforce_rate_limit(access_token: str) -> None:
    window = int(time.time()) // 60
    digest = hashlib.sha256(access_token.encode("utf-8")).hexdigest()[:24]
    key = f"mcp:rate:{digest}:{window}"
    count = await _redis.incr(key)
    if count == 1:
        await _redis.expire(key, 70)
    if count > config.RATE_LIMIT_PER_MINUTE:
        raise RuntimeError("MCP rate limit exceeded; retry after the current minute")


async def redis_health() -> str:
    try:
        return "ok" if await _redis.ping() else "error"
    except Exception:
        return "unreachable"
