"""/health, /ready checks — DB, cache, disk space."""

import shutil
from typing import Any

from sqlalchemy import text

from backend.core.config import get_settings
from backend.infrastructure.db import async_session_factory
from backend.infrastructure.redis_client import get_cache


async def check_database() -> str:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


async def check_cache() -> str:
    try:
        cache = await get_cache()
        await cache.ping()
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def check_disk_space() -> str:
    settings = get_settings()
    try:
        usage = shutil.disk_usage(".")
        free_mb = usage.free / (1024 * 1024)
        if free_mb < 200:
            return f"low: {free_mb:.0f}MB free"
        return f"ok: {free_mb:.0f}MB free"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    finally:
        _ = settings


def check_vector_store() -> str:
    try:
        from backend.rag.embeddings import get_embedder

        get_embedder()
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"degraded: {exc}"


async def readiness_checks() -> dict[str, Any]:
    checks = {
        "database": await check_database(),
        "cache": await check_cache(),
        "disk": check_disk_space(),
        "vector_store": check_vector_store(),
    }
    ready = all(v.startswith("ok") for v in checks.values())
    return {"ready": ready, "checks": checks}
