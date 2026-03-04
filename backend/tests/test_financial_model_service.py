import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import date
from app.domain.entities.assumption import Assumption
from app.domain.value_objects.enums import AssumptionGroup
from app.services.financial_model_service import FinancialModelService


def make_assumptions(set_id):
    """Minimal assumption set covering all required keys."""
    defs = [
        ("projection_periods", 5, AssumptionGroup.MODEL_STRUCTURE),
        ("purchase_price", 1_000_000, AssumptionGroup.TRANSACTION),
        ("ltv", 0.70, AssumptionGroup.TRANSACTION),
        ("closing_costs", 0.0, AssumptionGroup.TRANSACTION),
        ("acquisition_fee", 0.0, AssumptionGroup.TRANSACTION),
        ("base_gross_revenue", 100_000, AssumptionGroup.OPERATING),
        ("base_occupancy_rate", 1.0, AssumptionGroup.OPERATING),
        ("base_expense_ratio", 0.40, AssumptionGroup.OPERATING),
        ("base_capex_per_unit", 0.0, AssumptionGroup.OPERATING),
        ("sofr_rate", 0.04, AssumptionGroup.FINANCING),
        ("spread", 0.01, AssumptionGroup.FINANCING),
        ("loan_term", 30, AssumptionGroup.FINANCING),
        ("interest_only_years", 5, AssumptionGroup.FINANCING),
        ("exit_cap_rate", 0.06, AssumptionGroup.RETURN_TARGETS),
    ]
    return [
        Assumption(set_id=set_id, key=key, value_number=val, group=grp)
        for key, val, grp in defs
    ]


@pytest.mark.asyncio
async def test_compute_returns_projection_result():
    set_id = uuid4()
    assumption_repo = AsyncMock()
    assumption_repo.get_by_set_id.return_value = make_assumptions(set_id)

    svc = FinancialModelService(assumption_repo)
    result = await svc.compute(set_id)

    assert result.irr is not None
    assert result.equity_multiple > 1.0
    assert result.cap_rate_on_cost == pytest.approx(0.06, abs=0.001)


@pytest.mark.asyncio
async def test_compute_sensitivity_returns_grid():
    set_id = uuid4()
    assumption_repo = AsyncMock()
    assumption_repo.get_by_set_id.return_value = make_assumptions(set_id)

    svc = FinancialModelService(assumption_repo)
    grids = await svc.compute_sensitivity(
        set_id,
        x_axis={"key": "purchase_price", "values": [900_000, 1_000_000, 1_100_000]},
        y_axis={"key": "exit_cap_rate", "values": [0.055, 0.060, 0.065]},
        metrics=["irr", "equity_multiple"],
    )

    assert "irr" in grids
    assert "equity_multiple" in grids
    assert len(grids["irr"]) == 3   # 3 y values
    assert len(grids["irr"][0]) == 3  # 3 x values
