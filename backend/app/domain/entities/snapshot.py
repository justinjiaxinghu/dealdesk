from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Snapshot:
    name: str
    id: UUID = field(default_factory=uuid4)
    deal_id: UUID | None = None
    session_data: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
