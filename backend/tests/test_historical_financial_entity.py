from datetime import datetime
from uuid import uuid4
from app.domain.entities.historical_financial import HistoricalFinancial
from app.domain.value_objects.enums import HistoricalFinancialSource


def test_historical_financial_entity():
    hf = HistoricalFinancial(
        deal_id=uuid4(),
        period_label="T12",
        metric_key="noi",
        value=1_400_000.0,
        unit="$",
        source=HistoricalFinancialSource.EXTRACTED,
    )
    assert hf.period_label == "T12"
    assert hf.metric_key == "noi"
    assert hf.value == 1_400_000.0
    assert hf.id is not None
    assert hf.created_at is not None
