"""Dependencias reutilizables de FastAPI: autenticación y autorización."""
from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_token
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    if not token:
        raise AuthenticationError("Credenciales no proporcionadas")
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise AuthenticationError("Token inválido o expirado") from exc

    user = await UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Usuario inexistente o inactivo")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable:
    """Genera una dependencia que exige uno de los roles indicados."""

    async def _guard(user: CurrentUser) -> User:
        if user.role not in roles:
            raise PermissionDeniedError(
                "No tienes permisos para realizar esta acción",
                detail={"required": [r.value for r in roles], "actual": user.role.value},
            )
        return user

    return _guard


# Atajos de autorización comunes
require_admin = require_roles(UserRole.ADMIN)
require_operator = require_roles(UserRole.ADMIN, UserRole.OPERATOR)
require_any = require_roles(UserRole.ADMIN, UserRole.OPERATOR, UserRole.AUDITOR)
