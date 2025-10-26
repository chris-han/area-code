"""Parser for FOCUS specification files."""

import re
from pathlib import Path
from typing import Dict, List


def parse_focus_spec(spec_path: Path) -> List[Dict]:
    """
    Parse FOCUS dataset specification markdown file.

    Args:
        spec_path: Path to dataset.md specification file

    Returns:
        List of column definitions with name, data_type, feature_level, etc.
    """
    if not spec_path.exists():
        raise FileNotFoundError(f"FOCUS spec not found: {spec_path}")

    with open(spec_path, 'r', encoding='utf-8') as f:
        content = f.read()

    columns = []

    table_pattern = r'\|\s*\[([^\]]+)\]'
    lines = content.split('\n')

    in_columns_table = False
    for line in lines:
        if '| Column' in line and '| Column Type' in line:
            in_columns_table = True
            continue

        if in_columns_table:
            if line.startswith('|') and '---' not in line and '[' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 6:
                    col_match = re.search(r'\[([^\]]+)\]', parts[1])
                    if col_match:
                        col_name = col_match.group(1)
                        col_type = parts[2]
                        feature_level = parts[3]
                        allows_nulls = parts[4].lower() == 'true'
                        data_type = parts[5]

                        columns.append({
                            'name': _to_snake_case(col_name),
                            'original_name': col_name,
                            'column_type': col_type,
                            'data_type': data_type,
                            'feature_level': feature_level,
                            'allows_nulls': allows_nulls,
                        })
            elif not line.strip().startswith('|'):
                in_columns_table = False

    return columns


def _to_snake_case(name: str) -> str:
    """Convert PascalCase/Title Case to snake_case."""
    name = name.replace(' ', '')
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def map_focus_type_to_clickhouse(focus_type: str) -> str:
    """
    Map FOCUS data type to ClickHouse data type.

    Args:
        focus_type: FOCUS spec data type (e.g., "Decimal(38,18)", "String", "Date/Time")

    Returns:
        ClickHouse data type string
    """
    focus_type_lower = focus_type.lower()

    if 'decimal' in focus_type_lower:
        return 'Decimal(38, 18)'
    elif 'date/time' in focus_type_lower or 'datetime' in focus_type_lower:
        return 'DateTime64(3)'
    elif 'date' in focus_type_lower:
        return 'Date'
    elif 'string' in focus_type_lower:
        return 'String'
    elif 'json' in focus_type_lower:
        return 'String'
    elif 'boolean' in focus_type_lower:
        return 'UInt8'
    else:
        return 'String'
