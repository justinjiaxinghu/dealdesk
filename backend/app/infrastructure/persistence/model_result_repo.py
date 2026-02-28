# backend/app/infrastructure/persistence/model_result_repo.py
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.model_result import ModelResult
from app.domain.interfaces.repositories import ModelResultRepository
from app.infrastructure.persistence.mappers import (
    model_result_to_entity,
    model_result_to_model,
)
from app.infrastructure.persistence.models import ModelResultModel


class SqlAlchemyModelResultRepository(ModelResultRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, result: ModelResult) -> ModelResult:
        model = model_result_to_model(result)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model_result_to_entity(model)

    async def get_by_set_id(self, set_id: UUID) -> ModelResult | None:
        stmt = (
            select(ModelResultModel)
            .where(ModelResultModel.set_id == set_id)
            .order_by(ModelResultModel.computed_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model_result_to_entity(model) if model else None
