# backend/app/api/dependencies.py
"""FastAPI dependency injection wiring."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.database import get_session

# ---------------------------------------------------------------------------
# Provider singletons (stateless, created once)
# ---------------------------------------------------------------------------

from app.infrastructure.document_processing.pdfplumber_processor import (
    PdfPlumberProcessor,
)
from app.infrastructure.export.excel_exporter import OpenpyxlExcelExporter
from app.infrastructure.file_storage.local import LocalFileStorage
from app.infrastructure.llm.openai_provider import OpenAILLMProvider

_file_storage = LocalFileStorage()
_document_processor = PdfPlumberProcessor()
_llm_provider = OpenAILLMProvider()
_excel_exporter = OpenpyxlExcelExporter()


# ---------------------------------------------------------------------------
# Session dependency
# ---------------------------------------------------------------------------


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


# ---------------------------------------------------------------------------
# Repository factories (per-request, session-scoped)
# ---------------------------------------------------------------------------

from app.infrastructure.persistence.assumption_repo import (
    SqlAlchemyAssumptionRepository,
    SqlAlchemyAssumptionSetRepository,
)
from app.infrastructure.persistence.deal_repo import SqlAlchemyDealRepository
from app.infrastructure.persistence.document_repo import (
    SqlAlchemyDocumentRepository,
)
from app.infrastructure.persistence.export_repo import SqlAlchemyExportRepository
from app.infrastructure.persistence.extraction_repo import (
    SqlAlchemyExtractedFieldRepository,
    SqlAlchemyMarketTableRepository,
)


def get_deal_repo(session: DbSession) -> SqlAlchemyDealRepository:
    return SqlAlchemyDealRepository(session)


def get_document_repo(session: DbSession) -> SqlAlchemyDocumentRepository:
    return SqlAlchemyDocumentRepository(session)


def get_extracted_field_repo(session: DbSession) -> SqlAlchemyExtractedFieldRepository:
    return SqlAlchemyExtractedFieldRepository(session)


def get_market_table_repo(session: DbSession) -> SqlAlchemyMarketTableRepository:
    return SqlAlchemyMarketTableRepository(session)


def get_assumption_set_repo(session: DbSession) -> SqlAlchemyAssumptionSetRepository:
    return SqlAlchemyAssumptionSetRepository(session)


def get_assumption_repo(session: DbSession) -> SqlAlchemyAssumptionRepository:
    return SqlAlchemyAssumptionRepository(session)


def get_export_repo(session: DbSession) -> SqlAlchemyExportRepository:
    return SqlAlchemyExportRepository(session)


# ---------------------------------------------------------------------------
# Service factories (compose repos + providers)
# ---------------------------------------------------------------------------

from app.services.benchmark_service import BenchmarkService
from app.services.deal_service import DealService
from app.services.document_service import DocumentService
from app.services.export_service import ExportService


def get_deal_service(
    deal_repo: Annotated[SqlAlchemyDealRepository, Depends(get_deal_repo)],
    assumption_set_repo: Annotated[
        SqlAlchemyAssumptionSetRepository, Depends(get_assumption_set_repo)
    ],
) -> DealService:
    return DealService(
        deal_repo=deal_repo,
        assumption_set_repo=assumption_set_repo,
    )


def get_document_service(
    document_repo: Annotated[
        SqlAlchemyDocumentRepository, Depends(get_document_repo)
    ],
    extracted_field_repo: Annotated[
        SqlAlchemyExtractedFieldRepository, Depends(get_extracted_field_repo)
    ],
    market_table_repo: Annotated[
        SqlAlchemyMarketTableRepository, Depends(get_market_table_repo)
    ],
) -> DocumentService:
    return DocumentService(
        document_repo=document_repo,
        extracted_field_repo=extracted_field_repo,
        market_table_repo=market_table_repo,
        file_storage=_file_storage,
        document_processor=_document_processor,
        llm_provider=_llm_provider,
    )


def get_benchmark_service(
    deal_repo: Annotated[SqlAlchemyDealRepository, Depends(get_deal_repo)],
    assumption_set_repo: Annotated[
        SqlAlchemyAssumptionSetRepository, Depends(get_assumption_set_repo)
    ],
    assumption_repo: Annotated[
        SqlAlchemyAssumptionRepository, Depends(get_assumption_repo)
    ],
) -> BenchmarkService:
    return BenchmarkService(
        deal_repo=deal_repo,
        assumption_set_repo=assumption_set_repo,
        assumption_repo=assumption_repo,
        llm_provider=_llm_provider,
    )


def get_export_service(
    deal_repo: Annotated[SqlAlchemyDealRepository, Depends(get_deal_repo)],
    assumption_set_repo: Annotated[
        SqlAlchemyAssumptionSetRepository, Depends(get_assumption_set_repo)
    ],
    assumption_repo: Annotated[
        SqlAlchemyAssumptionRepository, Depends(get_assumption_repo)
    ],
    export_repo: Annotated[SqlAlchemyExportRepository, Depends(get_export_repo)],
) -> ExportService:
    return ExportService(
        deal_repo=deal_repo,
        assumption_set_repo=assumption_set_repo,
        assumption_repo=assumption_repo,
        export_repo=export_repo,
        file_storage=_file_storage,
        excel_exporter=_excel_exporter,
    )
