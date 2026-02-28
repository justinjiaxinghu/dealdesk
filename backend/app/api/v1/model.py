# backend/app/api/v1/model.py
"""Financial model compute and result routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_model_service
from app.api.schemas import ModelResultResponse
from app.services.model_service import ModelService

router = APIRouter(prefix="/assumption-sets/{set_id}", tags=["model"])


@router.post("/compute", response_model=ModelResultResponse)
async def compute_model(
    set_id: UUID,
    service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelResultResponse:
    try:
        result = await service.compute(set_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return ModelResultResponse.model_validate(result)


@router.get("/result", response_model=ModelResultResponse)
async def get_model_result(
    set_id: UUID,
    service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelResultResponse:
    result = await service.get_result(set_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No model result found for assumption set {set_id}",
        )
    return ModelResultResponse.model_validate(result)
