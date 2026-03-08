"""Dataset CRUD routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_dataset_repo
from app.api.schemas import (
    AddPropertiesRequest,
    CreateDatasetRequest,
    DatasetResponse,
    UpdateDatasetRequest,
)
from app.domain.entities.dataset import Dataset
from app.infrastructure.persistence.dataset_repo import SqlAlchemyDatasetRepository

router = APIRouter(tags=["datasets"])


@router.post(
    "/datasets",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset(
    body: CreateDatasetRequest,
    repo: Annotated[SqlAlchemyDatasetRepository, Depends(get_dataset_repo)],
) -> DatasetResponse:
    entity = Dataset(
        name=body.name,
        deal_id=body.deal_id,
        properties=body.properties,
    )
    created = await repo.create(entity)
    return DatasetResponse.model_validate(created)


@router.get("/datasets", response_model=list[DatasetResponse])
async def list_datasets(
    repo: Annotated[SqlAlchemyDatasetRepository, Depends(get_dataset_repo)],
) -> list[DatasetResponse]:
    datasets = await repo.list_all()
    return [DatasetResponse.model_validate(d) for d in datasets]


@router.get("/datasets/free", response_model=list[DatasetResponse])
async def list_free_datasets(
    repo: Annotated[SqlAlchemyDatasetRepository, Depends(get_dataset_repo)],
) -> list[DatasetResponse]:
    datasets = await repo.list_free()
    return [DatasetResponse.model_validate(d) for d in datasets]


@router.get(
    "/deals/{deal_id}/datasets", response_model=list[DatasetResponse]
)
async def list_deal_datasets(
    deal_id: UUID,
    repo: Annotated[SqlAlchemyDatasetRepository, Depends(get_dataset_repo)],
) -> list[DatasetResponse]:
    datasets = await repo.list_by_deal_id(deal_id)
    return [DatasetResponse.model_validate(d) for d in datasets]


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    repo: Annotated[SqlAlchemyDatasetRepository, Depends(get_dataset_repo)],
) -> DatasetResponse:
    entity = await repo.get_by_id(dataset_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found",
        )
    return DatasetResponse.model_validate(entity)


@router.patch("/datasets/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: UUID,
    body: UpdateDatasetRequest,
    repo: Annotated[SqlAlchemyDatasetRepository, Depends(get_dataset_repo)],
) -> DatasetResponse:
    entity = await repo.get_by_id(dataset_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found",
        )
    if body.name is not None:
        entity.name = body.name
    if body.deal_id is not None:
        entity.deal_id = body.deal_id
    if body.properties is not None:
        entity.properties = body.properties
    updated = await repo.update(entity)
    return DatasetResponse.model_validate(updated)


@router.post(
    "/datasets/{dataset_id}/properties",
    response_model=DatasetResponse,
)
async def add_properties(
    dataset_id: UUID,
    body: AddPropertiesRequest,
    repo: Annotated[SqlAlchemyDatasetRepository, Depends(get_dataset_repo)],
) -> DatasetResponse:
    entity = await repo.get_by_id(dataset_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found",
        )
    entity.properties = entity.properties + body.properties
    updated = await repo.update(entity)
    return DatasetResponse.model_validate(updated)


@router.delete(
    "/datasets/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dataset(
    dataset_id: UUID,
    repo: Annotated[SqlAlchemyDatasetRepository, Depends(get_dataset_repo)],
) -> None:
    entity = await repo.get_by_id(dataset_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found",
        )
    await repo.delete(dataset_id)
