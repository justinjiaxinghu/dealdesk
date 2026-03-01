# backend/app/api/v1/deals.py
"""Deal CRUD routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_deal_service
from app.api.schemas import CreateDealRequest, DealResponse, UpdateDealRequest
from app.services.deal_service import DealService

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    body: CreateDealRequest,
    service: Annotated[DealService, Depends(get_deal_service)],
) -> DealResponse:
    deal = await service.create_deal(
        name=body.name,
        address=body.address,
        city=body.city,
        state=body.state,
        property_type=body.property_type,
        latitude=body.latitude,
        longitude=body.longitude,
        square_feet=body.square_feet,
    )
    return DealResponse.model_validate(deal)


@router.get("", response_model=list[DealResponse])
async def list_deals(
    service: Annotated[DealService, Depends(get_deal_service)],
    property_type: str | None = None,
    city: str | None = None,
) -> list[DealResponse]:
    deals = await service.list_deals(
        property_type=property_type,
        city=city,
    )
    return [DealResponse.model_validate(d) for d in deals]


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: UUID,
    service: Annotated[DealService, Depends(get_deal_service)],
) -> DealResponse:
    deal = await service.get_deal(deal_id)
    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal {deal_id} not found",
        )
    return DealResponse.model_validate(deal)


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: UUID,
    body: UpdateDealRequest,
    service: Annotated[DealService, Depends(get_deal_service)],
) -> DealResponse:
    update_data = body.model_dump(exclude_unset=True)
    deal = await service.update_deal(deal_id, **update_data)
    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal {deal_id} not found",
        )
    return DealResponse.model_validate(deal)
