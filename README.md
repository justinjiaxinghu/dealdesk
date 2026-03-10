# DealDesk

AI-assisted real estate deal evaluation platform with agentic chat-driven market exploration. Upload an Offering Memorandum PDF, extract key data, generate AI-benchmarked underwriting assumptions, validate against market data, find comparable properties, and export to Excel. Explore markets freely with chat-powered search across web and connected file sources.

## Features

- **Exploration-First Workflow** — Chat-driven market exploration as the primary entry point, with optional deal context via OM upload
- **Agentic Chat** — GPT-4o with tool calling: web search (Tavily) and connected file search (ChromaDB) dynamically enabled based on user-selected source chips
- **PDF Ingestion** — Upload Offering Memorandum PDFs; text and tables extracted automatically with step-by-step progress tracking
- **AI Benchmarks** — GPT-4o generates market-aware assumptions (rent, vacancy, opex ratio, cap rate) with confidence ranges and source citations
- **Two-Phase Validation** — OM fields validated against market data via quick surface search followed by deep research
- **Comparable Properties** — Search comps via Rentcast API and Tavily web search with GPT-4o extraction
- **Connectors** — Cloud file storage integrations (OneDrive, Box, Google Drive, SharePoint) with ChromaDB vector search for semantic file retrieval
- **Reports** — Upload XLSX/PPTX templates with `{{marker}}` placeholders, detect fillable regions, and generate reports
- **Datasets** — Save properties from chat search results to datasets (deal-linked or standalone)
- **Financial Model** — DCF projection, sensitivity analysis, NOI, exit value, total cost, profit, and margin
- **Excel Export** — Download formatted .xlsx with Deal Inputs, Assumptions, and Model Output
- **Auto-Pipeline** — OM upload triggers extraction → historical financials → benchmarks → validation → comps automatically

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0 (async) |
| Database | SQLite (dev) / PostgreSQL (prod), Alembic migrations |
| PDF Processing | pdfplumber |
| LLM | OpenAI GPT-4o |
| Web Search | Tavily (validation + chat), Rentcast (comps) |
| Vector Search | ChromaDB (connector file semantic search) |
| Excel Export | openpyxl |
| Frontend | Next.js 16, React 19, TypeScript 5 |
| Styling | Tailwind CSS 4, shadcn/ui, Radix UI |
| Charts | Recharts |

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- OpenAI API key
- Tavily API key (for chat web search and validation)

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

# Run migrations (SQLite by default)
python -m alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on http://localhost:3000 and connects to the backend at http://localhost:8000.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEALDESK_DATABASE_URL` | `sqlite+aiosqlite:///./dealdesk.db` | Async DB URL |
| `DEALDESK_DATABASE_URL_SYNC` | `sqlite:///./dealdesk.db` | Sync DB URL (Alembic) |
| `DEALDESK_OPENAI_API_KEY` | `""` | OpenAI API key |
| `DEALDESK_OPENAI_MODEL` | `gpt-4o` | LLM model |
| `DEALDESK_FILE_STORAGE_PATH` | `./storage` | File storage directory |
| `DEALDESK_TAVILY_API_KEY` | `""` | Tavily API key |
| `DEALDESK_RENTCAST_API_KEY` | `""` | Rentcast API key |
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000/v1` | Frontend API base URL |

## Project Structure

```
backend/app/
  domain/          # Pure business logic, zero external deps
    entities/      # Dataclass entities (Deal, Document, Assumption, etc.)
    interfaces/    # ABCs for repos and providers
    value_objects/  # Enums and I/O types
  services/        # Business orchestration (Chat, Connector, Report, etc.)
  infrastructure/  # Concrete implementations
    persistence/   # SQLAlchemy repos + ORM models + Alembic
    document_processing/  # pdfplumber
    llm/           # OpenAI GPT-4o
    file_storage/  # Local filesystem
    export/        # openpyxl Excel
    comps/         # Rentcast + Tavily comp providers
    search/        # Tavily market search
    connectors/    # Mock data + ChromaDB vector store
  api/             # FastAPI routes + Pydantic schemas + DI
    v1/            # Versioned endpoints

frontend/src/
  interfaces/      # TypeScript types
  services/        # API client layer
  hooks/           # React data hooks (useDeal, useExploration, useChat)
  components/      # UI components organized by domain
  app/             # Next.js App Router pages

sample_templates/  # Example XLSX report templates
```

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

## License

Private — all rights reserved.
