"""Punto de entrada de la API FastAPI."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_models
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.seed import seed_superuser
from app.utils.files import ensure_dirs


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Inicialización al arrancar: logging, directorios, tablas y seed."""
    setup_logging()
    ensure_dirs()
    try:
        await init_models()
        await seed_superuser()
    except Exception:  # noqa: BLE001
        # No bloquea el arranque si la DB aún no está lista (Docker first boot)
        pass
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.APP_NAME}
