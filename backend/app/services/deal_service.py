# backend/app/services/deal_service.py
"""Service layer for deal operations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.domain.entities.assumption import AssumptionSet
from app.domain.entities.deal import Deal
from app.domain.interfaces.repositories import AssumptionSetRepository, DealRepository
from app.domain.value_objects.enums import PropertyType
from app.domain.value_objects.types import DealFilters


class DealService:
    def __init__(
        self,
        deal_repo: DealRepository,
        assumption_set_repo: AssumptionSetRepository,
    ) -> None:
        self._deal_repo = deal_repo
        self._assumption_set_repo = assumption_set_repo

    async def create_deal(
        self,
        name: str,
        address: str,
        city: str,
        state: str,
        property_type: PropertyType,
        latitude: float | None = None,
        longitude: float | None = None,
        square_feet: float | None = None,
    ) -> Deal:
        deal = Deal(
            name=name,
            address=address,
            city=city,
            state=state,
            property_type=property_type,
            latitude=latitude,
            longitude=longitude,
            square_feet=square_feet,
        )
        deal = await self._deal_repo.create(deal)

        # Create default "Base Case" assumption set
        base_set = AssumptionSet(deal_id=deal.id, name="Base Case")
        await self._assumption_set_repo.create(base_set)

        return deal

    async def get_deal(self, deal_id: UUID) -> Deal | None:
        return await self._deal_repo.get_by_id(deal_id)

    async def list_deals(
        self,
        property_type: str | None = None,
        status: str | None = None,
        city: str | None = None,
    ) -> list[Deal]:
        filters = DealFilters(
            property_type=property_type,
            status=status,
            city=city,
        )
        return await self._deal_repo.list(filters)

    async def update_deal(
        self,
        deal_id: UUID,
        **kwargs,
    ) -> Deal | None:
        deal = await self._deal_repo.get_by_id(deal_id)
        if deal is None:
            return None

        for field, value in kwargs.items():
            if value is not None and hasattr(deal, field):
                setattr(deal, field, value)
        deal.updated_at = datetime.utcnow()

        return await self._deal_repo.update(deal)
