# backend/app/infrastructure/comps/tavily_provider.py
"""Tavily + GPT-4o provider for scraping comparable properties from Zillow/Redfin."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from openai import AsyncOpenAI
from tavily import AsyncTavilyClient

from app.domain.entities.comp import Comp
from app.domain.entities.deal import Deal
from app.domain.entities.extraction import ExtractedField
from app.domain.interfaces.providers import CompsProvider
from app.domain.value_objects.enums import CompSource, PropertyType

logger = logging.getLogger(__name__)


class TavilyCompsProvider(CompsProvider):
    def __init__(
        self,
        tavily_api_key: str,
        openai_api_key: str,
        openai_model: str = "gpt-4o",
    ) -> None:
        self._tavily = AsyncTavilyClient(api_key=tavily_api_key)
        self._openai = AsyncOpenAI(api_key=openai_api_key)
        self._model = openai_model

    async def search_comps(
        self,
        deal: Deal,
        extracted_fields: list[ExtractedField],
    ) -> list[Comp]:
        property_type = deal.property_type.value
        location = f"{deal.city}, {deal.state}"

        queries = [
            f"{property_type} sold {location} 2023 2024 comparable properties",
            f"{property_type} comps {location} cap rate price per unit site:zillow.com OR site:loopnet.com",
        ]

        raw_results: list[dict] = []
        for query in queries:
            try:
                result = await self._tavily.search(
                    query=query,
                    search_depth="basic",
                    max_results=5,
                )
                raw_results.extend(result.get("results", []))
            except Exception as exc:
                logger.warning("Tavily search failed for query '%s': %s", query, exc)

        if not raw_results:
            return []

        search_text = "\n\n".join(
            f"URL: {r.get('url', '')}\nTitle: {r.get('title', '')}\nContent: {r.get('content', r.get('snippet', ''))[:500]}"
            for r in raw_results
        )

        system_prompt = f"""You are extracting comparable property data from web search results.
The subject property is a {property_type} in {location}.

Extract any comparable properties you find. Return ONLY a JSON object with this structure:
{{
    "comps": [
        {{
            "address": "street address only",
            "city": "city",
            "state": "2-letter state",
            "property_type": "{property_type}",
            "year_built": <int or null>,
            "unit_count": <int or null>,
            "square_feet": <float or null>,
            "sale_price": <float or null>,
            "price_per_unit": <float or null>,
            "price_per_sqft": <float or null>,
            "cap_rate": <decimal like 0.062, NOT 6.2 — or null>,
            "rent_per_unit": <monthly rent float or null>,
            "occupancy_rate": <decimal like 0.95, NOT 95 — or null>,
            "expense_ratio": <decimal or null>,
            "source_url": "url of the source"
        }}
    ]
}}

Only include properties with at least an address and one financial metric. Return {{"comps": []}} if none found."""

        try:
            response = await self._openai.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Search results:\n\n{search_text}"},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = response.choices[0].message.content or "{}"
            data = self._extract_json(content)
        except Exception as exc:
            logger.warning("GPT-4o comp extraction failed: %s", exc)
            return []

        fetched_at = datetime.utcnow()
        comps: list[Comp] = []

        for item in data.get("comps", []):
            address = item.get("address", "").strip()
            if not address:
                continue

            raw_pt = item.get("property_type", property_type)
            try:
                pt = PropertyType(raw_pt)
            except ValueError:
                pt = deal.property_type

            comps.append(
                Comp(
                    deal_id=deal.id,
                    address=address,
                    city=item.get("city", deal.city),
                    state=item.get("state", deal.state),
                    property_type=pt,
                    source=CompSource.TAVILY,
                    source_url=item.get("source_url"),
                    year_built=item.get("year_built"),
                    unit_count=item.get("unit_count"),
                    square_feet=item.get("square_feet"),
                    sale_price=item.get("sale_price"),
                    price_per_unit=item.get("price_per_unit"),
                    price_per_sqft=item.get("price_per_sqft"),
                    cap_rate=item.get("cap_rate"),
                    rent_per_unit=item.get("rent_per_unit"),
                    occupancy_rate=item.get("occupancy_rate"),
                    expense_ratio=item.get("expense_ratio"),
                    fetched_at=fetched_at,
                )
            )

        logger.info("Tavily/GPT-4o returned %d comps for deal %s", len(comps), deal.id)
        return comps

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response, handling markdown code blocks."""
        text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("```").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from LLM response: %s", text[:200])
            return {"comps": []}
