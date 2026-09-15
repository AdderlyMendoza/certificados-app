"""Modelos de trabajos de generación masiva y sus ítems individuales."""
from __future__ import annotations

from typing import Any

from sqlalchemy import (
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import GenerationStatus


class Generation(Base, TimestampMixin):
    """Trabajo de generación masiva: una plantilla + un dataset (Excel)."""

    __tablename__ = "generations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[GenerationStatus] = mapped_column(
        SAEnum(GenerationStatus), default=GenerationStatus.PENDING, nullable=False, index=True
    )

    template_id: Mapped[int] = mapped_column(
        ForeignKey("templates.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Dataset de origen y su mapeo de columnas -> variables
    dataset_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    column_mapping: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Progreso
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Resultado
    zip_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    template: Mapped["Template"] = relationship(back_populates="generations")  # noqa: F821
    owner: Mapped["User"] = relationship(back_populates="generations")  # noqa: F821
    items: Mapped[list["GenerationItem"]] = relationship(
        back_populates="generation", cascade="all, delete-orphan"
    )

    @property
    def progress_percent(self) -> int:
        if self.total_rows == 0:
            return 0
        return int(self.processed_rows / self.total_rows * 100)


class GenerationItem(Base, TimestampMixin):
    """Documento individual generado a partir de una fila del dataset."""

    __tablename__ = "generation_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    generation_id: Mapped[int] = mapped_column(
        ForeignKey("generations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[GenerationStatus] = mapped_column(
        SAEnum(GenerationStatus), default=GenerationStatus.PENDING, nullable=False
    )
    row_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    output_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    generation: Mapped["Generation"] = relationship(back_populates="items")
