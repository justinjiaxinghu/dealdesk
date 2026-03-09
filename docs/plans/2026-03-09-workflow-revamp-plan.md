# Workflow Revamp Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure DealDesk so Exploration is the primary entry point, add mocked data connectors with chat agent integration, and build a template-based report generator with copilot fill workflow.

**Architecture:** Incremental refactor. Existing backend entities (Deal, Exploration, ChatSession) stay intact. Frontend restructures routes/navigation. Two new backend feature areas added: Connectors (mocked) and Reports. All new backend features follow the existing clean-layer pattern (domain entities → services → API routes).

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy 2.0 async / Next.js 16 / React 19 / TypeScript / Tailwind / shadcn/ui / python-pptx (new) / openpyxl (existing)

**Design doc:** `docs/plans/2026-03-09-workflow-revamp-design.md`

---

## Phase 1: Exploration-First Merge

### Task 1: Update Navigation

**Files:**
- Modify: `frontend/src/app/layout.tsx`

**Step 1: Update nav links**

Replace the nav section (lines 36-46) with four new links:

```tsx
<nav className="flex items-center gap-4 text-sm">
  <Link href="/explore" className="text-muted-foreground hover:text-foreground transition-colors">
    Explore
  </Link>
  <Link href="/reports" className="text-muted-foreground hover:text-foreground transition-colors">
    Reports
  </Link>
  <Link href="/datasets" className="text-muted-foreground hover:text-foreground transition-colors">
    Datasets
  </Link>
  <Link href="/connectors" className="text-muted-foreground hover:text-foreground transition-colors">
    Connectors
  </Link>
</nav>
```

**Step 2: Verify navigation renders**

Run: `cd frontend && npm run dev`
Verify: Four nav links visible in header. "Explore" leads to `/explore`.

**Step 3: Commit**

```bash
git add frontend/src/app/layout.tsx
git commit -m "feat: update nav to Explore / Reports / Datasets / Connectors"
```

---

### Task 2: Make Explore the Home Page

**Files:**
- Modify: `frontend/src/app/page.tsx` — replace deals list with redirect to `/explore`

**Step 1: Replace home page with redirect**

Replace the entire content of `frontend/src/app/page.tsx` with:

```tsx
import { redirect } from "next/navigation";

export default function HomePage() {
  redirect("/explore");
}
```

**Step 2: Verify redirect**

Run: `cd frontend && npm run dev`
Navigate to `http://localhost:3000/` — should redirect to `/explore`.

**Step 3: Commit**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat: redirect home page to /explore"
```

---

### Task 3: Add OM Upload Endpoint

**Files:**
- Create: `backend/app/api/v1/om_upload.py`
- Modify: `backend/app/main.py` — register new router
- Modify: `backend/app/api/dependencies.py` — add factory if needed

This endpoint creates a deal from an uploaded OM PDF, links it to an exploration, and triggers the document processing pipeline.

**Step 1: Write test for OM upload endpoint**

Create `backend/tests/test_om_upload.py`:

```python
"""Tests for the OM upload endpoint."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_upload_om_creates_deal_and_links_exploration(client):
    # Create a free exploration first
    resp = await client.post("/v1/explorations", json={"name": "Test Exploration"})
    assert resp.status_code == 201
    exploration_id = resp.json()["id"]

    # Upload a minimal PDF
    pdf_bytes = b"%PDF-1.4 minimal"
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    resp = await client.post(
        f"/v1/explorations/{exploration_id}/upload-om",
        files=files,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "deal_id" in data
    assert "document_id" in data
    assert data["exploration_id"] == exploration_id

    # Verify exploration is now linked to the deal
    resp = await client.get(f"/v1/explorations/{exploration_id}")
    assert resp.status_code == 200
    assert resp.json()["deal_id"] == data["deal_id"]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_om_upload.py -v`
Expected: FAIL — route does not exist yet.

**Step 3: Implement the endpoint**

Create `backend/app/api/v1/om_upload.py`:

```python
"""OM upload endpoint — creates deal, links to exploration, triggers pipeline."""
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_db_session,
    get_deal_service,
    get_document_service,
)
from app.domain.entities.deal import Deal
from app.domain.value_objects.enums import PropertyType
from app.infrastructure.persistence.exploration_repo import (
    SqlAlchemyExplorationSessionRepository,
)

router = APIRouter(tags=["om-upload"])


@router.post("/explorations/{exploration_id}/upload-om", status_code=201)
async def upload_om(
    exploration_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    deal_service=Depends(get_deal_service),
    document_service=Depends(get_document_service),
):
    """Upload an Offering Memorandum PDF, create a deal, link to exploration, trigger pipeline."""
    exploration_repo = SqlAlchemyExplorationSessionRepository(session)
    exploration = await exploration_repo.get_by_id(exploration_id)
    if not exploration:
        raise HTTPException(status_code=404, detail="Exploration not found")

    if exploration.deal_id:
        # Exploration already has a deal — add document to existing deal
        deal_id = exploration.deal_id
    else:
        # Create a new deal from the filename
        deal_name = file.filename.replace(".pdf", "").replace("_", " ").title() if file.filename else "Untitled Deal"
        deal = await deal_service.create_deal(
            name=deal_name,
            address="TBD",
            city="TBD",
            state="TBD",
            property_type=PropertyType.OTHER,
        )
        deal_id = deal.id
        # Link exploration to the deal
        exploration.deal_id = deal_id
        await exploration_repo.update(exploration)

    # Upload document and trigger processing pipeline
    file_bytes = await file.read()
    document = await document_service.upload_document(
        deal_id=deal_id,
        filename=file.filename or "offering_memorandum.pdf",
        file_bytes=file_bytes,
        background_tasks=background_tasks,
    )

    return {
        "deal_id": str(deal_id),
        "document_id": str(document.id),
        "exploration_id": str(exploration_id),
    }
```

Register in `backend/app/main.py` — add import and include_router:

```python
from app.api.v1.om_upload import router as om_upload_router
# ... after existing includes:
app.include_router(om_upload_router, prefix="/v1")
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_om_upload.py -v`
Expected: PASS (or adjust based on existing service signatures).

**Step 5: Commit**

```bash
git add backend/app/api/v1/om_upload.py backend/app/main.py backend/tests/test_om_upload.py
git commit -m "feat: add POST /explorations/{id}/upload-om endpoint"
```

---

### Task 4: Add OM Upload Button to Search Bar

**Files:**
- Modify: `frontend/src/components/exploration/search-bar.tsx`

**Step 1: Add upload button and callback prop**

Add `onUploadOM` prop to `SearchBarProps`:

```typescript
interface SearchBarProps {
  onSearch: (query: string, connectors: string[]) => void;
  onUploadOM?: (file: File) => void;
  loading?: boolean;
}
```

Add a hidden file input and upload button next to the send button. Between the textarea and the send button (line 99-110 area), add:

```tsx
{/* OM Upload button */}
{onUploadOM && (
  <>
    <input
      ref={fileInputRef}
      type="file"
      accept=".pdf"
      className="hidden"
      onChange={(e) => {
        const file = e.target.files?.[0];
        if (file) {
          onUploadOM(file);
          e.target.value = "";
        }
      }}
    />
    <button
      type="button"
      onClick={() => fileInputRef.current?.click()}
      disabled={loading}
      className="flex items-center justify-center w-9 h-9 rounded-full border border-input text-muted-foreground shrink-0 transition-opacity hover:text-foreground hover:border-foreground disabled:opacity-30 disabled:cursor-not-allowed mb-0.5"
      aria-label="Upload Offering Memorandum"
      title="Upload Offering Memorandum"
    >
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 0V8a4 4 0 118 0v4m-8 0H5a2 2 0 00-2 2v6a2 2 0 002 2h14a2 2 0 002-2v-6a2 2 0 00-2-2h-4" />
      </svg>
    </button>
  </>
)}
```

Add `fileInputRef`:

```tsx
const fileInputRef = useRef<HTMLInputElement>(null);
```

Use a document/paper icon SVG instead. Better icon for "Upload OM":

```tsx
<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
  <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 5v11a2 2 0 002 2z" />
  <path strokeLinecap="round" strokeLinejoin="round" d="M12 11v6m-3-3l3-3 3 3" />
</svg>
```

**Step 2: Verify button renders**

Run: `cd frontend && npm run dev`
Navigate to an exploration workspace. Upload button should appear next to send button.

**Step 3: Commit**

```bash
git add frontend/src/components/exploration/search-bar.tsx
git commit -m "feat: add OM upload button to search bar"
```

---

### Task 5: Add Frontend OM Upload Service

**Files:**
- Modify: `frontend/src/services/exploration.service.ts`

**Step 1: Add uploadOM method**

Add to `explorationService`:

```typescript
async uploadOM(explorationId: string, file: File): Promise<{ deal_id: string; document_id: string; exploration_id: string }> {
  const formData = new FormData();
  formData.append("file", file);
  return apiUpload(`/explorations/${explorationId}/upload-om`, formData);
},
```

Make sure `apiUpload` is imported from the api-client.

**Step 2: Commit**

```bash
git add frontend/src/services/exploration.service.ts
git commit -m "feat: add uploadOM to exploration service"
```

---

### Task 6: Integrate OM Upload into Explore Workspace

**Files:**
- Modify: `frontend/src/app/explore/page.tsx`

This is the core integration. When an OM is uploaded, the explore workspace needs to:
1. Call `explorationService.uploadOM()`
2. Start showing the deal sidebar (reuse `DealSidebar` from the old deals page)
3. Run the auto-pipeline in the sidebar

**Step 1: Add deal state and sidebar to ExploreWorkspace**

In `ExploreWorkspace` component, add:

```tsx
import { useDeal } from "@/hooks/use-deal";
import { DealSidebar } from "@/components/layout/deal-sidebar";
import { explorationService } from "@/services/exploration.service";

// Inside ExploreWorkspace:
const [dealId, setDealId] = useState<string | null>(null);

// When exploration loads and has a deal_id, set it
useEffect(() => {
  if (exploration?.deal_id) {
    setDealId(exploration.deal_id);
  }
}, [exploration?.deal_id]);

// Deal hook (only fetches when dealId is set)
const dealData = useDeal(dealId);

const handleUploadOM = useCallback(async (file: File) => {
  try {
    const result = await explorationService.uploadOM(explorationId, file);
    setDealId(result.deal_id);
    await refresh();
  } catch (err) {
    console.error("OM upload failed", err);
  }
}, [explorationId, refresh]);
```

**Step 2: Update layout to show sidebar when deal exists**

Change the workspace JSX to a two-pane layout when a deal is present:

```tsx
return (
  <div className="h-[calc(100vh-120px)] flex">
    {/* Deal sidebar — only visible when OM uploaded */}
    {dealId && dealData.deal && (
      <div className="w-80 border-r overflow-y-auto shrink-0">
        <DealSidebar {...dealData} />
      </div>
    )}

    {/* Main exploration pane */}
    <div className="flex-1 flex flex-col min-w-0">
      <div className="mb-4 px-4 pt-2">
        <h1 className="text-2xl font-bold tracking-tight">
          {exploration?.name ?? "Market Discovery"}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Search for comparable properties and market data.
        </p>
      </div>

      <SessionTabs ... />

      <div className="flex-1 overflow-y-auto mt-2">
        {activeTabId === null ? (
          <OverviewTab deal={dealData.deal} properties={[]} onSelectProperty={handleSelectProperty} />
        ) : (
          <ChatThread messages={messages} loading={sending || searchLoading} />
        )}
      </div>

      <SearchBar onSearch={handleSearch} onUploadOM={handleUploadOM} loading={searchLoading || sending} />
    </div>
  </div>
);
```

**Step 3: Verify OM upload flow**

Run: `cd frontend && npm run dev` and `cd backend && uvicorn app.main:app --reload`
1. Go to `/explore`, create a new exploration
2. Click OM upload button, select a PDF
3. Sidebar should appear on the left showing pipeline progress
4. Chat should continue working on the right

**Step 4: Commit**

```bash
git add frontend/src/app/explore/page.tsx
git commit -m "feat: integrate OM upload + deal sidebar into explore workspace"
```

---

### Task 7: Remove Old Deals Pages

**Files:**
- Delete: `frontend/src/app/deals/new/page.tsx`
- Delete: `frontend/src/app/deals/[id]/page.tsx`
- Delete: `frontend/src/app/deals/` directory

**Step 1: Remove deals directory**

```bash
rm -rf frontend/src/app/deals
```

**Step 2: Verify no broken imports**

Run: `cd frontend && npm run build`
Fix any import errors if found.

**Step 3: Commit**

```bash
git add -A frontend/src/app/deals
git commit -m "feat: remove old deals pages — exploration is now the entry point"
```

---

## Phase 2: Connectors (Mocked)

### Task 8: Add Connector Domain Entities

**Files:**
- Create: `backend/app/domain/entities/connector.py`
- Modify: `backend/app/domain/value_objects/enums.py` — add ConnectorProvider enum

**Step 1: Add ConnectorProvider enum**

Add to `backend/app/domain/value_objects/enums.py`:

```python
class ConnectorProvider(StrEnum):
    ONEDRIVE = "onedrive"
    BOX = "box"
    GOOGLE_DRIVE = "google_drive"
    SHAREPOINT = "sharepoint"


class ConnectorStatus(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
```

**Step 2: Create Connector and ConnectorFile entities**

Create `backend/app/domain/entities/connector.py`:

```python
"""Connector and ConnectorFile domain entities."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.value_objects.enums import ConnectorProvider, ConnectorStatus


@dataclass
class Connector:
    provider: ConnectorProvider
    status: ConnectorStatus = ConnectorStatus.DISCONNECTED
    file_count: int = 0
    connected_at: datetime | None = None
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class ConnectorFile:
    connector_id: str
    name: str
    path: str
    file_type: str
    text_content: str
    indexed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid4()))
```

**Step 3: Commit**

```bash
git add backend/app/domain/entities/connector.py backend/app/domain/value_objects/enums.py
git commit -m "feat: add Connector and ConnectorFile domain entities"
```

---

### Task 9: Add Connector ORM Models and Migration

**Files:**
- Modify: `backend/app/infrastructure/persistence/models.py`
- Modify: `backend/app/infrastructure/persistence/mappers.py`

**Step 1: Add ORM models**

Add to `backend/app/infrastructure/persistence/models.py`:

```python
# ---------------------------------------------------------------------------
# Connectors
# ---------------------------------------------------------------------------


class ConnectorModel(Base):
    __tablename__ = "connectors"

    id = Column(UUIDType, primary_key=True)
    provider = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False, default="disconnected")
    file_count = Column(Integer, nullable=False, default=0)
    connected_at = Column(DateTime, nullable=True)

    files = relationship(
        "ConnectorFileModel", back_populates="connector", cascade="all, delete-orphan"
    )


class ConnectorFileModel(Base):
    __tablename__ = "connector_files"

    id = Column(UUIDType, primary_key=True)
    connector_id = Column(UUIDType, ForeignKey("connectors.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    text_content = Column(Text, nullable=False)
    indexed_at = Column(DateTime, nullable=False)

    connector = relationship("ConnectorModel", back_populates="files")
```

Add `Integer` and `Text` to the Column imports if not present.

**Step 2: Add mappers**

Add to `backend/app/infrastructure/persistence/mappers.py`:

```python
from app.domain.entities.connector import Connector, ConnectorFile
from app.domain.value_objects.enums import ConnectorProvider, ConnectorStatus

# Connector mappers

def connector_entity_to_model(entity: Connector) -> ConnectorModel:
    return ConnectorModel(
        id=entity.id,
        provider=entity.provider.value,
        status=entity.status.value,
        file_count=entity.file_count,
        connected_at=entity.connected_at,
    )

def connector_model_to_entity(model: ConnectorModel) -> Connector:
    return Connector(
        id=str(model.id),
        provider=ConnectorProvider(model.provider),
        status=ConnectorStatus(model.status),
        file_count=model.file_count,
        connected_at=model.connected_at,
    )

def connector_file_entity_to_model(entity: ConnectorFile) -> ConnectorFileModel:
    return ConnectorFileModel(
        id=entity.id,
        connector_id=entity.connector_id,
        name=entity.name,
        path=entity.path,
        file_type=entity.file_type,
        text_content=entity.text_content,
        indexed_at=entity.indexed_at,
    )

def connector_file_model_to_entity(model: ConnectorFileModel) -> ConnectorFile:
    return ConnectorFile(
        id=str(model.id),
        connector_id=str(model.connector_id),
        name=model.name,
        path=model.path,
        file_type=model.file_type,
        text_content=model.text_content,
        indexed_at=model.indexed_at,
    )
```

**Step 3: Commit**

```bash
git add backend/app/infrastructure/persistence/models.py backend/app/infrastructure/persistence/mappers.py
git commit -m "feat: add Connector ORM models and mappers"
```

---

### Task 10: Add Connector Repository

**Files:**
- Create: `backend/app/infrastructure/persistence/connector_repo.py`

**Step 1: Implement repository**

```python
"""Connector and ConnectorFile repositories."""
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.connector import Connector, ConnectorFile
from app.infrastructure.persistence.mappers import (
    connector_entity_to_model,
    connector_model_to_entity,
    connector_file_entity_to_model,
    connector_file_model_to_entity,
)
from app.infrastructure.persistence.models import ConnectorModel, ConnectorFileModel


class SqlAlchemyConnectorRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_provider(self, provider: str) -> Connector | None:
        result = await self._session.execute(
            select(ConnectorModel).where(ConnectorModel.provider == provider)
        )
        model = result.scalar_one_or_none()
        return connector_model_to_entity(model) if model else None

    async def list_all(self) -> list[Connector]:
        result = await self._session.execute(select(ConnectorModel))
        return [connector_model_to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: Connector) -> Connector:
        model = connector_entity_to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return connector_model_to_entity(model)

    async def update(self, entity: Connector) -> Connector:
        model = connector_entity_to_model(entity)
        merged = await self._session.merge(model)
        await self._session.flush()
        return connector_model_to_entity(merged)

    async def delete_files(self, connector_id: str) -> None:
        await self._session.execute(
            delete(ConnectorFileModel).where(
                ConnectorFileModel.connector_id == connector_id
            )
        )
        await self._session.flush()


class SqlAlchemyConnectorFileRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def bulk_create(self, entities: list[ConnectorFile]) -> None:
        for entity in entities:
            self._session.add(connector_file_entity_to_model(entity))
        await self._session.flush()

    async def search(self, query: str, connector_id: str | None = None) -> list[ConnectorFile]:
        stmt = select(ConnectorFileModel)
        if connector_id:
            stmt = stmt.where(ConnectorFileModel.connector_id == connector_id)
        # Simple text search — case-insensitive LIKE
        stmt = stmt.where(ConnectorFileModel.text_content.ilike(f"%{query}%"))
        result = await self._session.execute(stmt)
        return [connector_file_model_to_entity(m) for m in result.scalars().all()]

    async def count_by_connector(self, connector_id: str) -> int:
        from sqlalchemy import func
        result = await self._session.execute(
            select(func.count(ConnectorFileModel.id)).where(
                ConnectorFileModel.connector_id == connector_id
            )
        )
        return result.scalar_one()
```

**Step 2: Commit**

```bash
git add backend/app/infrastructure/persistence/connector_repo.py
git commit -m "feat: add connector repositories"
```

---

### Task 11: Add Mock Data Fixtures

**Files:**
- Create: `backend/app/infrastructure/connectors/mock_data.py`

**Step 1: Create mock data**

```python
"""Mock connector file data for demo purposes.

Each connector gets a set of realistic real estate documents with
pre-extracted text content.
"""

ONEDRIVE_FILES = [
    {
        "name": "Sunrise Senior Living - Rent Roll Q4 2025.xlsx",
        "path": "/Shared Files/Senior Housing/Sunrise/Rent Roll Q4 2025.xlsx",
        "file_type": "xlsx",
        "text_content": (
            "Sunrise Senior Living - Rent Roll as of December 2025\n"
            "Unit 101 | Assisted Living | 450 sqft | $5,200/mo | Occupied | Lease exp 06/2026\n"
            "Unit 102 | Memory Care | 380 sqft | $6,800/mo | Occupied | Lease exp 03/2026\n"
            "Unit 103 | Independent Living | 620 sqft | $3,900/mo | Vacant | Available\n"
            "Unit 104 | Assisted Living | 450 sqft | $5,200/mo | Occupied | Lease exp 09/2026\n"
            "Unit 105 | Memory Care | 380 sqft | $6,800/mo | Occupied | Lease exp 12/2026\n"
            "Total Units: 85 | Occupancy: 91.8% | Average Rent: $5,180/mo\n"
            "Property: 123 Oak Avenue, Phoenix, AZ 85004"
        ),
    },
    {
        "name": "Sunrise Senior Living - Financial Statement 2025.pdf",
        "path": "/Shared Files/Senior Housing/Sunrise/Financial Statement 2025.pdf",
        "file_type": "pdf",
        "text_content": (
            "Sunrise Senior Living - Annual Financial Statement 2025\n"
            "Revenue: $5,284,000 | Operating Expenses: $3,421,000 | NOI: $1,863,000\n"
            "Occupancy: 91.8% | Revenue per Occupied Unit: $62,400/yr\n"
            "Expense Ratio: 64.7% | Cap Rate (implied): 6.2%\n"
            "Year-over-Year Revenue Growth: 3.8%\n"
            "Major Expenses: Staffing $1,890,000 | Food Service $412,000 | Utilities $289,000\n"
            "Capital Expenditures: $320,000 (HVAC replacement, roof repairs)"
        ),
    },
    {
        "name": "Desert Ridge Land - Purchase Agreement.pdf",
        "path": "/Shared Files/Land Development/Desert Ridge/Purchase Agreement.pdf",
        "file_type": "pdf",
        "text_content": (
            "Purchase and Sale Agreement - Desert Ridge Estates\n"
            "Buyer: Starwood Land Partners LLC | Seller: Arizona Land Trust\n"
            "Purchase Price: $12,500,000 | Acreage: 240 acres\n"
            "Zoning: R-3 Residential | Entitled Lots: 480\n"
            "Price Per Lot: $26,042 | Estimated Infrastructure Cost: $8,200,000\n"
            "Closing Date: March 15, 2026 | Due Diligence Period: 60 days\n"
            "Earnest Money: $500,000 | Contingencies: Environmental Phase II, Title"
        ),
    },
    {
        "name": "Luxury Condo 500 Park Ave - Budget 2026.xlsx",
        "path": "/Shared Files/Luxury Condos/500 Park Ave/Budget 2026.xlsx",
        "file_type": "xlsx",
        "text_content": (
            "500 Park Avenue Luxury Condominiums - 2026 Development Budget\n"
            "Total Development Cost: $145,000,000\n"
            "Hard Costs: $98,000,000 | Soft Costs: $22,000,000 | Land: $25,000,000\n"
            "Total Units: 42 | Average Size: 2,100 sqft | Price PSF: $3,200\n"
            "Projected Revenue: $282,240,000 | Projected Profit: $137,240,000\n"
            "Construction Timeline: 24 months | Completion: Q4 2027\n"
            "Presales: 12 units (28.6%) | Average Presale Price: $6,720,000"
        ),
    },
    {
        "name": "Q4 2025 Quarterly Report - Senior Housing Portfolio.pptx",
        "path": "/Shared Files/Quarterly Reports/Q4 2025 Senior Housing Portfolio.pptx",
        "file_type": "pptx",
        "text_content": (
            "Starwood Capital - Senior Housing Portfolio Q4 2025 Report\n"
            "Portfolio Overview: 8 properties | 680 total units | 89.2% avg occupancy\n"
            "Total NOI: $14,200,000 (Q4) | YoY Growth: 4.1%\n"
            "Top Performer: Sunrise Phoenix (91.8% occ, 6.2% cap rate)\n"
            "Underperformer: Meadowbrook Chicago (82.1% occ, staffing challenges)\n"
            "Capital Expenditure: $2,100,000 across portfolio\n"
            "Disposition Pipeline: Evaluating sale of 2 stabilized assets\n"
            "Market Outlook: Demand accelerating, new supply constrained"
        ),
    },
]

BOX_FILES = [
    {
        "name": "Fund III - Medical Office Portfolio Model.xlsx",
        "path": "/Bain Capital RE/Fund III/Medical Office Portfolio Model.xlsx",
        "file_type": "xlsx",
        "text_content": (
            "Bain Capital Real Estate - Medical Office Portfolio Acquisition Model\n"
            "Portfolio: 20 properties | 1,200,000 total sqft | Weighted avg lease term: 4.2 years\n"
            "Purchase Price: $380,000,000 | Cap Rate: 6.8% | NOI: $25,840,000\n"
            "Debt: $247,000,000 (65% LTV) | Rate: 5.25% fixed | Term: 5 years\n"
            "Equity Required: $133,000,000 | Target IRR: 15% | Target Equity Multiple: 1.8x\n"
            "Hold Period: 5 years | Exit Cap Rate: 7.0%\n"
            "Key Markets: Boston, Providence, Chicago, Phoenix"
        ),
    },
    {
        "name": "Providence Medical Office - Rent Comps.xlsx",
        "path": "/Bain Capital RE/Fund III/Comps/Providence Medical Office Comps.xlsx",
        "file_type": "xlsx",
        "text_content": (
            "Providence, RI - Medical Office Rent Comparables (2025)\n"
            "123 Benefit St | 45,000 sqft | $28/sqft NNN | 95% occupied | Class A\n"
            "456 Thayer St | 32,000 sqft | $25/sqft NNN | 88% occupied | Class B+\n"
            "789 Hope St | 28,000 sqft | $22/sqft NNN | 91% occupied | Class B\n"
            "321 Wickenden St | 18,000 sqft | $30/sqft NNN | 100% occupied | Class A | New construction\n"
            "Market Average: $26.25/sqft NNN | Vacancy: 8.5%\n"
            "Trend: Rents up 3.2% YoY | New supply limited"
        ),
    },
    {
        "name": "Retail Portfolio - IC Memo.pdf",
        "path": "/Bain Capital RE/Fund III/Retail/IC Memo - Southeast Retail Portfolio.pdf",
        "file_type": "pdf",
        "text_content": (
            "Investment Committee Memorandum - Southeast Retail Portfolio\n"
            "Recommendation: Proceed to LOI at $52,000,000\n"
            "Properties: 5 grocery-anchored strip centers | 320,000 sqft\n"
            "Markets: Charlotte, Raleigh, Atlanta | NOI: $3,640,000 | Cap Rate: 7.0%\n"
            "Anchor Tenants: Publix (3), Harris Teeter (2) | WALT: 8.3 years\n"
            "Occupancy: 94.2% | Below-market rent roll with 15% mark-to-market upside\n"
            "Risk Factors: Retail headwinds, single-tenant concentration\n"
            "Comparable Sales: $155-$175 PSF in similar markets"
        ),
    },
]

GOOGLE_DRIVE_FILES = [
    {
        "name": "Market Research - Phoenix Multifamily 2025.pdf",
        "path": "/Research/Phoenix Multifamily Market Report 2025.pdf",
        "file_type": "pdf",
        "text_content": (
            "Phoenix Multifamily Market Report - Year End 2025\n"
            "Average Rent: $1,485/mo (+2.8% YoY) | Vacancy: 7.2% (up from 5.8%)\n"
            "New Supply: 12,400 units delivered in 2025 | Pipeline: 8,200 units\n"
            "Top Submarkets: Scottsdale ($1,890/mo), Tempe ($1,620/mo), Chandler ($1,550/mo)\n"
            "Cap Rates: Class A 5.0-5.5% | Class B 5.5-6.0% | Class C 6.0-7.0%\n"
            "Transaction Volume: $4.2B (down 15% from 2024)\n"
            "Outlook: Rent growth moderating, supply peak passing, absorption improving"
        ),
    },
    {
        "name": "Industrial Market Overview - Inland Empire.pdf",
        "path": "/Research/Inland Empire Industrial Q4 2025.pdf",
        "file_type": "pdf",
        "text_content": (
            "Inland Empire Industrial Market Overview Q4 2025\n"
            "Average Asking Rent: $1.15/sqft/mo NNN (+1.2% YoY, decelerating)\n"
            "Vacancy: 6.8% (up from 3.2% in 2023 - normalizing)\n"
            "Inventory: 620M sqft | New Completions: 22M sqft in 2025\n"
            "Net Absorption: 18M sqft | Under Construction: 12M sqft\n"
            "Cap Rates: Class A 5.25-5.75% | Class B 6.0-6.5%\n"
            "Key Tenants: Amazon, FedEx, UPS, Wayfair\n"
            "Outlook: Supply/demand rebalancing, rent growth stabilizing"
        ),
    },
]

SHAREPOINT_FILES = [
    {
        "name": "Investor Report Template - Quarterly.pptx",
        "path": "/Templates/Quarterly Investor Report Template.pptx",
        "file_type": "pptx",
        "text_content": (
            "Quarterly Investor Report Template\n"
            "Slide 1: Portfolio Summary | {{total_properties}} | {{total_noi}} | {{avg_occupancy}}\n"
            "Slide 2: Performance by Asset Class | Table: Asset Class | Properties | NOI | Occupancy\n"
            "Slide 3: Top 5 Performers | Table: Property | NOI | Occupancy | Cap Rate\n"
            "Slide 4: Underperformers | Table: Property | Issue | Action Plan\n"
            "Slide 5: Capital Activity | Acquisitions | Dispositions | CapEx\n"
            "Slide 6: Market Outlook | Key trends and risks\n"
            "Slide 7: Fund Financials | IRR | Equity Multiple | DPI"
        ),
    },
    {
        "name": "Due Diligence Checklist - Standard.xlsx",
        "path": "/Templates/DD Checklist Standard.xlsx",
        "file_type": "xlsx",
        "text_content": (
            "Standard Due Diligence Checklist\n"
            "1. Financial Review: Historical P&L (3yr), Rent Roll, Budget vs Actual\n"
            "2. Legal: Title Search, Survey, Environmental Phase I/II, Zoning\n"
            "3. Physical: Property Condition Assessment, Capital Needs Assessment\n"
            "4. Market: Rent Comps, Sale Comps, Supply Pipeline, Demand Drivers\n"
            "5. Tenant: Lease Abstracts, Tenant Credit, Rollover Schedule\n"
            "6. Insurance: Coverage Review, Loss History, Flood Zone\n"
            "7. Tax: Assessment Review, Appeal History, Projected Reassessment"
        ),
    },
]

MOCK_FILES_BY_PROVIDER = {
    "onedrive": ONEDRIVE_FILES,
    "box": BOX_FILES,
    "google_drive": GOOGLE_DRIVE_FILES,
    "sharepoint": SHAREPOINT_FILES,
}
```

**Step 2: Commit**

```bash
git add backend/app/infrastructure/connectors/mock_data.py
git commit -m "feat: add mock connector file data"
```

---

### Task 12: Add Connector Service

**Files:**
- Create: `backend/app/services/connector_service.py`

**Step 1: Write test**

Create `backend/tests/test_connector_service.py`:

```python
"""Tests for ConnectorService."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_list_connectors_returns_all_providers(client):
    resp = await client.get("/v1/connectors")
    assert resp.status_code == 200
    providers = {c["provider"] for c in resp.json()}
    assert providers == {"onedrive", "box", "google_drive", "sharepoint"}


@pytest.mark.asyncio
async def test_connect_seeds_mock_data(client):
    resp = await client.post("/v1/connectors/onedrive/connect")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "connected"
    assert data["file_count"] > 0


@pytest.mark.asyncio
async def test_disconnect_clears_files(client):
    # Connect first
    await client.post("/v1/connectors/onedrive/connect")
    # Disconnect
    resp = await client.post("/v1/connectors/onedrive/disconnect")
    assert resp.status_code == 200
    assert resp.json()["status"] == "disconnected"
    assert resp.json()["file_count"] == 0
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_connector_service.py -v`
Expected: FAIL — endpoints don't exist.

**Step 3: Implement ConnectorService**

Create `backend/app/services/connector_service.py`:

```python
"""Connector service — manages mock connector lifecycle and file search."""
from datetime import datetime, timezone

from app.domain.entities.connector import Connector, ConnectorFile
from app.domain.value_objects.enums import ConnectorProvider, ConnectorStatus
from app.infrastructure.connectors.mock_data import MOCK_FILES_BY_PROVIDER
from app.infrastructure.persistence.connector_repo import (
    SqlAlchemyConnectorRepository,
    SqlAlchemyConnectorFileRepository,
)

ALL_PROVIDERS = [p.value for p in ConnectorProvider]


class ConnectorService:
    def __init__(
        self,
        connector_repo: SqlAlchemyConnectorRepository,
        file_repo: SqlAlchemyConnectorFileRepository,
    ):
        self._connector_repo = connector_repo
        self._file_repo = file_repo

    async def list_connectors(self) -> list[Connector]:
        """Return all connectors, creating missing ones as disconnected."""
        existing = await self._connector_repo.list_all()
        existing_providers = {c.provider.value for c in existing}
        for provider in ALL_PROVIDERS:
            if provider not in existing_providers:
                connector = Connector(
                    provider=ConnectorProvider(provider),
                    status=ConnectorStatus.DISCONNECTED,
                )
                created = await self._connector_repo.create(connector)
                existing.append(created)
        return existing

    async def connect(self, provider: str) -> Connector:
        """Mock-connect a provider and seed its files."""
        connector = await self._connector_repo.get_by_provider(provider)
        if not connector:
            connector = Connector(
                provider=ConnectorProvider(provider),
                status=ConnectorStatus.DISCONNECTED,
            )
            connector = await self._connector_repo.create(connector)

        # Seed mock files
        mock_files = MOCK_FILES_BY_PROVIDER.get(provider, [])
        files = [
            ConnectorFile(
                connector_id=connector.id,
                name=f["name"],
                path=f["path"],
                file_type=f["file_type"],
                text_content=f["text_content"],
            )
            for f in mock_files
        ]
        await self._file_repo.bulk_create(files)

        connector.status = ConnectorStatus.CONNECTED
        connector.connected_at = datetime.now(timezone.utc)
        connector.file_count = len(files)
        return await self._connector_repo.update(connector)

    async def disconnect(self, provider: str) -> Connector:
        """Disconnect a provider and clear its files."""
        connector = await self._connector_repo.get_by_provider(provider)
        if not connector:
            connector = Connector(
                provider=ConnectorProvider(provider),
                status=ConnectorStatus.DISCONNECTED,
            )
            return await self._connector_repo.create(connector)

        await self._connector_repo.delete_files(connector.id)
        connector.status = ConnectorStatus.DISCONNECTED
        connector.connected_at = None
        connector.file_count = 0
        return await self._connector_repo.update(connector)

    async def search_files(
        self, query: str, provider: str | None = None
    ) -> list[ConnectorFile]:
        """Search across connected file contents."""
        connector_id = None
        if provider:
            connector = await self._connector_repo.get_by_provider(provider)
            if connector:
                connector_id = connector.id
        return await self._file_repo.search(query, connector_id)
```

**Step 4: Commit**

```bash
git add backend/app/services/connector_service.py backend/tests/test_connector_service.py
git commit -m "feat: add ConnectorService with mock connect/disconnect/search"
```

---

### Task 13: Add Connector API Routes

**Files:**
- Create: `backend/app/api/v1/connectors.py`
- Modify: `backend/app/api/schemas.py` — add connector schemas
- Modify: `backend/app/api/dependencies.py` — add connector DI
- Modify: `backend/app/main.py` — register router

**Step 1: Add schemas**

Add to `backend/app/api/schemas.py`:

```python
# --- Connectors ---

class ConnectorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    provider: str
    status: str
    file_count: int
    connected_at: datetime | None

class ConnectorFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    connector_id: str
    name: str
    path: str
    file_type: str
    text_content: str
    indexed_at: datetime
```

**Step 2: Add DI wiring**

Add to `backend/app/api/dependencies.py`:

```python
from app.infrastructure.persistence.connector_repo import (
    SqlAlchemyConnectorRepository,
    SqlAlchemyConnectorFileRepository,
)
from app.services.connector_service import ConnectorService


async def get_connector_service(
    session: AsyncSession = Depends(get_db_session),
) -> ConnectorService:
    return ConnectorService(
        connector_repo=SqlAlchemyConnectorRepository(session),
        file_repo=SqlAlchemyConnectorFileRepository(session),
    )
```

**Step 3: Create routes**

Create `backend/app/api/v1/connectors.py`:

```python
"""Connector management endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_connector_service
from app.api.schemas import ConnectorResponse
from app.services.connector_service import ConnectorService

router = APIRouter(prefix="/connectors", tags=["connectors"])

VALID_PROVIDERS = {"onedrive", "box", "google_drive", "sharepoint"}


@router.get("", response_model=list[ConnectorResponse])
async def list_connectors(
    service: ConnectorService = Depends(get_connector_service),
):
    connectors = await service.list_connectors()
    return [ConnectorResponse(
        id=str(c.id), provider=c.provider.value, status=c.status.value,
        file_count=c.file_count, connected_at=c.connected_at,
    ) for c in connectors]


@router.post("/{provider}/connect", response_model=ConnectorResponse)
async def connect_provider(
    provider: str,
    service: ConnectorService = Depends(get_connector_service),
):
    if provider not in VALID_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    connector = await service.connect(provider)
    return ConnectorResponse(
        id=str(connector.id), provider=connector.provider.value,
        status=connector.status.value, file_count=connector.file_count,
        connected_at=connector.connected_at,
    )


@router.post("/{provider}/disconnect", response_model=ConnectorResponse)
async def disconnect_provider(
    provider: str,
    service: ConnectorService = Depends(get_connector_service),
):
    if provider not in VALID_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    connector = await service.disconnect(provider)
    return ConnectorResponse(
        id=str(connector.id), provider=connector.provider.value,
        status=connector.status.value, file_count=connector.file_count,
        connected_at=connector.connected_at,
    )
```

**Step 4: Register router in main.py**

```python
from app.api.v1.connectors import router as connectors_router
app.include_router(connectors_router, prefix="/v1")
```

**Step 5: Run tests**

Run: `cd backend && python -m pytest tests/test_connector_service.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/api/v1/connectors.py backend/app/api/schemas.py backend/app/api/dependencies.py backend/app/main.py
git commit -m "feat: add connector API routes (list, connect, disconnect)"
```

---

### Task 14: Add connected_files_search Tool to Chat Agent

**Files:**
- Modify: `backend/app/services/chat_service.py`

**Step 1: Write test for file search tool**

Add to `backend/tests/test_connector_service.py`:

```python
@pytest.mark.asyncio
async def test_chat_agent_can_search_connected_files(client):
    # Connect onedrive
    await client.post("/v1/connectors/onedrive/connect")

    # Create exploration + session
    resp = await client.post("/v1/explorations", json={"name": "Test"})
    exploration_id = resp.json()["id"]
    resp = await client.post(
        f"/v1/explorations/{exploration_id}/sessions",
        json={"title": "Test Chat"},
    )
    session_id = resp.json()["id"]

    # Send a message asking about connected files
    resp = await client.post(
        f"/v1/sessions/{session_id}/messages",
        json={"content": "Search my connected files for Sunrise Senior Living rent roll"},
    )
    assert resp.status_code in (200, 201)
```

**Step 2: Add tool definition**

In `chat_service.py`, add to `TOOL_DEFINITIONS`:

```python
{
    "type": "function",
    "function": {
        "name": "connected_files_search",
        "description": "Search across the user's connected file storage (OneDrive, Box, Google Drive, SharePoint) for documents matching a query. Use this when the user asks about their own files, internal documents, rent rolls, financial statements, or any data from their connected sources.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find relevant files",
                },
                "provider": {
                    "type": "string",
                    "description": "Optional: filter by provider (onedrive, box, google_drive, sharepoint)",
                    "enum": ["onedrive", "box", "google_drive", "sharepoint"],
                },
            },
            "required": ["query"],
        },
    },
},
```

**Step 3: Handle tool execution in the agentic loop**

In the tool execution section of `send_message()`, add handling for `connected_files_search` alongside `web_search`:

```python
elif tool_name == "connected_files_search":
    query = args.get("query", "")
    provider = args.get("provider")
    files = await self._connector_service.search_files(query, provider)
    result_str = json.dumps([
        {
            "name": f.name,
            "path": f.path,
            "file_type": f.file_type,
            "relevant_content": f.text_content,
            "source": "connected_files",
        }
        for f in files
    ])
```

**Step 4: Inject ConnectorService into ChatService**

Update `ChatService.__init__` to accept a `connector_service` parameter. Update `dependencies.py` `get_chat_service()` to inject it.

**Step 5: Run tests**

Run: `cd backend && python -m pytest tests/test_connector_service.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/services/chat_service.py backend/app/api/dependencies.py backend/tests/test_connector_service.py
git commit -m "feat: add connected_files_search tool to chat agent"
```

---

### Task 15: Build Connectors Frontend Page

**Files:**
- Create: `frontend/src/app/connectors/page.tsx`
- Create: `frontend/src/services/connector.service.ts`
- Modify: `frontend/src/interfaces/api.ts` — add Connector types

**Step 1: Add TypeScript types**

Add to `frontend/src/interfaces/api.ts`:

```typescript
export interface Connector {
  id: string;
  provider: string;
  status: "connected" | "disconnected";
  file_count: number;
  connected_at: string | null;
}
```

**Step 2: Create connector service**

Create `frontend/src/services/connector.service.ts`:

```typescript
import { apiFetch } from "./api-client";
import type { Connector } from "@/interfaces/api";

export const connectorService = {
  async list(): Promise<Connector[]> {
    return apiFetch<Connector[]>("/connectors");
  },
  async connect(provider: string): Promise<Connector> {
    return apiFetch<Connector>(`/connectors/${provider}/connect`, { method: "POST" });
  },
  async disconnect(provider: string): Promise<Connector> {
    return apiFetch<Connector>(`/connectors/${provider}/disconnect`, { method: "POST" });
  },
};
```

**Step 3: Create connectors page**

Create `frontend/src/app/connectors/page.tsx`:

```tsx
"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { connectorService } from "@/services/connector.service";
import type { Connector } from "@/interfaces/api";

const PROVIDER_META: Record<string, { label: string; description: string }> = {
  onedrive: { label: "OneDrive", description: "Microsoft OneDrive and SharePoint personal files" },
  box: { label: "Box", description: "Box cloud storage and collaboration" },
  google_drive: { label: "Google Drive", description: "Google Drive documents and folders" },
  sharepoint: { label: "SharePoint", description: "Microsoft SharePoint team sites" },
};

export default function ConnectorsPage() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    connectorService
      .list()
      .then(setConnectors)
      .catch((err) => console.error("Failed to load connectors", err))
      .finally(() => setLoading(false));
  }, []);

  const handleToggle = useCallback(async (provider: string, currentStatus: string) => {
    setActionLoading(provider);
    try {
      const updated =
        currentStatus === "connected"
          ? await connectorService.disconnect(provider)
          : await connectorService.connect(provider);
      setConnectors((prev) =>
        prev.map((c) => (c.provider === provider ? updated : c))
      );
    } catch (err) {
      console.error("Failed to toggle connector", err);
    } finally {
      setActionLoading(null);
    }
  }, []);

  if (loading) {
    return <div className="text-muted-foreground">Loading connectors...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Connectors</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Connect your file storage to search across your documents in chat.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {connectors.map((c) => {
          const meta = PROVIDER_META[c.provider] ?? { label: c.provider, description: "" };
          const isConnected = c.status === "connected";
          return (
            <Card key={c.provider}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{meta.label}</CardTitle>
                  <Badge variant={isConnected ? "default" : "secondary"}>
                    {isConnected ? "Connected" : "Not Connected"}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{meta.description}</p>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    {isConnected
                      ? `${c.file_count} files indexed`
                      : "No files indexed"}
                  </div>
                  <Button
                    variant={isConnected ? "outline" : "default"}
                    size="sm"
                    disabled={actionLoading === c.provider}
                    onClick={() => handleToggle(c.provider, c.status)}
                  >
                    {actionLoading === c.provider
                      ? "..."
                      : isConnected
                        ? "Disconnect"
                        : "Connect"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
```

**Step 4: Verify page renders**

Run: `cd frontend && npm run dev`
Navigate to `/connectors`. Should see 4 connector cards. Click "Connect" on one — status should change.

**Step 5: Commit**

```bash
git add frontend/src/app/connectors/page.tsx frontend/src/services/connector.service.ts frontend/src/interfaces/api.ts
git commit -m "feat: add connectors page with mock connect/disconnect"
```

---

### Task 16: Make Search Bar Connector Chips Dynamic

**Files:**
- Modify: `frontend/src/components/exploration/search-bar.tsx`

**Step 1: Update SearchBar to accept dynamic connectors**

Replace the hardcoded `CONNECTORS` array with a prop. The search bar should show Tavily (always enabled) plus any connected external sources.

Add prop:

```typescript
interface SearchBarProps {
  onSearch: (query: string, connectors: string[]) => void;
  onUploadOM?: (file: File) => void;
  loading?: boolean;
  connectedSources?: string[]; // provider names that are connected
}
```

Build the chips list dynamically:

```typescript
const connectorChips = [
  { id: "tavily", label: "WEB SEARCH", enabled: true },
  ...["onedrive", "box", "google_drive", "sharepoint"].map((p) => ({
    id: p,
    label: p.replace("_", " ").toUpperCase(),
    enabled: connectedSources?.includes(p) ?? false,
  })),
];
```

Replace `CONNECTORS` with `connectorChips` in the JSX.

**Step 2: Pass connected sources from parent**

In `ExploreWorkspace` (explore/page.tsx), fetch connector status and pass to SearchBar:

```typescript
const [connectedSources, setConnectedSources] = useState<string[]>([]);

useEffect(() => {
  connectorService.list().then((connectors) => {
    setConnectedSources(
      connectors.filter((c) => c.status === "connected").map((c) => c.provider)
    );
  });
}, []);

// In JSX:
<SearchBar
  onSearch={handleSearch}
  onUploadOM={handleUploadOM}
  loading={searchLoading || sending}
  connectedSources={connectedSources}
/>
```

**Step 3: Commit**

```bash
git add frontend/src/components/exploration/search-bar.tsx frontend/src/app/explore/page.tsx
git commit -m "feat: make search bar connector chips dynamic based on connected sources"
```

---

## Phase 3: Report Generator

### Task 17: Add Report Domain Entities

**Files:**
- Create: `backend/app/domain/entities/report.py`
- Modify: `backend/app/domain/value_objects/enums.py`

**Step 1: Add enums**

Add to `enums.py`:

```python
class ReportFormat(StrEnum):
    PPTX = "pptx"
    XLSX = "xlsx"


class ReportJobStatus(StrEnum):
    DRAFT = "draft"
    COMPLETED = "completed"
```

**Step 2: Create entities**

Create `backend/app/domain/entities/report.py`:

```python
"""Report template and job domain entities."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class FillableRegion:
    """A detected fillable area in a template."""
    region_id: str
    label: str
    sheet_or_slide: str  # e.g., "Slide 3" or "Sheet1"
    region_type: str  # "table", "text", "placeholder"
    headers: list[str] = field(default_factory=list)
    row_count: int = 0


@dataclass
class ReportTemplate:
    name: str
    file_format: str  # "pptx" or "xlsx"
    file_path: str
    regions: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class ReportJob:
    template_id: str
    name: str
    fills: dict = field(default_factory=dict)  # region_id -> filled data
    status: str = "draft"
    output_file_path: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid4()))
```

**Step 3: Commit**

```bash
git add backend/app/domain/entities/report.py backend/app/domain/value_objects/enums.py
git commit -m "feat: add ReportTemplate and ReportJob domain entities"
```

---

### Task 18: Add Report ORM Models

**Files:**
- Modify: `backend/app/infrastructure/persistence/models.py`
- Modify: `backend/app/infrastructure/persistence/mappers.py`

**Step 1: Add ORM models**

Add to `models.py`:

```python
# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


class ReportTemplateModel(Base):
    __tablename__ = "report_templates"

    id = Column(UUIDType, primary_key=True)
    name = Column(String, nullable=False)
    file_format = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    regions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False)

    jobs = relationship("ReportJobModel", back_populates="template", cascade="all, delete-orphan")


class ReportJobModel(Base):
    __tablename__ = "report_jobs"

    id = Column(UUIDType, primary_key=True)
    template_id = Column(UUIDType, ForeignKey("report_templates.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    fills = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False, default="draft")
    output_file_path = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)

    template = relationship("ReportTemplateModel", back_populates="jobs")
```

**Step 2: Add mappers**

Add to `mappers.py`:

```python
from app.domain.entities.report import ReportTemplate, ReportJob

def report_template_entity_to_model(entity: ReportTemplate) -> ReportTemplateModel:
    return ReportTemplateModel(
        id=entity.id, name=entity.name, file_format=entity.file_format,
        file_path=entity.file_path, regions=entity.regions, created_at=entity.created_at,
    )

def report_template_model_to_entity(model: ReportTemplateModel) -> ReportTemplate:
    return ReportTemplate(
        id=str(model.id), name=model.name, file_format=model.file_format,
        file_path=model.file_path, regions=model.regions or [], created_at=model.created_at,
    )

def report_job_entity_to_model(entity: ReportJob) -> ReportJobModel:
    return ReportJobModel(
        id=entity.id, template_id=entity.template_id, name=entity.name,
        fills=entity.fills, status=entity.status,
        output_file_path=entity.output_file_path, created_at=entity.created_at,
    )

def report_job_model_to_entity(model: ReportJobModel) -> ReportJob:
    return ReportJob(
        id=str(model.id), template_id=str(model.template_id), name=model.name,
        fills=model.fills or {}, status=model.status,
        output_file_path=model.output_file_path, created_at=model.created_at,
    )
```

**Step 3: Commit**

```bash
git add backend/app/infrastructure/persistence/models.py backend/app/infrastructure/persistence/mappers.py
git commit -m "feat: add Report ORM models and mappers"
```

---

### Task 19: Add Report Repository

**Files:**
- Create: `backend/app/infrastructure/persistence/report_repo.py`

**Step 1: Implement repository**

```python
"""Report template and job repositories."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.report import ReportTemplate, ReportJob
from app.infrastructure.persistence.mappers import (
    report_template_entity_to_model, report_template_model_to_entity,
    report_job_entity_to_model, report_job_model_to_entity,
)
from app.infrastructure.persistence.models import ReportTemplateModel, ReportJobModel


class SqlAlchemyReportTemplateRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, entity: ReportTemplate) -> ReportTemplate:
        model = report_template_entity_to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return report_template_model_to_entity(model)

    async def get_by_id(self, template_id: str) -> ReportTemplate | None:
        result = await self._session.execute(
            select(ReportTemplateModel).where(ReportTemplateModel.id == template_id)
        )
        model = result.scalar_one_or_none()
        return report_template_model_to_entity(model) if model else None

    async def list_all(self) -> list[ReportTemplate]:
        result = await self._session.execute(
            select(ReportTemplateModel).order_by(ReportTemplateModel.created_at.desc())
        )
        return [report_template_model_to_entity(m) for m in result.scalars().all()]


class SqlAlchemyReportJobRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, entity: ReportJob) -> ReportJob:
        model = report_job_entity_to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return report_job_model_to_entity(model)

    async def get_by_id(self, job_id: str) -> ReportJob | None:
        result = await self._session.execute(
            select(ReportJobModel).where(ReportJobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        return report_job_model_to_entity(model) if model else None

    async def update(self, entity: ReportJob) -> ReportJob:
        model = report_job_entity_to_model(entity)
        merged = await self._session.merge(model)
        await self._session.flush()
        return report_job_model_to_entity(merged)

    async def list_all(self) -> list[ReportJob]:
        result = await self._session.execute(
            select(ReportJobModel).order_by(ReportJobModel.created_at.desc())
        )
        return [report_job_model_to_entity(m) for m in result.scalars().all()]
```

**Step 2: Commit**

```bash
git add backend/app/infrastructure/persistence/report_repo.py
git commit -m "feat: add report template and job repositories"
```

---

### Task 20: Add Report Service (Template Parsing + Fill + Export)

**Files:**
- Create: `backend/app/services/report_service.py`

This is the core report logic. It parses templates to detect fillable regions and generates filled output files.

**Step 1: Write test**

Create `backend/tests/test_report_service.py`:

```python
"""Tests for ReportService."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import io
from openpyxl import Workbook


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def make_test_xlsx() -> bytes:
    """Create a minimal XLSX template with a fillable table."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Portfolio Summary"
    ws["A1"] = "Property"
    ws["B1"] = "NOI"
    ws["C1"] = "Cap Rate"
    ws["A2"] = "{{property_1}}"
    ws["B2"] = "{{noi_1}}"
    ws["C2"] = "{{cap_rate_1}}"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_upload_template_detects_regions(client):
    xlsx_bytes = make_test_xlsx()
    files = {"file": ("template.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    resp = await client.post("/v1/report-templates", files=files)
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["regions"]) > 0
    assert data["file_format"] == "xlsx"


@pytest.mark.asyncio
async def test_create_job_and_generate(client):
    # Upload template
    xlsx_bytes = make_test_xlsx()
    files = {"file": ("template.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    resp = await client.post("/v1/report-templates", files=files)
    template_id = resp.json()["id"]

    # Create job
    resp = await client.post("/v1/report-jobs", json={
        "template_id": template_id,
        "name": "Q4 Report",
    })
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Update fills
    regions = resp.json()["fills"]  # empty initially
    resp = await client.patch(f"/v1/report-jobs/{job_id}", json={
        "fills": {
            "region_0": {
                "rows": [["Sunrise Phoenix", "$1,863,000", "6.2%"]]
            }
        }
    })
    assert resp.status_code == 200

    # Generate
    resp = await client.post(f"/v1/report-jobs/{job_id}/generate")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
```

**Step 2: Implement ReportService**

Create `backend/app/services/report_service.py`:

```python
"""Report service — template parsing, fill management, export generation."""
import io
import json
import re
from uuid import uuid4

from openpyxl import load_workbook

from app.domain.entities.report import ReportTemplate, ReportJob, FillableRegion
from app.domain.interfaces.providers import FileStorage
from app.infrastructure.persistence.report_repo import (
    SqlAlchemyReportTemplateRepository,
    SqlAlchemyReportJobRepository,
)

MARKER_PATTERN = re.compile(r"\{\{(\w+)\}\}")


class ReportService:
    def __init__(
        self,
        template_repo: SqlAlchemyReportTemplateRepository,
        job_repo: SqlAlchemyReportJobRepository,
        file_storage: FileStorage,
    ):
        self._template_repo = template_repo
        self._job_repo = job_repo
        self._file_storage = file_storage

    # --- Template operations ---

    async def upload_template(
        self, filename: str, file_bytes: bytes
    ) -> ReportTemplate:
        """Upload a template file, detect fillable regions, persist."""
        file_format = "xlsx" if filename.endswith(".xlsx") else "pptx"

        # Store the file
        file_path = await self._file_storage.store(
            f"report_templates/{uuid4()}_{filename}", file_bytes
        )

        # Detect regions
        if file_format == "xlsx":
            regions = self._detect_xlsx_regions(file_bytes)
        else:
            regions = self._detect_pptx_regions(file_bytes)

        template = ReportTemplate(
            name=filename.rsplit(".", 1)[0].replace("_", " ").title(),
            file_format=file_format,
            file_path=file_path,
            regions=[self._region_to_dict(r) for r in regions],
        )
        return await self._template_repo.create(template)

    async def get_template(self, template_id: str) -> ReportTemplate | None:
        return await self._template_repo.get_by_id(template_id)

    async def list_templates(self) -> list[ReportTemplate]:
        return await self._template_repo.list_all()

    # --- Job operations ---

    async def create_job(self, template_id: str, name: str) -> ReportJob:
        job = ReportJob(template_id=template_id, name=name)
        return await self._job_repo.create(job)

    async def update_fills(self, job_id: str, fills: dict) -> ReportJob:
        job = await self._job_repo.get_by_id(job_id)
        if not job:
            raise ValueError("Job not found")
        job.fills.update(fills)
        return await self._job_repo.update(job)

    async def generate(self, job_id: str) -> ReportJob:
        """Generate the filled report from template + fills."""
        job = await self._job_repo.get_by_id(job_id)
        if not job:
            raise ValueError("Job not found")
        template = await self._template_repo.get_by_id(job.template_id)
        if not template:
            raise ValueError("Template not found")

        template_bytes = await self._file_storage.retrieve(template.file_path)

        if template.file_format == "xlsx":
            output_bytes = self._fill_xlsx(template_bytes, template.regions, job.fills)
        else:
            output_bytes = self._fill_pptx(template_bytes, template.regions, job.fills)

        output_path = await self._file_storage.store(
            f"report_outputs/{uuid4()}_{job.name}.{template.file_format}",
            output_bytes,
        )
        job.output_file_path = output_path
        job.status = "completed"
        return await self._job_repo.update(job)

    async def get_job(self, job_id: str) -> ReportJob | None:
        return await self._job_repo.get_by_id(job_id)

    async def list_jobs(self) -> list[ReportJob]:
        return await self._job_repo.list_all()

    async def download(self, job_id: str) -> tuple[bytes, str]:
        """Return (file_bytes, filename) for download."""
        job = await self._job_repo.get_by_id(job_id)
        if not job or not job.output_file_path:
            raise ValueError("Report not generated yet")
        template = await self._template_repo.get_by_id(job.template_id)
        file_bytes = await self._file_storage.retrieve(job.output_file_path)
        ext = template.file_format if template else "xlsx"
        return file_bytes, f"{job.name}.{ext}"

    # --- Region detection ---

    def _detect_xlsx_regions(self, file_bytes: bytes) -> list[FillableRegion]:
        wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
        regions = []
        for idx, ws in enumerate(wb.worksheets):
            headers = []
            has_markers = False
            for row in ws.iter_rows(min_row=1, max_row=1):
                headers = [str(cell.value or "") for cell in row if cell.value]
            for row in ws.iter_rows(min_row=2):
                for cell in row:
                    if cell.value and MARKER_PATTERN.search(str(cell.value)):
                        has_markers = True
                        break
            if headers and has_markers:
                regions.append(FillableRegion(
                    region_id=f"region_{idx}",
                    label=ws.title or f"Sheet {idx+1}",
                    sheet_or_slide=ws.title or f"Sheet {idx+1}",
                    region_type="table",
                    headers=headers,
                    row_count=ws.max_row - 1 if ws.max_row else 0,
                ))
        return regions

    def _detect_pptx_regions(self, file_bytes: bytes) -> list[FillableRegion]:
        try:
            from pptx import Presentation
        except ImportError:
            return []
        prs = Presentation(io.BytesIO(file_bytes))
        regions = []
        for slide_idx, slide in enumerate(prs.slides):
            for shape in slide.shapes:
                if shape.has_table:
                    table = shape.table
                    headers = [cell.text for cell in table.rows[0].cells]
                    has_markers = any(
                        MARKER_PATTERN.search(cell.text)
                        for row in table.rows[1:]
                        for cell in row.cells
                    )
                    if has_markers or headers:
                        regions.append(FillableRegion(
                            region_id=f"region_{slide_idx}_{shape.shape_id}",
                            label=f"Slide {slide_idx+1} - Table",
                            sheet_or_slide=f"Slide {slide_idx+1}",
                            region_type="table",
                            headers=headers,
                            row_count=len(table.rows) - 1,
                        ))
                elif shape.has_text_frame:
                    text = shape.text_frame.text
                    if MARKER_PATTERN.search(text):
                        regions.append(FillableRegion(
                            region_id=f"region_{slide_idx}_{shape.shape_id}",
                            label=f"Slide {slide_idx+1} - Text",
                            sheet_or_slide=f"Slide {slide_idx+1}",
                            region_type="text",
                            headers=[],
                        ))
        return regions

    # --- Fill logic ---

    def _fill_xlsx(self, template_bytes: bytes, regions: list[dict], fills: dict) -> bytes:
        wb = load_workbook(io.BytesIO(template_bytes))
        for region in regions:
            region_id = region.get("region_id", "")
            fill_data = fills.get(region_id, {})
            rows = fill_data.get("rows", [])
            sheet_name = region.get("sheet_or_slide", "")
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                for row_idx, row_data in enumerate(rows):
                    for col_idx, value in enumerate(row_data):
                        ws.cell(row=row_idx + 2, column=col_idx + 1, value=value)

        # Also replace any remaining {{marker}} placeholders with fill values
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for cell in row:
                    if cell.value and isinstance(cell.value, str):
                        for match in MARKER_PATTERN.finditer(cell.value):
                            marker_key = match.group(1)
                            # Check all fills for a matching key
                            for fill_data in fills.values():
                                if marker_key in fill_data:
                                    cell.value = cell.value.replace(
                                        match.group(0), str(fill_data[marker_key])
                                    )

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def _fill_pptx(self, template_bytes: bytes, regions: list[dict], fills: dict) -> bytes:
        try:
            from pptx import Presentation
        except ImportError:
            return template_bytes
        prs = Presentation(io.BytesIO(template_bytes))

        # Replace markers in all text frames
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_table:
                    table = shape.table
                    for row in table.rows:
                        for cell in row.cells:
                            for match in MARKER_PATTERN.finditer(cell.text):
                                marker_key = match.group(1)
                                for fill_data in fills.values():
                                    if marker_key in fill_data:
                                        cell.text = cell.text.replace(
                                            match.group(0), str(fill_data[marker_key])
                                        )
                    # Fill table rows from region fills
                    for region in regions:
                        region_id = region.get("region_id", "")
                        fill_data = fills.get(region_id, {})
                        rows = fill_data.get("rows", [])
                        for row_idx, row_data in enumerate(rows):
                            if row_idx + 1 < len(table.rows):
                                for col_idx, value in enumerate(row_data):
                                    if col_idx < len(table.rows[row_idx + 1].cells):
                                        table.rows[row_idx + 1].cells[col_idx].text = str(value)

                elif shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            for match in MARKER_PATTERN.finditer(run.text):
                                marker_key = match.group(1)
                                for fill_data in fills.values():
                                    if marker_key in fill_data:
                                        run.text = run.text.replace(
                                            match.group(0), str(fill_data[marker_key])
                                        )

        buf = io.BytesIO()
        prs.save(buf)
        return buf.getvalue()

    @staticmethod
    def _region_to_dict(region: FillableRegion) -> dict:
        return {
            "region_id": region.region_id,
            "label": region.label,
            "sheet_or_slide": region.sheet_or_slide,
            "region_type": region.region_type,
            "headers": region.headers,
            "row_count": region.row_count,
        }
```

**Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_report_service.py -v`
Expected: FAIL (endpoints not wired yet — will pass after Task 21).

**Step 4: Commit**

```bash
git add backend/app/services/report_service.py backend/tests/test_report_service.py
git commit -m "feat: add ReportService with template parsing, fill, and export"
```

---

### Task 21: Add Report API Routes

**Files:**
- Create: `backend/app/api/v1/reports.py`
- Modify: `backend/app/api/schemas.py`
- Modify: `backend/app/api/dependencies.py`
- Modify: `backend/app/main.py`

**Step 1: Add schemas**

Add to `backend/app/api/schemas.py`:

```python
# --- Reports ---

class ReportTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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
    model_config = ConfigDict(from_attributes=True)
    id: str
    template_id: str
    name: str
    fills: dict
    status: str
    created_at: datetime
```

**Step 2: Add DI wiring**

Add to `dependencies.py`:

```python
from app.infrastructure.persistence.report_repo import (
    SqlAlchemyReportTemplateRepository,
    SqlAlchemyReportJobRepository,
)
from app.services.report_service import ReportService


async def get_report_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReportService:
    return ReportService(
        template_repo=SqlAlchemyReportTemplateRepository(session),
        job_repo=SqlAlchemyReportJobRepository(session),
        file_storage=_file_storage,
    )
```

**Step 3: Create routes**

Create `backend/app/api/v1/reports.py`:

```python
"""Report template and job endpoints."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.dependencies import get_report_service
from app.api.schemas import (
    ReportTemplateResponse,
    CreateReportJobRequest,
    UpdateReportJobRequest,
    ReportJobResponse,
)
from app.services.report_service import ReportService

router = APIRouter(tags=["reports"])


# --- Templates ---

@router.post("/report-templates", status_code=201, response_model=ReportTemplateResponse)
async def upload_template(
    file: UploadFile = File(...),
    service: ReportService = Depends(get_report_service),
):
    if not file.filename or not (file.filename.endswith(".xlsx") or file.filename.endswith(".pptx")):
        raise HTTPException(400, "Only .xlsx and .pptx files are supported")
    file_bytes = await file.read()
    template = await service.upload_template(file.filename, file_bytes)
    return ReportTemplateResponse(
        id=str(template.id), name=template.name, file_format=template.file_format,
        regions=template.regions, created_at=template.created_at,
    )


@router.get("/report-templates", response_model=list[ReportTemplateResponse])
async def list_templates(service: ReportService = Depends(get_report_service)):
    templates = await service.list_templates()
    return [
        ReportTemplateResponse(
            id=str(t.id), name=t.name, file_format=t.file_format,
            regions=t.regions, created_at=t.created_at,
        ) for t in templates
    ]


@router.get("/report-templates/{template_id}", response_model=ReportTemplateResponse)
async def get_template(
    template_id: str,
    service: ReportService = Depends(get_report_service),
):
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    return ReportTemplateResponse(
        id=str(template.id), name=template.name, file_format=template.file_format,
        regions=template.regions, created_at=template.created_at,
    )


# --- Jobs ---

@router.post("/report-jobs", status_code=201, response_model=ReportJobResponse)
async def create_job(
    body: CreateReportJobRequest,
    service: ReportService = Depends(get_report_service),
):
    job = await service.create_job(body.template_id, body.name)
    return ReportJobResponse(
        id=str(job.id), template_id=str(job.template_id), name=job.name,
        fills=job.fills, status=job.status, created_at=job.created_at,
    )


@router.patch("/report-jobs/{job_id}", response_model=ReportJobResponse)
async def update_job_fills(
    job_id: str,
    body: UpdateReportJobRequest,
    service: ReportService = Depends(get_report_service),
):
    try:
        job = await service.update_fills(job_id, body.fills)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return ReportJobResponse(
        id=str(job.id), template_id=str(job.template_id), name=job.name,
        fills=job.fills, status=job.status, created_at=job.created_at,
    )


@router.post("/report-jobs/{job_id}/generate", response_model=ReportJobResponse)
async def generate_report(
    job_id: str,
    service: ReportService = Depends(get_report_service),
):
    try:
        job = await service.generate(job_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return ReportJobResponse(
        id=str(job.id), template_id=str(job.template_id), name=job.name,
        fills=job.fills, status=job.status, created_at=job.created_at,
    )


@router.get("/report-jobs/{job_id}/download")
async def download_report(
    job_id: str,
    service: ReportService = Depends(get_report_service),
):
    try:
        file_bytes, filename = await service.download(job_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    media_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if filename.endswith(".xlsx")
        else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/report-jobs", response_model=list[ReportJobResponse])
async def list_jobs(service: ReportService = Depends(get_report_service)):
    jobs = await service.list_jobs()
    return [
        ReportJobResponse(
            id=str(j.id), template_id=str(j.template_id), name=j.name,
            fills=j.fills, status=j.status, created_at=j.created_at,
        ) for j in jobs
    ]
```

**Step 4: Register router**

Add to `main.py`:

```python
from app.api.v1.reports import router as reports_router
app.include_router(reports_router, prefix="/v1")
```

**Step 5: Install python-pptx**

```bash
cd backend && pip install python-pptx
```

Add `python-pptx` to the project's dependencies (pyproject.toml or setup.cfg).

**Step 6: Run tests**

Run: `cd backend && python -m pytest tests/test_report_service.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/app/api/v1/reports.py backend/app/api/schemas.py backend/app/api/dependencies.py backend/app/main.py
git commit -m "feat: add report API routes (templates, jobs, generate, download)"
```

---

### Task 22: Build Reports Frontend — Templates List and Upload

**Files:**
- Create: `frontend/src/app/reports/page.tsx`
- Create: `frontend/src/services/report.service.ts`
- Modify: `frontend/src/interfaces/api.ts`

**Step 1: Add TypeScript types**

Add to `frontend/src/interfaces/api.ts`:

```typescript
export interface FillableRegion {
  region_id: string;
  label: string;
  sheet_or_slide: string;
  region_type: string;
  headers: string[];
  row_count: number;
}

export interface ReportTemplate {
  id: string;
  name: string;
  file_format: string;
  regions: FillableRegion[];
  created_at: string;
}

export interface ReportJob {
  id: string;
  template_id: string;
  name: string;
  fills: Record<string, unknown>;
  status: string;
  created_at: string;
}
```

**Step 2: Create report service**

Create `frontend/src/services/report.service.ts`:

```typescript
import { apiFetch, apiUpload } from "./api-client";
import type { ReportTemplate, ReportJob } from "@/interfaces/api";

export const reportService = {
  async uploadTemplate(file: File): Promise<ReportTemplate> {
    const formData = new FormData();
    formData.append("file", file);
    return apiUpload<ReportTemplate>("/report-templates", formData);
  },
  async listTemplates(): Promise<ReportTemplate[]> {
    return apiFetch<ReportTemplate[]>("/report-templates");
  },
  async getTemplate(id: string): Promise<ReportTemplate> {
    return apiFetch<ReportTemplate>(`/report-templates/${id}`);
  },
  async createJob(templateId: string, name: string): Promise<ReportJob> {
    return apiFetch<ReportJob>("/report-jobs", {
      method: "POST",
      body: JSON.stringify({ template_id: templateId, name }),
    });
  },
  async updateFills(jobId: string, fills: Record<string, unknown>): Promise<ReportJob> {
    return apiFetch<ReportJob>(`/report-jobs/${jobId}`, {
      method: "PATCH",
      body: JSON.stringify({ fills }),
    });
  },
  async generate(jobId: string): Promise<ReportJob> {
    return apiFetch<ReportJob>(`/report-jobs/${jobId}/generate`, { method: "POST" });
  },
  async listJobs(): Promise<ReportJob[]> {
    return apiFetch<ReportJob[]>("/report-jobs");
  },
  downloadUrl(jobId: string): string {
    const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/v1";
    return `${base}/report-jobs/${jobId}/download`;
  },
};
```

**Step 3: Create reports page**

Create `frontend/src/app/reports/page.tsx` with:
- Two sections: "Templates" and "Generated Reports"
- Upload template button (file picker for .pptx/.xlsx)
- Template cards showing name, format, region count, date
- Generated report rows with download link
- Click template → navigate to `/reports/[templateId]/fill`

This is a substantial component. Build it as a standard list page following the patterns in the existing datasets page.

**Step 4: Verify**

Run: `cd frontend && npm run dev`
Navigate to `/reports`. Upload a template. Verify it appears in the list.

**Step 5: Commit**

```bash
git add frontend/src/app/reports/page.tsx frontend/src/services/report.service.ts frontend/src/interfaces/api.ts
git commit -m "feat: add reports page with template upload and job listing"
```

---

### Task 23: Build Copilot Fill Workflow Page

**Files:**
- Create: `frontend/src/app/reports/[id]/fill/page.tsx`

This is the section-by-section fill workflow.

**Step 1: Build the fill page**

Key structure:
- Fetch template + create a new job on mount
- Step through regions one at a time with Back/Next
- For each region, show: region label, headers, suggested data, editable cells
- Accept / Edit / Skip actions per region
- "Generate Report" button at the end
- Progress bar: "Region X of Y"

```tsx
"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { reportService } from "@/services/report.service";
import type { ReportTemplate, ReportJob, FillableRegion } from "@/interfaces/api";

export default function FillPage() {
  const params = useParams();
  const router = useRouter();
  const templateId = params.id as string;

  const [template, setTemplate] = useState<ReportTemplate | null>(null);
  const [job, setJob] = useState<ReportJob | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [fills, setFills] = useState<Record<string, { rows: string[][] }>>({});
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    async function init() {
      const tmpl = await reportService.getTemplate(templateId);
      setTemplate(tmpl);
      const newJob = await reportService.createJob(templateId, `Report - ${new Date().toLocaleDateString()}`);
      setJob(newJob);
      // Initialize empty fills for each region
      const initialFills: Record<string, { rows: string[][] }> = {};
      for (const region of tmpl.regions) {
        initialFills[region.region_id] = {
          rows: Array.from({ length: region.row_count || 1 }, () =>
            Array.from({ length: region.headers.length }, () => "")
          ),
        };
      }
      setFills(initialFills);
    }
    init();
  }, [templateId]);

  const currentRegion = template?.regions[currentIndex];
  const totalRegions = template?.regions.length ?? 0;

  const updateCell = useCallback((rowIdx: number, colIdx: number, value: string) => {
    if (!currentRegion) return;
    setFills((prev) => {
      const regionFill = { ...prev[currentRegion.region_id] };
      const newRows = regionFill.rows.map((r) => [...r]);
      newRows[rowIdx][colIdx] = value;
      return { ...prev, [currentRegion.region_id]: { rows: newRows } };
    });
  }, [currentRegion]);

  const handleNext = useCallback(async () => {
    if (!job) return;
    // Save current fills
    await reportService.updateFills(job.id, fills);
    if (currentIndex < totalRegions - 1) {
      setCurrentIndex((i) => i + 1);
    }
  }, [job, fills, currentIndex, totalRegions]);

  const handleBack = useCallback(() => {
    if (currentIndex > 0) setCurrentIndex((i) => i - 1);
  }, [currentIndex]);

  const handleGenerate = useCallback(async () => {
    if (!job) return;
    setGenerating(true);
    await reportService.updateFills(job.id, fills);
    const result = await reportService.generate(job.id);
    setJob(result);
    setGenerating(false);
  }, [job, fills]);

  if (!template || !job) {
    return <div className="text-muted-foreground">Loading template...</div>;
  }

  if (job.status === "completed") {
    return (
      <div className="text-center py-12 space-y-4">
        <h2 className="text-xl font-bold">Report Generated</h2>
        <p className="text-muted-foreground">Your report is ready for download.</p>
        <div className="flex gap-2 justify-center">
          <a href={reportService.downloadUrl(job.id)} download>
            <Button>Download Report</Button>
          </a>
          <Button variant="outline" onClick={() => router.push("/reports")}>
            Back to Reports
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{template.name}</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Fill in each section of the template. Region {currentIndex + 1} of {totalRegions}.
        </p>
        {/* Progress bar */}
        <div className="w-full bg-muted rounded-full h-2 mt-3">
          <div
            className="bg-foreground h-2 rounded-full transition-all"
            style={{ width: `${((currentIndex + 1) / totalRegions) * 100}%` }}
          />
        </div>
      </div>

      {currentRegion && (
        <div className="border rounded-lg p-6 space-y-4">
          <div>
            <h2 className="text-lg font-semibold">{currentRegion.label}</h2>
            <p className="text-sm text-muted-foreground">
              {currentRegion.sheet_or_slide} — {currentRegion.region_type}
            </p>
          </div>

          {/* Table editor */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  {currentRegion.headers.map((h, i) => (
                    <th key={i} className="text-left p-2 border-b font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(fills[currentRegion.region_id]?.rows ?? []).map((row, rowIdx) => (
                  <tr key={rowIdx}>
                    {row.map((cell, colIdx) => (
                      <td key={colIdx} className="p-1">
                        <Input
                          value={cell}
                          onChange={(e) => updateCell(rowIdx, colIdx, e.target.value)}
                          className="h-8 text-sm"
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={handleBack} disabled={currentIndex === 0}>
          Back
        </Button>
        <div className="flex gap-2">
          {currentIndex === totalRegions - 1 ? (
            <Button onClick={handleGenerate} disabled={generating}>
              {generating ? "Generating..." : "Generate Report"}
            </Button>
          ) : (
            <Button onClick={handleNext}>Next</Button>
          )}
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Verify**

Upload an XLSX template from `/reports`, then click it to open the fill workflow. Step through regions, fill data, generate.

**Step 3: Commit**

```bash
git add frontend/src/app/reports/[id]/fill/page.tsx
git commit -m "feat: add copilot fill workflow page for reports"
```

---

### Task 24: Add python-pptx Dependency

**Files:**
- Modify: `backend/pyproject.toml` or `setup.cfg` (whichever manages deps)

**Step 1: Add dependency**

Add `python-pptx>=0.6` to the project's install_requires/dependencies.

**Step 2: Install**

```bash
cd backend && pip install -e ".[dev]"
```

**Step 3: Commit**

```bash
git add backend/pyproject.toml
git commit -m "chore: add python-pptx dependency for report generation"
```

---

### Task 25: Run Full Test Suite and Fix Issues

**Step 1: Run all backend tests**

```bash
cd backend && python -m pytest tests/ -v
```

Fix any failures.

**Step 2: Run frontend build**

```bash
cd frontend && npm run build
```

Fix any TypeScript or build errors.

**Step 3: Manual smoke test**

1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Verify:
   - `/explore` is home page
   - Can create exploration, upload OM, sidebar appears
   - `/connectors` shows 4 cards, can connect/disconnect
   - Connected sources appear in search bar chips
   - Chat can search connected files
   - `/reports` shows template upload
   - Can upload XLSX template, fill, generate, download
   - `/datasets` still works

**Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve integration issues from workflow revamp"
```
