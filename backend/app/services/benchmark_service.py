# backend/app/services/benchmark_service.py
"""Service layer for benchmark generation."""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.assumption import Assumption
from app.domain.interfaces.providers import LLMProvider
from app.domain.interfaces.repositories import (
    AssumptionRepository,
    AssumptionSetRepository,
    DealRepository,
)
from app.domain.value_objects.enums import SourceType
from app.domain.value_objects.types import BenchmarkSuggestion, Location


class BenchmarkService:
    def __init__(
        self,
        deal_repo: DealRepository,
        assumption_set_repo: AssumptionSetRepository,
        assumption_repo: AssumptionRepository,
        llm_provider: LLMProvider,
    ) -> None:
        self._deal_repo = deal_repo
        self._assumption_set_repo = assumption_set_repo
        self._assumption_repo = assumption_repo
        self._llm_provider = llm_provider

    async def generate_benchmarks(
        self, deal_id: UUID
    ) -> list[BenchmarkSuggestion]:
        deal = await self._deal_repo.get_by_id(deal_id)
        if deal is None:
            raise ValueError(f"Deal {deal_id} not found")

        location = Location(
            address=deal.address,
            city=deal.city,
            state=deal.state,
            latitude=deal.latitude,
            longitude=deal.longitude,
        )

        suggestions = await self._llm_provider.generate_benchmarks(
            location, deal.property_type
        )

        # Upsert assumptions from benchmarks into the first assumption set
        sets = await self._assumption_set_repo.get_by_deal_id(deal_id)
        if not sets:
            raise ValueError(f"No assumption sets found for deal {deal_id}")

        target_set = sets[0]
        assumptions = [
            Assumption(
                set_id=target_set.id,
                key=s.key,
                value_number=s.value,
                unit=s.unit,
                range_min=s.range_min,
                range_max=s.range_max,
                source_type=SourceType.AI,
                source_ref=s.source,
            )
            for s in suggestions
        ]
        if assumptions:
            await self._assumption_repo.bulk_upsert(assumptions)

        return suggestions
