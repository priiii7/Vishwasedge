"""FastAPI app factory + lifespan management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response

from backend.api.middleware import register_middleware
from backend.api.routes import auth_router, documents_router, query_router, system_router
from backend.api.websocket import stream_router
from backend.core.config import get_settings
from backend.core.logging import configure_logging, get_logger
from backend.core.metrics import metrics_response
from backend.infrastructure.db import init_db
from backend.infrastructure.health import readiness_checks

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("startup", app=settings.app_name, version=settings.app_version, env=settings.environment)

    await init_db()

    try:
        from backend.rag.embeddings import get_embedder

        get_embedder()
    except Exception as exc:  # noqa: BLE001
        logger.warning("embedder_preload_failed", error=str(exc))

    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    register_middleware(app)

    app.include_router(auth_router)
    app.include_router(documents_router)
    app.include_router(query_router)
    app.include_router(system_router)
    app.include_router(stream_router)

    @app.get("/health", tags=["monitoring"])
    async def health() -> dict:
        from datetime import UTC, datetime

        return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}

    @app.get("/ready", tags=["monitoring"])
    async def ready() -> dict:
        return await readiness_checks()

    @app.get("/metrics", tags=["monitoring"])
    async def metrics() -> Response:
        if not settings.enable_metrics:
            return Response(status_code=404)
        body, content_type = metrics_response()
        return Response(content=body, media_type=content_type)

    return app


app = create_app()
