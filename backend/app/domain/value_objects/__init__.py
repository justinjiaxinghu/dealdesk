# backend/app/domain/value_objects/__init__.py
from app.domain.value_objects.enums import (
    DealStatus,
    DocumentType,
    ExportType,
    ProcessingStatus,
    PropertyType,
    SourceType,
)
from app.domain.value_objects.types import (
    BenchmarkSuggestion,
    DealFilters,
    ExtractedTable,
    Location,
    NormalizedField,
    PageText,
    ProcessingStep,
    RawField,
)

__all__ = [
    "PropertyType",
    "DealStatus",
    "ProcessingStatus",
    "SourceType",
    "DocumentType",
    "ExportType",
    "PageText",
    "ExtractedTable",
    "RawField",
    "NormalizedField",
    "Location",
    "BenchmarkSuggestion",
    "ProcessingStep",
    "DealFilters",
]
