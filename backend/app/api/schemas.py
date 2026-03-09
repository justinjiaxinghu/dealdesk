# backend/app/api/schemas.py
"""Pydantic request/response schemas for the DealDesk API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.value_objects.enums import (
    DocumentType,
    ExportType,
    ProcessingStatus,
    PropertyType,
    SourceType,
)


# ---------------------------------------------------------------------------
# Deal
# ---------------------------------------------------------------------------


class CreateDealRequest(BaseModel):
    name: str
    address: str
    city: str
    state: str
    property_type: PropertyType
    latitude: float | None = None
    longitude: float | None = None
    square_feet: float | None = None
    tags: list[str] = []


class UpdateDealRequest(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    property_type: PropertyType | None = None
    latitude: float | None = None
    longitude: float | None = None
    square_feet: float | None = None
    tags: list[str] | None = None


class DealResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    name: str
    address: str
    city: str
    state: str
    property_type: PropertyType
    latitude: float | None = None
    longitude: float | None = None
    square_feet: float | None = None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Processing Steps & Documents
# ---------------------------------------------------------------------------


class ProcessingStepResponse(BaseModel):
    model_config = {"from_attributes": True}

    name: str
    status: str
    detail: str = ""


class DocumentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    deal_id: UUID
    document_type: DocumentType
    file_path: str
    original_filename: str
    processing_status: ProcessingStatus
    processing_steps: list[ProcessingStepResponse] = []
    error_message: str | None = None
    page_count: int | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


class ExtractedFieldResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    document_id: UUID
    field_key: str
    value_text: str | None = None
    value_number: float | None = None
    unit: str | None = None
    confidence: float = 0.0
    source_page: int | None = None


class MarketTableResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    document_id: UUID
    table_type: str
    headers: list[str] = []
    rows: list[list[str]] = []
    source_page: int | None = None
    confidence: float = 0.0


# ---------------------------------------------------------------------------
# Assumptions
# ---------------------------------------------------------------------------


class AssumptionSetResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    deal_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class AssumptionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    set_id: UUID
    key: str
    value_number: float | None = None
    unit: str | None = None
    range_min: float | None = None
    range_max: float | None = None
    source_type: SourceType
    source_ref: str | None = None
    notes: str | None = None
    group: str | None = None
    forecast_method: str | None = None
    forecast_params: dict | None = None
    updated_at: datetime


class UpdateAssumptionRequest(BaseModel):
    key: str
    value_number: float | None = None
    unit: str | None = None
    range_min: float | None = None
    range_max: float | None = None
    source_type: SourceType = SourceType.MANUAL
    source_ref: str | None = None
    notes: str | None = None
    group: str | None = None
    forecast_method: str | None = None
    forecast_params: dict | None = None


class BulkUpdateAssumptionsRequest(BaseModel):
    assumptions: list[UpdateAssumptionRequest]


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


class ExportResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    deal_id: UUID
    set_id: UUID
    file_path: str
    export_type: ExportType
    created_at: datetime


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------


class GenerateBenchmarksRequest(BaseModel):
    pass  # Uses deal location data; no additional input required


class QuickExtractResponse(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    property_type: str | None = None
    square_feet: float | None = None


class BenchmarkResponse(BaseModel):
    key: str
    value: float
    unit: str
    range_min: float
    range_max: float
    source: str
    confidence: float


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class ValidationSourceResponse(BaseModel):
    url: str
    title: str
    snippet: str


class SearchStepResultResponse(BaseModel):
    url: str
    title: str
    snippet: str


class SearchStepResponse(BaseModel):
    phase: str
    query: str
    results: list[SearchStepResultResponse] = []


class FieldValidationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    deal_id: UUID
    field_key: str
    om_value: float | None = None
    market_value: float | None = None
    status: str
    explanation: str
    sources: list[ValidationSourceResponse] = []
    confidence: float
    search_steps: list[SearchStepResponse] = []
    created_at: datetime


# ---------------------------------------------------------------------------
# Historical Financials
# ---------------------------------------------------------------------------


class HistoricalFinancialResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    deal_id: UUID
    period_label: str
    metric_key: str
    value: float
    unit: str | None
    source: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Financial Model
# ---------------------------------------------------------------------------


class ProjectionResultResponse(BaseModel):
    irr: float | None
    equity_multiple: float
    cash_on_cash_yr1: float
    cap_rate_on_cost: float
    cash_flows: list[float]


class SensitivityAxisRequest(BaseModel):
    key: str
    values: list[float]


class SensitivityRequest(BaseModel):
    x_axis: SensitivityAxisRequest
    y_axis: SensitivityAxisRequest
    metrics: list[str] = ["irr", "equity_multiple", "cash_on_cash_yr1", "cap_rate_on_cost"]


class SensitivityResponse(BaseModel):
    grids: dict[str, list[list[float | None]]]
    x_axis: SensitivityAxisRequest
    y_axis: SensitivityAxisRequest


# ---------------------------------------------------------------------------
# Comps
# ---------------------------------------------------------------------------


class CompResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    deal_id: UUID
    address: str
    city: str
    state: str
    property_type: str
    source: str
    source_url: str | None = None
    year_built: int | None = None
    unit_count: int | None = None
    square_feet: float | None = None
    sale_price: float | None = None
    price_per_unit: float | None = None
    price_per_sqft: float | None = None
    cap_rate: float | None = None
    rent_per_unit: float | None = None
    occupancy_rate: float | None = None
    noi: float | None = None
    expense_ratio: float | None = None
    opex_per_unit: float | None = None
    fetched_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Exploration
# ---------------------------------------------------------------------------


class CreateExplorationRequest(BaseModel):
    name: str = "Untitled Discovery"
    tags: list[str] = []


class ExplorationSessionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    deal_id: UUID | None
    name: str
    saved: bool
    tags: list[str] = []
    created_at: datetime


class UpdateExplorationRequest(BaseModel):
    name: str | None = None
    saved: bool | None = None
    tags: list[str] | None = None


# ---------------------------------------------------------------------------
# Chat Sessions
# ---------------------------------------------------------------------------


class CreateChatSessionRequest(BaseModel):
    title: str = "New Search"
    connectors: list[str] = []


class ChatSessionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    exploration_session_id: UUID
    title: str
    connectors: list[str]
    created_at: datetime
    updated_at: datetime


class UpdateChatSessionRequest(BaseModel):
    title: str | None = None


# ---------------------------------------------------------------------------
# Chat Messages
# ---------------------------------------------------------------------------


class SendMessageRequest(BaseModel):
    content: str
    connectors: list[str] = []


class ChatMessageResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    session_id: UUID
    role: str
    content: str
    tool_calls: list[dict] | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------


class CreateSnapshotRequest(BaseModel):
    name: str


class SnapshotResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    deal_id: UUID | None
    name: str
    session_data: dict
    created_at: datetime


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------


class CreateDatasetRequest(BaseModel):
    name: str
    deal_id: UUID | None = None
    properties: list[dict] = []


class UpdateDatasetRequest(BaseModel):
    name: str | None = None
    deal_id: UUID | None = None
    properties: list[dict] | None = None


class AddPropertiesRequest(BaseModel):
    properties: list[dict]


class DatasetResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    deal_id: UUID | None
    name: str
    properties: list[dict]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Connectors
# ---------------------------------------------------------------------------


class ConnectorResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    provider: str
    status: str
    file_count: int
    connected_at: datetime | None


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


class ReportTemplateResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    name: str
    file_format: str
    regions: list[dict]
    created_at: datetime


class CreateReportJobRequest(BaseModel):
    template_id: str
    name: str


class UpdateReportJobRequest(BaseModel):
    fills: dict


class ReportJobResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    template_id: str
    name: str
    fills: dict
    status: str
    created_at: datetime
