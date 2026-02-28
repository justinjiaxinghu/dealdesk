# backend/app/services/export_service.py
"""Service layer for Excel export."""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.export import Export
from app.domain.interfaces.providers import ExcelExporter, FileStorage
from app.domain.interfaces.repositories import (
    AssumptionRepository,
    AssumptionSetRepository,
    DealRepository,
    ExportRepository,
    ModelResultRepository,
)


class ExportService:
    def __init__(
        self,
        deal_repo: DealRepository,
        assumption_set_repo: AssumptionSetRepository,
        assumption_repo: AssumptionRepository,
        model_result_repo: ModelResultRepository,
        export_repo: ExportRepository,
        file_storage: FileStorage,
        excel_exporter: ExcelExporter,
    ) -> None:
        self._deal_repo = deal_repo
        self._assumption_set_repo = assumption_set_repo
        self._assumption_repo = assumption_repo
        self._model_result_repo = model_result_repo
        self._export_repo = export_repo
        self._file_storage = file_storage
        self._excel_exporter = excel_exporter

    async def export_xlsx(self, set_id: UUID) -> Export:
        # Get assumption set
        assumption_set = await self._assumption_set_repo.get_by_id(set_id)
        if assumption_set is None:
            raise ValueError(f"Assumption set {set_id} not found")

        # Get deal
        deal = await self._deal_repo.get_by_id(assumption_set.deal_id)
        if deal is None:
            raise ValueError(f"Deal {assumption_set.deal_id} not found")

        # Get assumptions
        assumptions = await self._assumption_repo.get_by_set_id(set_id)

        # Get latest model result
        result = await self._model_result_repo.get_by_set_id(set_id)
        if result is None:
            raise ValueError(
                f"No model result found for assumption set {set_id}. "
                "Run compute first."
            )

        # Generate Excel bytes
        xlsx_bytes = await self._excel_exporter.export(deal, assumptions, result)

        # Store file
        file_path = f"exports/{deal.id}/{set_id}.xlsx"
        await self._file_storage.store(xlsx_bytes, file_path)

        # Create export record
        export = Export(
            deal_id=deal.id,
            set_id=set_id,
            file_path=file_path,
        )
        return await self._export_repo.create(export)
