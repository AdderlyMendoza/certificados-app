"""Modelos de plantilla y versionado de plantillas."""
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
from app.models.enums import TemplateStatus, TemplateType


class Template(Base, TimestampMixin):
    """Plantilla base (Word o PDF) con sus variables y configuración."""

    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    type: Mapped[TemplateType] = mapped_column(SAEnum(TemplateType), nullable=False)
    status: Mapped[TemplateStatus] = mapped_column(
        SAEnum(TemplateStatus), default=TemplateStatus.DRAFT, nullable=False
    )

    # Ruta del archivo fuente (.docx o .pdf) y metadatos
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Variables detectadas (lista de nombres) y, para PDF, layout del editor visual
    variables: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    layout: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Configuración del QR por defecto para esta plantilla
    qr_config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relaciones
    owner: Mapped["User"] = relationship(back_populates="templates")  # noqa: F821
    versions: Mapped[list["TemplateVersion"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateVersion.version.desc()",
    )
    generations: Mapped[list["Generation"]] = relationship(  # noqa: F821
        back_populates="template"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Template {self.name} ({self.type.value})>"


class TemplateVersion(Base, TimestampMixin):
    """Snapshot histórico de una plantilla (archivo + layout en un momento dado)."""

    __tablename__ = "template_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    layout: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    variables: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    template: Mapped["Template"] = relationship(back_populates="versions")
