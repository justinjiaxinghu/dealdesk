# backend/app/domain/entities/document.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import DocumentType, ProcessingStatus
from app.domain.value_objects.types import ProcessingStep


@dataclass
class Document:
    """
    A PDF document uploaded for a Deal, typically an OM (Offering Memorandum).

    An Offering Memorandum is a marketing document that sellers use to present
    a property for sale, containing financial data, property details, and
    market analysis.

    When a user uploads a PDF, the system creates a Document entity and kicks off
    background processing to extract text, tables, and structured fields. The
    processing_status and processing_steps fields track progress through the
    extraction pipeline, enabling the frontend to show a live progress bar.

    The extracted data (fields, tables) is stored in separate ExtractedField
    and MarketTable entities linked by document_id.
    """

    deal_id: UUID
    document_type: DocumentType
    file_path: str
    original_filename: str
    id: UUID = field(default_factory=uuid4)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_steps: list[ProcessingStep] = field(default_factory=list)
    error_message: str | None = None
    page_count: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
