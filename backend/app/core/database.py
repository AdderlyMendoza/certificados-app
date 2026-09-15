"""Configuración de la base de datos (SQLAlchemy 2.0 async + MySQL).

Expone el engine async, la factoría de sesiones y la dependencia
`get_db` que se inyecta en los endpoints/servicios.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Engine async principal (asyncmy)
engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    echo=settings.DEBUG,
    pool_pre_ping=True,      # evita conexiones muertas de MySQL ("server has gone away")
    pool_recycle=3600,       # recicla conexiones cada hora
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_models() -> None:
    """Crea las tablas si no existen (cómodo en desarrollo).

    En producción usa las migraciones de Alembic (`alembic upgrade head`).
    """
    from app.models import Base  # import local para evitar ciclos

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia FastAPI: una sesión por request, con commit/rollback automático."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
