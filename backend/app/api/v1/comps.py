from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_comps_service
from app.api.schemas import CompResponse
from app.services.comps_service import CompsService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["comps"])


@router.post(
    "/deals/{deal_id}/comps:search",
    response_model=list[CompResponse],
)
async def search_comps(
    deal_id: UUID,
    service: Annotated[CompsService, Depends(get_comps_service)],
) -> list[CompResponse]:
    try:
        comps = await service.search_comps(deal_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    return [CompResponse.model_validate(c) for c in comps]


@router.get(
    "/deals/{deal_id}/comps",
    response_model=list[CompResponse],
)
async def list_comps(
    deal_id: UUID,
    service: Annotated[CompsService, Depends(get_comps_service)],
) -> list[CompResponse]:
    comps = await service.list_comps(deal_id)
    return [CompResponse.model_validate(c) for c in comps]
