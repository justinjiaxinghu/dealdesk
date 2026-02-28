# backend/app/infrastructure/persistence/mappers.py
"""Bidirectional entity <-> ORM model mapping functions."""

from __future__ import annotations

from app.domain.entities.assumption import Assumption, AssumptionSet
from app.domain.entities.deal import Deal
from app.domain.entities.document import Document
from app.domain.entities.export import Export
from app.domain.entities.extraction import ExtractedField, MarketTable
from app.domain.entities.field_validation import FieldValidation
from app.domain.value_objects.enums import (
    DealStatus,
    DocumentType,
    ExportType,
    ProcessingStatus,
    PropertyType,
    SourceType,
    ValidationStatus,
)
from app.domain.value_objects.types import ProcessingStep
from app.infrastructure.persistence.models import (
    AssumptionModel,
    AssumptionSetModel,
    DealModel,
    DocumentModel,
    ExportModel,
    ExtractedFieldModel,
    FieldValidationModel,
    MarketTableModel,
)


# ---------------------------------------------------------------------------
# Deal
# ---------------------------------------------------------------------------


def deal_to_entity(model: DealModel) -> Deal:
    return Deal(
        id=model.id,
        name=model.name,
        address=model.address,
        city=model.city,
        state=model.state,
        property_type=PropertyType(model.property_type),
        latitude=model.latitude,
        longitude=model.longitude,
        square_feet=model.square_feet,
        status=DealStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def deal_to_model(entity: Deal) -> DealModel:
    return DealModel(
        id=entity.id,
        name=entity.name,
        address=entity.address,
        city=entity.city,
        state=entity.state,
        property_type=entity.property_type.value,
        latitude=entity.latitude,
        longitude=entity.longitude,
        square_feet=entity.square_feet,
        status=entity.status.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------


def _steps_to_dicts(steps: list[ProcessingStep]) -> list[dict]:
    return [
        {"name": s.name, "status": s.status, "detail": s.detail} for s in steps
    ]


def _dicts_to_steps(data: list[dict] | None) -> list[ProcessingStep]:
    if not data:
        return []
    return [
        ProcessingStep(name=d["name"], status=d["status"], detail=d.get("detail", ""))
        for d in data
    ]


def document_to_entity(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        deal_id=model.deal_id,
        document_type=DocumentType(model.document_type),
        file_path=model.file_path,
        original_filename=model.original_filename,
        processing_status=ProcessingStatus(model.processing_status),
        processing_steps=_dicts_to_steps(model.processing_steps),
        error_message=model.error_message,
        page_count=model.page_count,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def document_to_model(entity: Document) -> DocumentModel:
    return DocumentModel(
        id=entity.id,
        deal_id=entity.deal_id,
        document_type=entity.document_type.value,
        file_path=entity.file_path,
        original_filename=entity.original_filename,
        processing_status=entity.processing_status.value,
        processing_steps=_steps_to_dicts(entity.processing_steps),
        error_message=entity.error_message,
        page_count=entity.page_count,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


# ---------------------------------------------------------------------------
# Extracted Field
# ---------------------------------------------------------------------------


def extracted_field_to_entity(model: ExtractedFieldModel) -> ExtractedField:
    return ExtractedField(
        id=model.id,
        document_id=model.document_id,
        field_key=model.field_key,
        value_text=model.value_text,
        value_number=model.value_number,
        unit=model.unit,
        confidence=model.confidence,
        source_page=model.source_page,
    )


def extracted_field_to_model(entity: ExtractedField) -> ExtractedFieldModel:
    return ExtractedFieldModel(
        id=entity.id,
        document_id=entity.document_id,
        field_key=entity.field_key,
        value_text=entity.value_text,
        value_number=entity.value_number,
        unit=entity.unit,
        confidence=entity.confidence,
        source_page=entity.source_page,
    )


# ---------------------------------------------------------------------------
# Market Table
# ---------------------------------------------------------------------------


def market_table_to_entity(model: MarketTableModel) -> MarketTable:
    return MarketTable(
        id=model.id,
        document_id=model.document_id,
        table_type=model.table_type,
        headers=model.headers or [],
        rows=model.rows or [],
        source_page=model.source_page,
        confidence=model.confidence,
    )


def market_table_to_model(entity: MarketTable) -> MarketTableModel:
    return MarketTableModel(
        id=entity.id,
        document_id=entity.document_id,
        table_type=entity.table_type,
        headers=entity.headers,
        rows=entity.rows,
        source_page=entity.source_page,
        confidence=entity.confidence,
    )


# ---------------------------------------------------------------------------
# Assumption Set
# ---------------------------------------------------------------------------


def assumption_set_to_entity(model: AssumptionSetModel) -> AssumptionSet:
    return AssumptionSet(
        id=model.id,
        deal_id=model.deal_id,
        name=model.name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def assumption_set_to_model(entity: AssumptionSet) -> AssumptionSetModel:
    return AssumptionSetModel(
        id=entity.id,
        deal_id=entity.deal_id,
        name=entity.name,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


# ---------------------------------------------------------------------------
# Assumption
# ---------------------------------------------------------------------------


def assumption_to_entity(model: AssumptionModel) -> Assumption:
    return Assumption(
        id=model.id,
        set_id=model.set_id,
        key=model.key,
        value_number=model.value_number,
        unit=model.unit,
        range_min=model.range_min,
        range_max=model.range_max,
        source_type=SourceType(model.source_type),
        source_ref=model.source_ref,
        notes=model.notes,
        updated_at=model.updated_at,
    )


def assumption_to_model(entity: Assumption) -> AssumptionModel:
    return AssumptionModel(
        id=entity.id,
        set_id=entity.set_id,
        key=entity.key,
        value_number=entity.value_number,
        unit=entity.unit,
        range_min=entity.range_min,
        range_max=entity.range_max,
        source_type=entity.source_type.value,
        source_ref=entity.source_ref,
        notes=entity.notes,
        updated_at=entity.updated_at,
    )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def export_to_entity(model: ExportModel) -> Export:
    return Export(
        id=model.id,
        deal_id=model.deal_id,
        set_id=model.set_id,
        file_path=model.file_path,
        export_type=ExportType(model.export_type),
        created_at=model.created_at,
    )


def export_to_model(entity: Export) -> ExportModel:
    return ExportModel(
        id=entity.id,
        deal_id=entity.deal_id,
        set_id=entity.set_id,
        file_path=entity.file_path,
        export_type=entity.export_type.value,
        created_at=entity.created_at,
    )


# ---------------------------------------------------------------------------
# Field Validation
# ---------------------------------------------------------------------------


def field_validation_to_entity(model: FieldValidationModel) -> FieldValidation:
    return FieldValidation(
        id=model.id,
        deal_id=model.deal_id,
        field_key=model.field_key,
        om_value=model.om_value,
        market_value=model.market_value,
        status=ValidationStatus(model.status),
        explanation=model.explanation,
        sources=model.sources or [],
        confidence=model.confidence,
        created_at=model.created_at,
    )


def field_validation_to_model(entity: FieldValidation) -> FieldValidationModel:
    return FieldValidationModel(
        id=entity.id,
        deal_id=entity.deal_id,
        field_key=entity.field_key,
        om_value=entity.om_value,
        market_value=entity.market_value,
        status=entity.status.value,
        explanation=entity.explanation,
        sources=entity.sources,
        confidence=entity.confidence,
        created_at=entity.created_at,
    )
