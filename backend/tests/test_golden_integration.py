# backend/tests/test_golden_integration.py
"""
Golden integration test using the Lund Pointe Apartments Offering Memorandum.

Source: https://www.neilwalter.com/wp-content/uploads/2016/02/Lund-PointeApts_OfferingMemorandum.pdf

Known values from the OM (Pro Forma):
    Property:         Lund Pointe Apartments
    Address:          3300 Valentine Ln SE, Port Orchard, WA 98366
    Units:            25
    Square Feet:      23,760
    Offering Price:   $3,150,000
    Gross Revenue:    $284,100
    Vacancy:          3%
    Expenses:         $93,465
    Reserves:         $8,523
    Pro Forma NOI:    $173,589
    Comp Cap Rates:   5.10% - 6.29% (avg 5.64%)
    Implied Cap Rate: 5.51% ($173,589 / $3,150,000)

Requires: DEALDESK_OPENAI_API_KEY environment variable.
Run with: cd backend && python -m pytest tests/test_golden_integration.py -v -m integration
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest
from openai import AsyncOpenAI

from app.domain.entities.assumption import Assumption
from app.domain.value_objects.enums import ProcessingStatus, PropertyType, SourceType
from app.infrastructure.document_processing.pdfplumber_processor import (
    PdfPlumberProcessor,
)
from app.infrastructure.export.excel_exporter import OpenpyxlExcelExporter
from app.infrastructure.file_storage.local import LocalFileStorage
from app.infrastructure.llm.openai_provider import OpenAILLMProvider
from app.services.benchmark_service import BenchmarkService
from app.services.deal_service import DealService
from app.services.document_service import DocumentService
from app.services.export_service import ExportService
from app.services.model_service import ModelService
from tests.conftest import (
    InMemoryAssumptionRepository,
    InMemoryAssumptionSetRepository,
    InMemoryDealRepository,
    InMemoryDocumentRepository,
    InMemoryExportRepository,
    InMemoryExtractedFieldRepository,
    InMemoryMarketTableRepository,
    InMemoryModelResultRepository,
)

# Path to the fixture OM PDF
FIXTURE_DIR = Path(__file__).parent / "fixtures"
SAMPLE_OM_PATH = FIXTURE_DIR / "sample_om.pdf"

# OM reference values (from the Pro Forma on page 10)
OM_SQUARE_FEET = 23_760.0
OM_OFFERING_PRICE = 3_150_000.0
OM_GROSS_REVENUE = 284_100.0
OM_VACANCY_RATE = 0.03
OM_EXPENSES = 93_465.0
OM_RESERVES = 8_523.0
OM_PRO_FORMA_NOI = 173_589.0
OM_COMP_CAP_RATE_AVG = 0.0564
OM_IMPLIED_CAP_RATE = OM_PRO_FORMA_NOI / OM_OFFERING_PRICE  # ~0.0551

# Derived values for our model
# opex_ratio = (expenses + reserves) / effective_revenue
OM_EFFECTIVE_REVENUE = OM_GROSS_REVENUE * (1 - OM_VACANCY_RATE)
OM_OPEX_RATIO = (OM_EXPENSES + OM_RESERVES) / OM_EFFECTIVE_REVENUE
OM_RENT_PSF_YR = OM_GROSS_REVENUE / OM_SQUARE_FEET


pytestmark = pytest.mark.integration


def _skip_without_api_key():
    from app.config import settings

    if not settings.openai_api_key:
        pytest.skip("DEALDESK_OPENAI_API_KEY not set — skipping integration test")


async def _llm_judge(context: str, data_to_evaluate: str, criteria: str) -> dict:
    """
    Use an LLM as a strict financial advisor to evaluate data quality.

    Returns {"verdict": "PASS" | "FAIL", "reasoning": str, "issues": list[str]}
    """
    from app.config import settings

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = (
        f"You are a strict senior financial advisor evaluating data quality for "
        f"a commercial real estate underwriting platform.\n\n"
        f"## Property Context\n{context}\n\n"
        f"## Data to Evaluate\n{data_to_evaluate}\n\n"
        f"## Evaluation Criteria\n{criteria}\n\n"
        f"Respond with a JSON object containing:\n"
        f'- "verdict": "PASS" or "FAIL"\n'
        f'- "reasoning": A 2-3 sentence explanation of your evaluation\n'
        f'- "issues": An array of specific issues found (empty array if PASS)\n\n'
        f"Be strict. If any critical financial data is wrong, missing, or "
        f"nonsensical, verdict must be FAIL."
    )

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.0,
    )

    content = response.choices[0].message.content or "{}"
    return json.loads(content)


@pytest.fixture
def repos():
    """Create a fresh set of in-memory repositories."""
    return {
        "deal": InMemoryDealRepository(),
        "document": InMemoryDocumentRepository(),
        "extracted_field": InMemoryExtractedFieldRepository(),
        "market_table": InMemoryMarketTableRepository(),
        "assumption_set": InMemoryAssumptionSetRepository(),
        "assumption": InMemoryAssumptionRepository(),
        "model_result": InMemoryModelResultRepository(),
        "export": InMemoryExportRepository(),
    }


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
    model_service = ModelService(
        deal_repo=repos["deal"],
        assumption_set_repo=repos["assumption_set"],
        assumption_repo=repos["assumption"],
        model_result_repo=repos["model_result"],
    )
    export_service = ExportService(
        deal_repo=repos["deal"],
        assumption_set_repo=repos["assumption_set"],
        assumption_repo=repos["assumption"],
        model_result_repo=repos["model_result"],
        export_repo=repos["export"],
        file_storage=file_storage,
        excel_exporter=excel_exporter,
    )

    return {
        "deal": deal_service,
        "document": document_service,
        "benchmark": benchmark_service,
        "model": model_service,
        "export": export_service,
    }


class TestGoldenPipeline:
    """
    End-to-end golden integration test using the Lund Pointe Apartments OM.

    Exercises the full pipeline:
      1. Create deal
      2. Upload + process PDF (real pdfplumber + real OpenAI)
      3. Generate AI benchmarks (real OpenAI)
      4. Set assumptions to OM-known values
      5. Compute financial model
      6. Verify outputs against hand-calculated expected values
      7. Export to Excel
    """

    async def test_full_pipeline(self, services, repos):
        """Full pipeline: upload OM -> extract -> benchmark -> compute -> export."""
        _skip_without_api_key()

        # -- 1. Create deal --------------------------------------------------
        deal = await services["deal"].create_deal(
            name="Lund Pointe Apartments",
            address="3300 Valentine Ln SE",
            city="Port Orchard",
            state="WA",
            property_type=PropertyType.MULTIFAMILY,
            square_feet=OM_SQUARE_FEET,
        )
        assert deal.id is not None
        assert deal.name == "Lund Pointe Apartments"

        # Verify Base Case assumption set was created
        assumption_sets = await repos["assumption_set"].get_by_deal_id(deal.id)
        assert len(assumption_sets) == 1
        base_set = assumption_sets[0]
        assert base_set.name == "Base Case"

        # -- 2. Upload and process PDF ----------------------------------------
        assert SAMPLE_OM_PATH.exists(), f"Fixture not found: {SAMPLE_OM_PATH}"
        pdf_bytes = SAMPLE_OM_PATH.read_bytes()

        doc = await services["document"].upload_document(
            deal_id=deal.id,
            file_data=pdf_bytes,
            filename="lund_pointe_om.pdf",
        )
        assert doc.id is not None
        assert doc.processing_status == ProcessingStatus.PENDING

        # Process document (real pdfplumber + real OpenAI LLM)
        await services["document"].process_document(doc.id)

        # Verify processing completed
        processed_doc = await services["document"].get_document(doc.id)
        assert processed_doc is not None
        assert processed_doc.processing_status == ProcessingStatus.COMPLETE, (
            f"Processing failed: {processed_doc.error_message}"
        )
        assert processed_doc.page_count == 17  # Known page count

        # Verify fields were extracted
        fields = await services["document"].get_extracted_fields(doc.id)
        assert len(fields) > 0, "No fields extracted from OM"
        field_keys = {f.field_key for f in fields}
        print(f"\n  Extracted {len(fields)} fields: {sorted(field_keys)}")

        # Verify tables were extracted
        tables = await services["document"].get_market_tables(doc.id)
        assert len(tables) > 0, "No tables extracted from OM"
        print(f"  Extracted {len(tables)} tables")

        # -- 3. Generate AI benchmarks ----------------------------------------
        suggestions = await services["benchmark"].generate_benchmarks(deal.id)
        assert len(suggestions) > 0, "No benchmarks generated"
        suggestion_keys = {s.key for s in suggestions}
        print(f"  Generated {len(suggestions)} benchmarks: {sorted(suggestion_keys)}")

        # Verify benchmark assumptions were persisted
        assumptions = await repos["assumption"].get_by_set_id(base_set.id)
        assert len(assumptions) > 0, "No assumptions created from benchmarks"

        # -- 4. Set assumptions to OM-known values ----------------------------
        # Override with exact OM values so we can verify deterministic output
        om_assumptions = [
            Assumption(
                set_id=base_set.id,
                key="rent_psf_yr",
                value_number=OM_RENT_PSF_YR,
                unit="$/sf/yr",
                source_type=SourceType.OM,
                source_ref="Pro Forma Income Statement, Page 10",
            ),
            Assumption(
                set_id=base_set.id,
                key="vacancy_rate",
                value_number=OM_VACANCY_RATE,
                unit="%",
                source_type=SourceType.OM,
                source_ref="Pro Forma Income Statement, Page 10",
            ),
            Assumption(
                set_id=base_set.id,
                key="opex_ratio",
                value_number=OM_OPEX_RATIO,
                unit="ratio",
                source_type=SourceType.OM,
                source_ref="Pro Forma Income Statement, Page 10",
            ),
            Assumption(
                set_id=base_set.id,
                key="cap_rate",
                value_number=OM_IMPLIED_CAP_RATE,
                unit="%",
                source_type=SourceType.OM,
                source_ref="Implied from Offering Price / Pro Forma NOI",
            ),
            Assumption(
                set_id=base_set.id,
                key="purchase_price",
                value_number=OM_OFFERING_PRICE,
                unit="$",
                source_type=SourceType.OM,
                source_ref="Property Summary, Page 4",
            ),
        ]
        await repos["assumption"].bulk_upsert(om_assumptions)

        # -- 5. Compute financial model ----------------------------------------
        result = await services["model"].compute(base_set.id)
        assert result is not None

        print(f"\n  Model Output:")
        print(f"    NOI (stabilized):  ${result.noi_stabilized:,.2f}")
        print(f"    Exit value:        ${result.exit_value:,.2f}")
        print(f"    Total cost:        ${result.total_cost:,.2f}")
        print(f"    Profit:            ${result.profit:,.2f}")
        print(f"    Profit margin:     {result.profit_margin_pct:.2f}%")

        # -- 6. Assert outputs match OM Pro Forma (tight tolerance) -----------
        # Since we set exact OM values as assumptions, the model output
        # should closely match the OM's stated NOI.
        assert result.noi_stabilized == pytest.approx(OM_PRO_FORMA_NOI, rel=0.01), (
            f"NOI {result.noi_stabilized:,.2f} not within 1% of "
            f"OM Pro Forma NOI {OM_PRO_FORMA_NOI:,.2f}"
        )

        # Exit value = NOI / cap_rate ≈ offering price
        assert result.exit_value == pytest.approx(OM_OFFERING_PRICE, rel=0.01), (
            f"Exit value {result.exit_value:,.2f} not within 1% of "
            f"Offering Price {OM_OFFERING_PRICE:,.2f}"
        )

        # Total cost = purchase_price (no closing costs or capex in this OM)
        assert result.total_cost == pytest.approx(OM_OFFERING_PRICE, abs=1.0)

        # Profit should be near zero (exit value ≈ purchase price at implied cap rate)
        assert abs(result.profit) < 50_000, (
            f"Profit {result.profit:,.2f} unexpectedly large"
        )

        # -- 7. Export to Excel -----------------------------------------------
        export = await services["export"].export_xlsx(base_set.id)
        assert export is not None
        assert export.file_path.endswith(".xlsx")
        print(f"\n  Export created: {export.file_path}")

    async def test_extraction_quality_llm_judge(self, services, repos):
        """LLM-as-judge: verify extracted fields match the OM's actual content."""
        _skip_without_api_key()

        deal = await services["deal"].create_deal(
            name="Lund Pointe Apartments",
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

        processed_doc = await services["document"].get_document(doc.id)
        assert processed_doc.processing_status == ProcessingStatus.COMPLETE

        fields = await services["document"].get_extracted_fields(doc.id)
        assert len(fields) > 0, "No fields extracted"

        # Format extracted fields for the judge
        fields_summary = "\n".join(
            f"- {f.field_key}: {f.value_number if f.value_number is not None else f.value_text} "
            f"(unit: {f.unit}, confidence: {f.confidence:.2f})"
            for f in fields
        )
        print(f"\n  Extracted fields:\n{fields_summary}")

        om_context = (
            "Lund Pointe Apartments, 3300 Valentine Ln SE, Port Orchard, WA 98366.\n"
            "25-unit multifamily, 23,760 SF, built 1995.\n"
            "Offering Price: $3,150,000.\n"
            "Current NOI: $158,410. Pro Forma NOI: $173,589.\n"
            "Pro Forma Gross Revenue: $284,100. Vacancy: 3%.\n"
            "Expenses: $93,465. Reserves: $8,523.\n"
            "Unit mix: 12x 2BR/1BA (840 SF, $895/mo PF) + 13x 3BR/2BA (1,050 SF, $995/mo PF).\n"
            "Comparable cap rates: 5.10% - 6.29% (avg 5.64%)."
        )

        judgment = await _llm_judge(
            context=om_context,
            data_to_evaluate=f"Extracted fields from the OM PDF:\n{fields_summary}",
            criteria=(
                "Evaluate whether the extracted fields accurately reflect the OM's "
                "actual content. Check that:\n"
                "1. Key financial metrics are present (NOI, offering price, revenue, "
                "vacancy rate, square footage, unit count)\n"
                "2. Extracted numeric values are correct or very close to the OM's "
                "stated values\n"
                "3. No fabricated or hallucinated values that contradict the OM\n"
                "4. Field names are reasonable canonical names for CRE data\n"
                "Minor omissions are acceptable. Incorrect values are not."
            ),
        )

        print(f"\n  Judge verdict: {judgment['verdict']}")
        print(f"  Reasoning: {judgment['reasoning']}")
        if judgment.get("issues"):
            print(f"  Issues: {judgment['issues']}")

        assert judgment["verdict"] == "PASS", (
            f"LLM judge FAILED extraction quality.\n"
            f"Reasoning: {judgment['reasoning']}\n"
            f"Issues: {judgment.get('issues', [])}"
        )

    async def test_benchmarks_quality_llm_judge(self, services, repos):
        """LLM-as-judge: verify AI benchmarks are sensible for this property."""
        _skip_without_api_key()

        deal = await services["deal"].create_deal(
            name="Lund Pointe Apartments",
            address="3300 Valentine Ln SE",
            city="Port Orchard",
            state="WA",
            property_type=PropertyType.MULTIFAMILY,
            square_feet=OM_SQUARE_FEET,
        )

        suggestions = await services["benchmark"].generate_benchmarks(deal.id)
        assert len(suggestions) > 0, "No benchmarks generated"

        # Format benchmarks for the judge
        benchmarks_summary = "\n".join(
            f"- {s.key}: {s.value} {s.unit} "
            f"(range: {s.range_min}-{s.range_max}, confidence: {s.confidence:.2f}, "
            f"source: {s.source})"
            for s in suggestions
        )
        print(f"\n  Generated benchmarks:\n{benchmarks_summary}")

        judgment = await _llm_judge(
            context=(
                "25-unit multifamily apartment complex in Port Orchard, WA (Kitsap County).\n"
                "Built 1995, 23,760 SF. Located in suburban Puget Sound area.\n"
                "These benchmarks were generated by AI based only on property location "
                "and type — they did NOT see the OM document."
            ),
            data_to_evaluate=f"AI-generated market benchmarks:\n{benchmarks_summary}",
            criteria=(
                "Evaluate whether these benchmarks are reasonable market assumptions "
                "for a multifamily property in Port Orchard, WA. Check that:\n"
                "1. All essential assumptions are present (rent_psf_yr, vacancy_rate, "
                "cap_rate, opex_ratio)\n"
                "2. Values are within plausible market ranges for the Puget Sound "
                "suburban multifamily market\n"
                "3. The ranges (min/max) make sense and aren't absurdly wide or narrow\n"
                "4. Units are consistent (e.g., rates expressed correctly as decimals "
                "or percentages, rent in $/sf/yr)\n"
                "5. Values don't contradict each other (e.g., cap rate implying an "
                "unreasonable valuation)\n"
                "These are market estimates, not OM-specific values, so exact precision "
                "is not required — but they should pass a sniff test from a CRE professional."
            ),
        )

        print(f"\n  Judge verdict: {judgment['verdict']}")
        print(f"  Reasoning: {judgment['reasoning']}")
        if judgment.get("issues"):
            print(f"  Issues: {judgment['issues']}")

        assert judgment["verdict"] == "PASS", (
            f"LLM judge FAILED benchmark quality.\n"
            f"Reasoning: {judgment['reasoning']}\n"
            f"Issues: {judgment.get('issues', [])}"
        )

    async def test_judge_rejects_bad_extraction(self, services, repos):
        """Verify the LLM judge correctly FAILs when given wrong extracted values."""
        _skip_without_api_key()

        om_context = (
            "Lund Pointe Apartments, 3300 Valentine Ln SE, Port Orchard, WA 98366.\n"
            "25-unit multifamily, 23,760 SF, built 1995.\n"
            "Offering Price: $3,150,000.\n"
            "Current NOI: $158,410. Pro Forma NOI: $173,589.\n"
            "Pro Forma Gross Revenue: $284,100. Vacancy: 3%.\n"
            "Expenses: $93,465. Reserves: $8,523.\n"
            "Unit mix: 12x 2BR/1BA (840 SF) + 13x 3BR/2BA (1,050 SF).\n"
            "Comparable cap rates: 5.10% - 6.29% (avg 5.64%)."
        )

        # Fabricated extraction with wrong values
        bad_fields = (
            "Extracted fields from the OM PDF:\n"
            "- property_name: Lund Pointe Apartments (unit: None, confidence: 1.00)\n"
            "- number_of_units: 250.0 (unit: None, confidence: 0.95)\n"  # 10x too high
            "- total_square_feet: 237600.0 (unit: sf, confidence: 0.90)\n"  # 10x too high
            "- offering_price: 31500000.0 (unit: $, confidence: 0.95)\n"  # 10x too high
            "- pro_forma_noi: 50000.0 (unit: $/yr, confidence: 0.80)\n"  # Way too low
            "- vacancy_rate: 45.0 (unit: %, confidence: 0.70)\n"  # Absurdly high
            "- year_built: 2025.0 (unit: None, confidence: 0.60)\n"  # Wrong year
        )

        judgment = await _llm_judge(
            context=om_context,
            data_to_evaluate=bad_fields,
            criteria=(
                "Evaluate whether the extracted fields accurately reflect the OM's "
                "actual content. Check that:\n"
                "1. Key financial metrics are present (NOI, offering price, revenue, "
                "vacancy rate, square footage, unit count)\n"
                "2. Extracted numeric values are correct or very close to the OM's "
                "stated values\n"
                "3. No fabricated or hallucinated values that contradict the OM\n"
                "4. Field names are reasonable canonical names for CRE data\n"
                "Minor omissions are acceptable. Incorrect values are not."
            ),
        )

        print(f"\n  Judge verdict (should be FAIL): {judgment['verdict']}")
        print(f"  Reasoning: {judgment['reasoning']}")
        if judgment.get("issues"):
            print(f"  Issues: {judgment['issues']}")

        assert judgment["verdict"] == "FAIL", (
            "LLM judge should have FAILED obviously wrong extraction data, "
            f"but returned: {judgment['verdict']}\n"
            f"Reasoning: {judgment['reasoning']}"
        )
        assert len(judgment.get("issues", [])) > 0, (
            "Judge should have listed specific issues with the bad data"
        )

    async def test_judge_rejects_bad_benchmarks(self, services, repos):
        """Verify the LLM judge correctly FAILs when given nonsensical benchmarks."""
        _skip_without_api_key()

        bad_benchmarks = (
            "AI-generated market benchmarks:\n"
            "- rent_psf_yr: 500.0 $/sf/yr (range: 450.0-550.0, confidence: 0.90, "
            "source: Made Up Data)\n"  # ~40x too high for WA multifamily
            "- vacancy_rate: 75.0 % (range: 70.0-80.0, confidence: 0.85, "
            "source: Fictional Report)\n"  # No property operates at 75% vacancy
            "- cap_rate: 0.1 % (range: 0.05-0.15, confidence: 0.80, "
            "source: Imaginary Analytics)\n"  # Implies absurd valuation
            "- opex_ratio: 0.95 ratio (range: 0.90-0.99, confidence: 0.75, "
            "source: Nonexistent Survey)\n"  # 95% of revenue to expenses
        )

        judgment = await _llm_judge(
            context=(
                "25-unit multifamily apartment complex in Port Orchard, WA (Kitsap County).\n"
                "Built 1995, 23,760 SF. Located in suburban Puget Sound area.\n"
                "These benchmarks were generated by AI based only on property location "
                "and type — they did NOT see the OM document."
            ),
            data_to_evaluate=bad_benchmarks,
            criteria=(
                "Evaluate whether these benchmarks are reasonable market assumptions "
                "for a multifamily property in Port Orchard, WA. Check that:\n"
                "1. All essential assumptions are present (rent_psf_yr, vacancy_rate, "
                "cap_rate, opex_ratio)\n"
                "2. Values are within plausible market ranges for the Puget Sound "
                "suburban multifamily market\n"
                "3. The ranges (min/max) make sense and aren't absurdly wide or narrow\n"
                "4. Units are consistent (e.g., rates expressed correctly as decimals "
                "or percentages, rent in $/sf/yr)\n"
                "5. Values don't contradict each other (e.g., cap rate implying an "
                "unreasonable valuation)\n"
                "These are market estimates, not OM-specific values, so exact precision "
                "is not required — but they should pass a sniff test from a CRE professional."
            ),
        )

        print(f"\n  Judge verdict (should be FAIL): {judgment['verdict']}")
        print(f"  Reasoning: {judgment['reasoning']}")
        if judgment.get("issues"):
            print(f"  Issues: {judgment['issues']}")

        assert judgment["verdict"] == "FAIL", (
            "LLM judge should have FAILED obviously nonsensical benchmarks, "
            f"but returned: {judgment['verdict']}\n"
            f"Reasoning: {judgment['reasoning']}"
        )
        assert len(judgment.get("issues", [])) > 0, (
            "Judge should have listed specific issues with the bad benchmarks"
        )
