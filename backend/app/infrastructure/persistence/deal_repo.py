# backend/app/infrastructure/persistence/deal_repo.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.deal import Deal
from app.domain.interfaces.repositories import DealRepository
from app.domain.value_objects.types import DealFilters
from app.infrastructure.persistence.mappers import deal_to_entity, deal_to_model
from app.infrastructure.persistence.models import DealModel


class SqlAlchemyDealRepository(DealRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, deal: Deal) -> Deal:
        model = deal_to_model(deal)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return deal_to_entity(model)

    async def get_by_id(self, deal_id: UUID) -> Deal | None:
        stmt = select(DealModel).where(DealModel.id == deal_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return deal_to_entity(model) if model else None

    async def list(self, filters: DealFilters | None = None) -> list[Deal]:
        stmt = select(DealModel)
        if filters:
            if filters.property_type:
                stmt = stmt.where(DealModel.property_type == filters.property_type)
            if filters.city:
                stmt = stmt.where(DealModel.city == filters.city)
        stmt = stmt.order_by(DealModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [deal_to_entity(m) for m in result.scalars().all()]

    async def update(self, deal: Deal) -> Deal:
        stmt = select(DealModel).where(DealModel.id == deal.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.name = deal.name
        model.address = deal.address
        model.city = deal.city
        model.state = deal.state
        model.property_type = deal.property_type.value
        model.latitude = deal.latitude
        model.longitude = deal.longitude
        model.square_feet = deal.square_feet
        model.updated_at = datetime.utcnow()
        await self._session.flush()
        await self._session.refresh(model)
        return deal_to_entity(model)
