# backend/app/domain/entities/extraction.py
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class ExtractedField:
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
    document_id: UUID
    table_type: str
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    source_page: int | None = None
    confidence: float = 0.0
