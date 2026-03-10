# backend/app/domain/entities/extraction.py
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class ExtractedField:
    """
    A single data point extracted from a Document by the AI.

    When processing an OM (Offering Memorandum), the system uses GPT-4o to
    identify and extract key fields like:
    - "asking_price": the seller's listed price
    - "noi": NOI (Net Operating Income) — annual income minus operating expenses
    - "cap_rate": Capitalization Rate — NOI divided by property value, expressed
      as a percentage (e.g., 5% cap rate means $5 NOI per $100 of value)
    - "unit_count": number of rentable units

    Each extracted value is stored as an ExtractedField with:
    - field_key: standardized name (e.g., "asking_price")
    - value_text: raw text as it appeared in the document
    - value_number: parsed numeric value (if applicable)
    - unit: the unit of measurement (e.g., "$", "%", "sqft")
    - confidence: AI's confidence score (0.0 to 1.0)
    - source_page: which page the value was found on
    """

    document_id: UUID
    field_key: str
    id: UUID = field(default_factory=uuid4)
    value_text: str | None = None
    value_number: float | None = None
    unit: str | None = None
    confidence: float = 0.0
    source_page: int | None = None


@dataclass
class MarketTable:
    """
    A tabular data structure extracted from a Document.

    Offering Memorandums often contain tables like rent rolls, comparable sales,
    operating expense breakdowns, etc. This entity stores the raw table data
    (headers + rows) along with metadata about what type of table it is.

    Example table_types: "rent_roll", "comp_sales", "operating_expenses"
    """

    document_id: UUID
    table_type: str
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    source_page: int | None = None
    confidence: float = 0.0
