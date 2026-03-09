"""Connector management routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_connector_service
from app.api.schemas import ConnectorResponse
from app.services.connector_service import ConnectorService

router = APIRouter(tags=["connectors"])

VALID_PROVIDERS = {"onedrive", "box", "google_drive", "sharepoint"}


def _validate_provider(provider: str) -> None:
    if provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider '{provider}'. Must be one of: {sorted(VALID_PROVIDERS)}",
        )


@router.get("/connectors", response_model=list[ConnectorResponse])
async def list_connectors(
    service: Annotated[ConnectorService, Depends(get_connector_service)],
) -> list[ConnectorResponse]:
    connectors = await service.list_connectors()
    return [ConnectorResponse.model_validate(c) for c in connectors]


@router.post(
    "/connectors/{provider}/connect",
    response_model=ConnectorResponse,
)
async def connect_provider(
    provider: str,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
) -> ConnectorResponse:
    _validate_provider(provider)
    connector = await service.connect(provider)
    return ConnectorResponse.model_validate(connector)


@router.post(
    "/connectors/{provider}/disconnect",
    response_model=ConnectorResponse,
)
async def disconnect_provider(
    provider: str,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
) -> ConnectorResponse:
    _validate_provider(provider)
    connector = await service.disconnect(provider)
    return ConnectorResponse.model_validate(connector)
