"""Seed inicial: crea el superusuario administrador si no existe."""
from __future__ import annotations

import logging

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.enums import UserRole
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)


async def seed_superuser() -> None:
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        existing = await repo.get_by_email(settings.FIRST_SUPERUSER_EMAIL)
        if existing:
            return
        await repo.create(
            email=settings.FIRST_SUPERUSER_EMAIL,
            full_name=settings.FIRST_SUPERUSER_NAME,
            role=UserRole.ADMIN,
            is_active=True,
            hashed_password=hash_password(settings.FIRST_SUPERUSER_PASSWORD),
        )
        await session.commit()
        logger.info("Superusuario creado: %s", settings.FIRST_SUPERUSER_EMAIL)
