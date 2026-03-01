# backend/app/infrastructure/persistence/extraction_repo.py
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.extraction import ExtractedField, MarketTable
from app.domain.interfaces.repositories import (
    ExtractedFieldRepository,
    MarketTableRepository,
)
from app.infrastructure.persistence.mappers import (
    extracted_field_to_entity,
    extracted_field_to_model,
    market_table_to_entity,
    market_table_to_model,
)
from app.infrastructure.persistence.models import DocumentModel, ExtractedFieldModel, MarketTableModel


class SqlAlchemyExtractedFieldRepository(ExtractedFieldRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(
        self, fields: list[ExtractedField]
    ) -> list[ExtractedField]:
        models = [extracted_field_to_model(f) for f in fields]
        self._session.add_all(models)
        await self._session.flush()
        for m in models:
            await self._session.refresh(m)
        return [extracted_field_to_entity(m) for m in models]

    async def get_by_document_id(
        self, document_id: UUID
    ) -> list[ExtractedField]:
        stmt = select(ExtractedFieldModel).where(
            ExtractedFieldModel.document_id == document_id
        )
        result = await self._session.execute(stmt)
        return [extracted_field_to_entity(m) for m in result.scalars().all()]

    async def get_by_deal_id(self, deal_id: UUID) -> list[ExtractedField]:
        stmt = (
            select(ExtractedFieldModel)
            .join(DocumentModel, ExtractedFieldModel.document_id == DocumentModel.id)
            .where(DocumentModel.deal_id == deal_id)
        )
        result = await self._session.execute(stmt)
        return [extracted_field_to_entity(m) for m in result.scalars().all()]


class SqlAlchemyMarketTableRepository(MarketTableRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(self, tables: list[MarketTable]) -> list[MarketTable]:
        models = [market_table_to_model(t) for t in tables]
        self._session.add_all(models)
        await self._session.flush()
        for m in models:
            await self._session.refresh(m)
        return [market_table_to_entity(m) for m in models]

    async def get_by_document_id(self, document_id: UUID) -> list[MarketTable]:
        stmt = select(MarketTableModel).where(
            MarketTableModel.document_id == document_id
        )
        result = await self._session.execute(stmt)
        return [market_table_to_entity(m) for m in result.scalars().all()]
