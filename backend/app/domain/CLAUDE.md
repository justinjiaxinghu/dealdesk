# Domain Layer

Pure business logic with zero external dependencies. No imports from `infrastructure/`, `api/`, or third-party libraries.

## Entities (`entities/`)

All entities are plain `@dataclass` with `uuid4()` default IDs and `datetime.utcnow()` timestamps.

| Entity | Key Fields | Notes |
|--------|-----------|-------|
| `Deal` | name, address, city, state, property_type, square_feet | PropertyType enum |
| `Document` | deal_id, file_path, processing_status, processing_steps | Steps stored as list[ProcessingStep] |
| `Assumption` | set_id, key, value_number, unit, range_min/max, source_type | SourceType tracks origin (OM/AI/Manual/AI_Edited) |
| `AssumptionSet` | deal_id, name | "Base Case" created automatically with each deal |
| `ExtractedField` | document_id, field_key, value_text, value_number, unit, confidence | Numeric + text values |
| `FieldValidation` | deal_id, field_key, om_value, market_value, status, search_steps | search_steps is list[dict] tracking the full search DAG |

## Interfaces (`interfaces/`)

ABCs that infrastructure must implement:

- **Repositories**: `DealRepository`, `DocumentRepository`, `ExtractedFieldRepository`, `AssumptionSetRepository`, `AssumptionRepository`, `FieldValidationRepository`, `ExportRepository`, `MarketTableRepository`
- **Providers**: `LLMProvider` (benchmarks, normalization, extraction, validation), `DocumentProcessor` (text/table extraction), `FileStorage`, `ExcelExporter`

## Value Objects (`value_objects/`)

- `enums.py`: `PropertyType`, `ProcessingStatus`, `DocumentType`, `SourceType`, `ValidationStatus`, `ExportType`
- `types.py`: Frozen dataclasses for cross-layer data transfer — `FieldValidationResult`, `BenchmarkSuggestion`, `NormalizedField`, `PageText`, `ValidationSource`, etc.
