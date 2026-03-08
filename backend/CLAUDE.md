# Backend

Python 3.12+ / FastAPI / SQLAlchemy 2.0 async / Alembic

## Setup

```bash
source ~/anaconda3/etc/profile.d/conda.sh && conda activate dealdesk
cd backend && pip install -e ".[dev]"
```

## Commands

```bash
uvicorn app.main:app --reload          # Dev server on :8000
python -m pytest tests/ -v             # Run tests (asyncio_mode = "auto")
python -m alembic upgrade head         # Apply migrations
python -m alembic revision --autogenerate -m "desc"  # New migration
```

## Architecture

Clean layered architecture — dependency flows inward only:

```
api/ → services/ → domain/
                      ↑
infrastructure/ ──────┘ (implements domain interfaces)
```

- `domain/` has **zero** imports from infrastructure, api, or external libraries
- `services/` depend on `domain/interfaces/` ABCs — never concrete implementations
- `api/` is a thin translation layer: HTTP → service → HTTP
- DI via FastAPI `Depends()` — see `api/dependencies.py` for wiring

## Conventions

- All entities are `@dataclass` — no Pydantic in the domain layer
- Entity ↔ ORM model conversion via `infrastructure/persistence/mappers.py`
- Enums live in `domain/value_objects/enums.py`, frozen dataclasses in `types.py`
- Async throughout: SQLAlchemy async sessions, `asyncio.to_thread()` for sync ops (pdfplumber)
- Background tasks via FastAPI `BackgroundTasks` (document processing pipeline)
- Repos are per-session — constructed from session in `dependencies.py`
- Providers (LLM, file storage, comps, search) are singletons — constructed once at module level
- Auto table creation on startup via `Base.metadata.create_all` (dev); use Alembic for prod

## Key Dependencies

- FastAPI >= 0.115, SQLAlchemy[asyncio] >= 2.0, Pydantic >= 2.10
- openai >= 1.60, tavily-python >= 0.5, pdfplumber >= 0.11
- openpyxl >= 3.1, aiofiles >= 24.1
- Dev: pytest >= 8.0, pytest-asyncio >= 0.24, httpx >= 0.28, aiosqlite >= 0.20
