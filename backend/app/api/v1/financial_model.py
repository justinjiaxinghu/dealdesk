from __future__ import annotations
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import get_financial_model_service, get_assumption_set_repo
from app.api.schemas import ProjectionResultResponse, SensitivityRequest, SensitivityResponse
from app.services.financial_model_service import FinancialModelService

router = APIRouter(tags=["financial_model"])


async def _resolve_set_id(deal_id: UUID, assumption_set_repo) -> UUID:
    sets = await assumption_set_repo.get_by_deal_id(deal_id)
    if not sets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assumption set found for this deal",
        )
    return sets[0].id


@router.post(
    "/deals/{deal_id}/financial-model:compute",
    response_model=ProjectionResultResponse,
)
async def compute_financial_model(
    deal_id: UUID,
    service: Annotated[FinancialModelService, Depends(get_financial_model_service)],
    assumption_set_repo=Depends(get_assumption_set_repo),
) -> ProjectionResultResponse:
    set_id = await _resolve_set_id(deal_id, assumption_set_repo)
    result = await service.compute(set_id)
    return ProjectionResultResponse(
        irr=result.irr,
        equity_multiple=result.equity_multiple,
        cash_on_cash_yr1=result.cash_on_cash_yr1,
        cap_rate_on_cost=result.cap_rate_on_cost,
        cash_flows=result.cash_flows,
    )


@router.post(
    "/deals/{deal_id}/sensitivity",
    response_model=SensitivityResponse,
)
async def compute_sensitivity(
    deal_id: UUID,
    body: SensitivityRequest,
    service: Annotated[FinancialModelService, Depends(get_financial_model_service)],
    assumption_set_repo=Depends(get_assumption_set_repo),
) -> SensitivityResponse:
    set_id = await _resolve_set_id(deal_id, assumption_set_repo)
    grids = await service.compute_sensitivity(
        set_id,
        x_axis={"key": body.x_axis.key, "values": body.x_axis.values},
        y_axis={"key": body.y_axis.key, "values": body.y_axis.values},
        metrics=body.metrics,
    )
    return SensitivityResponse(grids=grids, x_axis=body.x_axis, y_axis=body.y_axis)
