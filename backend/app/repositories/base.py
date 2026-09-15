"""Repositorio base genérico con operaciones CRUD async."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """CRUD reutilizable sobre un modelo SQLAlchemy."""

    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id: int) -> ModelType | None:
        return await self.session.get(self.model, id)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
        order_by: Any | None = None,
    ) -> list[ModelType]:
        stmt = select(self.model)
        stmt = self._apply_filters(stmt, filters)
        stmt = stmt.order_by(order_by if order_by is not None else self.model.id.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *, filters: dict[str, Any] | None = None) -> int:
        stmt = select(func.count()).select_from(self.model)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, **data: Any) -> ModelType:
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelType, **data: Any) -> ModelType:
        for key, value in data.items():
            if value is not None and hasattr(obj, key):
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    def _apply_filters(self, stmt: Any, filters: dict[str, Any] | None) -> Any:
        if not filters:
            return stmt
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        return stmt
