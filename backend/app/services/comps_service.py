# backend/app/services/comps_service.py
from __future__ import annotations

import logging
from uuid import UUID

from app.domain.entities.comp import Comp
from app.domain.interfaces.providers import CompsProvider
from app.domain.interfaces.repositories import (
    CompRepository,
    DealRepository,
    ExtractedFieldRepository,
)

logger = logging.getLogger(__name__)


class CompsService:
    def __init__(
        self,
        deal_repo: DealRepository,
        extracted_field_repo: ExtractedFieldRepository,
        comp_repo: CompRepository,
        comps_provider: CompsProvider,
    ) -> None:
        self._deal_repo = deal_repo
        self._extracted_field_repo = extracted_field_repo
        self._comp_repo = comp_repo
        self._comps_provider = comps_provider

    async def search_comps(self, deal_id: UUID) -> list[Comp]:
        deal = await self._deal_repo.get_by_id(deal_id)
        if deal is None:
            raise ValueError(f"Deal {deal_id} not found")

        fields = await self._extracted_field_repo.get_by_deal_id(deal_id)

        comps = await self._comps_provider.search_comps(deal, fields)

        if comps:
            # Replace all existing comps for this deal with fresh results
            await self._comp_repo.delete_by_deal_id(deal_id)
            comps = await self._comp_repo.bulk_upsert(comps)

        logger.info("CompsService: stored %d comps for deal %s", len(comps), deal_id)
        return comps

    async def list_comps(self, deal_id: UUID) -> list[Comp]:
        return await self._comp_repo.get_by_deal_id(deal_id)
