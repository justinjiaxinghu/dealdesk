# Integration Test Expansion Design
**Date:** 2026-03-03

## Goal

Expand `test_golden_integration.py` to cover the three new features added in `pedro/expand_mvp`:
- Historical financials extraction (GPT-4o)
- DCF computation (`FinancialModelService.compute`)
- Sensitivity analysis (`FinancialModelService.compute_sensitivity`)

## Approach

Extend `TestGoldenPipeline` in `test_golden_integration.py`. All new tests use the same Lund Pointe Apartments fixture OM and the same `repos`/`services` fixture pattern. Two new in-memory repositories are added to `conftest.py`.

## `conftest.py` Changes

### New in-memory repos

```python
class InMemoryHistoricalFinancialRepository(HistoricalFinancialRepository):
    # bulk_upsert by (deal_id, period_label, metric_key) — delete-then-insert per deal
    # get_by_deal_id

class InMemoryValidationRepository(FieldValidationRepository):
    # bulk_upsert by (deal_id, field_key)
    # get_by_deal_id
```

### Extended fixtures

`repos` dict gains `"historical_financial"` key.
`services` dict gains `"historical_financial"` (`HistoricalFinancialService`) and `"financial_model"` (`FinancialModelService`) keys.

## New Test Methods

### 1. `test_historical_financials_extraction` (LLM judge)

**What it does:**
1. Create deal, upload + process OM
2. Call `HistoricalFinancialService.extract(deal_id, doc_id)`
3. Assert `len(results) > 0`
4. Feed results to `_llm_judge` — judge checks that extracted rows are plausible for Lund Pointe (gross revenue near $284K, NOI near $173K, vacancy ~3%, periods like "T12" or "Prior Year")

**Judge criteria:**
- At least one revenue and one NOI row present
- Numeric values plausible for a 25-unit WA multifamily (not orders of magnitude off)
- Period labels are recognisable financial period names
- No hallucinated metrics

### 2. `test_judge_rejects_bad_historical_financials` (inverse LLM judge)

**What it does:**
- Feed fabricated historicals with absurd values (gross revenue $50M, NOI -$2M) to the judge
- Assert verdict == "FAIL"
- Calibrates judge strictness (mirrors existing `test_judge_rejects_bad_extraction`)

### 3. `test_dcf_compute_known_values` (deterministic)

**What it does:**
1. Create deal + assumption set
2. Bulk-upsert assumptions matching OM known values:
   - `purchase_price = 3_150_000`
   - `base_gross_revenue = 284_100`
   - `base_occupancy_rate = 0.97` (3% vacancy)
   - `base_expense_ratio = (93_465 + 8_523) / (284_100 * 0.97)` ≈ 0.369
   - `exit_cap_rate = 0.0564` (avg comp cap rate)
   - `projection_periods = 5`
3. Call `FinancialModelService.compute(set_id)`
4. Assert:
   - `cap_rate_on_cost` ≈ 5.51% (±50bps) — matches OM implied cap rate
   - `equity_multiple > 1.0` — money-on-money positive
   - `irr is not None`
   - `cash_on_cash_yr1 > 0`

### 4. `test_dcf_quality_llm_judge` (LLM judge)

**What it does:**
1. Create deal + assumption set with OM-known values (same as above)
2. Compute projection
3. Feed `ProjectionResult` fields to `_llm_judge`
4. Judge assesses whether IRR/EM/CoC/cap_rate_on_cost are plausible for a $3.15M 25-unit multifamily in Port Orchard, WA

**Judge criteria:**
- IRR in 5–25% range for a stabilised MF at market assumptions
- Equity multiple 1.2x–3.0x for a 5-year hold
- Cash-on-cash Yr 1 > 0 (property covers debt service at 70% LTV)
- Cap rate on cost close to OM's implied cap rate (~5.5%)

### 5. `test_sensitivity_grid` (deterministic + LLM judge)

**What it does:**
1. Create deal + assumption set with OM-known values
2. Call `FinancialModelService.compute_sensitivity` with:
   - x-axis: `purchase_price` = [2_800_000, 3_000_000, 3_150_000, 3_300_000, 3_500_000]
   - y-axis: `exit_cap_rate` = [0.045, 0.050, 0.055, 0.060, 0.065]
   - metrics: `["irr", "equity_multiple"]`
3. **Deterministic assertions:**
   - Grid shape: 5 rows × 5 cols for each metric
   - IRR strictly decreasing across each row as purchase_price increases (higher price → lower return)
   - IRR strictly increasing down each column as exit_cap_rate increases (higher exit proceeds at same price → higher return)
4. **LLM judge:** Feed the IRR grid to the judge and ask if the directional relationships make economic sense

## File Changes Summary

| File | Change |
|------|--------|
| `backend/tests/conftest.py` | Add `InMemoryHistoricalFinancialRepository`, extend `repos`/`services` fixtures |
| `backend/tests/test_golden_integration.py` | Add 5 new test methods to `TestGoldenPipeline` |

## Acceptance Criteria

- All 5 new tests pass with a valid `DEALDESK_OPENAI_API_KEY`
- Deterministic assertions (cap rate, grid shape, monotonicity) pass without any LLM call
- LLM judge tests are marked `@pytest.mark.integration` (already the class-level marker)
- Total test count goes from 36 to 41
