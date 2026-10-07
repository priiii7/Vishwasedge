"""Tiered query-result cache: Redis (if configured) + in-memory LRU fallback."""

import hashlib
import json
from typing import Any

from backend.infrastructure.redis_client import get_cache


def _key(query: str, context: dict | None) -> str:
    payload = json.dumps({"q": query, "ctx": context or {}}, sort_keys=True)
    return "query:" + hashlib.sha256(payload.encode()).hexdigest()


async def get_cached_response(query: str, context: dict | None) -> dict[str, Any] | None:
    cache = await get_cache()
    raw = await cache.get(_key(query, context))
    if raw is None:
        return None
    return json.loads(raw) if isinstance(raw, str) else raw


async def set_cached_response(query: str, context: dict | None, response: dict[str, Any], ttl: int = 300) -> None:
    cache = await get_cache()
    await cache.set(_key(query, context), json.dumps(response), ttl=ttl)
