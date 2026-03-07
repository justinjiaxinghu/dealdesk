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
)
from app.domain.entities.comp import Comp
from app.domain.entities.field_validation import FieldValidation
from app.domain.entities.historical_financial import HistoricalFinancial
from app.domain.entities.exploration import ExplorationSession
from app.domain.entities.chat import ChatSession, ChatMessage
from app.domain.entities.snapshot import Snapshot
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

    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[ExtractedField]: ...


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


class ExportRepository(ABC):
    @abstractmethod
    async def create(self, export: Export) -> Export: ...

    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[Export]: ...


class FieldValidationRepository(ABC):
    @abstractmethod
    async def bulk_upsert(self, validations: list[FieldValidation]) -> list[FieldValidation]: ...

    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[FieldValidation]: ...


class CompRepository(ABC):
    @abstractmethod
    async def bulk_upsert(self, comps: list[Comp]) -> list[Comp]: ...

    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[Comp]: ...

    @abstractmethod
    async def delete_by_deal_id(self, deal_id: UUID) -> None: ...


class HistoricalFinancialRepository(ABC):
    @abstractmethod
    async def bulk_upsert(
        self, items: list[HistoricalFinancial]
    ) -> list[HistoricalFinancial]: ...

    @abstractmethod
    async def get_by_deal_id(self, deal_id: UUID) -> list[HistoricalFinancial]: ...


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
