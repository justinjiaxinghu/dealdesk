from uuid import uuid4, UUID
from datetime import datetime
from app.domain.entities.comp import Comp
from app.domain.value_objects.enums import CompSource, PropertyType


def test_comp_defaults():
    comp = Comp(
        deal_id=uuid4(),
        address="123 Main St",
        city="Austin",
        state="TX",
        property_type=PropertyType.MULTIFAMILY,
        source=CompSource.RENTCAST,
        fetched_at=datetime.utcnow(),
    )
    assert comp.cap_rate is None
    assert comp.rent_per_unit is None
    assert comp.source == CompSource.RENTCAST
    assert isinstance(comp.id, UUID)
    assert isinstance(comp.created_at, datetime)


def test_comp_with_metrics():
    comp = Comp(
        deal_id=uuid4(),
        address="456 Oak Ave",
        city="Austin",
        state="TX",
        property_type=PropertyType.MULTIFAMILY,
        cap_rate=0.062,
        price_per_unit=165000.0,
        rent_per_unit=1390.0,
        unit_count=48,
        year_built=2018,
        source=CompSource.RENTCAST,
        fetched_at=datetime.utcnow(),
    )
    assert comp.cap_rate == 0.062
    assert comp.unit_count == 48


def test_comp_unique_ids():
    kwargs = dict(
        deal_id=uuid4(),
        address="789 Pine",
        city="Austin",
        state="TX",
        property_type=PropertyType.MULTIFAMILY,
        source=CompSource.TAVILY,
        fetched_at=datetime.utcnow(),
    )
    comp1 = Comp(**kwargs)
    comp2 = Comp(**kwargs)
    assert comp1.id != comp2.id


def test_comp_required_fields():
    import pytest
    with pytest.raises(TypeError):
        Comp()  # missing required fields


from app.domain.interfaces.repositories import CompRepository
from app.domain.interfaces.providers import CompsProvider


def test_comp_repository_is_abstract():
    import inspect
    assert inspect.isabstract(CompRepository)


def test_comps_provider_is_abstract():
    import inspect
    assert inspect.isabstract(CompsProvider)


def test_comp_mapper_roundtrip():
    from datetime import datetime
    from app.infrastructure.persistence.mappers import comp_to_model, comp_to_entity
    from app.domain.value_objects.enums import CompSource, PropertyType
    from uuid import uuid4

    comp = Comp(
        deal_id=uuid4(),
        address="123 Main St",
        city="Austin",
        state="TX",
        property_type=PropertyType.MULTIFAMILY,
        source=CompSource.RENTCAST,
        cap_rate=0.062,
        fetched_at=datetime.utcnow(),
    )
    model = comp_to_model(comp)
    restored = comp_to_entity(model)
    assert restored.address == comp.address
    assert restored.cap_rate == comp.cap_rate
    assert restored.source == CompSource.RENTCAST
    assert restored.property_type == PropertyType.MULTIFAMILY
