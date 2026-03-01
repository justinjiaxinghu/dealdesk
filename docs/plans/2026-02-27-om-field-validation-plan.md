# OM Field Validation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Validate OM financial metrics against real market data using GPT-4o with Tavily web search, producing per-field status flags with cited sources.

**Architecture:** New `ValidationService` orchestrates the flow: fetch deal + extracted fields + benchmarks, call `LLMProvider.validate_om_fields()` which uses GPT-4o tool calling with a Tavily-backed `web_search` tool, persist results as `FieldValidation` entities. Frontend gets a new Validation tab and pipeline step.

**Tech Stack:** Tavily Python SDK (`tavily-python`), OpenAI tool calling (already have `openai>=1.60.0`), new SQLAlchemy model, new React component.

---

### Task 1: Add Tavily dependency and config

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/config.py`

**Step 1: Add tavily-python to dependencies**

In `backend/pyproject.toml`, add to the `dependencies` array:

```toml
    "tavily-python>=0.5.0",
```

**Step 2: Add Tavily API key to config**

In `backend/app/config.py`, add to the `Settings` class:

```python
    tavily_api_key: str = ""
```

**Step 3: Install**

Run: `cd backend && pip install -e ".[dev]"`
Expected: Installs successfully with tavily-python

**Step 4: Commit**

```bash
git add backend/pyproject.toml backend/app/config.py
git commit -m "chore: add tavily-python dependency and config"
```

---

### Task 2: Add ValidationStatus enum and FieldValidationResult value object

**Files:**
- Modify: `backend/app/domain/value_objects/enums.py` (after `ExportType` at line 46)
- Modify: `backend/app/domain/value_objects/types.py` (after `DealFilters` at line 77)
- Modify: `backend/app/domain/value_objects/__init__.py`

**Step 1: Add ValidationStatus enum**

In `backend/app/domain/value_objects/enums.py`, add after `ExportType`:

```python
class ValidationStatus(StrEnum):
    WITHIN_RANGE = "within_range"
    ABOVE_MARKET = "above_market"
    BELOW_MARKET = "below_market"
    SUSPICIOUS = "suspicious"
    INSUFFICIENT_DATA = "insufficient_data"
```

**Step 2: Add FieldValidationResult value object**

In `backend/app/domain/value_objects/types.py`, add after `DealFilters`:

```python
@dataclass(frozen=True)
class ValidationSource:
    url: str
    title: str
    snippet: str


@dataclass(frozen=True)
class FieldValidationResult:
    field_key: str
    om_value: float | None
    market_value: float | None
    status: str
    explanation: str
    sources: list[ValidationSource]
    confidence: float
```

**Step 3: Export from `__init__.py`**

In `backend/app/domain/value_objects/__init__.py`, add imports for `ValidationStatus`, `FieldValidationResult`, `ValidationSource`.

**Step 4: Commit**

```bash
git add backend/app/domain/value_objects/
git commit -m "feat: add ValidationStatus enum and FieldValidationResult value object"
```

---

### Task 3: Add FieldValidation domain entity

**Files:**
- Create: `backend/app/domain/entities/field_validation.py`
- Modify: `backend/app/domain/entities/__init__.py`

**Step 1: Create the entity**

Create `backend/app/domain/entities/field_validation.py`:

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import ValidationStatus


@dataclass
class FieldValidation:
    deal_id: UUID
    field_key: str
    id: UUID = field(default_factory=uuid4)
    om_value: float | None = None
    market_value: float | None = None
    status: ValidationStatus = ValidationStatus.INSUFFICIENT_DATA
    explanation: str = ""
    sources: list[dict] = field(default_factory=list)
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Step 2: Export from `__init__.py`**

In `backend/app/domain/entities/__init__.py`, add:

```python
from app.domain.entities.field_validation import FieldValidation
```

And add `"FieldValidation"` to `__all__`.

**Step 3: Commit**

```bash
git add backend/app/domain/entities/
git commit -m "feat: add FieldValidation domain entity"
```

---

### Task 4: Add FieldValidation ORM model and mapper

**Files:**
- Modify: `backend/app/infrastructure/persistence/models.py` (after `ExportModel`)
- Modify: `backend/app/infrastructure/persistence/mappers.py` (after export mappers)

**Step 1: Add ORM model**

In `backend/app/infrastructure/persistence/models.py`, add after `ExportModel`:

```python
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
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    deal = relationship("DealModel", back_populates="field_validations")
```

Also add to `DealModel` relationships (after `exports`):

```python
    field_validations = relationship(
        "FieldValidationModel", back_populates="deal", lazy="selectin"
    )
```

**Step 2: Add mappers**

In `backend/app/infrastructure/persistence/mappers.py`, add:

```python
from app.domain.entities.field_validation import FieldValidation
from app.domain.value_objects.enums import ValidationStatus
from app.infrastructure.persistence.models import FieldValidationModel


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
```

**Step 3: Commit**

```bash
git add backend/app/infrastructure/persistence/models.py backend/app/infrastructure/persistence/mappers.py
git commit -m "feat: add FieldValidation ORM model and mappers"
```

---

### Task 5: Add FieldValidationRepository

**Files:**
- Modify: `backend/app/domain/interfaces/repositories.py` (after `ExportRepository`)
- Create: `backend/app/infrastructure/persistence/field_validation_repo.py`

**Step 1: Add repository ABC**

In `backend/app/domain/interfaces/repositories.py`, add import for `FieldValidation` and after `ExportRepository`:

```python
class FieldValidationRepository(ABC):
    @abstractmethod
    async def bulk_upsert(self, validations: list[FieldValidation]) -> list[FieldValidation]: ...

    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[FieldValidation]: ...
```

**Step 2: Create concrete repository**

Create `backend/app/infrastructure/persistence/field_validation_repo.py`:

```python
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.field_validation import FieldValidation
from app.infrastructure.persistence.mappers import (
    field_validation_to_entity,
    field_validation_to_model,
)
from app.infrastructure.persistence.models import FieldValidationModel


class SqlAlchemyFieldValidationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_upsert(
        self, validations: list[FieldValidation]
    ) -> list[FieldValidation]:
        results: list[FieldValidation] = []
        for v in validations:
            stmt = select(FieldValidationModel).where(
                FieldValidationModel.deal_id == v.deal_id,
                FieldValidationModel.field_key == v.field_key,
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.om_value = v.om_value
                existing.market_value = v.market_value
                existing.status = v.status.value
                existing.explanation = v.explanation
                existing.sources = v.sources
                existing.confidence = v.confidence
                existing.created_at = datetime.utcnow()
                await self._session.flush()
                await self._session.refresh(existing)
                results.append(field_validation_to_entity(existing))
            else:
                model = field_validation_to_model(v)
                self._session.add(model)
                await self._session.flush()
                await self._session.refresh(model)
                results.append(field_validation_to_entity(model))

        return results

    async def get_by_deal_id(self, deal_id: UUID) -> list[FieldValidation]:
        stmt = select(FieldValidationModel).where(
            FieldValidationModel.deal_id == deal_id
        )
        result = await self._session.execute(stmt)
        return [field_validation_to_entity(m) for m in result.scalars().all()]
```

**Step 3: Commit**

```bash
git add backend/app/domain/interfaces/repositories.py backend/app/infrastructure/persistence/field_validation_repo.py
git commit -m "feat: add FieldValidationRepository with bulk upsert"
```

---

### Task 6: Add `validate_om_fields` to LLMProvider interface and OpenAI implementation

**Files:**
- Modify: `backend/app/domain/interfaces/providers.py` (add abstract method after `quick_extract_deal_info`)
- Modify: `backend/app/infrastructure/llm/openai_provider.py` (add implementation)

**Step 1: Add abstract method to LLMProvider**

In `backend/app/domain/interfaces/providers.py`, add import for `FieldValidationResult` and after `quick_extract_deal_info`:

```python
    @abstractmethod
    async def validate_om_fields(
        self,
        deal: Deal,
        fields: list[ExtractedField],
        benchmarks: list[Assumption],
    ) -> list[FieldValidationResult]: ...
```

Also add necessary imports: `from app.domain.entities.extraction import ExtractedField` and `from app.domain.value_objects.types import FieldValidationResult, ValidationSource`.

**Step 2: Implement in OpenAI provider**

In `backend/app/infrastructure/llm/openai_provider.py`, add imports at the top:

```python
import asyncio
from tavily import AsyncTavilyClient
from app.config import settings
from app.domain.entities.assumption import Assumption
from app.domain.entities.deal import Deal
from app.domain.entities.extraction import ExtractedField
from app.domain.value_objects.types import FieldValidationResult, ValidationSource
```

Add to `__init__`:

```python
        self._tavily = AsyncTavilyClient(api_key=settings.tavily_api_key)
```

Add the implementation method:

```python
    async def validate_om_fields(
        self,
        deal: Deal,
        fields: list[ExtractedField],
        benchmarks: list[Assumption],
    ) -> list[FieldValidationResult]:
        # Build context for the LLM
        fields_text = "\n".join(
            f"  - {f.field_key}: {f.value_number} {f.unit or ''}"
            for f in fields
            if f.value_number is not None
        )
        benchmarks_text = "\n".join(
            f"  - {a.key}: {a.value_number} {a.unit or ''} (range: {a.range_min}-{a.range_max})"
            for a in benchmarks
        )

        system_prompt = (
            "You are a commercial real estate analyst validating an Offering Memorandum. "
            "You have access to a web_search tool to look up current market data. "
            "For each financial metric from the OM, research the local market, compare "
            "the OM value to what you find, and assess whether it is reasonable.\n\n"
            "You MUST cite your sources. Every claim about market data must reference "
            "a specific source from your web searches.\n\n"
            "Only validate financial/operational metrics (rent, vacancy, cap rate, expenses, etc.). "
            "Skip descriptive fields like address, square footage, or property name."
        )

        user_prompt = (
            f"Property: {deal.property_type.value} at {deal.address}, {deal.city}, {deal.state}\n"
            f"Square Feet: {deal.square_feet or 'unknown'}\n\n"
            f"OM Extracted Fields:\n{fields_text}\n\n"
            f"AI Market Benchmarks:\n{benchmarks_text}\n\n"
            "Use the web_search tool to research current market data for this property's "
            "submarket. Then return a JSON object with a single key 'validations' containing "
            "an array. Each object must have:\n"
            '  "field_key": string (matching the OM field key)\n'
            '  "om_value": number (the OM value)\n'
            '  "market_value": number or null (market reference point)\n'
            '  "status": one of "within_range", "above_market", "below_market", "suspicious", "insufficient_data"\n'
            '  "explanation": string (detailed explanation citing sources with [Source Title](URL) markdown links)\n'
            '  "sources": array of {"url": string, "title": string, "snippet": string}\n'
            '  "confidence": number 0-1\n'
        )

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current market data, comps, and reports.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for market data",
                            }
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Agentic loop: let GPT-4o call web_search as many times as it needs
        for _ in range(10):  # max 10 tool call rounds
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                temperature=0.2,
            )

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                messages.append(choice.message.model_dump())

                for tool_call in choice.message.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query", "")

                    # Call Tavily
                    search_result = await self._tavily.search(
                        query=query,
                        search_depth="advanced",
                        max_results=5,
                    )

                    results_text = json.dumps(
                        [
                            {
                                "title": r.get("title", ""),
                                "url": r.get("url", ""),
                                "content": r.get("content", "")[:500],
                            }
                            for r in search_result.get("results", [])
                        ]
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": results_text,
                        }
                    )
            else:
                # Final response — parse JSON
                break

        content = response.choices[0].message.content or "{}"

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]

        data = json.loads(content)
        validations_raw = data.get("validations", [])

        return [
            FieldValidationResult(
                field_key=v["field_key"],
                om_value=v.get("om_value"),
                market_value=v.get("market_value"),
                status=v["status"],
                explanation=v["explanation"],
                sources=[
                    ValidationSource(
                        url=s.get("url", ""),
                        title=s.get("title", ""),
                        snippet=s.get("snippet", ""),
                    )
                    for s in v.get("sources", [])
                ],
                confidence=float(v.get("confidence", 0.5)),
            )
            for v in validations_raw
        ]
```

**Step 3: Commit**

```bash
git add backend/app/domain/interfaces/providers.py backend/app/infrastructure/llm/openai_provider.py
git commit -m "feat: add validate_om_fields with GPT-4o tool calling and Tavily search"
```

---

### Task 7: Add ValidationService

**Files:**
- Create: `backend/app/services/validation_service.py`

**Step 1: Create the service**

Create `backend/app/services/validation_service.py`:

```python
from __future__ import annotations

from uuid import UUID

from app.domain.entities.field_validation import FieldValidation
from app.domain.interfaces.providers import LLMProvider
from app.domain.interfaces.repositories import (
    AssumptionRepository,
    AssumptionSetRepository,
    DealRepository,
    FieldValidationRepository,
)
from app.domain.value_objects.enums import ValidationStatus


class ValidationService:
    def __init__(
        self,
        deal_repo: DealRepository,
        assumption_set_repo: AssumptionSetRepository,
        assumption_repo: AssumptionRepository,
        field_validation_repo: FieldValidationRepository,
        extracted_field_repo,
        llm_provider: LLMProvider,
    ) -> None:
        self._deal_repo = deal_repo
        self._assumption_set_repo = assumption_set_repo
        self._assumption_repo = assumption_repo
        self._field_validation_repo = field_validation_repo
        self._extracted_field_repo = extracted_field_repo
        self._llm_provider = llm_provider

    async def validate_fields(self, deal_id: UUID) -> list[FieldValidation]:
        # Fetch deal
        deal = await self._deal_repo.get_by_id(deal_id)
        if deal is None:
            raise ValueError(f"Deal {deal_id} not found")

        # Fetch all extracted fields across documents
        from app.domain.interfaces.repositories import DocumentRepository
        docs = await self._deal_repo._session  # We need documents
        # Actually, we need to get fields. Let's fetch via the repo.

        # Get extracted fields — need document IDs first
        # The extracted_field_repo works by document_id, so we need a deal-level query.
        # For simplicity, we'll accept document fields directly or add a deal-level method.
        all_fields = await self._extracted_field_repo.get_by_deal_id(deal_id)

        # Filter to numeric fields only
        numeric_fields = [f for f in all_fields if f.value_number is not None]

        if not numeric_fields:
            return []

        # Fetch benchmarks for context
        sets = await self._assumption_set_repo.get_by_deal_id(deal_id)
        benchmarks = []
        if sets:
            benchmarks = await self._assumption_repo.get_by_set_id(sets[0].id)

        # Call LLM for validation
        results = await self._llm_provider.validate_om_fields(
            deal, numeric_fields, benchmarks
        )

        # Convert to entities and persist
        validations = [
            FieldValidation(
                deal_id=deal_id,
                field_key=r.field_key,
                om_value=r.om_value,
                market_value=r.market_value,
                status=ValidationStatus(r.status),
                explanation=r.explanation,
                sources=[
                    {"url": s.url, "title": s.title, "snippet": s.snippet}
                    for s in r.sources
                ],
                confidence=r.confidence,
            )
            for r in results
        ]

        if validations:
            validations = await self._field_validation_repo.bulk_upsert(validations)

        return validations
```

**Step 2: Add `get_by_deal_id` to ExtractedFieldRepository**

In `backend/app/domain/interfaces/repositories.py`, add to `ExtractedFieldRepository`:

```python
    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[ExtractedField]: ...
```

In the concrete implementation at `backend/app/infrastructure/persistence/extraction_repo.py`, add:

```python
    async def get_by_deal_id(self, deal_id: UUID) -> list[ExtractedField]:
        stmt = (
            select(ExtractedFieldModel)
            .join(DocumentModel, ExtractedFieldModel.document_id == DocumentModel.id)
            .where(DocumentModel.deal_id == deal_id)
        )
        result = await self._session.execute(stmt)
        return [extracted_field_to_entity(m) for m in result.scalars().all()]
```

**Step 3: Commit**

```bash
git add backend/app/services/validation_service.py backend/app/domain/interfaces/repositories.py backend/app/infrastructure/persistence/extraction_repo.py
git commit -m "feat: add ValidationService with deal-level field fetching"
```

---

### Task 8: Add API endpoint and wire dependencies

**Files:**
- Create: `backend/app/api/v1/validation.py`
- Modify: `backend/app/api/schemas.py` (add response schema)
- Modify: `backend/app/api/dependencies.py` (add DI wiring)
- Modify: `backend/app/main.py` (register router)

**Step 1: Add Pydantic schemas**

In `backend/app/api/schemas.py`, add:

```python
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
```

**Step 2: Create API route**

Create `backend/app/api/v1/validation.py`:

```python
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_field_validation_repo, get_validation_service
from app.api.schemas import FieldValidationResponse
from app.infrastructure.persistence.field_validation_repo import (
    SqlAlchemyFieldValidationRepository,
)
from app.services.validation_service import ValidationService

router = APIRouter(tags=["validation"])


@router.post(
    "/deals/{deal_id}/validate",
    response_model=list[FieldValidationResponse],
)
async def validate_deal(
    deal_id: UUID,
    service: Annotated[ValidationService, Depends(get_validation_service)],
) -> list[FieldValidationResponse]:
    try:
        validations = await service.validate_fields(deal_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return [FieldValidationResponse.model_validate(v) for v in validations]


@router.get(
    "/deals/{deal_id}/validations",
    response_model=list[FieldValidationResponse],
)
async def list_validations(
    deal_id: UUID,
    repo: Annotated[
        SqlAlchemyFieldValidationRepository,
        Depends(get_field_validation_repo),
    ],
) -> list[FieldValidationResponse]:
    validations = await repo.get_by_deal_id(deal_id)
    return [FieldValidationResponse.model_validate(v) for v in validations]
```

**Step 3: Add DI wiring**

In `backend/app/api/dependencies.py`, add imports and factory functions:

```python
from app.infrastructure.persistence.field_validation_repo import (
    SqlAlchemyFieldValidationRepository,
)
from app.services.validation_service import ValidationService


def get_field_validation_repo(session: DbSession) -> SqlAlchemyFieldValidationRepository:
    return SqlAlchemyFieldValidationRepository(session)


def get_validation_service(
    deal_repo: Annotated[SqlAlchemyDealRepository, Depends(get_deal_repo)],
    assumption_set_repo: Annotated[
        SqlAlchemyAssumptionSetRepository, Depends(get_assumption_set_repo)
    ],
    assumption_repo: Annotated[
        SqlAlchemyAssumptionRepository, Depends(get_assumption_repo)
    ],
    field_validation_repo: Annotated[
        SqlAlchemyFieldValidationRepository, Depends(get_field_validation_repo)
    ],
    extracted_field_repo: Annotated[
        SqlAlchemyExtractedFieldRepository, Depends(get_extracted_field_repo)
    ],
) -> ValidationService:
    return ValidationService(
        deal_repo=deal_repo,
        assumption_set_repo=assumption_set_repo,
        assumption_repo=assumption_repo,
        field_validation_repo=field_validation_repo,
        extracted_field_repo=extracted_field_repo,
        llm_provider=_llm_provider,
    )
```

**Step 4: Register router**

In `backend/app/main.py`, add:

```python
from app.api.v1.validation import router as validation_router
```

And at line 47:

```python
app.include_router(validation_router, prefix="/v1")
```

**Step 5: Commit**

```bash
git add backend/app/api/v1/validation.py backend/app/api/schemas.py backend/app/api/dependencies.py backend/app/main.py
git commit -m "feat: add validation API endpoints and DI wiring"
```

---

### Task 9: Add frontend TypeScript types and API service

**Files:**
- Modify: `frontend/src/interfaces/api.ts`
- Create: `frontend/src/services/validation.service.ts`

**Step 1: Add TypeScript interfaces**

In `frontend/src/interfaces/api.ts`, add:

```typescript
export interface ValidationSource {
  url: string;
  title: string;
  snippet: string;
}

export interface FieldValidation {
  id: string;
  deal_id: string;
  field_key: string;
  om_value: number | null;
  market_value: number | null;
  status: string;
  explanation: string;
  sources: ValidationSource[];
  confidence: number;
  created_at: string;
}
```

**Step 2: Create validation service**

Create `frontend/src/services/validation.service.ts`:

```typescript
import type { FieldValidation } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const validationService = {
  async validate(dealId: string): Promise<FieldValidation[]> {
    return apiFetch<FieldValidation[]>(`/deals/${dealId}/validate`, {
      method: "POST",
    });
  },

  async list(dealId: string): Promise<FieldValidation[]> {
    return apiFetch<FieldValidation[]>(`/deals/${dealId}/validations`);
  },
};
```

**Step 3: Commit**

```bash
git add frontend/src/interfaces/api.ts frontend/src/services/validation.service.ts
git commit -m "feat: add frontend validation types and API service"
```

---

### Task 10: Add useDeal hook support for validations

**Files:**
- Modify: `frontend/src/hooks/use-deal.ts`

**Step 1: Add validations state**

Import `FieldValidation` type, add `validationService` import, add state:

```typescript
import type { FieldValidation } from "@/interfaces/api";
import { validationService } from "@/services/validation.service";

// Inside useDeal:
const [validations, setValidations] = useState<FieldValidation[]>([]);
```

**Step 2: Fetch validations in refresh**

After fetching assumptions, add:

```typescript
// Fetch field validations
const vals = await validationService.list(id);
setValidations(vals);
```

**Step 3: Return validations**

Add `validations` to the return object.

**Step 4: Commit**

```bash
git add frontend/src/hooks/use-deal.ts
git commit -m "feat: add validations to useDeal hook"
```

---

### Task 11: Create ValidationTable frontend component

**Files:**
- Create: `frontend/src/components/validation/validation-table.tsx`

**Step 1: Create the component**

```tsx
"use client";

import type { FieldValidation } from "@/interfaces/api";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const STATUS_CONFIG: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  within_range: { label: "In Range", variant: "default" },
  above_market: { label: "Above Market", variant: "destructive" },
  below_market: { label: "Below Market", variant: "destructive" },
  suspicious: { label: "Suspicious", variant: "destructive" },
  insufficient_data: { label: "Insufficient Data", variant: "secondary" },
};

function formatFieldKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/Psf/g, "PSF")
    .replace(/Pct/g, "%");
}

function formatValue(value: number | null, unit: string | undefined): string {
  if (value === null || value === undefined) return "-";
  if (unit === "%" || unit === "ratio") return `${value}%`;
  if (unit?.includes("$")) return `$${value.toLocaleString()}`;
  return value.toLocaleString();
}

interface ValidationTableProps {
  validations: FieldValidation[];
}

export function ValidationTable({ validations }: ValidationTableProps) {
  if (validations.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No validation results yet.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Field</TableHead>
            <TableHead>OM Value</TableHead>
            <TableHead>Market Value</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-[40%]">Explanation</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {validations.map((v) => {
            const config = STATUS_CONFIG[v.status] ?? STATUS_CONFIG.insufficient_data;
            return (
              <TableRow key={v.id}>
                <TableCell className="font-medium">
                  {formatFieldKey(v.field_key)}
                </TableCell>
                <TableCell>{v.om_value !== null ? v.om_value : "-"}</TableCell>
                <TableCell>
                  {v.market_value !== null ? v.market_value : "-"}
                </TableCell>
                <TableCell>
                  <Badge variant={config.variant}>{config.label}</Badge>
                </TableCell>
                <TableCell className="text-sm">
                  <div
                    className="prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={{ __html: markdownToHtml(v.explanation) }}
                  />
                  {v.sources.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {v.sources.map((s, i) => (
                        <a
                          key={i}
                          href={s.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block text-xs text-blue-600 hover:underline truncate"
                          title={s.snippet}
                        >
                          [{i + 1}] {s.title || s.url}
                        </a>
                      ))}
                    </div>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

function markdownToHtml(text: string): string {
  // Convert markdown links [text](url) to <a> tags
  return text.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">$1</a>',
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/validation/validation-table.tsx
git commit -m "feat: add ValidationTable component with status badges and source links"
```

---

### Task 12: Add Validation tab and pipeline step to deal workspace page

**Files:**
- Modify: `frontend/src/app/deals/[id]/page.tsx`
- Modify: `frontend/src/components/deals/deal-progress-bar.tsx`

**Step 1: Update progress bar**

In `deal-progress-bar.tsx`, update `STAGES`:

```typescript
const STAGES = [
  { key: "upload", label: "Upload OM" },
  { key: "extract", label: "Extract Data" },
  { key: "assumptions", label: "Set Assumptions" },
  { key: "validate", label: "Validate OM" },
  { key: "export", label: "Export" },
] as const;
```

Add to `ACTIVE_STEP_LABELS`:

```typescript
  validate: "Validating OM...",
```

Add `hasValidations: boolean` to `DealProgressBarProps`.

Update `getActiveStage`:

```typescript
function getActiveStage(props: DealProgressBarProps): number {
  if (props.hasValidations) return 4;
  if (props.hasAssumptions) return 3;
  if (props.hasFields) return 2;
  if (props.hasDocuments) return 1;
  return 0;
}
```

**Step 2: Update deal page**

In `page.tsx`:

- Import `ValidationTable` and `validationService`
- Add `"validate"` to `pipelineStep` union type: `"extract" | "assumptions" | "validate" | null`
- Destructure `validations` from `useDeal(id)`
- Add pipeline step 3 after benchmarks in `runPipeline`:

```typescript
        // Step 3: Validate OM fields
        const freshValidations = await validationService.list(id);
        if (freshValidations.length === 0) {
          if (cancelled) return;
          setPipelineStep("validate");
          await validationService.validate(id);
          if (cancelled) return;
          await refresh();
        }
```

- Pass `hasValidations={validations.length > 0}` to `DealProgressBar`
- Add new tab:

```tsx
<TabsTrigger value="validation">Validation</TabsTrigger>

<TabsContent value="validation" className="pt-4">
  <ValidationTable validations={validations} />
</TabsContent>
```

**Step 3: Commit**

```bash
git add frontend/src/app/deals/[id]/page.tsx frontend/src/components/deals/deal-progress-bar.tsx
git commit -m "feat: add Validation tab and pipeline step to deal workspace"
```

---

### Task 13: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update API routes**

Add:
- `POST /v1/deals/{id}/validate` — Validate OM fields against market data
- `GET /v1/deals/{id}/validations` — List field validations

**Step 2: Update pipeline description**

Change pipeline to: extract → benchmarks → validate → export

**Step 3: Update env vars**

Add `DEALDESK_TAVILY_API_KEY`

**Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with validation feature"
```

---

Plan complete and saved to `docs/plans/2026-02-27-om-field-validation-plan.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open a new session with executing-plans, batch execution with checkpoints

Which approach?