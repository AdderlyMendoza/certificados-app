"""Endpoints de autenticación."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.auth import RefreshRequest, Token
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    db: DbSession,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Login OAuth2 (username = email). Devuelve access + refresh token."""
    return await AuthService(db).authenticate(form.username, form.password)


@router.post("/refresh", response_model=Token)
async def refresh(db: DbSession, body: RefreshRequest) -> Token:
    return await AuthService(db).refresh(body.refresh_token)


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser) -> UserRead:
    return current_user  # type: ignore[return-value]
