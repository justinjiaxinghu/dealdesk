"""Report template and job domain entities."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class FillableRegion:
    """A detected fillable area in a template."""
    region_id: str
    label: str
    sheet_or_slide: str
    region_type: str
    headers: list[str] = field(default_factory=list)
    row_count: int = 0


@dataclass
class ReportTemplate:
    name: str
    file_format: str
    file_path: str
    regions: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class ReportJob:
    template_id: str
    name: str
    fills: dict = field(default_factory=dict)
    status: str = "draft"
    output_file_path: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid4()))
