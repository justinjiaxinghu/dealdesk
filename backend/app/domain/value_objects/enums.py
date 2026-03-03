# backend/app/domain/value_objects/enums.py
from enum import StrEnum


class PropertyType(StrEnum):
    MULTIFAMILY = "multifamily"
    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    OTHER = "other"



class ProcessingStatus(StrEnum):
    PENDING = "pending"
    UPLOADING = "uploading"
    EXTRACTING_TEXT = "extracting_text"
    EXTRACTING_TABLES = "extracting_tables"
    NORMALIZING = "normalizing"
    COMPLETE = "complete"
    FAILED = "failed"


class SourceType(StrEnum):
    OM = "om"
    AI = "ai"
    MANUAL = "manual"
    AI_EDITED = "ai_edited"


class DocumentType(StrEnum):
    OFFERING_MEMORANDUM = "offering_memorandum"
    RENT_ROLL = "rent_roll"
    FINANCIAL_STATEMENT = "financial_statement"
    OTHER = "other"


class ExportType(StrEnum):
    XLSX = "xlsx"


class ValidationStatus(StrEnum):
    WITHIN_RANGE = "within_range"
    ABOVE_MARKET = "above_market"
    BELOW_MARKET = "below_market"
    SUSPICIOUS = "suspicious"
    INSUFFICIENT_DATA = "insufficient_data"


class CompSource(StrEnum):
    RENTCAST = "rentcast"
    TAVILY = "tavily"
