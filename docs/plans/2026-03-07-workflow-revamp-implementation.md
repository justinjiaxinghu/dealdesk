# Workflow Revamp Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform DealDesk from a linear OM-processing pipeline into a two-entry-point market intelligence platform with agentic chat-driven exploration.

**Architecture:** New domain entities (ExplorationSession, ChatSession, ChatMessage, Snapshot) with a ChatService that runs an agentic GPT-4o loop with tool calling. The frontend is restructured from a tabbed workspace to a two-pane layout (deal sidebar + chat exploration). A new `/explore` page provides free-form market research without a deal.

**Tech Stack:** Python/FastAPI (backend), Next.js/React/TypeScript (frontend), OpenAI GPT-4o (agentic chat), Tavily (web search), Recharts (charts), shadcn/ui (components)

**Design Doc:** `docs/plans/2026-03-07-workflow-revamp-design.md`

---

## Task 1: Add New Enums

**Files:**
- Modify: `backend/app/domain/value_objects/enums.py` (after line 84)

**Step 1: Add ChatRole, ConnectorType enums**

Add after the `ProcessingStepStatus` enum (line 84):

```python
class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ConnectorType(str, Enum):
    TAVILY = "tavily"
    COSTAR = "costar"
    COMPSTACK = "compstack"
    LOOPNET = "loopnet"
    REA_VISTA = "rea_vista"
```

**Step 2: Verify import works**

Run: `cd backend && python -c "from app.domain.value_objects.enums import ChatRole, ConnectorType; print(ChatRole.USER, ConnectorType.TAVILY)"`
Expected: `user tavily`

**Step 3: Commit**

```bash
git add backend/app/domain/value_objects/enums.py
git commit -m "feat: add ChatRole and ConnectorType enums"
```

---

## Task 2: Add New Domain Entities

**Files:**
- Create: `backend/app/domain/entities/exploration.py`
- Create: `backend/app/domain/entities/chat.py`
- Create: `backend/app/domain/entities/snapshot.py`

**Step 1: Write ExplorationSession entity**

Create `backend/app/domain/entities/exploration.py`:

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ExplorationSession:
    name: str
    id: UUID = field(default_factory=uuid4)
    deal_id: UUID | None = None
    saved: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Step 2: Write ChatSession and ChatMessage entities**

Create `backend/app/domain/entities/chat.py`:

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.enums import ChatRole, ConnectorType


@dataclass
class ChatSession:
    exploration_session_id: UUID
    title: str
    id: UUID = field(default_factory=uuid4)
    connectors: list[ConnectorType] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ChatMessage:
    session_id: UUID
    role: ChatRole
    content: str
    id: UUID = field(default_factory=uuid4)
    tool_calls: list[dict] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Step 3: Write Snapshot entity**

Create `backend/app/domain/entities/snapshot.py`:

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Snapshot:
    name: str
    id: UUID = field(default_factory=uuid4)
    deal_id: UUID | None = None
    session_data: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Step 4: Verify imports**

Run: `cd backend && python -c "from app.domain.entities.exploration import ExplorationSession; from app.domain.entities.chat import ChatSession, ChatMessage; from app.domain.entities.snapshot import Snapshot; print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add backend/app/domain/entities/exploration.py backend/app/domain/entities/chat.py backend/app/domain/entities/snapshot.py
git commit -m "feat: add ExplorationSession, ChatSession, ChatMessage, Snapshot entities"
```

---

## Task 3: Add ORM Models

**Files:**
- Modify: `backend/app/infrastructure/persistence/models.py` (after line 358)

**Step 1: Add ExplorationSessionModel, ChatSessionModel, ChatMessageModel, SnapshotModel**

Add after `HistoricalFinancialModel` (after line 358). Import `JSON` at the top if not already imported (it is — used by DocumentModel).

```python
class ExplorationSessionModel(Base):
    __tablename__ = "exploration_sessions"

    id = Column(UUIDType, primary_key=True)
    deal_id = Column(UUIDType, ForeignKey("deals.id"), nullable=True, index=True)
    name = Column(String, nullable=False)
    saved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False)

    deal = relationship("DealModel", backref="exploration_sessions")
    chat_sessions = relationship(
        "ChatSessionModel", back_populates="exploration_session", lazy="selectin"
    )


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUIDType, primary_key=True)
    exploration_session_id = Column(
        UUIDType, ForeignKey("exploration_sessions.id"), nullable=False, index=True
    )
    title = Column(String, nullable=False)
    connectors = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    exploration_session = relationship(
        "ExplorationSessionModel", back_populates="chat_sessions"
    )
    messages = relationship(
        "ChatMessageModel", back_populates="chat_session", lazy="selectin"
    )


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(UUIDType, primary_key=True)
    session_id = Column(
        UUIDType, ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    tool_calls = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False)

    chat_session = relationship("ChatSessionModel", back_populates="messages")


class SnapshotModel(Base):
    __tablename__ = "snapshots"

    id = Column(UUIDType, primary_key=True)
    deal_id = Column(UUIDType, ForeignKey("deals.id"), nullable=True, index=True)
    name = Column(String, nullable=False)
    session_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False)

    deal = relationship("DealModel", backref="snapshots")
```

Also add `Boolean` to the imports at the top of the file (line 3):

```python
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint, Boolean
```

**Step 2: Verify models load**

Run: `cd backend && python -c "from app.infrastructure.persistence.models import ExplorationSessionModel, ChatSessionModel, ChatMessageModel, SnapshotModel; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/infrastructure/persistence/models.py
git commit -m "feat: add ORM models for exploration, chat, and snapshot"
```

---

## Task 4: Add Mappers

**Files:**
- Modify: `backend/app/infrastructure/persistence/mappers.py` (after line 410)

**Step 1: Add mapper functions for all new entities**

Add imports at top of file:

```python
from app.domain.entities.exploration import ExplorationSession
from app.domain.entities.chat import ChatSession, ChatMessage
from app.domain.entities.snapshot import Snapshot
from app.domain.value_objects.enums import ChatRole, ConnectorType
from app.infrastructure.persistence.models import (
    ExplorationSessionModel,
    ChatSessionModel,
    ChatMessageModel,
    SnapshotModel,
)
```

Add mapper functions after the last existing mapper:

```python
# --- ExplorationSession ---

def exploration_session_to_entity(model: ExplorationSessionModel) -> ExplorationSession:
    return ExplorationSession(
        id=model.id,
        deal_id=model.deal_id,
        name=model.name,
        saved=model.saved,
        created_at=model.created_at,
    )


def exploration_session_to_model(entity: ExplorationSession) -> ExplorationSessionModel:
    return ExplorationSessionModel(
        id=entity.id,
        deal_id=entity.deal_id,
        name=entity.name,
        saved=entity.saved,
        created_at=entity.created_at,
    )


# --- ChatSession ---

def chat_session_to_entity(model: ChatSessionModel) -> ChatSession:
    return ChatSession(
        id=model.id,
        exploration_session_id=model.exploration_session_id,
        title=model.title,
        connectors=[ConnectorType(c) for c in (model.connectors or [])],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def chat_session_to_model(entity: ChatSession) -> ChatSessionModel:
    return ChatSessionModel(
        id=entity.id,
        exploration_session_id=entity.exploration_session_id,
        title=entity.title,
        connectors=[c.value for c in entity.connectors],
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


# --- ChatMessage ---

def chat_message_to_entity(model: ChatMessageModel) -> ChatMessage:
    return ChatMessage(
        id=model.id,
        session_id=model.session_id,
        role=ChatRole(model.role),
        content=model.content,
        tool_calls=model.tool_calls,
        created_at=model.created_at,
    )


def chat_message_to_model(entity: ChatMessage) -> ChatMessageModel:
    return ChatMessageModel(
        id=entity.id,
        session_id=entity.session_id,
        role=entity.role.value,
        content=entity.content,
        tool_calls=entity.tool_calls,
        created_at=entity.created_at,
    )


# --- Snapshot ---

def snapshot_to_entity(model: SnapshotModel) -> Snapshot:
    return Snapshot(
        id=model.id,
        deal_id=model.deal_id,
        name=model.name,
        session_data=model.session_data or {},
        created_at=model.created_at,
    )


def snapshot_to_model(entity: Snapshot) -> SnapshotModel:
    return SnapshotModel(
        id=entity.id,
        deal_id=entity.deal_id,
        name=entity.name,
        session_data=entity.session_data,
        created_at=entity.created_at,
    )
```

**Step 2: Verify mappers import**

Run: `cd backend && python -c "from app.infrastructure.persistence.mappers import exploration_session_to_entity, chat_session_to_entity, chat_message_to_entity, snapshot_to_entity; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/infrastructure/persistence/mappers.py
git commit -m "feat: add mappers for exploration, chat, and snapshot entities"
```

---

## Task 5: Add Repository Interfaces

**Files:**
- Modify: `backend/app/domain/interfaces/repositories.py` (after line 128)

**Step 1: Add repository ABCs**

Add imports at top:

```python
from app.domain.entities.exploration import ExplorationSession
from app.domain.entities.chat import ChatSession, ChatMessage
from app.domain.entities.snapshot import Snapshot
```

Add after `HistoricalFinancialRepository` (after line 128):

```python
class ExplorationSessionRepository(ABC):
    @abstractmethod
    async def create(self, session: ExplorationSession) -> ExplorationSession: ...

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> ExplorationSession | None: ...

    @abstractmethod
    async def list_saved(self) -> list[ExplorationSession]: ...

    @abstractmethod
    async def list_by_deal_id(self, deal_id: UUID) -> list[ExplorationSession]: ...

    @abstractmethod
    async def update(self, session: ExplorationSession) -> ExplorationSession: ...

    @abstractmethod
    async def delete(self, session_id: UUID) -> None: ...


class ChatSessionRepository(ABC):
    @abstractmethod
    async def create(self, session: ChatSession) -> ChatSession: ...

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> ChatSession | None: ...

    @abstractmethod
    async def get_by_exploration_id(self, exploration_id: UUID) -> list[ChatSession]: ...

    @abstractmethod
    async def update(self, session: ChatSession) -> ChatSession: ...

    @abstractmethod
    async def delete(self, session_id: UUID) -> None: ...


class ChatMessageRepository(ABC):
    @abstractmethod
    async def create(self, message: ChatMessage) -> ChatMessage: ...

    @abstractmethod
    async def get_by_session_id(self, session_id: UUID) -> list[ChatMessage]: ...

    @abstractmethod
    async def bulk_create(self, messages: list[ChatMessage]) -> list[ChatMessage]: ...


class SnapshotRepository(ABC):
    @abstractmethod
    async def create(self, snapshot: Snapshot) -> Snapshot: ...

    @abstractmethod
    async def get_by_id(self, snapshot_id: UUID) -> Snapshot | None: ...

    @abstractmethod
    async def list_all(self) -> list[Snapshot]: ...

    @abstractmethod
    async def list_by_deal_id(self, deal_id: UUID) -> list[Snapshot]: ...

    @abstractmethod
    async def delete(self, snapshot_id: UUID) -> None: ...
```

**Step 2: Verify**

Run: `cd backend && python -c "from app.domain.interfaces.repositories import ExplorationSessionRepository, ChatSessionRepository, ChatMessageRepository, SnapshotRepository; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/domain/interfaces/repositories.py
git commit -m "feat: add repository interfaces for exploration, chat, and snapshot"
```

---

## Task 6: Add Repository Implementations

**Files:**
- Create: `backend/app/infrastructure/persistence/exploration_repo.py`
- Create: `backend/app/infrastructure/persistence/chat_repo.py`
- Create: `backend/app/infrastructure/persistence/snapshot_repo.py`

**Step 1: Write ExplorationSessionRepository implementation**

Create `backend/app/infrastructure/persistence/exploration_repo.py`:

```python
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.exploration import ExplorationSession
from app.domain.interfaces.repositories import ExplorationSessionRepository
from app.infrastructure.persistence.mappers import (
    exploration_session_to_entity,
    exploration_session_to_model,
)
from app.infrastructure.persistence.models import ExplorationSessionModel


class SqlAlchemyExplorationSessionRepository(ExplorationSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: ExplorationSession) -> ExplorationSession:
        model = exploration_session_to_model(entity)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return exploration_session_to_entity(model)

    async def get_by_id(self, session_id: UUID) -> ExplorationSession | None:
        stmt = select(ExplorationSessionModel).where(
            ExplorationSessionModel.id == str(session_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return exploration_session_to_entity(model) if model else None

    async def list_saved(self) -> list[ExplorationSession]:
        stmt = (
            select(ExplorationSessionModel)
            .where(ExplorationSessionModel.saved == True)
            .order_by(ExplorationSessionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [exploration_session_to_entity(m) for m in result.scalars().all()]

    async def list_by_deal_id(self, deal_id: UUID) -> list[ExplorationSession]:
        stmt = (
            select(ExplorationSessionModel)
            .where(ExplorationSessionModel.deal_id == str(deal_id))
            .order_by(ExplorationSessionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [exploration_session_to_entity(m) for m in result.scalars().all()]

    async def update(self, entity: ExplorationSession) -> ExplorationSession:
        stmt = select(ExplorationSessionModel).where(
            ExplorationSessionModel.id == str(entity.id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.name = entity.name
        model.saved = entity.saved
        model.deal_id = str(entity.deal_id) if entity.deal_id else None
        await self._session.commit()
        await self._session.refresh(model)
        return exploration_session_to_entity(model)

    async def delete(self, session_id: UUID) -> None:
        stmt = select(ExplorationSessionModel).where(
            ExplorationSessionModel.id == str(session_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()
```

**Step 2: Write ChatSession and ChatMessage repository implementations**

Create `backend/app/infrastructure/persistence/chat_repo.py`:

```python
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.chat import ChatMessage, ChatSession
from app.domain.interfaces.repositories import ChatMessageRepository, ChatSessionRepository
from app.infrastructure.persistence.mappers import (
    chat_message_to_entity,
    chat_message_to_model,
    chat_session_to_entity,
    chat_session_to_model,
)
from app.infrastructure.persistence.models import ChatMessageModel, ChatSessionModel


class SqlAlchemyChatSessionRepository(ChatSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: ChatSession) -> ChatSession:
        model = chat_session_to_model(entity)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return chat_session_to_entity(model)

    async def get_by_id(self, session_id: UUID) -> ChatSession | None:
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == str(session_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return chat_session_to_entity(model) if model else None

    async def get_by_exploration_id(self, exploration_id: UUID) -> list[ChatSession]:
        stmt = (
            select(ChatSessionModel)
            .where(ChatSessionModel.exploration_session_id == str(exploration_id))
            .order_by(ChatSessionModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [chat_session_to_entity(m) for m in result.scalars().all()]

    async def update(self, entity: ChatSession) -> ChatSession:
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == str(entity.id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.title = entity.title
        model.connectors = [c.value for c in entity.connectors]
        model.updated_at = entity.updated_at
        await self._session.commit()
        await self._session.refresh(model)
        return chat_session_to_entity(model)

    async def delete(self, session_id: UUID) -> None:
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == str(session_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()


class SqlAlchemyChatMessageRepository(ChatMessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: ChatMessage) -> ChatMessage:
        model = chat_message_to_model(entity)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return chat_message_to_entity(model)

    async def get_by_session_id(self, session_id: UUID) -> list[ChatMessage]:
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == str(session_id))
            .order_by(ChatMessageModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [chat_message_to_entity(m) for m in result.scalars().all()]

    async def bulk_create(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        models = [chat_message_to_model(m) for m in messages]
        self._session.add_all(models)
        await self._session.commit()
        for model in models:
            await self._session.refresh(model)
        return [chat_message_to_entity(m) for m in models]
```

**Step 3: Write Snapshot repository implementation**

Create `backend/app/infrastructure/persistence/snapshot_repo.py`:

```python
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.snapshot import Snapshot
from app.domain.interfaces.repositories import SnapshotRepository
from app.infrastructure.persistence.mappers import (
    snapshot_to_entity,
    snapshot_to_model,
)
from app.infrastructure.persistence.models import SnapshotModel


class SqlAlchemySnapshotRepository(SnapshotRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: Snapshot) -> Snapshot:
        model = snapshot_to_model(entity)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return snapshot_to_entity(model)

    async def get_by_id(self, snapshot_id: UUID) -> Snapshot | None:
        stmt = select(SnapshotModel).where(SnapshotModel.id == str(snapshot_id))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return snapshot_to_entity(model) if model else None

    async def list_all(self) -> list[Snapshot]:
        stmt = select(SnapshotModel).order_by(SnapshotModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [snapshot_to_entity(m) for m in result.scalars().all()]

    async def list_by_deal_id(self, deal_id: UUID) -> list[Snapshot]:
        stmt = (
            select(SnapshotModel)
            .where(SnapshotModel.deal_id == str(deal_id))
            .order_by(SnapshotModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [snapshot_to_entity(m) for m in result.scalars().all()]

    async def delete(self, snapshot_id: UUID) -> None:
        stmt = select(SnapshotModel).where(SnapshotModel.id == str(snapshot_id))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()
```

**Step 4: Verify all repos import**

Run: `cd backend && python -c "from app.infrastructure.persistence.exploration_repo import SqlAlchemyExplorationSessionRepository; from app.infrastructure.persistence.chat_repo import SqlAlchemyChatSessionRepository, SqlAlchemyChatMessageRepository; from app.infrastructure.persistence.snapshot_repo import SqlAlchemySnapshotRepository; print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add backend/app/infrastructure/persistence/exploration_repo.py backend/app/infrastructure/persistence/chat_repo.py backend/app/infrastructure/persistence/snapshot_repo.py
git commit -m "feat: add repository implementations for exploration, chat, and snapshot"
```

---

## Task 7: Add MarketSearchProvider

**Files:**
- Modify: `backend/app/domain/interfaces/providers.py` (after line 90)
- Create: `backend/app/domain/value_objects/types.py` — add `SearchResult` type (append)
- Create: `backend/app/infrastructure/search/market_search_provider.py`

**Step 1: Add SearchResult value object**

Append to `backend/app/domain/value_objects/types.py`:

```python
@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str  # connector name that produced this result
    raw_data: dict | None = None  # additional structured data if available
```

**Step 2: Add MarketSearchProvider interface**

Add import at top of `backend/app/domain/interfaces/providers.py`:

```python
from app.domain.value_objects.types import SearchResult
from app.domain.value_objects.enums import ConnectorType
```

Add after `CompsProvider` (after line 90):

```python
class MarketSearchProvider(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        connectors: list[ConnectorType],
        deal: Deal | None = None,
    ) -> list[SearchResult]: ...
```

**Step 3: Create TavilyMarketSearchProvider implementation**

Create `backend/app/infrastructure/search/` directory and `__init__.py`:

Create `backend/app/infrastructure/search/market_search_provider.py`:

```python
from __future__ import annotations

import logging

from app.domain.entities.deal import Deal
from app.domain.interfaces.providers import MarketSearchProvider
from app.domain.value_objects.enums import ConnectorType
from app.domain.value_objects.types import SearchResult

logger = logging.getLogger(__name__)


class TavilyMarketSearchProvider(MarketSearchProvider):
    def __init__(self, tavily_api_key: str) -> None:
        self._tavily_api_key = tavily_api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            from tavily import AsyncTavilyClient
            self._client = AsyncTavilyClient(api_key=self._tavily_api_key)
        return self._client

    async def search(
        self,
        query: str,
        connectors: list[ConnectorType],
        deal: Deal | None = None,
    ) -> list[SearchResult]:
        results: list[SearchResult] = []

        if ConnectorType.TAVILY in connectors:
            try:
                client = self._get_client()
                response = await client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=10,
                )
                for r in response.get("results", []):
                    results.append(
                        SearchResult(
                            title=r.get("title", ""),
                            url=r.get("url", ""),
                            snippet=r.get("content", ""),
                            source=ConnectorType.TAVILY.value,
                            raw_data=r,
                        )
                    )
            except Exception:
                logger.exception("Tavily search failed for query: %s", query)

        # Mock connectors — return empty for now
        for connector in connectors:
            if connector != ConnectorType.TAVILY:
                logger.info("Mock connector %s: no results (not implemented)", connector.value)

        return results
```

**Step 4: Create `__init__.py`**

Create empty `backend/app/infrastructure/search/__init__.py`.

**Step 5: Verify**

Run: `cd backend && python -c "from app.infrastructure.search.market_search_provider import TavilyMarketSearchProvider; print('OK')"`
Expected: `OK`

**Step 6: Commit**

```bash
git add backend/app/domain/interfaces/providers.py backend/app/domain/value_objects/types.py backend/app/infrastructure/search/
git commit -m "feat: add MarketSearchProvider interface and Tavily implementation"
```

---

## Task 8: Add ChatService (Agentic Loop)

**Files:**
- Create: `backend/app/services/chat_service.py`

**Step 1: Write the ChatService**

Create `backend/app/services/chat_service.py`:

```python
from __future__ import annotations

import json
import logging
from datetime import datetime
from uuid import UUID

from openai import AsyncOpenAI

from app.domain.entities.chat import ChatMessage, ChatSession
from app.domain.entities.deal import Deal
from app.domain.entities.exploration import ExplorationSession
from app.domain.interfaces.providers import MarketSearchProvider
from app.domain.interfaces.repositories import (
    ChatMessageRepository,
    ChatSessionRepository,
    DealRepository,
    ExplorationSessionRepository,
    ExtractedFieldRepository,
    AssumptionRepository,
    AssumptionSetRepository,
    FieldValidationRepository,
    CompRepository,
    HistoricalFinancialRepository,
)
from app.domain.value_objects.enums import ChatRole, ConnectorType

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 10

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for real estate market data, property listings, comps, supply pipeline, and market trends.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                },
                "required": ["query"],
            },
        },
    },
]

SYSTEM_PROMPT_DEAL = """You are a real estate market intelligence assistant analyzing a specific deal.

Deal Context:
{deal_context}

All research should be contextualized against this subject property. When returning property results, always note how they compare to the subject deal. Use the web_search tool to find market data, comparable properties, and validate assumptions.

When presenting properties you find, always include: address, property type, key financial metrics (cap rate, rent/sqft, sale price, NOI) where available, and how they compare to the subject deal.

Respond in markdown format."""

SYSTEM_PROMPT_FREE = """You are a real estate market intelligence assistant.

The user is exploring the market without a specific deal. Help them research properties, find comps, understand market trends, and discover opportunities. Use the web_search tool to find relevant data.

When presenting properties you find, always include: address, property type, key financial metrics (cap rate, rent/sqft, sale price, NOI) where available.

Respond in markdown format."""


class ChatService:
    def __init__(
        self,
        exploration_repo: ExplorationSessionRepository,
        chat_session_repo: ChatSessionRepository,
        chat_message_repo: ChatMessageRepository,
        deal_repo: DealRepository,
        extracted_field_repo: ExtractedFieldRepository,
        assumption_set_repo: AssumptionSetRepository,
        assumption_repo: AssumptionRepository,
        validation_repo: FieldValidationRepository,
        comp_repo: CompRepository,
        historical_financial_repo: HistoricalFinancialRepository,
        market_search_provider: MarketSearchProvider,
        openai_api_key: str,
        openai_model: str,
    ) -> None:
        self._exploration_repo = exploration_repo
        self._chat_session_repo = chat_session_repo
        self._chat_message_repo = chat_message_repo
        self._deal_repo = deal_repo
        self._extracted_field_repo = extracted_field_repo
        self._assumption_set_repo = assumption_set_repo
        self._assumption_repo = assumption_repo
        self._validation_repo = validation_repo
        self._comp_repo = comp_repo
        self._hf_repo = historical_financial_repo
        self._search_provider = market_search_provider
        self._openai = AsyncOpenAI(api_key=openai_api_key)
        self._model = openai_model

    async def _build_deal_context(self, deal: Deal) -> str:
        lines = [
            f"Name: {deal.name}",
            f"Property Type: {deal.property_type.value}",
            f"Location: {deal.address}, {deal.city}, {deal.state}",
        ]
        if deal.square_feet:
            lines.append(f"Square Feet: {deal.square_feet:,.0f}")

        fields = await self._extracted_field_repo.get_by_deal_id(deal.id)
        if fields:
            lines.append("\nExtracted Fields:")
            for f in fields[:15]:
                val = f.value_number if f.value_number is not None else f.value_text
                lines.append(f"  {f.field_key}: {val} {f.unit or ''}")

        sets = await self._assumption_set_repo.get_by_deal_id(deal.id)
        if sets:
            assumptions = await self._assumption_repo.get_by_set_id(sets[0].id)
            if assumptions:
                lines.append("\nKey Assumptions:")
                for a in assumptions[:10]:
                    lines.append(f"  {a.key}: {a.value_number} {a.unit or ''}")

        return "\n".join(lines)

    async def send_message(
        self,
        session_id: UUID,
        user_content: str,
        connectors: list[ConnectorType],
    ) -> list[ChatMessage]:
        chat_session = await self._chat_session_repo.get_by_id(session_id)
        if chat_session is None:
            raise ValueError(f"ChatSession {session_id} not found")

        exploration = await self._exploration_repo.get_by_id(
            chat_session.exploration_session_id
        )
        if exploration is None:
            raise ValueError("ExplorationSession not found")

        # Persist user message
        user_msg = ChatMessage(
            session_id=session_id,
            role=ChatRole.USER,
            content=user_content,
        )
        user_msg = await self._chat_message_repo.create(user_msg)

        # Build system prompt
        deal: Deal | None = None
        if exploration.deal_id:
            deal = await self._deal_repo.get_by_id(exploration.deal_id)

        if deal:
            deal_context = await self._build_deal_context(deal)
            system_prompt = SYSTEM_PROMPT_DEAL.format(deal_context=deal_context)
        else:
            system_prompt = SYSTEM_PROMPT_FREE

        # Load conversation history
        history = await self._chat_message_repo.get_by_session_id(session_id)
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            if msg.role == ChatRole.TOOL:
                messages.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": (msg.tool_calls or [{}])[0].get("id", ""),
                })
            elif msg.role == ChatRole.ASSISTANT and msg.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": msg.content or None,
                    "tool_calls": msg.tool_calls,
                })
            else:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

        # Agentic loop
        new_messages: list[ChatMessage] = [user_msg]
        for _ in range(MAX_TOOL_ROUNDS):
            response = await self._openai.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
            )
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                # Persist assistant message with tool calls
                tool_calls_data = [
                    {
                        "id": tc.id,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ]
                assistant_msg = ChatMessage(
                    session_id=session_id,
                    role=ChatRole.ASSISTANT,
                    content=choice.message.content or "",
                    tool_calls=tool_calls_data,
                )
                assistant_msg = await self._chat_message_repo.create(assistant_msg)
                new_messages.append(assistant_msg)
                messages.append({
                    "role": "assistant",
                    "content": choice.message.content or None,
                    "tool_calls": tool_calls_data,
                })

                # Execute each tool call
                for tc in choice.message.tool_calls:
                    args = json.loads(tc.function.arguments)
                    if tc.function.name == "web_search":
                        results = await self._search_provider.search(
                            query=args["query"],
                            connectors=connectors,
                            deal=deal,
                        )
                        tool_result = json.dumps(
                            [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results],
                            indent=2,
                        )
                    else:
                        tool_result = json.dumps({"error": f"Unknown tool: {tc.function.name}"})

                    tool_msg = ChatMessage(
                        session_id=session_id,
                        role=ChatRole.TOOL,
                        content=tool_result,
                        tool_calls=[{"id": tc.id}],
                    )
                    tool_msg = await self._chat_message_repo.create(tool_msg)
                    new_messages.append(tool_msg)
                    messages.append({
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tc.id,
                    })
            else:
                # Final response
                final_msg = ChatMessage(
                    session_id=session_id,
                    role=ChatRole.ASSISTANT,
                    content=choice.message.content or "",
                )
                final_msg = await self._chat_message_repo.create(final_msg)
                new_messages.append(final_msg)
                break

        return new_messages
```

**Step 2: Verify import**

Run: `cd backend && python -c "from app.services.chat_service import ChatService; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/services/chat_service.py
git commit -m "feat: add ChatService with agentic GPT-4o loop and web search tool"
```

---

## Task 9: Add Pydantic Schemas

**Files:**
- Modify: `backend/app/api/schemas.py` (after line 331)

**Step 1: Add schemas for exploration, chat, and snapshot**

Add after the last existing schema:

```python
# --- Exploration ---

class CreateExplorationRequest(BaseModel):
    name: str = "Untitled Exploration"


class ExplorationSessionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    deal_id: UUID | None
    name: str
    saved: bool
    created_at: datetime


class UpdateExplorationRequest(BaseModel):
    name: str | None = None
    saved: bool | None = None


# --- Chat Sessions ---

class CreateChatSessionRequest(BaseModel):
    title: str = "New Search"
    connectors: list[str] = []


class ChatSessionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    exploration_session_id: UUID
    title: str
    connectors: list[str]
    created_at: datetime
    updated_at: datetime


class UpdateChatSessionRequest(BaseModel):
    title: str | None = None


# --- Chat Messages ---

class SendMessageRequest(BaseModel):
    content: str
    connectors: list[str] = []


class ChatMessageResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    session_id: UUID
    role: str
    content: str
    tool_calls: list[dict] | None = None
    created_at: datetime


# --- Snapshots ---

class CreateSnapshotRequest(BaseModel):
    name: str


class SnapshotResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    deal_id: UUID | None
    name: str
    session_data: dict
    created_at: datetime
```

Add `UUID` and `datetime` to imports at top if not already there (they should be from existing schemas).

**Step 2: Verify**

Run: `cd backend && python -c "from app.api.schemas import ExplorationSessionResponse, ChatSessionResponse, ChatMessageResponse, SnapshotResponse; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/api/schemas.py
git commit -m "feat: add Pydantic schemas for exploration, chat, and snapshot"
```

---

## Task 10: Add DI Wiring

**Files:**
- Modify: `backend/app/api/dependencies.py` (after line 268)

**Step 1: Add new singleton providers and factory functions**

Add new imports at top:

```python
from app.infrastructure.persistence.exploration_repo import SqlAlchemyExplorationSessionRepository
from app.infrastructure.persistence.chat_repo import SqlAlchemyChatSessionRepository, SqlAlchemyChatMessageRepository
from app.infrastructure.persistence.snapshot_repo import SqlAlchemySnapshotRepository
from app.infrastructure.search.market_search_provider import TavilyMarketSearchProvider
from app.services.chat_service import ChatService
```

Add new singleton after existing singletons (after line 42):

```python
_market_search_provider = TavilyMarketSearchProvider(
    tavily_api_key=settings.tavily_api_key,
)
```

Add new repository factories after existing ones (after line 121):

```python
def get_exploration_session_repo(session: DbSession) -> SqlAlchemyExplorationSessionRepository:
    return SqlAlchemyExplorationSessionRepository(session)


def get_chat_session_repo(session: DbSession) -> SqlAlchemyChatSessionRepository:
    return SqlAlchemyChatSessionRepository(session)


def get_chat_message_repo(session: DbSession) -> SqlAlchemyChatMessageRepository:
    return SqlAlchemyChatMessageRepository(session)


def get_snapshot_repo(session: DbSession) -> SqlAlchemySnapshotRepository:
    return SqlAlchemySnapshotRepository(session)
```

Add new service factory after existing ones (after line 268):

```python
def get_chat_service(
    exploration_repo: Annotated[SqlAlchemyExplorationSessionRepository, Depends(get_exploration_session_repo)],
    chat_session_repo: Annotated[SqlAlchemyChatSessionRepository, Depends(get_chat_session_repo)],
    chat_message_repo: Annotated[SqlAlchemyChatMessageRepository, Depends(get_chat_message_repo)],
    deal_repo: Annotated[SqlAlchemyDealRepository, Depends(get_deal_repo)],
    extracted_field_repo: Annotated[SqlAlchemyExtractedFieldRepository, Depends(get_extracted_field_repo)],
    assumption_set_repo: Annotated[SqlAlchemyAssumptionSetRepository, Depends(get_assumption_set_repo)],
    assumption_repo: Annotated[SqlAlchemyAssumptionRepository, Depends(get_assumption_repo)],
    validation_repo: Annotated[SqlAlchemyFieldValidationRepository, Depends(get_field_validation_repo)],
    comp_repo: Annotated[SqlAlchemyCompRepository, Depends(get_comp_repo)],
    hf_repo: Annotated[SqlAlchemyHistoricalFinancialRepository, Depends(get_historical_financial_repo)],
) -> ChatService:
    return ChatService(
        exploration_repo=exploration_repo,
        chat_session_repo=chat_session_repo,
        chat_message_repo=chat_message_repo,
        deal_repo=deal_repo,
        extracted_field_repo=extracted_field_repo,
        assumption_set_repo=assumption_set_repo,
        assumption_repo=assumption_repo,
        validation_repo=validation_repo,
        comp_repo=comp_repo,
        historical_financial_repo=hf_repo,
        market_search_provider=_market_search_provider,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
    )
```

**Step 2: Verify**

Run: `cd backend && python -c "from app.api.dependencies import get_chat_service; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/api/dependencies.py
git commit -m "feat: add DI wiring for exploration, chat, and snapshot"
```

---

## Task 11: Add API Routes

**Files:**
- Create: `backend/app/api/v1/explorations.py`
- Create: `backend/app/api/v1/chat.py`
- Create: `backend/app/api/v1/snapshots.py`
- Modify: `backend/app/main.py` (register new routers)

**Step 1: Create exploration routes**

Create `backend/app/api/v1/explorations.py`:

```python
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_exploration_session_repo
from app.api.schemas import (
    CreateExplorationRequest,
    ExplorationSessionResponse,
    UpdateExplorationRequest,
)
from app.domain.entities.exploration import ExplorationSession
from app.infrastructure.persistence.exploration_repo import SqlAlchemyExplorationSessionRepository

router = APIRouter(tags=["explorations"])


@router.post("/deals/{deal_id}/explorations", response_model=ExplorationSessionResponse)
async def create_deal_exploration(
    deal_id: UUID,
    body: CreateExplorationRequest,
    repo: Annotated[SqlAlchemyExplorationSessionRepository, Depends(get_exploration_session_repo)],
) -> ExplorationSessionResponse:
    entity = ExplorationSession(name=body.name, deal_id=deal_id)
    created = await repo.create(entity)
    return ExplorationSessionResponse.model_validate(created)


@router.post("/explorations", response_model=ExplorationSessionResponse)
async def create_free_exploration(
    body: CreateExplorationRequest,
    repo: Annotated[SqlAlchemyExplorationSessionRepository, Depends(get_exploration_session_repo)],
) -> ExplorationSessionResponse:
    entity = ExplorationSession(name=body.name)
    created = await repo.create(entity)
    return ExplorationSessionResponse.model_validate(created)


@router.get("/explorations", response_model=list[ExplorationSessionResponse])
async def list_explorations(
    repo: Annotated[SqlAlchemyExplorationSessionRepository, Depends(get_exploration_session_repo)],
) -> list[ExplorationSessionResponse]:
    items = await repo.list_saved()
    return [ExplorationSessionResponse.model_validate(e) for e in items]


@router.get("/explorations/{exploration_id}", response_model=ExplorationSessionResponse)
async def get_exploration(
    exploration_id: UUID,
    repo: Annotated[SqlAlchemyExplorationSessionRepository, Depends(get_exploration_session_repo)],
) -> ExplorationSessionResponse:
    entity = await repo.get_by_id(exploration_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Exploration not found")
    return ExplorationSessionResponse.model_validate(entity)


@router.patch("/explorations/{exploration_id}", response_model=ExplorationSessionResponse)
async def update_exploration(
    exploration_id: UUID,
    body: UpdateExplorationRequest,
    repo: Annotated[SqlAlchemyExplorationSessionRepository, Depends(get_exploration_session_repo)],
) -> ExplorationSessionResponse:
    entity = await repo.get_by_id(exploration_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Exploration not found")
    if body.name is not None:
        entity.name = body.name
    if body.saved is not None:
        entity.saved = body.saved
    updated = await repo.update(entity)
    return ExplorationSessionResponse.model_validate(updated)


@router.delete("/explorations/{exploration_id}", status_code=204)
async def delete_exploration(
    exploration_id: UUID,
    repo: Annotated[SqlAlchemyExplorationSessionRepository, Depends(get_exploration_session_repo)],
) -> None:
    await repo.delete(exploration_id)
```

**Step 2: Create chat routes**

Create `backend/app/api/v1/chat.py`:

```python
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_chat_message_repo, get_chat_session_repo, get_chat_service
from app.api.schemas import (
    ChatMessageResponse,
    ChatSessionResponse,
    CreateChatSessionRequest,
    SendMessageRequest,
    UpdateChatSessionRequest,
)
from app.domain.entities.chat import ChatSession
from app.domain.value_objects.enums import ConnectorType
from app.infrastructure.persistence.chat_repo import (
    SqlAlchemyChatMessageRepository,
    SqlAlchemyChatSessionRepository,
)
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


@router.post(
    "/explorations/{exploration_id}/sessions",
    response_model=ChatSessionResponse,
)
async def create_chat_session(
    exploration_id: UUID,
    body: CreateChatSessionRequest,
    repo: Annotated[SqlAlchemyChatSessionRepository, Depends(get_chat_session_repo)],
) -> ChatSessionResponse:
    connectors = [ConnectorType(c) for c in body.connectors]
    entity = ChatSession(
        exploration_session_id=exploration_id,
        title=body.title,
        connectors=connectors,
    )
    created = await repo.create(entity)
    return ChatSessionResponse.model_validate({
        **vars(created),
        "connectors": [c.value for c in created.connectors],
    })


@router.get(
    "/explorations/{exploration_id}/sessions",
    response_model=list[ChatSessionResponse],
)
async def list_chat_sessions(
    exploration_id: UUID,
    repo: Annotated[SqlAlchemyChatSessionRepository, Depends(get_chat_session_repo)],
) -> list[ChatSessionResponse]:
    items = await repo.get_by_exploration_id(exploration_id)
    return [
        ChatSessionResponse.model_validate({
            **vars(s),
            "connectors": [c.value for c in s.connectors],
        })
        for s in items
    ]


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: UUID,
    repo: Annotated[SqlAlchemyChatSessionRepository, Depends(get_chat_session_repo)],
) -> ChatSessionResponse:
    entity = await repo.get_by_id(session_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return ChatSessionResponse.model_validate({
        **vars(entity),
        "connectors": [c.value for c in entity.connectors],
    })


@router.patch("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: UUID,
    body: UpdateChatSessionRequest,
    repo: Annotated[SqlAlchemyChatSessionRepository, Depends(get_chat_session_repo)],
) -> ChatSessionResponse:
    entity = await repo.get_by_id(session_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if body.title is not None:
        entity.title = body.title
    updated = await repo.update(entity)
    return ChatSessionResponse.model_validate({
        **vars(updated),
        "connectors": [c.value for c in updated.connectors],
    })


@router.delete("/chat/sessions/{session_id}", status_code=204)
async def delete_chat_session(
    session_id: UUID,
    repo: Annotated[SqlAlchemyChatSessionRepository, Depends(get_chat_session_repo)],
) -> None:
    await repo.delete(session_id)


@router.get(
    "/chat/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
async def list_messages(
    session_id: UUID,
    repo: Annotated[SqlAlchemyChatMessageRepository, Depends(get_chat_message_repo)],
) -> list[ChatMessageResponse]:
    messages = await repo.get_by_session_id(session_id)
    return [
        ChatMessageResponse.model_validate({
            **vars(m),
            "role": m.role.value,
        })
        for m in messages
    ]


@router.post(
    "/chat/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
async def send_message(
    session_id: UUID,
    body: SendMessageRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> list[ChatMessageResponse]:
    connectors = [ConnectorType(c) for c in body.connectors]
    new_messages = await service.send_message(
        session_id=session_id,
        user_content=body.content,
        connectors=connectors,
    )
    return [
        ChatMessageResponse.model_validate({
            **vars(m),
            "role": m.role.value,
        })
        for m in new_messages
    ]
```

**Step 3: Create snapshot routes**

Create `backend/app/api/v1/snapshots.py`:

```python
from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_chat_message_repo,
    get_chat_session_repo,
    get_exploration_session_repo,
    get_snapshot_repo,
)
from app.api.schemas import CreateSnapshotRequest, SnapshotResponse
from app.domain.entities.chat import ChatMessage, ChatSession
from app.domain.entities.exploration import ExplorationSession
from app.domain.entities.snapshot import Snapshot
from app.domain.value_objects.enums import ChatRole, ConnectorType
from app.infrastructure.persistence.chat_repo import (
    SqlAlchemyChatMessageRepository,
    SqlAlchemyChatSessionRepository,
)
from app.infrastructure.persistence.exploration_repo import SqlAlchemyExplorationSessionRepository
from app.infrastructure.persistence.snapshot_repo import SqlAlchemySnapshotRepository

router = APIRouter(tags=["snapshots"])


@router.post(
    "/explorations/{exploration_id}/snapshots",
    response_model=SnapshotResponse,
)
async def create_snapshot(
    exploration_id: UUID,
    body: CreateSnapshotRequest,
    exploration_repo: Annotated[SqlAlchemyExplorationSessionRepository, Depends(get_exploration_session_repo)],
    chat_session_repo: Annotated[SqlAlchemyChatSessionRepository, Depends(get_chat_session_repo)],
    chat_message_repo: Annotated[SqlAlchemyChatMessageRepository, Depends(get_chat_message_repo)],
    snapshot_repo: Annotated[SqlAlchemySnapshotRepository, Depends(get_snapshot_repo)],
) -> SnapshotResponse:
    exploration = await exploration_repo.get_by_id(exploration_id)
    if exploration is None:
        raise HTTPException(status_code=404, detail="Exploration not found")

    sessions = await chat_session_repo.get_by_exploration_id(exploration_id)
    session_data = {
        "exploration": {
            "name": exploration.name,
            "deal_id": str(exploration.deal_id) if exploration.deal_id else None,
        },
        "sessions": [],
    }
    for s in sessions:
        messages = await chat_message_repo.get_by_session_id(s.id)
        session_data["sessions"].append({
            "title": s.title,
            "connectors": [c.value for c in s.connectors],
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "tool_calls": m.tool_calls,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
        })

    snapshot = Snapshot(
        name=body.name,
        deal_id=exploration.deal_id,
        session_data=session_data,
    )
    created = await snapshot_repo.create(snapshot)
    return SnapshotResponse.model_validate(created)


@router.get("/snapshots", response_model=list[SnapshotResponse])
async def list_snapshots(
    repo: Annotated[SqlAlchemySnapshotRepository, Depends(get_snapshot_repo)],
) -> list[SnapshotResponse]:
    return [SnapshotResponse.model_validate(s) for s in await repo.list_all()]


@router.get("/deals/{deal_id}/snapshots", response_model=list[SnapshotResponse])
async def list_deal_snapshots(
    deal_id: UUID,
    repo: Annotated[SqlAlchemySnapshotRepository, Depends(get_snapshot_repo)],
) -> list[SnapshotResponse]:
    return [SnapshotResponse.model_validate(s) for s in await repo.list_by_deal_id(deal_id)]


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: UUID,
    repo: Annotated[SqlAlchemySnapshotRepository, Depends(get_snapshot_repo)],
) -> SnapshotResponse:
    snapshot = await repo.get_by_id(snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return SnapshotResponse.model_validate(snapshot)


@router.post("/snapshots/{snapshot_id}/restore", response_model=ExplorationSessionResponse)
async def restore_snapshot(
    snapshot_id: UUID,
    snapshot_repo: Annotated[SqlAlchemySnapshotRepository, Depends(get_snapshot_repo)],
    exploration_repo: Annotated[SqlAlchemyExplorationSessionRepository, Depends(get_exploration_session_repo)],
    chat_session_repo: Annotated[SqlAlchemyChatSessionRepository, Depends(get_chat_session_repo)],
    chat_message_repo: Annotated[SqlAlchemyChatMessageRepository, Depends(get_chat_message_repo)],
) -> dict:
    from app.api.schemas import ExplorationSessionResponse

    snapshot = await snapshot_repo.get_by_id(snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    data = snapshot.session_data
    exploration_data = data.get("exploration", {})
    deal_id = exploration_data.get("deal_id")

    exploration = ExplorationSession(
        name=f"{snapshot.name} (restored)",
        deal_id=UUID(deal_id) if deal_id else None,
    )
    exploration = await exploration_repo.create(exploration)

    for s_data in data.get("sessions", []):
        cs = ChatSession(
            exploration_session_id=exploration.id,
            title=s_data["title"],
            connectors=[ConnectorType(c) for c in s_data.get("connectors", [])],
        )
        cs = await chat_session_repo.create(cs)

        messages = [
            ChatMessage(
                session_id=cs.id,
                role=ChatRole(m["role"]),
                content=m["content"],
                tool_calls=m.get("tool_calls"),
            )
            for m in s_data.get("messages", [])
        ]
        if messages:
            await chat_message_repo.bulk_create(messages)

    return ExplorationSessionResponse.model_validate(exploration)


@router.delete("/snapshots/{snapshot_id}", status_code=204)
async def delete_snapshot(
    snapshot_id: UUID,
    repo: Annotated[SqlAlchemySnapshotRepository, Depends(get_snapshot_repo)],
) -> None:
    await repo.delete(snapshot_id)
```

**Step 4: Register routers in main.py**

Add imports and registrations in `backend/app/main.py`:

Add imports after existing router imports:

```python
from app.api.v1.explorations import router as explorations_router
from app.api.v1.chat import router as chat_router
from app.api.v1.snapshots import router as snapshots_router
```

Add registrations after existing ones (after line 54):

```python
app.include_router(explorations_router, prefix="/v1")
app.include_router(chat_router, prefix="/v1")
app.include_router(snapshots_router, prefix="/v1")
```

**Step 5: Verify server starts**

Run: `cd backend && source ~/anaconda3/etc/profile.d/conda.sh && conda activate dealdesk && python -c "from app.main import app; print('Routes:', len(app.routes))"`
Expected: Prints route count without errors.

**Step 6: Commit**

```bash
git add backend/app/api/v1/explorations.py backend/app/api/v1/chat.py backend/app/api/v1/snapshots.py backend/app/main.py
git commit -m "feat: add API routes for explorations, chat, and snapshots"
```

---

## Task 12: Add Alembic Migration

**Files:**
- Create: new migration file via alembic

**Step 1: Generate migration**

Run: `cd backend && source ~/anaconda3/etc/profile.d/conda.sh && conda activate dealdesk && python -m alembic revision --autogenerate -m "add exploration chat and snapshot tables"`

**Step 2: Review and run migration**

Run: `cd backend && python -m alembic upgrade head`
Expected: Migration applies without errors, creates `exploration_sessions`, `chat_sessions`, `chat_messages`, `snapshots` tables.

**Step 3: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat: add migration for exploration, chat, and snapshot tables"
```

---

## Task 13: Add Frontend TypeScript Interfaces

**Files:**
- Modify: `frontend/src/interfaces/api.ts`

**Step 1: Add new interfaces**

Append to `frontend/src/interfaces/api.ts`:

```typescript
// --- Exploration ---

export interface ExplorationSession {
  id: string;
  deal_id: string | null;
  name: string;
  saved: boolean;
  created_at: string;
}

// --- Chat ---

export interface ChatSession {
  id: string;
  exploration_session_id: string;
  title: string;
  connectors: string[];
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "tool";
  content: string;
  tool_calls: Record<string, unknown>[] | null;
  created_at: string;
}

// --- Snapshot ---

export interface Snapshot {
  id: string;
  deal_id: string | null;
  name: string;
  session_data: Record<string, unknown>;
  created_at: string;
}
```

**Step 2: Commit**

```bash
git add frontend/src/interfaces/api.ts
git commit -m "feat: add TypeScript interfaces for exploration, chat, and snapshot"
```

---

## Task 14: Add Frontend API Services

**Files:**
- Create: `frontend/src/services/exploration.service.ts`
- Create: `frontend/src/services/chat.service.ts`
- Create: `frontend/src/services/snapshot.service.ts`

**Step 1: Create exploration service**

Create `frontend/src/services/exploration.service.ts`:

```typescript
import { apiFetch } from "./api-client";
import type { ExplorationSession } from "@/interfaces/api";

export const explorationService = {
  createForDeal: (dealId: string, name = "Untitled Exploration") =>
    apiFetch<ExplorationSession>(`/deals/${dealId}/explorations`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  createFree: (name = "Untitled Exploration") =>
    apiFetch<ExplorationSession>("/explorations", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  list: () => apiFetch<ExplorationSession[]>("/explorations"),

  get: (id: string) => apiFetch<ExplorationSession>(`/explorations/${id}`),

  update: (id: string, data: { name?: string; saved?: boolean }) =>
    apiFetch<ExplorationSession>(`/explorations/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiFetch<void>(`/explorations/${id}`, { method: "DELETE" }),
};
```

**Step 2: Create chat service**

Create `frontend/src/services/chat.service.ts`:

```typescript
import { apiFetch } from "./api-client";
import type { ChatSession, ChatMessage } from "@/interfaces/api";

export const chatService = {
  createSession: (explorationId: string, title = "New Search", connectors: string[] = []) =>
    apiFetch<ChatSession>(`/explorations/${explorationId}/sessions`, {
      method: "POST",
      body: JSON.stringify({ title, connectors }),
    }),

  listSessions: (explorationId: string) =>
    apiFetch<ChatSession[]>(`/explorations/${explorationId}/sessions`),

  getSession: (sessionId: string) =>
    apiFetch<ChatSession>(`/chat/sessions/${sessionId}`),

  updateSession: (sessionId: string, data: { title?: string }) =>
    apiFetch<ChatSession>(`/chat/sessions/${sessionId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteSession: (sessionId: string) =>
    apiFetch<void>(`/chat/sessions/${sessionId}`, { method: "DELETE" }),

  listMessages: (sessionId: string) =>
    apiFetch<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`),

  sendMessage: (sessionId: string, content: string, connectors: string[] = []) =>
    apiFetch<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, connectors }),
    }),
};
```

**Step 3: Create snapshot service**

Create `frontend/src/services/snapshot.service.ts`:

```typescript
import { apiFetch } from "./api-client";
import type { Snapshot, ExplorationSession } from "@/interfaces/api";

export const snapshotService = {
  create: (explorationId: string, name: string) =>
    apiFetch<Snapshot>(`/explorations/${explorationId}/snapshots`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  list: () => apiFetch<Snapshot[]>("/snapshots"),

  listForDeal: (dealId: string) =>
    apiFetch<Snapshot[]>(`/deals/${dealId}/snapshots`),

  get: (id: string) => apiFetch<Snapshot>(`/snapshots/${id}`),

  restore: (id: string) =>
    apiFetch<ExplorationSession>(`/snapshots/${id}/restore`, { method: "POST" }),

  delete: (id: string) =>
    apiFetch<void>(`/snapshots/${id}`, { method: "DELETE" }),
};
```

**Step 4: Commit**

```bash
git add frontend/src/services/exploration.service.ts frontend/src/services/chat.service.ts frontend/src/services/snapshot.service.ts
git commit -m "feat: add frontend API services for exploration, chat, and snapshot"
```

---

## Task 15: Add Frontend Hooks

**Files:**
- Create: `frontend/src/hooks/use-exploration.ts`
- Create: `frontend/src/hooks/use-chat.ts`

**Step 1: Create exploration hook**

Create `frontend/src/hooks/use-exploration.ts`:

```typescript
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ExplorationSession, ChatSession } from "@/interfaces/api";
import { explorationService } from "@/services/exploration.service";
import { chatService } from "@/services/chat.service";

export function useExploration(explorationId: string | null) {
  const [exploration, setExploration] = useState<ExplorationSession | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const initialLoadDone = useRef(false);

  const refresh = useCallback(async () => {
    if (!explorationId) return;
    try {
      const [exp, sess] = await Promise.all([
        explorationService.get(explorationId),
        chatService.listSessions(explorationId),
      ]);
      setExploration(exp);
      setSessions(sess);
    } catch (err) {
      console.error("Failed to refresh exploration", err);
    } finally {
      if (!initialLoadDone.current) {
        initialLoadDone.current = true;
        setLoading(false);
      }
    }
  }, [explorationId]);

  useEffect(() => {
    if (explorationId) refresh();
  }, [explorationId, refresh]);

  return { exploration, sessions, loading, refresh };
}
```

**Step 2: Create chat hook**

Create `frontend/src/hooks/use-chat.ts`:

```typescript
"use client";

import { useCallback, useEffect, useState } from "react";
import type { ChatMessage } from "@/interfaces/api";
import { chatService } from "@/services/chat.service";

export function useChat(sessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  const loadMessages = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const msgs = await chatService.listMessages(sessionId);
      setMessages(msgs);
    } catch (err) {
      console.error("Failed to load messages", err);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) loadMessages();
  }, [sessionId, loadMessages]);

  const sendMessage = useCallback(
    async (content: string, connectors: string[] = []) => {
      if (!sessionId) return;
      setSending(true);
      try {
        const newMessages = await chatService.sendMessage(sessionId, content, connectors);
        setMessages((prev) => [...prev, ...newMessages]);
      } catch (err) {
        console.error("Failed to send message", err);
      } finally {
        setSending(false);
      }
    },
    [sessionId]
  );

  return { messages, loading, sending, sendMessage, refresh: loadMessages };
}
```

**Step 3: Commit**

```bash
git add frontend/src/hooks/use-exploration.ts frontend/src/hooks/use-chat.ts
git commit -m "feat: add useExploration and useChat hooks"
```

---

## Task 16: Install Recharts

**Files:**
- Modify: `frontend/package.json`

**Step 1: Install recharts**

Run: `cd frontend && npm install recharts`

**Step 2: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: add recharts dependency for comparison charts"
```

---

## Task 17: Build Frontend UI Components

This is the largest task. Create the core UI components for the new layout. Each component is a separate sub-step.

**Files:**
- Create: `frontend/src/components/exploration/search-bar.tsx`
- Create: `frontend/src/components/exploration/session-tabs.tsx`
- Create: `frontend/src/components/exploration/chat-thread.tsx`
- Create: `frontend/src/components/exploration/user-message.tsx`
- Create: `frontend/src/components/exploration/assistant-message.tsx`
- Create: `frontend/src/components/exploration/overview-tab.tsx`
- Create: `frontend/src/components/exploration/property-card.tsx`
- Create: `frontend/src/components/exploration/property-modal.tsx`
- Create: `frontend/src/components/exploration/comparison-toggle.tsx`
- Create: `frontend/src/components/exploration/comparison-chart.tsx`
- Create: `frontend/src/components/layout/deal-sidebar.tsx`

These are all new React components. The implementing agent should:

1. Build `SearchBar` first — connector chips + text input + send button. Connectors are: TAVILY (enabled), COSTAR/COMPSTACK/LOOPNET/REA_VISTA (grayed out "coming soon"). On submit, calls a callback with `{query, connectors}`.

2. Build `SessionTabs` — tab bar with Overview (always first, not closeable) + dynamic tabs (closeable with ×) + [+] button. Calls callbacks for tab select, tab close, new tab.

3. Build `UserMessage` and `AssistantMessage` — simple message bubbles. AssistantMessage renders markdown content. Both receive a `ChatMessage` prop.

4. Build `ChatThread` — scrollable list of messages. Filters out `role=tool` messages. Auto-scrolls to bottom on new messages.

5. Build `PropertyCard` — card with address, property type badge, key metrics (cap rate, rent/sqft, sale price). Clickable — calls `onSelect` callback.

6. Build `PropertyModal` — full detail modal using shadcn Dialog. Shows all property metrics. "vs Subject" column when deal context provided. Keyboard nav: ArrowLeft/ArrowRight or j/k to cycle, Escape to close. Shows "N of M" counter.

7. Build `OverviewTab` — renders two sections: metric comparison dashboard (if deal exists) and property card grid (from all sessions' tool results). Parses tool messages across all sessions to extract property data.

8. Build `ComparisonToggle` and `ComparisonChart` — toggle between table and chart view. Chart uses Recharts BarChart with subject deal as ReferenceLine.

9. Build `DealSidebar` — collapsible sections for Deal Summary, PDF Preview (iframe), Extraction (key fields), Validation (status badges), Assumptions (key metrics), Financials (summary). Each section has a chevron toggle and shows spinner during pipeline processing. Includes Export XLSX button.

**Commit after all components built:**

```bash
git add frontend/src/components/exploration/ frontend/src/components/layout/
git commit -m "feat: add exploration UI components and deal sidebar"
```

---

## Task 18: Rebuild Deal Workspace Page

**Files:**
- Rewrite: `frontend/src/app/deals/[id]/page.tsx`

The implementing agent should rewrite this page to use the new two-pane layout:

1. On mount, create or load an ExplorationSession for this deal (check if one exists via API, create if not)
2. Left pane: `DealSidebar` with pipeline auto-run logic (move existing pipeline from current page into sidebar)
3. Right pane: `SearchBar` + `SessionTabs` + active tab content (`OverviewTab` or `ChatThread`)
4. Wire up: creating new chat sessions (tabs), sending messages, switching tabs
5. Pass deal context to components that need it for "vs Subject" comparisons

**Commit:**

```bash
git add frontend/src/app/deals/[id]/page.tsx
git commit -m "feat: rebuild deal workspace as two-pane exploration layout"
```

---

## Task 19: Build Explore Page

**Files:**
- Create: `frontend/src/app/explore/page.tsx`

Same right-pane UI as deal workspace but full-width, no sidebar. On mount, create a temporary ExplorationSession (no deal_id). Same SearchBar + SessionTabs + ChatThread pattern.

**Commit:**

```bash
git add frontend/src/app/explore/page.tsx
git commit -m "feat: add free market exploration page"
```

---

## Task 20: Update Home Page

**Files:**
- Modify: `frontend/src/app/page.tsx`

Add:
1. "Explore Market" button next to "New Deal" — links to `/explore`
2. "Saved Explorations" section below deals table — fetches from `explorationService.list()`, shows name + deal name (if anchored) + date. Click navigates to `/deals/[id]` or `/explore` depending on `deal_id`.

**Commit:**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat: add Explore Market button and saved explorations to home page"
```

---

## Task 21: End-to-End Smoke Test

**Step 1: Start backend**

Run: `cd backend && source ~/anaconda3/etc/profile.d/conda.sh && conda activate dealdesk && uvicorn app.main:app --reload`

**Step 2: Test exploration API manually**

```bash
# Create free exploration
curl -X POST http://localhost:8000/v1/explorations -H "Content-Type: application/json" -d '{"name": "Test"}'

# Create chat session (use exploration_id from above)
curl -X POST http://localhost:8000/v1/explorations/{id}/sessions -H "Content-Type: application/json" -d '{"title": "Rent Comps", "connectors": ["tavily"]}'

# Send message (use session_id from above) — this will call GPT-4o + Tavily
curl -X POST http://localhost:8000/v1/chat/sessions/{id}/messages -H "Content-Type: application/json" -d '{"content": "Find medical office properties for sale in Providence, RI", "connectors": ["tavily"]}'
```

**Step 3: Start frontend and verify UI**

Run: `cd frontend && npm run dev`

Visit `http://localhost:3000`:
- Verify "Explore Market" button appears
- Click it — verify `/explore` page loads with search bar
- Navigate to an existing deal — verify two-pane layout with sidebar

**Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: smoke test fixes for exploration workflow"
```
