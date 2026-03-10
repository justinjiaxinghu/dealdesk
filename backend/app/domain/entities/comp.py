# backend/app/domain/entities/comp.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import CompSource, PropertyType


@dataclass
class Comp:
    """
    A comparable property ("comp") used to benchmark a Deal.

    In real estate, analysts compare a target property against similar recently
    sold or listed properties to assess whether the asking price is reasonable.
    This entity stores data about comparable properties including:
    - Physical attributes (year built, units, square footage)
    - Pricing metrics (sale price, price per unit, price per sqft, cap rate)
    - Income metrics (rent per unit, occupancy, NOI)
    - Expense metrics (expense ratio, opex per unit)

    Key acronyms:
    - NOI (Net Operating Income): Annual rental income minus operating expenses,
      before debt service. The core measure of a property's profitability.
    - Cap rate (Capitalization Rate): NOI / Property Value. A 5% cap rate means
      $5 of NOI per $100 of property value. Lower cap = higher price = lower risk.
    - Opex (Operating Expenses): Costs to run the property (maintenance, taxes,
      insurance, utilities, management fees). Does NOT include mortgage payments.

    Comps can come from various sources (web search, databases, manual entry)
    tracked by the source field.
    """

    deal_id: UUID
    address: str
    city: str
    state: str
    property_type: PropertyType
    source: CompSource
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
