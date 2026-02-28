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


class UpdateDealRequest(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    property_type: PropertyType | None = None
    latitude: float | None = None
    longitude: float | None = None
    square_feet: float | None = None


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
    created_at: datetime
