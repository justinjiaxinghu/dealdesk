from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ExplorationSession:
    name: str
    id: UUID = field(default_factory=uuid4)
    deal_id: UUID | None = None
    saved: bool = False
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
