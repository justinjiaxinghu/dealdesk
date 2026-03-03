# backend/app/infrastructure/comps/combined_provider.py
"""Combines Rentcast + Tavily results, deduplicates by address."""

from __future__ import annotations

import asyncio
import logging

from app.domain.entities.comp import Comp
from app.domain.entities.deal import Deal
from app.domain.entities.extraction import ExtractedField
from app.domain.interfaces.providers import CompsProvider

logger = logging.getLogger(__name__)


class CombinedCompsProvider(CompsProvider):
    def __init__(
        self,
        rentcast: CompsProvider,
        tavily: CompsProvider,
    ) -> None:
        self._rentcast = rentcast
        self._tavily = tavily

    async def search_comps(
        self,
        deal: Deal,
        extracted_fields: list[ExtractedField],
    ) -> list[Comp]:
        rentcast_result, tavily_result = await asyncio.gather(
            self._rentcast.search_comps(deal, extracted_fields),
            self._tavily.search_comps(deal, extracted_fields),
            return_exceptions=True,
        )

        all_comps: list[Comp] = []

        if isinstance(rentcast_result, list):
            all_comps.extend(rentcast_result)
        else:
            logger.warning("Rentcast provider failed: %s", rentcast_result)

        if isinstance(tavily_result, list):
            all_comps.extend(tavily_result)
        else:
            logger.warning("Tavily provider failed: %s", tavily_result)

        # Deduplicate by normalized address — Rentcast preferred (comes first)
        seen: set[str] = set()
        unique: list[Comp] = []
        for comp in all_comps:
            key = comp.address.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(comp)

        logger.info("Combined provider: %d unique comps for deal %s", len(unique), deal.id)
        return unique
