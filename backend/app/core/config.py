"""Configuración central de la aplicación.

Carga las variables de entorno (.env) usando pydantic-settings y expone
un objeto `settings` único e inmutable para toda la app.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "Certificados App"
    APP_ENV: Literal["development", "production"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # --- MySQL ---
    MYSQL_HOST: str = "mysql"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "cert_user"
    MYSQL_PASSWORD: str = "cert_pass"
    MYSQL_DATABASE: str = "certificados"

    # --- Redis / Celery ---
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6379/1"

    # --- Seguridad ---
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Superusuario inicial ---
    FIRST_SUPERUSER_EMAIL: str = "admin@certificados.com"
    FIRST_SUPERUSER_PASSWORD: str = "Admin1234!"
    FIRST_SUPERUSER_NAME: str = "Administrador"

    # --- Almacenamiento ---
    UPLOAD_DIR: str = "/app/uploads"
    GENERATED_DIR: str = "/app/generated"
    MAX_UPLOAD_MB: int = 25

    # --- LibreOffice ---
    SOFFICE_BIN: str = "soffice"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _assemble_cors(cls, v: Any) -> list[str]:
        """Acepta CORS como lista JSON o como string separado por comas."""
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def DATABASE_URL_ASYNC(self) -> str:
        """URL de conexión async (asyncmy) para SQLAlchemy/FastAPI."""
        return (
            f"mysql+asyncmy://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """URL de conexión sync (pymysql) para Alembic y scripts."""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        )

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Devuelve la instancia única de configuración (cacheada)."""
    return Settings()


settings = get_settings()
