# backend/app/infrastructure/persistence/export_repo.py
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.export import Export
from app.domain.interfaces.repositories import ExportRepository
from app.infrastructure.persistence.mappers import export_to_entity, export_to_model
from app.infrastructure.persistence.models import ExportModel


class SqlAlchemyExportRepository(ExportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, export: Export) -> Export:
        model = export_to_model(export)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return export_to_entity(model)

    async def get_by_deal_id(self, deal_id: UUID) -> list[Export]:
        stmt = (
            select(ExportModel)
            .where(ExportModel.deal_id == deal_id)
            .order_by(ExportModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [export_to_entity(m) for m in result.scalars().all()]
