# backend/app/api/v1/assumptions.py
"""Assumption set, assumption, and benchmark routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_assumption_repo,
    get_assumption_set_repo,
    get_benchmark_service,
)
from app.api.schemas import (
    AssumptionResponse,
    AssumptionSetResponse,
    BenchmarkResponse,
    BulkUpdateAssumptionsRequest,
    GenerateBenchmarksRequest,
)
from app.domain.entities.assumption import Assumption
from app.domain.value_objects.enums import SourceType
from app.infrastructure.persistence.assumption_repo import (
    SqlAlchemyAssumptionRepository,
    SqlAlchemyAssumptionSetRepository,
)
from app.services.benchmark_service import BenchmarkService

router = APIRouter(tags=["assumptions"])


@router.get(
    "/deals/{deal_id}/assumption-sets",
    response_model=list[AssumptionSetResponse],
)
async def list_assumption_sets(
    deal_id: UUID,
    repo: Annotated[
        SqlAlchemyAssumptionSetRepository, Depends(get_assumption_set_repo)
    ],
) -> list[AssumptionSetResponse]:
    sets = await repo.get_by_deal_id(deal_id)
    return [AssumptionSetResponse.model_validate(s) for s in sets]


@router.get(
    "/assumption-sets/{set_id}/assumptions",
    response_model=list[AssumptionResponse],
)
async def list_assumptions(
    set_id: UUID,
    repo: Annotated[SqlAlchemyAssumptionRepository, Depends(get_assumption_repo)],
) -> list[AssumptionResponse]:
    assumptions = await repo.get_by_set_id(set_id)
    return [AssumptionResponse.model_validate(a) for a in assumptions]


@router.put(
    "/assumption-sets/{set_id}/assumptions",
    response_model=list[AssumptionResponse],
)
async def bulk_update_assumptions(
    set_id: UUID,
    body: BulkUpdateAssumptionsRequest,
    repo: Annotated[SqlAlchemyAssumptionRepository, Depends(get_assumption_repo)],
) -> list[AssumptionResponse]:
    assumptions = [
        Assumption(
            set_id=set_id,
            key=a.key,
            value_number=a.value_number,
            unit=a.unit,
            range_min=a.range_min,
            range_max=a.range_max,
            source_type=a.source_type,
            source_ref=a.source_ref,
            notes=a.notes,
        )
        for a in body.assumptions
    ]
    result = await repo.bulk_upsert(assumptions)
    return [AssumptionResponse.model_validate(a) for a in result]


@router.post(
    "/deals/{deal_id}/benchmarks:generate",
    response_model=list[BenchmarkResponse],
)
async def generate_benchmarks(
    deal_id: UUID,
    body: GenerateBenchmarksRequest,
    service: Annotated[BenchmarkService, Depends(get_benchmark_service)],
) -> list[BenchmarkResponse]:
    try:
        suggestions = await service.generate_benchmarks(deal_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return [BenchmarkResponse.model_validate(s) for s in suggestions]
