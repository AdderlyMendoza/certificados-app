"""Servicio de autenticación."""
from __future__ import annotations

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.repositories.user import UserRepository
from app.schemas.auth import Token


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)

    async def authenticate(self, email: str, password: str) -> Token:
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Email o contraseña incorrectos")
        if not user.is_active:
            raise AuthenticationError("La cuenta está desactivada")
        return self._issue_tokens(user.id)

    async def refresh(self, refresh_token: str) -> Token:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
            user_id = int(payload["sub"])
        except (jwt.PyJWTError, KeyError, ValueError) as exc:
            raise AuthenticationError("Refresh token inválido") from exc

        user = await self.users.get(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Usuario inexistente o inactivo")
        return self._issue_tokens(user.id)

    @staticmethod
    def _issue_tokens(user_id: int) -> Token:
        return Token(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )
