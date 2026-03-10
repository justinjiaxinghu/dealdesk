# Workflow Revamp Design

Date: 2026-03-09
Status: Approved

## Context

User research interviews (Lauren Lam / Starwood, Henry Don / Bain Capital, Kurt Read / mid-market PE, Grace Bricken / Blackstone) consistently identified three pain points:

1. Workflows are question-driven, not deal-driven — users think in terms of "I need to find X" not "let me open Deal #47"
2. Data is scattered across OneDrive, Box, SharePoint with no search experience over it
3. Report/deck generation is painfully manual — 40-70 hrs/week copying data into tables

This redesign addresses all three by making Exploration the primary entry point, adding connector integrations, and building a template-based report generator.

## Approach

Incremental refactor. Keep existing backend entities (Deal, Exploration, ChatSession) and layer new features on top. Frontend restructures routes and navigation. Backend domain model stays intact — Deal still exists as an entity, it's just no longer the primary navigation entry point.

---

## Feature 1: Exploration-First Merge

### Navigation

Top nav changes from `Deals | Discovery | Datasets` to `Explore | Reports | Datasets | Connectors`.

- `/` redirects to `/explore`
- `/deals`, `/deals/new`, `/deals/[id]` routes are removed

### Explore Page (`/explore`)

**Default view (no exploration selected):** List of saved explorations + "New Exploration" button.

**Workspace view (`/explore?exploration=<id>`):** Full-height layout:

- **Left pane:** Collapsible deal sidebar. Only visible when an OM has been uploaded to this exploration. Identical to current `DealSidebar` — summary, docs, extracted fields, historicals, assumptions, validations, comps, export. Auto-pipeline (extract → historicals → benchmarks → validate → comps) runs in the sidebar with progress indicators.
- **Right pane:** Session tabs + chat thread + search bar (current exploration workspace).

### OM Upload Flow

- Search bar gets an **upload button** (document icon, tooltip "Upload Offering Memorandum")
- File picker filtered to `.pdf` only
- On upload, backend:
  1. Creates a Deal entity (auto-named from quick-extract or filename)
  2. Links Deal to the current Exploration (`exploration.deal_id = deal.id`)
  3. Triggers the existing auto-pipeline
- Deal sidebar panel slides open on the left, showing pipeline progress
- Chat context enriches with deal data as pipeline completes
- If exploration already has a deal linked, additional OMs are added as documents to the same deal
- Sidebar header shows "Offering Memorandum" with the filename

### Backend Changes

- New endpoint: `POST /v1/explorations/{id}/upload-om` — creates deal, links to exploration, uploads document, triggers pipeline
- Existing deal/document/pipeline endpoints remain unchanged

### Deleted Frontend Routes

- `app/deals/new/page.tsx`
- `app/deals/[id]/page.tsx` (logic moves into explore workspace)
- `app/page.tsx` (replaced by explore as home)

---

## Feature 2: Connectors (Mocked V1)

### Connectors Page (`/connectors`)

Grid of connector cards: **OneDrive, Box, Google Drive, SharePoint**.

Each card shows: icon, name, status (Connected / Not Connected), file count when connected.

- "Connect" is **mocked** — toggles status in backend, no real OAuth
- On connect, backend seeds hardcoded mock files (realistic RE documents: rent rolls, financial statements, lease agreements, IC memos)
- "Disconnect" clears the mock data

### Mock Data

Hardcoded fixtures in `infrastructure/connectors/mock_data.py` with pre-extracted text content for ~10-15 realistic files per connector. Populated into `connector_files` table on "connect".

### Chat Agent Integration

New tool alongside existing `web_search`:

- **`web_search`** — Tavily internet search (unchanged)
- **`connected_files_search`** — searches across `connector_files` text content
  - Parameters: `query` (string), `connector` (optional provider filter), `file_type` (optional)
  - Returns: file name, path, relevant text snippets, connector source

LLM decides which tool to use based on query context. Search bar connector chips become dynamic — Tavily always active, plus chips for each connected source.

### Backend Domain

- Entity: `Connector` — id, provider (enum: ONEDRIVE, BOX, GOOGLE_DRIVE, SHAREPOINT), status (connected/disconnected), connected_at
- Entity: `ConnectorFile` — id, connector_id, name, path, file_type, text_content, indexed_at
- Service: `ConnectorService` — toggle connect/disconnect, seed mock data, search file contents
- Tables: `connectors`, `connector_files`
- Endpoints:
  - `GET /v1/connectors` — list all connectors with status
  - `POST /v1/connectors/{provider}/connect` — mock connect + seed data
  - `POST /v1/connectors/{provider}/disconnect` — disconnect + clear data

### Not in V1

- No real OAuth / token storage
- No actual file indexing pipeline
- No vector/embedding search
- No folder scoping UI
- No write-back to cloud storage
- No real-time sync / webhooks

---

## Feature 3: Report Generator

### Reports Page (`/reports`)

Two sections:

- **Templates:** Uploaded PPTX/XLSX templates. Shows name, format, upload date, detected fillable region count.
- **Generated Reports:** Completed fills. Shows name, source template, date, download button.

### Template Upload

- "Upload Template" button → file picker for `.pptx, .xlsx`
- Backend parses template to detect fillable regions:
  - **PPTX:** Tables, text placeholders with `{{marker}}` syntax or empty table cells
  - **XLSX:** Empty cells adjacent to headers, cells with marker syntax
- Preview shown: "Found 12 tables across 45 slides"
- Template stored in file storage, metadata in `report_templates` table

### Copilot Fill Workflow (`/reports/{id}/fill`)

Section-by-section walkthrough of each detected region:

- **Left side:** Preview of the current slide/sheet region
- **Right side:** Data suggestion panel with ranked suggestions from:
  1. Connected source files (mock connector data)
  2. Exploration results (properties, comps from chat sessions)
  3. OM extracted data (if exploration has a linked deal)
  4. Web search (user can trigger fresh Tavily query)
- Actions per region: **Accept**, **Edit** manually, **Re-query**, **Skip**
- Progress bar: "Region 3 of 12"
- Back/Next navigation between regions

### Export

- "Generate Report" after all regions filled/skipped
- Backend fills original template preserving all styling/formatting
- Output saved to file storage, added to Generated Reports list
- Download in original format (PPTX or XLSX)

### Backend Domain

- Entity: `ReportTemplate` — id, name, file_format (pptx/xlsx), file_path, regions (JSON array), created_at
- Entity: `ReportJob` — id, template_id, name, fills (JSON: region_id → data), status (draft/completed), output_file_path, created_at
- Service: `ReportService` — template parsing, region detection, data suggestion, fill application, export
- Libraries: `python-pptx` (new), `openpyxl` (existing)
- Endpoints:
  - `POST /v1/report-templates` — upload template
  - `GET /v1/report-templates` — list templates
  - `GET /v1/report-templates/{id}` — get template with regions
  - `POST /v1/report-jobs` — create fill job from template
  - `PATCH /v1/report-jobs/{id}` — update fills for regions
  - `POST /v1/report-jobs/{id}/generate` — produce final document
  - `GET /v1/report-jobs/{id}/download` — download generated file

### Data Suggestion Engine

For each fillable region, matches region headers/labels against:
- Known field keys from extracted OM data
- Property fields from datasets/exploration results
- Falls back to "Search for this data" action (Tavily)

Suggestions returned as ranked list.

### Not in V1

- No chart generation — tables and text fills only
- No AI auto-detection of complex slide layouts — relies on table structures and marker syntax
- No collaborative editing
