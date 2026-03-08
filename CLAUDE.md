# DealDesk

## Project Overview

AI-assisted real estate deal evaluation platform with agentic chat-driven market exploration. Ingests Offering Memorandum PDFs, extracts data, generates AI benchmarks, validates against market data, finds comparable properties, and exports to Excel. Two entry points: deal-specific workspace (auto-pipeline after upload) and standalone market exploration (free-form chat search).

## Architecture

Clean layered monorepo: backend (Python/FastAPI) + frontend (Next.js/TypeScript).

```
backend/app/
  domain/          # Pure business logic, zero external deps
    entities/      # Dataclass entities (Deal, Document, Assumption, Dataset, etc.)
    interfaces/    # ABCs for repos and providers (DealRepository, FileStorage, etc.)
    value_objects/  # Enums (PropertyType, ValidationStatus) and I/O types (PageText, etc.)
  services/        # Business orchestration (DealService, DocumentService, ChatService, etc.)
  infrastructure/  # Concrete implementations of domain interfaces
    persistence/   # SQLAlchemy repos + ORM models + Alembic migrations
    document_processing/  # pdfplumber
    llm/           # OpenAI GPT-4o
    file_storage/  # Local filesystem
    export/        # openpyxl Excel
    comps/         # Comparable property providers (Rentcast + Tavily)
    search/        # Market search provider (Tavily)
  api/             # FastAPI routes + Pydantic schemas + DI wiring
    v1/            # Versioned endpoints

frontend/src/
  interfaces/      # TypeScript types (hand-written)
  services/        # API client layer (fetch wrappers)
  hooks/           # React data hooks (useDeal, useExploration, useChat)
  components/      # UI components organized by domain
  app/             # Next.js App Router pages
```

## Layer Rules

1. `domain/` has zero imports from `infrastructure/`, `api/`, or external libraries
2. `services/` depends on `domain/interfaces/` only — never concrete implementations
3. `api/` is a thin translation layer: HTTP -> service -> HTTP
4. Dependency injection via FastAPI `Depends()`

## Commands

### Backend

```bash
# Environment
source ~/anaconda3/etc/profile.d/conda.sh && conda activate dealdesk

# Install
cd backend && pip install -e ".[dev]"

# Run server
cd backend && uvicorn app.main:app --reload

# Run tests
cd backend && python -m pytest tests/ -v

# Database migrations
cd backend && python -m alembic upgrade head
cd backend && python -m alembic revision --autogenerate -m "description"
```

### Frontend

```bash
cd frontend && npm install
cd frontend && npm run dev          # Dev server on :3000
cd frontend && npm run build        # Production build
cd frontend && npm run generate-types  # Regenerate TS types from OpenAPI (backend must be running)
```

## Environment Variables

All prefixed with `DEALDESK_`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEALDESK_DATABASE_URL` | `sqlite+aiosqlite:///./dealdesk.db` | Async DB URL |
| `DEALDESK_DATABASE_URL_SYNC` | `sqlite:///./dealdesk.db` | Sync DB URL (Alembic) |
| `DEALDESK_OPENAI_API_KEY` | `""` | OpenAI API key for benchmarks + chat |
| `DEALDESK_OPENAI_MODEL` | `gpt-4o` | LLM model name |
| `DEALDESK_FILE_STORAGE_PATH` | `./storage` | Local file storage directory |
| `DEALDESK_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |
| `DEALDESK_TAVILY_API_KEY` | `""` | Tavily API key for validation + chat search |
| `DEALDESK_RENTCAST_API_KEY` | `""` | Rentcast API key for comparable properties |

Frontend: `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000/v1`)

## API Routes

All routes under `/v1`:

### Deals
- `POST /v1/deals` — Create deal (also creates Base Case assumption set)
- `GET /v1/deals` — List deals (filter by property_type, city)
- `GET /v1/deals/{id}` — Get deal
- `PATCH /v1/deals/{id}` — Update deal

### Documents
- `POST /v1/deals/{id}/documents` — Upload PDF (triggers background processing)
- `GET /v1/deals/{id}/documents` — List documents
- `GET /v1/deals/{id}/documents/{doc_id}` — Get single document
- `GET /v1/deals/{id}/documents/{doc_id}/fields` — Extracted fields
- `GET /v1/deals/{id}/documents/{doc_id}/tables` — Extracted tables
- `GET /v1/deals/{id}/documents/{doc_id}/pdf` — Download PDF file
- `POST /v1/documents/quick-extract` — Extract deal metadata from first PDF page

### Assumptions & Benchmarks
- `GET /v1/deals/{id}/assumption-sets` — List assumption sets
- `POST /v1/deals/{id}/benchmarks:generate` — AI benchmark generation
- `GET /v1/assumption-sets/{id}/assumptions` — List assumptions
- `PUT /v1/assumption-sets/{id}/assumptions` — Bulk update assumptions

### Validation
- `POST /v1/deals/{id}/validate` — Validate OM fields against market data
- `GET /v1/deals/{id}/validations` — List field validations

### Historical Financials
- `POST /v1/deals/{id}/historical-financials/extract/{doc_id}` — Extract from document
- `GET /v1/deals/{id}/historical-financials` — List historical financials

### Comps
- `POST /v1/deals/{id}/comps/search` — Search comparable properties
- `GET /v1/deals/{id}/comps` — List comps

### Financial Model
- `POST /v1/assumption-sets/{id}/compute` — Run DCF projection
- `POST /v1/assumption-sets/{id}/sensitivity` — Run sensitivity analysis

### Export
- `POST /v1/assumption-sets/{id}/export/xlsx` — Create export record
- `GET /v1/assumption-sets/{id}/export/xlsx` — Download XLSX file

### Exploration & Chat
- `POST /v1/deals/{deal_id}/explorations` — Create exploration for a deal
- `POST /v1/explorations` — Create free-form exploration
- `GET /v1/explorations` — List saved explorations
- `GET /v1/explorations/free` — List free (no-deal) explorations
- `GET /v1/deals/{deal_id}/explorations` — List explorations for a deal
- `GET /v1/explorations/{id}` — Get exploration
- `PATCH /v1/explorations/{id}` — Update exploration (name, saved flag)
- `DELETE /v1/explorations/{id}` — Delete exploration
- `POST /v1/explorations/{id}/sessions` — Create chat session
- `GET /v1/explorations/{id}/sessions` — List chat sessions
- `DELETE /v1/sessions/{id}` — Delete chat session
- `POST /v1/sessions/{id}/messages` — Send message (triggers agentic chat loop)
- `GET /v1/sessions/{id}/messages` — List messages

### Datasets
- `POST /v1/datasets` — Create dataset
- `GET /v1/datasets` — List all datasets
- `GET /v1/datasets/free` — List standalone datasets
- `GET /v1/deals/{deal_id}/datasets` — List deal-linked datasets
- `GET /v1/datasets/{id}` — Get dataset
- `PATCH /v1/datasets/{id}` — Update dataset
- `POST /v1/datasets/{id}/properties` — Add properties to dataset
- `DELETE /v1/datasets/{id}` — Delete dataset

### Snapshots
- `POST /v1/snapshots` — Create snapshot
- `GET /v1/snapshots` — List snapshots
- `GET /v1/snapshots/{id}` — Get snapshot
- `DELETE /v1/snapshots/{id}` — Delete snapshot

### Other
- `GET /health` — Health check

## Key Patterns

- **Entity-Model Mappers**: `infrastructure/persistence/mappers.py` converts between domain dataclasses and SQLAlchemy ORM models
- **Processing Steps**: Document entity stores `processing_steps` as JSON for step-by-step progress tracking
- **Source Type Tracking**: Every assumption tracks its origin (OM, AI, Manual, AI_Edited)
- **Background Tasks**: Document processing runs via FastAPI BackgroundTasks
- **Auto-Pipeline**: Frontend deal workspace auto-chains extraction → historical financials → benchmarks → validation (quick + deep) → comps after document upload
- **Read-Only Assumptions**: Assumptions are AI-generated and displayed read-only; users can regenerate but not manually edit
- **Quick Extract**: Deal creation form sends the first page of the uploaded PDF to GPT-4o to auto-fill deal metadata fields
- **Two-Phase Validation**: OM field validation runs in two phases — quick surface search (basic Tavily, 1-2 queries) followed by deep research (advanced Tavily, up to 10 rounds). Each search call is logged as a `search_step` with phase, query, and results.
- **Agentic Chat**: Chat service uses OpenAI tool calling with `web_search` (Tavily). Assistant responses include structured `properties` JSON blocks for rendering property cards.
- **Datasets**: Properties from chat search results can be saved to datasets (deal-linked or standalone). Datasets store properties as a JSON array.
- **Exploration Sessions**: Chat explorations can be saved/bookmarked for later reference. Free explorations (no deal) are reused across page visits.

## Testing

- `backend/tests/test_golden_integration.py` — End-to-end pipeline test (deal → upload → extract → benchmarks → export) with LLM-as-judge validation
- pytest with `asyncio_mode = "auto"`
- Run: `cd backend && python -m pytest tests/ -v`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| Database | SQLite (dev) / PostgreSQL (prod), Alembic migrations |
| PDF Processing | pdfplumber (digital PDFs) |
| LLM | OpenAI GPT-4o |
| Web Search | Tavily (validation + chat), Rentcast (comps) |
| Excel Export | openpyxl |
| Frontend | Next.js 16, React 19, TypeScript 5 |
| Styling | Tailwind CSS 4, shadcn/ui, Radix UI |
| Charts | Recharts |
