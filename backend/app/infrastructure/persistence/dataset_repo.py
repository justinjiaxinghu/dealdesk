from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.dataset import Dataset
from app.domain.interfaces.repositories import DatasetRepository
from app.infrastructure.persistence.mappers import (
    dataset_to_entity,
    dataset_to_model,
)
from app.infrastructure.persistence.models import DatasetModel


class SqlAlchemyDatasetRepository(DatasetRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: Dataset) -> Dataset:
        model = dataset_to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return dataset_to_entity(model)

    async def get_by_id(self, dataset_id: UUID) -> Dataset | None:
        stmt = select(DatasetModel).where(DatasetModel.id == dataset_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return dataset_to_entity(model) if model else None

    async def list_all(self) -> list[Dataset]:
        stmt = select(DatasetModel).order_by(DatasetModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [dataset_to_entity(m) for m in result.scalars().all()]

    async def list_by_deal_id(self, deal_id: UUID) -> list[Dataset]:
        stmt = (
            select(DatasetModel)
            .where(DatasetModel.deal_id == deal_id)
            .order_by(DatasetModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [dataset_to_entity(m) for m in result.scalars().all()]

    async def list_free(self) -> list[Dataset]:
        stmt = (
            select(DatasetModel)
            .where(DatasetModel.deal_id.is_(None))
            .order_by(DatasetModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [dataset_to_entity(m) for m in result.scalars().all()]

    async def update(self, entity: Dataset) -> Dataset:
        stmt = select(DatasetModel).where(DatasetModel.id == entity.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.name = entity.name
        model.deal_id = str(entity.deal_id) if entity.deal_id else None
        model.properties = entity.properties
        model.updated_at = datetime.utcnow()
        await self._session.flush()
        await self._session.refresh(model)
        return dataset_to_entity(model)

    async def delete(self, dataset_id: UUID) -> None:
        stmt = select(DatasetModel).where(DatasetModel.id == dataset_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
