from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.comp import Comp
from app.domain.interfaces.repositories import CompRepository
from app.infrastructure.persistence.mappers import comp_to_entity, comp_to_model
from app.infrastructure.persistence.models import CompModel


class SqlAlchemyCompRepository(CompRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_upsert(self, comps: list[Comp]) -> list[Comp]:
        results: list[Comp] = []
        for c in comps:
            stmt = select(CompModel).where(
                CompModel.deal_id == c.deal_id,
                CompModel.address == c.address,
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.city = c.city
                existing.state = c.state
                existing.property_type = c.property_type.value
                existing.source = c.source.value
                existing.source_url = c.source_url
                existing.year_built = c.year_built
                existing.unit_count = c.unit_count
                existing.square_feet = c.square_feet
                existing.sale_price = c.sale_price
                existing.price_per_unit = c.price_per_unit
                existing.price_per_sqft = c.price_per_sqft
                existing.cap_rate = c.cap_rate
                existing.rent_per_unit = c.rent_per_unit
                existing.occupancy_rate = c.occupancy_rate
                existing.noi = c.noi
                existing.expense_ratio = c.expense_ratio
                existing.opex_per_unit = c.opex_per_unit
                existing.fetched_at = c.fetched_at
                await self._session.flush()
                await self._session.refresh(existing)
                results.append(comp_to_entity(existing))
            else:
                model = comp_to_model(c)
                self._session.add(model)
                await self._session.flush()
                await self._session.refresh(model)
                results.append(comp_to_entity(model))

        return results

    async def get_by_deal_id(self, deal_id: UUID) -> list[Comp]:
        stmt = select(CompModel).where(CompModel.deal_id == deal_id)
        result = await self._session.execute(stmt)
        return [comp_to_entity(m) for m in result.scalars().all()]

    async def delete_by_deal_id(self, deal_id: UUID) -> None:
        stmt = delete(CompModel).where(CompModel.deal_id == deal_id)
        await self._session.execute(stmt)
        await self._session.flush()
