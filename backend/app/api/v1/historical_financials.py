from __future__ import annotations
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import get_historical_financial_service
from app.api.schemas import HistoricalFinancialResponse
from app.services.historical_financial_service import HistoricalFinancialService

router = APIRouter(tags=["historical_financials"])


@router.get(
    "/deals/{deal_id}/historical-financials",
    response_model=list[HistoricalFinancialResponse],
)
async def list_historical_financials(
    deal_id: UUID,
    service: Annotated[HistoricalFinancialService, Depends(get_historical_financial_service)],
) -> list[HistoricalFinancialResponse]:
    items = await service.list(deal_id)
    return [HistoricalFinancialResponse.model_validate(i) for i in items]


@router.post(
    "/deals/{deal_id}/documents/{document_id}/historical-financials:extract",
    response_model=list[HistoricalFinancialResponse],
)
async def extract_historical_financials(
    deal_id: UUID,
    document_id: UUID,
    service: Annotated[HistoricalFinancialService, Depends(get_historical_financial_service)],
) -> list[HistoricalFinancialResponse]:
    try:
        items = await service.extract(deal_id, document_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return [HistoricalFinancialResponse.model_validate(i) for i in items]
