from __future__ import annotations
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.historical_financial import HistoricalFinancial
from app.domain.interfaces.repositories import HistoricalFinancialRepository
from app.infrastructure.persistence.mappers import (
    historical_financial_to_entity,
    historical_financial_to_model,
)
from app.infrastructure.persistence.models import HistoricalFinancialModel


class SqlAlchemyHistoricalFinancialRepository(HistoricalFinancialRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_upsert(
        self, items: list[HistoricalFinancial]
    ) -> list[HistoricalFinancial]:
        if not items:
            return []
        deal_id = items[0].deal_id
        await self._session.execute(
            delete(HistoricalFinancialModel).where(
                HistoricalFinancialModel.deal_id == deal_id
            )
        )
        models = [historical_financial_to_model(i) for i in items]
        self._session.add_all(models)
        await self._session.flush()
        return [historical_financial_to_entity(m) for m in models]

    async def get_by_deal_id(self, deal_id: UUID) -> list[HistoricalFinancial]:
        result = await self._session.execute(
            select(HistoricalFinancialModel).where(
                HistoricalFinancialModel.deal_id == deal_id
            )
        )
        return [historical_financial_to_entity(m) for m in result.scalars()]
