# backend/app/domain/entities/export.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import ExportType


@dataclass
class Export:
    deal_id: UUID
    set_id: UUID
    file_path: str
    export_type: ExportType = ExportType.XLSX
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
