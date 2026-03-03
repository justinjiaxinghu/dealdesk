import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from app.domain.entities.deal import Deal
from app.domain.entities.document import Document
from app.domain.value_objects.enums import PropertyType, ProcessingStatus, DocumentType
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
        document_type=DocumentType.OFFERING_MEMORANDUM,
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
