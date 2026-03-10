# API Layer

FastAPI routes, Pydantic schemas, and dependency injection wiring. Thin translation: HTTP → service → HTTP.

## Routes (`v1/`)

All routes under `/v1` prefix. 17 route files:

| File | Routes | Notes |
|------|--------|-------|
| `deals.py` | CRUD `/deals` | List supports `property_type` and `city` filters |
| `documents.py` | `/deals/{id}/documents` | Upload triggers background processing; `/{doc_id}/pdf` serves file |
| `assumptions.py` | `/assumption-sets/{id}/assumptions` | GET + PUT (bulk update) |
| `validation.py` | `/deals/{id}/validate` | POST with optional `?phase=quick\|deep` query param |
| `exports.py` | `/assumption-sets/{id}/export/xlsx` | POST creates record, GET downloads file |
| `quick_extract.py` | `/documents/quick-extract` | Form auto-fill from first PDF page |
| `comps.py` | `/deals/{id}/comps` | POST search + GET list |
| `historical_financials.py` | `/deals/{id}/historical-financials` | POST extract from doc + GET list |
| `financial_model.py` | `/assumption-sets/{id}/compute`, `sensitivity` | DCF projection + sensitivity grid |
| `explorations.py` | `/explorations`, `/deals/{id}/explorations` | CRUD + list free/saved/by-deal |
| `chat.py` | `/explorations/{id}/sessions`, `/sessions/{id}/messages` | Chat session + message CRUD |
| `datasets.py` | `/datasets`, `/deals/{id}/datasets` | CRUD + add properties + list free/by-deal |
| `snapshots.py` | `/snapshots` | CRUD for session snapshots |
| `connectors.py` | `/connectors` | List, connect, disconnect, file search |
| `reports.py` | `/report-templates`, `/report-jobs` | Template upload, job CRUD, download |
| `om_upload.py` | `/explorations/{id}/om-upload` | OM upload with quick-extract + background processing |

## Schemas (`schemas.py`)

Pydantic models with `model_config = {"from_attributes": True}` for ORM compatibility.

- Request models: `CreateDealRequest`, `UpdateDealRequest`, `CreateDatasetRequest`, `AddPropertiesRequest`, etc.
- Response models mirror domain entities: `DealResponse`, `DocumentResponse`, `FieldValidationResponse`, `DatasetResponse`, etc.
- Nested response models: `ValidationSourceResponse`, `SearchStepResponse`, `ProcessingStepResponse`
- Entity → Response via `ResponseModel.model_validate(entity)`

## Dependencies (`dependencies.py`)

- **Singletons** (module-level): `_file_storage`, `_document_processor`, `_llm_provider`, `_excel_exporter`, `_combined_comps_provider`, `_market_search_provider`
- **Per-request**: `get_session()` yields async session, repos constructed from session
- **Repo factories**: `get_deal_repo()`, `get_document_repo()`, `get_dataset_repo()`, etc.
- **Service factories**: `get_deal_service()`, `get_document_service()`, `get_chat_service()`, etc. — compose repos + providers
- Used via `Annotated[ServiceType, Depends(get_service)]` in route signatures
