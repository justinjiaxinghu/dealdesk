# backend/app/api/v1/om_upload.py
"""OM upload endpoint for explorations."""

from __future__ import annotations

import asyncio
import io
import logging
from pathlib import Path
from typing import Annotated
from uuid import UUID

import pdfplumber
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    DbSession,
    get_deal_service,
    get_document_service,
    get_exploration_session_repo,
)
from app.domain.value_objects.enums import PropertyType
from app.domain.value_objects.types import PageText
from app.infrastructure.llm.openai_provider import OpenAILLMProvider
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
    session: DbSession,
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

    # 4. Quick-extract deal metadata from PDF and update the deal
    try:
        pages = await asyncio.to_thread(_extract_text_sync, file_data)
        if pages and any(p.text.strip() for p in pages):
            llm = OpenAILLMProvider()
            result = await llm.quick_extract_deal_info(pages)
            updates: dict = {}
            if result.name:
                updates["name"] = result.name
            if result.address:
                updates["address"] = result.address
            if result.city:
                updates["city"] = result.city
            if result.state:
                updates["state"] = result.state
            if result.property_type:
                try:
                    updates["property_type"] = PropertyType(result.property_type)
                except ValueError:
                    pass
            if result.square_feet:
                updates["square_feet"] = result.square_feet
            if updates:
                await deal_service.update_deal(deal_id, **updates)
                logger.info("Updated deal %s with quick-extract metadata", deal_id)
    except Exception:
        logger.exception("Quick-extract failed for deal %s, continuing", deal_id)

    # Commit now so the deal is visible to subsequent requests before the response
    await session.commit()

    background_tasks.add_task(document_service.process_document, doc.id)

    return OMUploadResponse(
        deal_id=deal_id,
        document_id=doc.id,
        exploration_id=exploration_id,
    )


def _extract_text_sync(file_bytes: bytes) -> list[PageText]:
    """Extract text from the first few pages of a PDF."""
    pages: list[PageText] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages[:5]):
            text = page.extract_text() or ""
            pages.append(PageText(page_number=i + 1, text=text))
    return pages
