"""
Naming Utilities

Functions for converting between naming conventions and generating IDs.
"""

import hashlib
import re
from typing import Any, Dict


def snake_to_pascal_case(snake_str: str) -> str:
    """
    Convert snake_case string to PascalCase

    Args:
        snake_str: String in snake_case format

    Returns:
        String in PascalCase format

    Examples:
        >>> snake_to_pascal_case('billing_account_id')
        'BillingAccountId'
        >>> snake_to_pascal_case('usage_date')
        'UsageDate'
    """
    components = snake_str.split("_")
    return "".join(word.capitalize() for word in components)


def to_snake_case(pascal_str: str) -> str:
    """
    Convert PascalCase string to snake_case (alias for pascal_to_snake_case)

    Args:
        pascal_str: String in PascalCase format

    Returns:
        String in snake_case format
    """
    return pascal_to_snake_case(pascal_str)


def pascal_to_snake_case(pascal_str: str) -> str:
    """
    Convert PascalCase string to snake_case

    Args:
        pascal_str: String in PascalCase format

    Returns:
        String in snake_case format

    Examples:
        >>> pascal_to_snake_case('BillingAccountId')
        'billing_account_id'
        >>> pascal_to_snake_case('UsageDate')
        'usage_date'
    """
    # Insert underscore before uppercase letters (except first)
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", pascal_str)
    # Insert underscore before uppercase letters preceded by lowercase
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def generate_deterministic_id(*args: Any) -> str:
    """
    Generate a deterministic ID from input arguments

    Args:
        *args: Arguments to use for ID generation

    Returns:
        Deterministic hash string

    Examples:
        >>> generate_deterministic_id('account123', '2024-01-01', 'resource456')
        'a1b2c3d4e5f6...'
    """
    # Convert all arguments to strings and concatenate
    combined = "|".join(str(arg) for arg in args if arg is not None)

    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(combined.encode("utf-8"))
    return hash_obj.hexdigest()


def normalize_column_name(column_name: str) -> str:
    """
    Normalize column name to snake_case format

    Args:
        column_name: Column name in any format

    Returns:
        Normalized column name in snake_case
    """
    # If already snake_case, return as-is
    if "_" in column_name and column_name.islower():
        return column_name

    # If PascalCase, convert to snake_case
    return pascal_to_snake_case(column_name)


def create_column_mapping(focus_columns: Dict[str, Any]) -> Dict[str, str]:
    """
    Create mapping between PascalCase and snake_case column names

    Args:
        focus_columns: Dictionary of FOCUS column definitions

    Returns:
        Dictionary mapping PascalCase to snake_case names
    """
    mapping = {}
    for pascal_name in focus_columns.keys():
        snake_name = pascal_to_snake_case(pascal_name)
        mapping[pascal_name] = snake_name

    return mapping


def validate_column_name(column_name: str) -> bool:
    """
    Validate that a column name follows proper naming conventions

    Args:
        column_name: Column name to validate

    Returns:
        True if valid, False otherwise
    """
    # Check for valid characters (letters, numbers, underscores)
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", column_name):
        return False

    # Check that it doesn't start or end with underscore
    if column_name.startswith("_") or column_name.endswith("_"):
        return False

    # Check for consecutive underscores
    if "__" in column_name:
        return False

    return True
