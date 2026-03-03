from __future__ import annotations
from datetime import date
from uuid import UUID
from app.domain.interfaces.repositories import AssumptionRepository
from app.domain.services.dcf import ProjectionParams, ProjectionResult, compute_projection


class FinancialModelService:
    def __init__(self, assumption_repo: AssumptionRepository) -> None:
        self._assumption_repo = assumption_repo

    async def _load_params(
        self, set_id: UUID, overrides: dict | None = None
    ) -> ProjectionParams:
        assumptions = await self._assumption_repo.get_by_set_id(set_id)
        vals: dict = {a.key: a.value_number for a in assumptions if a.value_number is not None}
        forecast: dict = {
            a.key: (a.forecast_method, a.forecast_params or {})
            for a in assumptions
            if a.forecast_method
        }
        if overrides:
            vals.update(overrides)

        def v(key: str, default: float = 0.0) -> float:
            return float(vals.get(key, default))

        def fm(key: str) -> tuple[str, dict]:
            return forecast.get(key, ("historical", {}))

        rev_method, rev_params = fm("base_gross_revenue")
        exp_method, exp_params = fm("base_expense_ratio")

        return ProjectionParams(
            start_date=date.today(),
            periods=int(v("projection_periods", 5)),
            cadence="annual",
            purchase_price=v("purchase_price"),
            ltv=v("ltv", 0.70),
            closing_costs=v("closing_costs"),
            acquisition_fee=v("acquisition_fee"),
            base_gross_revenue=v("base_gross_revenue"),
            base_occupancy_rate=v("base_occupancy_rate", 1.0),
            base_expense_ratio=v("base_expense_ratio", 0.40),
            base_capex_per_unit=v("base_capex_per_unit"),
            revenue_forecast_method=rev_method,
            revenue_forecast_params=rev_params,
            expense_forecast_method=exp_method,
            expense_forecast_params=exp_params,
            sofr_rate=v("sofr_rate", 0.04),
            spread=v("spread", 0.01),
            loan_term=int(v("loan_term", 30)),
            interest_only_years=int(v("interest_only_years", 0)),
            exit_cap_rate=v("exit_cap_rate", 0.06),
        )

    async def compute(self, set_id: UUID) -> ProjectionResult:
        params = await self._load_params(set_id)
        return compute_projection(params)

    async def compute_sensitivity(
        self,
        set_id: UUID,
        x_axis: dict,
        y_axis: dict,
        metrics: list[str],
    ) -> dict[str, list[list[float | None]]]:
        """Returns {metric: [[val_per_x_for_y0], [val_per_x_for_y1], ...]}"""
        grids: dict[str, list[list[float | None]]] = {m: [] for m in metrics}

        for y_val in y_axis["values"]:
            row: dict[str, list[float | None]] = {m: [] for m in metrics}
            for x_val in x_axis["values"]:
                overrides = {x_axis["key"]: x_val, y_axis["key"]: y_val}
                params = await self._load_params(set_id, overrides)
                result = compute_projection(params)
                for metric in metrics:
                    row[metric].append(getattr(result, metric, None))
            for metric in metrics:
                grids[metric].append(row[metric])

        return grids
