from __future__ import annotations
from uuid import UUID
from app.domain.entities.historical_financial import HistoricalFinancial
from app.domain.interfaces.providers import DocumentProcessor, FileStorage, LLMProvider
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
        file_storage: FileStorage,
    ) -> None:
        self._deal_repo = deal_repo
        self._document_repo = document_repo
        self._hf_repo = hf_repo
        self._llm = llm_provider
        self._processor = document_processor
        self._file_storage = file_storage

    async def extract(self, deal_id: UUID, document_id: UUID) -> list[HistoricalFinancial]:
        deal = await self._deal_repo.get_by_id(deal_id)
        if deal is None:
            raise ValueError(f"Deal {deal_id} not found")
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        file_path = await self._file_storage.retrieve(document.file_path)
        pages = await self._processor.extract_text(file_path)
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
