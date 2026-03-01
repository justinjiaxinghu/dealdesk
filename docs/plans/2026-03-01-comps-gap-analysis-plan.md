# Comps & Gap Analysis Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Comps & Gap Analysis" tab to the deal workspace that fetches real comparable properties via Rentcast + Tavily, stores them in the DB, and displays a gap analysis summary table plus individual comp cards with per-metric dot-on-line visualizations.

**Architecture:** New `Comp` domain entity → `CompsService` → `CombinedCompsProvider` (Rentcast API + Tavily/GPT-4o scraping) → new `comps` DB table. Auto-triggered as pipeline stage 5 after deep validation; cached to DB so re-renders are instant. Frontend adds `comps.service.ts`, extends `useDeal`, extends `DealProgressBar`, and adds a new `CompsTab` component.

**Tech Stack:** Python/FastAPI backend (follows existing layer rules), SQLAlchemy 2.0 async, Alembic migrations, Next.js 16/React 19/TypeScript, Tailwind CSS 4, shadcn/ui, Rentcast REST API (free tier), Tavily (existing), OpenAI GPT-4o (existing).

---

## Setup Notes

### Backend activation
```bash
source ~/anaconda3/etc/profile.d/conda.sh && conda activate dealdesk
cd /Users/pedrojudice/dealdesk/backend
```

### Run backend tests
```bash
cd /Users/pedrojudice/dealdesk/backend && python -m pytest tests/ -v
```

### Run backend server
```bash
cd /Users/pedrojudice/dealdesk/backend && uvicorn app.main:app --reload
```

### Frontend dev server
```bash
cd /Users/pedrojudice/dealdesk/frontend && npm run dev
```

### Key files to understand before starting
- `backend/app/domain/entities/field_validation.py` — pattern for domain entities
- `backend/app/services/validation_service.py` — pattern for services
- `backend/app/infrastructure/persistence/field_validation_repo.py` — pattern for repos
- `backend/app/infrastructure/persistence/mappers.py` — pattern for mappers
- `backend/app/api/v1/validation.py` — pattern for API routes
- `backend/app/api/dependencies.py` — pattern for DI wiring
- `frontend/src/services/validation.service.ts` — pattern for frontend services
- `frontend/src/hooks/use-deal.ts` — where to add comps fetching
- `frontend/src/components/deals/deal-progress-bar.tsx` — progress bar to extend
- `frontend/src/app/deals/[id]/page.tsx` — pipeline to extend

---

## Task 1: Domain Entity — `Comp`

**Files:**
- Create: `backend/app/domain/entities/comp.py`
- Modify: `backend/app/domain/entities/__init__.py`

**Step 1: Write the failing test**

Create `backend/tests/test_comp_entity.py`:

```python
from uuid import uuid4
from datetime import datetime
from app.domain.entities.comp import Comp


def test_comp_defaults():
    comp = Comp(
        deal_id=uuid4(),
        address="123 Main St",
        city="Austin",
        state="TX",
        property_type="multifamily",
        source="rentcast",
        fetched_at=datetime.utcnow(),
    )
    assert comp.cap_rate is None
    assert comp.rent_per_unit is None
    assert comp.source == "rentcast"
    assert comp.id is not None


def test_comp_with_metrics():
    comp = Comp(
        deal_id=uuid4(),
        address="456 Oak Ave",
        city="Austin",
        state="TX",
        property_type="multifamily",
        cap_rate=0.062,
        price_per_unit=165000.0,
        rent_per_unit=1390.0,
        unit_count=48,
        year_built=2018,
        source="rentcast",
        fetched_at=datetime.utcnow(),
    )
    assert comp.cap_rate == 0.062
    assert comp.unit_count == 48
```

**Step 2: Run to verify failure**

```bash
cd /Users/pedrojudice/dealdesk/backend && python -m pytest tests/test_comp_entity.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'app.domain.entities.comp'`

**Step 3: Implement**

Create `backend/app/domain/entities/comp.py`:

```python
# backend/app/domain/entities/comp.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Comp:
    deal_id: UUID
    address: str
    city: str
    state: str
    property_type: str
    source: str  # "rentcast" | "tavily"
    fetched_at: datetime
    id: UUID = field(default_factory=uuid4)
    # Physical
    year_built: int | None = None
    unit_count: int | None = None
    square_feet: float | None = None
    # Pricing
    sale_price: float | None = None
    price_per_unit: float | None = None
    price_per_sqft: float | None = None
    cap_rate: float | None = None
    # Income
    rent_per_unit: float | None = None
    occupancy_rate: float | None = None
    noi: float | None = None
    # Expenses
    expense_ratio: float | None = None
    opex_per_unit: float | None = None
    # Metadata
    source_url: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Step 4: Export from `__init__.py`**

Open `backend/app/domain/entities/__init__.py` and add `Comp` to the imports. Check current contents first with Read, then add:

```python
from app.domain.entities.comp import Comp
```

**Step 5: Run tests to verify pass**

```bash
cd /Users/pedrojudice/dealdesk/backend && python -m pytest tests/test_comp_entity.py -v
```
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add backend/app/domain/entities/comp.py backend/app/domain/entities/__init__.py backend/tests/test_comp_entity.py
git commit -m "feat: add Comp domain entity"
```

---

## Task 2: Domain Interfaces — `CompRepository` + `CompsProvider`

**Files:**
- Modify: `backend/app/domain/interfaces/repositories.py`
- Modify: `backend/app/domain/interfaces/providers.py`

**Step 1: Add `CompRepository` to repositories.py**

Add at the bottom of `backend/app/domain/interfaces/repositories.py`:

```python
from app.domain.entities.comp import Comp


class CompRepository(ABC):
    @abstractmethod
    async def bulk_upsert(self, comps: list[Comp]) -> list[Comp]: ...

    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[Comp]: ...

    @abstractmethod
    async def delete_by_deal_id(self, deal_id: UUID) -> None: ...
```

**Step 2: Add `CompsProvider` to providers.py**

Add at the bottom of `backend/app/domain/interfaces/providers.py`:

```python
from app.domain.entities.comp import Comp


class CompsProvider(ABC):
    @abstractmethod
    async def search_comps(
        self,
        deal: Deal,
        extracted_fields: list[ExtractedField],
    ) -> list[Comp]: ...
```

**Step 3: Write a test to verify ABCs are importable**

Add to `backend/tests/test_comp_entity.py`:

```python
from app.domain.interfaces.repositories import CompRepository
from app.domain.interfaces.providers import CompsProvider


def test_comp_repository_is_abstract():
    import inspect
    assert inspect.isabstract(CompRepository)


def test_comps_provider_is_abstract():
    import inspect
    assert inspect.isabstract(CompsProvider)
```

**Step 4: Run tests**

```bash
cd /Users/pedrojudice/dealdesk/backend && python -m pytest tests/test_comp_entity.py -v
```
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add backend/app/domain/interfaces/repositories.py backend/app/domain/interfaces/providers.py backend/tests/test_comp_entity.py
git commit -m "feat: add CompRepository and CompsProvider ABCs"
```

---

## Task 3: ORM Model + Alembic Migration

**Files:**
- Modify: `backend/app/infrastructure/persistence/models.py`
- Create: Alembic migration (auto-generated)

**Step 1: Add `CompModel` to models.py**

Add at the bottom of `backend/app/infrastructure/persistence/models.py`:

```python
# ---------------------------------------------------------------------------
# Comps
# ---------------------------------------------------------------------------


class CompModel(Base):
    __tablename__ = "comps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("deals.id"), nullable=False
    )
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    property_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Physical
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    square_feet: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Pricing
    sale_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_per_unit: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_per_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)
    cap_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Income
    rent_per_unit: Mapped[float | None] = mapped_column(Float, nullable=True)
    occupancy_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    noi: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Expenses
    expense_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    opex_per_unit: Mapped[float | None] = mapped_column(Float, nullable=True)

    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    deal = relationship("DealModel", back_populates="comps")
```

Also add the `comps` relationship to `DealModel`:

```python
comps = relationship("CompModel", back_populates="deal", lazy="selectin")
```

**Step 2: Generate Alembic migration**

```bash
source ~/anaconda3/etc/profile.d/conda.sh && conda activate dealdesk
cd /Users/pedrojudice/dealdesk/backend && python -m alembic revision --autogenerate -m "add comps table"
```

**Step 3: Apply migration**

```bash
cd /Users/pedrojudice/dealdesk/backend && python -m alembic upgrade head
```
Expected: `Running upgrade ... -> ..., add comps table`

**Step 4: Commit**

```bash
git add backend/app/infrastructure/persistence/models.py backend/alembic/versions/
git commit -m "feat: add CompModel ORM model and comps migration"
```

---

## Task 4: Mappers + Repository

**Files:**
- Modify: `backend/app/infrastructure/persistence/mappers.py`
- Create: `backend/app/infrastructure/persistence/comp_repo.py`

**Step 1: Add comp mappers to mappers.py**

Add at the bottom of `backend/app/infrastructure/persistence/mappers.py`:

```python
# ---------------------------------------------------------------------------
# Comp
# ---------------------------------------------------------------------------

from app.domain.entities.comp import Comp
from app.infrastructure.persistence.models import CompModel


def comp_to_entity(model: CompModel) -> Comp:
    return Comp(
        id=model.id,
        deal_id=model.deal_id,
        address=model.address,
        city=model.city,
        state=model.state,
        property_type=model.property_type,
        source=model.source,
        source_url=model.source_url,
        year_built=model.year_built,
        unit_count=model.unit_count,
        square_feet=model.square_feet,
        sale_price=model.sale_price,
        price_per_unit=model.price_per_unit,
        price_per_sqft=model.price_per_sqft,
        cap_rate=model.cap_rate,
        rent_per_unit=model.rent_per_unit,
        occupancy_rate=model.occupancy_rate,
        noi=model.noi,
        expense_ratio=model.expense_ratio,
        opex_per_unit=model.opex_per_unit,
        fetched_at=model.fetched_at,
        created_at=model.created_at,
    )


def comp_to_model(entity: Comp) -> CompModel:
    return CompModel(
        id=entity.id,
        deal_id=entity.deal_id,
        address=entity.address,
        city=entity.city,
        state=entity.state,
        property_type=entity.property_type,
        source=entity.source,
        source_url=entity.source_url,
        year_built=entity.year_built,
        unit_count=entity.unit_count,
        square_feet=entity.square_feet,
        sale_price=entity.sale_price,
        price_per_unit=entity.price_per_unit,
        price_per_sqft=entity.price_per_sqft,
        cap_rate=entity.cap_rate,
        rent_per_unit=entity.rent_per_unit,
        occupancy_rate=entity.occupancy_rate,
        noi=entity.noi,
        expense_ratio=entity.expense_ratio,
        opex_per_unit=entity.opex_per_unit,
        fetched_at=entity.fetched_at,
        created_at=entity.created_at,
    )
```

**Step 2: Create comp_repo.py**

Create `backend/app/infrastructure/persistence/comp_repo.py`:

```python
from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.comp import Comp
from app.domain.interfaces.repositories import CompRepository
from app.infrastructure.persistence.mappers import comp_to_entity, comp_to_model
from app.infrastructure.persistence.models import CompModel


class SqlAlchemyCompRepository(CompRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_upsert(self, comps: list[Comp]) -> list[Comp]:
        results: list[Comp] = []
        for c in comps:
            stmt = select(CompModel).where(
                CompModel.deal_id == c.deal_id,
                CompModel.address == c.address,
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.city = c.city
                existing.state = c.state
                existing.property_type = c.property_type
                existing.source = c.source
                existing.source_url = c.source_url
                existing.year_built = c.year_built
                existing.unit_count = c.unit_count
                existing.square_feet = c.square_feet
                existing.sale_price = c.sale_price
                existing.price_per_unit = c.price_per_unit
                existing.price_per_sqft = c.price_per_sqft
                existing.cap_rate = c.cap_rate
                existing.rent_per_unit = c.rent_per_unit
                existing.occupancy_rate = c.occupancy_rate
                existing.noi = c.noi
                existing.expense_ratio = c.expense_ratio
                existing.opex_per_unit = c.opex_per_unit
                existing.fetched_at = c.fetched_at
                await self._session.flush()
                await self._session.refresh(existing)
                results.append(comp_to_entity(existing))
            else:
                model = comp_to_model(c)
                self._session.add(model)
                await self._session.flush()
                await self._session.refresh(model)
                results.append(comp_to_entity(model))

        return results

    async def get_by_deal_id(self, deal_id: UUID) -> list[Comp]:
        stmt = select(CompModel).where(CompModel.deal_id == deal_id)
        result = await self._session.execute(stmt)
        return [comp_to_entity(m) for m in result.scalars().all()]

    async def delete_by_deal_id(self, deal_id: UUID) -> None:
        stmt = delete(CompModel).where(CompModel.deal_id == deal_id)
        await self._session.execute(stmt)
        await self._session.flush()
```

**Step 3: Write a smoke test**

Add to `backend/tests/test_comp_entity.py`:

```python
def test_comp_mapper_roundtrip():
    from datetime import datetime
    from app.infrastructure.persistence.mappers import comp_to_model, comp_to_entity
    from uuid import uuid4

    comp = Comp(
        deal_id=uuid4(),
        address="123 Main St",
        city="Austin",
        state="TX",
        property_type="multifamily",
        source="rentcast",
        cap_rate=0.062,
        fetched_at=datetime.utcnow(),
    )
    model = comp_to_model(comp)
    restored = comp_to_entity(model)
    assert restored.address == comp.address
    assert restored.cap_rate == comp.cap_rate
    assert restored.source == comp.source
```

**Step 4: Run tests**

```bash
cd /Users/pedrojudice/dealdesk/backend && python -m pytest tests/test_comp_entity.py -v
```
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add backend/app/infrastructure/persistence/mappers.py backend/app/infrastructure/persistence/comp_repo.py backend/tests/test_comp_entity.py
git commit -m "feat: add comp mappers and SqlAlchemyCompRepository"
```

---

## Task 5: Rentcast Provider

**Files:**
- Create: `backend/app/infrastructure/comps/__init__.py`
- Create: `backend/app/infrastructure/comps/rentcast_provider.py`
- Modify: `backend/app/config.py`

**Step 1: Add `rentcast_api_key` to config**

Edit `backend/app/config.py` to add:

```python
rentcast_api_key: str = ""
```

**Step 2: Create the infra/comps package**

```bash
touch backend/app/infrastructure/comps/__init__.py
```

**Step 3: Write the failing test**

Create `backend/tests/test_rentcast_provider.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from app.domain.entities.deal import Deal
from app.domain.value_objects.enums import PropertyType


@pytest.fixture
def sample_deal():
    return Deal(
        id=uuid4(),
        name="Test Deal",
        address="123 Main St",
        city="Austin",
        state="TX",
        property_type=PropertyType.MULTIFAMILY,
        latitude=30.2672,
        longitude=-97.7431,
    )


@pytest.mark.asyncio
async def test_rentcast_provider_returns_comps(sample_deal):
    from app.infrastructure.comps.rentcast_provider import RentcastCompsProvider

    mock_response = {
        "properties": [
            {
                "id": "prop_1",
                "formattedAddress": "456 Oak Ave, Austin, TX 78701",
                "addressLine1": "456 Oak Ave",
                "city": "Austin",
                "state": "TX",
                "propertyType": "Multi-Family",
                "yearBuilt": 2018,
                "bedrooms": None,
                "bathrooms": None,
                "squareFootage": 45000,
                "lastSalePrice": 7920000,
                "lastSaleDate": "2023-06-15",
                "rentEstimate": 1390,
            }
        ]
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_response_obj = AsyncMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response
        mock_client.get.return_value = mock_response_obj

        provider = RentcastCompsProvider(api_key="test_key")
        comps = await provider.search_comps(sample_deal, [])

    assert len(comps) == 1
    assert comps[0].address == "456 Oak Ave"
    assert comps[0].city == "Austin"
    assert comps[0].source == "rentcast"
    assert comps[0].rent_per_unit == 1390


@pytest.mark.asyncio
async def test_rentcast_provider_no_lat_lng_returns_empty(sample_deal):
    from app.infrastructure.comps.rentcast_provider import RentcastCompsProvider

    sample_deal.latitude = None
    sample_deal.longitude = None
    provider = RentcastCompsProvider(api_key="test_key")
    comps = await provider.search_comps(sample_deal, [])
    assert comps == []
```

**Step 4: Run to verify failure**

```bash
cd /Users/pedrojudice/dealdesk/backend && python -m pytest tests/test_rentcast_provider.py -v
```
Expected: FAIL — `ModuleNotFoundError`

**Step 5: Implement RentcastCompsProvider**

Create `backend/app/infrastructure/comps/rentcast_provider.py`:

```python
# backend/app/infrastructure/comps/rentcast_provider.py
"""Rentcast API provider for comparable property data."""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from app.domain.entities.comp import Comp
from app.domain.entities.deal import Deal
from app.domain.entities.extraction import ExtractedField
from app.domain.interfaces.providers import CompsProvider

logger = logging.getLogger(__name__)

RENTCAST_BASE = "https://api.rentcast.io/v1"

# Map Rentcast property types to our canonical types
_PROPERTY_TYPE_MAP = {
    "Multi-Family": "multifamily",
    "Single Family": "single_family",
    "Condo": "condo",
    "Townhouse": "townhouse",
}


class RentcastCompsProvider(CompsProvider):
    def __init__(self, api_key: str, radius_miles: float = 2.0, limit: int = 10) -> None:
        self._api_key = api_key
        self._radius_miles = radius_miles
        self._limit = limit

    async def search_comps(
        self,
        deal: Deal,
        extracted_fields: list[ExtractedField],
    ) -> list[Comp]:
        if not deal.latitude or not deal.longitude:
            logger.warning("Deal %s has no lat/lng — skipping Rentcast search", deal.id)
            return []

        if not self._api_key:
            logger.warning("DEALDESK_RENTCAST_API_KEY not set — skipping Rentcast search")
            return []

        params = {
            "latitude": deal.latitude,
            "longitude": deal.longitude,
            "radius": self._radius_miles,
            "propertyType": self._canonical_to_rentcast(deal.property_type.value),
            "limit": self._limit,
        }
        headers = {"X-Api-Key": self._api_key, "Accept": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{RENTCAST_BASE}/properties",
                    params=params,
                    headers=headers,
                )
                if response.status_code != 200:
                    logger.warning(
                        "Rentcast returned %d: %s", response.status_code, response.text[:200]
                    )
                    return []

                data = response.json()
        except Exception as exc:
            logger.warning("Rentcast request failed: %s", exc)
            return []

        properties = data.get("properties", [])
        fetched_at = datetime.utcnow()
        comps: list[Comp] = []

        for prop in properties:
            address_line = prop.get("addressLine1") or prop.get("formattedAddress", "")
            if not address_line:
                continue

            # Derive price_per_unit from lastSalePrice if unit_count available
            unit_count = prop.get("units") or prop.get("unitCount")
            sale_price = prop.get("lastSalePrice")
            price_per_unit = None
            if sale_price and unit_count and unit_count > 0:
                price_per_unit = sale_price / unit_count

            sq_ft = prop.get("squareFootage")
            price_per_sqft = None
            if sale_price and sq_ft and sq_ft > 0:
                price_per_sqft = sale_price / sq_ft

            comps.append(
                Comp(
                    deal_id=deal.id,
                    address=address_line,
                    city=prop.get("city", deal.city),
                    state=prop.get("state", deal.state),
                    property_type=_PROPERTY_TYPE_MAP.get(
                        prop.get("propertyType", ""), deal.property_type.value
                    ),
                    source="rentcast",
                    source_url=f"https://rentcast.io/property/{prop.get('id', '')}",
                    year_built=prop.get("yearBuilt"),
                    unit_count=unit_count,
                    square_feet=sq_ft,
                    sale_price=sale_price,
                    price_per_unit=price_per_unit,
                    price_per_sqft=price_per_sqft,
                    cap_rate=prop.get("capRate"),
                    rent_per_unit=prop.get("rentEstimate"),
                    occupancy_rate=prop.get("occupancyRate"),
                    fetched_at=fetched_at,
                )
            )

        logger.info("Rentcast returned %d comps for deal %s", len(comps), deal.id)
        return comps

    def _canonical_to_rentcast(self, property_type: str) -> str:
        mapping = {
            "multifamily": "Multi-Family",
            "office": "Office",
            "retail": "Retail",
            "industrial": "Industrial",
        }
        return mapping.get(property_type, "Multi-Family")
```

**Step 6: Run tests**

```bash
cd /Users/pedrojudice/dealdesk/backend && python -m pytest tests/test_rentcast_provider.py -v
```
Expected: PASS (2 tests)

**Step 7: Commit**

```bash
git add backend/app/infrastructure/comps/ backend/app/config.py backend/tests/test_rentcast_provider.py
git commit -m "feat: add RentcastCompsProvider"
```

---

## Task 6: Tavily Comps Provider

**Files:**
- Create: `backend/app/infrastructure/comps/tavily_provider.py`

**Step 1: Write the failing test**

Create `backend/tests/test_tavily_comps_provider.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.domain.entities.deal import Deal
from app.domain.value_objects.enums import PropertyType


@pytest.fixture
def sample_deal():
    return Deal(
        id=uuid4(),
        name="Test Deal",
        address="123 Main St",
        city="Austin",
        state="TX",
        property_type=PropertyType.MULTIFAMILY,
        latitude=30.2672,
        longitude=-97.7431,
    )


@pytest.mark.asyncio
async def test_tavily_comps_provider_returns_comps(sample_deal):
    from app.infrastructure.comps.tavily_provider import TavilyCompsProvider

    mock_search_result = {
        "results": [
            {
                "url": "https://zillow.com/homedetails/456-oak-ave",
                "title": "456 Oak Ave - Austin TX Multifamily",
                "content": "48 unit apartment sold for $7.9M, cap rate 6.2%, built 2018",
            }
        ]
    }

    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock()]
    mock_llm_response.choices[0].message.content = '''
    {
        "comps": [
            {
                "address": "456 Oak Ave",
                "city": "Austin",
                "state": "TX",
                "property_type": "multifamily",
                "year_built": 2018,
                "unit_count": 48,
                "cap_rate": 0.062,
                "sale_price": 7900000,
                "source_url": "https://zillow.com/homedetails/456-oak-ave"
            }
        ]
    }
    '''
    mock_llm_response.choices[0].finish_reason = "stop"

    with patch("tavily.AsyncTavilyClient") as mock_tavily_class, \
         patch("openai.AsyncOpenAI") as mock_openai_class:

        mock_tavily = AsyncMock()
        mock_tavily_class.return_value = mock_tavily
        mock_tavily.search.return_value = mock_search_result

        mock_openai = AsyncMock()
        mock_openai_class.return_value = mock_openai
        mock_openai.chat.completions.create.return_value = mock_llm_response

        provider = TavilyCompsProvider(
            tavily_api_key="test_tavily",
            openai_api_key="test_openai",
            openai_model="gpt-4o",
        )
        comps = await provider.search_comps(sample_deal, [])

    assert len(comps) >= 1
    assert comps[0].source == "tavily"
    assert comps[0].cap_rate == 0.062
```

**Step 2: Run to verify failure**

```bash
cd /Users/pedrojudice/dealdesk/backend && python -m pytest tests/test_tavily_comps_provider.py -v
```
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement TavilyCompsProvider**

Create `backend/app/infrastructure/comps/tavily_provider.py`:

```python
# backend/app/infrastructure/comps/tavily_provider.py
"""Tavily + GPT-4o provider for scraping comparable properties from Zillow/Redfin."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from openai import AsyncOpenAI
from tavily import AsyncTavilyClient

from app.domain.entities.comp import Comp
from app.domain.entities.deal import Deal
from app.domain.entities.extraction import ExtractedField
from app.domain.interfaces.providers import CompsProvider

logger = logging.getLogger(__name__)


class TavilyCompsProvider(CompsProvider):
    def __init__(
        self,
        tavily_api_key: str,
        openai_api_key: str,
        openai_model: str = "gpt-4o",
    ) -> None:
        self._tavily = AsyncTavilyClient(api_key=tavily_api_key)
        self._openai = AsyncOpenAI(api_key=openai_api_key)
        self._model = openai_model

    async def search_comps(
        self,
        deal: Deal,
        extracted_fields: list[ExtractedField],
    ) -> list[Comp]:
        property_type = deal.property_type.value
        location = f"{deal.city}, {deal.state}"

        queries = [
            f"{property_type} sold {location} 2023 2024 comparable properties",
            f"multifamily apartment comps {location} cap rate price per unit site:zillow.com OR site:loopnet.com",
        ]

        raw_results: list[dict] = []
        for query in queries:
            try:
                result = await self._tavily.search(
                    query=query,
                    search_depth="basic",
                    max_results=5,
                )
                raw_results.extend(result.get("results", []))
            except Exception as exc:
                logger.warning("Tavily search failed for query '%s': %s", query, exc)

        if not raw_results:
            return []

        # Ask GPT-4o to extract structured comp data from search results
        search_text = "\n\n".join(
            f"URL: {r.get('url', '')}\nTitle: {r.get('title', '')}\nContent: {r.get('content', '')[:500]}"
            for r in raw_results
        )

        system_prompt = f"""You are extracting comparable property data from web search results.
The subject property is a {property_type} in {location}.

Extract any comparable properties you find. Return ONLY a JSON object with this structure:
{{
    "comps": [
        {{
            "address": "street address only",
            "city": "city",
            "state": "2-letter state",
            "property_type": "{property_type}",
            "year_built": <int or null>,
            "unit_count": <int or null>,
            "square_feet": <float or null>,
            "sale_price": <float or null>,
            "price_per_unit": <float or null>,
            "price_per_sqft": <float or null>,
            "cap_rate": <decimal like 0.062, not 6.2 — or null>,
            "rent_per_unit": <monthly rent float or null>,
            "occupancy_rate": <decimal like 0.95, not 95 — or null>,
            "expense_ratio": <decimal or null>,
            "source_url": "url of the source"
        }}
    ]
}}

Only include properties with at least an address and one financial metric. Return [] if none found."""

        try:
            response = await self._openai.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Search results:\n\n{search_text}"},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = response.choices[0].message.content or "{}"
            data = self._extract_json(content)
        except Exception as exc:
            logger.warning("GPT-4o comp extraction failed: %s", exc)
            return []

        fetched_at = datetime.utcnow()
        comps: list[Comp] = []

        for item in data.get("comps", []):
            address = item.get("address", "").strip()
            if not address:
                continue
            comps.append(
                Comp(
                    deal_id=deal.id,
                    address=address,
                    city=item.get("city", deal.city),
                    state=item.get("state", deal.state),
                    property_type=item.get("property_type", property_type),
                    source="tavily",
                    source_url=item.get("source_url"),
                    year_built=item.get("year_built"),
                    unit_count=item.get("unit_count"),
                    square_feet=item.get("square_feet"),
                    sale_price=item.get("sale_price"),
                    price_per_unit=item.get("price_per_unit"),
                    price_per_sqft=item.get("price_per_sqft"),
                    cap_rate=item.get("cap_rate"),
                    rent_per_unit=item.get("rent_per_unit"),
                    occupancy_rate=item.get("occupancy_rate"),
                    expense_ratio=item.get("expense_ratio"),
                    fetched_at=fetched_at,
                )
            )

        logger.info("Tavily/GPT-4o returned %d comps for deal %s", len(comps), deal.id)
        return comps

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response, handling code blocks."""
        # Strip markdown code blocks
        text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("```").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from LLM response: %s", text[:200])
            return {"comps": []}
```

**Step 4: Run tests**

```bash
cd /Users/pedrojudice/dealdesk/backend && python -m pytest tests/test_tavily_comps_provider.py -v
```
Expected: PASS (1 test)

**Step 5: Commit**

```bash
git add backend/app/infrastructure/comps/tavily_provider.py backend/tests/test_tavily_comps_provider.py
git commit -m "feat: add TavilyCompsProvider"
```

---

## Task 7: Combined Provider + CompsService

**Files:**
- Create: `backend/app/infrastructure/comps/combined_provider.py`
- Create: `backend/app/services/comps_service.py`

**Step 1: Create CombinedCompsProvider**

Create `backend/app/infrastructure/comps/combined_provider.py`:

```python
# backend/app/infrastructure/comps/combined_provider.py
"""Combines Rentcast + Tavily results, deduplicates by address."""

from __future__ import annotations

import asyncio
import logging

from app.domain.entities.comp import Comp
from app.domain.entities.deal import Deal
from app.domain.entities.extraction import ExtractedField
from app.domain.interfaces.providers import CompsProvider
from app.infrastructure.comps.rentcast_provider import RentcastCompsProvider
from app.infrastructure.comps.tavily_provider import TavilyCompsProvider

logger = logging.getLogger(__name__)


class CombinedCompsProvider(CompsProvider):
    def __init__(
        self,
        rentcast: RentcastCompsProvider,
        tavily: TavilyCompsProvider,
    ) -> None:
        self._rentcast = rentcast
        self._tavily = tavily

    async def search_comps(
        self,
        deal: Deal,
        extracted_fields: list[ExtractedField],
    ) -> list[Comp]:
        rentcast_comps, tavily_comps = await asyncio.gather(
            self._rentcast.search_comps(deal, extracted_fields),
            self._tavily.search_comps(deal, extracted_fields),
            return_exceptions=True,
        )

        all_comps: list[Comp] = []

        if isinstance(rentcast_comps, list):
            all_comps.extend(rentcast_comps)
        else:
            logger.warning("Rentcast provider failed: %s", rentcast_comps)

        if isinstance(tavily_comps, list):
            all_comps.extend(tavily_comps)
        else:
            logger.warning("Tavily provider failed: %s", tavily_comps)

        # Deduplicate by normalized address — keep first occurrence (Rentcast preferred)
        seen: set[str] = set()
        unique: list[Comp] = []
        for comp in all_comps:
            key = comp.address.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(comp)

        logger.info("Combined provider: %d unique comps for deal %s", len(unique), deal.id)
        return unique
```

**Step 2: Create CompsService**

Create `backend/app/services/comps_service.py`:

```python
# backend/app/services/comps_service.py
from __future__ import annotations

import logging
from uuid import UUID

from app.domain.entities.comp import Comp
from app.domain.interfaces.providers import CompsProvider
from app.domain.interfaces.repositories import (
    CompRepository,
    DealRepository,
    ExtractedFieldRepository,
)

logger = logging.getLogger(__name__)


class CompsService:
    def __init__(
        self,
        deal_repo: DealRepository,
        extracted_field_repo: ExtractedFieldRepository,
        comp_repo: CompRepository,
        comps_provider: CompsProvider,
    ) -> None:
        self._deal_repo = deal_repo
        self._extracted_field_repo = extracted_field_repo
        self._comp_repo = comp_repo
        self._comps_provider = comps_provider

    async def search_comps(self, deal_id: UUID) -> list[Comp]:
        deal = await self._deal_repo.get_by_id(deal_id)
        if deal is None:
            raise ValueError(f"Deal {deal_id} not found")

        fields = await self._extracted_field_repo.get_by_deal_id(deal_id)

        comps = await self._comps_provider.search_comps(deal, fields)

        if comps:
            # Replace all existing comps for this deal with fresh results
            await self._comp_repo.delete_by_deal_id(deal_id)
            comps = await self._comp_repo.bulk_upsert(comps)

        logger.info("CompsService: stored %d comps for deal %s", len(comps), deal_id)
        return comps

    async def list_comps(self, deal_id: UUID) -> list[Comp]:
        return await self._comp_repo.get_by_deal_id(deal_id)
```

**Step 3: Write service test**

Create `backend/tests/test_comps_service.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from app.domain.entities.comp import Comp
from app.domain.entities.deal import Deal
from app.domain.value_objects.enums import PropertyType
from app.services.comps_service import CompsService


@pytest.fixture
def deal():
    return Deal(
        id=uuid4(),
        name="Test",
        address="123 Main",
        city="Austin",
        state="TX",
        property_type=PropertyType.MULTIFAMILY,
    )


@pytest.fixture
def sample_comp(deal):
    return Comp(
        deal_id=deal.id,
        address="456 Oak",
        city="Austin",
        state="TX",
        property_type="multifamily",
        source="rentcast",
        fetched_at=datetime.utcnow(),
        cap_rate=0.062,
    )


@pytest.mark.asyncio
async def test_search_comps_calls_provider_and_persists(deal, sample_comp):
    deal_repo = AsyncMock()
    deal_repo.get_by_id.return_value = deal
    field_repo = AsyncMock()
    field_repo.get_by_deal_id.return_value = []
    comp_repo = AsyncMock()
    comp_repo.bulk_upsert.return_value = [sample_comp]
    provider = AsyncMock()
    provider.search_comps.return_value = [sample_comp]

    service = CompsService(deal_repo, field_repo, comp_repo, provider)
    result = await service.search_comps(deal.id)

    assert len(result) == 1
    provider.search_comps.assert_called_once()
    comp_repo.delete_by_deal_id.assert_called_once_with(deal.id)
    comp_repo.bulk_upsert.assert_called_once()


@pytest.mark.asyncio
async def test_search_comps_raises_if_deal_not_found():
    deal_repo = AsyncMock()
    deal_repo.get_by_id.return_value = None
    service = CompsService(deal_repo, AsyncMock(), AsyncMock(), AsyncMock())

    with pytest.raises(ValueError, match="not found"):
        await service.search_comps(uuid4())


@pytest.mark.asyncio
async def test_list_comps(deal, sample_comp):
    comp_repo = AsyncMock()
    comp_repo.get_by_deal_id.return_value = [sample_comp]
    service = CompsService(AsyncMock(), AsyncMock(), comp_repo, AsyncMock())

    result = await service.list_comps(deal.id)
    assert len(result) == 1
    assert result[0].cap_rate == 0.062
```

**Step 4: Run tests**

```bash
cd /Users/pedrojudice/dealdesk/backend && python -m pytest tests/test_comps_service.py -v
```
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add backend/app/infrastructure/comps/combined_provider.py backend/app/services/comps_service.py backend/tests/test_comps_service.py
git commit -m "feat: add CombinedCompsProvider and CompsService"
```

---

## Task 8: API Routes + DI Wiring + Schema

**Files:**
- Create: `backend/app/api/v1/comps.py`
- Modify: `backend/app/api/schemas.py`
- Modify: `backend/app/api/dependencies.py`
- Modify: `backend/app/api/v1/router.py` (or wherever routes are registered — check `backend/app/main.py`)

**Step 1: Add `CompResponse` to schemas.py**

Add at the bottom of `backend/app/api/schemas.py`:

```python
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
```

**Step 2: Add DI wiring to dependencies.py**

Add at the bottom of `backend/app/api/dependencies.py`:

```python
from app.config import settings
from app.infrastructure.comps.rentcast_provider import RentcastCompsProvider
from app.infrastructure.comps.tavily_provider import TavilyCompsProvider
from app.infrastructure.comps.combined_provider import CombinedCompsProvider
from app.infrastructure.persistence.comp_repo import SqlAlchemyCompRepository
from app.services.comps_service import CompsService

_rentcast_provider = RentcastCompsProvider(api_key=settings.rentcast_api_key)
_tavily_comps_provider = TavilyCompsProvider(
    tavily_api_key=settings.tavily_api_key,
    openai_api_key=settings.openai_api_key,
    openai_model=settings.openai_model,
)
_combined_comps_provider = CombinedCompsProvider(
    rentcast=_rentcast_provider,
    tavily=_tavily_comps_provider,
)


def get_comp_repo(session: DbSession) -> SqlAlchemyCompRepository:
    return SqlAlchemyCompRepository(session)


def get_comps_service(
    deal_repo: Annotated[SqlAlchemyDealRepository, Depends(get_deal_repo)],
    extracted_field_repo: Annotated[
        SqlAlchemyExtractedFieldRepository, Depends(get_extracted_field_repo)
    ],
    comp_repo: Annotated[SqlAlchemyCompRepository, Depends(get_comp_repo)],
) -> CompsService:
    return CompsService(
        deal_repo=deal_repo,
        extracted_field_repo=extracted_field_repo,
        comp_repo=comp_repo,
        comps_provider=_combined_comps_provider,
    )
```

**Step 3: Create the API route file**

Create `backend/app/api/v1/comps.py`:

```python
from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_comp_repo, get_comps_service
from app.api.schemas import CompResponse
from app.infrastructure.persistence.comp_repo import SqlAlchemyCompRepository
from app.services.comps_service import CompsService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["comps"])


@router.post(
    "/deals/{deal_id}/comps:search",
    response_model=list[CompResponse],
)
async def search_comps(
    deal_id: UUID,
    service: Annotated[CompsService, Depends(get_comps_service)],
) -> list[CompResponse]:
    try:
        comps = await service.search_comps(deal_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return [CompResponse.model_validate(c) for c in comps]


@router.get(
    "/deals/{deal_id}/comps",
    response_model=list[CompResponse],
)
async def list_comps(
    deal_id: UUID,
    repo: Annotated[SqlAlchemyCompRepository, Depends(get_comp_repo)],
) -> list[CompResponse]:
    comps = await repo.get_by_deal_id(deal_id)
    return [CompResponse.model_validate(c) for c in comps]
```

**Step 4: Register the router**

Check `backend/app/main.py` to see how other routers are registered. Read it first, then add:

```python
from app.api.v1.comps import router as comps_router
app.include_router(comps_router, prefix="/v1")
```

**Step 5: Start the server and verify routes exist**

```bash
source ~/anaconda3/etc/profile.d/conda.sh && conda activate dealdesk
cd /Users/pedrojudice/dealdesk/backend && uvicorn app.main:app --reload
```

In another terminal:
```bash
curl http://localhost:8000/openapi.json | python -m json.tool | grep "comps"
```
Expected: Lines showing `/v1/deals/{deal_id}/comps:search` and `/v1/deals/{deal_id}/comps`

**Step 6: Commit**

```bash
git add backend/app/api/v1/comps.py backend/app/api/schemas.py backend/app/api/dependencies.py backend/app/main.py
git commit -m "feat: add comps API routes and DI wiring"
```

---

## Task 9: Frontend — TypeScript Types + Service

**Files:**
- Modify: `frontend/src/interfaces/api.ts`
- Create: `frontend/src/services/comps.service.ts`

**Step 1: Add `Comp` type to api.ts**

Open `frontend/src/interfaces/api.ts` and add the `Comp` interface. Check the existing file first to find the right place to add it (after `FieldValidation`):

```typescript
export interface Comp {
  id: string;
  deal_id: string;
  address: string;
  city: string;
  state: string;
  property_type: string;
  source: string; // "rentcast" | "tavily"
  source_url: string | null;
  year_built: number | null;
  unit_count: number | null;
  square_feet: number | null;
  sale_price: number | null;
  price_per_unit: number | null;
  price_per_sqft: number | null;
  cap_rate: number | null;
  rent_per_unit: number | null;
  occupancy_rate: number | null;
  noi: number | null;
  expense_ratio: number | null;
  opex_per_unit: number | null;
  fetched_at: string;
  created_at: string;
}
```

**Step 2: Create comps.service.ts**

Create `frontend/src/services/comps.service.ts`:

```typescript
// frontend/src/services/comps.service.ts
import type { Comp } from "@/interfaces/api";
import { apiFetch } from "./api-client";

export const compsService = {
  /** Fetch (or re-fetch) comparable properties for a deal. Stores results to DB. */
  async search(dealId: string): Promise<Comp[]> {
    return apiFetch<Comp[]>(`/deals/${dealId}/comps:search`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },

  /** List cached comps for a deal. */
  async list(dealId: string): Promise<Comp[]> {
    return apiFetch<Comp[]>(`/deals/${dealId}/comps`);
  },
};
```

**Step 3: Commit**

```bash
git add frontend/src/interfaces/api.ts frontend/src/services/comps.service.ts
git commit -m "feat: add Comp TypeScript type and comps service"
```

---

## Task 10: Extend `useDeal` Hook

**Files:**
- Modify: `frontend/src/hooks/use-deal.ts`

**Step 1: Add `comps` to useDeal**

Edit `frontend/src/hooks/use-deal.ts`:

1. Add `Comp` to the imports from `@/interfaces/api`
2. Add `compsService` import from `@/services/comps.service`
3. Add `const [comps, setComps] = useState<Comp[]>([]);` state
4. Add `compsService.list(id)` to the parallel fetch in `refresh()`
5. Add `comps` to the return object

The updated `refresh` parallel fetch block becomes:
```typescript
const [dealData, docs, sets, vals, compsData] = await Promise.all([
  dealService.get(id),
  documentService.list(id),
  assumptionService.listSets(id),
  validationService.list(id),
  compsService.list(id),
]);
// ... existing setDeal, setDocuments, setAssumptionSets ...
setValidations(vals);
setComps(compsData);
```

Note: The existing code fetches validations inside the try block after the parallel fetch. Move `validationService.list(id)` into the `Promise.all` call and remove the separate `const vals = await validationService.list(id)` line.

**Step 2: Commit**

```bash
git add frontend/src/hooks/use-deal.ts
git commit -m "feat: add comps to useDeal hook"
```

---

## Task 11: Extend `DealProgressBar` for 6 Stages

**Files:**
- Modify: `frontend/src/components/deals/deal-progress-bar.tsx`

**Step 1: Update the progress bar**

Edit `frontend/src/components/deals/deal-progress-bar.tsx`:

1. Add `"comps"` to the `STAGES` array between `validate` and `export`:

```typescript
const STAGES = [
  { key: "upload", label: "Upload OM" },
  { key: "extract", label: "Extract Data" },
  { key: "assumptions", label: "Set Assumptions" },
  { key: "validate", label: "Validate OM" },
  { key: "comps", label: "Find Comps" },
  { key: "export", label: "Export" },
] as const;
```

2. Add `"comps"` to `ACTIVE_STEP_LABELS`:
```typescript
const ACTIVE_STEP_LABELS: Record<string, string> = {
  extract: "Extracting data...",
  assumptions: "Generating benchmarks...",
  validate: "Validating OM...",
  comps: "Finding comparable properties...",
};
```

3. Update `DealProgressBarProps` to add `hasComps: boolean`

4. Update `getActiveStage` to include comps:
```typescript
function getActiveStage(props: DealProgressBarProps): number {
  if (props.hasComps) return 5;
  if (props.hasValidations) return 4;
  if (props.hasAssumptions) return 3;
  if (props.hasFields) return 2;
  if (props.hasDocuments) return 1;
  return 0;
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/deals/deal-progress-bar.tsx
git commit -m "feat: extend DealProgressBar to 6 stages with comps"
```

---

## Task 12: Extend the Auto-Pipeline

**Files:**
- Modify: `frontend/src/app/deals/[id]/page.tsx`

**Step 1: Add comps pipeline stage**

Edit `frontend/src/app/deals/[id]/page.tsx`:

1. Import `compsService` from `@/services/comps.service`
2. Add `"comps"` to the `pipelineStep` type union:
   ```typescript
   const [pipelineStep, setPipelineStep] = useState<
     "extract" | "assumptions" | "validate" | "comps" | null
   >(null);
   ```
3. Update the pipeline guard (line ~61) to also check comps:
   ```typescript
   if (allDocsComplete && assumptions.length > 0 && validations.length > 0 && comps.length > 0) return;
   ```
4. After the deep validation block (after `await refresh()`), add Step 4:
   ```typescript
   // Step 4: Find comparable properties
   const freshComps = await compsService.list(id);
   if (freshComps.length === 0) {
     if (cancelled) return;
     setPipelineStep("comps");
     setPipelineDetail("Searching for comparable properties...");
     await compsService.search(id);
     if (cancelled) return;
     await refresh();
   }
   ```
5. Update the `DealProgressBar` usage to pass `hasComps={comps.length > 0}`
6. Destructure `comps` from `useDeal`

**Step 2: Commit**

```bash
git add frontend/src/app/deals/[id]/page.tsx
git commit -m "feat: add comps as stage 5 in auto-pipeline"
```

---

## Task 13: `CompCard` Component

**Files:**
- Create: `frontend/src/components/comps/comp-card.tsx`

**Step 1: Create the comp card component**

Create `frontend/src/components/comps/comp-card.tsx`:

```typescript
"use client";

import type { Comp } from "@/interfaces/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

interface MetricRow {
  label: string;
  subjectValue: number | null;
  compValue: number | null;
  format: (v: number) => string;
}

interface DotLineChartProps {
  subjectValue: number | null;
  compValue: number | null;
  min: number;
  max: number;
  format: (v: number) => string;
  label: string;
}

function DotLineChart({ subjectValue, compValue, min, max, format, label }: DotLineChartProps) {
  const range = max - min || 1;

  function pct(value: number | null): number {
    if (value === null) return 0;
    return Math.max(0, Math.min(100, ((value - min) / range) * 100));
  }

  const hasSubject = subjectValue !== null;
  const hasComp = compValue !== null;

  if (!hasSubject && !hasComp) return null;

  return (
    <div className="mb-3">
      <div className="text-xs text-muted-foreground mb-1">{label}</div>
      <div className="relative h-6">
        {/* Track */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-muted -translate-y-1/2" />
        {/* Subject dot (blue) */}
        {hasSubject && (
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 flex flex-col items-center"
            style={{ left: `${pct(subjectValue)}%` }}
          >
            <div className="w-3 h-3 rounded-full bg-blue-600 border-2 border-white shadow" />
          </div>
        )}
        {/* Comp dot (orange) */}
        {hasComp && (
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 flex flex-col items-center"
            style={{ left: `${pct(compValue)}%` }}
          >
            <div className="w-3 h-3 rounded-full bg-orange-500 border-2 border-white shadow" />
          </div>
        )}
      </div>
      <div className="flex justify-between text-xs mt-1">
        <span className="text-blue-600 font-medium">
          {hasSubject ? `Subject: ${format(subjectValue!)}` : "Subject: N/A"}
        </span>
        <span className="text-orange-500 font-medium">
          {hasComp ? `This: ${format(compValue!)}` : "This: N/A"}
        </span>
      </div>
    </div>
  );
}

interface CompCardProps {
  comp: Comp;
  subjectMetrics: Partial<Record<keyof Comp, number>>;
  ranges: Partial<Record<keyof Comp, { min: number; max: number }>>;
}

const METRIC_CONFIG: Array<{
  key: keyof Comp;
  label: string;
  format: (v: number) => string;
}> = [
  { key: "cap_rate", label: "Cap Rate", format: (v) => `${(v * 100).toFixed(1)}%` },
  { key: "price_per_unit", label: "Price/Unit", format: (v) => `$${Math.round(v).toLocaleString()}` },
  { key: "price_per_sqft", label: "Price/Sqft", format: (v) => `$${v.toFixed(0)}` },
  { key: "rent_per_unit", label: "Rent/Unit", format: (v) => `$${Math.round(v).toLocaleString()}` },
  { key: "occupancy_rate", label: "Occupancy", format: (v) => `${(v * 100).toFixed(0)}%` },
  { key: "expense_ratio", label: "Expense Ratio", format: (v) => `${(v * 100).toFixed(0)}%` },
  { key: "year_built", label: "Year Built", format: (v) => v.toString() },
  { key: "unit_count", label: "Units", format: (v) => v.toString() },
];

export function CompCard({ comp, subjectMetrics, ranges }: CompCardProps) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="font-semibold text-sm leading-tight">{comp.address}</div>
            <div className="text-xs text-muted-foreground mt-0.5">
              {comp.city}, {comp.state}
            </div>
          </div>
          <Badge variant={comp.source === "rentcast" ? "default" : "secondary"} className="text-xs shrink-0">
            {comp.source === "rentcast" ? "Rentcast" : "Zillow"}
          </Badge>
        </div>
        <div className="flex gap-3 text-xs text-muted-foreground mt-1">
          {comp.unit_count && <span>{comp.unit_count} units</span>}
          {comp.year_built && <span>Built {comp.year_built}</span>}
          {comp.square_feet && <span>{comp.square_feet.toLocaleString()} sqft</span>}
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        {METRIC_CONFIG.map(({ key, label, format }) => {
          const compVal = comp[key] as number | null;
          const subjectVal = (subjectMetrics[key] ?? null) as number | null;
          const range = ranges[key];

          if (compVal === null && subjectVal === null) return null;
          if (!range) return null;

          return (
            <DotLineChart
              key={key}
              label={label}
              subjectValue={subjectVal}
              compValue={compVal}
              min={range.min}
              max={range.max}
              format={format}
            />
          );
        })}
      </CardContent>
    </Card>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/comps/comp-card.tsx
git commit -m "feat: add CompCard component with dot-on-line metric charts"
```

---

## Task 14: `CompsTab` Component (Gap Analysis + Card Grid)

**Files:**
- Create: `frontend/src/components/comps/comps-tab.tsx`

**Step 1: Create the comps tab component**

Create `frontend/src/components/comps/comps-tab.tsx`:

```typescript
"use client";

import { useState } from "react";
import type { Comp, ExtractedField } from "@/interfaces/api";
import { CompCard } from "./comp-card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

// ---------------------------------------------------------------------------
// Metric configuration for the gap analysis table
// ---------------------------------------------------------------------------

const GAP_METRICS: Array<{
  key: keyof Comp;
  label: string;
  format: (v: number) => string;
  higherIsBetter: boolean | null; // null = neutral (physical)
  extractedFieldKey?: string; // map to extracted field key
}> = [
  { key: "cap_rate", label: "Cap Rate", format: (v) => `${(v * 100).toFixed(2)}%`, higherIsBetter: true, extractedFieldKey: "cap_rate" },
  { key: "price_per_unit", label: "Price / Unit", format: (v) => `$${Math.round(v).toLocaleString()}`, higherIsBetter: false },
  { key: "price_per_sqft", label: "Price / Sqft", format: (v) => `$${v.toFixed(0)}`, higherIsBetter: false },
  { key: "rent_per_unit", label: "Rent / Unit", format: (v) => `$${Math.round(v).toLocaleString()}`, higherIsBetter: true, extractedFieldKey: "rent_per_unit" },
  { key: "occupancy_rate", label: "Occupancy", format: (v) => `${(v * 100).toFixed(0)}%`, higherIsBetter: true, extractedFieldKey: "occupancy_rate" },
  { key: "expense_ratio", label: "Expense Ratio", format: (v) => `${(v * 100).toFixed(0)}%`, higherIsBetter: false, extractedFieldKey: "expense_ratio" },
  { key: "year_built", label: "Year Built", format: (v) => v.toString(), higherIsBetter: null },
  { key: "unit_count", label: "Units", format: (v) => v.toString(), higherIsBetter: null },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function avg(values: number[]): number | null {
  const valid = values.filter((v) => v !== null && !isNaN(v));
  if (valid.length === 0) return null;
  return valid.reduce((a, b) => a + b, 0) / valid.length;
}

function getSubjectValue(
  metric: (typeof GAP_METRICS)[0],
  fields: ExtractedField[]
): number | null {
  if (!metric.extractedFieldKey) return null;
  const field = fields.find((f) => f.field_key === metric.extractedFieldKey);
  return field?.value_number ?? null;
}

function computeRanges(comps: Comp[]) {
  const ranges: Partial<Record<keyof Comp, { min: number; max: number }>> = {};
  for (const metric of GAP_METRICS) {
    const values = comps
      .map((c) => c[metric.key] as number | null)
      .filter((v): v is number => v !== null);
    if (values.length === 0) continue;
    ranges[metric.key] = { min: Math.min(...values), max: Math.max(...values) };
  }
  return ranges;
}

function gapLabel(
  subject: number | null,
  compAvg: number | null,
  metric: (typeof GAP_METRICS)[0],
  format: (v: number) => string
): { text: string; color: string } {
  if (subject === null || compAvg === null) return { text: "—", color: "text-muted-foreground" };
  const diff = subject - compAvg;
  const pct = Math.round((diff / compAvg) * 100);
  const sign = diff >= 0 ? "+" : "";
  const text = `${sign}${pct}%`;

  if (metric.higherIsBetter === null) return { text, color: "text-muted-foreground" };
  const favorable = (diff > 0 && metric.higherIsBetter) || (diff < 0 && !metric.higherIsBetter);
  return { text, color: favorable ? "text-green-600 font-semibold" : "text-red-600 font-semibold" };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface CompsTabProps {
  comps: Comp[];
  fields: ExtractedField[];
  onRefetch: () => Promise<void>;
}

export function CompsTab({ comps, fields, onRefetch }: CompsTabProps) {
  const [refetching, setRefetching] = useState(false);

  async function handleRefetch() {
    setRefetching(true);
    try {
      await onRefetch();
    } finally {
      setRefetching(false);
    }
  }

  const ranges = computeRanges(comps);
  const subjectMetrics: Partial<Record<keyof Comp, number>> = {};
  for (const metric of GAP_METRICS) {
    const val = getSubjectValue(metric, fields);
    if (val !== null) subjectMetrics[metric.key] = val;
  }

  return (
    <div className="space-y-6">
      {/* Header + re-fetch button */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold">Comparable Properties</h3>
          <p className="text-sm text-muted-foreground">
            {comps.length} comp{comps.length !== 1 ? "s" : ""} found
          </p>
        </div>
        <Button variant="outline" onClick={handleRefetch} disabled={refetching}>
          {refetching ? "Fetching..." : "Re-fetch Comps"}
        </Button>
      </div>

      {comps.length === 0 ? (
        <div className="text-muted-foreground text-sm py-8 text-center">
          No comparable properties found yet.
        </div>
      ) : (
        <>
          {/* Gap Analysis Table */}
          <div>
            <h4 className="text-sm font-semibold mb-2">Gap Analysis</h4>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Metric</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Comp Avg</TableHead>
                  <TableHead>Gap</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {GAP_METRICS.map((metric) => {
                  const compValues = comps
                    .map((c) => c[metric.key] as number | null)
                    .filter((v): v is number => v !== null);
                  const compAvg = avg(compValues);
                  const subjectVal = subjectMetrics[metric.key] ?? null;
                  const { text: gapText, color: gapColor } = gapLabel(
                    subjectVal,
                    compAvg,
                    metric,
                    metric.format
                  );

                  if (compAvg === null) return null;

                  return (
                    <TableRow key={metric.key as string}>
                      <TableCell className="font-medium">{metric.label}</TableCell>
                      <TableCell>
                        {subjectVal !== null ? metric.format(subjectVal) : <span className="text-muted-foreground">—</span>}
                      </TableCell>
                      <TableCell>{metric.format(compAvg)}</TableCell>
                      <TableCell className={gapColor}>{gapText}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>

          {/* Comp Cards Grid */}
          <div>
            <h4 className="text-sm font-semibold mb-2">Individual Comparables</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {comps.map((comp) => (
                <CompCard
                  key={comp.id}
                  comp={comp}
                  subjectMetrics={subjectMetrics}
                  ranges={ranges}
                />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/comps/comps-tab.tsx
git commit -m "feat: add CompsTab with gap analysis table and comp card grid"
```

---

## Task 15: Wire CompsTab into the Deal Workspace

**Files:**
- Modify: `frontend/src/app/deals/[id]/page.tsx`

**Step 1: Add the Comps tab to the deal workspace**

Edit `frontend/src/app/deals/[id]/page.tsx`:

1. Add imports:
   ```typescript
   import { CompsTab } from "@/components/comps/comps-tab";
   import { compsService } from "@/services/comps.service";
   ```

2. Destructure `comps` and `fields` from `useDeal` (fields is already there):
   ```typescript
   const { deal, documents, fields, assumptionSets, assumptions, validations, comps, loading, refresh } = useDeal(id);
   ```

3. Add `handleRefetchComps` function:
   ```typescript
   async function handleRefetchComps() {
     await compsService.search(id);
     await refresh();
   }
   ```

4. Add `hasComps={comps.length > 0}` to `DealProgressBar`

5. Add a new `TabsTrigger` and `TabsContent` for comps between validation and (if present) export:
   ```typescript
   <TabsTrigger value="comps">Comps</TabsTrigger>
   ```
   ```typescript
   <TabsContent value="comps" className="pt-4">
     <CompsTab
       comps={comps}
       fields={fields}
       onRefetch={handleRefetchComps}
     />
   </TabsContent>
   ```

**Step 2: Start both servers and test end-to-end**

```bash
# Terminal 1 — backend
source ~/anaconda3/etc/profile.d/conda.sh && conda activate dealdesk
cd /Users/pedrojudice/dealdesk/backend && uvicorn app.main:app --reload

# Terminal 2 — frontend
cd /Users/pedrojudice/dealdesk/frontend && npm run dev
```

Navigate to an existing deal, open the Comps tab. Click "Re-fetch Comps" to test the manual trigger. Verify comps load on page refresh without re-fetching.

**Step 3: Run backend tests one final time**

```bash
cd /Users/pedrojudice/dealdesk/backend && python -m pytest tests/ -v
```
Expected: All existing tests + new tests pass.

**Step 4: Final commit**

```bash
git add frontend/src/app/deals/[id]/page.tsx
git commit -m "feat: wire CompsTab into deal workspace and complete comps pipeline"
```

---

## Summary of New Files

| File | Purpose |
|------|---------|
| `backend/app/domain/entities/comp.py` | Comp domain entity |
| `backend/app/infrastructure/comps/__init__.py` | Package init |
| `backend/app/infrastructure/comps/rentcast_provider.py` | Rentcast API integration |
| `backend/app/infrastructure/comps/tavily_provider.py` | Tavily + GPT-4o scraping |
| `backend/app/infrastructure/comps/combined_provider.py` | Parallel merge + dedup |
| `backend/app/infrastructure/persistence/comp_repo.py` | SQLAlchemy comp repository |
| `backend/app/services/comps_service.py` | Business orchestration |
| `backend/app/api/v1/comps.py` | FastAPI routes |
| `frontend/src/services/comps.service.ts` | Frontend API client |
| `frontend/src/components/comps/comp-card.tsx` | Individual comp card |
| `frontend/src/components/comps/comps-tab.tsx` | Full tab with gap analysis |
| `backend/tests/test_comp_entity.py` | Entity + mapper + ABC tests |
| `backend/tests/test_rentcast_provider.py` | Rentcast provider tests |
| `backend/tests/test_tavily_comps_provider.py` | Tavily provider tests |
| `backend/tests/test_comps_service.py` | Service tests |

## Modified Files

| File | Change |
|------|--------|
| `backend/app/domain/entities/__init__.py` | Export Comp |
| `backend/app/domain/interfaces/repositories.py` | Add CompRepository |
| `backend/app/domain/interfaces/providers.py` | Add CompsProvider |
| `backend/app/infrastructure/persistence/models.py` | Add CompModel, DealModel.comps relationship |
| `backend/app/infrastructure/persistence/mappers.py` | Add comp mappers |
| `backend/app/api/schemas.py` | Add CompResponse |
| `backend/app/api/dependencies.py` | Add comp DI wiring |
| `backend/app/main.py` | Register comps router |
| `backend/app/config.py` | Add rentcast_api_key |
| `frontend/src/interfaces/api.ts` | Add Comp type |
| `frontend/src/hooks/use-deal.ts` | Add comps state + fetch |
| `frontend/src/components/deals/deal-progress-bar.tsx` | Add comps stage |
| `frontend/src/app/deals/[id]/page.tsx` | Add comps pipeline step + tab |
