# Report AI Fill Workflow Design

## Goal

Replace the empty manual fill table with an AI-powered workflow: user selects connected file sources and optionally provides a prompt, GPT-4o infers values for each template region, user reviews/edits on a single scrollable page, then exports to Excel.

## Flow

1. **Context selection page** — User lands here after clicking "Fill Report"
   - Connector chip toggles (same style as chat search bar) — only connected providers selectable
   - Optional textarea for instructions/prompt
   - "Generate" button triggers AI fill

2. **Review page** — All regions on one scrollable page with AI values pre-filled in editable inputs
   - Edit any cell, add/remove rows
   - "Export to Excel" button at bottom

## Backend

- New endpoint: `POST /report-jobs/{id}/ai-fill`
  - Request: `{ connectors: string[], prompt?: string }`
  - Searches connected files via ChromaDB using template region labels/headers as queries
  - Sends template structure + file context + user prompt to GPT-4o with structured JSON output
  - Returns and saves fills per region to the job

- Existing `POST /report-jobs/{id}/generate` handles XLSX export (already works)

## Data Flow

```
User selects connectors + writes prompt
  -> POST /report-jobs/{id}/ai-fill
    -> ChromaDB search (region headers as queries)
    -> GPT-4o: template structure + file content + prompt -> JSON fills
    -> Save fills to job
  -> Frontend receives fills, renders review page
  -> User edits, clicks Export
  -> POST /report-jobs/{id}/generate (existing)
  -> Download XLSX
```

## Files

- `backend/app/services/report_service.py` — Add `ai_fill()` method
- `backend/app/api/v1/reports.py` — Add `POST /report-jobs/{id}/ai-fill` route
- `frontend/src/app/reports/[id]/fill/page.tsx` — Replace wizard with context selection + review page
- `frontend/src/services/report.service.ts` — Add `aiFill()` method
