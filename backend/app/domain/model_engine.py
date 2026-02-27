# backend/app/domain/model_engine.py
from dataclasses import dataclass


@dataclass
class ModelInput:
    rent_psf_yr: float | None
    square_feet: float | None
    vacancy_rate: float | None
    opex_ratio: float | None
    cap_rate: float | None
    purchase_price: float | None
    closing_costs: float = 0.0
    capex_budget: float = 0.0


@dataclass(frozen=True)
class ModelOutput:
    gross_revenue: float
    effective_revenue: float
    operating_expenses: float
    noi_stabilized: float
    exit_value: float
    total_cost: float
    profit: float
    profit_margin_pct: float


class ModelEngine:
    REQUIRED_FIELDS = ["rent_psf_yr", "square_feet", "vacancy_rate", "opex_ratio", "cap_rate", "purchase_price"]

    @staticmethod
    def compute(inp: ModelInput) -> ModelOutput:
        missing = [f for f in ModelEngine.REQUIRED_FIELDS if getattr(inp, f) is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        if inp.cap_rate == 0.0:
            raise ValueError("cap_rate must be non-zero")

        gross_revenue = inp.rent_psf_yr * inp.square_feet
        effective_revenue = gross_revenue * (1 - inp.vacancy_rate)
        operating_expenses = inp.opex_ratio * effective_revenue
        noi = effective_revenue - operating_expenses

        exit_value = noi / inp.cap_rate
        total_cost = inp.purchase_price + inp.closing_costs + inp.capex_budget
        profit = exit_value - total_cost
        margin_pct = (profit / total_cost) * 100 if total_cost != 0 else 0.0

        return ModelOutput(
            gross_revenue=gross_revenue,
            effective_revenue=effective_revenue,
            operating_expenses=operating_expenses,
            noi_stabilized=noi,
            exit_value=exit_value,
            total_cost=total_cost,
            profit=profit,
            profit_margin_pct=margin_pct,
        )
