# backend/app/api/v1/documents.py
"""Document upload and retrieval routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.dependencies import get_document_service, get_document_repo
from app.api.schemas import (
    DocumentResponse,
    ExtractedFieldResponse,
    MarketTableResponse,
)
from app.infrastructure.file_storage.local import LocalFileStorage
from app.infrastructure.persistence.document_repo import SqlAlchemyDocumentRepository
from app.services.document_service import DocumentService

router = APIRouter(prefix="/deals/{deal_id}/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    deal_id: UUID,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentResponse:
    file_data = await file.read()
    doc = await service.upload_document(
        deal_id=deal_id,
        file_data=file_data,
        filename=file.filename or "unknown.pdf",
    )
    # Trigger background processing
    background_tasks.add_task(service.process_document, doc.id)
    return DocumentResponse.model_validate(doc)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    deal_id: UUID,
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[DocumentResponse]:
    docs = await service.get_documents(deal_id)
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    deal_id: UUID,
    document_id: UUID,
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentResponse:
    doc = await service.get_document(document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    return DocumentResponse.model_validate(doc)


@router.get("/{document_id}/pdf")
async def download_pdf(
    deal_id: UUID,
    document_id: UUID,
    repo: Annotated[SqlAlchemyDocumentRepository, Depends(get_document_repo)],
) -> FileResponse:
    doc = await repo.get_by_id(document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    file_storage = LocalFileStorage()
    try:
        file_path = await file_storage.retrieve(doc.file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found on disk",
        )
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found on disk",
        )
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=doc.original_filename,
    )


@router.get("/{document_id}/fields", response_model=list[ExtractedFieldResponse])
async def get_extracted_fields(
    deal_id: UUID,
    document_id: UUID,
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[ExtractedFieldResponse]:
    fields = await service.get_extracted_fields(document_id)
    return [ExtractedFieldResponse.model_validate(f) for f in fields]


@router.get("/{document_id}/tables", response_model=list[MarketTableResponse])
async def get_market_tables(
    deal_id: UUID,
    document_id: UUID,
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[MarketTableResponse]:
    tables = await service.get_market_tables(document_id)
    return [MarketTableResponse.model_validate(t) for t in tables]
