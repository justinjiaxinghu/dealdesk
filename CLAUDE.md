# DealDesk

## Project Overview

AI-assisted real estate deal evaluation platform. Ingests Offering Memorandum PDFs, extracts data, generates AI benchmarks, computes a back-of-envelope proforma model, and exports to Excel.

## Architecture

Clean layered monorepo: backend (Python/FastAPI) + frontend (Next.js/TypeScript).

```
backend/app/
  domain/          # Pure business logic, zero external deps
    entities/      # Dataclass entities (Deal, Document, Assumption, etc.)
    interfaces/    # ABCs for repos and providers (DealRepository, FileStorage, etc.)
    value_objects/  # Enums (PropertyType, DealStatus) and I/O types (PageText, etc.)
    model_engine.py # Deterministic financial model computation
  services/        # Business orchestration (DealService, DocumentService, etc.)
  infrastructure/  # Concrete implementations of domain interfaces
    persistence/   # SQLAlchemy repos + ORM models + Alembic migrations
    document_processing/  # pdfplumber
    llm/           # OpenAI GPT-4o
    file_storage/  # Local filesystem
    export/        # openpyxl Excel
  api/             # FastAPI routes + Pydantic schemas + DI wiring
    v1/            # Versioned endpoints

frontend/src/
  interfaces/      # TypeScript types (hand-written, OpenAPI codegen ready)
  services/        # API client layer (fetch wrappers)
  hooks/           # React data hooks (useDeal, useDeals)
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
| `DEALDESK_DATABASE_URL` | `postgresql+asyncpg://localhost:5432/dealdesk` | Async DB URL |
| `DEALDESK_DATABASE_URL_SYNC` | `postgresql://localhost:5432/dealdesk` | Sync DB URL (Alembic) |
| `DEALDESK_OPENAI_API_KEY` | `""` | OpenAI API key for benchmarks |
| `DEALDESK_OPENAI_MODEL` | `gpt-4o` | LLM model name |
| `DEALDESK_FILE_STORAGE_PATH` | `./storage` | Local file storage directory |
| `DEALDESK_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |

Frontend: `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000/v1`)

## API Routes

All routes under `/v1`:

- `POST /v1/deals` — Create deal (also creates Base Case assumption set)
- `GET /v1/deals` — List deals (filter by property_type, status, city)
- `GET /v1/deals/{id}` — Get deal
- `PATCH /v1/deals/{id}` — Update deal
- `POST /v1/deals/{id}/documents` — Upload PDF (triggers background processing)
- `GET /v1/deals/{id}/documents` — List documents
- `GET /v1/deals/{id}/documents/{doc_id}/fields` — Extracted fields
- `GET /v1/deals/{id}/documents/{doc_id}/tables` — Extracted tables
- `GET /v1/deals/{id}/assumption-sets` — List assumption sets
- `POST /v1/deals/{id}/benchmarks:generate` — AI benchmark generation
- `GET /v1/assumption-sets/{id}/assumptions` — List assumptions
- `PUT /v1/assumption-sets/{id}/assumptions` — Bulk update assumptions
- `POST /v1/assumption-sets/{id}/compute` — Compute model
- `GET /v1/assumption-sets/{id}/result` — Get model result
- `POST /v1/assumption-sets/{id}/export/xlsx` — Export to Excel
- `GET /health` — Health check

## Key Patterns

- **Entity-Model Mappers**: `infrastructure/persistence/mappers.py` converts between domain dataclasses and SQLAlchemy ORM models
- **Processing Steps**: Document entity stores `processing_steps` as JSON for step-by-step progress tracking
- **Source Type Tracking**: Every assumption tracks its origin (OM, AI, Manual, AI_Edited)
- **Background Tasks**: Document processing runs via FastAPI BackgroundTasks
- **Type Sharing**: Pydantic models are the single source of truth; frontend types generated via `openapi-typescript`

## Testing

- `backend/tests/test_model_engine.py` — 4 unit tests for ModelEngine (TDD)
- pytest with `asyncio_mode = "auto"`
- Run: `cd backend && python -m pytest tests/ -v`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| Database | PostgreSQL, Alembic migrations |
| PDF Processing | pdfplumber (digital PDFs) |
| LLM | OpenAI GPT-4o |
| Excel Export | openpyxl |
| Frontend | Next.js 16, React 19, TypeScript 5 |
| Styling | Tailwind CSS 4, shadcn/ui, Radix UI |
