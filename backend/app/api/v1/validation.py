from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_field_validation_repo, get_validation_service
from app.api.schemas import FieldValidationResponse
from app.infrastructure.persistence.field_validation_repo import (
    SqlAlchemyFieldValidationRepository,
)
from app.services.validation_service import ValidationService

router = APIRouter(tags=["validation"])


@router.post(
    "/deals/{deal_id}/validate",
    response_model=list[FieldValidationResponse],
)
async def validate_deal(
    deal_id: UUID,
    service: Annotated[ValidationService, Depends(get_validation_service)],
) -> list[FieldValidationResponse]:
    try:
        validations = await service.validate_fields(deal_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return [FieldValidationResponse.model_validate(v) for v in validations]


@router.get(
    "/deals/{deal_id}/validations",
    response_model=list[FieldValidationResponse],
)
async def list_validations(
    deal_id: UUID,
    repo: Annotated[
        SqlAlchemyFieldValidationRepository,
        Depends(get_field_validation_repo),
    ],
) -> list[FieldValidationResponse]:
    validations = await repo.get_by_deal_id(deal_id)
    return [FieldValidationResponse.model_validate(v) for v in validations]
