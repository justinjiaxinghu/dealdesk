import pytest
from app.domain.services.dcf import (
    ProjectionParams,
    ProjectionResult,
    compute_projection,
    _bisect_irr,
)
from datetime import date


def base_params(**overrides) -> ProjectionParams:
    defaults = dict(
        start_date=date(2026, 1, 1),
        periods=5,
        cadence="annual",
        purchase_price=1_000_000.0,
        ltv=0.70,
        closing_costs=0.0,
        acquisition_fee=0.0,
        base_gross_revenue=100_000.0,
        base_occupancy_rate=1.0,
        base_expense_ratio=0.40,
        base_capex_per_unit=0.0,
        revenue_forecast_method="historical",
        revenue_forecast_params={},
        expense_forecast_method="historical",
        expense_forecast_params={},
        sofr_rate=0.04,
        spread=0.01,
        loan_term=30,
        interest_only_years=5,
        exit_cap_rate=0.06,
    )
    defaults.update(overrides)
    return ProjectionParams(**defaults)


def test_cap_rate_on_cost():
    params = base_params()
    result = compute_projection(params)
    # NOI = 100k * 1.0 * (1 - 0.40) = 60k; total_cost = 1M
    assert result.cap_rate_on_cost == pytest.approx(0.06, abs=0.001)


def test_equity_multiple():
    params = base_params()
    result = compute_projection(params)
    # equity = 300k; annual net CF = 60k NOI - 35k IO debt = 25k/yr x5 = 125k
    # terminal: exit = 60k/0.06 = 1M, remaining IO balance = 700k, terminal CF = 300k
    # equity multiple = (125k + 300k) / 300k = 1.4167
    assert result.equity_multiple == pytest.approx(1.4167, abs=0.01)


def test_cash_on_cash_yr1():
    params = base_params()
    result = compute_projection(params)
    # yr1 net CF = 25k, equity = 300k → 8.33%
    assert result.cash_on_cash_yr1 == pytest.approx(0.0833, abs=0.001)


def test_irr_is_reasonable():
    params = base_params()
    result = compute_projection(params)
    assert result.irr is not None
    assert 0.07 < result.irr < 0.10


def test_zero_ltv_no_debt_service():
    params = base_params(ltv=0.0)
    result = compute_projection(params)
    # No debt: NOI = 60k/yr, equity = 1M, CoC = 6%
    assert result.cash_on_cash_yr1 == pytest.approx(0.06, abs=0.001)
    # Exit value = 1M, total CF = 60k*5 + 1M = 1.3M, EM = 1.3
    assert result.equity_multiple == pytest.approx(1.3, abs=0.01)


def test_bisect_irr_simple():
    # CF = [-100, 110] → IRR = 10%
    irr = _bisect_irr([-100.0, 110.0])
    assert irr == pytest.approx(0.10, abs=0.0001)


def test_bisect_irr_two_periods():
    # CF = [-100, 0, 121] → IRR = 10%
    irr = _bisect_irr([-100.0, 0.0, 121.0])
    assert irr == pytest.approx(0.10, abs=0.0001)
