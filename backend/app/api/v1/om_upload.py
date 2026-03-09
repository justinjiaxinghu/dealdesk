# backend/app/api/v1/om_upload.py
"""OM upload endpoint for explorations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.dependencies import (
    get_deal_service,
    get_document_service,
    get_exploration_session_repo,
)
from app.domain.value_objects.enums import PropertyType
from app.infrastructure.persistence.exploration_repo import (
    SqlAlchemyExplorationSessionRepository,
)
from app.services.deal_service import DealService
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["explorations"])


class OMUploadResponse(BaseModel):
    deal_id: UUID
    document_id: UUID
    exploration_id: UUID


@router.post(
    "/explorations/{exploration_id}/upload-om",
    response_model=OMUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_om(
    exploration_id: UUID,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    deal_service: Annotated[DealService, Depends(get_deal_service)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    exploration_repo: Annotated[
        SqlAlchemyExplorationSessionRepository,
        Depends(get_exploration_session_repo),
    ],
) -> OMUploadResponse:
    """Upload an Offering Memorandum PDF to an exploration.

    If the exploration has no deal yet, creates one and links it.
    If the exploration already has a deal, adds the document to the existing deal.
    Triggers background document processing pipeline.
    """
    # 1. Look up exploration
    exploration = await exploration_repo.get_by_id(exploration_id)
    if exploration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration {exploration_id} not found",
        )

    # 2. Create or reuse deal
    if exploration.deal_id is None:
        # Derive deal name from filename (strip extension)
        filename = file.filename or "unknown.pdf"
        deal_name = Path(filename).stem

        deal = await deal_service.create_deal(
            name=deal_name,
            address="TBD",
            city="TBD",
            state="TBD",
            property_type=PropertyType.OTHER,
        )

        # Link deal to exploration
        exploration.deal_id = deal.id
        await exploration_repo.update(exploration)

        deal_id = deal.id
        logger.info("Created deal %s for exploration %s", deal_id, exploration_id)
    else:
        deal_id = exploration.deal_id
        logger.info("Using existing deal %s for exploration %s", deal_id, exploration_id)

    # 3. Upload document and trigger processing
    file_data = await file.read()
    doc = await document_service.upload_document(
        deal_id=deal_id,
        file_data=file_data,
        filename=file.filename or "unknown.pdf",
    )
    background_tasks.add_task(document_service.process_document, doc.id)

    return OMUploadResponse(
        deal_id=deal_id,
        document_id=doc.id,
        exploration_id=exploration_id,
    )
