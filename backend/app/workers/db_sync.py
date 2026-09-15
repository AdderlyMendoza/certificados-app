"""Sesión SQLAlchemy *sincrona* para uso dentro de tareas Celery.

Celery no es async-friendly por defecto, así que las tareas usan un engine
sync (pymysql) independiente del engine async de la API.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SyncSessionLocal = sessionmaker(bind=sync_engine, class_=Session, expire_on_commit=False)
