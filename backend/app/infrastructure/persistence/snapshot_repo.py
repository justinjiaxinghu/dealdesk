from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.snapshot import Snapshot
from app.domain.interfaces.repositories import SnapshotRepository
from app.infrastructure.persistence.mappers import (
    snapshot_to_entity,
    snapshot_to_model,
)
from app.infrastructure.persistence.models import SnapshotModel


class SqlAlchemySnapshotRepository(SnapshotRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: Snapshot) -> Snapshot:
        model = snapshot_to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return snapshot_to_entity(model)

    async def get_by_id(self, snapshot_id: UUID) -> Snapshot | None:
        stmt = select(SnapshotModel).where(SnapshotModel.id == snapshot_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return snapshot_to_entity(model) if model else None

    async def list_all(self) -> list[Snapshot]:
        stmt = select(SnapshotModel).order_by(SnapshotModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [snapshot_to_entity(m) for m in result.scalars().all()]

    async def list_by_deal_id(self, deal_id: UUID) -> list[Snapshot]:
        stmt = (
            select(SnapshotModel)
            .where(SnapshotModel.deal_id == deal_id)
            .order_by(SnapshotModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [snapshot_to_entity(m) for m in result.scalars().all()]

    async def delete(self, snapshot_id: UUID) -> None:
        stmt = select(SnapshotModel).where(SnapshotModel.id == snapshot_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
