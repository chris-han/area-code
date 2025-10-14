#!/usr/bin/env python3
"""
Pytest tests for actual Azure billing functions

These tests use the actual functions extracted from the Azure billing implementation
without requiring all the complex dependencies.
"""

import pytest
import sys
import os
from typing import List

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def get_columns_from_create_query(query: str) -> List[str]:
    """
    Extracted function from api_2_ck_stg_azure_billing_detail_daily_delta.py
    Parses column names from a CREATE TABLE query string.
    """
    # Isolate query part before ENGINE clause
    try:
        engine_pos = query.upper().index('ENGINE')
        query_before_engine = query[:engine_pos]
    except ValueError:
        query_before_engine = query

    # Find column definitions within parentheses
    start_pos = query_before_engine.find('(')
    end_pos = query_before_engine.rfind(')')

    if start_pos == -1 or end_pos == -1 or start_pos >= end_pos:
        return []

    columns_str = query_before_engine[start_pos + 1:end_pos]
    
    columns = []
    for line in columns_str.split(','):
        line = line.strip()
        if line and not line.startswith('--'):
            columns.append(line.split()[0].replace('`', ''))
    return columns


def clean_json_string(s) -> dict:
    """
    Extracted function from api_2_ck_stg_azure_billing_detail_daily_delta.py
    Cleans and converts a string to a JSON object (Python dictionary).
    Returns None if the input is null-like, or the string is empty or '{}'.
    """
    import json
    import math
    from typing import Any, Dict
    
    # If input is None or NaN, return None
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return [None]
    
    if isinstance(s, str):
        s = s.strip()
        # If string is empty or represents an empty JSON object, return None
        if s == '':
            return [None]
        elif s == '{}':
            return [None]
        elif s == '[]':
            return [None]
        try:
            parsed_json = json.loads(s)
            return parsed_json

        except json.JSONDecodeError:
            # If not valid JSON, raise the error as per requirement
            raise ValueError(f"Invalid JSON string: '{s}'")
    # For other types like numbers, bools, etc., raise an error
    raise TypeError(f"Unsupported type for JSON cleaning: {type(s)}")


class TestAzureBillingActualFunctions:
    """Test actual Azure billing functions"""
    
    def test_get_columns_from_create_query_basic(self):
        """Test basic CREATE TABLE query parsing"""
        sample_query = '''
        CREATE TABLE IF NOT EXISTS dbo.test_table
        (
            id UInt64,
            name String,
            value Nullable(Float64),
            created_at DateTime DEFAULT now()
        )
        ENGINE = MergeTree()
        ORDER BY id
        '''
        expected_columns = ['id', 'name', 'value', 'created_at']
        result = get_columns_from_create_query(sample_query)
        assert result == expected_columns, f"Expected {expected_columns}, got {result}"
    
    def test_get_columns_from_create_query_with_backticks(self):
        """Test CREATE TABLE query with backticks"""
        sample_query = '''
        CREATE TABLE test_table
        (
            `id` UInt64,
            `user_name` String,
            `email` Nullable(String)
        )
        ENGINE = MergeTree()
        '''
        expected_columns = ['id', 'user_name', 'email']
        result = get_columns_from_create_query(sample_query)
        assert result == expected_columns
    
    def test_get_columns_from_create_query_no_engine(self):
        """Test CREATE TABLE query without ENGINE clause"""
        sample_query = '''
        CREATE TABLE test_table
        (
            id UInt64,
            name String
        )
        '''
        expected_columns = ['id', 'name']
        result = get_columns_from_create_query(sample_query)
        assert result == expected_columns
    
    def test_get_columns_from_create_query_empty(self):
        """Test empty or malformed query"""
        assert get_columns_from_create_query("") == []
        assert get_columns_from_create_query("CREATE TABLE test") == []
        assert get_columns_from_create_query("invalid query") == []
    
    def test_clean_json_string_valid(self):
        """Test clean_json_string with valid JSON"""
        valid_json = '{"app": "web-service", "env": "prod"}'
        result = clean_json_string(valid_json)
        assert isinstance(result, dict)
        assert result['app'] == 'web-service'
        assert result['env'] == 'prod'
    
    def test_clean_json_string_empty_cases(self):
        """Test clean_json_string with empty/null cases"""
        assert clean_json_string(None) == [None]
        assert clean_json_string('') == [None]
        assert clean_json_string('{}') == [None]
        assert clean_json_string('[]') == [None]
    
    def test_clean_json_string_invalid(self):
        """Test clean_json_string with invalid JSON"""
        with pytest.raises(ValueError, match="Invalid JSON string"):
            clean_json_string('{"invalid": }')
        
        with pytest.raises(ValueError, match="Invalid JSON string"):
            clean_json_string('{"app": "web-service", "missing":}')
    
    def test_clean_json_string_wrong_type(self):
        """Test clean_json_string with wrong input type"""
        with pytest.raises(TypeError, match="Unsupported type"):
            clean_json_string(123)
        
        with pytest.raises(TypeError, match="Unsupported type"):
            clean_json_string(['list', 'input'])
    
    def test_clean_json_string_complex(self):
        """Test clean_json_string with complex JSON"""
        complex_json = '{"tags": {"app": "billing", "env": "prod"}, "count": 42, "active": true}'
        result = clean_json_string(complex_json)
        assert isinstance(result, dict)
        assert result['tags']['app'] == 'billing'
        assert result['count'] == 42
        assert result['active'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])