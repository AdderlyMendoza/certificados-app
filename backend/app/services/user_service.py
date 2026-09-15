"""Servicio de gestión de usuarios."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)

    async def get(self, user_id: int) -> User:
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        return user

    async def list(self, *, offset: int, limit: int) -> tuple[list[User], int]:
        items = await self.users.list(offset=offset, limit=limit)
        total = await self.users.count()
        return items, total

    async def create(self, data: UserCreate) -> User:
        if await self.users.get_by_email(data.email):
            raise ConflictError("Ya existe un usuario con ese email")
        return await self.users.create(
            email=data.email,
            full_name=data.full_name,
            role=data.role,
            is_active=data.is_active,
            hashed_password=hash_password(data.password),
        )

    async def update(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get(user_id)
        payload = data.model_dump(exclude_unset=True)
        if "password" in payload:
            payload["hashed_password"] = hash_password(payload.pop("password"))
        return await self.users.update(user, **payload)

    async def delete(self, user_id: int) -> None:
        user = await self.get(user_id)
        await self.users.delete(user)
