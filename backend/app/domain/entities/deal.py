# backend/app/domain/entities/deal.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import PropertyType


@dataclass
class Deal:
    name: str
    address: str
    city: str
    state: str
    property_type: PropertyType
    id: UUID = field(default_factory=uuid4)
    latitude: float | None = None
    longitude: float | None = None
    square_feet: float | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
