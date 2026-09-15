"""Excepciones de dominio y handlers para FastAPI.

Las excepciones de dominio son agnósticas de HTTP; los handlers las
traducen a respuestas JSON con el status code adecuado.
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Excepción base de la aplicación."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "app_error"

    def __init__(self, message: str, *, detail: dict | None = None) -> None:
        self.message = message
        self.detail = detail or {}
        super().__init__(message)


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppException):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class ValidationError(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "validation_error"


class AuthenticationError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "authentication_error"


class PermissionDeniedError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    code = "permission_denied"


def register_exception_handlers(app: FastAPI) -> None:
    """Registra el handler único para todas las AppException."""

    @app.exception_handler(AppException)
    async def _handle_app_exception(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "detail": exc.detail},
        )
