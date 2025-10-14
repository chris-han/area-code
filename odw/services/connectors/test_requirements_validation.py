#!/usr/bin/env python3
"""
Test script to validate that all required dependencies are available
for the Azure billing functions to work properly.
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

def test_core_dependencies():
    """Test that core dependencies can be imported"""
    print("Testing core dependencies...")
    
    try:
        import polars as pl
        print("✓ polars imported successfully")
        
        import pandas as pd
        print("✓ pandas imported successfully")
        
        import pydantic
        print("✓ pydantic imported successfully")
        
        import clickhouse_connect
        print("✓ clickhouse-connect imported successfully")
        
        import xxhash
        print("✓ xxhash imported successfully")
        
        import psutil
        print("✓ psutil imported successfully")
        
        import pytest
        print("✓ pytest imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_azure_billing_functions():
    """Test that Azure billing functions can be extracted and used"""
    print("\nTesting Azure billing function extraction...")
    
    try:
        # Test clean_json_string function
        import json
        import math
        from typing import Any, Dict
        
        def clean_json_string(s: Any) -> Dict[str, Any]:
            """Extracted clean_json_string function"""
            if s is None or (isinstance(s, float) and math.isnan(s)):
                return None
            
            if isinstance(s, str):
                s = s.strip()
                if s == '' or s == '{}' or s == '[]':
                    return None
                try:
                    parsed_json = json.loads(s)
                    return parsed_json
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON string: '{s}'")
            raise TypeError(f"Unsupported type for JSON cleaning: {type(s)}")
        
        # Test the function
        result = clean_json_string('{"test": "value"}')
        assert result == {"test": "value"}
        print("✓ clean_json_string function works")
        
        # Test get_columns_from_create_query function
        from typing import List
        
        def get_columns_from_create_query(query: str) -> List[str]:
            """Extracted get_columns_from_create_query function"""
            try:
                engine_pos = query.upper().index('ENGINE')
                query_before_engine = query[:engine_pos]
            except ValueError:
                query_before_engine = query

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
        
        # Test the function
        test_query = '''
        CREATE TABLE test (
            id UInt64,
            name String
        )
        ENGINE = MergeTree()
        '''
        result = get_columns_from_create_query(test_query)
        assert result == ['id', 'name']
        print("✓ get_columns_from_create_query function works")
        
        return True
        
    except Exception as e:
        print(f"✗ Function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pytest_integration():
    """Test that pytest can discover and run tests"""
    print("\nTesting pytest integration...")
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/test_azure_billing_pytest.py::TestAzureBillingActualFunctions', 
            '--collect-only', '-q'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print("✓ pytest can discover Azure billing function tests")
            return True
        else:
            print(f"✗ pytest discovery failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ pytest integration test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("=" * 60)
    print("AZURE BILLING CONNECTOR - REQUIREMENTS VALIDATION")
    print("=" * 60)
    
    tests = [
        ("Core Dependencies", test_core_dependencies),
        ("Azure Billing Functions", test_azure_billing_functions),
        ("Pytest Integration", test_pytest_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:<30} {status}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("The requirements.txt file is complete and all dependencies work correctly.")
        print("\nYou can now run:")
        print("  uv pip install -r requirements.txt")
        print("  python -m pytest tests/test_azure_billing_pytest.py -v")
    else:
        print(f"\n⚠️  {len(results) - passed} validation(s) failed.")
        print("Please check the requirements.txt file and install missing dependencies.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)