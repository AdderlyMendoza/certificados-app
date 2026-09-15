"""Endpoint del dashboard: métricas y actividad reciente."""
from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser, DbSession
from app.models.audit_log import AuditLog
from app.models.enums import GenerationStatus
from app.models.generation import Generation
from app.models.template import Template
from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    total_templates: int
    total_generations: int
    total_certificates: int      # documentos producidos (filas procesadas)
    total_errors: int
    by_status: dict[str, int]


class ActivityItem(BaseModel):
    action: str
    entity: str | None
    created_at: str


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: DbSession, _: CurrentUser) -> DashboardStats:
    total_templates = int((await db.execute(select(func.count(Template.id)))).scalar_one())
    total_generations = int(
        (await db.execute(select(func.count(Generation.id)))).scalar_one()
    )
    total_certificates = int(
        (await db.execute(select(func.coalesce(func.sum(Generation.processed_rows), 0)))).scalar_one()
    )
    total_errors = int(
        (await db.execute(select(func.coalesce(func.sum(Generation.failed_rows), 0)))).scalar_one()
    )

    status_rows = await db.execute(
        select(Generation.status, func.count(Generation.id)).group_by(Generation.status)
    )
    by_status = {status.value: 0 for status in GenerationStatus}
    for status_value, count in status_rows.all():
        by_status[status_value.value] = int(count)

    return DashboardStats(
        total_templates=total_templates,
        total_generations=total_generations,
        total_certificates=total_certificates,
        total_errors=total_errors,
        by_status=by_status,
    )


@router.get("/activity", response_model=list[ActivityItem])
async def get_activity(db: DbSession, _: CurrentUser) -> list[ActivityItem]:
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(15)
    )
    return [
        ActivityItem(
            action=log.action, entity=log.entity, created_at=log.created_at.isoformat()
        )
        for log in result.scalars().all()
    ]
