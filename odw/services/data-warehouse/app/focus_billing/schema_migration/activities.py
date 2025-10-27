"""Temporal activities for schema migration."""

import hashlib
import json
import os
import tomli
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import clickhouse_connect
from temporalio import activity

from .models import SchemaDiff, MigrationResult
from .spec_parser import parse_focus_spec, map_focus_type_to_clickhouse


def _get_clickhouse_config() -> dict:
    """
    Read ClickHouse configuration from plugin_registry in bia_config database.

    Reads directly from plugin_registry.plugin_configurations table
    for the active 'ClickHouse Sink' plugin.

    Returns:
        Dictionary with ClickHouse connection parameters

    Raises:
        RuntimeError: If plugin configuration cannot be retrieved
    """
    import psycopg2

    moose_config_path = Path(__file__).resolve().parents[3] / 'moose.config.toml'
    if moose_config_path.exists():
        with open(moose_config_path, 'rb') as f:
            moose_config = tomli.load(f)
            pg_config = moose_config.get('plugin_registry_db', {})
    else:
        pg_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'bia_config',
            'user': 'temporal',
            'password': 'temporal'
        }

    try:
        conn = psycopg2.connect(
            host=pg_config.get('host', 'localhost'),
            port=pg_config.get('port', 5432),
            database=pg_config.get('database', 'bia_config'),
            user=pg_config.get('user', 'temporal'),
            password=pg_config.get('password', 'temporal')
        )

        cursor = conn.cursor()
        cursor.execute("""
            SELECT configuration
            FROM plugin_registry.plugin_configurations
            WHERE plugin_name = 'ClickHouse Sink'
            AND is_active = true
            LIMIT 1
        """)

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            raise RuntimeError(
                "ClickHouse Sink plugin not found in plugin_registry. "
                "Please configure the plugin in bia_config database."
            )

        plugin_config = row[0]
        config = {
            'host': plugin_config.get('host'),
            'port': plugin_config.get('port'),
            'database': plugin_config.get('dbName', 'default'),
            'user': plugin_config.get('user'),
            'password': plugin_config.get('password'),
        }

        if not config['host'] or not config['port']:
            raise RuntimeError(
                f"Invalid ClickHouse Sink configuration: host={config['host']}, port={config['port']}"
            )

        activity.logger.info(
            f"Loaded ClickHouse config from plugin_registry: {config['host']}:{config['port']}"
        )

        return config

    except psycopg2.Error as e:
        raise RuntimeError(f"Failed to connect to plugin_registry database: {e}") from e


@activity.defn
async def detect_schema_diff(
    source_parquet_path: str,
    canonical_schema_path: str,
    current_version: str
) -> dict:
    """
    Detect schema differences between source Parquet and canonical FOCUS spec.

    Args:
        source_parquet_path: Path to sample Parquet file
        canonical_schema_path: Path to FOCUS spec datasets directory
        current_version: Current schema version (e.g., "0_0")

    Returns:
        SchemaDiff as dictionary for Temporal serialization
    """
    activity.logger.info(
        f"Detecting schema diff: source={source_parquet_path}, "
        f"canonical={canonical_schema_path}, version={current_version}"
    )

    parquet_table = pq.read_table(source_parquet_path)
    source_schema = parquet_table.schema

    spec_path = Path(canonical_schema_path) / "cost_and_usage" / "dataset.md"
    canonical_columns = parse_focus_spec(spec_path)

    added_columns = []
    removed_columns = []
    type_changes = {}

    source_cols = {col.name: str(col.type) for col in source_schema}
    canonical_cols = {
        col['name']: map_focus_type_to_clickhouse(col['data_type'])
        for col in canonical_columns
    }

    for col_name, col_type in canonical_cols.items():
        if col_name not in source_cols:
            removed_columns.append(col_name)
        elif source_cols[col_name] != col_type:
            type_changes[col_name] = (source_cols[col_name], col_type)

    for col_name in source_cols:
        if col_name not in canonical_cols:
            added_columns.append(col_name)

    requires_migration = bool(added_columns or removed_columns or type_changes)

    major, minor = map(int, current_version.split('_'))
    new_version = f"{major}_{minor + 1}" if requires_migration else current_version

    diff = SchemaDiff(
        requires_migration=requires_migration,
        added_columns=added_columns,
        removed_columns=removed_columns,
        type_changes=type_changes,
        new_version=new_version
    )

    activity.logger.info(
        f"Schema diff detected: requires_migration={requires_migration}, "
        f"added={len(added_columns)}, removed={len(removed_columns)}, "
        f"type_changes={len(type_changes)}, new_version={new_version}"
    )

    return diff.to_dict()


@activity.defn
async def generate_transformation_code(diff_dict: dict) -> str:
    """
    Generate SQL transformation code based on schema diff.

    Args:
        diff_dict: SchemaDiff as dictionary

    Returns:
        SQL transformation code as string
    """
    diff = SchemaDiff.from_dict(diff_dict)

    activity.logger.info(f"Generating transformation code for version {diff.new_version}")

    sql_parts = []

    for col in diff.added_columns:
        sql_parts.append(f"    NULL AS {col}")

    for col_name, (old_type, new_type) in diff.type_changes.items():
        cast_expr = _generate_cast_expression(col_name, old_type, new_type)
        sql_parts.append(f"    {cast_expr} AS {col_name}")

    old_version_num = int(diff.new_version.split('_')[1]) - 1
    old_version = f"0_{old_version_num}"

    additional_columns = ",\n".join(sql_parts) if sql_parts else ""
    additional_columns_prefix = ",\n" if additional_columns else ""

    transformation_sql = f"""
CREATE MATERIALIZED VIEW FocusCostUsage_{diff.new_version}_migration_mv
ENGINE = MergeTree()
ORDER BY (billing_account_id, charge_period_start)
PARTITION BY toYYYYMM(charge_period_start)
AS
SELECT
    *{additional_columns_prefix}{additional_columns}
FROM FocusCostUsage_{old_version}
"""

    activity.logger.info(f"Generated transformation SQL ({len(transformation_sql)} bytes)")

    return transformation_sql


def _generate_cast_expression(col_name: str, old_type: str, new_type: str) -> str:
    """Generate type cast expression for schema migration."""
    if 'decimal' in new_type.lower() and 'decimal' not in old_type.lower():
        return f"CAST({col_name} AS {new_type})"
    elif 'datetime' in new_type.lower() and 'datetime' not in old_type.lower():
        return f"toDateTime64({col_name}, 3)"
    elif 'string' in new_type.lower() and 'int' in old_type.lower():
        return f"toString({col_name})"
    else:
        return f"CAST({col_name} AS {new_type})"


@activity.defn
async def apply_transformation_and_load_data(
    transform_code: str,
    new_version: str
) -> dict:
    """
    Apply schema migration by creating materialized view and validating.

    Args:
        transform_code: SQL transformation code
        new_version: New schema version (e.g., "0_1")

    Returns:
        MigrationResult as dictionary
    """
    activity.logger.info(f"Applying transformation for version {new_version}")

    start_time = datetime.utcnow()

    clickhouse_config = _get_clickhouse_config()
    activity.logger.info(
        f"Connecting to ClickHouse at {clickhouse_config['host']}:{clickhouse_config['port']}"
    )

    client = clickhouse_connect.get_client(
        host=clickhouse_config['host'],
        port=clickhouse_config['port'],
        database=clickhouse_config.get('database', 'default'),
        username=clickhouse_config.get('user'),
        password=clickhouse_config.get('password'),
    )

    try:
        old_version = f"0_{int(new_version.split('_')[1]) - 1}"

        table_exists_result = client.query(f"""
            SELECT count()
            FROM system.tables
            WHERE database = '{clickhouse_config['database']}'
            AND name = 'FocusCostUsage_{old_version}'
        """)
        table_exists = table_exists_result.first_row[0] > 0 if table_exists_result.row_count > 0 else False

        if not table_exists:
            activity.logger.warning(
                f"Base table FocusCostUsage_{old_version} does not exist. "
                f"Skipping migration - table must be created first via ingestion workflow."
            )
            return {
                "rows_migrated": 0,
                "old_version": old_version,
                "new_version": new_version,
                "status": "skipped",
                "reason": "base_table_not_found",
                "duration_seconds": 0
            }

        client.command(transform_code)
        activity.logger.info(f"Created migration materialized view for version {new_version}")

        old_count_result = client.query(f"SELECT COUNT(*) FROM FocusCostUsage_{old_version}")
        old_count = old_count_result.first_row[0] if old_count_result.row_count > 0 else 0

        new_count_result = client.query(
            f"SELECT COUNT(*) FROM FocusCostUsage_{new_version}_migration_mv"
        )
        new_count = new_count_result.first_row[0] if new_count_result.row_count > 0 else 0

        if old_count != new_count:
            raise ValueError(f"Row count mismatch: {old_count} (old) != {new_count} (new)")

        client.command(f"""
            CREATE OR REPLACE VIEW focus_data_table AS
            SELECT * FROM FocusCostUsage_{new_version}_migration_mv
        """)

        _track_schema_version(
            client=client,
            version=new_version,
            transform_code=transform_code,
            rows_migrated=new_count,
            status='success'
        )

        duration = (datetime.utcnow() - start_time).total_seconds()

        result = MigrationResult(
            rows_migrated=new_count,
            old_version=old_version,
            new_version=new_version,
            status='success',
            duration_seconds=duration
        )

        activity.logger.info(
            f"Migration complete: {new_count} rows migrated from {old_version} to {new_version} "
            f"in {duration:.2f}s"
        )

        return result.to_dict()

    except Exception as e:
        activity.logger.error(f"Migration failed: {e}")

        _track_schema_version(
            client=client,
            version=new_version,
            transform_code=transform_code,
            rows_migrated=0,
            status='failed'
        )

        raise


def _track_schema_version(
    client: Any,
    version: str,
    transform_code: str,
    rows_migrated: int,
    status: str
):
    """Track schema version migration in metadata table."""
    try:
        client.command("""
            CREATE TABLE IF NOT EXISTS focus_schema_versions (
                version String,
                applied_at DateTime64(3),
                schema_diff String,
                transformation_code_hash String,
                migration_status Enum8('pending' = 1, 'success' = 2, 'failed' = 3),
                rows_migrated UInt64
            ) ENGINE = MergeTree()
            ORDER BY applied_at
        """)

        code_hash = hashlib.sha256(transform_code.encode('utf-8')).hexdigest()

        client.insert(
            'focus_schema_versions',
            [[
                version,
                datetime.utcnow(),
                json.dumps({}),
                code_hash,
                status,
                rows_migrated
            ]],
            column_names=[
                'version',
                'applied_at',
                'schema_diff',
                'transformation_code_hash',
                'migration_status',
                'rows_migrated'
            ]
        )

    except Exception as e:
        activity.logger.warning(f"Failed to track schema version: {e}")
