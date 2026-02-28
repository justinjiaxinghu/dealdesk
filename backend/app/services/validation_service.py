from __future__ import annotations

from uuid import UUID

from app.domain.entities.field_validation import FieldValidation
from app.domain.interfaces.providers import LLMProvider
from app.domain.interfaces.repositories import (
    AssumptionRepository,
    AssumptionSetRepository,
    DealRepository,
    ExtractedFieldRepository,
    FieldValidationRepository,
)
from app.domain.value_objects.enums import ValidationStatus


class ValidationService:
    def __init__(
        self,
        deal_repo: DealRepository,
        assumption_set_repo: AssumptionSetRepository,
        assumption_repo: AssumptionRepository,
        field_validation_repo: FieldValidationRepository,
        extracted_field_repo: ExtractedFieldRepository,
        llm_provider: LLMProvider,
    ) -> None:
        self._deal_repo = deal_repo
        self._assumption_set_repo = assumption_set_repo
        self._assumption_repo = assumption_repo
        self._field_validation_repo = field_validation_repo
        self._extracted_field_repo = extracted_field_repo
        self._llm_provider = llm_provider

    async def validate_fields(self, deal_id: UUID) -> list[FieldValidation]:
        # Fetch deal
        deal = await self._deal_repo.get_by_id(deal_id)
        if deal is None:
            raise ValueError(f"Deal {deal_id} not found")

        # Fetch all extracted fields across documents
        all_fields = await self._extracted_field_repo.get_by_deal_id(deal_id)

        # Filter to numeric fields only
        numeric_fields = [f for f in all_fields if f.value_number is not None]

        if not numeric_fields:
            return []

        # Fetch benchmarks for context
        sets = await self._assumption_set_repo.get_by_deal_id(deal_id)
        benchmarks = []
        if sets:
            benchmarks = await self._assumption_repo.get_by_set_id(sets[0].id)

        # Call LLM for validation
        results = await self._llm_provider.validate_om_fields(
            deal, numeric_fields, benchmarks
        )

        # Convert to entities and persist
        validations = [
            FieldValidation(
                deal_id=deal_id,
                field_key=r.field_key,
                om_value=r.om_value,
                market_value=r.market_value,
                status=ValidationStatus(r.status),
                explanation=r.explanation,
                sources=[
                    {"url": s.url, "title": s.title, "snippet": s.snippet}
                    for s in r.sources
                ],
                confidence=r.confidence,
            )
            for r in results
        ]

        if validations:
            validations = await self._field_validation_repo.bulk_upsert(validations)

        return validations
