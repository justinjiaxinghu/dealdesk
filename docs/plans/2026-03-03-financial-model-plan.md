# Financial Model, Sensitivity & Historical Financials — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add structured editable assumption groups, historical financials extraction, a pure-Python DCF engine, and a sensitivity analysis tab to DealDesk.

**Architecture:** Extend the `Assumption` entity with `group`/`forecast_method`/`forecast_params` fields. Add a `HistoricalFinancial` entity extracted by GPT-4o during document processing. New `domain/services/dcf.py` (pure math) powers `FinancialModelService` for both point-in-time compute and sensitivity grids. Frontend gains three new/replaced components: `AssumptionPanel` (grouped editable), `HistoricalFinancialsTab`, and `SensitivityTab`.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, OpenAI GPT-4o, Next.js 16, React 19, TypeScript 5, Tailwind CSS 4, shadcn/ui

---

## Before You Start

```bash
source ~/anaconda3/etc/profile.d/conda.sh && conda activate dealdesk
cd /Users/pedrojudice/dealdesk/backend
python -m pytest tests/ -v   # confirm baseline passes
```

Frontend dev server: `cd frontend && npm run dev` (port 3000)
Backend dev server: `uvicorn app.main:app --reload` (port 8000)

---

## Task 1: Add `AssumptionGroup` enum to domain enums

**Files:**
- Modify: `backend/app/domain/value_objects/enums.py`

**Step 1: Add the enum**

Open `backend/app/domain/value_objects/enums.py`. After the `CompSource` enum, append:

```python
class AssumptionGroup(StrEnum):
    MODEL_STRUCTURE = "model_structure"
    TRANSACTION = "transaction"
    OPERATING = "operating"
    FINANCING = "financing"
    RETURN_TARGETS = "return_targets"
```

**Step 2: Export it**

Open `backend/app/domain/value_objects/__init__.py`. Add `AssumptionGroup` to the imports and `__all__` (match the existing pattern for other enums in that file).

**Step 3: Run tests to confirm nothing broke**

```bash
cd backend && python -m pytest tests/ -v
```
Expected: all existing tests pass.

**Step 4: Commit**

```bash
git add backend/app/domain/value_objects/enums.py backend/app/domain/value_objects/__init__.py
git commit -m "feat: add AssumptionGroup enum to domain value objects"
```

---

## Task 2: Extend `Assumption` entity and ORM model

**Files:**
- Modify: `backend/app/domain/entities/assumption.py`
- Modify: `backend/app/infrastructure/persistence/models.py`
- Modify: `backend/app/infrastructure/persistence/mappers.py`
- Modify: `backend/app/api/schemas.py`

**Step 1: Write the failing test**

Create `backend/tests/test_assumption_groups.py`:

```python
from app.domain.entities.assumption import Assumption
from app.domain.value_objects.enums import AssumptionGroup, SourceType
from uuid import uuid4


def test_assumption_has_group_field():
    a = Assumption(
        set_id=uuid4(),
        key="purchase_price",
        value_number=1_000_000,
        group=AssumptionGroup.TRANSACTION,
    )
    assert a.group == AssumptionGroup.TRANSACTION


def test_assumption_group_defaults_to_none():
    a = Assumption(set_id=uuid4(), key="some_key")
    assert a.group is None


def test_assumption_has_forecast_fields():
    a = Assumption(
        set_id=uuid4(),
        key="occupancy_rate",
        value_number=0.95,
        group=AssumptionGroup.OPERATING,
        forecast_method="gradual_ramp",
        forecast_params={"target_value": 0.97},
    )
    assert a.forecast_method == "gradual_ramp"
    assert a.forecast_params == {"target_value": 0.97}
```

**Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_assumption_groups.py -v
```
Expected: FAIL — `Assumption` has no `group` field.

**Step 3: Update `Assumption` entity**

In `backend/app/domain/entities/assumption.py`, add three fields after `notes`:

```python
from app.domain.value_objects.enums import AssumptionGroup, SourceType  # add AssumptionGroup

# in the dataclass, after notes:
group: AssumptionGroup | None = None
forecast_method: str | None = None
forecast_params: dict | None = None
```

**Step 4: Run test to verify it passes**

```bash
cd backend && python -m pytest tests/test_assumption_groups.py -v
```
Expected: PASS.

**Step 5: Update ORM model**

In `backend/app/infrastructure/persistence/models.py`, find `AssumptionModel`. After the `notes` column, add:

```python
group: Mapped[str | None] = mapped_column(String(50), nullable=True)
forecast_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
forecast_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
```

**Step 6: Update mapper**

In `backend/app/infrastructure/persistence/mappers.py`, find `assumption_to_entity` and `assumption_to_model`. Add the three new fields to both directions. Pattern: look at how `notes` is currently mapped and replicate it for `group`, `forecast_method`, `forecast_params`. For `group`, convert string ↔ `AssumptionGroup` enum the same way other enums are handled (e.g. `AssumptionGroup(model.group) if model.group else None`).

**Step 7: Update API schema**

In `backend/app/api/schemas.py`, find `AssumptionResponse` and `BulkUpdateAssumptionsRequest`. Add to both:

```python
group: str | None = None
forecast_method: str | None = None
forecast_params: dict | None = None
```

**Step 8: Run all tests**

```bash
cd backend && python -m pytest tests/ -v
```
Expected: all pass.

**Step 9: Commit**

```bash
git add backend/app/domain/entities/assumption.py \
        backend/app/infrastructure/persistence/models.py \
        backend/app/infrastructure/persistence/mappers.py \
        backend/app/api/schemas.py \
        backend/tests/test_assumption_groups.py
git commit -m "feat: add group, forecast_method, forecast_params to Assumption entity"
```

---

## Task 3: Alembic migration — assumption group columns

**Files:**
- Create: `backend/app/infrastructure/persistence/migrations/versions/<hash>_add_assumption_group_fields.py` (auto-generated)

**Step 1: Generate migration**

```bash
cd backend && python -m alembic revision --autogenerate -m "add assumption group and forecast fields"
```

**Step 2: Inspect the generated file**

Open the new file in `backend/app/infrastructure/persistence/migrations/versions/`. Confirm it adds three nullable columns to `assumptions`: `group`, `forecast_method`, `forecast_params`.

**Step 3: Apply migration**

```bash
cd backend && python -m alembic upgrade head
```
Expected: no errors.

**Step 4: Commit**

```bash
git add backend/app/infrastructure/persistence/migrations/
git commit -m "feat: migrate assumptions table — add group and forecast columns"
```

---

## Task 4: `HistoricalFinancial` entity, repo interface, ORM model, mapper, repo

**Files:**
- Create: `backend/app/domain/entities/historical_financial.py`
- Modify: `backend/app/domain/entities/__init__.py`
- Modify: `backend/app/domain/interfaces/repositories.py`
- Modify: `backend/app/infrastructure/persistence/models.py`
- Modify: `backend/app/infrastructure/persistence/mappers.py`
- Create: `backend/app/infrastructure/persistence/historical_financial_repo.py`

**Step 1: Write the failing test**

Create `backend/tests/test_historical_financial_entity.py`:

```python
from datetime import datetime
from uuid import uuid4
from app.domain.entities.historical_financial import HistoricalFinancial


def test_historical_financial_entity():
    hf = HistoricalFinancial(
        deal_id=uuid4(),
        period_label="T12",
        metric_key="noi",
        value=1_400_000.0,
        unit="$",
        source="extracted",
    )
    assert hf.period_label == "T12"
    assert hf.metric_key == "noi"
    assert hf.value == 1_400_000.0
    assert hf.id is not None
    assert hf.created_at is not None
```

**Step 2: Run to confirm fail**

```bash
cd backend && python -m pytest tests/test_historical_financial_entity.py -v
```

**Step 3: Create the entity**

Create `backend/app/domain/entities/historical_financial.py`:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class HistoricalFinancial:
    deal_id: UUID
    period_label: str
    metric_key: str
    value: float
    source: str           # "extracted" | "manual"
    id: UUID = field(default_factory=uuid4)
    unit: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Step 4: Export from entities `__init__`**

Open `backend/app/domain/entities/__init__.py`. Import and re-export `HistoricalFinancial` following the pattern used for other entities.

**Step 5: Run test to confirm pass**

```bash
cd backend && python -m pytest tests/test_historical_financial_entity.py -v
```

**Step 6: Add `HistoricalFinancialRepository` ABC**

In `backend/app/domain/interfaces/repositories.py`, import `HistoricalFinancial` and add at the bottom:

```python
class HistoricalFinancialRepository(ABC):
    @abstractmethod
    async def bulk_upsert(
        self, items: list[HistoricalFinancial]
    ) -> list[HistoricalFinancial]: ...

    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[HistoricalFinancial]: ...
```

**Step 7: Add ORM model**

In `backend/app/infrastructure/persistence/models.py`, after `CompModel`, add:

```python
# ---------------------------------------------------------------------------
# Historical Financials
# ---------------------------------------------------------------------------

class HistoricalFinancialModel(Base):
    __tablename__ = "historical_financials"
    __table_args__ = (
        UniqueConstraint("deal_id", "period_label", "metric_key", name="uq_hf_deal_period_metric"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    deal_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), ForeignKey("deals.id"), nullable=False)
    period_label: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="extracted")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    deal = relationship("DealModel", back_populates="historical_financials")
```

Also add to `DealModel.relationships`:
```python
historical_financials = relationship("HistoricalFinancialModel", back_populates="deal", lazy="selectin")
```

**Step 8: Add mapper functions**

In `backend/app/infrastructure/persistence/mappers.py`, add two functions:

```python
from app.domain.entities.historical_financial import HistoricalFinancial
from app.infrastructure.persistence.models import HistoricalFinancialModel


def historical_financial_to_model(entity: HistoricalFinancial) -> HistoricalFinancialModel:
    return HistoricalFinancialModel(
        id=entity.id,
        deal_id=entity.deal_id,
        period_label=entity.period_label,
        metric_key=entity.metric_key,
        value=entity.value,
        unit=entity.unit,
        source=entity.source,
        created_at=entity.created_at,
    )


def historical_financial_to_entity(model: HistoricalFinancialModel) -> HistoricalFinancial:
    return HistoricalFinancial(
        id=model.id,
        deal_id=model.deal_id,
        period_label=model.period_label,
        metric_key=model.metric_key,
        value=model.value,
        unit=model.unit,
        source=model.source,
        created_at=model.created_at,
    )
```

**Step 9: Create the repo**

Create `backend/app/infrastructure/persistence/historical_financial_repo.py`:

```python
from __future__ import annotations
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.historical_financial import HistoricalFinancial
from app.domain.interfaces.repositories import HistoricalFinancialRepository
from app.infrastructure.persistence.mappers import (
    historical_financial_to_entity,
    historical_financial_to_model,
)
from app.infrastructure.persistence.models import HistoricalFinancialModel


class SqlAlchemyHistoricalFinancialRepository(HistoricalFinancialRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_upsert(
        self, items: list[HistoricalFinancial]
    ) -> list[HistoricalFinancial]:
        if not items:
            return []
        deal_id = items[0].deal_id
        # Delete existing rows for this deal then re-insert
        await self._session.execute(
            delete(HistoricalFinancialModel).where(
                HistoricalFinancialModel.deal_id == deal_id
            )
        )
        models = [historical_financial_to_model(i) for i in items]
        self._session.add_all(models)
        await self._session.flush()
        return [historical_financial_to_entity(m) for m in models]

    async def get_by_deal_id(self, deal_id: UUID) -> list[HistoricalFinancial]:
        result = await self._session.execute(
            select(HistoricalFinancialModel).where(
                HistoricalFinancialModel.deal_id == deal_id
            )
        )
        return [historical_financial_to_entity(m) for m in result.scalars()]
```

**Step 10: Run all tests**

```bash
cd backend && python -m pytest tests/ -v
```
Expected: all pass.

**Step 11: Commit**

```bash
git add backend/app/domain/entities/historical_financial.py \
        backend/app/domain/entities/__init__.py \
        backend/app/domain/interfaces/repositories.py \
        backend/app/infrastructure/persistence/models.py \
        backend/app/infrastructure/persistence/mappers.py \
        backend/app/infrastructure/persistence/historical_financial_repo.py \
        backend/tests/test_historical_financial_entity.py
git commit -m "feat: add HistoricalFinancial entity, repo ABC, ORM model, mapper, and repo"
```

---

## Task 5: Alembic migration — `historical_financials` table

**Step 1: Generate**

```bash
cd backend && python -m alembic revision --autogenerate -m "create historical_financials table"
```

**Step 2: Inspect and apply**

```bash
cd backend && python -m alembic upgrade head
```

**Step 3: Commit**

```bash
git add backend/app/infrastructure/persistence/migrations/
git commit -m "feat: migrate — create historical_financials table"
```

---

## Task 6: LLM extraction of historical financials

**Files:**
- Modify: `backend/app/domain/value_objects/types.py`
- Modify: `backend/app/domain/interfaces/providers.py`
- Modify: `backend/app/infrastructure/llm/openai_provider.py`

**Step 1: Add `HistoricalFinancialResult` value object**

In `backend/app/domain/value_objects/types.py`, add after the last frozen dataclass:

```python
@dataclass(frozen=True)
class HistoricalFinancialResult:
    period_label: str    # "T12", "2024", "2023"
    metric_key: str      # "gross_revenue", "noi", "expense_ratio", "occupancy_rate", etc.
    value: float
    unit: str | None = None
```

Export it from `backend/app/domain/value_objects/__init__.py`.

**Step 2: Add abstract method to `LLMProvider`**

In `backend/app/domain/interfaces/providers.py`, import `HistoricalFinancialResult` and add to `LLMProvider`:

```python
@abstractmethod
async def extract_historical_financials(
    self,
    pages: list[PageText],
    deal: Deal,
) -> list[HistoricalFinancialResult]: ...
```

**Step 3: Implement in `OpenAILLMProvider`**

In `backend/app/infrastructure/llm/openai_provider.py`, import `HistoricalFinancialResult` and add this method to `OpenAILLMProvider`:

```python
async def extract_historical_financials(
    self,
    pages: list[PageText],
    deal: Deal,
) -> list[HistoricalFinancialResult]:
    text = "\n".join(p.text for p in pages[:20])  # first 20 pages
    prompt = (
        "You are a real estate financial analyst. Extract historical financial data "
        "from the following Offering Memorandum text.\n\n"
        "Look for T12, trailing twelve months, prior year, or any historical P&L data. "
        "Return a JSON object with key 'financials' containing an array of objects with:\n"
        '  "period_label": string (e.g. "T12", "2024", "2023", "T-1", "T-2")\n'
        '  "metric_key": string — use exactly these canonical keys:\n'
        "    gross_revenue, effective_gross_income, total_operating_expenses, noi,\n"
        "    expense_ratio, occupancy_rate, revenue_per_unit, opex_per_unit,\n"
        "    net_rentable_area, total_units\n"
        '  "value": number\n'
        '  "unit": string (e.g. "$", "%", "$/unit")\n\n'
        "Only include metrics you find explicitly in the text. If no historical data is found, "
        'return {"financials": []}.\n\n'
        f"OM Text:\n{text}"
    )
    response = await self._client.chat.completions.create(
        model=self._model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    content = response.choices[0].message.content or "{}"
    data = json.loads(content)
    results = []
    for item in data.get("financials", []):
        try:
            results.append(
                HistoricalFinancialResult(
                    period_label=item["period_label"],
                    metric_key=item["metric_key"],
                    value=float(item["value"]),
                    unit=item.get("unit"),
                )
            )
        except (KeyError, ValueError):
            continue
    return results
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/ -v
```
Expected: all pass (no tests call this new method yet).

**Step 5: Commit**

```bash
git add backend/app/domain/value_objects/types.py \
        backend/app/domain/value_objects/__init__.py \
        backend/app/domain/interfaces/providers.py \
        backend/app/infrastructure/llm/openai_provider.py
git commit -m "feat: add extract_historical_financials to LLMProvider and OpenAI implementation"
```

---

## Task 7: `HistoricalFinancialService` and API route

**Files:**
- Create: `backend/app/services/historical_financial_service.py`
- Modify: `backend/app/api/schemas.py`
- Create: `backend/app/api/v1/historical_financials.py`
- Modify: `backend/app/api/dependencies.py`
- Modify: `backend/app/main.py`

**Step 1: Write the failing test**

Create `backend/tests/test_historical_financial_service.py`:

```python
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from app.domain.entities.deal import Deal
from app.domain.entities.document import Document
from app.domain.value_objects.enums import PropertyType, ProcessingStatus
from app.domain.value_objects.types import HistoricalFinancialResult, PageText
from app.services.historical_financial_service import HistoricalFinancialService


@pytest.fixture
def deal():
    return Deal(
        id=uuid4(), name="Test", address="123 Main",
        city="Austin", state="TX", property_type=PropertyType.MULTIFAMILY,
    )


@pytest.fixture
def document(deal):
    return Document(
        id=uuid4(), deal_id=deal.id,
        file_path="/tmp/test.pdf", original_filename="test.pdf",
        processing_status=ProcessingStatus.COMPLETE,
    )


@pytest.mark.asyncio
async def test_extract_persists_results(deal, document):
    deal_repo = AsyncMock()
    deal_repo.get_by_id.return_value = deal
    doc_repo = AsyncMock()
    doc_repo.get_by_id.return_value = document
    hf_repo = AsyncMock()
    hf_repo.bulk_upsert.return_value = []
    llm = AsyncMock()
    llm.extract_historical_financials.return_value = [
        HistoricalFinancialResult("T12", "noi", 1_400_000.0, "$")
    ]
    processor = AsyncMock()
    processor.extract_text.return_value = [PageText(page_number=1, text="NOI $1.4M")]

    svc = HistoricalFinancialService(deal_repo, doc_repo, hf_repo, llm, processor)
    result = await svc.extract(deal.id, document.id)

    llm.extract_historical_financials.assert_called_once()
    hf_repo.bulk_upsert.assert_called_once()


@pytest.mark.asyncio
async def test_extract_raises_if_deal_not_found():
    deal_repo = AsyncMock()
    deal_repo.get_by_id.return_value = None
    svc = HistoricalFinancialService(deal_repo, AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock())
    with pytest.raises(ValueError, match="not found"):
        await svc.extract(uuid4(), uuid4())
```

**Step 2: Run to confirm fail**

```bash
cd backend && python -m pytest tests/test_historical_financial_service.py -v
```

**Step 3: Create the service**

Create `backend/app/services/historical_financial_service.py`:

```python
from __future__ import annotations
from uuid import UUID
from app.domain.entities.historical_financial import HistoricalFinancial
from app.domain.interfaces.providers import DocumentProcessor, LLMProvider
from app.domain.interfaces.repositories import (
    DealRepository,
    DocumentRepository,
    HistoricalFinancialRepository,
)


class HistoricalFinancialService:
    def __init__(
        self,
        deal_repo: DealRepository,
        document_repo: DocumentRepository,
        hf_repo: HistoricalFinancialRepository,
        llm_provider: LLMProvider,
        document_processor: DocumentProcessor,
    ) -> None:
        self._deal_repo = deal_repo
        self._document_repo = document_repo
        self._hf_repo = hf_repo
        self._llm = llm_provider
        self._processor = document_processor

    async def extract(self, deal_id: UUID, document_id: UUID) -> list[HistoricalFinancial]:
        deal = await self._deal_repo.get_by_id(deal_id)
        if deal is None:
            raise ValueError(f"Deal {deal_id} not found")
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        from pathlib import Path
        pages = await self._processor.extract_text(Path(document.file_path))
        results = await self._llm.extract_historical_financials(pages, deal)

        items = [
            HistoricalFinancial(
                deal_id=deal_id,
                period_label=r.period_label,
                metric_key=r.metric_key,
                value=r.value,
                unit=r.unit,
                source="extracted",
            )
            for r in results
        ]
        return await self._hf_repo.bulk_upsert(items)

    async def list(self, deal_id: UUID) -> list[HistoricalFinancial]:
        return await self._hf_repo.get_by_deal_id(deal_id)
```

**Step 4: Run test to confirm pass**

```bash
cd backend && python -m pytest tests/test_historical_financial_service.py -v
```

**Step 5: Add API schema**

In `backend/app/api/schemas.py`, add:

```python
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
```

**Step 6: Create the API route**

Create `backend/app/api/v1/historical_financials.py`:

```python
from __future__ import annotations
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import get_historical_financial_service
from app.api.schemas import HistoricalFinancialResponse
from app.services.historical_financial_service import HistoricalFinancialService

router = APIRouter(tags=["historical_financials"])


@router.get(
    "/deals/{deal_id}/historical-financials",
    response_model=list[HistoricalFinancialResponse],
)
async def list_historical_financials(
    deal_id: UUID,
    service: Annotated[HistoricalFinancialService, Depends(get_historical_financial_service)],
) -> list[HistoricalFinancialResponse]:
    items = await service.list(deal_id)
    return [HistoricalFinancialResponse.model_validate(i) for i in items]


@router.post(
    "/deals/{deal_id}/documents/{document_id}/historical-financials:extract",
    response_model=list[HistoricalFinancialResponse],
)
async def extract_historical_financials(
    deal_id: UUID,
    document_id: UUID,
    service: Annotated[HistoricalFinancialService, Depends(get_historical_financial_service)],
) -> list[HistoricalFinancialResponse]:
    try:
        items = await service.extract(deal_id, document_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return [HistoricalFinancialResponse.model_validate(i) for i in items]
```

**Step 7: Wire DI in `dependencies.py`**

In `backend/app/api/dependencies.py`:

1. Import the new repo class:
```python
from app.infrastructure.persistence.historical_financial_repo import SqlAlchemyHistoricalFinancialRepository
```

2. Add repo factory:
```python
def get_historical_financial_repo(session: DbSession) -> SqlAlchemyHistoricalFinancialRepository:
    return SqlAlchemyHistoricalFinancialRepository(session)
```

3. Import the service:
```python
from app.services.historical_financial_service import HistoricalFinancialService
```

4. Add service factory:
```python
def get_historical_financial_service(
    deal_repo: Annotated[SqlAlchemyDealRepository, Depends(get_deal_repo)],
    document_repo: Annotated[SqlAlchemyDocumentRepository, Depends(get_document_repo)],
    hf_repo: Annotated[SqlAlchemyHistoricalFinancialRepository, Depends(get_historical_financial_repo)],
) -> HistoricalFinancialService:
    return HistoricalFinancialService(
        deal_repo=deal_repo,
        document_repo=document_repo,
        hf_repo=hf_repo,
        llm_provider=_llm_provider,
        document_processor=_document_processor,
    )
```

**Step 8: Register router in `main.py`**

In `backend/app/main.py`, import the new router and add it to the app the same way other routers are registered:

```python
from app.api.v1.historical_financials import router as historical_financials_router
# ... in the include_router section:
app.include_router(historical_financials_router, prefix="/v1")
```

**Step 9: Run all tests**

```bash
cd backend && python -m pytest tests/ -v
```

**Step 10: Commit**

```bash
git add backend/app/services/historical_financial_service.py \
        backend/app/api/schemas.py \
        backend/app/api/v1/historical_financials.py \
        backend/app/api/dependencies.py \
        backend/app/main.py \
        backend/tests/test_historical_financial_service.py
git commit -m "feat: add HistoricalFinancialService and API routes"
```

---

## Task 8: Pure Python DCF engine

**Files:**
- Create: `backend/app/domain/services/__init__.py`
- Create: `backend/app/domain/services/dcf.py`
- Create: `backend/tests/test_dcf.py`

**Step 1: Write the failing tests first**

Create `backend/tests/test_dcf.py`:

```python
import pytest
from app.domain.services.dcf import (
    ProjectionParams,
    ProjectionResult,
    compute_projection,
    _bisect_irr,
)
from datetime import date


def base_params(**overrides) -> ProjectionParams:
    defaults = dict(
        start_date=date(2026, 1, 1),
        periods=5,
        cadence="annual",
        purchase_price=1_000_000.0,
        ltv=0.70,
        closing_costs=0.0,
        acquisition_fee=0.0,
        base_gross_revenue=100_000.0,
        base_occupancy_rate=1.0,
        base_expense_ratio=0.40,
        base_capex_per_unit=0.0,
        revenue_forecast_method="historical",
        revenue_forecast_params={},
        expense_forecast_method="historical",
        expense_forecast_params={},
        sofr_rate=0.04,
        spread=0.01,
        loan_term=30,
        interest_only_years=5,
        exit_cap_rate=0.06,
    )
    defaults.update(overrides)
    return ProjectionParams(**defaults)


def test_cap_rate_on_cost():
    params = base_params()
    result = compute_projection(params)
    # NOI = 100k * 1.0 * (1 - 0.40) = 60k; total_cost = 1M
    assert result.cap_rate_on_cost == pytest.approx(0.06, abs=0.001)


def test_equity_multiple():
    params = base_params()
    result = compute_projection(params)
    # equity = 300k, annual CF = 60k NOI - 35k debt = 25k/yr x 5 = 125k
    # terminal: exit = 60k/0.06 = 1M, remaining balance = 700k, terminal CF = 300k
    # total distributions = 125k + 300k = 425k
    # equity multiple = 425k / 300k = 1.4167
    assert result.equity_multiple == pytest.approx(1.4167, abs=0.01)


def test_cash_on_cash_yr1():
    params = base_params()
    result = compute_projection(params)
    # yr1 CF = 25k, equity = 300k → 8.33%
    assert result.cash_on_cash_yr1 == pytest.approx(0.0833, abs=0.001)


def test_irr_is_reasonable():
    params = base_params()
    result = compute_projection(params)
    # Should be roughly 8-9%
    assert result.irr is not None
    assert 0.07 < result.irr < 0.10


def test_zero_ltv_no_debt_service():
    params = base_params(ltv=0.0)
    result = compute_projection(params)
    # No debt: NOI = 60k/yr, equity = 1M, CoC = 6%
    assert result.cash_on_cash_yr1 == pytest.approx(0.06, abs=0.001)
    # Exit value = 1M, total CF = 60k*5 + 1M = 1.3M, EM = 1.3
    assert result.equity_multiple == pytest.approx(1.3, abs=0.01)


def test_step_change_revenue():
    # Revenue grows by 5k/yr (step_value=5000)
    params = base_params(
        revenue_forecast_method="step_change",
        revenue_forecast_params={"step_value": 5000},
    )
    result = compute_projection(params)
    # yr1 revenue = 105k, yr5 revenue = 125k
    # exit NOI = 125k * (1-0.40) = 75k; exit value = 75k/0.06 = 1.25M
    assert result.equity_multiple > base_params().model_copy() and True  # just check it runs


def test_bisect_irr_simple():
    # CF = [-100, 110] → IRR = 10%
    irr = _bisect_irr([-100.0, 110.0])
    assert irr == pytest.approx(0.10, abs=0.0001)


def test_bisect_irr_two_periods():
    # CF = [-100, 0, 121] → IRR = 10%
    irr = _bisect_irr([-100.0, 0.0, 121.0])
    assert irr == pytest.approx(0.10, abs=0.0001)
```

**Step 2: Run to confirm fail**

```bash
cd backend && python -m pytest tests/test_dcf.py -v
```
Expected: FAIL — module not found.

**Step 3: Create `domain/services/`**

```bash
touch backend/app/domain/services/__init__.py
```

**Step 4: Implement `dcf.py`**

Create `backend/app/domain/services/dcf.py`:

```python
"""Pure Python DCF engine. Zero external dependencies."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class ProjectionParams:
    # Model structure
    start_date: date
    periods: int
    cadence: str                      # "annual" | "quarterly"
    # Transaction
    purchase_price: float
    ltv: float
    closing_costs: float
    acquisition_fee: float
    # Operating
    base_gross_revenue: float
    base_occupancy_rate: float
    base_expense_ratio: float
    base_capex_per_unit: float
    revenue_forecast_method: str      # "historical" | "step_change" | "gradual_ramp"
    revenue_forecast_params: dict[str, Any]
    expense_forecast_method: str
    expense_forecast_params: dict[str, Any]
    # Financing
    sofr_rate: float
    spread: float
    loan_term: int                    # years
    interest_only_years: int
    # Returns
    exit_cap_rate: float


@dataclass(frozen=True)
class ProjectionResult:
    irr: float | None
    equity_multiple: float
    cash_on_cash_yr1: float
    cap_rate_on_cost: float
    cash_flows: list[float]


def _apply_forecast(base: float, period: int, method: str, params: dict[str, Any]) -> float:
    """Return the value at period t (1-indexed) using the specified forecast method."""
    if method == "step_change":
        return base + params.get("step_value", 0.0) * period
    if method == "gradual_ramp":
        target = params.get("target_value", base)
        if period == 0:
            return base
        # Linear ramp: period 1 → slightly above base, last period → target
        # We ramp over `periods` but don't know it here; use ratio approach
        # Caller supplies periods; we approximate: value_t = base + (target-base)*(t/periods)
        # `periods` is not in params by default; fall back to simple linear if not supplied
        n = params.get("periods", 5)
        return base + (target - base) * (period / n)
    # "historical" or unknown: flat
    return base


def _npv(cash_flows: list[float], rate: float) -> float:
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))


def _bisect_irr(
    cash_flows: list[float],
    low: float = -0.5,
    high: float = 10.0,
    tol: float = 1e-8,
    max_iter: int = 1000,
) -> float | None:
    """Bisection method to find IRR."""
    npv_low = _npv(cash_flows, low)
    npv_high = _npv(cash_flows, high)
    if npv_low * npv_high > 0:
        return None  # No sign change — IRR not in range
    for _ in range(max_iter):
        mid = (low + high) / 2
        npv_mid = _npv(cash_flows, mid)
        if abs(npv_mid) < tol or (high - low) / 2 < tol:
            return mid
        if npv_low * npv_mid < 0:
            high = mid
        else:
            low = mid
            npv_low = npv_mid
    return (low + high) / 2


def compute_projection(params: ProjectionParams) -> ProjectionResult:
    """Compute DCF projection and return metrics."""
    equity = params.purchase_price * (1 - params.ltv)
    loan = params.purchase_price * params.ltv
    total_cost = params.purchase_price + params.closing_costs + params.acquisition_fee

    # Annual interest rate
    interest_rate = params.sofr_rate + params.spread

    # Compute annual debt service (interest-only for IO periods, then amortizing)
    def _debt_service(period: int) -> float:
        if loan == 0:
            return 0.0
        if period <= params.interest_only_years:
            return loan * interest_rate
        # Amortizing payment for remaining term
        remaining_term = params.loan_term - params.interest_only_years
        if remaining_term <= 0 or interest_rate == 0:
            return loan / params.loan_term
        r = interest_rate
        n = remaining_term
        return loan * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    def _remaining_balance(period: int) -> float:
        if loan == 0:
            return 0.0
        if period <= params.interest_only_years:
            return loan
        amort_periods = period - params.interest_only_years
        remaining_term = params.loan_term - params.interest_only_years
        if remaining_term <= 0 or interest_rate == 0:
            return max(0.0, loan - loan * amort_periods / params.loan_term)
        r = interest_rate
        n = remaining_term
        return loan * ((1 + r) ** n - (1 + r) ** amort_periods) / ((1 + r) ** n - 1)

    # Build cash flows: t=0 is equity outflow
    cash_flows: list[float] = [-equity]
    period_nois: list[float] = []

    for t in range(1, params.periods + 1):
        rev = _apply_forecast(
            params.base_gross_revenue, t,
            params.revenue_forecast_method, params.revenue_forecast_params
        )
        occ = params.base_occupancy_rate  # occupancy flat for now
        egi = rev * occ
        exp_ratio = _apply_forecast(
            params.base_expense_ratio, t,
            params.expense_forecast_method, params.expense_forecast_params
        )
        opex = egi * exp_ratio
        capex = params.base_capex_per_unit  # already per-unit total
        noi = egi - opex - capex
        period_nois.append(noi)
        ds = _debt_service(t)
        net_cf = noi - ds
        cash_flows.append(net_cf)

    # Terminal cash flow in final period
    final_noi = period_nois[-1] if period_nois else 0.0
    exit_value = final_noi / params.exit_cap_rate if params.exit_cap_rate > 0 else 0.0
    remaining_bal = _remaining_balance(params.periods)
    terminal_cf = exit_value - remaining_bal
    cash_flows[-1] += terminal_cf

    # Metrics
    yr1_noi = period_nois[0] if period_nois else 0.0
    cap_rate_on_cost = yr1_noi / total_cost if total_cost > 0 else 0.0
    yr1_net_cf = cash_flows[1] if len(cash_flows) > 1 else 0.0
    coc_yr1 = yr1_net_cf / equity if equity > 0 else 0.0
    total_distributions = sum(cash_flows[1:])
    equity_multiple = total_distributions / equity if equity > 0 else 0.0
    irr = _bisect_irr(cash_flows)

    return ProjectionResult(
        irr=irr,
        equity_multiple=equity_multiple,
        cash_on_cash_yr1=coc_yr1,
        cap_rate_on_cost=cap_rate_on_cost,
        cash_flows=cash_flows,
    )
```

**Step 5: Run tests**

```bash
cd backend && python -m pytest tests/test_dcf.py -v
```
Expected: all pass.

**Step 6: Run full suite**

```bash
cd backend && python -m pytest tests/ -v
```

**Step 7: Commit**

```bash
git add backend/app/domain/services/__init__.py \
        backend/app/domain/services/dcf.py \
        backend/tests/test_dcf.py
git commit -m "feat: add pure-Python DCF engine with IRR bisection"
```

---

## Task 9: `FinancialModelService` with sensitivity support

**Files:**
- Create: `backend/app/services/financial_model_service.py`
- Create: `backend/tests/test_financial_model_service.py`

**Step 1: Write the failing test**

Create `backend/tests/test_financial_model_service.py`:

```python
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import date
from app.domain.entities.assumption import Assumption
from app.domain.value_objects.enums import AssumptionGroup, SourceType
from app.services.financial_model_service import FinancialModelService


def make_assumptions(set_id):
    """Minimal assumption set covering all required keys."""
    defs = [
        ("start_date", None, AssumptionGroup.MODEL_STRUCTURE),  # stored as notes
        ("projection_periods", 5, AssumptionGroup.MODEL_STRUCTURE),
        ("purchase_price", 1_000_000, AssumptionGroup.TRANSACTION),
        ("ltv", 0.70, AssumptionGroup.TRANSACTION),
        ("closing_costs", 0.0, AssumptionGroup.TRANSACTION),
        ("acquisition_fee", 0.0, AssumptionGroup.TRANSACTION),
        ("base_gross_revenue", 100_000, AssumptionGroup.OPERATING),
        ("base_occupancy_rate", 1.0, AssumptionGroup.OPERATING),
        ("base_expense_ratio", 0.40, AssumptionGroup.OPERATING),
        ("base_capex_per_unit", 0.0, AssumptionGroup.OPERATING),
        ("sofr_rate", 0.04, AssumptionGroup.FINANCING),
        ("spread", 0.01, AssumptionGroup.FINANCING),
        ("loan_term", 30, AssumptionGroup.FINANCING),
        ("interest_only_years", 5, AssumptionGroup.FINANCING),
        ("exit_cap_rate", 0.06, AssumptionGroup.RETURN_TARGETS),
    ]
    return [
        Assumption(set_id=set_id, key=key, value_number=val, group=grp)
        for key, val, grp in defs
    ]


@pytest.mark.asyncio
async def test_compute_returns_projection_result():
    set_id = uuid4()
    assumption_repo = AsyncMock()
    assumption_repo.get_by_set_id.return_value = make_assumptions(set_id)

    svc = FinancialModelService(assumption_repo)
    result = await svc.compute(set_id)

    assert result.irr is not None
    assert result.equity_multiple > 1.0
    assert result.cap_rate_on_cost == pytest.approx(0.06, abs=0.001)


@pytest.mark.asyncio
async def test_compute_sensitivity_returns_grid():
    set_id = uuid4()
    assumption_repo = AsyncMock()
    assumption_repo.get_by_set_id.return_value = make_assumptions(set_id)

    svc = FinancialModelService(assumption_repo)
    grids = await svc.compute_sensitivity(
        set_id,
        x_axis={"key": "purchase_price", "values": [900_000, 1_000_000, 1_100_000]},
        y_axis={"key": "exit_cap_rate", "values": [0.055, 0.060, 0.065]},
        metrics=["irr", "equity_multiple"],
    )

    assert "irr" in grids
    assert "equity_multiple" in grids
    assert len(grids["irr"]) == 3   # 3 y values
    assert len(grids["irr"][0]) == 3  # 3 x values
```

**Step 2: Run to confirm fail**

```bash
cd backend && python -m pytest tests/test_financial_model_service.py -v
```

**Step 3: Implement**

Create `backend/app/services/financial_model_service.py`:

```python
from __future__ import annotations
from datetime import date
from uuid import UUID
from app.domain.interfaces.repositories import AssumptionRepository
from app.domain.services.dcf import ProjectionParams, ProjectionResult, compute_projection


_REQUIRED_KEYS = {
    "projection_periods", "purchase_price", "ltv", "closing_costs",
    "acquisition_fee", "base_gross_revenue", "base_occupancy_rate",
    "base_expense_ratio", "base_capex_per_unit", "sofr_rate", "spread",
    "loan_term", "interest_only_years", "exit_cap_rate",
}


class FinancialModelService:
    def __init__(self, assumption_repo: AssumptionRepository) -> None:
        self._assumption_repo = assumption_repo

    async def _load_params(
        self, set_id: UUID, overrides: dict | None = None
    ) -> ProjectionParams:
        assumptions = await self._assumption_repo.get_by_set_id(set_id)
        vals: dict = {a.key: a.value_number for a in assumptions if a.value_number is not None}
        forecast: dict = {
            a.key: (a.forecast_method, a.forecast_params or {})
            for a in assumptions
            if a.forecast_method
        }
        if overrides:
            vals.update(overrides)

        def v(key: str, default: float = 0.0) -> float:
            return float(vals.get(key, default))

        def fm(key: str) -> tuple[str, dict]:
            return forecast.get(key, ("historical", {}))

        rev_method, rev_params = fm("base_gross_revenue")
        exp_method, exp_params = fm("base_expense_ratio")

        return ProjectionParams(
            start_date=date.today(),
            periods=int(v("projection_periods", 5)),
            cadence="annual",
            purchase_price=v("purchase_price"),
            ltv=v("ltv", 0.70),
            closing_costs=v("closing_costs"),
            acquisition_fee=v("acquisition_fee"),
            base_gross_revenue=v("base_gross_revenue"),
            base_occupancy_rate=v("base_occupancy_rate", 1.0),
            base_expense_ratio=v("base_expense_ratio", 0.40),
            base_capex_per_unit=v("base_capex_per_unit"),
            revenue_forecast_method=rev_method,
            revenue_forecast_params=rev_params,
            expense_forecast_method=exp_method,
            expense_forecast_params=exp_params,
            sofr_rate=v("sofr_rate", 0.04),
            spread=v("spread", 0.01),
            loan_term=int(v("loan_term", 30)),
            interest_only_years=int(v("interest_only_years", 0)),
            exit_cap_rate=v("exit_cap_rate", 0.06),
        )

    async def compute(self, set_id: UUID) -> ProjectionResult:
        params = await self._load_params(set_id)
        return compute_projection(params)

    async def compute_sensitivity(
        self,
        set_id: UUID,
        x_axis: dict,         # {"key": str, "values": list[float]}
        y_axis: dict,         # {"key": str, "values": list[float]}
        metrics: list[str],
    ) -> dict[str, list[list[float | None]]]:
        """Returns {metric: [[val_per_x_for_y0], [val_per_x_for_y1], ...]}"""
        grids: dict[str, list[list[float | None]]] = {m: [] for m in metrics}

        for y_val in y_axis["values"]:
            row: dict[str, list[float | None]] = {m: [] for m in metrics}
            for x_val in x_axis["values"]:
                overrides = {x_axis["key"]: x_val, y_axis["key"]: y_val}
                params = await self._load_params(set_id, overrides)
                result = compute_projection(params)
                for metric in metrics:
                    row[metric].append(getattr(result, metric, None))
            for metric in metrics:
                grids[metric].append(row[metric])

        return grids
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_financial_model_service.py tests/test_dcf.py -v
```
Expected: all pass.

**Step 5: Run full suite**

```bash
cd backend && python -m pytest tests/ -v
```

**Step 6: Commit**

```bash
git add backend/app/services/financial_model_service.py \
        backend/tests/test_financial_model_service.py
git commit -m "feat: add FinancialModelService with compute and sensitivity"
```

---

## Task 10: Financial model and sensitivity API routes

**Files:**
- Create: `backend/app/api/v1/financial_model.py`
- Modify: `backend/app/api/schemas.py`
- Modify: `backend/app/api/dependencies.py`
- Modify: `backend/app/main.py`

**Step 1: Add schemas**

In `backend/app/api/schemas.py`, add:

```python
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
    # metric_name -> list[list[float | None]]
    grids: dict[str, list[list[float | None]]]
    x_axis: SensitivityAxisRequest
    y_axis: SensitivityAxisRequest
```

**Step 2: Create route file**

Create `backend/app/api/v1/financial_model.py`:

```python
from __future__ import annotations
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import get_financial_model_service, get_assumption_set_repo
from app.api.schemas import ProjectionResultResponse, SensitivityRequest, SensitivityResponse
from app.services.financial_model_service import FinancialModelService

router = APIRouter(tags=["financial_model"])


async def _resolve_set_id(
    deal_id: UUID,
    assumption_set_repo,
) -> UUID:
    sets = await assumption_set_repo.get_by_deal_id(deal_id)
    if not sets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assumption set found for this deal",
        )
    return sets[0].id


@router.post(
    "/deals/{deal_id}/financial-model:compute",
    response_model=ProjectionResultResponse,
)
async def compute_financial_model(
    deal_id: UUID,
    service: Annotated[FinancialModelService, Depends(get_financial_model_service)],
    assumption_set_repo=Depends(get_assumption_set_repo),
) -> ProjectionResultResponse:
    set_id = await _resolve_set_id(deal_id, assumption_set_repo)
    result = await service.compute(set_id)
    return ProjectionResultResponse(
        irr=result.irr,
        equity_multiple=result.equity_multiple,
        cash_on_cash_yr1=result.cash_on_cash_yr1,
        cap_rate_on_cost=result.cap_rate_on_cost,
        cash_flows=result.cash_flows,
    )


@router.post(
    "/deals/{deal_id}/sensitivity",
    response_model=SensitivityResponse,
)
async def compute_sensitivity(
    deal_id: UUID,
    body: SensitivityRequest,
    service: Annotated[FinancialModelService, Depends(get_financial_model_service)],
    assumption_set_repo=Depends(get_assumption_set_repo),
) -> SensitivityResponse:
    set_id = await _resolve_set_id(deal_id, assumption_set_repo)
    grids = await service.compute_sensitivity(
        set_id,
        x_axis={"key": body.x_axis.key, "values": body.x_axis.values},
        y_axis={"key": body.y_axis.key, "values": body.y_axis.values},
        metrics=body.metrics,
    )
    return SensitivityResponse(grids=grids, x_axis=body.x_axis, y_axis=body.y_axis)
```

**Step 3: Wire DI**

In `backend/app/api/dependencies.py`:

```python
from app.services.financial_model_service import FinancialModelService

def get_financial_model_service(
    assumption_repo: Annotated[SqlAlchemyAssumptionRepository, Depends(get_assumption_repo)],
) -> FinancialModelService:
    return FinancialModelService(assumption_repo=assumption_repo)
```

**Step 4: Register router**

In `backend/app/main.py`:

```python
from app.api.v1.financial_model import router as financial_model_router
app.include_router(financial_model_router, prefix="/v1")
```

**Step 5: Run all tests**

```bash
cd backend && python -m pytest tests/ -v
```

**Step 6: Commit**

```bash
git add backend/app/api/v1/financial_model.py \
        backend/app/api/schemas.py \
        backend/app/api/dependencies.py \
        backend/app/main.py
git commit -m "feat: add financial model compute and sensitivity API routes"
```

---

## Task 11: Frontend — update TypeScript interfaces and services

**Files:**
- Modify: `frontend/src/interfaces/api.ts`
- Create: `frontend/src/services/historical-financial.service.ts`
- Create: `frontend/src/services/financial-model.service.ts`

**Step 1: Add types to `api.ts`**

Open `frontend/src/interfaces/api.ts`. Add the following types (follow the existing style in that file):

```typescript
export interface HistoricalFinancial {
  id: string;
  deal_id: string;
  period_label: string;
  metric_key: string;
  value: number;
  unit: string | null;
  source: string;
  created_at: string;
}

export interface ProjectionResult {
  irr: number | null;
  equity_multiple: number;
  cash_on_cash_yr1: number;
  cap_rate_on_cost: number;
  cash_flows: number[];
}

export interface SensitivityAxis {
  key: string;
  values: number[];
}

export interface SensitivityRequest {
  x_axis: SensitivityAxis;
  y_axis: SensitivityAxis;
  metrics?: string[];
}

export interface SensitivityResponse {
  grids: Record<string, (number | null)[][]>;
  x_axis: SensitivityAxis;
  y_axis: SensitivityAxis;
}
```

Also update the `Assumption` interface to add the three new fields:
```typescript
group: string | null;
forecast_method: string | null;
forecast_params: Record<string, unknown> | null;
```

**Step 2: Create historical financial service**

Create `frontend/src/services/historical-financial.service.ts`:

```typescript
import { apiFetch } from "./api-client";
import type { HistoricalFinancial } from "@/interfaces/api";

export const historicalFinancialService = {
  list: (dealId: string): Promise<HistoricalFinancial[]> =>
    apiFetch<HistoricalFinancial[]>(`/deals/${dealId}/historical-financials`),

  extract: (dealId: string, documentId: string): Promise<HistoricalFinancial[]> =>
    apiFetch<HistoricalFinancial[]>(
      `/deals/${dealId}/documents/${documentId}/historical-financials:extract`,
      { method: "POST" }
    ),
};
```

**Step 3: Create financial model service**

Create `frontend/src/services/financial-model.service.ts`:

```typescript
import { apiFetch } from "./api-client";
import type {
  ProjectionResult,
  SensitivityRequest,
  SensitivityResponse,
} from "@/interfaces/api";

export const financialModelService = {
  compute: (dealId: string): Promise<ProjectionResult> =>
    apiFetch<ProjectionResult>(`/deals/${dealId}/financial-model:compute`, {
      method: "POST",
    }),

  sensitivity: (dealId: string, body: SensitivityRequest): Promise<SensitivityResponse> =>
    apiFetch<SensitivityResponse>(`/deals/${dealId}/sensitivity`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
```

**Step 4: Build check**

```bash
cd frontend && npm run build 2>&1 | tail -20
```
Expected: no TypeScript errors.

**Step 5: Commit**

```bash
git add frontend/src/interfaces/api.ts \
        frontend/src/services/historical-financial.service.ts \
        frontend/src/services/financial-model.service.ts
git commit -m "feat: add HistoricalFinancial, ProjectionResult, Sensitivity TS types and services"
```

---

## Task 12: Frontend — `AssumptionPanel` (grouped, editable)

**Files:**
- Create: `frontend/src/components/assumptions/assumption-panel.tsx`
- Modify: deal workspace page (wherever `AssumptionEditor` is currently rendered)

**Step 1: Find where AssumptionEditor is rendered**

Search:
```bash
grep -r "AssumptionEditor" frontend/src --include="*.tsx" -l
```

**Step 2: Create `AssumptionPanel`**

Create `frontend/src/components/assumptions/assumption-panel.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Assumption } from "@/interfaces/api";

const GROUPS = [
  { key: "model_structure", label: "Model Structure" },
  { key: "transaction", label: "Transaction" },
  { key: "operating", label: "Operating" },
  { key: "financing", label: "Financing" },
  { key: "return_targets", label: "Return Targets" },
] as const;

const FORECAST_METHODS = [
  { value: "historical", label: "In-line with historicals" },
  { value: "step_change", label: "Step change" },
  { value: "gradual_ramp", label: "Gradual ramp to target" },
];

interface AssumptionPanelProps {
  assumptions: Assumption[];
  onUpdate?: (key: string, value: number | null) => void;
}

export function AssumptionPanel({ assumptions, onUpdate }: AssumptionPanelProps) {
  const [expanded, setExpanded] = useState<Set<string>>(
    new Set(["model_structure", "transaction", "operating", "financing", "return_targets"])
  );

  function toggle(key: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  if (assumptions.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No assumptions yet. AI benchmarks will be generated automatically after
        document processing completes.
      </p>
    );
  }

  const ungrouped = assumptions.filter((a) => !a.group);
  const grouped = GROUPS.map((g) => ({
    ...g,
    items: assumptions.filter((a) => a.group === g.key),
  }));

  return (
    <div className="space-y-3">
      {grouped.map((group) => {
        if (group.items.length === 0) return null;
        const isOpen = expanded.has(group.key);
        return (
          <div key={group.key} className="border rounded-lg overflow-hidden">
            <button
              type="button"
              className="w-full flex items-center justify-between px-4 py-2 bg-muted/40 hover:bg-muted/70 text-sm font-medium"
              onClick={() => toggle(group.key)}
            >
              <span>{group.label}</span>
              <span className="text-muted-foreground">{isOpen ? "▲" : "▼"}</span>
            </button>
            {isOpen && (
              <div className="divide-y">
                {group.items.map((a) => (
                  <AssumptionRow key={a.id} assumption={a} onUpdate={onUpdate} />
                ))}
              </div>
            )}
          </div>
        );
      })}

      {ungrouped.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <button
            type="button"
            className="w-full flex items-center justify-between px-4 py-2 bg-muted/40 hover:bg-muted/70 text-sm font-medium"
            onClick={() => toggle("_other")}
          >
            <span>Other</span>
            <span className="text-muted-foreground">{expanded.has("_other") ? "▲" : "▼"}</span>
          </button>
          {expanded.has("_other") && (
            <div className="divide-y">
              {ungrouped.map((a) => (
                <AssumptionRow key={a.id} assumption={a} onUpdate={onUpdate} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AssumptionRow({
  assumption: a,
  onUpdate,
}: {
  assumption: Assumption;
  onUpdate?: (key: string, value: number | null) => void;
}) {
  const isOperating = a.group === "operating";

  return (
    <div className="px-4 py-2 flex items-start gap-3 text-sm">
      <div className="flex-1 min-w-0">
        <div className="font-medium text-xs text-muted-foreground uppercase tracking-wide mb-1">
          {a.key}
        </div>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            className="h-7 w-32 text-sm"
            defaultValue={a.value_number ?? ""}
            onBlur={(e) => onUpdate?.(a.key, e.target.value ? Number(e.target.value) : null)}
          />
          {a.unit && <span className="text-muted-foreground text-xs">{a.unit}</span>}
        </div>
      </div>
      {isOperating && (
        <div className="flex-1 min-w-0">
          <div className="text-xs text-muted-foreground mb-1">Forecast</div>
          <Select defaultValue={a.forecast_method ?? "historical"}>
            <SelectTrigger className="h-7 text-xs w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {FORECAST_METHODS.map((m) => (
                <SelectItem key={m.value} value={m.value} className="text-xs">
                  {m.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
      <div className="flex items-center pt-5">
        <SourceBadge sourceType={a.source_type} />
      </div>
    </div>
  );
}

function SourceBadge({ sourceType }: { sourceType: string }) {
  switch (sourceType.toLowerCase()) {
    case "extracted":
      return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">Extracted</Badge>;
    case "benchmark":
      return <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100">Benchmark</Badge>;
    default:
      return <Badge variant="outline">{sourceType}</Badge>;
  }
}
```

**Step 3: Replace `AssumptionEditor` with `AssumptionPanel`**

In the deal workspace file (found in Step 1), swap the import and component usage:

```tsx
// Replace:
import { AssumptionEditor } from "@/components/assumptions/assumption-editor";
// With:
import { AssumptionPanel } from "@/components/assumptions/assumption-panel";

// Replace:
<AssumptionEditor assumptions={assumptions} />
// With:
<AssumptionPanel assumptions={assumptions} />
```

**Step 4: Build check**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

**Step 5: Commit**

```bash
git add frontend/src/components/assumptions/assumption-panel.tsx \
        # + whichever workspace file was modified
git commit -m "feat: add AssumptionPanel with grouped collapsible sections and editable fields"
```

---

## Task 13: Frontend — `HistoricalFinancialsTab`

**Files:**
- Create: `frontend/src/components/historical/historical-financials-tab.tsx`

**Step 1: Create the component**

Create `frontend/src/components/historical/historical-financials-tab.tsx`:

```tsx
"use client";

import type { HistoricalFinancial } from "@/interfaces/api";

const METRIC_LABELS: Record<string, string> = {
  gross_revenue: "Gross Revenue",
  effective_gross_income: "Effective Gross Income",
  total_operating_expenses: "Total OpEx",
  noi: "NOI",
  expense_ratio: "Expense Ratio",
  occupancy_rate: "Occupancy Rate",
  revenue_per_unit: "Revenue / Unit",
  opex_per_unit: "OpEx / Unit",
  total_units: "Total Units",
  net_rentable_area: "Net Rentable Area",
};

function formatValue(value: number, unit: string | null): string {
  if (unit === "%" || unit === "%" ) {
    return `${(value * 100).toFixed(1)}%`;
  }
  if (unit === "$") {
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
    if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
    return `$${value.toFixed(0)}`;
  }
  return `${value.toLocaleString()}${unit ? ` ${unit}` : ""}`;
}

function trendArrow(values: number[]): string {
  if (values.length < 2) return "";
  const delta = values[values.length - 1] - values[0];
  if (delta > 0) return " ↑";
  if (delta < 0) return " ↓";
  return " →";
}

interface HistoricalFinancialsTabProps {
  items: HistoricalFinancial[];
}

export function HistoricalFinancialsTab({ items }: HistoricalFinancialsTabProps) {
  if (items.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No historical financials extracted yet.
      </p>
    );
  }

  // Collect unique periods (sorted) and unique metric keys
  const periods = [...new Set(items.map((i) => i.period_label))].sort();
  const metrics = [...new Set(items.map((i) => i.metric_key))];

  // Build lookup: metric_key -> period_label -> item
  const lookup: Record<string, Record<string, HistoricalFinancial>> = {};
  for (const item of items) {
    lookup[item.metric_key] ??= {};
    lookup[item.metric_key][item.period_label] = item;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left p-2 font-medium w-48">Metric</th>
            {periods.map((p) => (
              <th key={p} className="text-right p-2 font-medium">{p}</th>
            ))}
            <th className="text-right p-2 font-medium w-8">Trend</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => {
            const row = lookup[metric] ?? {};
            const values = periods
              .map((p) => row[p]?.value)
              .filter((v): v is number => v !== undefined);
            const firstItem = Object.values(row)[0];
            return (
              <tr key={metric} className="border-b hover:bg-muted/30">
                <td className="p-2 font-medium">
                  {METRIC_LABELS[metric] ?? metric}
                </td>
                {periods.map((p) => {
                  const item = row[p];
                  return (
                    <td key={p} className="p-2 text-right tabular-nums">
                      {item ? formatValue(item.value, item.unit) : "—"}
                    </td>
                  );
                })}
                <td className="p-2 text-right text-muted-foreground">
                  {trendArrow(values)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
```

**Step 2: Build check**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

**Step 3: Commit**

```bash
git add frontend/src/components/historical/historical-financials-tab.tsx
git commit -m "feat: add HistoricalFinancialsTab component"
```

---

## Task 14: Frontend — `SensitivityTab`

**Files:**
- Create: `frontend/src/components/sensitivity/sensitivity-table.tsx`
- Create: `frontend/src/components/sensitivity/sensitivity-tab.tsx`

**Step 1: Create `SensitivityTable`**

Create `frontend/src/components/sensitivity/sensitivity-table.tsx`:

```tsx
"use client";

import type { SensitivityResponse } from "@/interfaces/api";

const METRIC_LABELS: Record<string, string> = {
  irr: "IRR",
  equity_multiple: "Equity Multiple",
  cash_on_cash_yr1: "Cash-on-Cash (Yr 1)",
  cap_rate_on_cost: "Cap Rate on Cost",
};

const AXIS_LABELS: Record<string, string> = {
  purchase_price: "Purchase Price",
  exit_cap_rate: "Exit Cap Rate",
  ltv: "LTV",
  occupancy_rate: "Occupancy Rate",
  base_gross_revenue: "Gross Revenue",
  sofr_rate: "SOFR Rate",
  spread: "Spread",
};

function formatCell(metric: string, value: number | null): string {
  if (value === null || value === undefined) return "—";
  if (metric === "irr" || metric === "cash_on_cash_yr1" || metric === "cap_rate_on_cost") {
    return `${(value * 100).toFixed(2)}%`;
  }
  if (metric === "equity_multiple") {
    return `${value.toFixed(2)}x`;
  }
  return value.toFixed(2);
}

function cellColor(metric: string, value: number | null, target: number | null): string {
  if (value === null || target === null) return "";
  const meets =
    metric === "equity_multiple" || metric === "irr" || metric === "cash_on_cash_yr1"
      ? value >= target
      : value >= target;
  return meets ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700";
}

interface SensitivityTableProps {
  metric: string;
  response: SensitivityResponse;
  target?: number | null;
}

export function SensitivityTable({ metric, response, target }: SensitivityTableProps) {
  const grid = response.grids[metric];
  if (!grid) return null;

  const xVals = response.x_axis.values;
  const yVals = response.y_axis.values;
  const xLabel = AXIS_LABELS[response.x_axis.key] ?? response.x_axis.key;
  const yLabel = AXIS_LABELS[response.y_axis.key] ?? response.y_axis.key;

  return (
    <div>
      <h3 className="text-sm font-semibold mb-2">{METRIC_LABELS[metric] ?? metric}</h3>
      <div className="overflow-x-auto">
        <table className="text-xs border-collapse">
          <thead>
            <tr>
              <th className="border p-1 bg-muted text-left font-medium min-w-24">
                {yLabel} \ {xLabel}
              </th>
              {xVals.map((x) => (
                <th key={x} className="border p-1 bg-muted text-right font-medium min-w-20">
                  {x.toLocaleString()}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {yVals.map((y, yi) => (
              <tr key={y}>
                <td className="border p-1 bg-muted font-medium text-right">{y.toLocaleString()}</td>
                {(grid[yi] ?? []).map((val, xi) => (
                  <td
                    key={xi}
                    className={`border p-1 text-right tabular-nums ${cellColor(metric, val, target ?? null)}`}
                  >
                    {formatCell(metric, val)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

**Step 2: Create `SensitivityTab`**

Create `frontend/src/components/sensitivity/sensitivity-tab.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { SensitivityTable } from "./sensitivity-table";
import { financialModelService } from "@/services/financial-model.service";
import type { SensitivityResponse } from "@/interfaces/api";

const DEFAULT_CONFIGS = [
  {
    metrics: ["irr", "equity_multiple"] as const,
    x_axis: { key: "purchase_price", values: [900_000, 950_000, 1_000_000, 1_050_000, 1_100_000] },
    y_axis: { key: "exit_cap_rate", values: [0.05, 0.055, 0.06, 0.065, 0.07] },
  },
  {
    metrics: ["cash_on_cash_yr1", "cap_rate_on_cost"] as const,
    x_axis: { key: "base_gross_revenue", values: [85_000, 92_500, 100_000, 107_500, 115_000] },
    y_axis: { key: "sofr_rate", values: [0.03, 0.04, 0.05, 0.06] },
  },
];

interface SensitivityTabProps {
  dealId: string;
}

export function SensitivityTab({ dealId }: SensitivityTabProps) {
  const [results, setResults] = useState<SensitivityResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function recalculate() {
    setLoading(true);
    setError(null);
    try {
      const responses = await Promise.all(
        DEFAULT_CONFIGS.map((cfg) =>
          financialModelService.sensitivity(dealId, {
            x_axis: cfg.x_axis,
            y_axis: cfg.y_axis,
            metrics: [...cfg.metrics],
          })
        )
      );
      setResults(responses);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to compute sensitivity");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Two-way sensitivity tables. Cells turn green when the return meets or exceeds your target.
        </p>
        <Button size="sm" onClick={recalculate} disabled={loading}>
          {loading ? "Calculating..." : "Recalculate"}
        </Button>
      </div>

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      {results.length === 0 && !loading && (
        <p className="text-sm text-muted-foreground">
          Click Recalculate to generate sensitivity tables.
        </p>
      )}

      {results.map((response, i) => (
        <div key={i} className="space-y-4 border rounded-lg p-4">
          {DEFAULT_CONFIGS[i].metrics.map((metric) => (
            <SensitivityTable key={metric} metric={metric} response={response} />
          ))}
        </div>
      ))}
    </div>
  );
}
```

**Step 3: Build check**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

**Step 4: Commit**

```bash
git add frontend/src/components/sensitivity/sensitivity-table.tsx \
        frontend/src/components/sensitivity/sensitivity-tab.tsx
git commit -m "feat: add SensitivityTable and SensitivityTab components"
```

---

## Task 15: Wire new tabs into the deal workspace

**Files:**
- Modify: `frontend/src/app/deals/[id]/page.tsx` (or wherever the tab layout lives — search for `TabsList` or `Tabs`)
- Modify: `frontend/src/hooks/useDeal.ts` (add historical financials fetch)

**Step 1: Find the workspace file**

```bash
grep -r "TabsList\|TabsContent" frontend/src --include="*.tsx" -l
```

**Step 2: Update `useDeal` hook**

Open `frontend/src/hooks/useDeal.ts`. Add a parallel fetch for historical financials alongside the existing fetches:

```typescript
import { historicalFinancialService } from "@/services/historical-financial.service";
// In the hook's parallel fetch:
const historicalFinancials = await historicalFinancialService.list(dealId);
// Return it in the hook's return value
```

**Step 3: Update tab layout in workspace**

In the deal workspace page, add three new tabs. The new tab order is:

```
Extraction | Historical Financials | Assumptions | Validation | Comps | Sensitivity
```

Add tab triggers:
```tsx
<TabsTrigger value="historical">Historical Financials</TabsTrigger>
<TabsTrigger value="sensitivity">Sensitivity</TabsTrigger>
```

Add tab content panels, importing the new components:
```tsx
import { HistoricalFinancialsTab } from "@/components/historical/historical-financials-tab";
import { SensitivityTab } from "@/components/sensitivity/sensitivity-tab";

// In the JSX:
<TabsContent value="historical">
  <HistoricalFinancialsTab items={historicalFinancials} />
</TabsContent>

<TabsContent value="sensitivity">
  <SensitivityTab dealId={deal.id} />
</TabsContent>
```

**Step 4: Export gating**

Find where the export button is rendered. Add a disabled check:

```tsx
const allGroupsFilled = ["model_structure", "transaction", "operating", "financing", "return_targets"]
  .every((group) => assumptions.some((a) => a.group === group && a.value_number !== null));

// On the button:
<Button disabled={!allGroupsFilled} title={!allGroupsFilled ? "Fill all assumption groups before exporting" : undefined}>
  Export XLSX
</Button>
```

**Step 5: Build check**

```bash
cd frontend && npm run build 2>&1 | tail -20
```
Expected: no TypeScript errors.

**Step 6: Run backend tests one final time**

```bash
cd backend && python -m pytest tests/ -v
```

**Step 7: Commit**

```bash
git add frontend/src/app/deals/ frontend/src/hooks/
git commit -m "feat: wire Historical Financials and Sensitivity tabs into deal workspace, add export gating"
```

---

## Done

All backend tests should pass. All frontend builds should succeed. The deal workspace now has:

- Structured, editable assumption groups (Model / Transaction / Operating / Financing / Return Targets)
- Historical Financials tab with data extracted from the OM by GPT-4o
- A DCF engine computing IRR, equity multiple, cash-on-cash, cap rate on cost
- Sensitivity tab with two pre-configured two-way tables, recalculate on demand
- Export button disabled until all assumption groups are populated
