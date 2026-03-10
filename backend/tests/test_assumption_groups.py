from app.domain.entities.assumption import Assumption
from app.domain.value_objects.enums import AssumptionGroup, ForecastMethod, SourceType
from uuid import uuid4


def test_assumption_has_group_field():
    a = Assumption(
        set_id=uuid4(),
        key="purchase_price",
        value_number=1_000_000,
        group=AssumptionGroup.TRANSACTION,
    )
    assert a.group == AssumptionGroup.TRANSACTION


def test_assumption_group_defaults_to_none():
    a = Assumption(set_id=uuid4(), key="some_key")
    assert a.group is None


def test_assumption_has_forecast_fields():
    a = Assumption(
        set_id=uuid4(),
        key="occupancy_rate",
        value_number=0.95,
        group=AssumptionGroup.OPERATING,
        forecast_method=ForecastMethod.GRADUAL_RAMP,
        forecast_params={"target_value": 0.97},
    )
    assert a.forecast_method == ForecastMethod.GRADUAL_RAMP
    assert a.forecast_params == {"target_value": 0.97}
