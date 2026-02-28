# backend/app/api/v1/exports.py
"""Export routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.api.dependencies import get_export_service
from app.api.schemas import ExportResponse
from app.services.export_service import ExportService

router = APIRouter(prefix="/assumption-sets/{set_id}", tags=["exports"])


@router.post("/export/xlsx", response_model=ExportResponse)
async def export_xlsx(
    set_id: UUID,
    service: Annotated[ExportService, Depends(get_export_service)],
) -> ExportResponse:
    try:
        export = await service.export_xlsx(set_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return ExportResponse.model_validate(export)


@router.get("/export/xlsx")
async def download_xlsx(
    set_id: UUID,
    service: Annotated[ExportService, Depends(get_export_service)],
) -> Response:
    """Generate and return the XLSX file directly as a download."""
    try:
        xlsx_bytes, filename = await service.generate_xlsx(set_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
