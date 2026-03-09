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


class HistoricalFinancialSource(StrEnum):
    EXTRACTED = "extracted"
    MANUAL = "manual"


class AssumptionGroup(StrEnum):
    MODEL_STRUCTURE = "model_structure"
    TRANSACTION = "transaction"
    OPERATING = "operating"
    FINANCING = "financing"
    RETURN_TARGETS = "return_targets"


class ForecastMethod(StrEnum):
    HISTORICAL = "historical"
    STEP_CHANGE = "step_change"
    GRADUAL_RAMP = "gradual_ramp"


class Cadence(StrEnum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"


class ProcessingStepStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ConnectorType(StrEnum):
    TAVILY = "tavily"
    COSTAR = "costar"
    COMPSTACK = "compstack"
    LOOPNET = "loopnet"
    REA_VISTA = "rea_vista"


class ConnectorProvider(StrEnum):
    ONEDRIVE = "onedrive"
    BOX = "box"
    GOOGLE_DRIVE = "google_drive"
    SHAREPOINT = "sharepoint"


class ConnectorStatus(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
