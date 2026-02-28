# backend/app/infrastructure/llm/openai_provider.py
from __future__ import annotations

import json

from openai import AsyncOpenAI
from tavily import AsyncTavilyClient

from app.config import settings
from app.domain.entities.assumption import Assumption
from app.domain.entities.deal import Deal
from app.domain.entities.extraction import ExtractedField
from app.domain.interfaces.providers import LLMProvider
from app.domain.value_objects.enums import PropertyType
from app.domain.value_objects.types import (
    BenchmarkSuggestion,
    FieldValidationResult,
    Location,
    NormalizedField,
    PageText,
    QuickExtractResult,
    RawField,
    ValidationSource,
)


class OpenAILLMProvider(LLMProvider):
    """LLM provider backed by OpenAI API."""

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
        self._tavily: AsyncTavilyClient | None = None

    async def generate_benchmarks(
        self, location: Location, property_type: PropertyType
    ) -> list[BenchmarkSuggestion]:
        prompt = (
            f"You are a commercial real estate analyst. Generate market benchmark "
            f"assumptions for a {property_type.value} property located at "
            f"{location.address}, {location.city}, {location.state}.\n\n"
            f"Return a JSON object with a single key 'benchmarks' containing an "
            f"array of objects. Each object must have these exact keys:\n"
            f'  "key": string (e.g. "rent_psf_yr", "vacancy_rate", "cap_rate", '
            f'"opex_ratio")\n'
            f'  "value": number\n'
            f'  "unit": string (e.g. "$/sf/yr", "%", "ratio")\n'
            f'  "range_min": number\n'
            f'  "range_max": number\n'
            f'  "source": string (data source description)\n'
            f'  "confidence": number between 0 and 1\n\n'
            f"Include at least: rent_psf_yr, vacancy_rate, cap_rate, opex_ratio, "
            f"purchase_price (total purchase price, not per square foot)."
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        benchmarks_raw = data.get("benchmarks", [])

        return [
            BenchmarkSuggestion(
                key=b["key"],
                value=float(b["value"]),
                unit=b["unit"],
                range_min=float(b["range_min"]),
                range_max=float(b["range_max"]),
                source=b["source"],
                confidence=float(b["confidence"]),
            )
            for b in benchmarks_raw
        ]

    async def normalize_extracted_fields(
        self, raw_fields: list[RawField]
    ) -> list[NormalizedField]:
        fields_data = [
            {"key": f.key, "value": f.value, "source_page": f.source_page}
            for f in raw_fields
        ]

        prompt = (
            f"You are a commercial real estate document parser. Normalize these "
            f"extracted fields into canonical form.\n\n"
            f"Raw fields:\n{json.dumps(fields_data, indent=2)}\n\n"
            f"Return a JSON object with a single key 'fields' containing an array "
            f"of objects. Each object must have these exact keys:\n"
            f'  "key": string (canonical field name, e.g. "rent_psf_yr", '
            f'"square_feet", "vacancy_rate")\n'
            f'  "value_text": string or null (text representation)\n'
            f'  "value_number": number or null (numeric value if applicable)\n'
            f'  "unit": string or null (e.g. "$/sf/yr", "sf", "%")\n'
            f'  "confidence": number between 0 and 1\n'
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        fields_raw = data.get("fields", [])

        return [
            NormalizedField(
                key=f["key"],
                value_text=f.get("value_text"),
                value_number=(
                    float(f["value_number"]) if f.get("value_number") is not None else None
                ),
                unit=f.get("unit"),
                confidence=float(f.get("confidence", 0.5)),
            )
            for f in fields_raw
        ]

    async def quick_extract_deal_info(
        self, pages: list[PageText]
    ) -> QuickExtractResult:
        valid_property_types = [pt.value for pt in PropertyType]
        text = "\n\n".join(
            f"--- Page {p.page_number} ---\n{p.text}" for p in pages
        )

        prompt = (
            "You are a commercial real estate document parser. Extract the basic "
            "deal information from this Offering Memorandum text.\n\n"
            f"Document text:\n{text}\n\n"
            "Return a JSON object with these exact keys:\n"
            '  "name": string - a short deal name (e.g. "Lund Pointe Apartments" '
            'or "100 Main St Acquisition")\n'
            '  "address": string - street address\n'
            '  "city": string - city name\n'
            '  "state": string - two-letter state abbreviation\n'
            f'  "property_type": string - MUST be one of: {json.dumps(valid_property_types)}\n'
            '  "square_feet": number or null - total square footage if mentioned\n\n'
            "Use null for any field you cannot determine from the text."
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        sq_ft = data.get("square_feet")
        raw_pt = data.get("property_type")
        # Validate against enum; fall back to null if LLM returns invalid value
        pt = raw_pt if raw_pt in valid_property_types else None

        return QuickExtractResult(
            name=data.get("name"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            property_type=pt,
            square_feet=float(sq_ft) if sq_ft is not None else None,
        )

    async def validate_om_fields(
        self,
        deal: Deal,
        fields: list[ExtractedField],
        benchmarks: list[Assumption],
    ) -> list[FieldValidationResult]:
        # Build context for the LLM
        fields_text = "\n".join(
            f"  - {f.field_key}: {f.value_number} {f.unit or ''}"
            for f in fields
            if f.value_number is not None
        )
        benchmarks_text = "\n".join(
            f"  - {a.key}: {a.value_number} {a.unit or ''} (range: {a.range_min}-{a.range_max})"
            for a in benchmarks
        )

        system_prompt = (
            "You are a commercial real estate analyst validating an Offering Memorandum. "
            "You have access to a web_search tool to look up current market data. "
            "For each financial metric from the OM, research the local market, compare "
            "the OM value to what you find, and assess whether it is reasonable.\n\n"
            "You MUST cite your sources. Every claim about market data must reference "
            "a specific source from your web searches.\n\n"
            "Only validate financial/operational metrics (rent, vacancy, cap rate, expenses, etc.). "
            "Skip descriptive fields like address, square footage, or property name."
        )

        user_prompt = (
            f"Property: {deal.property_type.value} at {deal.address}, {deal.city}, {deal.state}\n"
            f"Square Feet: {deal.square_feet or 'unknown'}\n\n"
            f"OM Extracted Fields:\n{fields_text}\n\n"
            f"AI Market Benchmarks:\n{benchmarks_text}\n\n"
            "Use the web_search tool to research current market data for this property's "
            "submarket. Then return a JSON object with a single key 'validations' containing "
            "an array. Each object must have:\n"
            '  "field_key": string (matching the OM field key)\n'
            '  "om_value": number (the OM value)\n'
            '  "market_value": number or null (market reference point)\n'
            '  "status": one of "within_range", "above_market", "below_market", "suspicious", "insufficient_data"\n'
            '  "explanation": string (detailed explanation citing sources with [Source Title](URL) markdown links)\n'
            '  "sources": array of {"url": string, "title": string, "snippet": string}\n'
            '  "confidence": number 0-1\n'
        )

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current market data, comps, and reports.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for market data",
                            }
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Agentic loop: let GPT-4o call web_search as many times as it needs
        for _ in range(10):  # max 10 tool call rounds
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                temperature=0.2,
            )

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                messages.append(choice.message.model_dump())

                for tool_call in choice.message.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query", "")

                    # Call Tavily (lazy init)
                    if self._tavily is None:
                        self._tavily = AsyncTavilyClient(api_key=settings.tavily_api_key)
                    search_result = await self._tavily.search(
                        query=query,
                        search_depth="advanced",
                        max_results=5,
                    )

                    results_text = json.dumps(
                        [
                            {
                                "title": r.get("title", ""),
                                "url": r.get("url", ""),
                                "content": r.get("content", "")[:500],
                            }
                            for r in search_result.get("results", [])
                        ]
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": results_text,
                        }
                    )
            else:
                # Final response — parse JSON
                break

        content = response.choices[0].message.content or "{}"

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]

        data = json.loads(content)
        validations_raw = data.get("validations", [])

        return [
            FieldValidationResult(
                field_key=v["field_key"],
                om_value=v.get("om_value"),
                market_value=v.get("market_value"),
                status=v["status"],
                explanation=v["explanation"],
                sources=[
                    ValidationSource(
                        url=s.get("url", ""),
                        title=s.get("title", ""),
                        snippet=s.get("snippet", ""),
                    )
                    for s in v.get("sources", [])
                ],
                confidence=float(v.get("confidence", 0.5)),
            )
            for v in validations_raw
        ]
