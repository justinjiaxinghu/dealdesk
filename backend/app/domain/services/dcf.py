"""Pure Python DCF engine. Zero external dependencies."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class ProjectionParams:
    # Model structure
    start_date: date
    periods: int
    cadence: str                      # "annual" | "quarterly"
    # Transaction
    purchase_price: float
    ltv: float
    closing_costs: float
    acquisition_fee: float
    # Operating
    base_gross_revenue: float
    base_occupancy_rate: float
    base_expense_ratio: float
    base_capex_per_unit: float
    revenue_forecast_method: str      # "historical" | "step_change" | "gradual_ramp"
    revenue_forecast_params: dict[str, Any]
    expense_forecast_method: str
    expense_forecast_params: dict[str, Any]
    # Financing
    sofr_rate: float
    spread: float
    loan_term: int                    # years
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


def _apply_forecast(base: float, period: int, method: str, params: dict[str, Any], total_periods: int = 5) -> float:
    """Return the value at period t (1-indexed) using the specified forecast method."""
    if method == "step_change":
        return base + params.get("step_value", 0.0) * period
    if method == "gradual_ramp":
        target = params.get("target_value", base)
        if total_periods <= 0:
            return base
        return base + (target - base) * (period / total_periods)
    # "historical" or unknown: flat
    return base


def _npv(cash_flows: list[float], rate: float) -> float:
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))


def _bisect_irr(
    cash_flows: list[float],
    low: float = -0.5,
    high: float = 10.0,
    tol: float = 1e-8,
    max_iter: int = 1000,
) -> float | None:
    """Bisection method to find IRR. Returns None if no root found in [low, high]."""
    npv_low = _npv(cash_flows, low)
    npv_high = _npv(cash_flows, high)
    if npv_low * npv_high > 0:
        return None  # No sign change
    for _ in range(max_iter):
        mid = (low + high) / 2
        npv_mid = _npv(cash_flows, mid)
        if abs(npv_mid) < tol or (high - low) / 2 < tol:
            return mid
        if npv_low * npv_mid < 0:
            high = mid
        else:
            low = mid
            npv_low = npv_mid
    return (low + high) / 2


def compute_projection(params: ProjectionParams) -> ProjectionResult:
    """Compute DCF projection and return metrics."""
    equity = params.purchase_price * (1 - params.ltv)
    loan = params.purchase_price * params.ltv
    total_cost = params.purchase_price + params.closing_costs + params.acquisition_fee

    interest_rate = params.sofr_rate + params.spread

    def _debt_service(period: int) -> float:
        if loan == 0:
            return 0.0
        if period <= params.interest_only_years:
            return loan * interest_rate
        remaining_term = params.loan_term - params.interest_only_years
        if remaining_term <= 0 or interest_rate == 0:
            return loan / max(params.loan_term, 1)
        r = interest_rate
        n = remaining_term
        return loan * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    def _remaining_balance(period: int) -> float:
        if loan == 0:
            return 0.0
        if period <= params.interest_only_years:
            return loan
        amort_periods = period - params.interest_only_years
        remaining_term = params.loan_term - params.interest_only_years
        if remaining_term <= 0 or interest_rate == 0:
            return max(0.0, loan - loan * amort_periods / max(params.loan_term, 1))
        r = interest_rate
        n = remaining_term
        return loan * ((1 + r) ** n - (1 + r) ** amort_periods) / ((1 + r) ** n - 1)

    cash_flows: list[float] = [-equity]
    period_nois: list[float] = []

    for t in range(1, params.periods + 1):
        rev = _apply_forecast(
            params.base_gross_revenue, t,
            params.revenue_forecast_method, params.revenue_forecast_params,
            params.periods,
        )
        egi = rev * params.base_occupancy_rate
        exp_ratio = _apply_forecast(
            params.base_expense_ratio, t,
            params.expense_forecast_method, params.expense_forecast_params,
            params.periods,
        )
        opex = egi * exp_ratio
        noi = egi - opex - params.base_capex_per_unit
        period_nois.append(noi)
        ds = _debt_service(t)
        cash_flows.append(noi - ds)

    # Terminal cash flow: exit value uses forward NOI (period n+1)
    forward_rev = _apply_forecast(
        params.base_gross_revenue,
        params.periods + 1,
        params.revenue_forecast_method,
        params.revenue_forecast_params,
        params.periods,
    )
    forward_egi = forward_rev * params.base_occupancy_rate
    forward_exp_ratio = _apply_forecast(
        params.base_expense_ratio,
        params.periods + 1,
        params.expense_forecast_method,
        params.expense_forecast_params,
        params.periods,
    )
    forward_noi = forward_egi - forward_egi * forward_exp_ratio - params.base_capex_per_unit
    exit_value = forward_noi / params.exit_cap_rate if params.exit_cap_rate > 0 else 0.0
    remaining_bal = _remaining_balance(params.periods)
    cash_flows[-1] += exit_value - remaining_bal

    yr1_noi = period_nois[0] if period_nois else 0.0
    cap_rate_on_cost = yr1_noi / total_cost if total_cost > 0 else 0.0
    yr1_net_cf = cash_flows[1] if len(cash_flows) > 1 else 0.0
    coc_yr1 = yr1_net_cf / equity if equity > 0 else 0.0
    total_distributions = sum(cash_flows[1:])
    equity_multiple = total_distributions / equity if equity > 0 else 0.0
    irr = _bisect_irr(cash_flows)

    return ProjectionResult(
        irr=irr,
        equity_multiple=equity_multiple,
        cash_on_cash_yr1=coc_yr1,
        cap_rate_on_cost=cap_rate_on_cost,
        cash_flows=cash_flows,
    )
