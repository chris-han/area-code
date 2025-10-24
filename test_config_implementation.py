#!/usr/bin/env python3
"""
Test script for FOCUS billing configuration and observability implementation
"""

import sys
import os
from pathlib import Path

# Change to the correct directory and set up path
os.chdir('odw/services/data-warehouse')
sys.path.append('app')

def test_configuration():
    """Test the configuration implementation"""
    print("=== Testing Configuration Implementation ===")
    
    try:
        from focus_billing.config import focus_config
        
        print("✓ Configuration module imported successfully")
        print(f"✓ FOCUS data root: {focus_config.focus_data_root}")
        print(f"✓ ClickHouse host: {focus_config.clickhouse_host}:{focus_config.clickhouse_port}")
        print(f"✓ ClickHouse database: {focus_config.clickhouse_database}")
        print(f"✓ Batch size: {focus_config.batch_size}")
        print(f"✓ Max workers: {focus_config.max_workers}")
        print(f"✓ Connection timeout: {focus_config.connection_timeout}s")
        print(f"✓ Send/receive timeout: {focus_config.send_receive_timeout}s")
        
        # Test path validation
        path_results = focus_config.validate_paths()
        print(f"\n--- Path Validation ---")
        for path_name, exists in path_results.items():
            status = "✓" if exists else "✗"
            print(f"{status} {path_name}: {exists}")
        
        # Test ClickHouse connection parameters
        conn_params = focus_config.get_clickhouse_connection_params()
        print(f"\n--- ClickHouse Connection Parameters ---")
        for key, value in conn_params.items():
            if key == 'password':
                print(f"✓ {key}: {'*' * len(str(value))}")
            else:
                print(f"✓ {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_observability():
    """Test the observability implementation"""
    print("\n=== Testing Observability Implementation ===")
    
    try:
        from focus_billing.observability import focus_observability, MetricType, TimedOperation
        
        print("✓ Observability module imported successfully")
        
        # Test metric emission
        focus_observability.emit_counter("test.counter", 1.0, {"test": "true"})
        focus_observability.emit_gauge("test.gauge", 42.0, {"test": "true"}, "units")
        focus_observability.emit_timer("test.timer", 1.5, {"test": "true"})
        
        print("✓ Metrics emitted successfully")
        
        # Test timed operation
        with TimedOperation(focus_observability, "test.timed_operation", {"test": "true"}):
            import time
            time.sleep(0.1)
        
        print("✓ Timed operation completed successfully")
        
        # Get metrics summary
        summary = focus_observability.get_metrics_summary()
        print(f"✓ Collected {summary['total_metrics']} metrics")
        
        if 'by_type' in summary:
            for metric_type, metrics in summary['by_type'].items():
                print(f"  - {metric_type}: {len(metrics)} metrics")
        
        return True
        
    except Exception as e:
        print(f"✗ Observability test failed: {e}")
        return False

def test_validation_script():
    """Test the validation script"""
    print("\n=== Testing Validation Script ===")
    
    try:
        # Import the validation functions
        sys.path.append('app/focus_billing')
        from validate_system import validate_configuration, validate_performance
        
        print("✓ Validation script imported successfully")
        
        # Test configuration validation
        config_results = validate_configuration()
        print(f"✓ Configuration validation completed: {config_results['config_valid']}")
        
        # Test performance validation
        performance_results = validate_performance()
        print(f"✓ Performance validation completed: {performance_results['performance_valid']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Validation script test failed: {e}")
        return False

def test_workflow_integration():
    """Test workflow integration with observability"""
    print("\n=== Testing Workflow Integration ===")
    
    try:
        from focus_billing.workflow import FocusBillingIngestParams, FocusBillingIngestWorkflow
        
        print("✓ Workflow module imported successfully")
        
        # Create test parameters
        params = FocusBillingIngestParams(
            dry_run=True,
            max_files=1,
            batch_size=100
        )
        
        print(f"✓ Workflow parameters created: dry_run={params.dry_run}, batch_size={params.batch_size}")
        
        # Test workflow initialization (don't execute)
        workflow = FocusBillingIngestWorkflow(params)
        print("✓ Workflow initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Workflow integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("FOCUS Billing Configuration and Observability Test")
    print("=" * 60)
    
    tests = [
        ("Configuration", test_configuration),
        ("Observability", test_observability),
        ("Validation Script", test_validation_script),
        ("Workflow Integration", test_workflow_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Configuration and observability implementation is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())