# backend/app/api/v1/explorations.py
"""Exploration session CRUD routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_exploration_session_repo
from app.api.schemas import (
    CreateExplorationRequest,
    ExplorationSessionResponse,
    UpdateExplorationRequest,
)
from app.domain.entities.exploration import ExplorationSession
from app.infrastructure.persistence.exploration_repo import (
    SqlAlchemyExplorationSessionRepository,
)

router = APIRouter(tags=["explorations"])


@router.post(
    "/deals/{deal_id}/explorations",
    response_model=ExplorationSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_deal_exploration(
    deal_id: UUID,
    body: CreateExplorationRequest,
    repo: Annotated[
        SqlAlchemyExplorationSessionRepository,
        Depends(get_exploration_session_repo),
    ],
) -> ExplorationSessionResponse:
    entity = ExplorationSession(name=body.name, deal_id=deal_id)
    created = await repo.create(entity)
    return ExplorationSessionResponse.model_validate(created)


@router.post(
    "/explorations",
    response_model=ExplorationSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_free_exploration(
    body: CreateExplorationRequest,
    repo: Annotated[
        SqlAlchemyExplorationSessionRepository,
        Depends(get_exploration_session_repo),
    ],
) -> ExplorationSessionResponse:
    entity = ExplorationSession(name=body.name)
    created = await repo.create(entity)
    return ExplorationSessionResponse.model_validate(created)


@router.get("/explorations", response_model=list[ExplorationSessionResponse])
async def list_explorations(
    repo: Annotated[
        SqlAlchemyExplorationSessionRepository,
        Depends(get_exploration_session_repo),
    ],
) -> list[ExplorationSessionResponse]:
    explorations = await repo.list_saved()
    return [ExplorationSessionResponse.model_validate(e) for e in explorations]


@router.get(
    "/explorations/{exploration_id}",
    response_model=ExplorationSessionResponse,
)
async def get_exploration(
    exploration_id: UUID,
    repo: Annotated[
        SqlAlchemyExplorationSessionRepository,
        Depends(get_exploration_session_repo),
    ],
) -> ExplorationSessionResponse:
    entity = await repo.get_by_id(exploration_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration {exploration_id} not found",
        )
    return ExplorationSessionResponse.model_validate(entity)


@router.patch(
    "/explorations/{exploration_id}",
    response_model=ExplorationSessionResponse,
)
async def update_exploration(
    exploration_id: UUID,
    body: UpdateExplorationRequest,
    repo: Annotated[
        SqlAlchemyExplorationSessionRepository,
        Depends(get_exploration_session_repo),
    ],
) -> ExplorationSessionResponse:
    entity = await repo.get_by_id(exploration_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration {exploration_id} not found",
        )
    if body.name is not None:
        entity.name = body.name
    if body.saved is not None:
        entity.saved = body.saved
    updated = await repo.update(entity)
    return ExplorationSessionResponse.model_validate(updated)


@router.delete(
    "/explorations/{exploration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_exploration(
    exploration_id: UUID,
    repo: Annotated[
        SqlAlchemyExplorationSessionRepository,
        Depends(get_exploration_session_repo),
    ],
) -> None:
    entity = await repo.get_by_id(exploration_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration {exploration_id} not found",
        )
    await repo.delete(exploration_id)
