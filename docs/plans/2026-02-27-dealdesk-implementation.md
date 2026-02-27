# DealDesk MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an AI-assisted real estate deal evaluation platform that ingests OM PDFs, extracts data, generates benchmarks, computes a back-of-envelope model, and exports to Excel.

**Architecture:** Monorepo with clean layered backend (domain → services → infrastructure → api) using Python ABCs as interfaces. Frontend is Next.js with auto-generated TypeScript types from OpenAPI. All data source access goes through interfaces for swappability.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, pdfplumber, OpenAI GPT-4o, openpyxl, Next.js 14+, Tailwind CSS, shadcn/ui

**Prerequisites:**
- Conda environment: `conda create -n dealdesk python=3.12 && conda activate dealdesk`
- PostgreSQL running locally
- Node.js 20+ installed
- Working directory: `/Users/justinjhu/Documents/dealdesk`

---

## Task 1: Backend Project Scaffolding

**Files:**
- Modify: `backend/pyproject.toml` (already exists)
- Create: `backend/app/config.py`
- Create: `backend/app/main.py` (placeholder)

**Step 1: Verify pyproject.toml**

The file already exists. Verify it has correct dependencies:

Run: `cat backend/pyproject.toml`

**Step 2: Create config.py**

```python
# backend/app/config.py
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "DEALDESK_"}

    database_url: str = "postgresql+asyncpg://localhost:5432/dealdesk"
    database_url_sync: str = "postgresql://localhost:5432/dealdesk"
    file_storage_path: Path = Path("./storage")
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
```

**Step 3: Create placeholder main.py**

```python
# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(title="DealDesk API", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 4: Install dependencies and verify**

Run: `cd backend && pip install -e ".[dev]"`
Run: `python -c "from app.config import settings; print(settings.model_dump())"`
Expected: Settings dict printed without errors

**Step 5: Commit**

```bash
git add backend/
git commit -m "feat: backend scaffolding with config and health endpoint"
```

---

## Task 2: Domain Value Objects

**Files:**
- Create: `backend/app/domain/value_objects/enums.py`
- Create: `backend/app/domain/value_objects/types.py`
- Modify: `backend/app/domain/value_objects/__init__.py`

**Step 1: Create enums**

```python
# backend/app/domain/value_objects/enums.py
from enum import StrEnum


class PropertyType(StrEnum):
    MULTIFAMILY = "multifamily"
    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    OTHER = "other"


class DealStatus(StrEnum):
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    EXPORTED = "exported"


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
```

**Step 2: Create service I/O value types**

```python
# backend/app/domain/value_objects/types.py
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class ExtractedTable:
    page_number: int
    headers: list[str]
    rows: list[list[str]]
    confidence: float = 0.0


@dataclass(frozen=True)
class RawField:
    key: str
    value: str
    source_page: int


@dataclass(frozen=True)
class NormalizedField:
    key: str
    value_text: str | None
    value_number: float | None
    unit: str | None
    confidence: float


@dataclass(frozen=True)
class Location:
    address: str
    city: str
    state: str
    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True)
class BenchmarkSuggestion:
    key: str
    value: float
    unit: str
    range_min: float
    range_max: float
    source: str
    confidence: float


@dataclass(frozen=True)
class ProcessingStep:
    name: str
    status: str  # "pending", "in_progress", "complete", "failed"
    detail: str = ""


@dataclass
class DealFilters:
    property_type: str | None = None
    status: str | None = None
    city: str | None = None
```

**Step 3: Update __init__.py**

```python
# backend/app/domain/value_objects/__init__.py
from app.domain.value_objects.enums import (
    DealStatus,
    DocumentType,
    ExportType,
    ProcessingStatus,
    PropertyType,
    SourceType,
)
from app.domain.value_objects.types import (
    BenchmarkSuggestion,
    DealFilters,
    ExtractedTable,
    Location,
    NormalizedField,
    PageText,
    ProcessingStep,
    RawField,
)

__all__ = [
    "PropertyType",
    "DealStatus",
    "ProcessingStatus",
    "SourceType",
    "DocumentType",
    "ExportType",
    "PageText",
    "ExtractedTable",
    "RawField",
    "NormalizedField",
    "Location",
    "BenchmarkSuggestion",
    "ProcessingStep",
    "DealFilters",
]
```

**Step 4: Verify imports**

Run: `cd backend && python -c "from app.domain.value_objects import PropertyType, PageText; print(PropertyType.MULTIFAMILY, PageText(1, 'test'))"`
Expected: `multifamily PageText(page_number=1, text='test')`

**Step 5: Commit**

```bash
git add backend/app/domain/value_objects/
git commit -m "feat: domain value objects - enums and service I/O types"
```

---

## Task 3: Domain Entities

**Files:**
- Create: `backend/app/domain/entities/deal.py`
- Create: `backend/app/domain/entities/document.py`
- Create: `backend/app/domain/entities/extraction.py`
- Create: `backend/app/domain/entities/assumption.py`
- Create: `backend/app/domain/entities/model_result.py`
- Create: `backend/app/domain/entities/export.py`
- Modify: `backend/app/domain/entities/__init__.py`

**Step 1: Create Deal entity**

```python
# backend/app/domain/entities/deal.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import DealStatus, PropertyType


@dataclass
class Deal:
    name: str
    address: str
    city: str
    state: str
    property_type: PropertyType
    id: UUID = field(default_factory=uuid4)
    latitude: float | None = None
    longitude: float | None = None
    square_feet: float | None = None
    status: DealStatus = DealStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
```

**Step 2: Create Document entity**

```python
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
```

**Step 3: Create Extraction entities**

```python
# backend/app/domain/entities/extraction.py
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class ExtractedField:
    document_id: UUID
    field_key: str
    id: UUID = field(default_factory=uuid4)
    value_text: str | None = None
    value_number: float | None = None
    unit: str | None = None
    confidence: float = 0.0
    source_page: int | None = None


@dataclass
class MarketTable:
    document_id: UUID
    table_type: str
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    source_page: int | None = None
    confidence: float = 0.0
```

**Step 4: Create Assumption entities**

```python
# backend/app/domain/entities/assumption.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import SourceType


@dataclass
class AssumptionSet:
    deal_id: UUID
    name: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Assumption:
    set_id: UUID
    key: str
    id: UUID = field(default_factory=uuid4)
    value_number: float | None = None
    unit: str | None = None
    range_min: float | None = None
    range_max: float | None = None
    source_type: SourceType = SourceType.MANUAL
    source_ref: str | None = None
    notes: str | None = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
```

**Step 5: Create ModelResult entity**

```python
# backend/app/domain/entities/model_result.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ModelResult:
    set_id: UUID
    noi_stabilized: float
    exit_value: float
    total_cost: float
    profit: float
    profit_margin_pct: float
    id: UUID = field(default_factory=uuid4)
    computed_at: datetime = field(default_factory=datetime.utcnow)
```

**Step 6: Create Export entity**

```python
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
```

**Step 7: Update __init__.py**

```python
# backend/app/domain/entities/__init__.py
from app.domain.entities.assumption import Assumption, AssumptionSet
from app.domain.entities.deal import Deal
from app.domain.entities.document import Document
from app.domain.entities.export import Export
from app.domain.entities.extraction import ExtractedField, MarketTable
from app.domain.entities.model_result import ModelResult

__all__ = [
    "Deal",
    "Document",
    "ExtractedField",
    "MarketTable",
    "AssumptionSet",
    "Assumption",
    "ModelResult",
    "Export",
]
```

**Step 8: Verify imports**

Run: `cd backend && python -c "from app.domain.entities import Deal, Document, Assumption; print('OK')"`
Expected: `OK`

**Step 9: Commit**

```bash
git add backend/app/domain/entities/
git commit -m "feat: domain entities - Deal, Document, Extraction, Assumption, ModelResult, Export"
```

---

## Task 4: Domain Interfaces (ABCs)

**Files:**
- Create: `backend/app/domain/interfaces/repositories.py`
- Create: `backend/app/domain/interfaces/providers.py`
- Modify: `backend/app/domain/interfaces/__init__.py`

**Step 1: Create repository interfaces**

```python
# backend/app/domain/interfaces/repositories.py
from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import (
    Assumption,
    AssumptionSet,
    Deal,
    Document,
    Export,
    ExtractedField,
    MarketTable,
    ModelResult,
)
from app.domain.value_objects import DealFilters, ProcessingStep


class DealRepository(ABC):
    @abstractmethod
    async def create(self, deal: Deal) -> Deal: ...

    @abstractmethod
    async def get_by_id(self, deal_id: UUID) -> Deal | None: ...

    @abstractmethod
    async def list(self, filters: DealFilters | None = None) -> list[Deal]: ...

    @abstractmethod
    async def update(self, deal: Deal) -> Deal: ...


class DocumentRepository(ABC):
    @abstractmethod
    async def create(self, document: Document) -> Document: ...

    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Document | None: ...

    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[Document]: ...

    @abstractmethod
    async def update(self, document: Document) -> Document: ...

    @abstractmethod
    async def update_processing_step(
        self, document_id: UUID, step: ProcessingStep
    ) -> Document: ...


class ExtractedFieldRepository(ABC):
    @abstractmethod
    async def bulk_create(self, fields: list[ExtractedField]) -> list[ExtractedField]: ...

    @abstractmethod
    async def get_by_document_id(self, document_id: UUID) -> list[ExtractedField]: ...


class MarketTableRepository(ABC):
    @abstractmethod
    async def bulk_create(self, tables: list[MarketTable]) -> list[MarketTable]: ...

    @abstractmethod
    async def get_by_document_id(self, document_id: UUID) -> list[MarketTable]: ...


class AssumptionSetRepository(ABC):
    @abstractmethod
    async def create(self, assumption_set: AssumptionSet) -> AssumptionSet: ...

    @abstractmethod
    async def get_by_id(self, set_id: UUID) -> AssumptionSet | None: ...

    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[AssumptionSet]: ...


class AssumptionRepository(ABC):
    @abstractmethod
    async def bulk_upsert(self, assumptions: list[Assumption]) -> list[Assumption]: ...

    @abstractmethod
    async def get_by_set_id(self, set_id: UUID) -> list[Assumption]: ...

    @abstractmethod
    async def update(self, assumption: Assumption) -> Assumption: ...


class ModelResultRepository(ABC):
    @abstractmethod
    async def create(self, result: ModelResult) -> ModelResult: ...

    @abstractmethod
    async def get_by_set_id(self, set_id: UUID) -> ModelResult | None: ...


class ExportRepository(ABC):
    @abstractmethod
    async def create(self, export: Export) -> Export: ...

    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[Export]: ...
```

**Step 2: Create provider interfaces**

```python
# backend/app/domain/interfaces/providers.py
from abc import ABC, abstractmethod
from pathlib import Path

from app.domain.entities import Assumption, Deal, ModelResult
from app.domain.value_objects import (
    BenchmarkSuggestion,
    ExtractedTable,
    Location,
    NormalizedField,
    PageText,
    PropertyType,
    RawField,
)


class DocumentProcessor(ABC):
    @abstractmethod
    async def extract_text(self, file_path: Path) -> list[PageText]: ...

    @abstractmethod
    async def extract_tables(self, file_path: Path) -> list[ExtractedTable]: ...


class LLMProvider(ABC):
    @abstractmethod
    async def generate_benchmarks(
        self, location: Location, property_type: PropertyType
    ) -> list[BenchmarkSuggestion]: ...

    @abstractmethod
    async def normalize_extracted_fields(
        self, raw_fields: list[RawField]
    ) -> list[NormalizedField]: ...


class FileStorage(ABC):
    @abstractmethod
    async def store(self, data: bytes, path: str) -> str: ...

    @abstractmethod
    async def retrieve(self, path: str) -> Path: ...

    @abstractmethod
    async def delete(self, path: str) -> None: ...


class ExcelExporter(ABC):
    @abstractmethod
    async def export(
        self, deal: Deal, assumptions: list[Assumption], results: ModelResult
    ) -> bytes: ...
```

**Step 3: Update __init__.py**

```python
# backend/app/domain/interfaces/__init__.py
from app.domain.interfaces.providers import (
    DocumentProcessor,
    ExcelExporter,
    FileStorage,
    LLMProvider,
)
from app.domain.interfaces.repositories import (
    AssumptionRepository,
    AssumptionSetRepository,
    DealRepository,
    DocumentRepository,
    ExportRepository,
    ExtractedFieldRepository,
    MarketTableRepository,
    ModelResultRepository,
)

__all__ = [
    "DealRepository",
    "DocumentRepository",
    "ExtractedFieldRepository",
    "MarketTableRepository",
    "AssumptionSetRepository",
    "AssumptionRepository",
    "ModelResultRepository",
    "ExportRepository",
    "DocumentProcessor",
    "LLMProvider",
    "FileStorage",
    "ExcelExporter",
]
```

**Step 4: Verify imports**

Run: `cd backend && python -c "from app.domain.interfaces import DealRepository, DocumentProcessor, FileStorage; print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add backend/app/domain/
git commit -m "feat: domain interfaces - repository ABCs and provider ABCs"
```

---

## Task 5: Model Engine + Tests (TDD)

**Files:**
- Create: `backend/tests/test_model_engine.py`
- Create: `backend/app/domain/model_engine.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_model_engine.py
import pytest

from app.domain.model_engine import ModelEngine, ModelInput, ModelOutput


class TestModelEngine:
    def test_basic_computation(self):
        inp = ModelInput(
            rent_psf_yr=30.0,
            square_feet=50000.0,
            vacancy_rate=0.05,
            opex_ratio=0.35,
            cap_rate=0.065,
            purchase_price=15_000_000.0,
            closing_costs=450_000.0,
            capex_budget=500_000.0,
        )
        result = ModelEngine.compute(inp)

        # Revenue = 30 * 50000 = 1,500,000
        # Effective revenue = 1,500,000 * (1 - 0.05) = 1,425,000
        # OpEx = 0.35 * 1,425,000 = 498,750
        # NOI = 1,425,000 - 498,750 = 926,250
        assert result.gross_revenue == pytest.approx(1_500_000.0)
        assert result.effective_revenue == pytest.approx(1_425_000.0)
        assert result.operating_expenses == pytest.approx(498_750.0)
        assert result.noi_stabilized == pytest.approx(926_250.0)

        # Exit value = 926,250 / 0.065 = 14,250,000
        assert result.exit_value == pytest.approx(14_250_000.0)

        # Total cost = 15,000,000 + 450,000 + 500,000 = 15,950,000
        assert result.total_cost == pytest.approx(15_950_000.0)

        # Profit = 14,250,000 - 15,950,000 = -1,700,000
        assert result.profit == pytest.approx(-1_700_000.0)

        # Margin = -1,700,000 / 15,950,000 = -0.10658...
        assert result.profit_margin_pct == pytest.approx(-10.658, rel=0.01)

    def test_zero_vacancy(self):
        inp = ModelInput(
            rent_psf_yr=25.0,
            square_feet=10000.0,
            vacancy_rate=0.0,
            opex_ratio=0.30,
            cap_rate=0.07,
            purchase_price=3_000_000.0,
            closing_costs=90_000.0,
            capex_budget=100_000.0,
        )
        result = ModelEngine.compute(inp)
        assert result.gross_revenue == pytest.approx(250_000.0)
        assert result.effective_revenue == pytest.approx(250_000.0)
        assert result.noi_stabilized == pytest.approx(175_000.0)

    def test_missing_required_fields_raises(self):
        inp = ModelInput(
            rent_psf_yr=None,
            square_feet=50000.0,
            vacancy_rate=0.05,
            opex_ratio=0.35,
            cap_rate=0.065,
            purchase_price=15_000_000.0,
            closing_costs=0.0,
            capex_budget=0.0,
        )
        with pytest.raises(ValueError, match="rent_psf_yr"):
            ModelEngine.compute(inp)

    def test_zero_cap_rate_raises(self):
        inp = ModelInput(
            rent_psf_yr=30.0,
            square_feet=50000.0,
            vacancy_rate=0.05,
            opex_ratio=0.35,
            cap_rate=0.0,
            purchase_price=15_000_000.0,
            closing_costs=0.0,
            capex_budget=0.0,
        )
        with pytest.raises(ValueError, match="cap_rate"):
            ModelEngine.compute(inp)
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_model_engine.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.domain.model_engine'`

**Step 3: Implement ModelEngine**

```python
# backend/app/domain/model_engine.py
from dataclasses import dataclass


@dataclass
class ModelInput:
    rent_psf_yr: float | None
    square_feet: float | None
    vacancy_rate: float | None
    opex_ratio: float | None
    cap_rate: float | None
    purchase_price: float | None
    closing_costs: float = 0.0
    capex_budget: float = 0.0


@dataclass(frozen=True)
class ModelOutput:
    gross_revenue: float
    effective_revenue: float
    operating_expenses: float
    noi_stabilized: float
    exit_value: float
    total_cost: float
    profit: float
    profit_margin_pct: float


class ModelEngine:
    REQUIRED_FIELDS = ["rent_psf_yr", "square_feet", "vacancy_rate", "opex_ratio", "cap_rate", "purchase_price"]

    @staticmethod
    def compute(inp: ModelInput) -> ModelOutput:
        missing = [f for f in ModelEngine.REQUIRED_FIELDS if getattr(inp, f) is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        if inp.cap_rate == 0.0:
            raise ValueError("cap_rate must be non-zero")

        gross_revenue = inp.rent_psf_yr * inp.square_feet
        effective_revenue = gross_revenue * (1 - inp.vacancy_rate)
        operating_expenses = inp.opex_ratio * effective_revenue
        noi = effective_revenue - operating_expenses

        exit_value = noi / inp.cap_rate
        total_cost = inp.purchase_price + inp.closing_costs + inp.capex_budget
        profit = exit_value - total_cost
        margin_pct = (profit / total_cost) * 100 if total_cost != 0 else 0.0

        return ModelOutput(
            gross_revenue=gross_revenue,
            effective_revenue=effective_revenue,
            operating_expenses=operating_expenses,
            noi_stabilized=noi,
            exit_value=exit_value,
            total_cost=total_cost,
            profit=profit,
            profit_margin_pct=margin_pct,
        )
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_model_engine.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add backend/app/domain/model_engine.py backend/tests/test_model_engine.py
git commit -m "feat: model engine with TDD - computes NOI, exit value, profit, margin"
```

---

## Task 6: SQLAlchemy Models + Database Setup

**Files:**
- Create: `backend/app/infrastructure/persistence/database.py`
- Create: `backend/app/infrastructure/persistence/models.py`

**Step 1: Create database session management**

```python
# backend/app/infrastructure/persistence/database.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
```

**Step 2: Create SQLAlchemy ORM models**

```python
# backend/app/infrastructure/persistence/models.py
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class DealModel(Base):
    __tablename__ = "deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    property_type = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    square_feet = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("DocumentModel", back_populates="deal")
    assumption_sets = relationship("AssumptionSetModel", back_populates="deal")
    exports = relationship("ExportModel", back_populates="deal")


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False)
    document_type = Column(String(50), nullable=False)
    file_path = Column(String(1000), nullable=False)
    original_filename = Column(String(500), nullable=False)
    processing_status = Column(String(50), nullable=False, default="pending")
    processing_steps = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    deal = relationship("DealModel", back_populates="documents")
    extracted_fields = relationship("ExtractedFieldModel", back_populates="document")
    market_tables = relationship("MarketTableModel", back_populates="document")


class ExtractedFieldModel(Base):
    __tablename__ = "extracted_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    field_key = Column(String(255), nullable=False)
    value_text = Column(Text, nullable=True)
    value_number = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    confidence = Column(Float, default=0.0)
    source_page = Column(Integer, nullable=True)

    document = relationship("DocumentModel", back_populates="extracted_fields")


class MarketTableModel(Base):
    __tablename__ = "market_tables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    table_type = Column(String(100), nullable=False)
    headers = Column(JSON, default=list)
    rows = Column(JSON, default=list)
    source_page = Column(Integer, nullable=True)
    confidence = Column(Float, default=0.0)

    document = relationship("DocumentModel", back_populates="market_tables")


class AssumptionSetModel(Base):
    __tablename__ = "assumption_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    deal = relationship("DealModel", back_populates="assumption_sets")
    assumptions = relationship("AssumptionModel", back_populates="assumption_set")
    model_results = relationship("ModelResultModel", back_populates="assumption_set")


class AssumptionModel(Base):
    __tablename__ = "assumptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    set_id = Column(UUID(as_uuid=True), ForeignKey("assumption_sets.id"), nullable=False)
    key = Column(String(100), nullable=False)
    value_number = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    range_min = Column(Float, nullable=True)
    range_max = Column(Float, nullable=True)
    source_type = Column(String(50), nullable=False, default="manual")
    source_ref = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assumption_set = relationship("AssumptionSetModel", back_populates="assumptions")


class ModelResultModel(Base):
    __tablename__ = "model_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    set_id = Column(UUID(as_uuid=True), ForeignKey("assumption_sets.id"), nullable=False)
    noi_stabilized = Column(Float, nullable=False)
    exit_value = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)
    profit_margin_pct = Column(Float, nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow)

    assumption_set = relationship("AssumptionSetModel", back_populates="model_results")


class ExportModel(Base):
    __tablename__ = "exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False)
    set_id = Column(UUID(as_uuid=True), ForeignKey("assumption_sets.id"), nullable=False)
    file_path = Column(String(1000), nullable=False)
    export_type = Column(String(50), nullable=False, default="xlsx")
    created_at = Column(DateTime, default=datetime.utcnow)

    deal = relationship("DealModel", back_populates="exports")
```

**Step 3: Verify imports**

Run: `cd backend && python -c "from app.infrastructure.persistence.models import Base, DealModel; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add backend/app/infrastructure/persistence/
git commit -m "feat: SQLAlchemy ORM models and async database session"
```

---

## Task 7: Alembic Setup + Initial Migration

**Step 1: Initialize Alembic**

Run: `cd backend && python -m alembic init alembic`

**Step 2: Edit `alembic/env.py`**

Replace the contents of `backend/alembic/env.py` with:

```python
# backend/alembic/env.py
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.infrastructure.persistence.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 3: Create the database and generate migration**

Run: `createdb dealdesk` (skip if already exists)
Run: `cd backend && python -m alembic revision --autogenerate -m "initial schema"`

**Step 4: Run migration**

Run: `cd backend && python -m alembic upgrade head`
Expected: Tables created in dealdesk database

**Step 5: Commit**

```bash
git add backend/alembic/ backend/alembic.ini
git commit -m "feat: Alembic setup with initial database migration"
```

---

## Task 8: Repository Implementations

**Files:**
- Create: `backend/app/infrastructure/persistence/mappers.py`
- Create: `backend/app/infrastructure/persistence/deal_repo.py`
- Create: `backend/app/infrastructure/persistence/document_repo.py`
- Create: `backend/app/infrastructure/persistence/extraction_repo.py`
- Create: `backend/app/infrastructure/persistence/assumption_repo.py`
- Create: `backend/app/infrastructure/persistence/model_result_repo.py`
- Create: `backend/app/infrastructure/persistence/export_repo.py`

**Step 1: Create entity ↔ ORM mappers**

```python
# backend/app/infrastructure/persistence/mappers.py
from app.domain.entities import (
    Assumption,
    AssumptionSet,
    Deal,
    Document,
    Export,
    ExtractedField,
    MarketTable,
    ModelResult,
)
from app.domain.value_objects import ProcessingStep
from app.domain.value_objects.enums import (
    DealStatus,
    DocumentType,
    ExportType,
    ProcessingStatus,
    PropertyType,
    SourceType,
)
from app.infrastructure.persistence.models import (
    AssumptionModel,
    AssumptionSetModel,
    DealModel,
    DocumentModel,
    ExportModel,
    ExtractedFieldModel,
    MarketTableModel,
    ModelResultModel,
)


def deal_to_entity(m: DealModel) -> Deal:
    return Deal(
        id=m.id, name=m.name, address=m.address, city=m.city, state=m.state,
        property_type=PropertyType(m.property_type), latitude=m.latitude,
        longitude=m.longitude, square_feet=m.square_feet,
        status=DealStatus(m.status), created_at=m.created_at, updated_at=m.updated_at,
    )


def deal_to_model(e: Deal) -> DealModel:
    return DealModel(
        id=e.id, name=e.name, address=e.address, city=e.city, state=e.state,
        property_type=e.property_type.value, latitude=e.latitude,
        longitude=e.longitude, square_feet=e.square_feet,
        status=e.status.value, created_at=e.created_at, updated_at=e.updated_at,
    )


def document_to_entity(m: DocumentModel) -> Document:
    steps = [ProcessingStep(**s) for s in (m.processing_steps or [])]
    return Document(
        id=m.id, deal_id=m.deal_id, document_type=DocumentType(m.document_type),
        file_path=m.file_path, original_filename=m.original_filename,
        processing_status=ProcessingStatus(m.processing_status),
        processing_steps=steps, error_message=m.error_message,
        page_count=m.page_count, created_at=m.created_at, updated_at=m.updated_at,
    )


def document_to_model(e: Document) -> DocumentModel:
    steps = [{"name": s.name, "status": s.status, "detail": s.detail} for s in e.processing_steps]
    return DocumentModel(
        id=e.id, deal_id=e.deal_id, document_type=e.document_type.value,
        file_path=e.file_path, original_filename=e.original_filename,
        processing_status=e.processing_status.value, processing_steps=steps,
        error_message=e.error_message, page_count=e.page_count,
        created_at=e.created_at, updated_at=e.updated_at,
    )


def extracted_field_to_entity(m: ExtractedFieldModel) -> ExtractedField:
    return ExtractedField(
        id=m.id, document_id=m.document_id, field_key=m.field_key,
        value_text=m.value_text, value_number=m.value_number, unit=m.unit,
        confidence=m.confidence, source_page=m.source_page,
    )


def extracted_field_to_model(e: ExtractedField) -> ExtractedFieldModel:
    return ExtractedFieldModel(
        id=e.id, document_id=e.document_id, field_key=e.field_key,
        value_text=e.value_text, value_number=e.value_number, unit=e.unit,
        confidence=e.confidence, source_page=e.source_page,
    )


def market_table_to_entity(m: MarketTableModel) -> MarketTable:
    return MarketTable(
        id=m.id, document_id=m.document_id, table_type=m.table_type,
        headers=m.headers or [], rows=m.rows or [],
        source_page=m.source_page, confidence=m.confidence,
    )


def market_table_to_model(e: MarketTable) -> MarketTableModel:
    return MarketTableModel(
        id=e.id, document_id=e.document_id, table_type=e.table_type,
        headers=e.headers, rows=e.rows, source_page=e.source_page,
        confidence=e.confidence,
    )


def assumption_set_to_entity(m: AssumptionSetModel) -> AssumptionSet:
    return AssumptionSet(
        id=m.id, deal_id=m.deal_id, name=m.name,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def assumption_to_entity(m: AssumptionModel) -> Assumption:
    return Assumption(
        id=m.id, set_id=m.set_id, key=m.key, value_number=m.value_number,
        unit=m.unit, range_min=m.range_min, range_max=m.range_max,
        source_type=SourceType(m.source_type), source_ref=m.source_ref,
        notes=m.notes, updated_at=m.updated_at,
    )


def model_result_to_entity(m: ModelResultModel) -> ModelResult:
    return ModelResult(
        id=m.id, set_id=m.set_id, noi_stabilized=m.noi_stabilized,
        exit_value=m.exit_value, total_cost=m.total_cost, profit=m.profit,
        profit_margin_pct=m.profit_margin_pct, computed_at=m.computed_at,
    )


def export_to_entity(m: ExportModel) -> Export:
    return Export(
        id=m.id, deal_id=m.deal_id, set_id=m.set_id, file_path=m.file_path,
        export_type=ExportType(m.export_type), created_at=m.created_at,
    )
```

**Step 2: Create DealRepo**

```python
# backend/app/infrastructure/persistence/deal_repo.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Deal
from app.domain.interfaces import DealRepository
from app.domain.value_objects import DealFilters
from app.infrastructure.persistence.mappers import deal_to_entity, deal_to_model
from app.infrastructure.persistence.models import DealModel


class SqlAlchemyDealRepository(DealRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, deal: Deal) -> Deal:
        model = deal_to_model(deal)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return deal_to_entity(model)

    async def get_by_id(self, deal_id: UUID) -> Deal | None:
        result = await self._session.get(DealModel, deal_id)
        return deal_to_entity(result) if result else None

    async def list(self, filters: DealFilters | None = None) -> list[Deal]:
        stmt = select(DealModel).order_by(DealModel.created_at.desc())
        if filters:
            if filters.property_type:
                stmt = stmt.where(DealModel.property_type == filters.property_type)
            if filters.status:
                stmt = stmt.where(DealModel.status == filters.status)
            if filters.city:
                stmt = stmt.where(DealModel.city.ilike(f"%{filters.city}%"))
        result = await self._session.execute(stmt)
        return [deal_to_entity(m) for m in result.scalars()]

    async def update(self, deal: Deal) -> Deal:
        model = await self._session.get(DealModel, deal.id)
        if not model:
            raise ValueError(f"Deal {deal.id} not found")
        for field in ["name", "address", "city", "state", "latitude", "longitude", "square_feet"]:
            setattr(model, field, getattr(deal, field))
        model.property_type = deal.property_type.value
        model.status = deal.status.value
        await self._session.flush()
        await self._session.refresh(model)
        return deal_to_entity(model)
```

**Step 3: Create DocumentRepo**

```python
# backend/app/infrastructure/persistence/document_repo.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Document
from app.domain.interfaces import DocumentRepository
from app.domain.value_objects import ProcessingStep
from app.infrastructure.persistence.mappers import document_to_entity, document_to_model
from app.infrastructure.persistence.models import DocumentModel


class SqlAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, document: Document) -> Document:
        model = document_to_model(document)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return document_to_entity(model)

    async def get_by_id(self, document_id: UUID) -> Document | None:
        result = await self._session.get(DocumentModel, document_id)
        return document_to_entity(result) if result else None

    async def get_by_deal_id(self, deal_id: UUID) -> list[Document]:
        stmt = select(DocumentModel).where(DocumentModel.deal_id == deal_id)
        result = await self._session.execute(stmt)
        return [document_to_entity(m) for m in result.scalars()]

    async def update(self, document: Document) -> Document:
        model = await self._session.get(DocumentModel, document.id)
        if not model:
            raise ValueError(f"Document {document.id} not found")
        model.processing_status = document.processing_status.value
        model.processing_steps = [
            {"name": s.name, "status": s.status, "detail": s.detail}
            for s in document.processing_steps
        ]
        model.error_message = document.error_message
        model.page_count = document.page_count
        await self._session.flush()
        await self._session.refresh(model)
        return document_to_entity(model)

    async def update_processing_step(
        self, document_id: UUID, step: ProcessingStep
    ) -> Document:
        model = await self._session.get(DocumentModel, document_id)
        if not model:
            raise ValueError(f"Document {document_id} not found")
        steps = list(model.processing_steps or [])
        existing_idx = next((i for i, s in enumerate(steps) if s["name"] == step.name), None)
        step_dict = {"name": step.name, "status": step.status, "detail": step.detail}
        if existing_idx is not None:
            steps[existing_idx] = step_dict
        else:
            steps.append(step_dict)
        model.processing_steps = steps
        model.processing_status = step.status if step.status == "failed" else model.processing_status
        await self._session.flush()
        await self._session.refresh(model)
        return document_to_entity(model)
```

**Step 4: Create ExtractionRepo (fields + tables)**

```python
# backend/app/infrastructure/persistence/extraction_repo.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import ExtractedField, MarketTable
from app.domain.interfaces import ExtractedFieldRepository, MarketTableRepository
from app.infrastructure.persistence.mappers import (
    extracted_field_to_entity,
    extracted_field_to_model,
    market_table_to_entity,
    market_table_to_model,
)
from app.infrastructure.persistence.models import ExtractedFieldModel, MarketTableModel


class SqlAlchemyExtractedFieldRepository(ExtractedFieldRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def bulk_create(self, fields: list[ExtractedField]) -> list[ExtractedField]:
        models = [extracted_field_to_model(f) for f in fields]
        self._session.add_all(models)
        await self._session.flush()
        for m in models:
            await self._session.refresh(m)
        return [extracted_field_to_entity(m) for m in models]

    async def get_by_document_id(self, document_id: UUID) -> list[ExtractedField]:
        stmt = select(ExtractedFieldModel).where(ExtractedFieldModel.document_id == document_id)
        result = await self._session.execute(stmt)
        return [extracted_field_to_entity(m) for m in result.scalars()]


class SqlAlchemyMarketTableRepository(MarketTableRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def bulk_create(self, tables: list[MarketTable]) -> list[MarketTable]:
        models = [market_table_to_model(t) for t in tables]
        self._session.add_all(models)
        await self._session.flush()
        for m in models:
            await self._session.refresh(m)
        return [market_table_to_entity(m) for m in models]

    async def get_by_document_id(self, document_id: UUID) -> list[MarketTable]:
        stmt = select(MarketTableModel).where(MarketTableModel.document_id == document_id)
        result = await self._session.execute(stmt)
        return [market_table_to_entity(m) for m in result.scalars()]
```

**Step 5: Create AssumptionRepo**

```python
# backend/app/infrastructure/persistence/assumption_repo.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Assumption, AssumptionSet
from app.domain.interfaces import AssumptionRepository, AssumptionSetRepository
from app.infrastructure.persistence.mappers import assumption_set_to_entity, assumption_to_entity
from app.infrastructure.persistence.models import AssumptionModel, AssumptionSetModel


class SqlAlchemyAssumptionSetRepository(AssumptionSetRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, assumption_set: AssumptionSet) -> AssumptionSet:
        model = AssumptionSetModel(
            id=assumption_set.id, deal_id=assumption_set.deal_id, name=assumption_set.name,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return assumption_set_to_entity(model)

    async def get_by_id(self, set_id: UUID) -> AssumptionSet | None:
        result = await self._session.get(AssumptionSetModel, set_id)
        return assumption_set_to_entity(result) if result else None

    async def get_by_deal_id(self, deal_id: UUID) -> list[AssumptionSet]:
        stmt = select(AssumptionSetModel).where(AssumptionSetModel.deal_id == deal_id)
        result = await self._session.execute(stmt)
        return [assumption_set_to_entity(m) for m in result.scalars()]


class SqlAlchemyAssumptionRepository(AssumptionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def bulk_upsert(self, assumptions: list[Assumption]) -> list[Assumption]:
        results = []
        for a in assumptions:
            existing = await self._session.execute(
                select(AssumptionModel).where(
                    AssumptionModel.set_id == a.set_id, AssumptionModel.key == a.key
                )
            )
            model = existing.scalar_one_or_none()
            if model:
                model.value_number = a.value_number
                model.unit = a.unit
                model.range_min = a.range_min
                model.range_max = a.range_max
                model.source_type = a.source_type.value
                model.source_ref = a.source_ref
                model.notes = a.notes
            else:
                model = AssumptionModel(
                    id=a.id, set_id=a.set_id, key=a.key, value_number=a.value_number,
                    unit=a.unit, range_min=a.range_min, range_max=a.range_max,
                    source_type=a.source_type.value, source_ref=a.source_ref, notes=a.notes,
                )
                self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
            results.append(assumption_to_entity(model))
        return results

    async def get_by_set_id(self, set_id: UUID) -> list[Assumption]:
        stmt = select(AssumptionModel).where(AssumptionModel.set_id == set_id)
        result = await self._session.execute(stmt)
        return [assumption_to_entity(m) for m in result.scalars()]

    async def update(self, assumption: Assumption) -> Assumption:
        model = await self._session.get(AssumptionModel, assumption.id)
        if not model:
            raise ValueError(f"Assumption {assumption.id} not found")
        model.value_number = assumption.value_number
        model.unit = assumption.unit
        model.source_type = assumption.source_type.value
        model.notes = assumption.notes
        await self._session.flush()
        await self._session.refresh(model)
        return assumption_to_entity(model)
```

**Step 6: Create ModelResultRepo + ExportRepo**

```python
# backend/app/infrastructure/persistence/model_result_repo.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import ModelResult
from app.domain.interfaces import ModelResultRepository
from app.infrastructure.persistence.mappers import model_result_to_entity
from app.infrastructure.persistence.models import ModelResultModel


class SqlAlchemyModelResultRepository(ModelResultRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, result: ModelResult) -> ModelResult:
        model = ModelResultModel(
            id=result.id, set_id=result.set_id, noi_stabilized=result.noi_stabilized,
            exit_value=result.exit_value, total_cost=result.total_cost,
            profit=result.profit, profit_margin_pct=result.profit_margin_pct,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model_result_to_entity(model)

    async def get_by_set_id(self, set_id: UUID) -> ModelResult | None:
        stmt = select(ModelResultModel).where(ModelResultModel.set_id == set_id).order_by(ModelResultModel.computed_at.desc())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model_result_to_entity(model) if model else None
```

```python
# backend/app/infrastructure/persistence/export_repo.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Export
from app.domain.interfaces import ExportRepository
from app.infrastructure.persistence.mappers import export_to_entity
from app.infrastructure.persistence.models import ExportModel


class SqlAlchemyExportRepository(ExportRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, export: Export) -> Export:
        model = ExportModel(
            id=export.id, deal_id=export.deal_id, set_id=export.set_id,
            file_path=export.file_path, export_type=export.export_type.value,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return export_to_entity(model)

    async def get_by_deal_id(self, deal_id: UUID) -> list[Export]:
        stmt = select(ExportModel).where(ExportModel.deal_id == deal_id)
        result = await self._session.execute(stmt)
        return [export_to_entity(m) for m in result.scalars()]
```

**Step 7: Verify imports**

Run: `cd backend && python -c "from app.infrastructure.persistence.deal_repo import SqlAlchemyDealRepository; print('OK')"`
Expected: `OK`

**Step 8: Commit**

```bash
git add backend/app/infrastructure/persistence/
git commit -m "feat: SQLAlchemy repository implementations with entity-model mappers"
```

---

## Task 9: Infrastructure Providers (File Storage, Document Processor, LLM, Excel)

**Files:**
- Create: `backend/app/infrastructure/file_storage/local.py`
- Create: `backend/app/infrastructure/document_processing/pdfplumber_processor.py`
- Create: `backend/app/infrastructure/llm/openai_provider.py`
- Create: `backend/app/infrastructure/export/excel_exporter.py`

**Step 1: LocalFileStorage**

```python
# backend/app/infrastructure/file_storage/local.py
import aiofiles
from pathlib import Path

from app.config import settings
from app.domain.interfaces import FileStorage


class LocalFileStorage(FileStorage):
    def __init__(self, base_path: Path | None = None):
        self._base_path = base_path or settings.file_storage_path
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def store(self, data: bytes, path: str) -> str:
        full_path = self._base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)
        return str(full_path)

    async def retrieve(self, path: str) -> Path:
        full_path = self._base_path / path if not Path(path).is_absolute() else Path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")
        return full_path

    async def delete(self, path: str) -> None:
        full_path = self._base_path / path if not Path(path).is_absolute() else Path(path)
        if full_path.exists():
            full_path.unlink()
```

**Step 2: PdfPlumberProcessor**

```python
# backend/app/infrastructure/document_processing/pdfplumber_processor.py
import asyncio
from pathlib import Path

import pdfplumber

from app.domain.interfaces import DocumentProcessor
from app.domain.value_objects import ExtractedTable, PageText


class PdfPlumberProcessor(DocumentProcessor):
    async def extract_text(self, file_path: Path) -> list[PageText]:
        return await asyncio.to_thread(self._extract_text_sync, file_path)

    async def extract_tables(self, file_path: Path) -> list[ExtractedTable]:
        return await asyncio.to_thread(self._extract_tables_sync, file_path)

    def _extract_text_sync(self, file_path: Path) -> list[PageText]:
        pages = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(PageText(page_number=i + 1, text=text))
        return pages

    def _extract_tables_sync(self, file_path: Path) -> list[ExtractedTable]:
        tables = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                for table_data in page.extract_tables():
                    if not table_data or len(table_data) < 2:
                        continue
                    headers = [str(h or "") for h in table_data[0]]
                    rows = [[str(c or "") for c in row] for row in table_data[1:]]
                    tables.append(
                        ExtractedTable(
                            page_number=i + 1,
                            headers=headers,
                            rows=rows,
                            confidence=0.8,
                        )
                    )
        return tables
```

**Step 3: OpenAILLMProvider**

```python
# backend/app/infrastructure/llm/openai_provider.py
import json

from openai import AsyncOpenAI

from app.config import settings
from app.domain.interfaces import LLMProvider
from app.domain.value_objects import (
    BenchmarkSuggestion,
    Location,
    NormalizedField,
    PropertyType,
    RawField,
)


class OpenAILLMProvider(LLMProvider):
    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    async def generate_benchmarks(
        self, location: Location, property_type: PropertyType
    ) -> list[BenchmarkSuggestion]:
        prompt = f"""Generate real estate underwriting benchmarks for a {property_type.value} property at:
Address: {location.address}, {location.city}, {location.state}

Return a JSON array of benchmark objects. Each must have:
- key: one of "rent_psf_yr", "vacancy_rate", "opex_ratio", "cap_rate"
- value: recommended value (float)
- unit: the unit (e.g., "$/sf/yr", "percent", "ratio")
- range_min: low end of reasonable range
- range_max: high end of reasonable range
- source: brief description of data source
- confidence: 0.0 to 1.0

Return ONLY the JSON array, no other text."""

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        items = data if isinstance(data, list) else data.get("benchmarks", [])
        return [
            BenchmarkSuggestion(
                key=b["key"], value=float(b["value"]), unit=b["unit"],
                range_min=float(b["range_min"]), range_max=float(b["range_max"]),
                source=b["source"], confidence=float(b.get("confidence", 0.7)),
            )
            for b in items
        ]

    async def normalize_extracted_fields(
        self, raw_fields: list[RawField]
    ) -> list[NormalizedField]:
        fields_text = "\n".join(f"- {f.key}: {f.value} (page {f.source_page})" for f in raw_fields)
        prompt = f"""Normalize these extracted real estate document fields into canonical form.

Raw fields:
{fields_text}

Return a JSON array. Each object:
- key: canonical key (e.g., "rent_psf_yr", "vacancy_rate", "noi", "cap_rate", "square_feet", "purchase_price", "year_built", "units", "opex_ratio")
- value_text: original text value or null
- value_number: parsed numeric value or null
- unit: unit string or null
- confidence: 0.0-1.0

Return ONLY the JSON array."""

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        items = data if isinstance(data, list) else data.get("fields", [])
        return [
            NormalizedField(
                key=f["key"], value_text=f.get("value_text"),
                value_number=f.get("value_number"), unit=f.get("unit"),
                confidence=float(f.get("confidence", 0.5)),
            )
            for f in items
        ]
```

**Step 4: OpenpyxlExcelExporter**

```python
# backend/app/infrastructure/export/excel_exporter.py
import asyncio
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from app.domain.entities import Assumption, Deal, ModelResult
from app.domain.interfaces import ExcelExporter


class OpenpyxlExcelExporter(ExcelExporter):
    async def export(
        self, deal: Deal, assumptions: list[Assumption], results: ModelResult
    ) -> bytes:
        return await asyncio.to_thread(self._export_sync, deal, assumptions, results)

    def _export_sync(
        self, deal: Deal, assumptions: list[Assumption], results: ModelResult
    ) -> bytes:
        wb = Workbook()

        # --- Inputs Sheet ---
        ws_inputs = wb.active
        ws_inputs.title = "Deal Inputs"
        header_font = Font(bold=True, size=12)
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font_white = Font(bold=True, size=11, color="FFFFFF")

        ws_inputs.append(["DealDesk - Deal Summary"])
        ws_inputs["A1"].font = Font(bold=True, size=14)
        ws_inputs.append([])
        for label, value in [
            ("Deal Name", deal.name),
            ("Address", deal.address),
            ("City", deal.city),
            ("State", deal.state),
            ("Property Type", deal.property_type.value),
            ("Square Feet", deal.square_feet),
        ]:
            ws_inputs.append([label, value])
        ws_inputs.column_dimensions["A"].width = 20
        ws_inputs.column_dimensions["B"].width = 30

        # --- Assumptions Sheet ---
        ws_assumptions = wb.create_sheet("Assumptions")
        headers = ["Key", "Value", "Unit", "Source", "Range Min", "Range Max", "Notes"]
        ws_assumptions.append(headers)
        for i, cell in enumerate(ws_assumptions[1], 1):
            cell.font = header_font_white
            cell.fill = header_fill
        for a in assumptions:
            ws_assumptions.append([
                a.key, a.value_number, a.unit, a.source_type.value,
                a.range_min, a.range_max, a.notes,
            ])
        for col in "ABCDEFG":
            ws_assumptions.column_dimensions[col].width = 18

        # --- Model Output Sheet ---
        ws_model = wb.create_sheet("Model Output")
        ws_model.append(["Back of Envelope Model"])
        ws_model["A1"].font = Font(bold=True, size=14)
        ws_model.append([])
        for label, value, fmt in [
            ("Gross Revenue", results.noi_stabilized + results.noi_stabilized * 0.538, "$"),
            ("NOI (Stabilized)", results.noi_stabilized, "$"),
            ("Exit Value", results.exit_value, "$"),
            ("Total Cost", results.total_cost, "$"),
            ("Profit / (Loss)", results.profit, "$"),
            ("Profit Margin", results.profit_margin_pct, "%"),
        ]:
            ws_model.append([label, value])
        ws_model.column_dimensions["A"].width = 25
        ws_model.column_dimensions["B"].width = 20

        buf = BytesIO()
        wb.save(buf)
        return buf.getvalue()
```

**Step 5: Verify imports**

Run: `cd backend && python -c "from app.infrastructure.file_storage.local import LocalFileStorage; from app.infrastructure.document_processing.pdfplumber_processor import PdfPlumberProcessor; from app.infrastructure.llm.openai_provider import OpenAILLMProvider; from app.infrastructure.export.excel_exporter import OpenpyxlExcelExporter; print('OK')"`
Expected: `OK`

**Step 6: Commit**

```bash
git add backend/app/infrastructure/
git commit -m "feat: infrastructure providers - file storage, PDF processor, OpenAI LLM, Excel exporter"
```

---

## Task 10: Pydantic API Schemas

**Files:**
- Create: `backend/app/api/schemas.py`

**Step 1: Create all request/response schemas**

```python
# backend/app/api/schemas.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.value_objects.enums import (
    DealStatus,
    DocumentType,
    ExportType,
    ProcessingStatus,
    PropertyType,
    SourceType,
)


# --- Deal ---

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
    id: UUID
    name: str
    address: str
    city: str
    state: str
    property_type: PropertyType
    latitude: float | None
    longitude: float | None
    square_feet: float | None
    status: DealStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Document ---

class ProcessingStepResponse(BaseModel):
    name: str
    status: str
    detail: str = ""


class DocumentResponse(BaseModel):
    id: UUID
    deal_id: UUID
    document_type: DocumentType
    original_filename: str
    processing_status: ProcessingStatus
    processing_steps: list[ProcessingStepResponse]
    error_message: str | None
    page_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Extraction ---

class ExtractedFieldResponse(BaseModel):
    id: UUID
    document_id: UUID
    field_key: str
    value_text: str | None
    value_number: float | None
    unit: str | None
    confidence: float
    source_page: int | None


class MarketTableResponse(BaseModel):
    id: UUID
    document_id: UUID
    table_type: str
    headers: list[str]
    rows: list[list[str]]
    source_page: int | None
    confidence: float


# --- Assumptions ---

class AssumptionSetResponse(BaseModel):
    id: UUID
    deal_id: UUID
    name: str
    created_at: datetime


class AssumptionResponse(BaseModel):
    id: UUID
    set_id: UUID
    key: str
    value_number: float | None
    unit: str | None
    range_min: float | None
    range_max: float | None
    source_type: SourceType
    source_ref: str | None
    notes: str | None
    updated_at: datetime


class UpdateAssumptionRequest(BaseModel):
    key: str
    value_number: float | None = None
    unit: str | None = None
    source_type: SourceType = SourceType.MANUAL
    notes: str | None = None


class BulkUpdateAssumptionsRequest(BaseModel):
    assumptions: list[UpdateAssumptionRequest]


# --- Model ---

class ModelResultResponse(BaseModel):
    id: UUID
    set_id: UUID
    gross_revenue: float | None = None
    effective_revenue: float | None = None
    operating_expenses: float | None = None
    noi_stabilized: float
    exit_value: float
    total_cost: float
    profit: float
    profit_margin_pct: float
    computed_at: datetime


# --- Export ---

class ExportResponse(BaseModel):
    id: UUID
    deal_id: UUID
    set_id: UUID
    file_path: str
    export_type: ExportType
    created_at: datetime


# --- Benchmark ---

class GenerateBenchmarksRequest(BaseModel):
    property_type: PropertyType | None = None


class BenchmarkResponse(BaseModel):
    key: str
    value: float
    unit: str
    range_min: float
    range_max: float
    source: str
    confidence: float
```

**Step 2: Verify imports**

Run: `cd backend && python -c "from app.api.schemas import CreateDealRequest, DealResponse, ModelResultResponse; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/api/schemas.py
git commit -m "feat: Pydantic API request/response schemas"
```

---

## Task 11: Service Layer

**Files:**
- Create: `backend/app/services/deal_service.py`
- Create: `backend/app/services/document_service.py`
- Create: `backend/app/services/benchmark_service.py`
- Create: `backend/app/services/model_service.py`
- Create: `backend/app/services/export_service.py`

**Step 1: DealService**

```python
# backend/app/services/deal_service.py
from uuid import UUID

from app.domain.entities import AssumptionSet, Deal
from app.domain.interfaces import AssumptionSetRepository, DealRepository
from app.domain.value_objects import DealFilters, DealStatus, PropertyType


class DealService:
    def __init__(
        self,
        deal_repo: DealRepository,
        assumption_set_repo: AssumptionSetRepository,
    ):
        self._deal_repo = deal_repo
        self._assumption_set_repo = assumption_set_repo

    async def create_deal(
        self,
        name: str,
        address: str,
        city: str,
        state: str,
        property_type: PropertyType,
        latitude: float | None = None,
        longitude: float | None = None,
        square_feet: float | None = None,
    ) -> Deal:
        deal = Deal(
            name=name, address=address, city=city, state=state,
            property_type=property_type, latitude=latitude,
            longitude=longitude, square_feet=square_feet,
        )
        deal = await self._deal_repo.create(deal)

        # Create default assumption set "Base Case"
        base_set = AssumptionSet(deal_id=deal.id, name="Base Case")
        await self._assumption_set_repo.create(base_set)

        return deal

    async def get_deal(self, deal_id: UUID) -> Deal | None:
        return await self._deal_repo.get_by_id(deal_id)

    async def list_deals(self, filters: DealFilters | None = None) -> list[Deal]:
        return await self._deal_repo.list(filters)

    async def update_deal(self, deal_id: UUID, **kwargs) -> Deal:
        deal = await self._deal_repo.get_by_id(deal_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")
        for key, value in kwargs.items():
            if value is not None and hasattr(deal, key):
                setattr(deal, key, value)
        return await self._deal_repo.update(deal)
```

**Step 2: DocumentService**

```python
# backend/app/services/document_service.py
import logging
from uuid import UUID

from app.domain.entities import Document, ExtractedField, MarketTable
from app.domain.interfaces import (
    DocumentProcessor,
    DocumentRepository,
    ExtractedFieldRepository,
    FileStorage,
    LLMProvider,
    MarketTableRepository,
)
from app.domain.value_objects import (
    DocumentType,
    ProcessingStatus,
    ProcessingStep,
    RawField,
    SourceType,
)

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(
        self,
        document_repo: DocumentRepository,
        extracted_field_repo: ExtractedFieldRepository,
        market_table_repo: MarketTableRepository,
        file_storage: FileStorage,
        document_processor: DocumentProcessor,
        llm_provider: LLMProvider,
    ):
        self._document_repo = document_repo
        self._field_repo = extracted_field_repo
        self._table_repo = market_table_repo
        self._file_storage = file_storage
        self._processor = document_processor
        self._llm = llm_provider

    async def upload_document(
        self,
        deal_id: UUID,
        filename: str,
        data: bytes,
        document_type: DocumentType = DocumentType.OFFERING_MEMORANDUM,
    ) -> Document:
        path = f"deals/{deal_id}/documents/{filename}"
        stored_path = await self._file_storage.store(data, path)

        doc = Document(
            deal_id=deal_id,
            document_type=document_type,
            file_path=stored_path,
            original_filename=filename,
            processing_steps=[
                ProcessingStep(name="upload", status="complete", detail="File uploaded"),
                ProcessingStep(name="extract_text", status="pending"),
                ProcessingStep(name="extract_tables", status="pending"),
                ProcessingStep(name="normalize_fields", status="pending"),
                ProcessingStep(name="ready", status="pending"),
            ],
        )
        return await self._document_repo.create(doc)

    async def process_document(self, document_id: UUID) -> None:
        doc = await self._document_repo.get_by_id(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        try:
            # Step 1: Extract text
            await self._document_repo.update_processing_step(
                document_id, ProcessingStep(name="extract_text", status="in_progress")
            )
            file_path = await self._file_storage.retrieve(doc.file_path)
            pages = await self._processor.extract_text(file_path)
            await self._document_repo.update_processing_step(
                document_id,
                ProcessingStep(name="extract_text", status="complete", detail=f"{len(pages)} pages found"),
            )

            # Step 2: Extract tables
            await self._document_repo.update_processing_step(
                document_id, ProcessingStep(name="extract_tables", status="in_progress")
            )
            tables = await self._processor.extract_tables(file_path)
            if tables:
                table_entities = [
                    MarketTable(
                        document_id=document_id, table_type="extracted",
                        headers=t.headers, rows=t.rows,
                        source_page=t.page_number, confidence=t.confidence,
                    )
                    for t in tables
                ]
                await self._table_repo.bulk_create(table_entities)
            await self._document_repo.update_processing_step(
                document_id,
                ProcessingStep(name="extract_tables", status="complete", detail=f"{len(tables)} tables found"),
            )

            # Step 3: Normalize fields via LLM
            await self._document_repo.update_processing_step(
                document_id, ProcessingStep(name="normalize_fields", status="in_progress")
            )
            raw_fields = []
            for page in pages:
                for line in page.text.split("\n"):
                    if ":" in line:
                        parts = line.split(":", 1)
                        raw_fields.append(RawField(key=parts[0].strip(), value=parts[1].strip(), source_page=page.page_number))

            if raw_fields:
                normalized = await self._llm.normalize_extracted_fields(raw_fields[:50])
                field_entities = [
                    ExtractedField(
                        document_id=document_id, field_key=f.key,
                        value_text=f.value_text, value_number=f.value_number,
                        unit=f.unit, confidence=f.confidence,
                    )
                    for f in normalized
                ]
                await self._field_repo.bulk_create(field_entities)
            await self._document_repo.update_processing_step(
                document_id,
                ProcessingStep(name="normalize_fields", status="complete", detail=f"{len(raw_fields)} fields processed"),
            )

            # Step 4: Mark ready
            doc.processing_status = ProcessingStatus.COMPLETE
            doc.page_count = len(pages)
            await self._document_repo.update(doc)
            await self._document_repo.update_processing_step(
                document_id, ProcessingStep(name="ready", status="complete")
            )

        except Exception as e:
            logger.exception(f"Failed to process document {document_id}")
            doc.processing_status = ProcessingStatus.FAILED
            doc.error_message = str(e)
            await self._document_repo.update(doc)
            await self._document_repo.update_processing_step(
                document_id, ProcessingStep(name="ready", status="failed", detail=str(e))
            )

    async def get_documents(self, deal_id: UUID) -> list[Document]:
        return await self._document_repo.get_by_deal_id(deal_id)

    async def get_document(self, document_id: UUID) -> Document | None:
        return await self._document_repo.get_by_id(document_id)

    async def get_extracted_fields(self, document_id: UUID) -> list[ExtractedField]:
        return await self._field_repo.get_by_document_id(document_id)

    async def get_market_tables(self, document_id: UUID) -> list[MarketTable]:
        return await self._table_repo.get_by_document_id(document_id)
```

**Step 3: BenchmarkService**

```python
# backend/app/services/benchmark_service.py
from uuid import UUID

from app.domain.entities import Assumption
from app.domain.interfaces import (
    AssumptionRepository,
    AssumptionSetRepository,
    DealRepository,
    LLMProvider,
)
from app.domain.value_objects import Location, SourceType


class BenchmarkService:
    def __init__(
        self,
        deal_repo: DealRepository,
        assumption_set_repo: AssumptionSetRepository,
        assumption_repo: AssumptionRepository,
        llm_provider: LLMProvider,
    ):
        self._deal_repo = deal_repo
        self._set_repo = assumption_set_repo
        self._assumption_repo = assumption_repo
        self._llm = llm_provider

    async def generate_benchmarks(self, deal_id: UUID) -> list[Assumption]:
        deal = await self._deal_repo.get_by_id(deal_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")

        location = Location(
            address=deal.address, city=deal.city, state=deal.state,
            latitude=deal.latitude, longitude=deal.longitude,
        )
        benchmarks = await self._llm.generate_benchmarks(location, deal.property_type)

        sets = await self._set_repo.get_by_deal_id(deal_id)
        if not sets:
            raise ValueError(f"No assumption sets for deal {deal_id}")
        base_set = sets[0]

        assumptions = [
            Assumption(
                set_id=base_set.id, key=b.key, value_number=b.value,
                unit=b.unit, range_min=b.range_min, range_max=b.range_max,
                source_type=SourceType.AI, source_ref=b.source,
            )
            for b in benchmarks
        ]
        return await self._assumption_repo.bulk_upsert(assumptions)
```

**Step 4: ModelService**

```python
# backend/app/services/model_service.py
from uuid import UUID

from app.domain.entities import ModelResult
from app.domain.interfaces import (
    AssumptionRepository,
    AssumptionSetRepository,
    DealRepository,
    ModelResultRepository,
)
from app.domain.model_engine import ModelEngine, ModelInput


class ModelService:
    def __init__(
        self,
        deal_repo: DealRepository,
        assumption_set_repo: AssumptionSetRepository,
        assumption_repo: AssumptionRepository,
        model_result_repo: ModelResultRepository,
    ):
        self._deal_repo = deal_repo
        self._set_repo = assumption_set_repo
        self._assumption_repo = assumption_repo
        self._result_repo = model_result_repo

    async def compute(self, set_id: UUID) -> ModelResult:
        assumption_set = await self._set_repo.get_by_id(set_id)
        if not assumption_set:
            raise ValueError(f"AssumptionSet {set_id} not found")

        deal = await self._deal_repo.get_by_id(assumption_set.deal_id)
        if not deal:
            raise ValueError(f"Deal not found for set {set_id}")

        assumptions = await self._assumption_repo.get_by_set_id(set_id)
        lookup = {a.key: a.value_number for a in assumptions}

        model_input = ModelInput(
            rent_psf_yr=lookup.get("rent_psf_yr"),
            square_feet=deal.square_feet or lookup.get("square_feet"),
            vacancy_rate=lookup.get("vacancy_rate"),
            opex_ratio=lookup.get("opex_ratio"),
            cap_rate=lookup.get("cap_rate"),
            purchase_price=lookup.get("purchase_price"),
            closing_costs=lookup.get("closing_costs", 0.0) or 0.0,
            capex_budget=lookup.get("capex_budget", 0.0) or 0.0,
        )

        output = ModelEngine.compute(model_input)

        result = ModelResult(
            set_id=set_id,
            noi_stabilized=output.noi_stabilized,
            exit_value=output.exit_value,
            total_cost=output.total_cost,
            profit=output.profit,
            profit_margin_pct=output.profit_margin_pct,
        )
        return await self._result_repo.create(result)

    async def get_result(self, set_id: UUID) -> ModelResult | None:
        return await self._result_repo.get_by_set_id(set_id)
```

**Step 5: ExportService**

```python
# backend/app/services/export_service.py
from uuid import UUID

from app.domain.entities import Export
from app.domain.interfaces import (
    AssumptionRepository,
    AssumptionSetRepository,
    DealRepository,
    ExcelExporter,
    ExportRepository,
    FileStorage,
    ModelResultRepository,
)
from app.domain.value_objects import ExportType


class ExportService:
    def __init__(
        self,
        deal_repo: DealRepository,
        assumption_set_repo: AssumptionSetRepository,
        assumption_repo: AssumptionRepository,
        model_result_repo: ModelResultRepository,
        export_repo: ExportRepository,
        excel_exporter: ExcelExporter,
        file_storage: FileStorage,
    ):
        self._deal_repo = deal_repo
        self._set_repo = assumption_set_repo
        self._assumption_repo = assumption_repo
        self._result_repo = model_result_repo
        self._export_repo = export_repo
        self._exporter = excel_exporter
        self._file_storage = file_storage

    async def export_xlsx(self, set_id: UUID) -> Export:
        assumption_set = await self._set_repo.get_by_id(set_id)
        if not assumption_set:
            raise ValueError(f"AssumptionSet {set_id} not found")

        deal = await self._deal_repo.get_by_id(assumption_set.deal_id)
        assumptions = await self._assumption_repo.get_by_set_id(set_id)
        result = await self._result_repo.get_by_set_id(set_id)
        if not result:
            raise ValueError("No model result. Compute the model first.")

        xlsx_bytes = await self._exporter.export(deal, assumptions, result)

        slug = deal.name.lower().replace(" ", "-")[:30]
        path = f"exports/{deal.id}/{slug}.xlsx"
        stored_path = await self._file_storage.store(xlsx_bytes, path)

        export = Export(
            deal_id=deal.id, set_id=set_id, file_path=stored_path,
            export_type=ExportType.XLSX,
        )
        return await self._export_repo.create(export)
```

**Step 6: Verify imports**

Run: `cd backend && python -c "from app.services.deal_service import DealService; from app.services.model_service import ModelService; print('OK')"`
Expected: `OK`

**Step 7: Commit**

```bash
git add backend/app/services/
git commit -m "feat: service layer - deal, document, benchmark, model, export services"
```

---

## Task 12: API Routes

**Files:**
- Create: `backend/app/api/v1/deals.py`
- Create: `backend/app/api/v1/documents.py`
- Create: `backend/app/api/v1/assumptions.py`
- Create: `backend/app/api/v1/model.py`
- Create: `backend/app/api/v1/exports.py`
- Create: `backend/app/api/dependencies.py`

**Step 1: Create dependency injection helpers**

```python
# backend/app/api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces import (
    AssumptionRepository,
    AssumptionSetRepository,
    DealRepository,
    DocumentProcessor,
    DocumentRepository,
    ExcelExporter,
    ExportRepository,
    ExtractedFieldRepository,
    FileStorage,
    LLMProvider,
    MarketTableRepository,
    ModelResultRepository,
)
from app.infrastructure.document_processing.pdfplumber_processor import PdfPlumberProcessor
from app.infrastructure.export.excel_exporter import OpenpyxlExcelExporter
from app.infrastructure.file_storage.local import LocalFileStorage
from app.infrastructure.llm.openai_provider import OpenAILLMProvider
from app.infrastructure.persistence.assumption_repo import (
    SqlAlchemyAssumptionRepository,
    SqlAlchemyAssumptionSetRepository,
)
from app.infrastructure.persistence.database import get_session
from app.infrastructure.persistence.deal_repo import SqlAlchemyDealRepository
from app.infrastructure.persistence.document_repo import SqlAlchemyDocumentRepository
from app.infrastructure.persistence.export_repo import SqlAlchemyExportRepository
from app.infrastructure.persistence.extraction_repo import (
    SqlAlchemyExtractedFieldRepository,
    SqlAlchemyMarketTableRepository,
)
from app.infrastructure.persistence.model_result_repo import SqlAlchemyModelResultRepository
from app.services.benchmark_service import BenchmarkService
from app.services.deal_service import DealService
from app.services.document_service import DocumentService
from app.services.export_service import ExportService
from app.services.model_service import ModelService


# --- Providers (singletons) ---

def get_file_storage() -> FileStorage:
    return LocalFileStorage()


def get_document_processor() -> DocumentProcessor:
    return PdfPlumberProcessor()


def get_llm_provider() -> LLMProvider:
    return OpenAILLMProvider()


def get_excel_exporter() -> ExcelExporter:
    return OpenpyxlExcelExporter()


# --- Repositories ---

def get_deal_repo(session: AsyncSession = Depends(get_session)) -> DealRepository:
    return SqlAlchemyDealRepository(session)


def get_document_repo(session: AsyncSession = Depends(get_session)) -> DocumentRepository:
    return SqlAlchemyDocumentRepository(session)


def get_field_repo(session: AsyncSession = Depends(get_session)) -> ExtractedFieldRepository:
    return SqlAlchemyExtractedFieldRepository(session)


def get_table_repo(session: AsyncSession = Depends(get_session)) -> MarketTableRepository:
    return SqlAlchemyMarketTableRepository(session)


def get_assumption_set_repo(session: AsyncSession = Depends(get_session)) -> AssumptionSetRepository:
    return SqlAlchemyAssumptionSetRepository(session)


def get_assumption_repo(session: AsyncSession = Depends(get_session)) -> AssumptionRepository:
    return SqlAlchemyAssumptionRepository(session)


def get_model_result_repo(session: AsyncSession = Depends(get_session)) -> ModelResultRepository:
    return SqlAlchemyModelResultRepository(session)


def get_export_repo(session: AsyncSession = Depends(get_session)) -> ExportRepository:
    return SqlAlchemyExportRepository(session)


# --- Services ---

def get_deal_service(
    deal_repo: DealRepository = Depends(get_deal_repo),
    set_repo: AssumptionSetRepository = Depends(get_assumption_set_repo),
) -> DealService:
    return DealService(deal_repo, set_repo)


def get_document_service(
    doc_repo: DocumentRepository = Depends(get_document_repo),
    field_repo: ExtractedFieldRepository = Depends(get_field_repo),
    table_repo: MarketTableRepository = Depends(get_table_repo),
    file_storage: FileStorage = Depends(get_file_storage),
    processor: DocumentProcessor = Depends(get_document_processor),
    llm: LLMProvider = Depends(get_llm_provider),
) -> DocumentService:
    return DocumentService(doc_repo, field_repo, table_repo, file_storage, processor, llm)


def get_benchmark_service(
    deal_repo: DealRepository = Depends(get_deal_repo),
    set_repo: AssumptionSetRepository = Depends(get_assumption_set_repo),
    assumption_repo: AssumptionRepository = Depends(get_assumption_repo),
    llm: LLMProvider = Depends(get_llm_provider),
) -> BenchmarkService:
    return BenchmarkService(deal_repo, set_repo, assumption_repo, llm)


def get_model_service(
    deal_repo: DealRepository = Depends(get_deal_repo),
    set_repo: AssumptionSetRepository = Depends(get_assumption_set_repo),
    assumption_repo: AssumptionRepository = Depends(get_assumption_repo),
    result_repo: ModelResultRepository = Depends(get_model_result_repo),
) -> ModelService:
    return ModelService(deal_repo, set_repo, assumption_repo, result_repo)


def get_export_service(
    deal_repo: DealRepository = Depends(get_deal_repo),
    set_repo: AssumptionSetRepository = Depends(get_assumption_set_repo),
    assumption_repo: AssumptionRepository = Depends(get_assumption_repo),
    result_repo: ModelResultRepository = Depends(get_model_result_repo),
    export_repo: ExportRepository = Depends(get_export_repo),
    exporter: ExcelExporter = Depends(get_excel_exporter),
    file_storage: FileStorage = Depends(get_file_storage),
) -> ExportService:
    return ExportService(deal_repo, set_repo, assumption_repo, result_repo, export_repo, exporter, file_storage)
```

**Step 2: Deals route**

```python
# backend/app/api/v1/deals.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_deal_service
from app.api.schemas import CreateDealRequest, DealResponse, UpdateDealRequest
from app.domain.value_objects import DealFilters
from app.services.deal_service import DealService

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("", response_model=DealResponse, status_code=201)
async def create_deal(
    req: CreateDealRequest,
    service: DealService = Depends(get_deal_service),
):
    deal = await service.create_deal(**req.model_dump())
    return deal


@router.get("", response_model=list[DealResponse])
async def list_deals(
    property_type: str | None = None,
    status: str | None = None,
    city: str | None = None,
    service: DealService = Depends(get_deal_service),
):
    filters = DealFilters(property_type=property_type, status=status, city=city)
    return await service.list_deals(filters)


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: UUID,
    service: DealService = Depends(get_deal_service),
):
    deal = await service.get_deal(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: UUID,
    req: UpdateDealRequest,
    service: DealService = Depends(get_deal_service),
):
    return await service.update_deal(deal_id, **req.model_dump(exclude_none=True))
```

**Step 3: Documents route**

```python
# backend/app/api/v1/documents.py
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile

from app.api.dependencies import get_document_service
from app.api.schemas import (
    DocumentResponse,
    ExtractedFieldResponse,
    MarketTableResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/deals/{deal_id}/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    deal_id: UUID,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    service: DocumentService = Depends(get_document_service),
):
    data = await file.read()
    doc = await service.upload_document(deal_id, file.filename, data)
    background_tasks.add_task(service.process_document, doc.id)
    return doc


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    deal_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_documents(deal_id)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    deal_id: UUID,
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}/fields", response_model=list[ExtractedFieldResponse])
async def get_extracted_fields(
    deal_id: UUID,
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_extracted_fields(document_id)


@router.get("/{document_id}/tables", response_model=list[MarketTableResponse])
async def get_market_tables(
    deal_id: UUID,
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_market_tables(document_id)
```

**Step 4: Assumptions + Benchmarks route**

```python
# backend/app/api/v1/assumptions.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_assumption_repo,
    get_assumption_set_repo,
    get_benchmark_service,
)
from app.api.schemas import (
    AssumptionResponse,
    AssumptionSetResponse,
    BenchmarkResponse,
    BulkUpdateAssumptionsRequest,
)
from app.domain.entities import Assumption
from app.domain.interfaces import AssumptionRepository, AssumptionSetRepository
from app.domain.value_objects import SourceType
from app.services.benchmark_service import BenchmarkService

router = APIRouter(tags=["assumptions"])


@router.get("/deals/{deal_id}/assumption-sets", response_model=list[AssumptionSetResponse])
async def list_assumption_sets(
    deal_id: UUID,
    repo: AssumptionSetRepository = Depends(get_assumption_set_repo),
):
    return await repo.get_by_deal_id(deal_id)


@router.get("/assumption-sets/{set_id}/assumptions", response_model=list[AssumptionResponse])
async def list_assumptions(
    set_id: UUID,
    repo: AssumptionRepository = Depends(get_assumption_repo),
):
    return await repo.get_by_set_id(set_id)


@router.put("/assumption-sets/{set_id}/assumptions", response_model=list[AssumptionResponse])
async def bulk_update_assumptions(
    set_id: UUID,
    req: BulkUpdateAssumptionsRequest,
    repo: AssumptionRepository = Depends(get_assumption_repo),
):
    entities = [
        Assumption(
            set_id=set_id, key=a.key, value_number=a.value_number,
            unit=a.unit, source_type=a.source_type, notes=a.notes,
        )
        for a in req.assumptions
    ]
    return await repo.bulk_upsert(entities)


@router.post("/deals/{deal_id}/benchmarks:generate", response_model=list[BenchmarkResponse])
async def generate_benchmarks(
    deal_id: UUID,
    service: BenchmarkService = Depends(get_benchmark_service),
):
    assumptions = await service.generate_benchmarks(deal_id)
    return [
        BenchmarkResponse(
            key=a.key, value=a.value_number or 0, unit=a.unit or "",
            range_min=a.range_min or 0, range_max=a.range_max or 0,
            source=a.source_ref or "", confidence=0.7,
        )
        for a in assumptions
    ]
```

**Step 5: Model route**

```python
# backend/app/api/v1/model.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_model_service
from app.api.schemas import ModelResultResponse
from app.services.model_service import ModelService

router = APIRouter(prefix="/assumption-sets/{set_id}", tags=["model"])


@router.post("/compute", response_model=ModelResultResponse)
async def compute_model(
    set_id: UUID,
    service: ModelService = Depends(get_model_service),
):
    try:
        result = await service.compute(set_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.get("/result", response_model=ModelResultResponse)
async def get_model_result(
    set_id: UUID,
    service: ModelService = Depends(get_model_service),
):
    result = await service.get_result(set_id)
    if not result:
        raise HTTPException(status_code=404, detail="No model result. Compute first.")
    return result
```

**Step 6: Export route**

```python
# backend/app/api/v1/exports.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.dependencies import get_export_service, get_file_storage
from app.api.schemas import ExportResponse
from app.domain.interfaces import FileStorage
from app.services.export_service import ExportService

router = APIRouter(prefix="/assumption-sets/{set_id}", tags=["exports"])


@router.post("/export/xlsx", response_model=ExportResponse)
async def export_xlsx(
    set_id: UUID,
    service: ExportService = Depends(get_export_service),
):
    try:
        export = await service.export_xlsx(set_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return export


@router.get("/export/{export_id}/download")
async def download_export(
    set_id: UUID,
    export_id: UUID,
    file_storage: FileStorage = Depends(get_file_storage),
):
    # For MVP, serve the file directly
    # In production, return a signed URL
    try:
        # export_id is used for lookup; for now just serve from path
        return FileResponse(
            path=str(export_id),  # This would need proper lookup
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="dealdesk-export.xlsx",
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Export file not found")
```

**Step 7: Verify imports**

Run: `cd backend && python -c "from app.api.v1.deals import router; print('OK')"`
Expected: `OK`

**Step 8: Commit**

```bash
git add backend/app/api/
git commit -m "feat: API routes - deals, documents, assumptions, model, exports with DI"
```

---

## Task 13: App Factory (main.py)

**Files:**
- Modify: `backend/app/main.py`

**Step 1: Update main.py with all routers and CORS**

```python
# backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.assumptions import router as assumptions_router
from app.api.v1.deals import router as deals_router
from app.api.v1.documents import router as documents_router
from app.api.v1.exports import router as exports_router
from app.api.v1.model import router as model_router
from app.config import settings
from app.infrastructure.persistence.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="DealDesk API",
    version="0.1.0",
    description="AI-Assisted Real Estate Deal Evaluation",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deals_router, prefix="/v1")
app.include_router(documents_router, prefix="/v1")
app.include_router(assumptions_router, prefix="/v1")
app.include_router(model_router, prefix="/v1")
app.include_router(exports_router, prefix="/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 2: Verify the app starts**

Run: `cd backend && python -c "from app.main import app; print(f'Routes: {len(app.routes)}')"`
Expected: `Routes: <some number > 5>`

**Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: FastAPI app factory with all routers, CORS, and lifespan"
```

---

## Task 14: Frontend Scaffolding + OpenAPI Codegen

**Step 1: Create Next.js app**

Run: `cd /Users/justinjhu/Documents/dealdesk && npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --no-import-alias --use-npm`

When prompted, accept defaults.

**Step 2: Install dependencies**

Run: `cd frontend && npm install openapi-typescript-fetch && npm install -D openapi-typescript`

**Step 3: Install shadcn/ui**

Run: `cd frontend && npx shadcn@latest init -d`

**Step 4: Add shadcn components**

Run: `cd frontend && npx shadcn@latest add button input table tabs badge card dialog label select textarea`

**Step 5: Create OpenAPI codegen script**

Add to `frontend/package.json` scripts:

```json
"generate-types": "npx openapi-typescript http://localhost:8000/openapi.json -o src/interfaces/api.ts"
```

**Step 6: Create placeholder api.ts with hand-written types (until backend runs)**

```typescript
// frontend/src/interfaces/api.ts
// These types will be auto-generated from OpenAPI once backend is running.
// For now, define manually to unblock frontend development.

export interface Deal {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  property_type: string;
  latitude: number | null;
  longitude: number | null;
  square_feet: number | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CreateDealInput {
  name: string;
  address: string;
  city: string;
  state: string;
  property_type: string;
  latitude?: number | null;
  longitude?: number | null;
  square_feet?: number | null;
}

export interface ProcessingStep {
  name: string;
  status: string;
  detail: string;
}

export interface Document {
  id: string;
  deal_id: string;
  document_type: string;
  original_filename: string;
  processing_status: string;
  processing_steps: ProcessingStep[];
  error_message: string | null;
  page_count: number | null;
  created_at: string;
}

export interface ExtractedField {
  id: string;
  document_id: string;
  field_key: string;
  value_text: string | null;
  value_number: number | null;
  unit: string | null;
  confidence: number;
  source_page: number | null;
}

export interface MarketTable {
  id: string;
  document_id: string;
  table_type: string;
  headers: string[];
  rows: string[][];
  source_page: number | null;
  confidence: number;
}

export interface AssumptionSet {
  id: string;
  deal_id: string;
  name: string;
  created_at: string;
}

export interface Assumption {
  id: string;
  set_id: string;
  key: string;
  value_number: number | null;
  unit: string | null;
  range_min: number | null;
  range_max: number | null;
  source_type: string;
  source_ref: string | null;
  notes: string | null;
  updated_at: string;
}

export interface ModelResult {
  id: string;
  set_id: string;
  noi_stabilized: number;
  exit_value: number;
  total_cost: number;
  profit: number;
  profit_margin_pct: number;
  computed_at: string;
}

export interface ExportRecord {
  id: string;
  deal_id: string;
  set_id: string;
  file_path: string;
  export_type: string;
  created_at: string;
}

export interface Benchmark {
  key: string;
  value: number;
  unit: string;
  range_min: number;
  range_max: number;
  source: string;
  confidence: number;
}
```

**Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: Next.js frontend scaffolding with Tailwind, shadcn/ui, and TypeScript interfaces"
```

---

## Task 15: Frontend API Client Services

**Files:**
- Create: `frontend/src/services/api-client.ts`
- Create: `frontend/src/services/deal.service.ts`
- Create: `frontend/src/services/document.service.ts`
- Create: `frontend/src/services/assumption.service.ts`
- Create: `frontend/src/services/model.service.ts`
- Create: `frontend/src/services/export.service.ts`

**Step 1: Base API client**

```typescript
// frontend/src/services/api-client.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export async function apiUpload<T>(
  path: string,
  file: File
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(url, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body);
  }

  return res.json();
}
```

**Step 2: Deal service**

```typescript
// frontend/src/services/deal.service.ts
import type { CreateDealInput, Deal } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const dealService = {
  async create(input: CreateDealInput): Promise<Deal> {
    return apiFetch<Deal>("/deals", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  async list(): Promise<Deal[]> {
    return apiFetch<Deal[]>("/deals");
  },

  async get(id: string): Promise<Deal> {
    return apiFetch<Deal>(`/deals/${id}`);
  },

  async update(id: string, input: Partial<CreateDealInput>): Promise<Deal> {
    return apiFetch<Deal>(`/deals/${id}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    });
  },
};
```

**Step 3: Document service**

```typescript
// frontend/src/services/document.service.ts
import type { Document, ExtractedField, MarketTable } from "@/interfaces/api";
import { apiFetch, apiUpload } from "./api-client";

export const documentService = {
  async upload(dealId: string, file: File): Promise<Document> {
    return apiUpload<Document>(`/deals/${dealId}/documents`, file);
  },

  async list(dealId: string): Promise<Document[]> {
    return apiFetch<Document[]>(`/deals/${dealId}/documents`);
  },

  async get(dealId: string, docId: string): Promise<Document> {
    return apiFetch<Document>(`/deals/${dealId}/documents/${docId}`);
  },

  async getFields(dealId: string, docId: string): Promise<ExtractedField[]> {
    return apiFetch<ExtractedField[]>(`/deals/${dealId}/documents/${docId}/fields`);
  },

  async getTables(dealId: string, docId: string): Promise<MarketTable[]> {
    return apiFetch<MarketTable[]>(`/deals/${dealId}/documents/${docId}/tables`);
  },
};
```

**Step 4: Assumption service**

```typescript
// frontend/src/services/assumption.service.ts
import type { Assumption, AssumptionSet, Benchmark } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const assumptionService = {
  async listSets(dealId: string): Promise<AssumptionSet[]> {
    return apiFetch<AssumptionSet[]>(`/deals/${dealId}/assumption-sets`);
  },

  async listAssumptions(setId: string): Promise<Assumption[]> {
    return apiFetch<Assumption[]>(`/assumption-sets/${setId}/assumptions`);
  },

  async bulkUpdate(
    setId: string,
    assumptions: { key: string; value_number: number | null; unit?: string; notes?: string }[]
  ): Promise<Assumption[]> {
    return apiFetch<Assumption[]>(`/assumption-sets/${setId}/assumptions`, {
      method: "PUT",
      body: JSON.stringify({ assumptions }),
    });
  },

  async generateBenchmarks(dealId: string): Promise<Benchmark[]> {
    return apiFetch<Benchmark[]>(`/deals/${dealId}/benchmarks:generate`, {
      method: "POST",
    });
  },
};
```

**Step 5: Model + export services**

```typescript
// frontend/src/services/model.service.ts
import type { ModelResult } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const modelService = {
  async compute(setId: string): Promise<ModelResult> {
    return apiFetch<ModelResult>(`/assumption-sets/${setId}/compute`, {
      method: "POST",
    });
  },

  async getResult(setId: string): Promise<ModelResult | null> {
    try {
      return await apiFetch<ModelResult>(`/assumption-sets/${setId}/result`);
    } catch {
      return null;
    }
  },
};
```

```typescript
// frontend/src/services/export.service.ts
import type { ExportRecord } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const exportService = {
  async exportXlsx(setId: string): Promise<ExportRecord> {
    return apiFetch<ExportRecord>(`/assumption-sets/${setId}/export/xlsx`, {
      method: "POST",
    });
  },
};
```

**Step 6: Commit**

```bash
git add frontend/src/services/ frontend/src/interfaces/
git commit -m "feat: frontend API client services with TypeScript interfaces"
```

---

## Task 16: Frontend Pages + Components

**Files:**
- Create: `frontend/src/app/page.tsx` (deal list)
- Create: `frontend/src/app/deals/new/page.tsx`
- Create: `frontend/src/app/deals/[id]/page.tsx`
- Create: `frontend/src/components/deals/deal-list.tsx`
- Create: `frontend/src/components/deals/create-deal-form.tsx`
- Create: `frontend/src/components/deals/deal-progress-bar.tsx`
- Create: `frontend/src/components/extraction/extracted-fields-table.tsx`
- Create: `frontend/src/components/assumptions/assumption-editor.tsx`
- Create: `frontend/src/components/model/model-outputs.tsx`
- Create: `frontend/src/components/documents/processing-tracker.tsx`
- Create: `frontend/src/hooks/use-deal.ts`

**Step 1: Deal list hook**

```typescript
// frontend/src/hooks/use-deal.ts
"use client";

import { useCallback, useEffect, useState } from "react";
import type { Assumption, AssumptionSet, Deal, Document, ExtractedField, MarketTable, ModelResult } from "@/interfaces/api";
import { dealService } from "@/services/deal.service";
import { documentService } from "@/services/document.service";
import { assumptionService } from "@/services/assumption.service";
import { modelService } from "@/services/model.service";

export function useDeals() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setDeals(await dealService.list());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);
  return { deals, loading, refresh };
}

export function useDeal(id: string) {
  const [deal, setDeal] = useState<Deal | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [assumptionSets, setAssumptionSets] = useState<AssumptionSet[]>([]);
  const [assumptions, setAssumptions] = useState<Assumption[]>([]);
  const [modelResult, setModelResult] = useState<ModelResult | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [d, docs, sets] = await Promise.all([
        dealService.get(id),
        documentService.list(id),
        assumptionService.listSets(id),
      ]);
      setDeal(d);
      setDocuments(docs);
      setAssumptionSets(sets);

      if (sets.length > 0) {
        const [a, r] = await Promise.all([
          assumptionService.listAssumptions(sets[0].id),
          modelService.getResult(sets[0].id),
        ]);
        setAssumptions(a);
        setModelResult(r);
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { refresh(); }, [refresh]);
  return { deal, documents, assumptionSets, assumptions, modelResult, loading, refresh };
}
```

**Step 2: Deal list page**

```tsx
// frontend/src/app/page.tsx
"use client";

import Link from "next/link";
import { useDeals } from "@/hooks/use-deal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function HomePage() {
  const { deals, loading } = useDeals();

  const statusColor: Record<string, string> = {
    draft: "bg-gray-200 text-gray-800",
    processing: "bg-yellow-200 text-yellow-800",
    ready: "bg-green-200 text-green-800",
    exported: "bg-blue-200 text-blue-800",
  };

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">DealDesk</h1>
        <Link href="/deals/new">
          <Button>New Deal</Button>
        </Link>
      </div>

      {loading ? (
        <p className="text-muted-foreground">Loading deals...</p>
      ) : deals.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg">No deals yet.</p>
          <p>Create your first deal to get started.</p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Address</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {deals.map((deal) => (
              <TableRow key={deal.id}>
                <TableCell>
                  <Link href={`/deals/${deal.id}`} className="text-blue-600 hover:underline font-medium">
                    {deal.name}
                  </Link>
                </TableCell>
                <TableCell>{deal.address}, {deal.city}, {deal.state}</TableCell>
                <TableCell className="capitalize">{deal.property_type.replace("_", " ")}</TableCell>
                <TableCell>
                  <Badge className={statusColor[deal.status] || ""}>{deal.status}</Badge>
                </TableCell>
                <TableCell>{new Date(deal.created_at).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
```

**Step 3: Create deal form**

```tsx
// frontend/src/components/deals/create-deal-form.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { dealService } from "@/services/deal.service";
import { documentService } from "@/services/document.service";

const PROPERTY_TYPES = [
  { value: "multifamily", label: "Multifamily" },
  { value: "office", label: "Office" },
  { value: "retail", label: "Retail" },
  { value: "industrial", label: "Industrial" },
  { value: "mixed_use", label: "Mixed Use" },
  { value: "other", label: "Other" },
];

export function CreateDealForm() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "", address: "", city: "", state: "",
    property_type: "multifamily", square_feet: "",
  });
  const [file, setFile] = useState<File | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const deal = await dealService.create({
        ...form,
        square_feet: form.square_feet ? parseFloat(form.square_feet) : null,
      });
      if (file) {
        await documentService.upload(deal.id, file);
      }
      router.push(`/deals/${deal.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create deal");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-lg">
      {error && <p className="text-red-600 text-sm">{error}</p>}

      <div className="space-y-2">
        <Label htmlFor="name">Deal Name</Label>
        <Input id="name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
      </div>

      <div className="space-y-2">
        <Label htmlFor="address">Address</Label>
        <Input id="address" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} required />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="city">City</Label>
          <Input id="city" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="state">State</Label>
          <Input id="state" value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} required />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Property Type</Label>
          <Select value={form.property_type} onValueChange={(v) => setForm({ ...form, property_type: v })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {PROPERTY_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="sqft">Square Feet</Label>
          <Input id="sqft" type="number" value={form.square_feet} onChange={(e) => setForm({ ...form, square_feet: e.target.value })} />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="om">Offering Memorandum (PDF)</Label>
        <Input id="om" type="file" accept=".pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      </div>

      <Button type="submit" disabled={loading} className="w-full">
        {loading ? "Creating..." : "Create Deal"}
      </Button>
    </form>
  );
}
```

**Step 4: Create deal page**

```tsx
// frontend/src/app/deals/new/page.tsx
import { CreateDealForm } from "@/components/deals/create-deal-form";

export default function NewDealPage() {
  return (
    <div className="max-w-6xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Create New Deal</h1>
      <CreateDealForm />
    </div>
  );
}
```

**Step 5: Processing tracker component**

```tsx
// frontend/src/components/documents/processing-tracker.tsx
"use client";

import type { ProcessingStep } from "@/interfaces/api";

const STATUS_ICON: Record<string, string> = {
  complete: "\u2713",
  in_progress: "\u25CF",
  pending: "\u25CB",
  failed: "\u2717",
};

const STATUS_COLOR: Record<string, string> = {
  complete: "text-green-600",
  in_progress: "text-yellow-600 animate-pulse",
  pending: "text-gray-400",
  failed: "text-red-600",
};

export function ProcessingTracker({ steps }: { steps: ProcessingStep[] }) {
  return (
    <div className="space-y-2">
      {steps.map((step, i) => (
        <div key={i} className="flex items-center gap-3 text-sm">
          <span className={`text-lg ${STATUS_COLOR[step.status]}`}>
            {STATUS_ICON[step.status]}
          </span>
          <span className="capitalize font-medium">{step.name.replace("_", " ")}</span>
          {step.detail && (
            <span className="text-muted-foreground">({step.detail})</span>
          )}
        </div>
      ))}
    </div>
  );
}
```

**Step 6: Deal progress bar**

```tsx
// frontend/src/components/deals/deal-progress-bar.tsx
"use client";

const STAGES = [
  { key: "upload", label: "Upload OM" },
  { key: "extract", label: "Extract Data" },
  { key: "assumptions", label: "Set Assumptions" },
  { key: "model", label: "Compute Model" },
  { key: "export", label: "Export" },
];

export function DealProgressBar({ currentStage }: { currentStage: string }) {
  const currentIdx = STAGES.findIndex((s) => s.key === currentStage);

  return (
    <div className="flex items-center gap-2 text-sm mb-6">
      {STAGES.map((stage, i) => (
        <div key={stage.key} className="flex items-center gap-2">
          <div className={`flex items-center gap-1 ${
            i < currentIdx ? "text-green-600" :
            i === currentIdx ? "text-blue-600 font-semibold" :
            "text-gray-400"
          }`}>
            <span>{i < currentIdx ? "\u2713" : i === currentIdx ? "\u25CF" : "\u25CB"}</span>
            <span>{stage.label}</span>
          </div>
          {i < STAGES.length - 1 && <span className="text-gray-300">\u2192</span>}
        </div>
      ))}
    </div>
  );
}
```

**Step 7: Extracted fields table**

```tsx
// frontend/src/components/extraction/extracted-fields-table.tsx
"use client";

import type { ExtractedField } from "@/interfaces/api";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

function confidenceBadge(c: number) {
  if (c > 0.9) return <Badge className="bg-green-200 text-green-800">High</Badge>;
  if (c > 0.7) return <Badge className="bg-yellow-200 text-yellow-800">Review</Badge>;
  return <Badge className="bg-red-200 text-red-800">Low</Badge>;
}

export function ExtractedFieldsTable({ fields }: { fields: ExtractedField[] }) {
  if (fields.length === 0) {
    return <p className="text-muted-foreground py-4">No extracted fields yet.</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Field</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>Unit</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead>Source</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {fields.map((f) => (
          <TableRow key={f.id}>
            <TableCell className="font-medium">{f.field_key}</TableCell>
            <TableCell>{f.value_number ?? f.value_text ?? "-"}</TableCell>
            <TableCell>{f.unit || "-"}</TableCell>
            <TableCell>{confidenceBadge(f.confidence)}</TableCell>
            <TableCell>{f.source_page ? `Page ${f.source_page}` : "-"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

**Step 8: Assumption editor**

```tsx
// frontend/src/components/assumptions/assumption-editor.tsx
"use client";

import { useState } from "react";
import type { Assumption } from "@/interfaces/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { assumptionService } from "@/services/assumption.service";

const SOURCE_BADGE: Record<string, string> = {
  om: "bg-purple-200 text-purple-800",
  ai: "bg-blue-200 text-blue-800",
  manual: "bg-gray-200 text-gray-800",
  ai_edited: "bg-cyan-200 text-cyan-800",
};

export function AssumptionEditor({
  setId,
  assumptions,
  onUpdate,
}: {
  setId: string;
  assumptions: Assumption[];
  onUpdate: () => void;
}) {
  const [values, setValues] = useState<Record<string, string>>(
    Object.fromEntries(assumptions.map((a) => [a.key, String(a.value_number ?? "")]))
  );
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updates = assumptions.map((a) => ({
        key: a.key,
        value_number: values[a.key] ? parseFloat(values[a.key]) : null,
        unit: a.unit,
        source_type: values[a.key] !== String(a.value_number ?? "") ? "manual" as const : a.source_type as any,
      }));
      await assumptionService.bulkUpdate(setId, updates);
      onUpdate();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-3">
        {assumptions.map((a) => (
          <div key={a.id} className="flex items-center gap-4 p-3 border rounded">
            <span className="w-40 font-medium text-sm">{a.key}</span>
            <Input
              type="number"
              step="any"
              className="w-32"
              value={values[a.key] || ""}
              onChange={(e) => setValues({ ...values, [a.key]: e.target.value })}
            />
            <span className="text-sm text-muted-foreground w-20">{a.unit || ""}</span>
            <Badge className={SOURCE_BADGE[a.source_type] || ""}>{a.source_type.toUpperCase()}</Badge>
            {a.range_min != null && a.range_max != null && (
              <span className="text-xs text-muted-foreground">
                Range: {a.range_min} - {a.range_max}
              </span>
            )}
          </div>
        ))}
      </div>
      <Button onClick={handleSave} disabled={saving}>
        {saving ? "Saving..." : "Save Assumptions"}
      </Button>
    </div>
  );
}
```

**Step 9: Model outputs component**

```tsx
// frontend/src/components/model/model-outputs.tsx
"use client";

import type { ModelResult } from "@/interfaces/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function currency(n: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}

export function ModelOutputs({ result }: { result: ModelResult | null }) {
  if (!result) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No model results yet.</p>
        <p className="text-sm">Set assumptions and click Compute.</p>
      </div>
    );
  }

  const metrics = [
    { label: "NOI (Stabilized)", value: currency(result.noi_stabilized), color: "" },
    { label: "Exit Value", value: currency(result.exit_value), color: "" },
    { label: "Total Cost", value: currency(result.total_cost), color: "" },
    {
      label: "Profit / (Loss)",
      value: currency(result.profit),
      color: result.profit >= 0 ? "text-green-600" : "text-red-600",
    },
    {
      label: "Profit Margin",
      value: `${result.profit_margin_pct.toFixed(1)}%`,
      color: result.profit_margin_pct >= 0 ? "text-green-600" : "text-red-600",
    },
  ];

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Computed: {new Date(result.computed_at).toLocaleString()}
      </p>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {metrics.map((m) => (
          <Card key={m.label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{m.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className={`text-2xl font-bold ${m.color}`}>{m.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

**Step 10: Deal workspace page**

```tsx
// frontend/src/app/deals/[id]/page.tsx
"use client";

import { use, useState } from "react";
import { useDeal } from "@/hooks/use-deal";
import { DealProgressBar } from "@/components/deals/deal-progress-bar";
import { ProcessingTracker } from "@/components/documents/processing-tracker";
import { ExtractedFieldsTable } from "@/components/extraction/extracted-fields-table";
import { AssumptionEditor } from "@/components/assumptions/assumption-editor";
import { ModelOutputs } from "@/components/model/model-outputs";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { documentService } from "@/services/document.service";
import { assumptionService } from "@/services/assumption.service";
import { modelService } from "@/services/model.service";
import { exportService } from "@/services/export.service";
import type { ExtractedField, MarketTable } from "@/interfaces/api";

export default function DealPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { deal, documents, assumptionSets, assumptions, modelResult, loading, refresh } = useDeal(id);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [tables, setTables] = useState<MarketTable[]>([]);
  const [computing, setComputing] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  const loadExtraction = async (docId: string) => {
    const [f, t] = await Promise.all([
      documentService.getFields(id, docId),
      documentService.getTables(id, docId),
    ]);
    setFields(f);
    setTables(t);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await assumptionService.generateBenchmarks(id);
      await refresh();
    } finally {
      setGenerating(false);
    }
  };

  const handleCompute = async () => {
    if (!assumptionSets[0]) return;
    setComputing(true);
    try {
      await modelService.compute(assumptionSets[0].id);
      await refresh();
    } finally {
      setComputing(false);
    }
  };

  const handleExport = async () => {
    if (!assumptionSets[0]) return;
    setExporting(true);
    try {
      await exportService.exportXlsx(assumptionSets[0].id);
      await refresh();
    } finally {
      setExporting(false);
    }
  };

  // Determine current stage for progress bar
  const currentStage = !documents.length ? "upload"
    : documents.some((d) => d.processing_status !== "complete") ? "extract"
    : !assumptions.length ? "assumptions"
    : !modelResult ? "model"
    : "export";

  if (loading || !deal) {
    return <div className="max-w-6xl mx-auto p-8">Loading...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h1 className="text-2xl font-bold">{deal.name}</h1>
          <p className="text-muted-foreground">{deal.address}, {deal.city}, {deal.state}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleCompute} disabled={computing}>
            {computing ? "Computing..." : "Compute Model"}
          </Button>
          <Button onClick={handleExport} disabled={exporting || !modelResult}>
            {exporting ? "Exporting..." : "Export XLSX"}
          </Button>
        </div>
      </div>

      <DealProgressBar currentStage={currentStage} />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="extraction">Extraction</TabsTrigger>
          <TabsTrigger value="assumptions">Assumptions</TabsTrigger>
          <TabsTrigger value="model">Model</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6 space-y-6">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="font-medium">Property Type:</span> {deal.property_type}</div>
            <div><span className="font-medium">Square Feet:</span> {deal.square_feet || "—"}</div>
            <div><span className="font-medium">Status:</span> <Badge>{deal.status}</Badge></div>
          </div>

          <div>
            <h3 className="font-semibold mb-3">Documents</h3>
            {documents.length === 0 ? (
              <p className="text-muted-foreground">No documents uploaded.</p>
            ) : (
              documents.map((doc) => (
                <div key={doc.id} className="border rounded p-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="font-medium">{doc.original_filename}</span>
                    <Badge>{doc.processing_status}</Badge>
                  </div>
                  <ProcessingTracker steps={doc.processing_steps} />
                  {doc.processing_status === "complete" && (
                    <Button variant="link" className="p-0" onClick={() => { loadExtraction(doc.id); setActiveTab("extraction"); }}>
                      View Extraction &rarr;
                    </Button>
                  )}
                </div>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="extraction" className="mt-6">
          {documents.length > 0 && fields.length === 0 && (
            <Button variant="outline" onClick={() => loadExtraction(documents[0].id)}>
              Load Extracted Data
            </Button>
          )}
          {fields.length > 0 && (
            <>
              <h3 className="font-semibold mb-3">Extracted Fields</h3>
              <ExtractedFieldsTable fields={fields} />
            </>
          )}
          {tables.length > 0 && (
            <div className="mt-6">
              <h3 className="font-semibold mb-3">Market Tables</h3>
              {tables.map((t) => (
                <div key={t.id} className="border rounded p-4 mb-4 overflow-x-auto">
                  <p className="text-sm text-muted-foreground mb-2">Page {t.source_page} — {t.table_type}</p>
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr>{t.headers.map((h, i) => <th key={i} className="text-left p-1 border-b font-medium">{h}</th>)}</tr>
                    </thead>
                    <tbody>
                      {t.rows.map((row, i) => (
                        <tr key={i}>{row.map((c, j) => <td key={j} className="p-1 border-b">{c}</td>)}</tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="assumptions" className="mt-6 space-y-4">
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleGenerate} disabled={generating}>
              {generating ? "Generating..." : "Generate AI Benchmarks"}
            </Button>
          </div>
          {assumptionSets[0] && (
            <AssumptionEditor
              setId={assumptionSets[0].id}
              assumptions={assumptions}
              onUpdate={refresh}
            />
          )}
        </TabsContent>

        <TabsContent value="model" className="mt-6">
          <ModelOutputs result={modelResult} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

**Step 11: Update layout**

```tsx
// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DealDesk",
  description: "AI-Assisted Real Estate Deal Evaluation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background antialiased">{children}</body>
    </html>
  );
}
```

**Step 12: Commit**

```bash
git add frontend/src/
git commit -m "feat: frontend pages - deal list, create deal, deal workspace with all tabs"
```

---

## Task 17: GitHub Repo + Final Commit

**Step 1: Create .gitignore**

```
# backend
backend/__pycache__/
backend/**/__pycache__/
backend/*.egg-info/
backend/.env
backend/storage/

# frontend
frontend/node_modules/
frontend/.next/
frontend/out/

# general
.env
.DS_Store
*.pyc
```

**Step 2: Create GitHub repository**

Run: `cd /Users/justinjhu/Documents/dealdesk && gh repo create dealdesk --public --source=. --remote=origin`

**Step 3: Push all code**

```bash
git add .gitignore
git commit -m "chore: add .gitignore"
git branch -M main
git push -u origin main
```

**Step 4: Verify**

Run: `gh repo view --web`
Expected: Browser opens to the GitHub repo with all code pushed.
