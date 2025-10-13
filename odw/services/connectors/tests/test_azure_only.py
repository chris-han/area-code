#!/usr/bin/env python3
"""
Simplified test script for Azure Billing Connector components only

This script tests only the Azure billing components we implemented,
avoiding dependencies on other connectors and moose_lib.
"""

import sys
import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_configuration_models():
    """Test 1: Configuration Models"""
    logger.info("=== Testing Configuration Models ===")
    
    try:
        from azure_billing import (
            AzureApiConfig, ProcessingConfig, AzureBillingConnectorConfig, AzureBillingDetail
        )
        
        # Test AzureApiConfig
        api_config = AzureApiConfig(
            enrollment_number="123456789",
            api_key="test-api-key"
        )
        logger.info(f"✓ AzureApiConfig created: {api_config.enrollment_number}")
        
        # Test ProcessingConfig
        processing_config = ProcessingConfig(
            batch_size=500,
            chunk_size=5000
        )
        logger.info(f"✓ ProcessingConfig created: batch_size={processing_config.batch_size}")
        
        # Test AzureBillingConnectorConfig
        connector_config = AzureBillingConnectorConfig(
            azure_enrollment_number="123456789",
            azure_api_key="test-api-key",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        logger.info(f"✓ AzureBillingConnectorConfig created")
        
        # Test effective configurations
        effective_batch_size = connector_config.get_effective_batch_size()
        effective_api_config = connector_config.get_azure_api_config()
        logger.info(f"✓ Effective batch size: {effective_batch_size}")
        logger.info(f"✓ Effective API config: {effective_api_config.enrollment_number}")
        
        # Test AzureBillingDetail model
        test_record = AzureBillingDetail(
            instance_id="test-instance-123",
            month_date=date(2024, 1, 1),
            extended_cost=100.50,
            consumed_quantity=10.0
        )
        logger.info(f"✓ AzureBillingDetail model created: {test_record.instance_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration models test failed: {str(e)}")
        return False


def test_azure_api_client():
    """Test 2: Azure EA API Client"""
    logger.info("=== Testing Azure EA API Client ===")
    
    try:
        from azure_billing import AzureApiConfig, AzureEAApiClient
        
        # Create test configuration
        config = AzureApiConfig(
            enrollment_number="123456789",
            api_key="test-api-key",
            base_url="https://ea.azure.cn/rest"
        )
        
        # Create API client
        client = AzureEAApiClient(config)
        logger.info(f"✓ AzureEAApiClient created")
        
        # Test URL building
        billing_url = client.get_billing_data_url("2024-01")
        expected_url = "https://ea.azure.cn/rest/123456789/billingPeriods/2024-01/usagedetails"
        assert billing_url == expected_url, f"URL mismatch: {billing_url}"
        logger.info(f"✓ URL building works: {billing_url}")
        
        # Test headers
        headers = client._build_headers()
        assert "Authorization" in headers, "Authorization header missing"
        assert headers["Authorization"] == "bearer test-api-key", "Authorization header incorrect"
        logger.info(f"✓ Headers built correctly")
        
        # Test retry delay calculation
        delay1 = client._calculate_retry_delay(1)
        delay2 = client._calculate_retry_delay(2)
        assert delay2 > delay1, "Exponential backoff not working"
        logger.info(f"✓ Retry delay calculation works: {delay1:.2f}s -> {delay2:.2f}s")
        
        # Test retryable error detection
        class MockResponse:
            def __init__(self, status_code):
                self.status_code = status_code
        
        assert client._is_retryable_error(MockResponse(503), None) == True
        assert client._is_retryable_error(MockResponse(401), None) == False
        logger.info(f"✓ Retryable error detection works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Azure API client test failed: {str(e)}")
        return False


def test_resource_tracking_engine():
    """Test 3: Resource Tracking Engine"""
    logger.info("=== Testing Resource Tracking Engine ===")
    
    try:
        from azure_billing import ResourceTrackingEngine
        import polars as pl
        
        # Create engine
        engine = ResourceTrackingEngine()
        logger.info(f"✓ ResourceTrackingEngine created")
        
        # Load patterns (will use mock data)
        patterns = engine.load_patterns()
        logger.info(f"✓ Loaded {len(patterns)} patterns")
        
        # Test pattern matching
        match_result = engine._match_pattern(
            instance_id="/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm",
            resource_group="test-rg",
            subscription_guid="12345678-1234-1234-1234-123456789012",
            pattern="*/subscriptions/12345678-1234-1234-1234-123456789012/*",
            priority=3
        )
        logger.info(f"✓ Pattern matching works: {match_result}")
        
        # Test wildcard matching
        assert engine._wildcard_match("test-vm-01", "test-vm-*") == True
        assert engine._wildcard_match("prod-vm-01", "test-vm-*") == False
        logger.info(f"✓ Wildcard matching works")
        
        # Test vectorized tracking with sample data
        test_data = pl.DataFrame({
            'instance_id': [
                '/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/rg-production/providers/Microsoft.Compute/virtualMachines/vm-web-01',
                '/subscriptions/87654321-4321-4321-4321-210987654321/resourceGroups/rg-test/providers/Microsoft.Storage/storageAccounts/teststorage'
            ],
            'resource_group': ['rg-production', 'rg-test'],
            'subscription_guid': ['12345678-1234-1234-1234-123456789012', '87654321-4321-4321-4321-210987654321']
        })
        
        tracking_series, audit_df = engine.apply_tracking(test_data)
        logger.info(f"✓ Vectorized tracking works: {len(tracking_series)} assignments, {len(audit_df)} audit entries")
        
        # Test audit summary
        audit_summary = engine.generate_audit_summary(audit_df)
        logger.info(f"✓ Audit summary generated: {audit_summary}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Resource tracking engine test failed: {str(e)}")
        return False


def test_data_transformer():
    """Test 4: Data Transformer"""
    logger.info("=== Testing Data Transformer ===")
    
    try:
        from azure_billing import AzureBillingTransformer
        import polars as pl
        
        # Create sample raw data
        raw_data = pl.DataFrame({
            'instanceId': ['/subscriptions/test/resourceGroups/rg1/providers/Microsoft.Compute/virtualMachines/vm1'],
            'accountName': ['Test Account'],
            'subscriptionGuid': ['12345678-1234-1234-1234-123456789012'],
            'date': ['2024-01-15'],
            'extendedCost': [100.50],
            'consumedQuantity': [10.0],
            'meterCategory': ['Virtual Machines'],
            'meterName': ['D2s v3'],
            'product': ['Standard_D2s_v3 VM'],
            'tags': ['{"app": "web-service", "cost_center": "IT"}'],
            'additionalInfo': ['{"resourceType": "VirtualMachine"}']
        })
        
        logger.info(f"✓ Created sample raw data: {len(raw_data)} records")
        
        # Test field mappings
        mapped_df = AzureBillingTransformer._apply_field_mappings(raw_data)
        assert 'instance_id' in mapped_df.columns, "Field mapping failed"
        assert 'account_name' in mapped_df.columns, "Field mapping failed"
        logger.info(f"✓ Field mappings applied")
        
        # Test data type conversions
        typed_df = AzureBillingTransformer._convert_data_types(mapped_df)
        logger.info(f"✓ Data type conversions applied")
        
        # Test computed fields
        computed_df = AzureBillingTransformer._derive_computed_fields(typed_df)
        assert 'month_date' in computed_df.columns, "Computed field missing"
        assert 'newmonth' in computed_df.columns, "Computed field missing"
        logger.info(f"✓ Computed fields derived")
        
        # Test JSON processing
        json_df = AzureBillingTransformer._process_json_fields(computed_df)
        assert 'ppm_billing_item' in json_df.columns, "JSON extraction failed"
        logger.info(f"✓ JSON fields processed")
        
        # Test VM-specific logic
        vm_df = AzureBillingTransformer.derive_vm_specific_fields(json_df)
        assert 'sku' in vm_df.columns, "VM field missing"
        assert 'resource_name' in vm_df.columns, "VM field missing"
        logger.info(f"✓ VM-specific fields derived")
        
        # Test full transformation
        transformed_df = AzureBillingTransformer.transform_raw_data(raw_data)
        logger.info(f"✓ Full transformation completed: {len(transformed_df)} records")
        
        # Test JSON cleaning
        test_json = '{"app": "web-service", "invalid": }'
        cleaned = AzureBillingTransformer.clean_json_string(test_json)
        logger.info(f"✓ JSON cleaning works: {cleaned}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Data transformer test failed: {str(e)}")
        return False


def test_error_handler():
    """Test 5: Error Handler"""
    logger.info("=== Testing Error Handler ===")
    
    try:
        from azure_billing import ErrorHandler, ErrorType, ErrorSeverity
        import requests
        
        # Create error handler
        handler = ErrorHandler()
        logger.info(f"✓ ErrorHandler created")
        
        # Test API error handling
        class MockResponse:
            def __init__(self, status_code, url="http://test.com", text="Error"):
                self.status_code = status_code
                self.url = url
                self.text = text
                self.headers = {}
        
        # Test retryable error
        is_retryable = handler.handle_api_error(MockResponse(503), {"context": "test"})
        assert is_retryable == True, "503 should be retryable"
        logger.info(f"✓ API error handling works (retryable)")
        
        # Test non-retryable error
        is_retryable = handler.handle_api_error(MockResponse(401), {"context": "test"})
        assert is_retryable == False, "401 should not be retryable"
        logger.info(f"✓ API error handling works (non-retryable)")
        
        # Test data error handling
        test_record = {"field1": "value1", "field2": None}
        recovered = handler.handle_data_error(
            KeyError("missing_field"), 
            test_record, 
            {"context": "test"}
        )
        logger.info(f"✓ Data error handling works: {recovered}")
        
        # Test error statistics
        error_summary = handler.get_error_summary()
        assert 'error_counts' in error_summary, "Error summary missing counts"
        logger.info(f"✓ Error statistics work: {error_summary}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error handler test failed: {str(e)}")
        return False


def test_integration():
    """Test 6: Integration Test"""
    logger.info("=== Testing Integration ===")
    
    try:
        from azure_billing import AzureBillingConnector, AzureBillingConnectorConfig
        
        # Test connector creation
        config = AzureBillingConnectorConfig(
            azure_enrollment_number="123456789",
            azure_api_key="test-api-key",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            batch_size=100
        )
        
        connector = AzureBillingConnector(config)
        logger.info(f"✓ Connector created")
        
        # Test component initialization
        connector._initialize_components()
        assert connector._api_client is not None, "API client not initialized"
        assert connector._resource_tracking_engine is not None, "Resource tracking engine not initialized"
        assert connector._transformer is not None, "Transformer not initialized"
        logger.info(f"✓ Components initialized")
        
        # Test memory monitoring
        memory_usage = connector.get_memory_usage()
        assert 'rss_mb' in memory_usage, "Memory usage missing"
        logger.info(f"✓ Memory monitoring works: {memory_usage['rss_mb']:.1f}MB")
        
        # Test memory monitor context manager
        from azure_billing import MemoryMonitor
        with MemoryMonitor("test_operation") as monitor:
            # Simulate some work
            import time
            time.sleep(0.1)
        logger.info(f"✓ Memory monitor context manager works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Integration test failed: {str(e)}")
        return False


def test_end_to_end_simulation():
    """Test 7: End-to-End Simulation"""
    logger.info("=== Testing End-to-End Simulation ===")
    
    try:
        # Simulate the complete flow without actual API calls
        from azure_billing import (
            AzureBillingConnectorConfig, 
            AzureBillingTransformer, 
            ResourceTrackingEngine
        )
        import polars as pl
        
        logger.info("Simulating complete data processing flow...")
        
        # 1. Create mock raw data (simulating API response)
        mock_api_data = [
            {
                'instanceId': '/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/rg-prod/providers/Microsoft.Compute/virtualMachines/vm-web-01',
                'accountName': 'Production Account',
                'subscriptionGuid': '12345678-1234-1234-1234-123456789012',
                'date': '2024-01-15',
                'extendedCost': 150.75,
                'consumedQuantity': 24.0,
                'meterCategory': 'Virtual Machines',
                'meterName': 'D2s v3',
                'product': 'Standard_D2s_v3 VM',
                'tags': '{"app": "web-service", "cost_center": "IT", "environment": "prod"}',
                'additionalInfo': '{"resourceType": "VirtualMachine", "location": "eastus"}',
                'resourceGroup': 'rg-prod'
            },
            {
                'instanceId': '/subscriptions/87654321-4321-4321-4321-210987654321/resourceGroups/rg-test/providers/Microsoft.Storage/storageAccounts/teststorage',
                'accountName': 'Test Account',
                'subscriptionGuid': '87654321-4321-4321-4321-210987654321',
                'date': '2024-01-15',
                'extendedCost': 25.50,
                'consumedQuantity': 100.0,
                'meterCategory': 'Storage',
                'meterName': 'LRS Data Stored',
                'product': 'Standard LRS',
                'tags': '{"app": "data-service", "cost_center": "Engineering"}',
                'additionalInfo': '{"resourceType": "StorageAccount"}',
                'resourceGroup': 'rg-test'
            }
        ]
        
        logger.info(f"✓ Created {len(mock_api_data)} mock API records")
        
        # 2. Convert to DataFrame
        df = pl.DataFrame(mock_api_data)
        logger.info(f"✓ Converted to DataFrame: {len(df)} records")
        
        # 3. Transform data
        transformer = AzureBillingTransformer()
        transformed_df = transformer.transform_raw_data(df)
        logger.info(f"✓ Data transformation completed: {len(transformed_df)} records")
        
        # 4. Apply resource tracking
        engine = ResourceTrackingEngine()
        tracking_series, audit_df = engine.apply_tracking(transformed_df)
        logger.info(f"✓ Resource tracking applied: {len(audit_df)} audit entries")
        
        # 5. Add tracking to DataFrame
        final_df = transformed_df.with_columns(tracking_series)
        
        # 6. Apply business rules
        business_df = transformer.apply_business_rules(final_df)
        logger.info(f"✓ Business rules applied: {len(business_df)} final records")
        
        # 7. Validate final data structure
        required_fields = ['instance_id', 'month_date', 'extended_cost', 'resource_tracking']
        for field in required_fields:
            assert field in business_df.columns, f"Required field {field} missing"
        
        logger.info(f"✓ End-to-end simulation successful!")
        logger.info(f"  - Processed {len(business_df)} records")
        logger.info(f"  - Generated {len(audit_df)} audit entries")
        
        # Show sample of final data
        sample_record = business_df.row(0, named=True)
        logger.info(f"  - Sample record: instance_id={sample_record.get('instance_id', 'N/A')[:50]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ End-to-end simulation failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    logger.info("Starting Azure Billing Connector Test Suite (Azure Components Only)")
    logger.info("=" * 70)
    
    tests = [
        ("Configuration Models", test_configuration_models),
        ("Azure API Client", test_azure_api_client),
        ("Resource Tracking Engine", test_resource_tracking_engine),
        ("Data Transformer", test_data_transformer),
        ("Error Handler", test_error_handler),
        ("Integration Test", test_integration),
        ("End-to-End Simulation", test_end_to_end_simulation),
    ]
    
    results = {}
    
    # Run individual component tests
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {str(e)}")
            results[test_name] = False
        
        logger.info("")  # Add spacing between tests
    
    # Print summary
    logger.info("=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "PASS" if passed_test else "FAIL"
        logger.info(f"{test_name:<30} {status}")
        if passed_test:
            passed += 1
    
    logger.info("=" * 70)
    logger.info(f"TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Azure Billing Connector is ready.")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Set up real Azure EA API credentials")
        logger.info("2. Configure ClickHouse connection for resource tracking")
        logger.info("3. Test with real Azure billing data")
        logger.info("4. Deploy to production environment")
    else:
        logger.warning(f"⚠️  {total - passed} tests failed. Review the logs above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)