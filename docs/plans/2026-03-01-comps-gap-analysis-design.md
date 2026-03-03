# Comparable Properties & Gap Analysis — Design

**Date:** 2026-03-01
**Status:** Approved

## Overview

Add a "Comps & Gap Analysis" tab to the deal workspace that fetches real comparable properties based on extracted deal data, stores them in the database, and displays a gap analysis table + individual comp cards with per-metric visualizations.

---

## Data Sources

- **Rentcast free tier** — structured JSON for nearby properties (cap rate, price/unit, rent/unit, etc.)
- **Tavily + GPT-4o** — targeted Zillow/Redfin scraping to fill metric gaps Rentcast doesn't cover

New env var: `DEALDESK_RENTCAST_API_KEY`

---

## Data Model

New `Comp` domain entity and `comps` DB table:

```python
@dataclass
class Comp:
    deal_id: UUID
    id: UUID = uuid4()
    # Identity
    address: str
    city: str
    state: str
    # Physical
    property_type: str
    year_built: int | None
    unit_count: int | None
    square_feet: float | None
    # Pricing
    sale_price: float | None
    price_per_unit: float | None
    price_per_sqft: float | None
    cap_rate: float | None
    # Income
    rent_per_unit: float | None
    occupancy_rate: float | None
    noi: float | None
    # Expenses
    expense_ratio: float | None
    opex_per_unit: float | None
    # Metadata
    source: str          # "rentcast" | "tavily"
    source_url: str | None
    fetched_at: datetime
```

DB upsert key: `(deal_id, address)`.

---

## Backend Architecture

### Domain Layer

- `domain/entities/comp.py` — `Comp` dataclass
- `domain/interfaces/repositories.py` — add `CompRepository` ABC with `list_by_deal_id()`, `bulk_upsert()`
- `domain/interfaces/providers.py` — add `CompsProvider` ABC with `search_comps(deal, extracted_fields) -> list[Comp]`
- `domain/value_objects/types.py` — no new types needed; `Comp` entity is the transfer type

### Service Layer

- `services/comps_service.py` — `CompsService`
  - `search_comps(deal_id)`: fetches deal + extracted fields → calls provider → bulk-upserts → returns `list[Comp]`
  - `list_comps(deal_id)`: returns cached comps from DB

### Infrastructure Layer

- `infrastructure/comps/rentcast_provider.py` — `RentcastCompsProvider`
  - Calls Rentcast `/v1/properties` endpoint with lat/long radius + property type filter
  - Maps response to `list[Comp]` with `source="rentcast"`
- `infrastructure/comps/tavily_provider.py` — `TavilyCompsProvider`
  - Uses existing `AsyncTavilyClient` with targeted queries (e.g. `"multifamily sold Austin TX 2024 site:zillow.com"`)
  - GPT-4o extracts structured comp data from search results (same agentic loop as validation)
  - Maps results to `list[Comp]` with `source="tavily"`
- `infrastructure/comps/combined_provider.py` — `CombinedCompsProvider`
  - Runs Rentcast + Tavily in parallel, merges, dedupes by address
- `infrastructure/persistence/comp_repo.py` — `SqlAlchemyCompRepository`
- `infrastructure/persistence/models.py` — add `CompModel`
- `infrastructure/persistence/mappers.py` — add `comp_to_entity` / `comp_to_model`

### API Layer

Two new routes under `/v1/deals/{id}`:
- `POST /v1/deals/{id}/comps:search` — triggers fetch + upsert, returns `list[CompResponse]`
- `GET /v1/deals/{id}/comps` — returns cached comps

New Pydantic schema: `CompResponse` in `api/v1/schemas.py` (or new `api/v1/comps.py`).

DI wiring in `api/dependencies.py`: `get_comps_service()` factory.

### Alembic Migration

New migration for `comps` table.

---

## Frontend Architecture

### Pipeline Extension

Stage 5 added after deep validation:

```
Upload → Extract → Benchmarks → Validate → Comps → Done
```

- `pipelineStep` type gains `"comps"` value
- After deep validation, if `comps.length === 0`, auto-calls `compsService.search(dealId)`
- Progress bar extended from 5 to 6 stages in `DealProgressBar`

### New Files

- `services/comps.service.ts`
  - `search(dealId): Promise<Comp[]>` — POST comps:search
  - `list(dealId): Promise<Comp[]>` — GET comps
- `components/comps/comps-tab.tsx` — full tab: gap analysis table + comp card grid + "Re-fetch Comps" button
- `components/comps/comp-card.tsx` — individual comp card with dual dot-on-line charts

### `useDeal` Hook

Add `comps: Comp[]` to the hook's fetched data (parallel with existing fetches).

### Comps Tab Layout

**Top — Gap Analysis Table:**

| Metric | Subject | Comp Avg | Gap | Status |
|--------|---------|----------|-----|--------|
| Cap Rate | 5.2% | 6.1% | -0.9% | ▼ Below |
| Price/Unit | $185k | $162k | +14% | ▲ Above |
| Rent/Unit | $1,450 | $1,380 | +5% | ▲ Above |
| Occupancy | 94% | 91% | +3% | ▲ Above |
| Expense Ratio | 38% | 42% | -4% | ▼ Below |
| Year Built | 2016 | 2017 | -1yr | — |

Gap column color-coded: green = favorable, red = unfavorable, grey = neutral/physical metrics.

**Bottom — Comp Cards Grid (responsive, 2–3 columns):**

Each card:
- Header: address, city/state, source badge (Rentcast / Zillow)
- Facts row: unit count, year built, sq ft
- Per-metric dot-on-line charts for all available metrics:
  - Two dots on a shared scale: Subject (blue) vs. This Comp (orange)
  - Scale = min/max across all comps for that metric
  - Value labels next to each dot

**Re-fetch Comps button** at top of tab — calls `compsService.search()`, refreshes data.

---

## Metrics Covered

| Category | Metrics |
|----------|---------|
| Pricing | cap_rate, price_per_unit, price_per_sqft |
| Income | rent_per_unit, occupancy_rate, noi |
| Expenses | expense_ratio, opex_per_unit |
| Physical | year_built, unit_count, square_feet |

---

## Key Constraints

- Domain layer: zero external dependencies
- Services depend on domain interfaces (ABCs) only
- All API calls from frontend go through service layer
- Comps stored to DB after each fetch — tab renders from cache, no re-fetch on page load
- Rentcast free tier rate limits: batch requests conservatively (single radius search per deal)
