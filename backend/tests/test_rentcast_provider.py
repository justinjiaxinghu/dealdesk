import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.domain.entities.deal import Deal
from app.domain.value_objects.enums import PropertyType


@pytest.fixture
def sample_deal():
    return Deal(
        id=uuid4(),
        name="Test Deal",
        address="123 Main St",
        city="Austin",
        state="TX",
        property_type=PropertyType.MULTIFAMILY,
        latitude=30.2672,
        longitude=-97.7431,
    )


@pytest.mark.asyncio
async def test_rentcast_provider_returns_comps(sample_deal):
    from app.infrastructure.comps.rentcast_provider import RentcastCompsProvider

    mock_response_data = {
        "properties": [
            {
                "id": "prop_1",
                "formattedAddress": "456 Oak Ave, Austin, TX 78701",
                "addressLine1": "456 Oak Ave",
                "city": "Austin",
                "state": "TX",
                "propertyType": "Multi-Family",
                "yearBuilt": 2018,
                "squareFootage": 45000,
                "lastSalePrice": 7920000,
                "rentEstimate": 1390,
            }
        ]
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.get.return_value = mock_response

        provider = RentcastCompsProvider(api_key="test_key")
        comps = await provider.search_comps(sample_deal, [])

    assert len(comps) == 1
    assert comps[0].address == "456 Oak Ave"
    assert comps[0].city == "Austin"
    assert comps[0].source.value == "rentcast"
    assert comps[0].rent_per_unit == 1390


@pytest.mark.asyncio
async def test_rentcast_provider_no_lat_lng_returns_empty(sample_deal):
    from app.infrastructure.comps.rentcast_provider import RentcastCompsProvider

    sample_deal.latitude = None
    sample_deal.longitude = None
    provider = RentcastCompsProvider(api_key="test_key")
    comps = await provider.search_comps(sample_deal, [])
    assert comps == []


@pytest.mark.asyncio
async def test_rentcast_provider_no_api_key_returns_empty(sample_deal):
    from app.infrastructure.comps.rentcast_provider import RentcastCompsProvider

    provider = RentcastCompsProvider(api_key="")
    comps = await provider.search_comps(sample_deal, [])
    assert comps == []
