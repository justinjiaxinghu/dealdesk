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
  hooks/        # React data hooks (useDeal, useDeals)
  components/   # UI components organized by domain
  app/          # Next.js App Router pages
```

## Conventions

- **All pages use `"use client"`** — no server components currently
- **Service-first API calls**: Never use raw `fetch()` in components. Always go through `services/*.ts`.
- **`apiFetch<T>(path, options)`** in `api-client.ts` is the base wrapper — adds `NEXT_PUBLIC_API_BASE` prefix, JSON headers, error handling via `ApiError`
- **`apiUpload<T>(path, formData)`** for multipart uploads (no Content-Type header — browser sets boundary)
- **Types are hand-written** in `interfaces/api.ts` — not auto-generated from OpenAPI (yet)
- **`useDeal(id)` hook** fetches all deal-related data (deal, documents, fields, assumptions, validations) in parallel. Only shows loading spinner on initial load, not during pipeline refreshes.

## Auto-Pipeline

The deal workspace page (`app/deals/[id]/page.tsx`) runs an automatic pipeline after document upload:

1. **Extract**: Polls `documentService.list()` every 2s until all docs complete
2. **Benchmarks**: If no assumptions exist, calls `assumptionService.generateBenchmarks()`
3. **Validate Quick**: Calls `validationService.validate(id, "quick")` — shows "Phase 1" in progress bar
4. **Validate Deep**: Calls `validationService.validate(id, "deep")` — shows "Phase 2" in progress bar

Pipeline state tracked via `pipelineStep` and `pipelineDetail` state variables, displayed in `DealProgressBar`.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000/v1` | Backend API base URL |
