"""
Pytest-compatible test for FOCUS schema migration workflow.

Run with:
    pytest app/focus_billing/tests/test_schema_migration.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from focus_billing.schema_migration.models import SchemaDiff
from focus_billing.schema_migration.spec_parser import (
    parse_focus_spec,
    map_focus_type_to_clickhouse,
    _to_snake_case
)


class TestSchemaParser:
    """Test suite for FOCUS spec parser"""

    def test_snake_case_conversion(self):
        """Test PascalCase to snake_case conversion"""
        assert _to_snake_case("BillingAccountId") == "billing_account_id"
        assert _to_snake_case("ChargePeriodStart") == "charge_period_start"
        assert _to_snake_case("SkuPriceId") == "sku_price_id"
        assert _to_snake_case("x_AccountId") == "x__account_id"

    def test_focus_type_mapping(self):
        """Test FOCUS type to ClickHouse type mapping"""
        assert map_focus_type_to_clickhouse("Decimal(38,18)") == "Decimal(38, 18)"
        assert map_focus_type_to_clickhouse("Date/Time") == "DateTime64(3)"
        assert map_focus_type_to_clickhouse("String") == "String"
        assert map_focus_type_to_clickhouse("JSON") == "String"
        assert map_focus_type_to_clickhouse("Boolean") == "UInt8"

    @pytest.mark.integration
    def test_parse_focus_spec(self):
        """Test parsing FOCUS specification file"""
        spec_path = Path("/home/chris/repo/area-code/FOCUS_Spec/specification/datasets/cost_and_usage/dataset.md")

        if not spec_path.exists():
            pytest.skip("FOCUS spec not found")

        columns = parse_focus_spec(spec_path)

        assert len(columns) > 0, "Should parse columns from spec"
        assert any(col['name'] == 'billing_account_id' for col in columns)
        assert any(col['name'] == 'billed_cost' for col in columns)


class TestSchemaDiff:
    """Test suite for SchemaDiff model"""

    def test_schema_diff_creation(self):
        """Test creating SchemaDiff object"""
        diff = SchemaDiff(
            requires_migration=True,
            added_columns=['new_col_1', 'new_col_2'],
            removed_columns=['old_col'],
            type_changes={'amount': ('Int64', 'Decimal(38,18)')},
            new_version='0_1'
        )

        assert diff.requires_migration is True
        assert len(diff.added_columns) == 2
        assert len(diff.removed_columns) == 1
        assert len(diff.type_changes) == 1
        assert diff.new_version == '0_1'

    def test_schema_diff_serialization(self):
        """Test SchemaDiff to/from dict conversion"""
        diff = SchemaDiff(
            requires_migration=False,
            added_columns=[],
            removed_columns=[],
            type_changes={},
            new_version='0_0'
        )

        diff_dict = diff.to_dict()
        assert diff_dict['requires_migration'] is False
        assert diff_dict['new_version'] == '0_0'

        restored_diff = SchemaDiff.from_dict(diff_dict)
        assert restored_diff.requires_migration == diff.requires_migration
        assert restored_diff.new_version == diff.new_version


class TestSchemaMigrationIntegration:
    """Integration tests for schema migration workflow"""

    @pytest.fixture
    def sample_parquet_path(self):
        """Return path to sample parquet file"""
        return "/home/chris/repo/area-code/bia_admin/bia_backend/workflows/focus_billing/data/focus/20250701-20250731/202507161527/cc47e41e-a6ab-462e-9b26-fe7237024648/part_0_0001.snappy.parquet"

    @pytest.fixture
    def canonical_schema_path(self):
        """Return path to canonical FOCUS spec"""
        return "/home/chris/repo/area-code/FOCUS_Spec/specification/datasets"

    @pytest.mark.integration
    def test_detect_no_drift(self, sample_parquet_path, canonical_schema_path):
        """Test schema drift detection when no drift exists"""
        import asyncio
        from focus_billing.schema_migration.activities import detect_schema_diff

        if not Path(sample_parquet_path).exists():
            pytest.skip("Sample parquet file not found")

        if not Path(canonical_schema_path).exists():
            pytest.skip("FOCUS spec not found")

        diff_dict = asyncio.run(
            detect_schema_diff(sample_parquet_path, canonical_schema_path, "0_0")
        )

        assert 'requires_migration' in diff_dict
        assert 'new_version' in diff_dict


class TestVersionIncrement:
    """Test version increment logic"""

    def test_version_increment_minor(self):
        """Test minor version increment"""
        current = "0_0"
        major, minor = map(int, current.split('_'))
        new_version = f"{major}_{minor + 1}"

        assert new_version == "0_1"

    def test_version_increment_multiple(self):
        """Test multiple version increments"""
        current = "0_5"
        major, minor = map(int, current.split('_'))
        new_version = f"{major}_{minor + 1}"

        assert new_version == "0_6"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
