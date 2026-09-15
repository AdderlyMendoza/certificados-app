"""Registro central de modelos ORM.

Importar todos los modelos aquí garantiza que Alembic y SQLAlchemy
conozcan el metadata completo (`Base.metadata`).
"""
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.generation import Generation, GenerationItem
from app.models.template import Template, TemplateVersion
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Template",
    "TemplateVersion",
    "Generation",
    "GenerationItem",
    "AuditLog",
]
