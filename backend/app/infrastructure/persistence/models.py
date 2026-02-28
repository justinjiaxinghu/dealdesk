# backend/app/infrastructure/persistence/models.py
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import CHAR, JSON


class UUIDType(TypeDecorator):
    """Platform-agnostic UUID type. Stores as CHAR(36) on SQLite, native UUID on PostgreSQL."""

    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value)
        return value


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Deals
# ---------------------------------------------------------------------------


class DealModel(Base):
    __tablename__ = "deals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    property_type: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    square_feet: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    documents = relationship("DocumentModel", back_populates="deal", lazy="selectin")
    assumption_sets = relationship(
        "AssumptionSetModel", back_populates="deal", lazy="selectin"
    )
    exports = relationship("ExportModel", back_populates="deal", lazy="selectin")
    field_validations = relationship(
        "FieldValidationModel", back_populates="deal", lazy="selectin"
    )


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


class DocumentModel(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("deals.id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    processing_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    processing_steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    deal = relationship("DealModel", back_populates="documents")
    extracted_fields = relationship(
        "ExtractedFieldModel", back_populates="document", lazy="selectin"
    )
    market_tables = relationship(
        "MarketTableModel", back_populates="document", lazy="selectin"
    )


# ---------------------------------------------------------------------------
# Extracted Fields
# ---------------------------------------------------------------------------


class ExtractedFieldModel(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("documents.id"), nullable=False
    )
    field_key: Mapped[str] = mapped_column(String(255), nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    document = relationship("DocumentModel", back_populates="extracted_fields")


# ---------------------------------------------------------------------------
# Market Tables
# ---------------------------------------------------------------------------


class MarketTableModel(Base):
    __tablename__ = "market_tables"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("documents.id"), nullable=False
    )
    table_type: Mapped[str] = mapped_column(String(100), nullable=False)
    headers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    rows: Mapped[list | None] = mapped_column(JSON, nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    document = relationship("DocumentModel", back_populates="market_tables")


# ---------------------------------------------------------------------------
# Assumption Sets
# ---------------------------------------------------------------------------


class AssumptionSetModel(Base):
    __tablename__ = "assumption_sets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("deals.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    deal = relationship("DealModel", back_populates="assumption_sets")
    assumptions = relationship(
        "AssumptionModel", back_populates="assumption_set", lazy="selectin"
    )


# ---------------------------------------------------------------------------
# Assumptions
# ---------------------------------------------------------------------------


class AssumptionModel(Base):
    __tablename__ = "assumptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    set_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("assumption_sets.id"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    range_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    range_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="manual"
    )
    source_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    assumption_set = relationship("AssumptionSetModel", back_populates="assumptions")


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------


class ExportModel(Base):
    __tablename__ = "exports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("deals.id"), nullable=False
    )
    set_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("assumption_sets.id"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    export_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="xlsx"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    deal = relationship("DealModel", back_populates="exports")
    assumption_set = relationship("AssumptionSetModel")


# ---------------------------------------------------------------------------
# Field Validations
# ---------------------------------------------------------------------------


class FieldValidationModel(Base):
    __tablename__ = "field_validations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("deals.id"), nullable=False
    )
    field_key: Mapped[str] = mapped_column(String(255), nullable=False)
    om_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="insufficient_data")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sources: Mapped[list | None] = mapped_column(JSON, nullable=True)
    search_steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    deal = relationship("DealModel", back_populates="field_validations")
