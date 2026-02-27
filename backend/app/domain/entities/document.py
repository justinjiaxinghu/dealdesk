# backend/app/domain/entities/document.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import DocumentType, ProcessingStatus
from app.domain.value_objects.types import ProcessingStep


@dataclass
class Document:
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
