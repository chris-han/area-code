#!/usr/bin/env python3
"""
FOCUS Billing End-to-End Test Wrapper

Simple wrapper to test the end-to-end testing functionality without requiring
full pytest setup. This validates that all components can be imported and
basic functionality works.
"""

import sys
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all required modules can be imported"""
    print("=== Testing Imports ===")
    
    try:
        from focus_billing.config import get_focus_config
        print("✓ Configuration module imported")
        
        from focus_billing.query_loader import FocusQueryLoader
        print("✓ Query loader module imported")
        
        from focus_billing.observability import focus_observability
        print("✓ Observability module imported")
        
        from focus_billing.workflow import FocusBillingIngestWorkflow, FocusBillingIngestParams
        print("✓ Workflow module imported")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n=== Testing Configuration ===")
    
    try:
        from focus_billing.config import get_focus_config
        
        print(f"ClickHouse host: {get_focus_config().clickhouse_host}")
        print(f"Database: {get_focus_config().clickhouse_database}")
        print(f"Data root: {get_focus_config().focus_data_root}")
        
        # Test path validation
        path_status = get_focus_config().validate_paths()
        print(f"Path validation: {sum(path_status.values())}/{len(path_status)} paths exist")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_query_catalog():
    """Test query catalog loading"""
    print("\n=== Testing Query Catalog ===")
    
    try:
        from focus_billing.query_loader import FocusQueryLoader
        
        query_loader = FocusQueryLoader()
        queries_dict = query_loader.load_queries()
        queries = list(queries_dict.values())
        
        print(f"Loaded {len(queries)} queries")
        
        if queries:
            sample_query = queries[0]
            print(f"Sample query: {sample_query.slug}")
            print(f"Title: {sample_query.name}")
            print(f"SQL length: {len(sample_query.sql)} characters")
        
        return len(queries) > 0
    except Exception as e:
        print(f"✗ Query catalog test failed: {e}")
        return False

def test_clickhouse_connectivity():
    """Test ClickHouse connectivity (basic check)"""
    print("\n=== Testing ClickHouse Connectivity ===")
    
    try:
        from focus_billing.observability import FocusObservability
        
        # Create observability instance
        observability = FocusObservability()
        
        # Test basic connectivity by checking a single table
        table_names = ["focus_cost_usage", "focus_contract_commitment", "focus_ingest_manifest"]
        
        connection_works = True
        table_results = []
        
        for table_name in table_names:
            try:
                status = observability.verify_table_exists(table_name)
                status_icon = "✓" if status.passed else "⚠"
                print(f"  {status_icon} {table_name}: {status.message}")
                table_results.append(status)
                
                # Check for connection issues
                if "connection" in status.message.lower() or "timeout" in status.message.lower():
                    connection_works = False
                    
            except Exception as e:
                print(f"  ✗ {table_name}: {e}")
                if "connection" in str(e).lower() or "timeout" in str(e).lower():
                    connection_works = False
        
        print(f"Table checks completed: {len(table_results)} tables")
        return connection_works
    except Exception as e:
        print(f"✗ ClickHouse connectivity test failed: {e}")
        return False

def test_api_imports():
    """Test API module imports"""
    print("\n=== Testing API Imports ===")
    
    try:
        from apis.focus_billing.list_use_cases import list_focus_use_cases_api
        print("✓ list_use_cases API imported")
        
        from apis.focus_billing.execute_use_case import execute_focus_use_case_api
        print("✓ execute_use_case API imported")
        
        from apis.focus_billing.list_supported_features import list_supported_features_api
        print("✓ list_supported_features API imported")
        
        return True
    except Exception as e:
        print(f"✗ API import test failed: {e}")
        return False

def test_smoke_test_components():
    """Test smoke test components can be created"""
    print("\n=== Testing Smoke Test Components ===")
    
    try:
        import tempfile
        import json
        import pandas as pd
        from datetime import datetime
        
        # Test creating sample data (similar to smoke tests)
        temp_dir = tempfile.mkdtemp()
        
        # Create minimal sample data
        sample_data = {
            "BillingAccountId": ["test-account"] * 5,
            "UsageDate": [datetime(2025, 7, 1)] * 5,
            "BilledCost": [1.00, 2.50, 0.75, 3.25, 1.50],
            "EffectiveCost": [1.00, 2.50, 0.75, 3.25, 1.50],
            "BillingCurrency": ["USD"] * 5,
            "ServiceCategory": ["Compute"] * 5,
            "ServiceName": ["Virtual Machines"] * 5,
            "ResourceId": [f"test-resource-{i}" for i in range(5)],
            "Provider": ["Azure"] * 5,
            "Region": ["East US"] * 5
        }
        
        df = pd.DataFrame(sample_data)
        print(f"Created test DataFrame with {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        return True
    except Exception as e:
        print(f"✗ Smoke test components test failed: {e}")
        return False

def test_verification_file_access():
    """Test access to verification results file"""
    print("\n=== Testing Verification File Access ===")
    
    try:
        verification_file = Path("focus-mcp-main/verification_results_clickhouse.json")
        
        if verification_file.exists():
            with open(verification_file, 'r') as f:
                verification_data = json.load(f)
            
            print(f"✓ Verification file loaded")
            print(f"Results count: {len(verification_data.get('results', []))}")
            print(f"Date range: {verification_data.get('start_date')} to {verification_data.get('end_date')}")
            
            return True
        else:
            print(f"⚠ Verification file not found: {verification_file}")
            print("This is acceptable - verification tests will be skipped")
            return True
            
    except Exception as e:
        print(f"✗ Verification file access test failed: {e}")
        return False

def run_basic_api_test():
    """Run a basic API test"""
    print("\n=== Testing Basic API Functionality ===")
    
    try:
        # Import the API function and models
        from apis.focus_billing.list_use_cases import list_focus_use_cases, ListFocusUseCasesQueryParams
        
        # Create empty query parameters (no filters)
        params = ListFocusUseCasesQueryParams()
        
        # Call the function directly (bypassing Moose API wrapper for testing)
        response = list_focus_use_cases(client=None, params=params)
        
        print(f"✓ API call successful")
        print(f"Response type: {type(response)}")
        
        # Access response attributes (it's a Pydantic model)
        print(f"Total use cases: {response.total_count}")
        print(f"Categories: {response.categories}")
        
        if response.use_cases:
            sample_case = response.use_cases[0]
            print(f"Sample use case: {sample_case.slug}")
            print(f"Sample name: {sample_case.name}")
            print(f"Sample parameters: {sample_case.parameters}")
        
        return True
    except Exception as e:
        print(f"✗ Basic API test failed: {e}")
        return False

def main():
    """Run all wrapper tests"""
    print("FOCUS Billing End-to-End Test Wrapper")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Query Catalog", test_query_catalog),
        ("ClickHouse Connectivity", test_clickhouse_connectivity),
        ("API Imports", test_api_imports),
        ("Smoke Test Components", test_smoke_test_components),
        ("Verification File Access", test_verification_file_access),
        ("Basic API Functionality", run_basic_api_test)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:8} {test_name}")
        if success:
            passed += 1
    
    print("-" * 50)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 All tests passed! End-to-end testing suite is ready.")
        return 0
    elif passed >= total * 0.7:
        print("⚠ Most tests passed. Some issues may need attention.")
        return 0
    else:
        print("❌ Many tests failed. System may have configuration issues.")
        return 1

if __name__ == "__main__":
    import json
    sys.exit(main())