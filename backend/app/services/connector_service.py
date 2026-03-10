"""Connector service — manages mock connector lifecycle and file search."""

import logging
from datetime import datetime, timezone

from app.domain.entities.connector import Connector, ConnectorFile
from app.domain.value_objects.enums import ConnectorProvider, ConnectorStatus
from app.infrastructure.connectors.mock_data import MOCK_FILES_BY_PROVIDER
from app.infrastructure.connectors import vector_store
from app.infrastructure.persistence.connector_repo import (
    SqlAlchemyConnectorRepository,
    SqlAlchemyConnectorFileRepository,
)

logger = logging.getLogger(__name__)

ALL_PROVIDERS = [p.value for p in ConnectorProvider]


class ConnectorService:
    def __init__(
        self,
        connector_repo: SqlAlchemyConnectorRepository,
        file_repo: SqlAlchemyConnectorFileRepository,
    ):
        self._connector_repo = connector_repo
        self._file_repo = file_repo

    async def list_connectors(self) -> list[Connector]:
        """Return all connectors, creating missing ones as disconnected."""
        existing = await self._connector_repo.list_all()
        existing_providers = {c.provider.value for c in existing}
        for provider in ALL_PROVIDERS:
            if provider not in existing_providers:
                connector = Connector(
                    provider=ConnectorProvider(provider),
                    status=ConnectorStatus.DISCONNECTED,
                )
                created = await self._connector_repo.create(connector)
                existing.append(created)
        return existing

    async def connect(self, provider: str) -> Connector:
        """Mock-connect a provider and seed its files."""
        connector = await self._connector_repo.get_by_provider(provider)
        if not connector:
            connector = Connector(
                provider=ConnectorProvider(provider),
                status=ConnectorStatus.DISCONNECTED,
            )
            connector = await self._connector_repo.create(connector)

        mock_files = MOCK_FILES_BY_PROVIDER.get(provider, [])
        files = [
            ConnectorFile(
                connector_id=connector.id,
                name=f["name"],
                path=f["path"],
                file_type=f["file_type"],
                text_content=f["text_content"],
            )
            for f in mock_files
        ]
        await self._file_repo.bulk_create(files)

        # Index files into ChromaDB for vector search
        vector_store.index_files(
            connector_id=str(connector.id),
            provider=provider,
            files=mock_files,
        )

        connector.status = ConnectorStatus.CONNECTED
        connector.connected_at = datetime.now(timezone.utc)
        connector.file_count = len(files)
        return await self._connector_repo.update(connector)

    async def disconnect(self, provider: str) -> Connector:
        """Disconnect a provider and clear its files."""
        connector = await self._connector_repo.get_by_provider(provider)
        if not connector:
            connector = Connector(
                provider=ConnectorProvider(provider),
                status=ConnectorStatus.DISCONNECTED,
            )
            return await self._connector_repo.create(connector)

        await self._connector_repo.delete_files(connector.id)
        vector_store.remove_files(str(connector.id))

        connector.status = ConnectorStatus.DISCONNECTED
        connector.connected_at = None
        connector.file_count = 0
        return await self._connector_repo.update(connector)

    async def search_files(
        self, query: str, provider: str | None = None
    ) -> list[ConnectorFile]:
        """Search across connected files using vector similarity."""
        connector_id = None
        if provider:
            connector = await self._connector_repo.get_by_provider(provider)
            if connector:
                connector_id = str(connector.id)

        results = vector_store.search(query, connector_id=connector_id)

        # Convert to ConnectorFile entities
        return [
            ConnectorFile(
                connector_id=r["provider"],  # use provider as a reference
                name=r["name"],
                path=r["path"],
                file_type=r["file_type"],
                text_content=r["text_content"],
            )
            for r in results
        ]
