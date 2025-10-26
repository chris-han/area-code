import pytest

from app.views.daily_pageviews import daily_pageviews_mv, daily_pageviews_table
from moose_lib.blocks import AggregatingMergeTreeEngine
from moose_lib.blocks import ClickHouseEngines


pytestmark = pytest.mark.unit


def test_daily_pageviews_uses_engine_config():
    engine = daily_pageviews_table.config.engine
    assert isinstance(engine, AggregatingMergeTreeEngine)
    assert not isinstance(engine, ClickHouseEngines)


def test_daily_pageviews_materialized_view_target_table():
    assert daily_pageviews_mv.target_table is daily_pageviews_table
    assert daily_pageviews_mv.target_table.config.order_by_fields == ["view_date"]
