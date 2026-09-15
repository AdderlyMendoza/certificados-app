"""Endpoints de gestión de usuarios (solo Admin)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import DbSession, require_admin
from app.schemas.common import Message, Page
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(require_admin)]
)


@router.get("", response_model=Page[UserRead])
async def list_users(
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[UserRead]:
    items, total = await UserService(db).list(offset=(page - 1) * size, limit=size)
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(db: DbSession, data: UserCreate) -> UserRead:
    return await UserService(db).create(data)  # type: ignore[return-value]


@router.get("/{user_id}", response_model=UserRead)
async def get_user(db: DbSession, user_id: int) -> UserRead:
    return await UserService(db).get(user_id)  # type: ignore[return-value]


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(db: DbSession, user_id: int, data: UserUpdate) -> UserRead:
    return await UserService(db).update(user_id, data)  # type: ignore[return-value]


@router.delete("/{user_id}", response_model=Message)
async def delete_user(db: DbSession, user_id: int) -> Message:
    await UserService(db).delete(user_id)
    return Message(message="Usuario eliminado")
