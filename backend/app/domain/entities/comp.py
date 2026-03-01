# backend/app/domain/entities/comp.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Comp:
    deal_id: UUID
    address: str
    city: str
    state: str
    property_type: str
    source: str  # "rentcast" | "tavily"
    fetched_at: datetime
    id: UUID = field(default_factory=uuid4)
    # Physical
    year_built: int | None = None
    unit_count: int | None = None
    square_feet: float | None = None
    # Pricing
    sale_price: float | None = None
    price_per_unit: float | None = None
    price_per_sqft: float | None = None
    cap_rate: float | None = None
    # Income
    rent_per_unit: float | None = None
    occupancy_rate: float | None = None
    noi: float | None = None
    # Expenses
    expense_ratio: float | None = None
    opex_per_unit: float | None = None
    # Metadata
    source_url: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
