# backend/app/domain/entities/assumption.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import SourceType


@dataclass
class AssumptionSet:
    deal_id: UUID
    name: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Assumption:
    set_id: UUID
    key: str
    id: UUID = field(default_factory=uuid4)
    value_number: float | None = None
    unit: str | None = None
    range_min: float | None = None
    range_max: float | None = None
    source_type: SourceType = SourceType.MANUAL
    source_ref: str | None = None
    notes: str | None = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
