# Financial Model, Sensitivity Analysis & Historical Financials — Design

**Date:** 2026-03-03
**Status:** Approved

## Overview

Extend DealDesk with a full financial model layer: structured editable assumptions (grouped by category), historical financials extracted from OMs, a Python DCF engine, and a sensitivity analysis tab. Stays within the existing layered architecture (Option A — assumption groups + new FinancialModelService).

---

## Tab Order

```
Extraction → Historical Financials → Assumptions → Validation → Comps → Sensitivity
```

---

## Data Model

### Assumption entity — 3 new fields

```python
group: AssumptionGroup | None
# model_structure | transaction | operating | financing | return_targets

forecast_method: str | None
# "historical" | "step_change" | "gradual_ramp" — operating group only

forecast_params: dict | None
# JSON: {"step_value": 0.02} or {"target_value": 0.95}
```

Backward-compatible migration: all nullable, existing rows get `group=None`.

### New AssumptionGroup enum

```python
class AssumptionGroup(str, Enum):
    MODEL_STRUCTURE = "model_structure"
    TRANSACTION = "transaction"
    OPERATING = "operating"
    FINANCING = "financing"
    RETURN_TARGETS = "return_targets"
```

### New HistoricalFinancial entity + table

```python
@dataclass
class HistoricalFinancial:
    deal_id: UUID
    period_label: str       # "T12", "2024", "2023", etc.
    metric_key: str         # "gross_revenue", "noi", "expense_ratio", "occupancy_rate", etc.
    value: float
    unit: str | None
    source: str             # "extracted" | "manual"
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
```

DB upsert key: `(deal_id, period_label, metric_key)`.

---

## Backend Architecture

### DCF Engine

New file: `domain/services/dcf.py` — pure functions, zero external deps.

```python
@dataclass(frozen=True)
class ProjectionParams:
    # Model
    start_date: date
    periods: int
    cadence: str             # "annual" | "quarterly"
    # Transaction
    purchase_price: float
    ltv: float
    closing_costs: float
    acquisition_fee: float
    # Operating (base values + per-line forecast method)
    base_gross_revenue: float
    base_expense_ratio: float
    base_occupancy_rate: float
    base_capex_per_unit: float
    revenue_forecast_method: str
    revenue_forecast_params: dict
    expense_forecast_method: str
    expense_forecast_params: dict
    # Financing
    sofr_rate: float
    spread: float
    loan_term: int
    interest_only_years: int
    # Returns
    exit_cap_rate: float

@dataclass(frozen=True)
class ProjectionResult:
    irr: float | None
    equity_multiple: float
    cash_on_cash_yr1: float
    cap_rate_on_cost: float
    cash_flows: list[float]
```

IRR solved via bisection (~20 lines, no numpy needed).

**Forecast methods:**
- `historical`: Use base value as-is, flat over projection period
- `step_change`: Apply `forecast_params["step_value"]` each period
- `gradual_ramp`: Linearly interpolate from base to `forecast_params["target_value"]`

### FinancialModelService

New file: `services/financial_model_service.py`

- `compute(set_id: UUID) -> ProjectionResult` — loads assumptions, assembles `ProjectionParams`, calls `dcf.compute_projection()`
- `compute_sensitivity(set_id, x_axis, y_axis) -> list[SensitivityGrid]` — nested loop over two axes, calls `compute_projection()` for each cell, returns one grid per metric

### Historical Financials extraction

- New method on `LLMProvider` ABC: `extract_historical_financials(pages, deal) -> list[HistoricalFinancialResult]`
- GPT-4o scans OM pages for T12 / prior-year P&L, maps to canonical metric keys
- New `HistoricalFinancialService` with `extract(deal_id, doc_id)` and `list(deal_id)`
- Triggered as a new step in the document processing pipeline (after field extraction)

### New domain interfaces

- `HistoricalFinancialRepository` ABC: `bulk_upsert(items)`, `list_by_deal_id(deal_id)`

### New API routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/v1/deals/{id}/historical-financials` | GET | Return extracted historicals |
| `/v1/deals/{id}/financial-model:compute` | POST | Run DCF, return `ProjectionResult` |
| `/v1/deals/{id}/sensitivity` | POST | Body: `{x_axis, y_axis, metrics}`, returns grids |

**Sensitivity request body:**
```json
{
  "x_axis": {"key": "purchase_price", "values": [18000000, 19000000, 20000000]},
  "y_axis": {"key": "exit_cap_rate", "values": [0.05, 0.055, 0.06, 0.065]},
  "metrics": ["irr", "equity_multiple", "cash_on_cash_yr1", "cap_rate_on_cost"]
}
```

### New Alembic migrations

1. `alter_assumptions_add_group_forecast` — adds `group`, `forecast_method`, `forecast_params` columns
2. `create_historical_financials` — new `historical_financials` table

---

## Frontend Architecture

### Assumption groups — fields per section

| Section | Fields |
|---------|--------|
| Model Structure | start_date, projection_periods, cadence (annual/quarterly) |
| Transaction | purchase_price, ltv, closing_costs, acquisition_fee |
| Operating | occupancy_rate, rent_per_unit, revenue_growth, expense_ratio, capex_per_unit — each with forecast method dropdown |
| Financing | sofr_term (3mo/6mo), sofr_rate (fetched/editable), spread, loan_term, interest_only_years |
| Return Targets | target_irr, target_equity_multiple, exit_cap_rate |

**Forecast method dropdown** (operating fields only):
- `In-line with historicals` — no extra input
- `Step change` — shows "Change per period" input
- `Gradual ramp to target` — shows "Target value" input

### New / changed components

| File | Change |
|------|--------|
| `components/assumptions/assumption-panel.tsx` | Replaces `AssumptionEditor`. Five collapsible sections, all fields editable inline |
| `components/historical/historical-financials-tab.tsx` | Periods as columns, metrics as rows. Sparkline trend arrow per row |
| `components/sensitivity/sensitivity-tab.tsx` | Four stacked two-way tables, one per return metric |
| `components/sensitivity/sensitivity-table.tsx` | Axis dropdowns, color-coded cells vs. investor targets, "Recalculate" button |

### Historical Financials tab

Periods displayed as columns, metrics as rows:

| Metric | T-2 | T-1 | T12 |
|--------|-----|-----|-----|
| Gross Revenue | $2.1M | $2.3M | $2.4M |
| NOI | $1.2M | $1.35M | $1.4M |
| Expense Ratio | 43% | 41% | 40% |
| Occupancy | 91% | 93% | 94% |

Small trend arrows per row (up/down/flat). Historical values feed into operating assumptions as the `historical` baseline.

### Sensitivity tab

Four stacked two-way tables (IRR, equity multiple, cash-on-cash, cap rate on cost). Each table:
- Row and column axis labels with dropdowns to swap variables
- Cells color-coded against investor target (green = meets target, red = misses)
- "Recalculate" button triggers `POST /sensitivity`

**Pre-configured default axes:**
- IRR + equity multiple: `purchase_price` × `exit_cap_rate`
- Cash-on-cash + cap rate on cost: `occupancy_rate` × `revenue_growth`

### Export gating

Export button disabled until all five assumption groups have at least one value. Tooltip checklist shows which groups are still incomplete.

### New services / hooks

- `services/historical-financial.service.ts` — `list(dealId)`
- `services/financial-model.service.ts` — `compute(dealId)`, `sensitivity(dealId, body)`
- `useDeal` hook extended to fetch historical financials in parallel

---

## Return Metrics

| Metric | Computation |
|--------|------------|
| IRR | Bisection on NPV=0 across all cash flows including terminal |
| Equity Multiple | Total distributions / equity invested |
| Cash-on-Cash (Yr 1) | Year 1 net cash flow / equity invested |
| Cap Rate on Cost | Year 1 NOI / (purchase price + closing costs) |

---

## Key Constraints

- `domain/services/dcf.py` has zero external dependencies — pure Python math
- `FinancialModelService` depends only on domain interfaces (ABCs)
- All API calls from frontend go through service layer
- Sensitivity computed server-side — no per-cell frontend computation
- `HistoricalFinancial` extraction runs as a new pipeline step, progress tracked in `processing_steps`
