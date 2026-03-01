# DealDesk

AI-assisted real estate deal evaluation platform. Upload an Offering Memorandum PDF, extract key data, generate AI-benchmarked underwriting assumptions, validate claims against live market data, and export to Excel — reducing deal screening from 3-4 hours to under 30 minutes.

## Features

- **PDF Ingestion** — Upload digitally-generated Offering Memorandum PDFs; text and tables are extracted automatically with step-by-step progress tracking
- **AI Benchmarks** — GPT-4o generates market-aware assumptions (rent, vacancy, opex ratio, cap rate) with confidence ranges and source citations
- **OM Validation** — Two-phase web search validates OM claims against live market data: a quick surface check followed by deep research with comparable transactions and market reports. Every search query and source is tracked in a visible research DAG.
- **Assumption Management** — View AI-generated assumptions with full source tracking (OM, AI, Manual, AI-Edited); regenerate benchmarks on demand
- **Excel Export** — Download a formatted .xlsx with Deal Inputs and Assumptions tabs
- **Deal Pipeline** — List, filter, and track deals by property type and city
- **Auto-Pipeline** — After document upload, extraction, benchmark generation, and validation run automatically with a live 5-stage progress bar

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async) |
| Database | SQLite (dev) / PostgreSQL (prod), Alembic migrations |
| PDF Processing | pdfplumber |
| LLM | OpenAI GPT-4o |
| Web Search | Tavily (for OM validation) |
| Excel Export | openpyxl |
| Frontend | Next.js 16, React 19, TypeScript 5 |
| Styling | Tailwind CSS 4, shadcn/ui, Radix UI |

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- OpenAI API key
- Tavily API key (for OM validation)

### Backend

```bash
# Create and activate conda environment
conda create -n dealdesk python=3.12
conda activate dealdesk

# Install dependencies
cd backend
pip install -e ".[dev]"

# Set up environment variables
export DEALDESK_OPENAI_API_KEY="your-key-here"
export DEALDESK_TAVILY_API_KEY="your-key-here"

# Run migrations (uses SQLite by default)
python -m alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

For PostgreSQL, also set:
```bash
export DEALDESK_DATABASE_URL="postgresql+asyncpg://localhost:5432/dealdesk"
export DEALDESK_DATABASE_URL_SYNC="postgresql://localhost:5432/dealdesk"
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on http://localhost:3000 and connects to the backend at http://localhost:8000.

## Project Structure

```
backend/app/
  domain/          # Pure business logic, zero external deps
    entities/      # Dataclass entities (Deal, Document, Assumption, etc.)
    interfaces/    # ABCs for repos and providers
    value_objects/  # Enums and I/O types
  services/        # Business orchestration
  infrastructure/  # Concrete implementations
    persistence/   # SQLAlchemy repos + ORM models + Alembic
    document_processing/  # pdfplumber
    llm/           # OpenAI GPT-4o + Tavily web search
    file_storage/  # Local filesystem
    export/        # openpyxl Excel
  api/             # FastAPI routes + Pydantic schemas + DI
    v1/            # Versioned endpoints

frontend/src/
  interfaces/      # TypeScript types
  services/        # API client layer
  hooks/           # React data hooks
  components/      # UI components by domain
  app/             # Next.js App Router pages
```

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

## License

Private — all rights reserved.
