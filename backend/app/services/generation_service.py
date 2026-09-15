"""Servicio de generación masiva: dataset, preview, encolado y estado."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enums import GenerationStatus
from app.models.generation import Generation
from app.models.user import User
from app.repositories.generation import GenerationRepository
from app.repositories.template import TemplateRepository
from app.schemas.generation import DatasetPreview, GenerationCreate
from app.services.documents import dataset_reader
from app.utils.files import save_upload


class GenerationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.generations = GenerationRepository(session)
        self.templates = TemplateRepository(session)

    async def get(self, generation_id: int) -> Generation:
        gen = await self.generations.get(generation_id)
        if gen is None:
            raise NotFoundError("Generación no encontrada")
        return gen

    async def list(self, *, offset: int, limit: int) -> tuple[list[Generation], int]:
        items = await self.generations.list(offset=offset, limit=limit)
        total = await self.generations.count()
        return items, total

    @staticmethod
    def preview_dataset(content: bytes, filename: str) -> DatasetPreview:
        """Guarda temporalmente el dataset y devuelve una vista previa."""
        path = save_upload(content, filename, subdir="datasets")
        return dataset_reader.preview(path)

    async def create(
        self, data: GenerationCreate, *, content: bytes, filename: str, owner: User
    ) -> Generation:
        template = await self.templates.get(data.template_id)
        if template is None:
            raise NotFoundError("La plantilla indicada no existe")

        dataset_path = save_upload(content, filename, subdir="datasets")
        columns, rows = dataset_reader.read_rows(dataset_path)
        if not rows:
            raise ValidationError("El dataset no contiene filas de datos")

        return await self.generations.create(
            name=data.name,
            template_id=template.id,
            owner_id=owner.id,
            dataset_path=str(dataset_path),
            column_mapping=data.column_mapping,
            total_rows=len(rows),
            status=GenerationStatus.PENDING,
        )

    async def start(self, generation_id: int) -> Generation:
        """Encola el trabajo en Celery."""
        gen = await self.get(generation_id)
        if gen.status not in (GenerationStatus.PENDING, GenerationStatus.FAILED):
            raise ConflictError(f"La generación ya está en estado '{gen.status.value}'")

        # Import diferido para evitar dependencia circular con workers
        from app.workers.tasks import run_generation

        task = run_generation.delay(gen.id)
        return await self.generations.update(
            gen, status=GenerationStatus.PENDING, celery_task_id=task.id
        )

    async def cancel(self, generation_id: int) -> Generation:
        gen = await self.get(generation_id)
        if gen.status in (GenerationStatus.COMPLETED, GenerationStatus.CANCELLED):
            raise ConflictError("La generación ya finalizó")

        if gen.celery_task_id:
            from app.workers.celery_app import celery_app

            celery_app.control.revoke(gen.celery_task_id, terminate=True)
        return await self.generations.update(gen, status=GenerationStatus.CANCELLED)

    def zip_file(self, gen: Generation) -> Path:
        if not gen.zip_path or not Path(gen.zip_path).exists():
            raise NotFoundError("El ZIP aún no está disponible")
        return Path(gen.zip_path)
