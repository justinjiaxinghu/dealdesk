from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import ChatRole, ConnectorType


@dataclass
class ChatSession:
    exploration_session_id: UUID
    title: str
    id: UUID = field(default_factory=uuid4)
    connectors: list[ConnectorType] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ChatMessage:
    session_id: UUID
    role: ChatRole
    content: str
    id: UUID = field(default_factory=uuid4)
    tool_calls: list[dict] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
