from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from focus_billing.schema_migration.activities import dynamic_dispatch


class DummyClickHouseClient:
    def __init__(self, executed: List[str]):
        self._executed = executed

    def command(self, sql: str):
        self._executed.append(sql)

    def close(self):
        return None


def test_dynamic_dispatch_executes_generated_sql(monkeypatch):
    executed: List[str] = []

    def fake_get_client(**kwargs):
        return DummyClickHouseClient(executed)

    import clickhouse_connect

    monkeypatch.setattr(clickhouse_connect, "get_client", fake_get_client)

    sql_fixture = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "schema_migration"
        / "generated"
        / "focus_cost_usage.sql"
    )

    if not sql_fixture.exists():
        pytest.skip("Generated schema artifacts are not present.")

    result = asyncio.run(
        dynamic_dispatch("execute_clickhouse_schema", {"sql_path": str(sql_fixture)})
    )

    assert result["executed_statements"] >= 2
    assert any(
        stmt.upper().startswith("CREATE TABLE FOCUS_COST_USAGE") for stmt in executed
    )
