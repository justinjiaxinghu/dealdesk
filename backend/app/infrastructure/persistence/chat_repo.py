from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.chat import ChatMessage, ChatSession
from app.domain.interfaces.repositories import ChatMessageRepository, ChatSessionRepository
from app.infrastructure.persistence.mappers import (
    chat_message_to_entity,
    chat_message_to_model,
    chat_session_to_entity,
    chat_session_to_model,
)
from app.infrastructure.persistence.models import ChatMessageModel, ChatSessionModel


class SqlAlchemyChatSessionRepository(ChatSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: ChatSession) -> ChatSession:
        model = chat_session_to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return chat_session_to_entity(model)

    async def get_by_id(self, session_id: UUID) -> ChatSession | None:
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == session_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return chat_session_to_entity(model) if model else None

    async def get_by_exploration_id(self, exploration_id: UUID) -> list[ChatSession]:
        stmt = (
            select(ChatSessionModel)
            .where(ChatSessionModel.exploration_session_id == exploration_id)
            .order_by(ChatSessionModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [chat_session_to_entity(m) for m in result.scalars().all()]

    async def update(self, entity: ChatSession) -> ChatSession:
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == entity.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.title = entity.title
        model.connectors = [c.value for c in entity.connectors]
        model.updated_at = entity.updated_at
        await self._session.flush()
        await self._session.refresh(model)
        return chat_session_to_entity(model)

    async def delete(self, session_id: UUID) -> None:
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == session_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()


class SqlAlchemyChatMessageRepository(ChatMessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: ChatMessage) -> ChatMessage:
        model = chat_message_to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return chat_message_to_entity(model)

    async def get_by_session_id(self, session_id: UUID) -> list[ChatMessage]:
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [chat_message_to_entity(m) for m in result.scalars().all()]

    async def bulk_create(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        models = [chat_message_to_model(m) for m in messages]
        self._session.add_all(models)
        await self._session.flush()
        for model in models:
            await self._session.refresh(model)
        return [chat_message_to_entity(m) for m in models]
