from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import client_config
from app.routers import approvals, audit_logs, auth, chat, runs, tools, workspace


def create_app() -> FastAPI:
    app = FastAPI(title="Velaris AI API", version="0.1.0")

    cors_origins = client_config.get("cors_origins", ["http://localhost:3000"])
    if "http://localhost:3000" not in cors_origins:
        cors_origins.append("http://localhost:3000")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(chat.router, prefix="/chat", tags=["chat"])
    app.include_router(runs.router, prefix="/runs", tags=["runs"])
    app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
    app.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
    app.include_router(tools.router, prefix="/tools", tags=["tools"])
    app.include_router(workspace.router, prefix="/workspace", tags=["workspace"])

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
