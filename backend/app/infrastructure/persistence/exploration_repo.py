from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.exploration import ExplorationSession
from app.domain.interfaces.repositories import ExplorationSessionRepository
from app.infrastructure.persistence.mappers import (
    exploration_session_to_entity,
    exploration_session_to_model,
)
from app.infrastructure.persistence.models import ExplorationSessionModel


class SqlAlchemyExplorationSessionRepository(ExplorationSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: ExplorationSession) -> ExplorationSession:
        model = exploration_session_to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return exploration_session_to_entity(model)

    async def get_by_id(self, session_id: UUID) -> ExplorationSession | None:
        stmt = select(ExplorationSessionModel).where(
            ExplorationSessionModel.id == session_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return exploration_session_to_entity(model) if model else None

    async def list_saved(self) -> list[ExplorationSession]:
        stmt = (
            select(ExplorationSessionModel)
            .where(ExplorationSessionModel.saved == True)  # noqa: E712
            .order_by(ExplorationSessionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [exploration_session_to_entity(m) for m in result.scalars().all()]

    async def list_free(self) -> list[ExplorationSession]:
        stmt = (
            select(ExplorationSessionModel)
            .where(ExplorationSessionModel.deal_id.is_(None))
            .order_by(ExplorationSessionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [exploration_session_to_entity(m) for m in result.scalars().all()]

    async def list_by_deal_id(self, deal_id: UUID) -> list[ExplorationSession]:
        stmt = (
            select(ExplorationSessionModel)
            .where(ExplorationSessionModel.deal_id == deal_id)
            .order_by(ExplorationSessionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [exploration_session_to_entity(m) for m in result.scalars().all()]

    async def update(self, entity: ExplorationSession) -> ExplorationSession:
        stmt = select(ExplorationSessionModel).where(
            ExplorationSessionModel.id == entity.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.name = entity.name
        model.saved = entity.saved
        model.deal_id = str(entity.deal_id) if entity.deal_id else None
        await self._session.flush()
        await self._session.refresh(model)
        return exploration_session_to_entity(model)

    async def delete(self, session_id: UUID) -> None:
        stmt = select(ExplorationSessionModel).where(
            ExplorationSessionModel.id == session_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
