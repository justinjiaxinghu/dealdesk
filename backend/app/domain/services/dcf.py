"""
Pure Python DCF (Discounted Cash Flow) engine. Zero external dependencies.

DCF is a financial model that estimates the value of an investment based on
its expected future cash flows. Money today is worth more than money in the
future (due to inflation, risk, opportunity cost), so future cash flows are
"discounted" back to present value.

For real estate, this model projects cash flows over a holding period:
- Year 0: Initial equity investment (negative cash flow)
- Years 1-N: Rental income minus expenses minus debt payments
- Final year: Includes sale proceeds (exit value minus remaining loan balance)

The model calculates key return metrics that investors use to evaluate deals.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.domain.value_objects.enums import Cadence, ForecastMethod

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProjectionParams:
    """
    All inputs needed to run a DCF projection.

    Model Structure:
    - start_date: When the investment begins
    - periods: Number of years (or quarters) to project
    - cadence: "annual" or "quarterly" projection intervals

    Transaction (how the deal is structured):
    - purchase_price: Total price paid for the property
    - ltv: Loan-to-Value ratio (e.g., 0.7 = 70% debt, 30% equity)
    - closing_costs: Legal fees, title insurance, etc.
    - acquisition_fee: Fee paid to the deal sponsor/manager

    Operating (property financials):
    - base_gross_revenue: Starting annual rental income
    - base_occupancy_rate: % of units rented (e.g., 0.95 = 95% occupied)
    - base_expense_ratio: Operating expenses as % of income
    - base_capex_per_unit: Capital expenditures (roof repairs, HVAC, etc.)
    - revenue/expense_forecast_method: How to project future values
      ("historical" = flat, "step_change" = fixed annual increase,
       "gradual_ramp" = linear interpolation to target)

    Financing (loan terms):
    - sofr_rate: SOFR (Secured Overnight Financing Rate) — the benchmark
      interest rate that banks use, replaced LIBOR in 2023
    - spread: Additional interest charged above SOFR (e.g., 0.02 = 2%)
    - loan_term: Total loan duration in years
    - interest_only_years: Years before principal payments begin

    Returns:
    - exit_cap_rate: Cap rate used to estimate sale price at exit
      (Exit Value = Forward NOI / Exit Cap Rate)
    """

    # Model structure
    start_date: date
    periods: int
    cadence: Cadence
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
    revenue_forecast_method: ForecastMethod
    revenue_forecast_params: dict[str, Any]
    expense_forecast_method: ForecastMethod
    expense_forecast_params: dict[str, Any]
    # Financing
    sofr_rate: float
    spread: float
    loan_term: int
    interest_only_years: int
    # Returns
    exit_cap_rate: float


@dataclass(frozen=True)
class ProjectionResult:
    """
    Output metrics from a DCF projection — the key numbers investors care about.

    - irr: IRR (Internal Rate of Return) — the annualized return rate that makes
      NPV (Net Present Value) equal zero. Answers: "What's my effective annual
      return?" A 15% IRR means your money grows ~15% per year. Returns None if
      no valid IRR exists (e.g., all positive or all negative cash flows).

    - equity_multiple: Total distributions / initial equity. Answers: "How many
      times did I get my money back?" A 2.0x multiple means you doubled your
      investment (put in $100K, got back $200K total).

    - cash_on_cash_yr1: Year 1 cash flow / equity invested. Answers: "What's my
      first-year cash yield?" An 8% CoC means $8K cash return on $100K invested.

    - cap_rate_on_cost: Year 1 NOI / total acquisition cost. Answers: "What's my
      yield on total investment?" Similar to cap rate but includes closing costs
      and fees, not just purchase price.

    - cash_flows: The full series of projected cash flows, starting with the
      initial equity investment (negative) followed by each period's net cash
      flow. The final period includes sale proceeds.
    """

    irr: float | None
    equity_multiple: float
    cash_on_cash_yr1: float
    cap_rate_on_cost: float
    cash_flows: list[float]


def _apply_forecast(base: float, period: int, method: ForecastMethod, params: dict[str, Any], total_periods: int = 5) -> float:
    """Return the value at period t (1-indexed) using the specified forecast method."""
    if method == ForecastMethod.STEP_CHANGE:
        return base + params.get("step_value", 0.0) * period
    if method == ForecastMethod.GRADUAL_RAMP:
        target = params.get("target_value", base)
        if total_periods <= 0:
            return base
        return base + (target - base) * (period / total_periods)
    # historical or unknown: flat
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
        logger.debug(
            "IRR bisection: no sign change — NPV(%.2f)=%.2f, NPV(%.2f)=%.2f; "
            "cash_flows=%s",
            low, npv_low, high, npv_high,
            [f"{cf:,.0f}" for cf in cash_flows],
        )
        return None
    for _ in range(max_iter):
        mid = (low + high) / 2
        npv_mid = _npv(cash_flows, mid)
        if abs(npv_mid) < tol or (high - low) / 2 < tol:
            logger.debug("IRR bisection converged: %.4f%%", mid * 100)
            return mid
        if npv_low * npv_mid < 0:
            high = mid
        else:
            low = mid
            npv_low = npv_mid
    result = (low + high) / 2
    logger.debug("IRR bisection max_iter reached, estimate: %.4f%%", result * 100)
    return result


def compute_projection(params: ProjectionParams) -> ProjectionResult:
    """Compute DCF projection and return metrics."""
    logger.debug(
        "DCF inputs — price=%.0f, ltv=%.2f, gross_rev=%.0f, occupancy=%.3f, "
        "exp_ratio=%.3f, capex=%.0f, exit_cap=%.4f, periods=%d, "
        "sofr=%.4f, spread=%.4f",
        params.purchase_price, params.ltv, params.base_gross_revenue,
        params.base_occupancy_rate, params.base_expense_ratio,
        params.base_capex_per_unit, params.exit_cap_rate, params.periods,
        params.sofr_rate, params.spread,
    )
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
