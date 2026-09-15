"""Router principal que agrega todos los endpoints de la v1."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, dashboard, generations, qr, templates, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(templates.router)
api_router.include_router(generations.router)
api_router.include_router(qr.router)
api_router.include_router(dashboard.router)
