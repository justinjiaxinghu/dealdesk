# backend/tests/conftest.py
"""Shared test fixtures and in-memory repository implementations."""

from __future__ import annotations

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
from app.domain.interfaces.repositories import (
    AssumptionRepository,
    AssumptionSetRepository,
    DealRepository,
    DocumentRepository,
    ExportRepository,
    ExtractedFieldRepository,
    MarketTableRepository,
)
from app.domain.value_objects.types import DealFilters, ProcessingStep


# ---------------------------------------------------------------------------
# In-memory repository implementations
# ---------------------------------------------------------------------------


class InMemoryDealRepository(DealRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Deal] = {}

    async def create(self, deal: Deal) -> Deal:
        self._store[deal.id] = deal
        return deal

    async def get_by_id(self, deal_id: UUID) -> Deal | None:
        return self._store.get(deal_id)

    async def list(self, filters: DealFilters | None = None) -> list[Deal]:
        deals = list(self._store.values())
        if filters:
            if filters.property_type:
                deals = [d for d in deals if d.property_type.value == filters.property_type]
            if filters.city:
                deals = [d for d in deals if d.city == filters.city]
        return deals

    async def update(self, deal: Deal) -> Deal:
        self._store[deal.id] = deal
        return deal


class InMemoryDocumentRepository(DocumentRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Document] = {}

    async def create(self, document: Document) -> Document:
        self._store[document.id] = document
        return document

    async def get_by_id(self, document_id: UUID) -> Document | None:
        return self._store.get(document_id)

    async def get_by_deal_id(self, deal_id: UUID) -> list[Document]:
        return [d for d in self._store.values() if d.deal_id == deal_id]

    async def update(self, document: Document) -> Document:
        self._store[document.id] = document
        return document

    async def update_processing_step(
        self, document_id: UUID, step: ProcessingStep
    ) -> Document:
        doc = self._store.get(document_id)
        if doc is None:
            raise ValueError(f"Document {document_id} not found")
        # Replace existing step with same name, or append
        updated = False
        for i, s in enumerate(doc.processing_steps):
            if s.name == step.name:
                doc.processing_steps[i] = step
                updated = True
                break
        if not updated:
            doc.processing_steps.append(step)
        self._store[document_id] = doc
        return doc


class InMemoryExtractedFieldRepository(ExtractedFieldRepository):
    def __init__(self, document_repo: InMemoryDocumentRepository | None = None) -> None:
        self._store: list[ExtractedField] = []
        self._document_repo = document_repo

    async def bulk_create(self, fields: list[ExtractedField]) -> list[ExtractedField]:
        self._store.extend(fields)
        return fields

    async def get_by_document_id(self, document_id: UUID) -> list[ExtractedField]:
        return [f for f in self._store if f.document_id == document_id]

    async def get_by_deal_id(self, deal_id: UUID) -> list[ExtractedField]:
        if self._document_repo is None:
            return []
        docs = await self._document_repo.get_by_deal_id(deal_id)
        doc_ids = {d.id for d in docs}
        return [f for f in self._store if f.document_id in doc_ids]


class InMemoryMarketTableRepository(MarketTableRepository):
    def __init__(self) -> None:
        self._store: list[MarketTable] = []

    async def bulk_create(self, tables: list[MarketTable]) -> list[MarketTable]:
        self._store.extend(tables)
        return tables

    async def get_by_document_id(self, document_id: UUID) -> list[MarketTable]:
        return [t for t in self._store if t.document_id == document_id]


class InMemoryAssumptionSetRepository(AssumptionSetRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, AssumptionSet] = {}

    async def create(self, assumption_set: AssumptionSet) -> AssumptionSet:
        self._store[assumption_set.id] = assumption_set
        return assumption_set

    async def get_by_id(self, set_id: UUID) -> AssumptionSet | None:
        return self._store.get(set_id)

    async def get_by_deal_id(self, deal_id: UUID) -> list[AssumptionSet]:
        return [s for s in self._store.values() if s.deal_id == deal_id]


class InMemoryAssumptionRepository(AssumptionRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Assumption] = {}

    async def bulk_upsert(self, assumptions: list[Assumption]) -> list[Assumption]:
        for a in assumptions:
            # Upsert by (set_id, key) — find existing and replace, or insert new
            existing = None
            for stored in self._store.values():
                if stored.set_id == a.set_id and stored.key == a.key:
                    existing = stored
                    break
            if existing:
                # Update in place
                a_with_id = Assumption(
                    id=existing.id,
                    set_id=a.set_id,
                    key=a.key,
                    value_number=a.value_number,
                    unit=a.unit,
                    range_min=a.range_min,
                    range_max=a.range_max,
                    source_type=a.source_type,
                    source_ref=a.source_ref,
                    notes=a.notes,
                )
                self._store[existing.id] = a_with_id
            else:
                self._store[a.id] = a
        return assumptions

    async def get_by_set_id(self, set_id: UUID) -> list[Assumption]:
        return [a for a in self._store.values() if a.set_id == set_id]

    async def update(self, assumption: Assumption) -> Assumption:
        self._store[assumption.id] = assumption
        return assumption


class InMemoryExportRepository(ExportRepository):
    def __init__(self) -> None:
        self._store: list[Export] = []

    async def create(self, export: Export) -> Export:
        self._store.append(export)
        return export

    async def get_by_deal_id(self, deal_id: UUID) -> list[Export]:
        return [e for e in self._store if e.deal_id == deal_id]
