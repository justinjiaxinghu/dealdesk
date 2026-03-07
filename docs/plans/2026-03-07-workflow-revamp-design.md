# Workflow Revamp Design

## Overview

Revamp DealDesk from a linear OM-processing pipeline into a two-entry-point market intelligence platform. Users can either upload an OM to evaluate a specific deal, or freely explore the market — both through an agentic chat-driven interface.

## Entry Points

### 1. OM Upload (existing)
User uploads an OM via `/deals/new`. Creates a deal. Redirects to `/deals/[id]` where the pipeline auto-runs (extraction, benchmarks, validation, comps) and populates the left sidebar. The right pane is the exploration interface for researching in context of that deal.

### 2. Free Exploration (new)
User clicks "Explore Market" on the home page. Goes to `/explore` — full-width exploration interface with no deal context. No left sidebar, no pipeline. The user just searches and researches.

## Pages

### Home (`/`)
- "New Deal" button (existing)
- "Explore Market" button (new)
- Deals table (existing)
- Saved Explorations table (new): lists all saved ExplorationSessions with name, associated deal (if any), and save date

### Deal Creation (`/deals/new`)
Unchanged. PDF upload + quick-extract form.

### Deal Workspace (`/deals/[id]`)
Two-pane layout replacing the current tabbed workspace.

**Left Sidebar (~350px, collapsible sections):**
- Deal Summary: name, type, address, sqft
- PDF Preview: embedded OM viewer
- Extraction: key extracted fields with confidence indicators. Spinner while pipeline step runs, checkmark when done.
- Validation: summary badges (e.g., "4 in range, 1 above market")
- Assumptions: key metrics (cap rate, IRR, equity multiple)
- Financials: historical summary (NOI, revenue)
- Export XLSX button

Each section shows a spinner/loading indicator during its pipeline step and a checkmark when complete. Sections are collapsible with chevron toggles. Content is summarized (key metrics and status), not full tables.

**Right Pane:**
- Search bar at top: connector chips (multi-select per search) + text input + send button
- Tab bar: [Overview] + user-created conversation tabs + [+] button to create new tab
- Active tab content area

**Overview Tab (default):**
Dynamic based on what data exists across all sessions:
- If evaluation-type research exists: metric comparison dashboard (deal vs market averages)
- If exploration-type research exists: property card grid
- Both can coexist as separate sections

**Conversation Tabs:**
Each tab is a full conversation thread. Contains:
- Table/Chart toggle at top
- Scrollable message history (user messages + AI responses)
- AI responses include inline structured data: property cards, comparison tables, metric summaries
- Chart view shows the same data as comparative visualizations (bar charts, scatter plots) with the subject deal highlighted as a reference line

### Free Exploration (`/explore`)
Same right-pane UI as the deal workspace but full-width (no left sidebar). No deal context — the AI operates in pure research mode. No "vs Subject" comparisons.

### Saved Explorations
Accessed from the home page. Clicking a saved exploration resumes it at `/deals/[id]` (if deal-anchored) or `/explore` (if free).

## Property Modal
Clicking a property card anywhere opens a detail modal:
- Full property details (type, year built, size, units)
- All financial metrics
- "vs Subject Deal" comparison column (only when deal-anchored)
- Source attribution and links
- Header shows position counter ("2 of 8")
- Keyboard navigation: arrow keys or j/k to cycle, Esc to close
- Previous/Next buttons in the modal footer

## Data Model

### New Enums
```
ChatRole: USER | ASSISTANT | TOOL
ConnectorType: TAVILY | COSTAR | COMPSTACK | LOOPNET | REA_VISTA
```

### New Entities

**ExplorationSession** — Top-level saved research session.
```
ExplorationSession
  id: UUID
  deal_id: UUID | None      # set if OM-anchored, null if free exploration
  name: str                  # user-provided name on save
  saved: bool                # false = temporary, true = explicitly saved
  created_at: datetime
```

**ChatSession** — One conversation tab within an exploration.
```
ChatSession
  id: UUID
  exploration_session_id: UUID -> ExplorationSession
  title: str                 # tab name
  connectors: list[ConnectorType]
  created_at: datetime
  updated_at: datetime
```

**ChatMessage** — A single message in a conversation thread.
```
ChatMessage
  id: UUID
  session_id: UUID -> ChatSession
  role: ChatRole
  content: str               # markdown for assistant messages
  tool_calls: list[dict] | None  # tool calls made (assistant messages)
  created_at: datetime
```

**Snapshot** — Named point-in-time save of an exploration.
```
Snapshot
  id: UUID
  deal_id: UUID | None
  name: str
  session_data: dict         # JSON blob of all sessions + messages
  created_at: datetime
```

Restore: `POST /snapshots/{id}/restore` hydrates `session_data` back into live ExplorationSession + ChatSession + ChatMessage records with new UUIDs.

## API Endpoints

### Exploration Sessions
```
POST   /v1/deals/{id}/explorations           # Create exploration (deal-anchored)
POST   /v1/explorations                       # Create exploration (free)
GET    /v1/explorations                       # List all saved explorations
GET    /v1/explorations/{exploration_id}      # Get exploration with sessions
DELETE /v1/explorations/{exploration_id}      # Delete
PATCH  /v1/explorations/{exploration_id}      # Update (save/rename)
```

### Chat Sessions (tabs)
```
POST   /v1/explorations/{exploration_id}/sessions    # Create new tab
GET    /v1/explorations/{exploration_id}/sessions    # List tabs
GET    /v1/chat/sessions/{session_id}                # Get session with messages
DELETE /v1/chat/sessions/{session_id}                # Delete tab
PATCH  /v1/chat/sessions/{session_id}                # Rename tab
```

### Chat Messages
```
POST   /v1/chat/sessions/{session_id}/messages   # Send message (triggers agentic loop)
GET    /v1/chat/sessions/{session_id}/messages   # Get message history
```

`POST /messages` is the heavy endpoint. It runs the agentic loop and returns the full assistant response. No streaming for MVP — frontend shows a loading state.

### Snapshots
```
POST   /v1/explorations/{exploration_id}/snapshots   # Save snapshot
GET    /v1/deals/{id}/snapshots                      # List snapshots for deal
GET    /v1/snapshots                                 # List all snapshots
GET    /v1/snapshots/{snapshot_id}                   # Load snapshot (read-only)
POST   /v1/snapshots/{snapshot_id}/restore           # Restore to live sessions
DELETE /v1/snapshots/{snapshot_id}                   # Delete
```

## Backend Architecture

### ChatService (new)
The core agentic loop. When a user sends a message:

1. Load context:
   - If deal-anchored: deal summary, extracted fields, assumptions, validation results, comps, historical financials
   - Conversation history for this session
   - Selected connectors
2. Build system prompt with context + available tools
3. Send to GPT-4o with tool definitions
4. Agentic loop: if model calls tools, execute them, persist as `ChatMessage(role=TOOL)`, feed results back, repeat until model returns final response
5. Persist final `ChatMessage(role=ASSISTANT)` and return

### System Prompts

**OM-anchored:**
```
You are a real estate market intelligence assistant analyzing a deal.

Deal Context:
- Name, type, location, sqft
- Key metrics from extraction/assumptions
- Validation summary

All research should be contextualized against this property.
When returning property results, note how they compare to the subject deal.
```

**Free exploration:**
```
You are a real estate market intelligence assistant.
The user is exploring the market without a specific deal.
Help them research properties, find comps, and understand market trends.
```

### Agent Tools

| Tool | Description | Backend |
|------|-------------|---------|
| `web_search` | Search via Tavily (respects connector selection) | New MarketSearchProvider |
| `comp_lookup` | Search for comparable properties | Existing CompsProvider |
| `financial_model` | Run DCF with given assumptions | Existing FinancialModelService |
| `get_deal_context` | Retrieve current deal's extracted data | Existing repos |
| `get_validation` | Get validation results | Existing ValidationService |

Tools available depend on context: `get_deal_context`, `get_validation`, and `financial_model` are only available when deal-anchored.

### MarketSearchProvider (new)
Wraps Tavily (and mock connectors for future: CoStar, CompStack, etc.). Interface:
```
async search(query: str, connectors: list[ConnectorType], deal: Deal | None) -> list[SearchResult]
```

Returns structured results with source attribution. Mock connectors return empty results for now.

## Frontend Architecture

### New Components

**Layout:**
- `DealWorkspaceLayout` — Two-pane split, replaces current tabbed page
- `DealSidebar` — Collapsible sections with pipeline status indicators

**Chat:**
- `SearchBar` — Connector chips + text input + send button
- `SessionTabs` — Tab bar with Overview + conversation tabs + [+] button
- `ChatThread` — Renders conversation for active session
- `UserMessage` — User query bubble
- `AssistantMessage` — Markdown content with inline property cards / comparison data
- `ToolMessage` — Hidden by default (assistant summarizes results)

**Results:**
- `OverviewTab` — Dynamic: metric dashboard (evaluation data) and/or property card grid (exploration data)
- `PropertyCard` — Key metrics for a discovered property
- `PropertyModal` — Full detail modal with keyboard navigation (arrow/j/k, Esc)
- `ComparisonToggle` — Table/Chart switch
- `ComparisonChart` — Recharts bar/scatter charts with subject deal reference line

**Existing components reused:**
- `AssumptionPanel` (summarized in sidebar)
- shadcn/ui primitives (Badge, Card, Button, Table, Dialog)
- Pipeline progress logic (adapted for sidebar spinners)

### New Services
- `exploration.service.ts` — CRUD for ExplorationSessions
- `chat.service.ts` — Session CRUD + send message + get history
- `snapshot.service.ts` — Save/list/load/restore snapshots

### New Hooks
- `useExploration(explorationId)` — Fetches exploration with sessions
- `useChatSession(sessionId)` — Fetches messages, provides `sendMessage()` mutation
- `useDealSidebar(dealId)` — Fetches all sidebar data (deal, fields, validation, assumptions, financials)

### Charting
Add Recharts as a dependency for the comparison charts. Lightweight, React-native, supports bar charts, scatter plots, and reference lines.

## Pipeline Integration

The existing auto-pipeline (extraction -> benchmarks -> validation -> comps) runs unchanged on first visit to `/deals/[id]`. Instead of driving a progress bar, it drives the sidebar section states:
- Each section starts with a spinner
- As each pipeline step completes, the section updates to show a checkmark + summarized data
- Pipeline logic moves from the page component into the `DealSidebar` component

## Export

Retained as-is. The "Export XLSX" button in the left sidebar generates an Excel file from the current assumptions using the existing export service and hardcoded template.

## Decisions & Trade-offs

- **No streaming for MVP.** The agentic loop may take 10-30s with multiple tool calls. Frontend shows a loading indicator. SSE streaming can be added later.
- **Snapshot as JSON blob.** Simple and immutable. Restore endpoint hydrates back into live records.
- **Mock connectors.** ConnectorType enum includes CoStar, CompStack, etc. but only Tavily is implemented. Others return empty results. UI shows them as selectable but grayed out / "coming soon."
- **Intent is implicit, not classified.** The Overview tab renders based on what data exists (property results vs metric comparisons) rather than an explicit intent enum on the session.
- **No global state library.** Continue with service-first pattern + React hooks. Chat state is per-component, fetched via hooks.
