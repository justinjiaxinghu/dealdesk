# backend/tests/test_model_engine.py
import pytest

from app.domain.model_engine import ModelEngine, ModelInput, ModelOutput


class TestModelEngine:
    def test_basic_computation(self):
        inp = ModelInput(
            rent_psf_yr=30.0,
            square_feet=50000.0,
            vacancy_rate=0.05,
            opex_ratio=0.35,
            cap_rate=0.065,
            purchase_price=15_000_000.0,
            closing_costs=450_000.0,
            capex_budget=500_000.0,
        )
        result = ModelEngine.compute(inp)

        # Revenue = 30 * 50000 = 1,500,000
        # Effective revenue = 1,500,000 * (1 - 0.05) = 1,425,000
        # OpEx = 0.35 * 1,425,000 = 498,750
        # NOI = 1,425,000 - 498,750 = 926,250
        assert result.gross_revenue == pytest.approx(1_500_000.0)
        assert result.effective_revenue == pytest.approx(1_425_000.0)
        assert result.operating_expenses == pytest.approx(498_750.0)
        assert result.noi_stabilized == pytest.approx(926_250.0)

        # Exit value = 926,250 / 0.065 = 14,250,000
        assert result.exit_value == pytest.approx(14_250_000.0)

        # Total cost = 15,000,000 + 450,000 + 500,000 = 15,950,000
        assert result.total_cost == pytest.approx(15_950_000.0)

        # Profit = 14,250,000 - 15,950,000 = -1,700,000
        assert result.profit == pytest.approx(-1_700_000.0)

        # Margin = -1,700,000 / 15,950,000 = -0.10658...
        assert result.profit_margin_pct == pytest.approx(-10.658, rel=0.01)

    def test_zero_vacancy(self):
        inp = ModelInput(
            rent_psf_yr=25.0,
            square_feet=10000.0,
            vacancy_rate=0.0,
            opex_ratio=0.30,
            cap_rate=0.07,
            purchase_price=3_000_000.0,
            closing_costs=90_000.0,
            capex_budget=100_000.0,
        )
        result = ModelEngine.compute(inp)
        assert result.gross_revenue == pytest.approx(250_000.0)
        assert result.effective_revenue == pytest.approx(250_000.0)
        assert result.noi_stabilized == pytest.approx(175_000.0)

    def test_missing_required_fields_raises(self):
        inp = ModelInput(
            rent_psf_yr=None,
            square_feet=50000.0,
            vacancy_rate=0.05,
            opex_ratio=0.35,
            cap_rate=0.065,
            purchase_price=15_000_000.0,
            closing_costs=0.0,
            capex_budget=0.0,
        )
        with pytest.raises(ValueError, match="rent_psf_yr"):
            ModelEngine.compute(inp)

    def test_zero_cap_rate_raises(self):
        inp = ModelInput(
            rent_psf_yr=30.0,
            square_feet=50000.0,
            vacancy_rate=0.05,
            opex_ratio=0.35,
            cap_rate=0.0,
            purchase_price=15_000_000.0,
            closing_costs=0.0,
            capex_budget=0.0,
        )
        with pytest.raises(ValueError, match="cap_rate"):
            ModelEngine.compute(inp)
