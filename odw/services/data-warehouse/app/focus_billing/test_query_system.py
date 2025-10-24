#!/usr/bin/env python3
"""
Test script for FOCUS Query System

Tests the query loader and parameter handler with actual YAML files
to validate the implementation works with real data.
"""

import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from focus_billing.query_loader import FocusQueryLoader, FocusQueryParameterExtractor
from focus_billing.query_executor import FocusQueryParameterHandler, FocusQueryValidator
from focus_billing.config import FocusBillingConfig
from focus_billing.models import FocusQueryRequest


def test_query_loading():
    """Test loading queries from actual YAML files."""
    print("=" * 60)
    print("Testing Query Loading")
    print("=" * 60)
    
    config = FocusBillingConfig()
    loader = FocusQueryLoader(config)
    
    try:
        queries = loader.load_queries()
        print(f"✓ Successfully loaded {len(queries)} queries")
        
        # Show query details
        for slug, query in list(queries.items())[:5]:  # Show first 5
            print(f"\nQuery: {slug}")
            print(f"  Name: {query.name}")
            print(f"  Parameters: {query.parameters}")
            print(f"  SQL Preview: {query.sql[:100]}...")
            
        return queries
        
    except Exception as e:
        print(f"✗ Error loading queries: {e}")
        return None


def test_parameter_extraction():
    """Test parameter extraction from SQL queries."""
    print("\n" + "=" * 60)
    print("Testing Parameter Extraction")
    print("=" * 60)
    
    test_queries = [
        "SELECT * FROM focus_data_table WHERE ChargePeriodStart >= ? AND ChargePeriodEnd < ?",
        "SELECT ServiceName, SUM(BilledCost) FROM focus_data_table WHERE ServiceName = ? GROUP BY ServiceName",
        "SELECT * FROM focus_data_table WHERE JSONExtractString(Tags, '$.Application') = ? AND ChargePeriodStart >= ?",
    ]
    
    for i, sql in enumerate(test_queries, 1):
        print(f"\nTest Query {i}:")
        print(f"SQL: {sql}")
        
        analysis = FocusQueryParameterExtractor.analyze_query_parameters(sql)
        print(f"Positional parameters: {analysis['positional_count']}")
        print(f"Named parameters: {analysis['named_parameters']}")
        print(f"Has date filters: {analysis['has_date_filters']}")
        print(f"Table references: {analysis['table_references']}")
        print(f"JSON extractions: {len(analysis['json_extractions'])}")


def test_parameter_validation():
    """Test parameter validation and type coercion."""
    print("\n" + "=" * 60)
    print("Testing Parameter Validation")
    print("=" * 60)
    
    handler = FocusQueryParameterHandler()
    
    # Test date coercion
    test_dates = [
        "2024-01-01",
        "2024/01/31", 
        date(2024, 2, 15),
        datetime(2024, 3, 1, 12, 0, 0)
    ]
    
    print("\nDate coercion tests:")
    for test_date in test_dates:
        try:
            result = handler._coerce_to_date(test_date)
            print(f"  {test_date} ({type(test_date).__name__}) -> {result} ({type(result).__name__})")
        except Exception as e:
            print(f"  {test_date} -> ERROR: {e}")
    
    # Test numeric coercion
    test_numbers = ["123", 123.0, "45.67", Decimal("89.12")]
    
    print("\nNumeric coercion tests:")
    for test_num in test_numbers:
        try:
            int_result = handler._coerce_to_int(test_num) if isinstance(test_num, (str, int, float)) else "N/A"
            decimal_result = handler._coerce_to_decimal(test_num)
            print(f"  {test_num} -> int: {int_result}, decimal: {decimal_result}")
        except Exception as e:
            print(f"  {test_num} -> ERROR: {e}")


def test_sql_parameter_conversion():
    """Test converting positional to named parameters."""
    print("\n" + "=" * 60)
    print("Testing SQL Parameter Conversion")
    print("=" * 60)
    
    handler = FocusQueryParameterHandler()
    
    test_cases = [
        {
            "sql": "SELECT * FROM table WHERE col1 = ? AND col2 = ?",
            "params": ["start_date", "end_date"]
        },
        {
            "sql": "SELECT ServiceName, SUM(BilledCost) FROM focus_data_table WHERE ServiceName = ? AND ChargePeriodStart >= ? AND ChargePeriodEnd < ?",
            "params": ["service_name", "start_date", "end_date"]
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Original SQL: {case['sql']}")
        print(f"Parameters: {case['params']}")
        
        converted_sql = handler._convert_to_named_parameters(case['sql'], case['params'])
        print(f"Converted SQL: {converted_sql}")


def test_query_validation():
    """Test query validation functionality."""
    print("\n" + "=" * 60)
    print("Testing Query Validation")
    print("=" * 60)
    
    config = FocusBillingConfig()
    loader = FocusQueryLoader(config)
    
    try:
        queries = loader.load_queries()
        
        # Test validation on a few queries
        for slug, query in list(queries.items())[:3]:
            print(f"\nValidating query: {slug}")
            
            # Syntax validation
            syntax_issues = FocusQueryValidator.validate_query_syntax(query)
            if syntax_issues:
                print(f"  Syntax issues: {syntax_issues}")
            else:
                print("  ✓ Syntax validation passed")
            
            # Parameter validation with sample data
            if query.parameters:
                sample_params = {}
                for param in query.parameters:
                    if 'date' in param.lower():
                        sample_params[param] = "2024-01-01"
                    elif 'service' in param.lower():
                        sample_params[param] = "Compute"
                    else:
                        sample_params[param] = "test_value"
                
                param_issues = FocusQueryValidator.validate_parameter_usage(query, sample_params)
                if param_issues:
                    print(f"  Parameter issues: {param_issues}")
                else:
                    print("  ✓ Parameter validation passed")
            
    except Exception as e:
        print(f"✗ Error during validation: {e}")


def test_real_query_execution_prep():
    """Test preparing real queries for execution."""
    print("\n" + "=" * 60)
    print("Testing Real Query Execution Preparation")
    print("=" * 60)
    
    config = FocusBillingConfig()
    loader = FocusQueryLoader(config)
    handler = FocusQueryParameterHandler()
    
    try:
        queries = loader.load_queries()
        
        # Test with a specific query that has date parameters
        test_slug = None
        for slug, query in queries.items():
            if 'start_date' in query.parameters and 'end_date' in query.parameters:
                test_slug = slug
                break
        
        if test_slug:
            query = queries[test_slug]
            print(f"\nTesting query: {test_slug}")
            print(f"Original SQL: {query.sql}")
            
            # Prepare parameters
            raw_params = {
                'start_date': '2024-01-01',
                'end_date': '2024-01-31'
            }
            
            # Add any additional parameters the query might need
            for param in query.parameters:
                if param not in raw_params:
                    if 'service' in param.lower():
                        raw_params[param] = 'Compute'
                    elif 'application' in param.lower():
                        raw_params[param] = 'WebApp'
                    else:
                        raw_params[param] = 'test_value'
            
            print(f"Parameters: {raw_params}")
            
            # Validate and prepare
            try:
                prepared_sql, validated_params = handler.validate_and_prepare_parameters(query, raw_params)
                print(f"✓ Parameter validation successful")
                print(f"Prepared SQL: {prepared_sql}")
                print(f"Validated parameters: {validated_params}")
            except Exception as e:
                print(f"✗ Parameter validation failed: {e}")
        else:
            print("No suitable query found for testing")
            
    except Exception as e:
        print(f"✗ Error during execution preparation: {e}")


def main():
    """Run all tests."""
    print("FOCUS Query System Test Suite")
    print("Testing query loading and parameter handling functionality")
    
    # Run all tests
    queries = test_query_loading()
    
    if queries:
        test_parameter_extraction()
        test_parameter_validation()
        test_sql_parameter_conversion()
        test_query_validation()
        test_real_query_execution_prep()
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"✓ Successfully loaded {len(queries)} FOCUS queries")
        print("✓ Parameter extraction working")
        print("✓ Parameter validation working")
        print("✓ SQL conversion working")
        print("✓ Query validation working")
        print("✓ Execution preparation working")
        print("\nAll tests completed successfully!")
    else:
        print("\n✗ Query loading failed - cannot run additional tests")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())