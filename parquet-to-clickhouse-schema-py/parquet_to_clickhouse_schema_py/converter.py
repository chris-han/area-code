"""
Utilities for generating ClickHouse DDL statements and matching Pydantic models
from Parquet schemas.

The implementation relies exclusively on PyArrow for schema inspection. The
public entry points are :func:`write_clickhouse_schema` and
:func:`write_pydantic_model`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.types as patypes


INDENT_WIDTH = 4


@dataclass(frozen=True)
class GeneratorConfig:
    """Configuration for schema generation."""

    indent: int = INDENT_WIDTH


def write_clickhouse_schema(
    parquet_path: str | Path,
    output_path: str | Path,
    table_name: str,
    primary_key: str,
    *,
    config: GeneratorConfig | None = None,
) -> None:
    """
    Generate a ClickHouse table definition for the provided Parquet file.

    Parameters
    ----------
    parquet_path:
        Path to the Parquet file whose schema should be inspected.
    output_path:
        Destination file that will receive the ClickHouse DDL.
    table_name:
        Name of the ClickHouse table to be created.
    primary_key:
        Primary key column (or comma separated list) for the MergeTree engine.
    config:
        Optional :class:`GeneratorConfig` to tweak indentation.
    """

    config = config or GeneratorConfig()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema = _load_arrow_schema(Path(parquet_path))
    ddl = _render_schema(schema, table_name, primary_key, config)
    output_path.write_text(ddl, encoding="utf-8")


def _load_arrow_schema(parquet_path: Path) -> pa.Schema:
    """
    Load the Parquet schema as a PyArrow schema.

    PyArrow exposes full logical type information that maps cleanly to
    ClickHouse via Arrow interoperability.
    """

    parquet_file = pq.ParquetFile(str(parquet_path))
    return parquet_file.schema.to_arrow_schema()


def _render_schema(
    schema: pa.Schema,
    table_name: str,
    primary_key: str,
    config: GeneratorConfig,
) -> str:
    lines: List[str] = [
        f"drop table if exists {table_name};",
        f"create table {table_name} (",
    ]

    for idx, field in enumerate(schema):
        prefix = " " * config.indent
        if idx > 0:
            prefix += ", "
        lines.extend(_render_field(field, config.indent, prefix, config))

    lines.append(f") engine = MergeTree() primary key ({primary_key});")
    lines.append("")  # Ensure trailing newline for parity with original tool.
    return "\n".join(lines)


def _render_field(
    field: pa.Field,
    indent: int,
    prefix: str,
    config: GeneratorConfig,
) -> List[str]:
    pa_type = field.type

    if patypes.is_struct(pa_type):
        return _render_struct(field, indent, prefix, config)
    if patypes.is_list(pa_type) or patypes.is_large_list(pa_type):
        return _render_list(field, indent, prefix, config)
    if patypes.is_map(pa_type):
        return _render_map(field, indent, prefix, config)

    type_repr = _clickhouse_primitive_type(pa_type)
    if field.nullable:
        type_repr = f"Nullable({type_repr})"

    return [f"{prefix}{field.name} {type_repr}"]


def _render_struct(
    field: pa.Field,
    indent: int,
    prefix: str,
    config: GeneratorConfig,
) -> List[str]:
    lines = [f"{prefix}{field.name} Tuple("]
    child_indent = indent + config.indent
    lines.extend(
        _render_children(field.type, child_indent, config),
    )
    lines.append(f"{' ' * indent})")
    return lines


def _render_list(
    field: pa.Field,
    indent: int,
    prefix: str,
    config: GeneratorConfig,
) -> List[str]:
    list_type = field.type
    lines = [f"{prefix}{field.name} Nested ("]
    child_indent = indent + config.indent

    value_field = list_type.value_field
    # The value field can be unnamed; reuse the parent field name in that case.
    nested_name = value_field.name or field.name
    nested_field = pa.field(
        nested_name,
        value_field.type,
        nullable=value_field.nullable,
        metadata=value_field.metadata,
    )

    if patypes.is_struct(nested_field.type):
        lines.extend(_render_children(nested_field.type, child_indent, config))
    else:
        child_prefix = " " * child_indent
        lines.extend(_render_field(nested_field, child_indent, child_prefix, config))

    lines.append(f"{' ' * indent})")
    return lines


def _render_map(
    field: pa.Field,
    indent: int,
    prefix: str,
    config: GeneratorConfig,
) -> List[str]:
    map_type = field.type
    lines = [f"{prefix}{field.name} Map ("]
    child_indent = indent + config.indent

    key_field = pa.field("key", map_type.key_type, nullable=False)
    item_field = pa.field("value", map_type.item_type, nullable=map_type.value_field.nullable)

    lines.extend(
        _render_field(key_field, child_indent, " " * child_indent, config)
    )
    value_prefix = " " * child_indent + ", "
    lines.extend(_render_field(item_field, child_indent, value_prefix, config))

    lines.append(f"{' ' * indent})")
    return lines


def _render_children(
    struct_type: pa.StructType,
    indent: int,
    config: GeneratorConfig,
) -> List[str]:
    child_lines: List[str] = []
    for idx, child in enumerate(struct_type):
        child_prefix = " " * indent
        if idx > 0:
            child_prefix += ", "
        child_lines.extend(_render_field(child, indent, child_prefix, config))
    return child_lines


def _clickhouse_primitive_type(pa_type: pa.DataType) -> str:
    if patypes.is_boolean(pa_type):
        return "Bool"
    if patypes.is_int8(pa_type):
        return "Int8"
    if patypes.is_int16(pa_type):
        return "Int16"
    if patypes.is_int32(pa_type):
        return "Int32"
    if patypes.is_int64(pa_type):
        return "Int64"
    if patypes.is_uint8(pa_type):
        return "UInt8"
    if patypes.is_uint16(pa_type):
        return "UInt16"
    if patypes.is_uint32(pa_type):
        return "UInt32"
    if patypes.is_uint64(pa_type):
        return "UInt64"
    if patypes.is_float16(pa_type):
        return "Float32"
    if patypes.is_float32(pa_type):
        return "Float32"
    if patypes.is_float64(pa_type):
        return "Float64"
    if patypes.is_decimal(pa_type):
        return f"Decimal({pa_type.precision}, {pa_type.scale})"
    if patypes.is_timestamp(pa_type):
        unit_scale = {"s": 0, "ms": 3, "us": 6, "ns": 9}
        precision = unit_scale.get(pa_type.unit, 0)
        if precision == 0:
            return "DateTime"
        return f"DateTime64({precision})"
    if patypes.is_date32(pa_type):
        return "Date32"
    if patypes.is_date64(pa_type):
        return "DateTime"
    if patypes.is_time(pa_type):
        return "DateTime64(6)"
    if patypes.is_binary(pa_type) or patypes.is_string(pa_type) or patypes.is_large_binary(pa_type) or patypes.is_large_string(pa_type):
        return "String"
    if patypes.is_duration(pa_type):
        return "Interval"

    raise TypeError(f"Unsupported Parquet type: {pa_type}")


def write_pydantic_model(
    parquet_path: str | Path,
    output_path: str | Path,
    class_name: str,
    *,
    config: GeneratorConfig | None = None,
) -> None:
    """
    Generate a Pydantic model definition that matches the inferred schema.

    Parameters
    ----------
    parquet_path:
        Path to the Parquet file whose schema should be inspected.
    output_path:
        Destination file that will receive the Pydantic model definition.
    class_name:
        Name of the model class to generate.
    config:
        Optional :class:`GeneratorConfig` to tweak indentation.
    """

    config = config or GeneratorConfig()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema = _load_arrow_schema(Path(parquet_path))
    model_source = _render_pydantic_model(schema, class_name, config)
    output_path.write_text(model_source, encoding="utf-8")


def _render_pydantic_model(
    schema: pa.Schema,
    class_name: str,
    config: GeneratorConfig,
) -> str:
    typing_imports: set[str] = set()
    datetime_imports: set[str] = set()
    decimal_required = False

    fields: List[str] = []
    for field in schema:
        field_type, import_info = _python_type_for_field(field)
        typing_imports.update(import_info.get("typing", set()))
        datetime_imports.update(import_info.get("datetime", set()))
        if import_info.get("decimal"):
            decimal_required = True

        default = " = None" if field.nullable else ""
        indent = " " * config.indent
        fields.append(f"{indent}{field.name}: {field_type}{default}")

    import_lines: List[str] = []
    if decimal_required:
        import_lines.append("from decimal import Decimal")
    if datetime_imports:
        imports = ", ".join(sorted(datetime_imports))
        import_lines.append(f"from datetime import {imports}")
    if typing_imports:
        imports = ", ".join(sorted(typing_imports))
        import_lines.append(f"from typing import {imports}")
    import_lines.append("from pydantic import BaseModel")

    if not fields:
        fields = [" " * config.indent + "pass"]

    lines = import_lines + ["", f"class {class_name}(BaseModel):"] + fields + ["", ""]
    return "\n".join(lines)


def _python_type_for_field(field: pa.Field) -> tuple[str, dict[str, set[str]]]:
    pa_type = field.type
    imports: dict[str, set[str]] = {"typing": set(), "datetime": set(), "decimal": set()}

    base_type = _base_python_type(pa_type, imports)
    if field.nullable:
        imports["typing"].add("Optional")
        type_repr = f"Optional[{base_type}]"
    else:
        type_repr = base_type

    return type_repr, imports


def _base_python_type(pa_type: pa.DataType, imports: dict[str, set[str]]) -> str:
    if patypes.is_boolean(pa_type):
        return "bool"
    if patypes.is_int8(pa_type) or patypes.is_int16(pa_type) or patypes.is_int32(pa_type) or patypes.is_int64(pa_type):
        return "int"
    if patypes.is_uint8(pa_type) or patypes.is_uint16(pa_type) or patypes.is_uint32(pa_type) or patypes.is_uint64(pa_type):
        return "int"
    if patypes.is_float16(pa_type) or patypes.is_float32(pa_type) or patypes.is_float64(pa_type):
        return "float"
    if patypes.is_decimal(pa_type):
        imports["decimal"].add("Decimal")
        return "Decimal"
    if patypes.is_timestamp(pa_type) or patypes.is_date64(pa_type):
        imports["datetime"].add("datetime")
        return "datetime"
    if patypes.is_date32(pa_type):
        imports["datetime"].add("date")
        return "date"
    if patypes.is_time(pa_type):
        imports["datetime"].add("time")
        return "time"
    if patypes.is_duration(pa_type):
        imports["datetime"].add("timedelta")
        return "timedelta"
    if patypes.is_string(pa_type) or patypes.is_large_string(pa_type):
        return "str"
    if patypes.is_binary(pa_type) or patypes.is_large_binary(pa_type):
        return "bytes"

    raise NotImplementedError(f"Pydantic model generation does not support type: {pa_type}")


__all__ = [
    "GeneratorConfig",
    "write_clickhouse_schema",
    "write_pydantic_model",
]
