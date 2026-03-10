# Domain Layer

Pure business logic with zero external dependencies. No imports from `infrastructure/`, `api/`, or third-party libraries.

## Entities (`entities/`)

All entities are plain `@dataclass` with `uuid4()` default IDs and `datetime.utcnow()` timestamps.

| Entity | Key Fields | Notes |
|--------|-----------|-------|
| `Deal` | name, address, city, state, property_type, square_feet, lat/lng | PropertyType enum |
| `Document` | deal_id, file_path, processing_status, processing_steps | Steps stored as list[ProcessingStep] |
| `Assumption` | set_id, key, value_number, unit, range_min/max, source_type, group, forecast_method | SourceType tracks origin (OM/AI/Manual/AI_Edited) |
| `AssumptionSet` | deal_id, name | "Base Case" created automatically with each deal |
| `ExtractedField` | document_id, field_key, value_text, value_number, unit, confidence | Numeric + text values |
| `MarketTable` | document_id, table_type, headers, rows, confidence | Extracted table data |
| `FieldValidation` | deal_id, field_key, om_value, market_value, status, search_steps | search_steps is list[dict] tracking the full search DAG |
| `Export` | deal_id, set_id, file_path, export_type | XLSX export record |
| `Comp` | deal_id, address, city, state, property_type, source, pricing/income/expense fields | CompSource enum (rentcast/tavily) |
| `HistoricalFinancial` | deal_id, period_label, metric_key, value, unit, source | Extracted from OM documents |
| `ExplorationSession` | deal_id (nullable), name, saved | Container for chat sessions; deal-linked or free |
| `ChatSession` | exploration_session_id, title, connectors | Individual chat thread |
| `ChatMessage` | session_id, role, content, tool_calls | ChatRole enum (user/assistant/tool) |
| `Dataset` | deal_id (nullable), name, properties | Properties stored as list[dict]; deal-linked or standalone |
| `Snapshot` | deal_id (nullable), name, session_data | Session state snapshot |
| `Connector` | provider, status, file_count, connected_at | ConnectorProvider + ConnectorStatus enums |
| `ConnectorFile` | connector_id, name, path, file_type, text_content, indexed_at | Files indexed in ChromaDB |
| `ReportTemplate` | name, file_format, file_path, regions | FillableRegion list (detected placeholders) |
| `ReportJob` | template_id, name, fills, status, output_file_path | ReportJobStatus enum (draft/completed) |
| `FillableRegion` | region_id, label, sheet_or_slide, region_type, headers, row_count | Detected fillable area in template |

## Interfaces (`interfaces/`)

ABCs that infrastructure must implement:

**Repositories** (`repositories.py`):
`DealRepository`, `DocumentRepository`, `ExtractedFieldRepository`, `MarketTableRepository`, `AssumptionSetRepository`, `AssumptionRepository`, `ExportRepository`, `FieldValidationRepository`, `CompRepository`, `HistoricalFinancialRepository`, `ExplorationSessionRepository`, `ChatSessionRepository`, `ChatMessageRepository`, `SnapshotRepository`, `DatasetRepository`

Note: Connector and Report repos are defined directly in infrastructure (not via domain interfaces) since they use concrete SQLAlchemy repos.

**Providers** (`providers.py`):
- `LLMProvider` — benchmarks, normalization, extraction, validation, historical financials
- `DocumentProcessor` — text/table extraction from PDFs
- `FileStorage` — store/retrieve/delete files
- `ExcelExporter` — deal + assumptions → XLSX bytes
- `CompsProvider` — search comparable properties
- `MarketSearchProvider` — web search for chat (Tavily)

## Value Objects (`value_objects/`)

- `enums.py`: `PropertyType`, `ProcessingStatus`, `DocumentType`, `SourceType`, `ValidationStatus`, `ExportType`, `CompSource`, `HistoricalFinancialSource`, `AssumptionGroup`, `ForecastMethod`, `Cadence`, `ProcessingStepStatus`, `ChatRole`, `ConnectorType`, `ConnectorProvider`, `ConnectorStatus`, `ReportFormat`, `ReportJobStatus`
- `types.py`: Frozen dataclasses for cross-layer data transfer — `FieldValidationResult`, `BenchmarkSuggestion`, `NormalizedField`, `PageText`, `ValidationSource`, `QuickExtractResult`, `HistoricalFinancialResult`, `SearchResult`, `Location`, `RawField`, `ExtractedTable`, `ProcessingStep`
