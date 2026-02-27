# backend/app/domain/entities/model_result.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ModelResult:
    set_id: UUID
    noi_stabilized: float
    exit_value: float
    total_cost: float
    profit: float
    profit_margin_pct: float
    id: UUID = field(default_factory=uuid4)
    computed_at: datetime = field(default_factory=datetime.utcnow)
