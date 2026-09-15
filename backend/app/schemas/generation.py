"""Schemas de generación masiva."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import GenerationStatus


class GenerationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    template_id: int
    # Mapeo opcional columna_excel -> variable_plantilla (si difieren los nombres)
    column_mapping: dict[str, str] | None = None


class DatasetPreview(BaseModel):
    """Vista previa de un Excel/CSV subido antes de generar."""

    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    errors: list[str] = Field(default_factory=list)


class GenerationItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    row_index: int
    status: GenerationStatus
    output_path: str | None
    error_message: str | None


class GenerationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: GenerationStatus
    template_id: int
    owner_id: int
    total_rows: int
    processed_rows: int
    failed_rows: int
    zip_path: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
