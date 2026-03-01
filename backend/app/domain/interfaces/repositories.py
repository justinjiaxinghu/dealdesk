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
from app.domain.entities.field_validation import FieldValidation
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
