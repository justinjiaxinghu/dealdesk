from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.field_validation import FieldValidation
from app.infrastructure.persistence.mappers import (
    field_validation_to_entity,
    field_validation_to_model,
)
from app.infrastructure.persistence.models import FieldValidationModel


class SqlAlchemyFieldValidationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_upsert(
        self, validations: list[FieldValidation]
    ) -> list[FieldValidation]:
        results: list[FieldValidation] = []
        for v in validations:
            stmt = select(FieldValidationModel).where(
                FieldValidationModel.deal_id == v.deal_id,
                FieldValidationModel.field_key == v.field_key,
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.om_value = v.om_value
                existing.market_value = v.market_value
                existing.status = v.status.value
                existing.explanation = v.explanation
                existing.sources = v.sources
                existing.confidence = v.confidence
                existing.search_steps = v.search_steps
                existing.created_at = datetime.utcnow()
                await self._session.flush()
                await self._session.refresh(existing)
                results.append(field_validation_to_entity(existing))
            else:
                model = field_validation_to_model(v)
                self._session.add(model)
                await self._session.flush()
                await self._session.refresh(model)
                results.append(field_validation_to_entity(model))

        return results

    async def get_by_deal_id(self, deal_id: UUID) -> list[FieldValidation]:
        stmt = select(FieldValidationModel).where(
            FieldValidationModel.deal_id == deal_id
        )
        result = await self._session.execute(stmt)
        return [field_validation_to_entity(m) for m in result.scalars().all()]
