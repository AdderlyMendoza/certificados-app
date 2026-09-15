"""Enumeraciones de dominio compartidas por modelos y schemas."""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    """Roles del sistema con permisos diferenciados."""

    ADMIN = "admin"          # control total
    OPERATOR = "operator"    # crea plantillas y genera documentos
    AUDITOR = "auditor"      # solo lectura + logs


class TemplateType(str, enum.Enum):
    """Tipo de motor que procesa la plantilla."""

    WORD = "word"   # .docx procesado con docxtpl (variables {{...}})
    PDF = "pdf"     # .pdf usado como fondo + overlay por coordenadas


class TemplateStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class GenerationStatus(str, enum.Enum):
    """Estados del ciclo de vida de un trabajo de generación masiva."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FieldType(str, enum.Enum):
    """Tipos de elemento soportados por el editor visual del PDF."""

    TEXT = "text"
    VARIABLE = "variable"
    QR = "qr"
    IMAGE = "image"
    SIGNATURE = "signature"
    DATE = "date"
    NUMBER = "number"
    BARCODE = "barcode"
