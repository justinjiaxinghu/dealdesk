from uuid import uuid4
from datetime import datetime
from app.domain.entities.comp import Comp


def test_comp_defaults():
    comp = Comp(
        deal_id=uuid4(),
        address="123 Main St",
        city="Austin",
        state="TX",
        property_type="multifamily",
        source="rentcast",
        fetched_at=datetime.utcnow(),
    )
    assert comp.cap_rate is None
    assert comp.rent_per_unit is None
    assert comp.source == "rentcast"
    assert comp.id is not None


def test_comp_with_metrics():
    comp = Comp(
        deal_id=uuid4(),
        address="456 Oak Ave",
        city="Austin",
        state="TX",
        property_type="multifamily",
        cap_rate=0.062,
        price_per_unit=165000.0,
        rent_per_unit=1390.0,
        unit_count=48,
        year_built=2018,
        source="rentcast",
        fetched_at=datetime.utcnow(),
    )
    assert comp.cap_rate == 0.062
    assert comp.unit_count == 48
