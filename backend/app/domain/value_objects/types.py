# backend/app/domain/value_objects/types.py
from dataclasses import dataclass, field

from app.domain.value_objects.enums import ProcessingStepStatus


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class ExtractedTable:
    page_number: int
    headers: list[str]
    rows: list[list[str]]
    confidence: float = 0.0


@dataclass(frozen=True)
class RawField:
    key: str
    value: str
    source_page: int


@dataclass(frozen=True)
class NormalizedField:
    key: str
    value_text: str | None
    value_number: float | None
    unit: str | None
    confidence: float


@dataclass(frozen=True)
class Location:
    address: str
    city: str
    state: str
    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True)
class BenchmarkSuggestion:
    key: str
    value: float
    unit: str
    range_min: float
    range_max: float
    source: str
    confidence: float


@dataclass(frozen=True)
class ProcessingStep:
    name: str
    status: ProcessingStepStatus
    detail: str = ""


@dataclass(frozen=True)
class QuickExtractResult:
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    property_type: str | None = None
    square_feet: float | None = None


@dataclass(frozen=True)
class HistoricalFinancialResult:
    period_label: str    # "T12", "2024", "2023"
    metric_key: str      # "gross_revenue", "noi", "expense_ratio", "occupancy_rate", etc.
    value: float
    unit: str | None = None


@dataclass
class DealFilters:
    property_type: str | None = None
    city: str | None = None


@dataclass(frozen=True)
class ValidationSource:
    url: str
    title: str
    snippet: str


@dataclass(frozen=True)
class FieldValidationResult:
    field_key: str
    om_value: float | None
    market_value: float | None
    status: str
    explanation: str
    sources: list[ValidationSource]
    confidence: float
    search_steps: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str  # connector name that produced this result
    raw_data: dict | None = None  # additional structured data if available
