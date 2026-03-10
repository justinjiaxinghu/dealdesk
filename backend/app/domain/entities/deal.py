# backend/app/domain/entities/deal.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import PropertyType


@dataclass
class Deal:
    """
    A real estate investment opportunity being evaluated.

    This is the top-level entity in the system. When a user wants to analyze
    a potential property acquisition, they create a Deal. Everything else
    (documents, assumptions, validations, exports) belongs to a Deal.

    Example: A user uploads an OM (Offering Memorandum — a marketing document
    sellers use to present a property for sale) for "123 Main St Apartments"
    and creates a Deal to track the evaluation process.
    """

    name: str
    address: str
    city: str
    state: str
    property_type: PropertyType
    id: UUID = field(default_factory=uuid4)
    latitude: float | None = None
    longitude: float | None = None
    square_feet: float | None = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
