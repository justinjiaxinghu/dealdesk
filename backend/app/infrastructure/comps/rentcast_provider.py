# backend/app/infrastructure/comps/rentcast_provider.py
"""Rentcast API provider for comparable property data."""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from app.domain.entities.comp import Comp
from app.domain.entities.deal import Deal
from app.domain.entities.extraction import ExtractedField
from app.domain.interfaces.providers import CompsProvider
from app.domain.value_objects.enums import CompSource, PropertyType

logger = logging.getLogger(__name__)

RENTCAST_BASE = "https://api.rentcast.io/v1"

# Only map property types that exist in the PropertyType enum.
# Rentcast types that have no canonical equivalent fall back to deal.property_type.
_PROPERTY_TYPE_MAP: dict[str, PropertyType] = {
    "Multi-Family": PropertyType.MULTIFAMILY,
    "Office": PropertyType.OFFICE,
    "Retail": PropertyType.RETAIL,
    "Industrial": PropertyType.INDUSTRIAL,
}

_CANONICAL_TO_RENTCAST: dict[PropertyType, str] = {
    PropertyType.MULTIFAMILY: "Multi-Family",
    PropertyType.OFFICE: "Office",
    PropertyType.RETAIL: "Retail",
    PropertyType.INDUSTRIAL: "Industrial",
}


class RentcastCompsProvider(CompsProvider):
    def __init__(self, api_key: str, radius_miles: float = 2.0, limit: int = 10) -> None:
        self._api_key = api_key
        self._radius_miles = radius_miles
        self._limit = limit

    async def search_comps(
        self,
        deal: Deal,
        extracted_fields: list[ExtractedField],
    ) -> list[Comp]:
        if not deal.latitude or not deal.longitude:
            logger.warning("Deal %s has no lat/lng — skipping Rentcast search", deal.id)
            return []

        if not self._api_key:
            logger.warning("DEALDESK_RENTCAST_API_KEY not set — skipping Rentcast search")
            return []

        rentcast_type = _CANONICAL_TO_RENTCAST.get(deal.property_type, "Multi-Family")
        params = {
            "latitude": deal.latitude,
            "longitude": deal.longitude,
            "radius": self._radius_miles,
            "propertyType": rentcast_type,
            "limit": self._limit,
        }
        headers = {"X-Api-Key": self._api_key, "Accept": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{RENTCAST_BASE}/properties",
                    params=params,
                    headers=headers,
                )
                if response.status_code != 200:
                    logger.warning(
                        "Rentcast returned %d: %s", response.status_code, response.text[:200]
                    )
                    return []

                data = response.json()
        except Exception as exc:
            logger.warning("Rentcast request failed: %s", exc)
            return []

        properties = data.get("properties", [])
        fetched_at = datetime.utcnow()
        comps: list[Comp] = []

        for prop in properties:
            address_line = (
                prop.get("addressLine1")
                or prop.get("formattedAddress", "").split(",")[0].strip()
            )
            if not address_line:
                continue

            unit_count = prop.get("units") or prop.get("unitCount")
            sale_price = prop.get("lastSalePrice")
            price_per_unit = None
            if sale_price and unit_count and unit_count > 0:
                price_per_unit = sale_price / unit_count

            sq_ft = prop.get("squareFootage")
            price_per_sqft = None
            if sale_price and sq_ft and sq_ft > 0:
                price_per_sqft = sale_price / sq_ft

            raw_type = prop.get("propertyType", "")
            property_type = _PROPERTY_TYPE_MAP.get(raw_type, deal.property_type)

            comps.append(
                Comp(
                    deal_id=deal.id,
                    address=address_line,
                    city=prop.get("city", deal.city),
                    state=prop.get("state", deal.state),
                    property_type=property_type,
                    source=CompSource.RENTCAST,
                    source_url=f"https://rentcast.io/property/{prop.get('id', '')}",
                    year_built=prop.get("yearBuilt"),
                    unit_count=unit_count,
                    square_feet=sq_ft,
                    sale_price=sale_price,
                    price_per_unit=price_per_unit,
                    price_per_sqft=price_per_sqft,
                    cap_rate=prop.get("capRate"),
                    rent_per_unit=prop.get("rentEstimate"),
                    occupancy_rate=prop.get("occupancyRate"),
                    fetched_at=fetched_at,
                )
            )

        logger.info("Rentcast returned %d comps for deal %s", len(comps), deal.id)
        return comps
