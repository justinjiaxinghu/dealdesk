# backend/app/api/dependencies.py
"""FastAPI dependency injection wiring."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.persistence.database import get_session

# ---------------------------------------------------------------------------
# Provider singletons (stateless, created once)
# ---------------------------------------------------------------------------

from app.infrastructure.comps.combined_provider import CombinedCompsProvider
from app.infrastructure.comps.rentcast_provider import RentcastCompsProvider
from app.infrastructure.comps.tavily_provider import TavilyCompsProvider
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
from app.infrastructure.persistence.comp_repo import SqlAlchemyCompRepository
from app.infrastructure.persistence.field_validation_repo import (
    SqlAlchemyFieldValidationRepository,
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


def get_field_validation_repo(session: DbSession) -> SqlAlchemyFieldValidationRepository:
    return SqlAlchemyFieldValidationRepository(session)


def get_comp_repo(session: DbSession) -> SqlAlchemyCompRepository:
    return SqlAlchemyCompRepository(session)


# ---------------------------------------------------------------------------
# Service factories (compose repos + providers)
# ---------------------------------------------------------------------------

from app.services.benchmark_service import BenchmarkService
from app.services.comps_service import CompsService
from app.services.deal_service import DealService
from app.services.document_service import DocumentService
from app.services.export_service import ExportService
from app.services.validation_service import ValidationService


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


def get_validation_service(
    deal_repo: Annotated[SqlAlchemyDealRepository, Depends(get_deal_repo)],
    assumption_set_repo: Annotated[
        SqlAlchemyAssumptionSetRepository, Depends(get_assumption_set_repo)
    ],
    assumption_repo: Annotated[
        SqlAlchemyAssumptionRepository, Depends(get_assumption_repo)
    ],
    field_validation_repo: Annotated[
        SqlAlchemyFieldValidationRepository, Depends(get_field_validation_repo)
    ],
    extracted_field_repo: Annotated[
        SqlAlchemyExtractedFieldRepository, Depends(get_extracted_field_repo)
    ],
) -> ValidationService:
    return ValidationService(
        deal_repo=deal_repo,
        assumption_set_repo=assumption_set_repo,
        assumption_repo=assumption_repo,
        field_validation_repo=field_validation_repo,
        extracted_field_repo=extracted_field_repo,
        llm_provider=_llm_provider,
    )


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
