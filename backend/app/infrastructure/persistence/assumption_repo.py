# backend/app/infrastructure/persistence/assumption_repo.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.assumption import Assumption, AssumptionSet
from app.domain.interfaces.repositories import (
    AssumptionRepository,
    AssumptionSetRepository,
)
from app.infrastructure.persistence.mappers import (
    assumption_set_to_entity,
    assumption_set_to_model,
    assumption_to_entity,
    assumption_to_model,
)
from app.infrastructure.persistence.models import AssumptionModel, AssumptionSetModel


class SqlAlchemyAssumptionSetRepository(AssumptionSetRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, assumption_set: AssumptionSet) -> AssumptionSet:
        model = assumption_set_to_model(assumption_set)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return assumption_set_to_entity(model)

    async def get_by_id(self, set_id: UUID) -> AssumptionSet | None:
        stmt = select(AssumptionSetModel).where(AssumptionSetModel.id == set_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return assumption_set_to_entity(model) if model else None

    async def get_by_deal_id(self, deal_id: UUID) -> list[AssumptionSet]:
        stmt = (
            select(AssumptionSetModel)
            .where(AssumptionSetModel.deal_id == deal_id)
            .order_by(AssumptionSetModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [assumption_set_to_entity(m) for m in result.scalars().all()]


class SqlAlchemyAssumptionRepository(AssumptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_upsert(
        self, assumptions: list[Assumption]
    ) -> list[Assumption]:
        results: list[Assumption] = []
        for assumption in assumptions:
            # Check if an assumption with the same set_id + key already exists
            stmt = select(AssumptionModel).where(
                AssumptionModel.set_id == assumption.set_id,
                AssumptionModel.key == assumption.key,
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                existing.value_number = assumption.value_number
                existing.unit = assumption.unit
                existing.range_min = assumption.range_min
                existing.range_max = assumption.range_max
                existing.source_type = assumption.source_type.value
                existing.source_ref = assumption.source_ref
                existing.notes = assumption.notes
                existing.updated_at = datetime.utcnow()
                await self._session.flush()
                await self._session.refresh(existing)
                results.append(assumption_to_entity(existing))
            else:
                # Create new
                model = assumption_to_model(assumption)
                self._session.add(model)
                await self._session.flush()
                await self._session.refresh(model)
                results.append(assumption_to_entity(model))

        return results

    async def get_by_set_id(self, set_id: UUID) -> list[Assumption]:
        stmt = (
            select(AssumptionModel)
            .where(AssumptionModel.set_id == set_id)
            .order_by(AssumptionModel.key)
        )
        result = await self._session.execute(stmt)
        return [assumption_to_entity(m) for m in result.scalars().all()]

    async def update(self, assumption: Assumption) -> Assumption:
        stmt = select(AssumptionModel).where(AssumptionModel.id == assumption.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.key = assumption.key
        model.value_number = assumption.value_number
        model.unit = assumption.unit
        model.range_min = assumption.range_min
        model.range_max = assumption.range_max
        model.source_type = assumption.source_type.value
        model.source_ref = assumption.source_ref
        model.notes = assumption.notes
        model.updated_at = datetime.utcnow()
        await self._session.flush()
        await self._session.refresh(model)
        return assumption_to_entity(model)
