# Infrastructure Layer

Concrete implementations of domain interfaces. Each subdirectory implements one concern.

## Persistence (`persistence/`)

SQLAlchemy 2.0 async with ORM models.

- **`models.py`**: ORM models mirroring domain entities. Uses custom `UUIDType` for SQLite/PostgreSQL compatibility. JSON columns for `processing_steps`, `sources`, `search_steps`.
- **`mappers.py`**: Bidirectional `entity_to_model` / `model_to_entity` converters. Handles enum `.value` ↔ `Enum()` conversion and ProcessingStep serialization.
- **`database.py`**: Session factory and engine setup from `config.database_url`.
- **Repos** (`*_repo.py`): Each repo takes an `AsyncSession`, implements domain interface. Key patterns:
  - `bulk_upsert()` on assumptions: match by `(set_id, key)`, insert or update
  - `bulk_upsert()` on validations: match by `(deal_id, field_key)`
  - `update_processing_step()`: manages JSON array of processing steps on documents

## LLM (`llm/`)

`OpenAILLMProvider` — GPT-4o with structured JSON output.

- `generate_benchmarks()`: Market assumptions for a property location/type
- `normalize_extracted_fields()`: Canonical field names from raw extraction
- `quick_extract_deal_info()`: Lightweight first-page extraction for form auto-fill
- `validate_om_fields()`: Two-phase validation with Tavily web search
  - Phase parameter: `"quick"` (basic, 3 rounds), `"deep"` (advanced, 10 rounds), or `None` (both)
  - `_run_search_phase()`: Agentic loop — LLM calls `web_search` tool, we execute via Tavily, feed results back
  - `_extract_json()`: Robust JSON extraction from LLM responses (handles code blocks, embedded JSON, prose)
  - All completions use `response_format={"type": "json_object"}` even with tools

## Document Processing (`document_processing/`)

`PdfplumberProcessor` — wraps sync pdfplumber in `asyncio.to_thread()`. Extracts per-page text and tables.

## File Storage (`file_storage/`)

`LocalFileStorage` — filesystem-based storage at `DEALDESK_FILE_STORAGE_PATH`.

## Export (`export/`)

`OpenpyxlExcelExporter` — two-sheet XLSX workbook (Deal Inputs + Assumptions).
