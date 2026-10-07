"""Async Redis connection pool with graceful in-memory LRU fallback.

Per the spec's own resilience requirement: if Redis is unavailable, degrade
to an in-memory LRU cache rather than failing. We make that the default
(REDIS_URL unset) rather than something that only kicks in on error.
"""

from collections import OrderedDict
from typing import Any

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class InMemoryLRUCache:
    def __init__(self, max_items: int = 2000):
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._max_items = max_items

    async def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:  # noqa: ARG002
        self._store[key] = value
        self._store.move_to_end(key)
        if len(self._store) > self._max_items:
            self._store.popitem(last=False)

    async def ping(self) -> bool:
        return True


class RedisCacheAdapter:
    def __init__(self, client: Any):
        self._client = client

    async def get(self, key: str) -> Any | None:
        return await self._client.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self._client.set(key, value, ex=ttl)

    async def ping(self) -> bool:
        return bool(await self._client.ping())


_cache_singleton: InMemoryLRUCache | RedisCacheAdapter | None = None


async def get_cache() -> InMemoryLRUCache | RedisCacheAdapter:
    global _cache_singleton
    if _cache_singleton is not None:
        return _cache_singleton

    settings = get_settings()
    if settings.redis_url:
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(settings.redis_url, decode_responses=True)
            await client.ping()
            _cache_singleton = RedisCacheAdapter(client)
            logger.info("cache_backend", backend="redis")
            return _cache_singleton
        except Exception as exc:  # noqa: BLE001
            logger.warning("redis_unavailable_falling_back", error=str(exc))

    _cache_singleton = InMemoryLRUCache(max_items=settings.cache_size_mb * 4)
    logger.info("cache_backend", backend="in_memory_lru")
    return _cache_singleton
