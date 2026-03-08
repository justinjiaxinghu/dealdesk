# Frontend

Next.js 16 / React 19 / TypeScript 5 / Tailwind CSS 4 / shadcn/ui

## Commands

```bash
npm install
npm run dev          # Dev server on :3000
npm run build        # Production build
```

## Architecture

```
src/
  interfaces/   # Hand-written TypeScript types (api.ts)
  services/     # API client wrappers — all fetch calls go through here
  hooks/        # React data hooks (useDeal, useExploration, useChat)
  components/   # UI components organized by domain
  app/          # Next.js App Router pages
```

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Deals list | Table of deals + saved explorations section |
| `/deals/new` | Create deal | PDF upload + quick-extract auto-fill form |
| `/deals/[id]` | Deal workspace | Sidebar (summary, docs, assumptions, validations) + exploration chat pane |
| `/explore` | Market exploration | Standalone chat-driven property search (no deal context) |
| `/datasets` | Dataset list | Table of all datasets with property counts |
| `/datasets/[id]` | Dataset detail | Dynamic property table, inline rename, add/remove properties |

## Conventions

- **All pages use `"use client"`** — no server components currently
- **Service-first API calls**: Never use raw `fetch()` in components. Always go through `services/*.ts`.
- **`apiFetch<T>(path, options)`** in `api-client.ts` is the base wrapper — adds `NEXT_PUBLIC_API_BASE` prefix, JSON headers, error handling via `ApiError`
- **`apiUpload<T>(path, formData)`** for multipart uploads (no Content-Type header — browser sets boundary)
- **Types are hand-written** in `interfaces/api.ts` — not auto-generated from OpenAPI (yet)
- **`useDeal(id)` hook** fetches all deal-related data (deal, documents, fields, assumptions, validations, comps, historicals) in parallel
- **`useExploration(id)` hook** fetches exploration + chat sessions
- **`useChat(sessionId)` hook** fetches messages; exposes `setMessages` with `skipNextLoad` ref to prevent overwrites of optimistic messages

## Auto-Pipeline

The deal workspace page (`app/deals/[id]/page.tsx`) runs an automatic pipeline after document upload:

1. **Extract**: Polls `documentService.list()` every 2s until all docs complete
2. **Historical**: Calls `historicalFinancialService.extract()` for each completed doc
3. **Benchmarks**: If no assumptions exist, calls `assumptionService.generateBenchmarks()`
4. **Validate Quick**: Calls `validationService.validate(id, "quick")` — "Phase 1" in progress bar
5. **Validate Deep**: Calls `validationService.validate(id, "deep")` — "Phase 2" in progress bar
6. **Comps**: If no comps exist, calls `compsService.search()`

Pipeline state tracked via `pipelineStep` and `pipelineDetail` state variables.

## Services

| Service | Purpose |
|---------|---------|
| `deal.service` | Deal CRUD |
| `document.service` | Upload, list, field/table extraction, quick-extract |
| `assumption.service` | Assumption sets, assumptions, benchmark generation |
| `validation.service` | Field validation (quick + deep phases) |
| `export.service` | XLSX download |
| `comps.service` | Comparable property search + listing |
| `financial-model.service` | DCF compute + sensitivity analysis |
| `historical-financial.service` | Historical financials listing + extraction |
| `exploration.service` | Exploration session CRUD (listFree, listByDeal) |
| `chat.service` | Chat session + message operations |
| `dataset.service` | Dataset CRUD + add properties |
| `snapshot.service` | Snapshot CRUD |

## Key Patterns

- **Optimistic messages**: User messages are shown immediately before API completes; `skipNextLoad` ref prevents `useEffect` from overwriting them
- **Structured properties**: Assistant messages may contain ` ```properties ` JSON blocks parsed into interactive property cards
- **Add to Dataset**: Property cards have "Add to Dataset" dropdown — create new or add to existing
- **Exploration reuse**: Free explorations (no deal) are reused across page visits via `listFree()` instead of creating new ones each mount
- **Retry with backoff**: Deal exploration init retries up to 3 times with increasing delay

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000/v1` | Backend API base URL |
