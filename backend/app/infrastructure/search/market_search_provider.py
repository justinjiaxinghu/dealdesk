from __future__ import annotations

import logging

from app.domain.entities.deal import Deal
from app.domain.interfaces.providers import MarketSearchProvider
from app.domain.value_objects.enums import ConnectorType
from app.domain.value_objects.types import SearchResult

logger = logging.getLogger(__name__)


class TavilyMarketSearchProvider(MarketSearchProvider):
    def __init__(self, tavily_api_key: str) -> None:
        self._tavily_api_key = tavily_api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            from tavily import AsyncTavilyClient
            self._client = AsyncTavilyClient(api_key=self._tavily_api_key)
        return self._client

    async def search(
        self,
        query: str,
        connectors: list[ConnectorType],
        deal: Deal | None = None,
    ) -> list[SearchResult]:
        results: list[SearchResult] = []

        if ConnectorType.TAVILY in connectors:
            try:
                client = self._get_client()
                response = await client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=10,
                )
                for r in response.get("results", []):
                    results.append(
                        SearchResult(
                            title=r.get("title", ""),
                            url=r.get("url", ""),
                            snippet=r.get("content", ""),
                            source=ConnectorType.TAVILY.value,
                            raw_data=r,
                        )
                    )
            except Exception:
                logger.exception("Tavily search failed for query: %s", query)

        # Mock connectors — return empty for now
        for connector in connectors:
            if connector != ConnectorType.TAVILY:
                logger.info("Mock connector %s: no results (not implemented)", connector.value)

        return results
