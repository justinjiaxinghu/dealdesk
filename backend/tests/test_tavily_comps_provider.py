import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.domain.entities.deal import Deal
from app.domain.value_objects.enums import PropertyType, CompSource


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
async def test_tavily_comps_provider_returns_comps(sample_deal):
    from app.infrastructure.comps.tavily_provider import TavilyCompsProvider

    mock_search_result = {
        "results": [
            {
                "url": "https://zillow.com/homedetails/456-oak-ave",
                "title": "456 Oak Ave - Austin TX Multifamily",
                "content": "48 unit apartment sold for $7.9M, cap rate 6.2%, built 2018",
            }
        ]
    }

    mock_llm_response = MagicMock()
    mock_llm_response.choices = [MagicMock()]
    mock_llm_response.choices[0].message.content = '{"comps": [{"address": "456 Oak Ave", "city": "Austin", "state": "TX", "property_type": "multifamily", "year_built": 2018, "unit_count": 48, "cap_rate": 0.062, "sale_price": 7900000, "source_url": "https://zillow.com/homedetails/456-oak-ave"}]}'

    mock_tavily = AsyncMock()
    mock_tavily.search.return_value = mock_search_result

    mock_openai_client = AsyncMock()
    mock_openai_client.chat.completions.create.return_value = mock_llm_response

    with patch("app.infrastructure.comps.tavily_provider.AsyncTavilyClient", return_value=mock_tavily), \
         patch("app.infrastructure.comps.tavily_provider.AsyncOpenAI", return_value=mock_openai_client):

        provider = TavilyCompsProvider(
            tavily_api_key="test_tavily",
            openai_api_key="test_openai",
            openai_model="gpt-4o",
        )
        comps = await provider.search_comps(sample_deal, [])

    assert len(comps) >= 1
    assert comps[0].source == CompSource.TAVILY
    assert comps[0].cap_rate == 0.062


@pytest.mark.asyncio
async def test_tavily_comps_provider_empty_search_returns_empty(sample_deal):
    from app.infrastructure.comps.tavily_provider import TavilyCompsProvider

    mock_tavily = AsyncMock()
    mock_tavily.search.return_value = {"results": []}

    with patch("app.infrastructure.comps.tavily_provider.AsyncTavilyClient", return_value=mock_tavily), \
         patch("app.infrastructure.comps.tavily_provider.AsyncOpenAI"):

        provider = TavilyCompsProvider(
            tavily_api_key="test_tavily",
            openai_api_key="test_openai",
        )
        comps = await provider.search_comps(sample_deal, [])

    assert comps == []
