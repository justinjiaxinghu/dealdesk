# backend/app/infrastructure/persistence/document_repo.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document import Document
from app.domain.interfaces.repositories import DocumentRepository
from app.domain.value_objects.types import ProcessingStep
from app.infrastructure.persistence.mappers import (
    document_to_entity,
    document_to_model,
)
from app.infrastructure.persistence.models import DocumentModel


class SqlAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, document: Document) -> Document:
        model = document_to_model(document)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return document_to_entity(model)

    async def get_by_id(self, document_id: UUID) -> Document | None:
        stmt = select(DocumentModel).where(DocumentModel.id == document_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return document_to_entity(model) if model else None

    async def get_by_deal_id(self, deal_id: UUID) -> list[Document]:
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.deal_id == deal_id)
            .order_by(DocumentModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [document_to_entity(m) for m in result.scalars().all()]

    async def update(self, document: Document) -> Document:
        stmt = select(DocumentModel).where(DocumentModel.id == document.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.document_type = document.document_type.value
        model.file_path = document.file_path
        model.original_filename = document.original_filename
        model.processing_status = document.processing_status.value
        model.processing_steps = [
            {"name": s.name, "status": s.status, "detail": s.detail}
            for s in document.processing_steps
        ]
        model.error_message = document.error_message
        model.page_count = document.page_count
        model.updated_at = datetime.utcnow()
        await self._session.flush()
        await self._session.refresh(model)
        return document_to_entity(model)

    async def update_processing_step(
        self, document_id: UUID, step: ProcessingStep
    ) -> Document:
        stmt = select(DocumentModel).where(DocumentModel.id == document_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()

        # Manage the JSON processing_steps array
        steps: list[dict] = list(model.processing_steps or [])
        # Replace existing step with the same name, or append
        updated = False
        for i, existing in enumerate(steps):
            if existing["name"] == step.name:
                steps[i] = {
                    "name": step.name,
                    "status": step.status,
                    "detail": step.detail,
                }
                updated = True
                break
        if not updated:
            steps.append(
                {"name": step.name, "status": step.status, "detail": step.detail}
            )

        model.processing_steps = steps
        model.updated_at = datetime.utcnow()
        await self._session.flush()
        await self._session.refresh(model)
        return document_to_entity(model)
