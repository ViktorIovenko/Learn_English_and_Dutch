from __future__ import annotations

import asyncio
import csv
import io
import ipaddress
import json
import socket
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from mcp_gateway import config


class FileImportError(ValueError):
    pass


async def _validate_public_https(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise FileImportError("file download_url must be an HTTPS URL")
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise FileImportError("file host could not be resolved") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise FileImportError("file URL resolves to a non-public address")


async def download_file(url: str) -> tuple[bytes, str]:
    current = url
    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
        for _ in range(4):
            await _validate_public_https(current)
            async with client.stream("GET", current, headers={"Accept": "text/csv,application/json"}) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        raise FileImportError("file redirect has no location")
                    current = urljoin(current, location)
                    continue
                response.raise_for_status()
                chunks: list[bytes] = []
                size = 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > config.MAX_FILE_BYTES:
                        raise FileImportError("file exceeds the size limit")
                    chunks.append(chunk)
                return b"".join(chunks), str(response.headers.get("content-type") or "")
    raise FileImportError("too many file redirects")


def parse_words(content: bytes, *, file_name: str = "", lesson_title: str = "") -> tuple[str, list[dict[str, str]]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FileImportError("file must be UTF-8 CSV or JSON") from exc
    stripped = text.lstrip()
    rows: list[dict[str, Any]]
    detected_lesson = lesson_title.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise FileImportError("invalid JSON file") from exc
        if isinstance(payload, dict):
            detected_lesson = detected_lesson or str(payload.get("lesson") or "").strip()
            payload = payload.get("words") or payload.get("rows")
        if not isinstance(payload, list):
            raise FileImportError("JSON must contain an array of words")
        rows = payload
    else:
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;|\t")
        except csv.Error:
            dialect = csv.excel
        rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    if not 1 <= len(rows) <= 100:
        raise FileImportError("file must contain 1 to 100 rows")
    words: list[dict[str, str]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise FileImportError(f"row {index + 1} must be an object")
        normalized = {str(key or "").strip().lower(): str(value or "").strip() for key, value in raw.items()}
        detected_lesson = detected_lesson or normalized.get("lesson", "")
        word = {key: value for key, value in normalized.items() if key in {"nl", "en", "ru", "de", "fr", "es", "it", "pt", "pl", "uk"} or key.startswith("ex_")}
        if not any(value for key, value in word.items() if not key.startswith("ex_")):
            raise FileImportError(f"row {index + 1} has no word values")
        words.append(word)
    if not detected_lesson:
        raise FileImportError("lesson_title is required: supply a meaningful title explicitly or in the file")
    if len(detected_lesson) > 200:
        raise FileImportError("lesson_title must not exceed 200 characters")
    return detected_lesson, words
