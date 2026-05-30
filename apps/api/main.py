import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import asyncio as redis_asyncio
from sqlalchemy import text

from app.config import client_config
from app.database import engine
from app.config import settings
from app.routers import approvals, audit_logs, auth, backend, chat, client_api, client_data, data_backend, runs, tools, workspace

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="Velaris AI API", version="0.1.0")

    cors_origins = settings.cors_origins or client_config.get("cors_origins", [])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(backend.router, prefix="/backend", tags=["backend-blueprints"])
    app.include_router(chat.router, prefix="/chat", tags=["chat"])
    app.include_router(runs.router, prefix="/runs", tags=["runs"])
    app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
    app.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
    app.include_router(tools.router, prefix="/tools", tags=["tools"])
    app.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
    app.include_router(client_data.router, prefix="/client-data", tags=["client-data"])
    app.include_router(data_backend.router, prefix="/data", tags=["data-backend"])
    app.include_router(client_api.router, prefix="/client-api", tags=["client-api"])

    async def _service_health() -> dict[str, str]:
        database_status = "ok"
        redis_status = "ok"
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception as exc:
            logger.warning("Database health check failed: %s", exc)
            database_status = "error"

        redis_client = redis_asyncio.from_url(settings.redis_url, decode_responses=True)
        try:
            await redis_client.ping()
        except Exception as exc:
            logger.warning("Redis health check failed: %s", exc)
            redis_status = "error"
        finally:
            await redis_client.aclose()

        status = "ok" if database_status == "ok" and redis_status == "ok" else "degraded"
        return {
            "status": status,
            "version": "0.1.0",
            "environment": settings.environment,
            "services": {"database": database_status, "redis": redis_status},
        }

    @app.get("/health")
    async def health() -> dict:
        return await _service_health()

    @app.get("/api/health")
    async def api_health() -> dict:
        return await _service_health()

    return app


app = create_app()
