"""Connector and ConnectorFile domain entities."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.value_objects.enums import ConnectorProvider, ConnectorStatus


@dataclass
class Connector:
    provider: ConnectorProvider
    status: ConnectorStatus = ConnectorStatus.DISCONNECTED
    file_count: int = 0
    connected_at: datetime | None = None
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class ConnectorFile:
    connector_id: str
    name: str
    path: str
    file_type: str
    text_content: str
    indexed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid4()))
