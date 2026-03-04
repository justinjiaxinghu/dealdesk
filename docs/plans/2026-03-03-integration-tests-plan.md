# Integration Test Expansion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend `TestGoldenPipeline` with 5 new tests covering historical financials extraction, deterministic DCF, and sensitivity analysis — using both hand-checked assertions and LLM-as-judge.

**Architecture:** All tests live in `test_golden_integration.py` (same class, same fixture OM). `conftest.py` gets one new in-memory repo (`InMemoryHistoricalFinancialRepository`) and both fixtures (`repos`, `services`) are extended to wire in `HistoricalFinancialService` and `FinancialModelService`.

**Tech Stack:** pytest-asyncio, OpenAI GPT-4o (judge calls), existing pdfplumber + in-memory repos.

---

## Reference values (defined at top of test file — already present)

```python
OM_SQUARE_FEET = 23_760.0
OM_OFFERING_PRICE = 3_150_000.0
OM_GROSS_REVENUE = 284_100.0
OM_VACANCY_RATE = 0.03
OM_EXPENSES = 93_465.0
OM_RESERVES = 8_523.0
OM_PRO_FORMA_NOI = 173_589.0
OM_COMP_CAP_RATE_AVG = 0.0564
OM_IMPLIED_CAP_RATE = OM_PRO_FORMA_NOI / OM_OFFERING_PRICE  # ~0.05511

OM_EFFECTIVE_REVENUE = OM_GROSS_REVENUE * (1 - OM_VACANCY_RATE)   # 275_577
OM_OPEX_RATIO = (OM_EXPENSES + OM_RESERVES) / OM_EFFECTIVE_REVENUE  # ~0.3702
```

---

### Task 1: Extend `conftest.py` — add `InMemoryHistoricalFinancialRepository` and wire fixtures

**Files:**
- Modify: `backend/tests/conftest.py`

**Step 1: Add imports**

At the top of `conftest.py`, add after existing imports:

```python
from app.domain.entities.historical_financial import HistoricalFinancial
from app.domain.interfaces.repositories import HistoricalFinancialRepository
```

**Step 2: Add the in-memory repo class**

Add after `InMemoryExportRepository`:

```python
class InMemoryHistoricalFinancialRepository(HistoricalFinancialRepository):
    def __init__(self) -> None:
        self._store: list[HistoricalFinancial] = []

    async def bulk_upsert(self, items: list[HistoricalFinancial]) -> list[HistoricalFinancial]:
        if items:
            deal_id = items[0].deal_id
            self._store = [i for i in self._store if i.deal_id != deal_id]
        self._store.extend(items)
        return items

    async def get_by_deal_id(self, deal_id: UUID) -> list[HistoricalFinancial]:
        return [i for i in self._store if i.deal_id == deal_id]
```

**Step 3: Verify existing tests still pass**

```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate dealdesk
cd backend && python -m pytest tests/ -v --ignore=tests/test_golden_integration.py
```

Expected: 31 passed.

**Step 4: Commit**

```bash
git add backend/tests/conftest.py
git commit -m "test: add InMemoryHistoricalFinancialRepository to conftest"
```

---

### Task 2: Extend `test_golden_integration.py` imports and fixtures

**Files:**
- Modify: `backend/tests/test_golden_integration.py`

**Step 1: Add new imports**

At the top of the file, add after the existing service imports:

```python
from app.domain.entities.assumption import Assumption
from app.services.financial_model_service import FinancialModelService
from app.services.historical_financial_service import HistoricalFinancialService
```

Add to the `from tests.conftest import (...)` block:

```python
    InMemoryHistoricalFinancialRepository,
```

**Step 2: Extend the `repos` fixture**

Replace the `repos` fixture with:

```python
@pytest.fixture
def repos():
    """Create a fresh set of in-memory repositories."""
    document_repo = InMemoryDocumentRepository()
    return {
        "deal": InMemoryDealRepository(),
        "document": document_repo,
        "extracted_field": InMemoryExtractedFieldRepository(document_repo=document_repo),
        "market_table": InMemoryMarketTableRepository(),
        "assumption_set": InMemoryAssumptionSetRepository(),
        "assumption": InMemoryAssumptionRepository(),
        "export": InMemoryExportRepository(),
        "historical_financial": InMemoryHistoricalFinancialRepository(),
    }
```

**Step 3: Extend the `services` fixture**

Replace the `services` fixture with:

```python
@pytest.fixture
def services(repos, tmp_path):
    """Wire up all services with real providers and in-memory repos."""
    file_storage = LocalFileStorage(base_path=tmp_path)
    document_processor = PdfPlumberProcessor()
    llm_provider = OpenAILLMProvider()
    excel_exporter = OpenpyxlExcelExporter()

    deal_service = DealService(
        deal_repo=repos["deal"],
        assumption_set_repo=repos["assumption_set"],
    )
    document_service = DocumentService(
        document_repo=repos["document"],
        extracted_field_repo=repos["extracted_field"],
        market_table_repo=repos["market_table"],
        file_storage=file_storage,
        document_processor=document_processor,
        llm_provider=llm_provider,
    )
    benchmark_service = BenchmarkService(
        deal_repo=repos["deal"],
        assumption_set_repo=repos["assumption_set"],
        assumption_repo=repos["assumption"],
        llm_provider=llm_provider,
    )
    export_service = ExportService(
        deal_repo=repos["deal"],
        assumption_set_repo=repos["assumption_set"],
        assumption_repo=repos["assumption"],
        export_repo=repos["export"],
        file_storage=file_storage,
        excel_exporter=excel_exporter,
    )
    historical_financial_service = HistoricalFinancialService(
        deal_repo=repos["deal"],
        document_repo=repos["document"],
        hf_repo=repos["historical_financial"],
        llm_provider=llm_provider,
        document_processor=document_processor,
    )
    financial_model_service = FinancialModelService(
        assumption_repo=repos["assumption"],
    )

    return {
        "deal": deal_service,
        "document": document_service,
        "benchmark": benchmark_service,
        "export": export_service,
        "historical_financial": historical_financial_service,
        "financial_model": financial_model_service,
    }
```

**Step 4: Verify existing tests still pass**

```bash
cd backend && python -m pytest tests/test_golden_integration.py -v
```

Expected: 5 passed (all existing tests still pass with extended fixtures).

**Step 5: Commit**

```bash
git add backend/tests/test_golden_integration.py
git commit -m "test: extend golden integration fixtures for historical financial and DCF services"
```

---

### Task 3: Add `test_dcf_compute_known_values` (deterministic)

**Files:**
- Modify: `backend/tests/test_golden_integration.py`

**Step 1: Write the test**

Add inside `class TestGoldenPipeline`, after `test_full_pipeline`:

```python
async def test_dcf_compute_known_values(self, services, repos):
    """Deterministic: OM-known assumptions produce expected DCF metrics."""
    # Create deal (no LLM calls needed)
    deal = await services["deal"].create_deal(
        name="Lund Pointe Deterministic",
        address="3300 Valentine Ln SE",
        city="Port Orchard",
        state="WA",
        property_type=PropertyType.MULTIFAMILY,
        square_feet=OM_SQUARE_FEET,
    )
    assumption_sets = await repos["assumption_set"].get_by_deal_id(deal.id)
    base_set = assumption_sets[0]

    # Seed assumptions from OM-known values
    assumptions = [
        Assumption(set_id=base_set.id, key="purchase_price",       value_number=OM_OFFERING_PRICE),
        Assumption(set_id=base_set.id, key="base_gross_revenue",   value_number=OM_GROSS_REVENUE),
        Assumption(set_id=base_set.id, key="base_occupancy_rate",  value_number=1.0 - OM_VACANCY_RATE),
        Assumption(set_id=base_set.id, key="base_expense_ratio",   value_number=OM_OPEX_RATIO),
        Assumption(set_id=base_set.id, key="exit_cap_rate",        value_number=OM_COMP_CAP_RATE_AVG),
        Assumption(set_id=base_set.id, key="projection_periods",   value_number=5),
        Assumption(set_id=base_set.id, key="ltv",                  value_number=0.70),
    ]
    await repos["assumption"].bulk_upsert(assumptions)

    result = await services["financial_model"].compute(base_set.id)

    print(
        f"\n  DCF — IRR={result.irr:.3%}, EM={result.equity_multiple:.2f}x, "
        f"CoC={result.cash_on_cash_yr1:.3%}, cap_rate_on_cost={result.cap_rate_on_cost:.4%}"
    )

    # Cap rate on cost ≈ OM implied cap rate (5.51%) — tolerance ±50bps
    assert abs(result.cap_rate_on_cost - OM_IMPLIED_CAP_RATE) < 0.005, (
        f"cap_rate_on_cost={result.cap_rate_on_cost:.4f} not within 50bps of "
        f"OM implied cap rate {OM_IMPLIED_CAP_RATE:.4f}"
    )
    assert result.equity_multiple > 1.0, (
        f"equity_multiple={result.equity_multiple:.3f} — must be > 1.0x"
    )
    assert result.irr is not None, "IRR bisection should converge"
    assert result.cash_on_cash_yr1 > 0, (
        f"cash_on_cash_yr1={result.cash_on_cash_yr1:.4f} — property should cover debt service"
    )
```

**Step 2: Run the test**

```bash
cd backend && python -m pytest tests/test_golden_integration.py::TestGoldenPipeline::test_dcf_compute_known_values -v
```

Expected: PASS. If it fails on cap_rate_on_cost, print the actual value and check the opex ratio calculation — the test uses `OM_OPEX_RATIO` which is defined at module level as `(OM_EXPENSES + OM_RESERVES) / OM_EFFECTIVE_REVENUE`.

**Step 3: Commit**

```bash
git add backend/tests/test_golden_integration.py
git commit -m "test: add deterministic DCF integration test with OM-known values"
```

---

### Task 4: Add `test_dcf_quality_llm_judge` (LLM judge)

**Files:**
- Modify: `backend/tests/test_golden_integration.py`

**Step 1: Write the test**

Add inside `class TestGoldenPipeline`:

```python
async def test_dcf_quality_llm_judge(self, services, repos):
    """LLM-as-judge: verify DCF outputs are plausible for Lund Pointe."""
    _skip_without_api_key()

    deal = await services["deal"].create_deal(
        name="Lund Pointe DCF Judge",
        address="3300 Valentine Ln SE",
        city="Port Orchard",
        state="WA",
        property_type=PropertyType.MULTIFAMILY,
        square_feet=OM_SQUARE_FEET,
    )
    assumption_sets = await repos["assumption_set"].get_by_deal_id(deal.id)
    base_set = assumption_sets[0]

    assumptions = [
        Assumption(set_id=base_set.id, key="purchase_price",       value_number=OM_OFFERING_PRICE),
        Assumption(set_id=base_set.id, key="base_gross_revenue",   value_number=OM_GROSS_REVENUE),
        Assumption(set_id=base_set.id, key="base_occupancy_rate",  value_number=1.0 - OM_VACANCY_RATE),
        Assumption(set_id=base_set.id, key="base_expense_ratio",   value_number=OM_OPEX_RATIO),
        Assumption(set_id=base_set.id, key="exit_cap_rate",        value_number=OM_COMP_CAP_RATE_AVG),
        Assumption(set_id=base_set.id, key="projection_periods",   value_number=5),
        Assumption(set_id=base_set.id, key="ltv",                  value_number=0.70),
    ]
    await repos["assumption"].bulk_upsert(assumptions)

    result = await services["financial_model"].compute(base_set.id)

    dcf_summary = (
        f"- IRR: {result.irr:.3%}\n"
        f"- Equity Multiple: {result.equity_multiple:.3f}x\n"
        f"- Cash-on-Cash (Yr 1): {result.cash_on_cash_yr1:.3%}\n"
        f"- Cap Rate on Cost: {result.cap_rate_on_cost:.3%}\n"
        f"- Cash Flows (equity, yr1-yr5+exit): {[f'{cf:,.0f}' for cf in result.cash_flows]}"
    )
    print(f"\n  DCF summary:\n{dcf_summary}")

    om_context = (
        "Lund Pointe Apartments, Port Orchard WA. 25-unit multifamily, built 1995.\n"
        f"Purchase price: ${OM_OFFERING_PRICE:,.0f}. "
        f"Pro forma NOI: ${OM_PRO_FORMA_NOI:,.0f}. "
        f"Gross revenue: ${OM_GROSS_REVENUE:,.0f}. Vacancy: {OM_VACANCY_RATE:.0%}.\n"
        f"Comp cap rates: 5.10%–6.29% (avg {OM_COMP_CAP_RATE_AVG:.2%}). "
        f"Exit cap rate used: {OM_COMP_CAP_RATE_AVG:.2%}. LTV: 70%. 5-year hold."
    )

    judgment = await _llm_judge(
        context=om_context,
        data_to_evaluate=f"DCF model outputs:\n{dcf_summary}",
        criteria=(
            "Evaluate whether these DCF outputs are financially plausible for this property. Check:\n"
            "1. IRR is in the 5%–25% range for a stabilised multifamily at 70% LTV in WA\n"
            "2. Equity multiple is between 1.1x and 2.5x for a 5-year hold\n"
            "3. Cash-on-cash Yr 1 is positive (property covers debt service)\n"
            "4. Cap rate on cost is close to the property's implied cap rate (~5.5%)\n"
            "5. Cash flow signs make sense: negative initial equity outflow, positive operating years, "
            "large positive terminal year (exit proceeds)\n"
            "Be strict on sign conventions and order-of-magnitude errors. "
            "Minor rounding is fine."
        ),
    )

    print(f"\n  Judge verdict: {judgment['verdict']}")
    print(f"  Reasoning: {judgment['reasoning']}")
    if judgment.get("issues"):
        print(f"  Issues: {judgment['issues']}")

    assert judgment["verdict"] == "PASS", (
        f"LLM judge FAILED DCF quality.\n"
        f"Reasoning: {judgment['reasoning']}\n"
        f"Issues: {judgment.get('issues', [])}"
    )
```

**Step 2: Run the test**

```bash
cd backend && python -m pytest tests/test_golden_integration.py::TestGoldenPipeline::test_dcf_quality_llm_judge -v -s
```

Expected: PASS. The `-s` flag shows print statements so you can see the judge's reasoning.

**Step 3: Commit**

```bash
git add backend/tests/test_golden_integration.py
git commit -m "test: add LLM-judge integration test for DCF output quality"
```

---

### Task 5: Add `test_historical_financials_extraction` + `test_judge_rejects_bad_historical_financials`

**Files:**
- Modify: `backend/tests/test_golden_integration.py`

**Step 1: Write both tests**

Add inside `class TestGoldenPipeline`:

```python
async def test_historical_financials_extraction(self, services, repos):
    """LLM-as-judge: GPT-4o extracts plausible historical financials from the OM."""
    _skip_without_api_key()

    deal = await services["deal"].create_deal(
        name="Lund Pointe HF",
        address="3300 Valentine Ln SE",
        city="Port Orchard",
        state="WA",
        property_type=PropertyType.MULTIFAMILY,
        square_feet=OM_SQUARE_FEET,
    )

    pdf_bytes = SAMPLE_OM_PATH.read_bytes()
    doc = await services["document"].upload_document(
        deal_id=deal.id,
        file_data=pdf_bytes,
        filename="lund_pointe_om.pdf",
    )
    await services["document"].process_document(doc.id)

    results = await services["historical_financial"].extract(deal.id, doc.id)
    assert len(results) > 0, "No historical financials extracted"

    rows_summary = "\n".join(
        f"- period={r.period_label}, metric={r.metric_key}, value={r.value}, unit={r.unit}"
        for r in results
    )
    print(f"\n  Extracted {len(results)} historical financial rows:\n{rows_summary}")

    om_context = (
        "Lund Pointe Apartments, Port Orchard WA. 25-unit multifamily.\n"
        f"Pro forma gross revenue: ${OM_GROSS_REVENUE:,.0f}/yr. "
        f"Pro forma NOI: ${OM_PRO_FORMA_NOI:,.0f}/yr. "
        f"Vacancy: {OM_VACANCY_RATE:.0%}. Expenses: ${OM_EXPENSES:,.0f}. "
        f"Reserves: ${OM_RESERVES:,.0f}."
    )

    judgment = await _llm_judge(
        context=om_context,
        data_to_evaluate=f"Extracted historical financial rows:\n{rows_summary}",
        criteria=(
            "Evaluate whether these historical financial rows are plausible for this property. Check:\n"
            "1. At least one revenue metric and one NOI or expense metric is present\n"
            "2. Revenue values are in the plausible range for a 25-unit WA multifamily "
            "(not orders of magnitude off from ~$284K/yr gross)\n"
            "3. Period labels are recognisable financial period names (T12, Prior Year, "
            "Trailing 12, 2023, 2024, etc.)\n"
            "4. Metric keys are standard CRE financial line items (gross_revenue, noi, "
            "vacancy_loss, operating_expenses, etc.)\n"
            "5. No hallucinated metrics with nonsensical values\n"
            "Minor omissions are acceptable. Incorrect values or fabricated metrics are not."
        ),
    )

    print(f"\n  Judge verdict: {judgment['verdict']}")
    print(f"  Reasoning: {judgment['reasoning']}")
    if judgment.get("issues"):
        print(f"  Issues: {judgment['issues']}")

    assert judgment["verdict"] == "PASS", (
        f"LLM judge FAILED historical financials quality.\n"
        f"Reasoning: {judgment['reasoning']}\n"
        f"Issues: {judgment.get('issues', [])}"
    )


async def test_judge_rejects_bad_historical_financials(self, services, repos):
    """Verify the LLM judge correctly FAILs fabricated historical financials."""
    _skip_without_api_key()

    bad_rows = (
        "Extracted historical financial rows:\n"
        "- period=T12, metric=gross_revenue, value=50000000.0, unit=$/yr\n"   # 50M for 25-unit — absurd
        "- period=T12, metric=noi, value=-2000000.0, unit=$/yr\n"             # Deeply negative
        "- period=T12, metric=vacancy_rate, value=0.95, unit=ratio\n"         # 95% vacancy
        "- period=T12, metric=cap_rate, value=0.001, unit=ratio\n"            # 0.1% cap rate
    )

    om_context = (
        "Lund Pointe Apartments, Port Orchard WA. 25-unit multifamily.\n"
        f"Pro forma gross revenue: ${OM_GROSS_REVENUE:,.0f}/yr. "
        f"Pro forma NOI: ${OM_PRO_FORMA_NOI:,.0f}/yr."
    )

    judgment = await _llm_judge(
        context=om_context,
        data_to_evaluate=bad_rows,
        criteria=(
            "Evaluate whether these historical financial rows are plausible for this property. Check:\n"
            "1. At least one revenue metric and one NOI or expense metric is present\n"
            "2. Revenue values are in the plausible range for a 25-unit WA multifamily "
            "(not orders of magnitude off from ~$284K/yr gross)\n"
            "3. Period labels are recognisable financial period names\n"
            "4. Metric keys are standard CRE financial line items\n"
            "5. No hallucinated metrics with nonsensical values\n"
            "Minor omissions are acceptable. Incorrect values or fabricated metrics are not."
        ),
    )

    print(f"\n  Judge verdict (should be FAIL): {judgment['verdict']}")
    print(f"  Reasoning: {judgment['reasoning']}")

    assert judgment["verdict"] == "FAIL", (
        "LLM judge should have FAILED fabricated historical financials, "
        f"but returned: {judgment['verdict']}\n"
        f"Reasoning: {judgment['reasoning']}"
    )
    assert len(judgment.get("issues", [])) > 0, (
        "Judge should have listed specific issues"
    )
```

**Step 2: Run both tests**

```bash
cd backend && python -m pytest \
  tests/test_golden_integration.py::TestGoldenPipeline::test_historical_financials_extraction \
  tests/test_golden_integration.py::TestGoldenPipeline::test_judge_rejects_bad_historical_financials \
  -v -s
```

Expected: both PASS.

**Step 3: Commit**

```bash
git add backend/tests/test_golden_integration.py
git commit -m "test: add LLM-judge integration tests for historical financials extraction"
```

---

### Task 6: Add `test_sensitivity_grid` (deterministic + LLM judge)

**Files:**
- Modify: `backend/tests/test_golden_integration.py`

**Step 1: Write the test**

Add inside `class TestGoldenPipeline`:

```python
async def test_sensitivity_grid(self, services, repos):
    """Sensitivity: correct grid shape, economic monotonicity, and LLM judge confirmation."""
    _skip_without_api_key()

    deal = await services["deal"].create_deal(
        name="Lund Pointe Sensitivity",
        address="3300 Valentine Ln SE",
        city="Port Orchard",
        state="WA",
        property_type=PropertyType.MULTIFAMILY,
        square_feet=OM_SQUARE_FEET,
    )
    assumption_sets = await repos["assumption_set"].get_by_deal_id(deal.id)
    base_set = assumption_sets[0]

    assumptions = [
        Assumption(set_id=base_set.id, key="purchase_price",       value_number=OM_OFFERING_PRICE),
        Assumption(set_id=base_set.id, key="base_gross_revenue",   value_number=OM_GROSS_REVENUE),
        Assumption(set_id=base_set.id, key="base_occupancy_rate",  value_number=1.0 - OM_VACANCY_RATE),
        Assumption(set_id=base_set.id, key="base_expense_ratio",   value_number=OM_OPEX_RATIO),
        Assumption(set_id=base_set.id, key="exit_cap_rate",        value_number=OM_COMP_CAP_RATE_AVG),
        Assumption(set_id=base_set.id, key="projection_periods",   value_number=5),
        Assumption(set_id=base_set.id, key="ltv",                  value_number=0.70),
    ]
    await repos["assumption"].bulk_upsert(assumptions)

    x_prices = [2_800_000, 3_000_000, 3_150_000, 3_300_000, 3_500_000]
    y_cap_rates = [0.045, 0.050, 0.055, 0.060, 0.065]

    grids = await services["financial_model"].compute_sensitivity(
        set_id=base_set.id,
        x_axis={"key": "purchase_price", "values": x_prices},
        y_axis={"key": "exit_cap_rate", "values": y_cap_rates},
        metrics=["irr", "equity_multiple"],
    )

    irr_grid = grids["irr"]
    em_grid = grids["equity_multiple"]

    # --- Shape ---
    assert len(irr_grid) == len(y_cap_rates), f"Expected {len(y_cap_rates)} rows, got {len(irr_grid)}"
    assert all(len(row) == len(x_prices) for row in irr_grid), "IRR grid row length mismatch"
    assert len(em_grid) == len(y_cap_rates), f"Expected {len(y_cap_rates)} EM rows"

    # --- Monotonicity: higher purchase_price → lower IRR (each row) ---
    for i, row in enumerate(irr_grid):
        non_none = [v for v in row if v is not None]
        assert non_none == sorted(non_none, reverse=True), (
            f"Row {i} (exit_cap_rate={y_cap_rates[i]:.3f}): IRR should decrease as "
            f"purchase_price increases, got {[f'{v:.3%}' if v else 'None' for v in row]}"
        )

    # --- Monotonicity: higher exit_cap_rate → lower exit value → lower IRR (each column) ---
    for j, price in enumerate(x_prices):
        col = [irr_grid[i][j] for i in range(len(y_cap_rates))]
        non_none = [v for v in col if v is not None]
        assert non_none == sorted(non_none, reverse=True), (
            f"Col {j} (purchase_price={price:,.0f}): IRR should decrease as "
            f"exit_cap_rate increases (higher cap rate = lower exit value), "
            f"got {[f'{v:.3%}' if v else 'None' for v in col]}"
        )

    # Format grid for display and judge
    header = "purchase_price →\n" + " " * 12 + "  ".join(f"{p/1e6:.2f}M" for p in x_prices)
    rows_str = []
    for i, cap_rate in enumerate(y_cap_rates):
        row_str = f"exit_cap={cap_rate:.3f}: " + "  ".join(
            f"{v:.2%}" if v is not None else "N/A" for v in irr_grid[i]
        )
        rows_str.append(row_str)
    irr_table = header + "\n" + "\n".join(rows_str)
    print(f"\n  IRR sensitivity grid:\n{irr_table}")

    judgment = await _llm_judge(
        context=(
            f"Lund Pointe Apartments, Port Orchard WA. 25-unit multifamily. "
            f"Base purchase price: ${OM_OFFERING_PRICE:,.0f}. "
            f"Base exit cap rate: {OM_COMP_CAP_RATE_AVG:.2%}. 5-year hold, 70% LTV."
        ),
        data_to_evaluate=(
            f"IRR sensitivity grid (purchase price on x-axis, exit cap rate on y-axis):\n{irr_table}"
        ),
        criteria=(
            "Evaluate whether the directional relationships in this IRR sensitivity grid make economic sense:\n"
            "1. As purchase price increases (left to right), IRR should decrease — "
            "paying more for the same income stream lowers returns\n"
            "2. As exit cap rate increases (top to bottom), IRR should decrease — "
            "a higher exit cap rate compresses the exit value (exit_value = NOI / cap_rate), "
            "reducing proceeds and therefore returns\n"
            "3. Center cell (base case) IRR should be plausible for this asset "
            "(roughly 8%–18% for a stabilised WA multifamily at 70% LTV)\n"
            "4. The range of IRR values across the grid should be economically reasonable "
            "(roughly 5%–25% spread, not 0.001% to 500%)\n"
            "If directions are wrong or values are nonsensical, verdict must be FAIL."
        ),
    )

    print(f"\n  Judge verdict: {judgment['verdict']}")
    print(f"  Reasoning: {judgment['reasoning']}")
    if judgment.get("issues"):
        print(f"  Issues: {judgment['issues']}")

    assert judgment["verdict"] == "PASS", (
        f"LLM judge FAILED sensitivity grid quality.\n"
        f"Reasoning: {judgment['reasoning']}\n"
        f"Issues: {judgment.get('issues', [])}"
    )
```

**Step 2: Run the test**

```bash
cd backend && python -m pytest tests/test_golden_integration.py::TestGoldenPipeline::test_sensitivity_grid -v -s
```

Expected: PASS — grid is 5×5, IRR decreases left-to-right and top-to-bottom, judge confirms.

If the monotonicity assertion fails on the column direction, double-check the DCF engine: exit_value = forward_noi / exit_cap_rate, so higher cap_rate → smaller denominator in IRR calculation... wait, larger denominator = smaller exit value. Re-read `dcf.py` line 159:
```python
exit_value = forward_noi / params.exit_cap_rate if params.exit_cap_rate > 0 else 0.0
```
Confirmed: higher exit_cap_rate → lower exit_value → lower IRR. If the grid goes the other way, there is a bug in the DCF engine.

**Step 3: Run full integration suite**

```bash
cd backend && python -m pytest tests/test_golden_integration.py -v -s
```

Expected: 10 passed (5 original + 5 new).

**Step 4: Run full suite including unit tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: 41 passed.

**Step 5: Commit**

```bash
git add backend/tests/test_golden_integration.py
git commit -m "test: add sensitivity grid integration test (deterministic + LLM judge)"
```

---

## Summary

| Task | File | Tests added |
|------|------|-------------|
| 1 | conftest.py | InMemoryHistoricalFinancialRepository |
| 2 | test_golden_integration.py | fixture extensions only |
| 3 | test_golden_integration.py | test_dcf_compute_known_values |
| 4 | test_golden_integration.py | test_dcf_quality_llm_judge |
| 5 | test_golden_integration.py | test_historical_financials_extraction + test_judge_rejects_bad_historical_financials |
| 6 | test_golden_integration.py | test_sensitivity_grid |

**Total: 36 → 41 tests (+5 new integration tests)**
