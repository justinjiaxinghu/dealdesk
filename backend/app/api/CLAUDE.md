# API Layer

FastAPI routes, Pydantic schemas, and dependency injection wiring. Thin translation: HTTP → service → HTTP.

## Routes (`v1/`)

All routes under `/v1` prefix. Key endpoints:

| File | Routes | Notes |
|------|--------|-------|
| `deals.py` | CRUD `/deals` | List supports `property_type` and `city` filters |
| `documents.py` | `/deals/{id}/documents` | Upload triggers background processing pipeline |
| `assumptions.py` | `/assumption-sets/{id}/assumptions` | GET + PUT (bulk update) |
| `validation.py` | `/deals/{id}/validate` | POST with optional `?phase=quick\|deep` query param |
| `exports.py` | `/assumption-sets/{id}/export/xlsx` | POST creates record, GET downloads file |
| `quick_extract.py` | `/documents/quick-extract` | Form auto-fill from first PDF page |

## Schemas (`schemas.py`)

Pydantic models with `model_config = {"from_attributes": True}` for ORM compatibility.

- Request models: `CreateDealRequest`, `UpdateDealRequest`, etc.
- Response models mirror domain entities: `DealResponse`, `DocumentResponse`, `FieldValidationResponse`, etc.
- Nested response models: `ValidationSourceResponse`, `SearchStepResponse`, `ProcessingStepResponse`
- Entity → Response via `ResponseModel.model_validate(entity)`

## Dependencies (`dependencies.py`)

- **Singletons** (module-level): `_file_storage`, `_document_processor`, `_llm_provider`, `_excel_exporter`
- **Per-request**: `get_session()` yields async session, repos constructed from session
- **Service factories**: `get_deal_service()`, `get_document_service()`, etc. — compose repos + providers
- Used via `Annotated[ServiceType, Depends(get_service)]` in route signatures
