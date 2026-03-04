from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class HistoricalFinancial:
    deal_id: UUID
    period_label: str
    metric_key: str
    value: float
    source: str           # "extracted" | "manual"
    id: UUID = field(default_factory=uuid4)
    unit: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
