"""Servicio de plantillas: CRUD, subida, detección de variables y versionado."""
from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.enums import TemplateType
from app.models.template import Template
from app.models.user import User
from app.repositories.template import TemplateRepository, TemplateVersionRepository
from app.schemas.template import TemplateBase, TemplateUpdate
from app.services.documents import pdf_engine, word_engine
from app.utils.files import save_upload, unique_filename

_EXT_TO_TYPE = {".docx": TemplateType.WORD, ".pdf": TemplateType.PDF}


class TemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.templates = TemplateRepository(session)
        self.versions = TemplateVersionRepository(session)

    async def get(self, template_id: int) -> Template:
        tpl = await self.templates.get(template_id)
        if tpl is None:
            raise NotFoundError("Plantilla no encontrada")
        return tpl

    async def list(
        self, *, offset: int, limit: int, category: str | None = None
    ) -> tuple[list[Template], int]:
        filters = {"category": category} if category else None
        items = await self.templates.list(offset=offset, limit=limit, filters=filters)
        total = await self.templates.count(filters=filters)
        return items, total

    async def create_from_upload(
        self, *, meta: TemplateBase, content: bytes, filename: str, owner: User
    ) -> Template:
        suffix = Path(filename).suffix.lower()
        if suffix not in _EXT_TO_TYPE:
            raise ValidationError("Solo se admiten archivos .docx o .pdf")

        path = save_upload(content, filename, subdir="templates")
        ttype = _EXT_TO_TYPE[suffix]

        # Detección automática de variables y layout inicial
        variables: list[str] = []
        layout = None
        if ttype == TemplateType.WORD:
            variables = word_engine.detect_variables(path)
        else:
            width, height = pdf_engine.get_page_size(path)
            layout = {"page_width": width, "page_height": height, "fields": []}

        tpl = await self.templates.create(
            name=meta.name,
            description=meta.description,
            category=meta.category,
            type=ttype,
            file_path=str(path),
            original_filename=filename,
            file_size=len(content),
            variables=variables,
            layout=layout,
            owner_id=owner.id,
        )
        await self._snapshot(tpl, note="Versión inicial")
        return tpl

    async def update(self, template_id: int, data: TemplateUpdate) -> Template:
        tpl = await self.get(template_id)
        payload = data.model_dump(exclude_unset=True)

        # El layout/qr_config llegan como modelos anidados -> a dict para JSON
        if "layout" in payload and payload["layout"] is not None:
            payload["layout"] = data.layout.model_dump()  # type: ignore[union-attr]
        if "qr_config" in payload and payload["qr_config"] is not None:
            payload["qr_config"] = data.qr_config.model_dump()  # type: ignore[union-attr]

        return await self.templates.update(tpl, **payload)

    async def delete(self, template_id: int) -> None:
        tpl = await self.get(template_id)
        Path(tpl.file_path).unlink(missing_ok=True)
        await self.templates.delete(tpl)

    async def duplicate(self, template_id: int, owner: User) -> Template:
        src = await self.get(template_id)
        new_path = save_upload(
            Path(src.file_path).read_bytes(), src.original_filename, subdir="templates"
        )
        copy = await self.templates.create(
            name=f"{src.name} (copia)",
            description=src.description,
            category=src.category,
            type=src.type,
            file_path=str(new_path),
            original_filename=src.original_filename,
            file_size=src.file_size,
            variables=list(src.variables),
            layout=src.layout,
            qr_config=src.qr_config,
            owner_id=owner.id,
        )
        await self._snapshot(copy, note=f"Duplicada de #{src.id}")
        return copy

    async def list_versions(self, template_id: int):
        tpl = await self.get(template_id)
        return await self.versions.list(
            offset=0, limit=100, filters={"template_id": tpl.id}
        )

    async def _snapshot(self, tpl: Template, note: str | None = None) -> None:
        """Crea un snapshot de versión copiando el archivo actual."""
        version_path = Path(tpl.file_path).with_name(unique_filename(tpl.original_filename))
        shutil.copy2(tpl.file_path, version_path)
        await self.versions.create(
            template_id=tpl.id,
            version=tpl.current_version,
            file_path=str(version_path),
            layout=tpl.layout,
            variables=list(tpl.variables),
            note=note,
        )
