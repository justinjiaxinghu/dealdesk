# backend/app/domain/entities/field_validation.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import ValidationStatus


@dataclass
class FieldValidation:
    deal_id: UUID
    field_key: str
    id: UUID = field(default_factory=uuid4)
    om_value: float | None = None
    market_value: float | None = None
    status: ValidationStatus = ValidationStatus.INSUFFICIENT_DATA
    explanation: str = ""
    sources: list[dict] = field(default_factory=list)
    confidence: float = 0.0
    search_steps: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
