"""Connector and ConnectorFile repositories."""
from sqlalchemy import select, delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.connector import Connector, ConnectorFile
from app.infrastructure.persistence.mappers import (
    connector_entity_to_model,
    connector_model_to_entity,
    connector_file_entity_to_model,
    connector_file_model_to_entity,
)
from app.infrastructure.persistence.models import ConnectorModel, ConnectorFileModel


class SqlAlchemyConnectorRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_provider(self, provider: str) -> Connector | None:
        result = await self._session.execute(
            select(ConnectorModel).where(ConnectorModel.provider == provider)
        )
        model = result.scalar_one_or_none()
        return connector_model_to_entity(model) if model else None

    async def list_all(self) -> list[Connector]:
        result = await self._session.execute(select(ConnectorModel))
        return [connector_model_to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: Connector) -> Connector:
        model = connector_entity_to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return connector_model_to_entity(model)

    async def update(self, entity: Connector) -> Connector:
        model = connector_entity_to_model(entity)
        merged = await self._session.merge(model)
        await self._session.flush()
        return connector_model_to_entity(merged)

    async def delete_files(self, connector_id: str) -> None:
        await self._session.execute(
            delete(ConnectorFileModel).where(
                ConnectorFileModel.connector_id == connector_id
            )
        )
        await self._session.flush()


class SqlAlchemyConnectorFileRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def bulk_create(self, entities: list[ConnectorFile]) -> None:
        for entity in entities:
            self._session.add(connector_file_entity_to_model(entity))
        await self._session.flush()

    async def search(self, query: str, connector_id: str | None = None) -> list[ConnectorFile]:
        stmt = select(ConnectorFileModel)
        if connector_id:
            stmt = stmt.where(ConnectorFileModel.connector_id == connector_id)
        # Match any word in the query (OR logic) so "Arizona properties" matches
        # files containing "Arizona" or "properties"
        words = [w for w in query.split() if len(w) >= 2]
        if words:
            stmt = stmt.where(
                or_(*(ConnectorFileModel.text_content.ilike(f"%{w}%") for w in words))
            )
        else:
            stmt = stmt.where(ConnectorFileModel.text_content.ilike(f"%{query}%"))
        result = await self._session.execute(stmt)
        return [connector_file_model_to_entity(m) for m in result.scalars().all()]

    async def count_by_connector(self, connector_id: str) -> int:
        result = await self._session.execute(
            select(func.count(ConnectorFileModel.id)).where(
                ConnectorFileModel.connector_id == connector_id
            )
        )
        return result.scalar_one()
