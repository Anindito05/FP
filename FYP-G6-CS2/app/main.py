"""FastAPI application factory and health endpoints."""
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from .config import get_settings
from .database import get_db, check_db_health, dispose_engine

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize optional inference resources and dispose database engine."""
    from .prompts import get_prompt
    for name in ("analysis.v1.md","companion.v1.md","gentle_checkin.v1.md","helpline_extract.v1.md","nearby_extract.v1.md"):
        get_prompt(name)
    app.state.models_ready = True
    yield
    await dispose_engine()

async def health_live() -> dict:
    """Liveness probe. Incoming: none. Outgoing: status."""
    return {"status": "ok"}

async def health_ready(db: AsyncSession = Depends(get_db)) -> dict:
    """Readiness probe. Incoming: db. Outgoing: component status."""
    ok = await check_db_health(db)
    from .llm import build_llm_client
    llm_ok=False
    try:
        await build_llm_client(get_settings()).generate([{"role":"user","content":"Reply OK"}],2,0)
        llm_ok=True
    except Exception: pass
    degraded=not llm_ok
    return {"status": "ok" if ok else "not_ready", "database": ok, "llm_reachable":llm_ok, "analysis_mode":"degraded" if degraded else "normal"}

def create_app() -> FastAPI:
    """Build versioned API. Incoming: none. Outgoing: FastAPI."""
    settings = get_settings()
    app = FastAPI(title="Mental Wellness Support API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])
    @app.get("/api/v1/health/live")
    async def live() -> dict: return await health_live()
    @app.get("/api/v1/health/ready")
    async def ready(db: AsyncSession = Depends(get_db)) -> dict: return await health_ready(db)
    from .routers import auth, chat, resources, admin
    for router in (auth.router, chat.router, resources.router, admin.router):
        app.include_router(router, prefix="/api/v1")
    return app
