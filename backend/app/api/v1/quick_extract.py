# backend/app/api/v1/quick_extract.py
"""Lightweight PDF extraction for pre-populating deal forms."""

from __future__ import annotations

import asyncio
import io
import tempfile
from pathlib import Path

import pdfplumber
from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.schemas import QuickExtractResponse
from app.infrastructure.llm.openai_provider import OpenAILLMProvider
from app.domain.value_objects.types import PageText

router = APIRouter(prefix="/documents", tags=["documents"])

_MAX_PAGES = 5


def _extract_text_sync(file_bytes: bytes) -> list[PageText]:
    """Extract text from the first few pages of a PDF."""
    pages: list[PageText] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages[:_MAX_PAGES]):
            text = page.extract_text() or ""
            pages.append(PageText(page_number=i + 1, text=text))
    return pages


@router.post("/quick-extract", response_model=QuickExtractResponse)
async def quick_extract(file: UploadFile) -> QuickExtractResponse:
    """Extract basic deal info from a PDF for form pre-population."""
    file_data = await file.read()

    if not file_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    pages = await asyncio.to_thread(_extract_text_sync, file_data)
    if not pages or all(not p.text.strip() for p in pages):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract text from PDF",
        )

    llm = OpenAILLMProvider()
    result = await llm.quick_extract_deal_info(pages)

    return QuickExtractResponse(
        name=result.name,
        address=result.address,
        city=result.city,
        state=result.state,
        property_type=result.property_type,
        square_feet=result.square_feet,
    )
