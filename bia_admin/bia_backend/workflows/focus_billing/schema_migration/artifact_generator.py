"""
Schema artifact generation utilities using the shared parquet-to-clickhouse converter.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from parquet_to_clickhouse_schema_py import write_clickhouse_schema, write_pydantic_model


@dataclass(frozen=True)
class SchemaArtifacts:
    """Paths to generated schema assets."""

    ddl_path: Path
    model_path: Path


def generate_schema_artifacts(
    parquet_path: Path,
    output_dir: Path,
    *,
    table_name: str,
    primary_key: str,
    class_name: str,
) -> SchemaArtifacts:
    """
    Generate ClickHouse DDL and matching Pydantic model from a Parquet sample.

    Parameters
    ----------
    parquet_path:
        Parquet file used to infer the schema.
    output_dir:
        Directory where generated artifacts should be written.
    table_name:
        Target ClickHouse table name.
    primary_key:
        Primary key column list for the generated MergeTree DDL.
    class_name:
        Name of the Pydantic model class to produce.
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    ddl_path = output_dir / f"{table_name}.sql"
    model_path = output_dir / f"{class_name}.py"

    write_clickhouse_schema(
        parquet_path=parquet_path,
        output_path=ddl_path,
        table_name=table_name,
        primary_key=primary_key,
    )

    write_pydantic_model(
        parquet_path=parquet_path,
        output_path=model_path,
        class_name=class_name,
    )

    return SchemaArtifacts(ddl_path=ddl_path, model_path=model_path)
