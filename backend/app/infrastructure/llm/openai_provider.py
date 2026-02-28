# backend/app/infrastructure/llm/openai_provider.py
from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.config import settings
from app.domain.interfaces.providers import LLMProvider
from app.domain.value_objects.enums import PropertyType
from app.domain.value_objects.types import (
    BenchmarkSuggestion,
    Location,
    NormalizedField,
    RawField,
)


class OpenAILLMProvider(LLMProvider):
    """LLM provider backed by OpenAI API."""

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

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
            f"purchase_price_psf."
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
