from __future__ import annotations

import logging
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

logger = logging.getLogger(__name__)


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

    async def validate_fields(
        self, deal_id: UUID, *, phase: str | None = None
    ) -> list[FieldValidation]:
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

        # For deep phase, load existing quick-phase validations as context
        prior_quick_results: list[dict] | None = None
        existing_search_steps: list[dict] = []
        if phase == "deep":
            existing = await self._field_validation_repo.get_by_deal_id(deal_id)
            if existing:
                prior_quick_results = [
                    {
                        "field_key": v.field_key,
                        "om_value": v.om_value,
                        "market_value": v.market_value,
                        "status": v.status.value,
                        "explanation": v.explanation,
                        "sources": v.sources,
                        "confidence": v.confidence,
                    }
                    for v in existing
                ]
                existing_search_steps = existing[0].search_steps if existing else []

        # Call LLM for validation
        results = await self._llm_provider.validate_om_fields(
            deal,
            numeric_fields,
            benchmarks,
            phase=phase,
            prior_quick_results=prior_quick_results,
        )

        logger.info(
            "LLM validate_om_fields(phase=%s) returned %d results",
            phase, len(results),
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
                search_steps=(
                    existing_search_steps + r.search_steps
                    if phase == "deep" and existing_search_steps
                    else r.search_steps
                ),
            )
            for r in results
        ]

        if validations:
            validations = await self._field_validation_repo.bulk_upsert(validations)
        elif phase == "deep":
            # Deep phase returned nothing — return existing quick-phase results
            logger.warning("Deep phase returned 0 results; keeping existing validations")
            validations = await self._field_validation_repo.get_by_deal_id(deal_id)

        return validations
