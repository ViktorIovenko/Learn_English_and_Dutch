from __future__ import annotations

import os


INTERNAL_API_URL = os.getenv("MCP_INTERNAL_API_URL", "http://learn-words:7001").rstrip("/")
INTERNAL_TOKEN = os.getenv("MCP_INTERNAL_TOKEN", "")
PUBLIC_MCP_URL = os.getenv("MCP_PUBLIC_URL", "https://learn.iovenko.eu/mcp").rstrip("/")
ISSUER_URL = os.getenv("MCP_ISSUER_URL", "https://learn.iovenko.eu").rstrip("/")
ALLOWED_HOST = os.getenv("MCP_ALLOWED_HOST", "learn.iovenko.eu")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("MCP_REQUEST_TIMEOUT_SECONDS", "20"))
# "Complete" lesson scenarios may call the cloud provider several times.
LONG_REQUEST_TIMEOUT_SECONDS = float(os.getenv("MCP_LONG_REQUEST_TIMEOUT_SECONDS", "90"))
MAX_FILE_BYTES = int(os.getenv("MCP_MAX_FILE_BYTES", str(5 * 1024 * 1024)))
REDIS_URL = os.getenv("MCP_REDIS_URL", "redis://mcp-redis:6379/0")
RATE_LIMIT_PER_MINUTE = int(os.getenv("MCP_RATE_LIMIT_PER_MINUTE", "120"))
VERSION = os.getenv("MCP_CONNECTOR_VERSION", "1.0.0")
