"""Endpoints CRUD de plantillas + subida, preview y versionado."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response

from app.core.config import settings
from app.core.dependencies import CurrentUser, DbSession, require_operator
from app.core.exceptions import ValidationError
from app.models.enums import TemplateType
from app.schemas.common import Message, Page
from app.schemas.template import (
    TemplateBase,
    TemplateRead,
    TemplateUpdate,
    TemplateVersionRead,
)
from app.services.documents import pdf_engine
from app.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=Page[TemplateRead])
async def list_templates(
    db: DbSession,
    _: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
) -> Page[TemplateRead]:
    items, total = await TemplateService(db).list(
        offset=(page - 1) * size, limit=size, category=category
    )
    return Page(items=items, total=total, page=page, size=size)


@router.post(
    "",
    response_model=TemplateRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operator)],
)
async def upload_template(
    db: DbSession,
    current_user: CurrentUser,
    name: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    description: Annotated[str | None, Form()] = None,
    category: Annotated[str | None, Form()] = None,
) -> TemplateRead:
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise ValidationError(f"El archivo supera {settings.MAX_UPLOAD_MB} MB")
    meta = TemplateBase(name=name, description=description, category=category)
    return await TemplateService(db).create_from_upload(  # type: ignore[return-value]
        meta=meta, content=content, filename=file.filename or "plantilla", owner=current_user
    )


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(db: DbSession, _: CurrentUser, template_id: int) -> TemplateRead:
    return await TemplateService(db).get(template_id)  # type: ignore[return-value]


@router.patch(
    "/{template_id}",
    response_model=TemplateRead,
    dependencies=[Depends(require_operator)],
)
async def update_template(
    db: DbSession, _: CurrentUser, template_id: int, data: TemplateUpdate
) -> TemplateRead:
    return await TemplateService(db).update(template_id, data)  # type: ignore[return-value]


@router.delete(
    "/{template_id}", response_model=Message, dependencies=[Depends(require_operator)]
)
async def delete_template(db: DbSession, _: CurrentUser, template_id: int) -> Message:
    await TemplateService(db).delete(template_id)
    return Message(message="Plantilla eliminada")


@router.post(
    "/{template_id}/duplicate",
    response_model=TemplateRead,
    dependencies=[Depends(require_operator)],
)
async def duplicate_template(
    db: DbSession, current_user: CurrentUser, template_id: int
) -> TemplateRead:
    return await TemplateService(db).duplicate(template_id, current_user)  # type: ignore[return-value]


@router.get("/{template_id}/variables", response_model=list[str])
async def get_variables(db: DbSession, _: CurrentUser, template_id: int) -> list[str]:
    tpl = await TemplateService(db).get(template_id)
    return tpl.variables


@router.get("/{template_id}/versions", response_model=list[TemplateVersionRead])
async def list_versions(
    db: DbSession, _: CurrentUser, template_id: int
) -> list[TemplateVersionRead]:
    return await TemplateService(db).list_versions(template_id)  # type: ignore[return-value]


@router.get("/{template_id}/preview")
async def preview_template(
    db: DbSession,
    _: CurrentUser,
    template_id: int,
    page: Annotated[int, Query(ge=0)] = 0,
) -> Response:
    """Devuelve un PNG de la página (solo plantillas PDF, para el editor)."""
    tpl = await TemplateService(db).get(template_id)
    if tpl.type != TemplateType.PDF:
        raise ValidationError("La vista previa de imagen solo aplica a plantillas PDF")
    png = pdf_engine.render_preview(Path(tpl.file_path), page=page)
    return Response(content=png, media_type="image/png")
