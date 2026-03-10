# Components

Organized by domain. All are client components (`"use client"`).

## UI Base (`ui/`)

shadcn/ui components (Radix UI primitives + Tailwind). Do not edit directly — use `npx shadcn@latest add <component>` to add new ones.

Components: Button, Input, Label, Card, Dialog, Tabs, Table, Badge, Textarea, Select, FilterChip, Popover

## Domain Components

| Directory | Component | Purpose |
|-----------|-----------|---------|
| `deals/` | `CreateDealForm` | File upload + quick-extract auto-fill + deal creation form |
| `deals/` | `DealProgressBar` | Multi-stage progress bar with spinner/checkmarks |
| `documents/` | `ProcessingTracker` | Document processing status with step-by-step progress dots |
| `extraction/` | `ExtractedFieldsTable` | Table of extracted fields (key, value, unit, confidence) |
| `assumptions/` | `AssumptionEditor` | Read-only assumption table — users can regenerate but not manually edit |
| `assumptions/` | `AssumptionPanel` | Assumption panel UI wrapper |
| `validation/` | `ValidationTable` | Expandable validation results with status badges |
| `validation/` | `SearchStepTree` | Quick/deep search phase visualization — shows queries and result links per phase |
| `validation/` | `ValidationDetailModal` | Modal showing OM vs Market values, confidence, explanation, search steps, sources |
| `comps/` | `CompCard` | Comparable property card |
| `comps/` | `CompsTab` | Comps tab container |
| `historical/` | `HistoricalFinancialsTab` | Historical financials display tab |
| `sensitivity/` | `SensitivityTab` | Sensitivity analysis tab |
| `sensitivity/` | `SensitivityTable` | Sensitivity data table |
| `exploration/` | `SearchBar` | ChatGPT-style bottom-positioned input with auto-resize textarea, send button, connector chips |
| `exploration/` | `SessionTabs` | Chat session dropdown selector + New Chat + Save/Bookmark + inline rename |
| `exploration/` | `ChatThread` | Chat message list with auto-scroll, loading indicator with source pills |
| `exploration/` | `UserMessage` | User message bubble |
| `exploration/` | `AssistantMessage` | Assistant message with markdown rendering, property cards, detail modal, "Add to Dataset" button |
| `exploration/` | `PropertyCard` | Compact property card in search results (clickable) |
| `exploration/` | `PropertyModal` | Full property detail modal |
| `exploration/` | `ComparisonToggle` | Toggle for comparison mode |
| `exploration/` | `ComparisonChart` | Comparison chart visualization |
| `layout/` | `DealSidebar` | Sidebar for deal workspace with deal summary, documents, assumptions, validations, historical financials, pipeline progress banner |

## Patterns

- **Status badges**: Use `Badge` with variant mapping (`within_range` → default, `above_market` → destructive, etc.)
- **Markdown rendering**: `AssistantMessage` has a custom markdown renderer handling paragraphs, bold, headers, lists, code blocks, tables, and links
- **Property extraction**: `extractProperties()` parses ` ```properties ` fenced JSON blocks from assistant content into `PropertyData[]`
- **Expandable rows**: `ValidationTable` uses `expandedId` state — one row expanded at a time
- **Validation detail modal**: Sidebar validation rows are clickable buttons opening `ValidationDetailModal`
- **Connector chips**: `SearchBar` renders toggleable `FilterChip` components for each connected source. Disabled chips shown for unconnected providers.
- **Chat rename**: `SessionTabs` supports inline rename via pencil icon (hover to reveal). Enter commits, Escape cancels.
- **Loading source pills**: `ChatThread` shows animated pills during loading indicating which sources are being queried (e.g., "OneDrive", "Web Search")
- **No emoji** unless user explicitly requests it
