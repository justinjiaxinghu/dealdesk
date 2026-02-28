# backend/app/services/document_service.py
"""Service layer for document upload and processing."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from app.domain.entities.document import Document
from app.domain.entities.extraction import ExtractedField, MarketTable
from app.domain.interfaces.providers import (
    DocumentProcessor,
    FileStorage,
    LLMProvider,
)
from app.domain.interfaces.repositories import (
    DocumentRepository,
    ExtractedFieldRepository,
    MarketTableRepository,
)
from app.domain.value_objects.enums import DocumentType, ProcessingStatus
from app.domain.value_objects.types import ProcessingStep, RawField

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(
        self,
        document_repo: DocumentRepository,
        extracted_field_repo: ExtractedFieldRepository,
        market_table_repo: MarketTableRepository,
        file_storage: FileStorage,
        document_processor: DocumentProcessor,
        llm_provider: LLMProvider,
    ) -> None:
        self._document_repo = document_repo
        self._extracted_field_repo = extracted_field_repo
        self._market_table_repo = market_table_repo
        self._file_storage = file_storage
        self._document_processor = document_processor
        self._llm_provider = llm_provider

    async def upload_document(
        self,
        deal_id: UUID,
        file_data: bytes,
        filename: str,
        document_type: DocumentType = DocumentType.OFFERING_MEMORANDUM,
    ) -> Document:
        # Store the file
        storage_path = f"documents/{deal_id}/{filename}"
        await self._file_storage.store(file_data, storage_path)

        # Create document entity with initial processing steps
        doc = Document(
            deal_id=deal_id,
            document_type=document_type,
            file_path=storage_path,
            original_filename=filename,
            processing_status=ProcessingStatus.PENDING,
            processing_steps=[
                ProcessingStep(name="extract_text", status="pending"),
                ProcessingStep(name="extract_tables", status="pending"),
                ProcessingStep(name="normalize_fields", status="pending"),
            ],
        )
        return await self._document_repo.create(doc)

    async def process_document(self, document_id: UUID) -> None:
        """Background task: runs the full extraction pipeline."""
        doc = await self._document_repo.get_by_id(document_id)
        if doc is None:
            return

        try:
            # Update status to processing
            doc.processing_status = ProcessingStatus.EXTRACTING_TEXT
            await self._document_repo.update(doc)

            # Step 1: Extract text
            await self._document_repo.update_processing_step(
                document_id,
                ProcessingStep(name="extract_text", status="in_progress"),
            )
            file_path = await self._file_storage.retrieve(doc.file_path)
            pages = await self._document_processor.extract_text(file_path)
            doc.page_count = len(pages)
            await self._document_repo.update_processing_step(
                document_id,
                ProcessingStep(
                    name="extract_text",
                    status="complete",
                    detail=f"Extracted {len(pages)} pages",
                ),
            )

            # Step 2: Extract tables
            doc.processing_status = ProcessingStatus.EXTRACTING_TABLES
            await self._document_repo.update(doc)
            await self._document_repo.update_processing_step(
                document_id,
                ProcessingStep(name="extract_tables", status="in_progress"),
            )
            tables = await self._document_processor.extract_tables(file_path)
            # Persist market tables
            market_tables = [
                MarketTable(
                    document_id=document_id,
                    table_type="extracted",
                    headers=t.headers,
                    rows=t.rows,
                    source_page=t.page_number,
                    confidence=t.confidence,
                )
                for t in tables
            ]
            if market_tables:
                await self._market_table_repo.bulk_create(market_tables)
            await self._document_repo.update_processing_step(
                document_id,
                ProcessingStep(
                    name="extract_tables",
                    status="complete",
                    detail=f"Extracted {len(tables)} tables",
                ),
            )

            # Step 3: Normalize fields via LLM
            doc.processing_status = ProcessingStatus.NORMALIZING
            await self._document_repo.update(doc)
            await self._document_repo.update_processing_step(
                document_id,
                ProcessingStep(name="normalize_fields", status="in_progress"),
            )
            # Build raw fields from extracted text
            raw_fields: list[RawField] = []
            for page in pages:
                if page.text.strip():
                    raw_fields.append(
                        RawField(
                            key="page_text",
                            value=page.text[:2000],  # Truncate for LLM context
                            source_page=page.page_number,
                        )
                    )
            if raw_fields:
                normalized = await self._llm_provider.normalize_extracted_fields(
                    raw_fields
                )
                extracted_fields = [
                    ExtractedField(
                        document_id=document_id,
                        field_key=nf.key,
                        value_text=nf.value_text,
                        value_number=nf.value_number,
                        unit=nf.unit,
                        confidence=nf.confidence,
                    )
                    for nf in normalized
                ]
                if extracted_fields:
                    await self._extracted_field_repo.bulk_create(extracted_fields)

            await self._document_repo.update_processing_step(
                document_id,
                ProcessingStep(name="normalize_fields", status="complete"),
            )

            # Mark complete
            doc.processing_status = ProcessingStatus.COMPLETE
            await self._document_repo.update(doc)

        except Exception as exc:
            logger.exception("Document processing failed for %s", document_id)
            doc.processing_status = ProcessingStatus.FAILED
            doc.error_message = str(exc)
            await self._document_repo.update(doc)

    async def get_documents(self, deal_id: UUID) -> list[Document]:
        return await self._document_repo.get_by_deal_id(deal_id)

    async def get_document(self, document_id: UUID) -> Document | None:
        return await self._document_repo.get_by_id(document_id)

    async def get_extracted_fields(
        self, document_id: UUID
    ) -> list[ExtractedField]:
        return await self._extracted_field_repo.get_by_document_id(document_id)

    async def get_market_tables(self, document_id: UUID) -> list[MarketTable]:
        return await self._market_table_repo.get_by_document_id(document_id)
