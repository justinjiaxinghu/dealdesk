from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_comp_repo, get_comps_service
from app.api.schemas import CompResponse
from app.infrastructure.persistence.comp_repo import SqlAlchemyCompRepository
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return [CompResponse.model_validate(c) for c in comps]


@router.get(
    "/deals/{deal_id}/comps",
    response_model=list[CompResponse],
)
async def list_comps(
    deal_id: UUID,
    repo: Annotated[SqlAlchemyCompRepository, Depends(get_comp_repo)],
) -> list[CompResponse]:
    comps = await repo.get_by_deal_id(deal_id)
    return [CompResponse.model_validate(c) for c in comps]
