from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import HistoricalFinancialSource


@dataclass
class HistoricalFinancial:
    """
    A single historical financial data point for a Deal.

    OMs (Offering Memorandums) typically include several years of historical
    financial performance — revenue, expenses, NOI (Net Operating Income), etc.
    This entity stores one metric for one time period.

    Example: For a property's 2023 financials, you might have multiple
    HistoricalFinancial records:
    - period_label="2023", metric_key="revenue", value=500000
    - period_label="2023", metric_key="operating_expenses", value=200000
    - period_label="2023", metric_key="noi", value=300000

    The source field tracks whether this data was extracted from the OM by AI
    ("extracted") or entered manually by a user ("manual").
    """

    deal_id: UUID
    period_label: str
    metric_key: str
    value: float
    source: HistoricalFinancialSource = HistoricalFinancialSource.EXTRACTED
    id: UUID = field(default_factory=uuid4)
    unit: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
