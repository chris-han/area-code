from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
import pytest

from parquet_to_clickhouse_schema_py import write_clickhouse_schema, write_pydantic_model


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = (
    REPO_ROOT
    / "bia_admin"
    / "bia_backend"
    / "workflows"
    / "focus_billing"
    / "data"
    / "focus"
)


@pytest.fixture(scope="module")
def parquet_path() -> Path:
    files = sorted(DATA_ROOT.glob("**/*.parquet"))
    if not files:
        pytest.skip("No parquet data available in the expected dataset directory.")
    return files[0]


@pytest.fixture(scope="module")
def arrow_schema(parquet_path: Path):
    return pq.ParquetFile(parquet_path).schema.to_arrow_schema()


def test_write_clickhouse_schema_generates_expected_columns(tmp_path: Path, parquet_path: Path) -> None:
    output_path = tmp_path / "schema.sql"
    write_clickhouse_schema(
        parquet_path=parquet_path,
        output_path=output_path,
        table_name="focus_billing",
        primary_key="BillingAccountId",
    )

    ddl = output_path.read_text(encoding="utf-8")
    print(ddl)

    assert ddl.startswith("drop table if exists focus_billing;")
    assert ") engine = MergeTree() primary key (BillingAccountId);" in ddl
    assert "BilledCost Nullable(Decimal(38, 18))" in ddl
    assert "BillingPeriodEnd Nullable(DateTime64(9))" in ddl
    assert "x_SkuIsCreditEligible Nullable(Bool)" in ddl


def test_write_pydantic_model_matches_schema(tmp_path: Path, parquet_path: Path, arrow_schema) -> None:
    output_path = tmp_path / "model.py"
    class_name = "FocusBillingRecord"

    write_pydantic_model(
        parquet_path=parquet_path,
        output_path=output_path,
        class_name=class_name,
    )

    model_source = output_path.read_text(encoding="utf-8")
    print(model_source)

    namespace: dict[str, object] = {}
    exec(model_source, namespace)
    model_cls = namespace[class_name]

    expected_fields = [field.name for field in arrow_schema]
    model_field_names = list(model_cls.model_fields.keys())

    assert model_field_names == expected_fields
    assert "BilledCost: Optional[Decimal] = None" in model_source
    assert "BillingAccountId: Optional[str] = None" in model_source
    assert "x_SkuIsCreditEligible: Optional[bool] = None" in model_source
