"""Schemas de plantilla, layout del editor visual y configuración de QR."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FieldType, TemplateStatus, TemplateType


# --------------------------------------------------------------------------
# Editor visual (layout del PDF)
# --------------------------------------------------------------------------
class LayoutField(BaseModel):
    """Un elemento posicionado sobre el PDF de fondo.

    Coordenadas en píxeles con origen ARRIBA-IZQUIERDA respecto a la página
    renderizada en el editor. La generación las traduce al sistema de PyMuPDF.
    """

    name: str
    type: FieldType
    page: int = Field(default=0, ge=0)
    x: float
    y: float
    width: float | None = None
    height: float | None = None

    # Estilo de texto
    font: str = "Helvetica"
    font_size: float = Field(default=14, gt=0)
    color: str = "#000000"
    bold: bool = False
    italic: bool = False
    align: Literal["left", "center", "right"] = "left"
    rotation: float = 0.0

    # Contenido fijo (para type=text) o nombre de variable / plantilla de texto
    value: str | None = None

    # Ajuste automático de tamaño de fuente para que el texto quepa en `width`
    auto_fit: bool = False


class QRConfig(BaseModel):
    """Configuración del código QR."""

    content_type: Literal["text", "url", "uuid", "code"] = "text"
    content_template: str = "{{codigo}}"   # admite variables del dataset
    size: int = Field(default=200, ge=50, le=2000)
    margin: int = Field(default=2, ge=0, le=20)
    error_correction: Literal["L", "M", "Q", "H"] = "M"
    fill_color: str = "#000000"
    back_color: str = "#FFFFFF"


class TemplateLayout(BaseModel):
    """Layout completo: dimensiones de página y campos."""

    page_width: float
    page_height: float
    fields: list[LayoutField] = Field(default_factory=list)


# --------------------------------------------------------------------------
# CRUD
# --------------------------------------------------------------------------
class TemplateBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=120)


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=120)
    status: TemplateStatus | None = None
    layout: TemplateLayout | None = None
    qr_config: QRConfig | None = None


class TemplateRead(TemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: TemplateType
    status: TemplateStatus
    original_filename: str
    file_size: int
    variables: list[str]
    layout: dict | None
    qr_config: dict | None
    current_version: int
    owner_id: int
    created_at: datetime
    updated_at: datetime


class TemplateVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: int
    note: str | None
    variables: list[str]
    created_at: datetime
