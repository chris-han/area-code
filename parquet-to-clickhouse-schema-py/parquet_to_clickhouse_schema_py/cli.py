"""Command line interface for the Parquet → ClickHouse schema generator."""

from __future__ import annotations

import argparse
from pathlib import Path

from .converter import write_clickhouse_schema, write_pydantic_model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a ClickHouse table schema based on a Parquet file.",
    )
    parser.add_argument(
        "--parquet-path",
        required=True,
        help="Absolute or relative path to the source Parquet file.",
    )
    parser.add_argument(
        "--clickhouse-schema-path",
        required=True,
        help="Destination file for the generated ClickHouse DDL.",
    )
    parser.add_argument(
        "--table-name",
        required=True,
        help="Name of the ClickHouse table to create.",
    )
    parser.add_argument(
        "--primary-key",
        required=True,
        help="Primary key column list for the MergeTree engine.",
    )
    parser.add_argument(
        "--pydantic-model-path",
        help="Optional path to write a matching Pydantic model definition.",
    )
    parser.add_argument(
        "--pydantic-class-name",
        default="ParquetRecord",
        help="Name of the generated Pydantic model class (default: %(default)s).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    write_clickhouse_schema(
        Path(args.parquet_path),
        Path(args.clickhouse_schema_path),
        args.table_name,
        args.primary_key,
    )

    if args.pydantic_model_path:
        write_pydantic_model(
            Path(args.parquet_path),
            Path(args.pydantic_model_path),
            args.pydantic_class_name,
        )


if __name__ == "__main__":
    main()
