# backend/app/domain/entities/field_validation.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import ValidationStatus


@dataclass
class FieldValidation:
    """
    The result of validating an extracted OM field against market data.

    After extracting fields from an OM (Offering Memorandum — the seller's
    marketing document), the system validates them by searching the web
    (via Tavily) for comparable market data. This helps analysts spot red
    flags — e.g., if the OM claims a 7% cap rate but market data shows 5%
    is typical for the area.

    Cap rate = Capitalization Rate = NOI / Property Value. A higher cap rate
    means higher yield but often higher risk.

    Validation runs in two phases:
    1. Quick surface search (1-2 queries) for fast initial results
    2. Deep research (up to 10 rounds) for thorough validation

    The search_steps field stores the full search DAG (Directed Acyclic Graph —
    the tree of queries and their results) showing every query made, which the
    frontend displays in expandable rows.
    """

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
