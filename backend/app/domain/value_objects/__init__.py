# backend/app/domain/value_objects/__init__.py
from app.domain.value_objects.enums import (
    DealStatus,
    DocumentType,
    ExportType,
    ProcessingStatus,
    PropertyType,
    SourceType,
    ValidationStatus,
)
from app.domain.value_objects.types import (
    BenchmarkSuggestion,
    DealFilters,
    ExtractedTable,
    FieldValidationResult,
    Location,
    NormalizedField,
    PageText,
    ProcessingStep,
    QuickExtractResult,
    RawField,
    ValidationSource,
)

__all__ = [
    "PropertyType",
    "DealStatus",
    "ProcessingStatus",
    "SourceType",
    "DocumentType",
    "ExportType",
    "ValidationStatus",
    "PageText",
    "ExtractedTable",
    "RawField",
    "NormalizedField",
    "Location",
    "BenchmarkSuggestion",
    "ProcessingStep",
    "QuickExtractResult",
    "DealFilters",
    "ValidationSource",
    "FieldValidationResult",
]
