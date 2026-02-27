# DealDesk MVP Design

## Overview

DealDesk is an AI-assisted real estate deal evaluation platform. It ingests Offering Memorandum PDFs, extracts key deal/market data, generates AI-suggested underwriting assumptions, and produces a "Back of the Envelope" proforma — reducing screening time from 3-4 hours to <30 minutes.

This document covers the MVP design (P0 user stories from the PRD).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL |
| PDF Processing | pdfplumber (digital PDFs only) |
| LLM Provider | OpenAI GPT-4o (structured outputs) |
| File Storage | Local filesystem (MVP), interface for S3 later |
| Excel Export | openpyxl |
| Frontend | Next.js 14+ (App Router), React, TypeScript |
| Styling | Tailwind CSS + shadcn/ui |
| Type Sharing | OpenAPI codegen (Pydantic → openapi-typescript) |
| Testing | pytest (backend), Vitest (frontend) |

## Architecture: Monorepo with Clean Layered Design

### Project Structure

```
dealdesk/
├── backend/
│   ├── app/
│   │   ├── domain/                  # Pure business logic, no framework deps
│   │   │   ├── entities/            # Deal, Document, Assumption, ModelResult
│   │   │   ├── interfaces/          # ABCs: repos, services, providers
│   │   │   └── value_objects/       # PropertyType enum, Money, Confidence
│   │   ├── services/                # Use cases: CreateDeal, ProcessDocument, etc.
│   │   ├── infrastructure/          # Concrete implementations
│   │   │   ├── persistence/         # SQLAlchemy repos implementing domain interfaces
│   │   │   ├── document_processing/ # pdfplumber implementation
│   │   │   ├── llm/                 # OpenAI implementation
│   │   │   ├── file_storage/        # Local filesystem implementation
│   │   │   └── export/              # openpyxl Excel generator
│   │   ├── api/                     # FastAPI routers (thin: validate → delegate → respond)
│   │   │   └── v1/                  # Versioned routes
│   │   ├── config.py                # Pydantic BaseSettings
│   │   └── main.py                  # App factory, DI wiring
│   ├── alembic/                     # DB migrations
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── interfaces/              # Auto-generated TypeScript types from OpenAPI
│   │   ├── services/                # API client classes
│   │   ├── components/              # React components
│   │   ├── app/                     # Next.js app router pages
│   │   └── hooks/                   # Custom React hooks
│   ├── package.json
│   └── tsconfig.json
└── docs/plans/
```

### Layer Rules

1. `domain/` has zero imports from `infrastructure/`, `api/`, or external libraries
2. `services/` depends on `domain/interfaces/` only — never on concrete implementations
3. `api/` is a thin translation layer: HTTP → service → HTTP
4. Dependency injection via FastAPI `Depends()`

## Domain Model

### Entities

```
Deal            id, name, address, city, state, lat/lng, property_type, status
Document        id, deal_id, type, file_path, processing_status, processing_steps (JSON)
ExtractedField  id, document_id, field_key, value_text, value_number, unit, confidence, source_page
MarketTable     id, document_id, table_type, headers (JSON), rows (JSON), source_page, confidence
AssumptionSet   id, deal_id, name
Assumption      id, set_id, key, value_number, unit, range_min/max, source_type, source_ref, notes
ModelResult     id, set_id, noi_stabilized, exit_value, total_cost, profit, profit_margin_pct
Export          id, deal_id, set_id, file_path, type
```

### Core Interfaces (Python ABCs)

**Repository Interfaces (data access):**

```python
class DealRepository(ABC):
    async def create(self, deal: Deal) -> Deal
    async def get_by_id(self, id: UUID) -> Deal | None
    async def list(self, filters: DealFilters) -> list[Deal]
    async def update(self, deal: Deal) -> Deal

class DocumentRepository(ABC)         # CRUD + get_by_deal_id + update_processing_step
class ExtractedFieldRepository(ABC)    # CRUD + get_by_document_id + bulk_create
class MarketTableRepository(ABC)       # CRUD + get_by_document_id + bulk_create
class AssumptionSetRepository(ABC)     # CRUD + get_by_deal_id
class AssumptionRepository(ABC)        # CRUD + bulk_upsert + get_by_set_id
class ModelResultRepository(ABC)       # create + get_by_set_id
class ExportRepository(ABC)            # create + get_by_deal_id
```

**Service Interfaces (external capabilities):**

```python
class DocumentProcessor(ABC):
    async def extract_text(self, file_path: Path) -> list[PageText]
    async def extract_tables(self, file_path: Path) -> list[ExtractedTable]

class LLMProvider(ABC):
    async def generate_benchmarks(self, location: Location, property_type: PropertyType) -> list[BenchmarkSuggestion]
    async def normalize_extracted_fields(self, raw_fields: list[RawField]) -> list[NormalizedField]

class FileStorage(ABC):
    async def store(self, file: UploadFile, path: str) -> str
    async def retrieve(self, path: str) -> Path
    async def delete(self, path: str) -> None

class ExcelExporter(ABC):
    async def export(self, deal: Deal, assumptions: list[Assumption], results: ModelResult) -> Path
```

## Type Sharing: OpenAPI Codegen

Single source of truth: Pydantic models in the backend.

```
Pydantic models → FastAPI → OpenAPI spec (auto) → openapi-typescript → TypeScript types (auto)
```

- Backend defines request/response schemas as Pydantic models
- FastAPI auto-generates `/openapi.json`
- `npx openapi-typescript` generates `src/interfaces/api.ts`
- Frontend API client classes use generated types
- No manual TypeScript type duplication

## Data Flows

### Flow 1: Create Deal + Upload OM

```
POST /v1/deals → create deal record
POST /v1/deals/{id}/documents → upload PDF
  → FileStorage.store() saves locally
  → DocumentRepository.create() records metadata
  → Background task: process_document(doc_id)

process_document (background):
  Step 1: FileStorage.retrieve()
  Step 2: DocumentProcessor.extract_text() → pages with text
  Step 3: DocumentProcessor.extract_tables() → structured tables
  Step 4: LLMProvider.normalize_extracted_fields() → canonical field keys
  Step 5: Persist extracted fields + tables to DB
  Each step updates Document.processing_steps for real-time progress tracking
```

### Flow 2: Generate Benchmarks

```
POST /v1/deals/{id}/benchmarks:generate
  → LLMProvider.generate_benchmarks(location, property_type)
  → Returns rent, vacancy, opex_ratio, cap_rate with ranges + sources
  → AssumptionRepository.bulk_upsert() merges with OM-extracted values
```

### Flow 3: Compute Model

```
POST /v1/assumption-sets/{id}/compute
  → ModelEngine.compute(assumptions) — pure deterministic math:
    NOI = (rent_psf × sqft × (1 - vacancy)) - (opex_ratio × revenue)
    exit_value = NOI / cap_rate
    profit = exit_value - total_cost
    margin = profit / total_cost
  → ModelResultRepository.create()
```

### Flow 4: Export to Excel

```
POST /v1/assumption-sets/{id}/export/xlsx
  → ExcelExporter.export(deal, assumptions, results)
  → Generates .xlsx with Inputs, Outputs, and Assumptions tabs
  → FileStorage.store() saves file
  → Returns download URL
```

### Background Tasks

MVP uses FastAPI BackgroundTasks (built-in). Only document processing runs in background. Interface boundaries allow migration to Celery later without changing business logic.

## Frontend Design

### Pages

```
/                  → Deal list (table: name, address, type, status, date)
/deals/new         → Create deal wizard (name, address, property type, upload OM)
/deals/[id]        → Deal workspace (main screen)
/deals/[id]/export → Export confirmation + download
```

### Deal Workspace Layout

Tabbed workspace with 4 tabs:

- **Overview**: Deal metadata, uploaded documents, processing status
- **Extraction**: Extracted fields table (editable, with confidence indicators), market tables
- **Assumptions**: Key assumptions with AI-suggested ranges, source tags, editable values
- **Model**: Inputs summary → outputs (NOI, exit value, costs, profit/loss, margin)

### Global Deal Progress Bar

```
Upload OM → Extract Data → Set Assumptions → Compute Model → Export
   ✓           ✓              ● current           ○            ○
```

### Frontend Architecture

```
src/
  interfaces/api.ts         # Auto-generated from OpenAPI
  services/
    api-client.ts           # Base HTTP client (fetch wrapper)
    deal.service.ts         # DealService
    document.service.ts     # DocumentService
    assumption.service.ts   # AssumptionService
    export.service.ts       # ExportService
  components/
    deals/                  # DealList, DealCard, CreateDealForm
    extraction/             # ExtractedFieldsTable, MarketTableView
    assumptions/            # AssumptionEditor, BenchmarkRangeSlider
    model/                  # ModelOutputs, ProfitLossCard
    ui/                     # Shared: Button, Input, Table, Tabs, Badge
  app/                      # Next.js App Router pages
  hooks/                    # useDeal, useAssumptions, useModelResults
```

## User Observability

Core principle: every async operation has a visible status, every step shows progress.

### Document Processing — Step Tracker

```
Step 1: Uploading PDF         ✓ Complete
Step 2: Extracting text       ✓ Complete (12 pages found)
Step 3: Detecting tables      ● In progress...
Step 4: Normalizing fields    ○ Pending
Step 5: Ready for review      ○ Pending
```

Backend stores `processing_steps` JSON on Document entity. Frontend polls for updates.

### Extraction Confidence — Visual Indicators

- Green (>0.9): High confidence
- Yellow (0.7-0.9): Review recommended
- Red (<0.7): Low confidence, needs verification
- Source badge: "From OM Page 3" / "AI Normalized"

### Assumption Source Tags

- `[OM]` — Extracted from offering memorandum
- `[AI]` — Generated by benchmark AI
- `[Manual]` — User entered/edited
- `[AI → Edited]` — AI-generated, then modified by user

### Model Staleness

- Changed assumptions highlighted
- "Model outdated — 2 assumptions changed" warning
- Results show computation timestamp

### Export Progress

```
Generating Excel...  [████████░░] 80%
✓ Ready — Download dealdesk-123-main-st.xlsx
```

## Error Handling

- **PDF processing failure**: Status set to `failed` with human-readable message. "Retry" button.
- **LLM errors**: Partial results returned where possible, with `[AI — Error]` tags on failed assumptions.
- **Validation errors**: Structured 422 responses with field-level messages.
- **Computation errors**: Clear message: "Cannot compute — missing: rent_psf_yr, cap_rate"
- **No silent failures**: Every error persisted, surfaced in UI, and actionable.

## Testing Strategy

**Backend:**
- Unit tests for ModelEngine (deterministic math with known inputs/outputs)
- Unit tests with mocks for services (mock repo + provider interfaces)
- Integration tests for API routes (test DB)
- Fixture PDFs (2-3 sample OMs) for extraction tests

**Frontend:**
- Component tests (Vitest + Testing Library) for interactive components
- API client tests against mocked HTTP responses

## MVP Scope Summary

**In:**
- Deal creation + OM PDF upload
- Document processing (text + table extraction) with step-by-step progress
- AI benchmark generation (rent, vacancy, opex ratio, cap rate)
- Back of the Envelope model (deterministic computation)
- Assumption editing with source tracking + audit trail
- Excel export (.xlsx)
- Deal list with status

**Out:**
- Full proforma (monthly schedules, debt waterfalls)
- Comps database
- Zoning parsing
- Multi-user collaboration/permissions
- Real-time collaboration (SSE/WebSocket)
