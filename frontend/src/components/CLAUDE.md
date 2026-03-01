# Components

Organized by domain. All are client components (`"use client"`).

## UI Base (`ui/`)

shadcn/ui components (Radix UI primitives + Tailwind). Do not edit directly — use `npx shadcn@latest add <component>` to add new ones.

Components: Button, Input, Label, Card, Dialog, Tabs, Table, Badge, Textarea, Select

## Domain Components

| Directory | Component | Purpose |
|-----------|-----------|---------|
| `deals/` | `CreateDealForm` | File upload + quick-extract auto-fill + deal creation form |
| `deals/` | `DealProgressBar` | 5-stage progress bar with spinner/checkmarks. Props: `hasDocuments`, `hasFields`, `hasAssumptions`, `hasValidations`, `activeStep`, `activeDetail` |
| `documents/` | `ProcessingTracker` | Document processing status with step-by-step progress dots |
| `extraction/` | `ExtractedFieldsTable` | Table of extracted fields (key, value, unit, confidence) |
| `assumptions/` | `AssumptionEditor` | Read-only assumption table — users can regenerate but not manually edit |
| `validation/` | `ValidationTable` | Expandable validation results with status badges. Click row → shows explanation, search steps, sources |
| `validation/` | `SearchStepTree` | Quick/deep search phase visualization — shows queries and result links per phase |

## Patterns

- **Status badges**: Use `Badge` with variant mapping (`within_range` → default, `above_market` → destructive, etc.)
- **Markdown links in explanations**: `markdownLinksToHtml()` converts `[text](url)` to `<a>` tags via regex
- **Expandable rows**: `ValidationTable` uses `expandedId` state — one row expanded at a time
- **No emoji** unless user explicitly requests it
