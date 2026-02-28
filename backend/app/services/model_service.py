# backend/app/services/model_service.py
"""Service layer for financial model computation."""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.model_result import ModelResult
from app.domain.interfaces.repositories import (
    AssumptionRepository,
    AssumptionSetRepository,
    DealRepository,
    ModelResultRepository,
)
from app.domain.model_engine import ModelEngine, ModelInput


class ModelService:
    def __init__(
        self,
        deal_repo: DealRepository,
        assumption_set_repo: AssumptionSetRepository,
        assumption_repo: AssumptionRepository,
        model_result_repo: ModelResultRepository,
    ) -> None:
        self._deal_repo = deal_repo
        self._assumption_set_repo = assumption_set_repo
        self._assumption_repo = assumption_repo
        self._model_result_repo = model_result_repo

    async def compute(self, set_id: UUID) -> ModelResult:
        # Retrieve assumption set to get the deal_id
        assumption_set = await self._assumption_set_repo.get_by_id(set_id)
        if assumption_set is None:
            raise ValueError(f"Assumption set {set_id} not found")

        deal = await self._deal_repo.get_by_id(assumption_set.deal_id)
        if deal is None:
            raise ValueError(f"Deal {assumption_set.deal_id} not found")

        assumptions = await self._assumption_repo.get_by_set_id(set_id)
        lookup = {a.key: a.value_number for a in assumptions}

        model_input = ModelInput(
            rent_psf_yr=lookup.get("rent_psf_yr"),
            square_feet=deal.square_feet,
            vacancy_rate=lookup.get("vacancy_rate"),
            opex_ratio=lookup.get("opex_ratio"),
            cap_rate=lookup.get("cap_rate"),
            purchase_price=lookup.get("purchase_price"),
            closing_costs=lookup.get("closing_costs", 0.0) or 0.0,
            capex_budget=lookup.get("capex_budget", 0.0) or 0.0,
        )

        output = ModelEngine.compute(model_input)

        result = ModelResult(
            set_id=set_id,
            noi_stabilized=output.noi_stabilized,
            exit_value=output.exit_value,
            total_cost=output.total_cost,
            profit=output.profit,
            profit_margin_pct=output.profit_margin_pct,
        )
        return await self._model_result_repo.create(result)

    async def get_result(self, set_id: UUID) -> ModelResult | None:
        return await self._model_result_repo.get_by_set_id(set_id)
