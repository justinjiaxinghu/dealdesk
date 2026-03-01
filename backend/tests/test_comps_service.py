import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime

from app.domain.entities.comp import Comp
from app.domain.entities.deal import Deal
from app.domain.value_objects.enums import PropertyType, CompSource
from app.services.comps_service import CompsService


@pytest.fixture
def deal():
    return Deal(
        id=uuid4(),
        name="Test",
        address="123 Main",
        city="Austin",
        state="TX",
        property_type=PropertyType.MULTIFAMILY,
    )


@pytest.fixture
def sample_comp(deal):
    return Comp(
        deal_id=deal.id,
        address="456 Oak",
        city="Austin",
        state="TX",
        property_type=PropertyType.MULTIFAMILY,
        source=CompSource.RENTCAST,
        fetched_at=datetime.utcnow(),
        cap_rate=0.062,
    )


@pytest.mark.asyncio
async def test_search_comps_calls_provider_and_persists(deal, sample_comp):
    deal_repo = AsyncMock()
    deal_repo.get_by_id.return_value = deal
    field_repo = AsyncMock()
    field_repo.get_by_deal_id.return_value = []
    comp_repo = AsyncMock()
    comp_repo.bulk_upsert.return_value = [sample_comp]
    provider = AsyncMock()
    provider.search_comps.return_value = [sample_comp]

    service = CompsService(deal_repo, field_repo, comp_repo, provider)
    result = await service.search_comps(deal.id)

    assert len(result) == 1
    provider.search_comps.assert_called_once()
    comp_repo.delete_by_deal_id.assert_called_once_with(deal.id)
    comp_repo.bulk_upsert.assert_called_once()


@pytest.mark.asyncio
async def test_search_comps_raises_if_deal_not_found():
    deal_repo = AsyncMock()
    deal_repo.get_by_id.return_value = None
    service = CompsService(deal_repo, AsyncMock(), AsyncMock(), AsyncMock())

    with pytest.raises(ValueError, match="not found"):
        await service.search_comps(uuid4())


@pytest.mark.asyncio
async def test_search_comps_empty_provider_result_does_not_delete(deal):
    deal_repo = AsyncMock()
    deal_repo.get_by_id.return_value = deal
    field_repo = AsyncMock()
    field_repo.get_by_deal_id.return_value = []
    comp_repo = AsyncMock()
    provider = AsyncMock()
    provider.search_comps.return_value = []

    service = CompsService(deal_repo, field_repo, comp_repo, provider)
    result = await service.search_comps(deal.id)

    assert result == []
    comp_repo.delete_by_deal_id.assert_not_called()
    comp_repo.bulk_upsert.assert_not_called()


@pytest.mark.asyncio
async def test_list_comps(deal, sample_comp):
    comp_repo = AsyncMock()
    comp_repo.get_by_deal_id.return_value = [sample_comp]
    service = CompsService(AsyncMock(), AsyncMock(), comp_repo, AsyncMock())

    result = await service.list_comps(deal.id)
    assert len(result) == 1
    assert result[0].cap_rate == 0.062
