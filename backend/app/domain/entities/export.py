# backend/app/domain/entities/export.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import ExportType


@dataclass
class Export:
    """
    A record of an exported file (typically Excel) for a Deal's AssumptionSet.

    After analyzing a deal, users export the assumptions and extracted data to
    Excel for further modeling or sharing with colleagues. This entity tracks
    each export: which deal/assumption set it's for, where the file is stored,
    and when it was created.

    The actual Excel generation is handled by the ExcelExporter in infrastructure.
    """

    deal_id: UUID
    set_id: UUID
    file_path: str
    export_type: ExportType = ExportType.XLSX
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
