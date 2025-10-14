#!/usr/bin/env python3
"""
Test Configuration for Azure Billing Connector Test Suite

This module provides configuration settings and utilities for testing
the Azure Billing Connector implementation.
"""

import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional


class TestConfig:
    """Configuration settings for Azure Billing Connector tests"""
    
    # Test data settings
    DEFAULT_TEST_ENROLLMENT = "123456789"
    DEFAULT_TEST_API_KEY = "test-api-key-12345"
    DEFAULT_TEST_BASE_URL = "https://ea.azure.cn/rest"
    
    # Test date ranges
    DEFAULT_START_DATE = datetime(2024, 1, 1)
    DEFAULT_END_DATE = datetime(2024, 1, 31)
    
    # Processing settings
    DEFAULT_BATCH_SIZE = 100
    DEFAULT_CHUNK_SIZE = 1000
    
    # Test timeouts
    TEST_TIMEOUT_SECONDS = 300  # 5 minutes
    API_TIMEOUT_SECONDS = 30
    
    # Memory limits for testing
    MEMORY_THRESHOLD_MB = 500
    
    # Test data samples
    SAMPLE_INSTANCE_IDS = [
        "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/rg-production/providers/Microsoft.Compute/virtualMachines/vm-web-01",
        "/subscriptions/87654321-4321-4321-4321-210987654321/resourceGroups/rg-test/providers/Microsoft.Storage/storageAccounts/teststorage",
        "/subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/rg-dev/providers/Microsoft.Sql/servers/sqlserver-dev/databases/testdb"
    ]
    
    SAMPLE_RESOURCE_GROUPS = [
        "rg-production",
        "rg-test", 
        "rg-dev"
    ]
    
    SAMPLE_SUBSCRIPTION_GUIDS = [
        "12345678-1234-1234-1234-123456789012",
        "87654321-4321-4321-4321-210987654321",
        "11111111-2222-3333-4444-555555555555"
    ]
    
    @classmethod
    def get_test_connector_config(cls) -> Dict[str, Any]:
        """Get standard test connector configuration"""
        return {
            'azure_enrollment_number': cls.DEFAULT_TEST_ENROLLMENT,
            'azure_api_key': cls.DEFAULT_TEST_API_KEY,
            'api_base_url': cls.DEFAULT_TEST_BASE_URL,
            'start_date': cls.DEFAULT_START_DATE,
            'end_date': cls.DEFAULT_END_DATE,
            'batch_size': cls.DEFAULT_BATCH_SIZE
        }
    
    @classmethod
    def get_mock_api_response(cls, record_count: int = 2) -> Dict[str, Any]:
        """Generate mock Azure EA API response"""
        records = []
        
        for i in range(record_count):
            record = {
                'instanceId': cls.SAMPLE_INSTANCE_IDS[i % len(cls.SAMPLE_INSTANCE_IDS)],
                'accountName': f'Test Account {i+1}',
                'subscriptionGuid': cls.SAMPLE_SUBSCRIPTION_GUIDS[i % len(cls.SAMPLE_SUBSCRIPTION_GUIDS)],
                'subscriptionName': f'Test Subscription {i+1}',
                'date': '2024-01-15',
                'month': 1,
                'day': 15,
                'year': 2024,
                'product': 'Standard_D2s_v3 VM' if i % 2 == 0 else 'Standard LRS',
                'meterId': f'meter-{i+1:04d}',
                'meterCategory': 'Virtual Machines' if i % 2 == 0 else 'Storage',
                'meterSubCategory': 'Dv3 Series' if i % 2 == 0 else 'Locally Redundant',
                'meterName': 'D2s v3' if i % 2 == 0 else 'LRS Data Stored',
                'consumedQuantity': 24.0 + i,
                'resourceRate': 0.096 + (i * 0.001),
                'extendedCost': 150.75 + (i * 10),
                'resourceLocation': 'East US',
                'consumedService': 'Microsoft.Compute' if i % 2 == 0 else 'Microsoft.Storage',
                'serviceInfo1': '',
                'serviceInfo2': '',
                'additionalInfo': f'{{"resourceType": "{"VirtualMachine" if i % 2 == 0 else "StorageAccount"}", "location": "eastus"}}',
                'tags': f'{{"app": "{"web-service" if i % 2 == 0 else "data-service"}", "cost_center": "{"IT" if i % 2 == 0 else "Engineering"}", "environment": "{"prod" if i % 2 == 0 else "test"}"}}',
                'storeServiceIdentifier': '',
                'departmentName': 'IT Department',
                'costCenter': 'CC-001',
                'unitOfMeasure': 'Hours' if i % 2 == 0 else 'GB',
                'resourceGroup': cls.SAMPLE_RESOURCE_GROUPS[i % len(cls.SAMPLE_RESOURCE_GROUPS)]
            }
            records.append(record)
        
        return {
            'value': records,
            'nextLink': None  # No pagination for test data
        }
    
    @classmethod
    def get_mock_resource_patterns(cls) -> List[tuple]:
        """Get mock resource tracking patterns"""
        return [
            ("*/subscriptions/12345678-1234-1234-1234-123456789012/*", "Production App", 1),
            ("*/resourceGroups/rg-production/*", "Production Resources", 2),
            ("*/subscriptions/87654321-4321-4321-4321-210987654321/*", "Test Environment", 3),
            ("*/resourceGroups/rg-test/*", "Test Resources", 4),
            ("*/providers/Microsoft.Compute/virtualMachines/*", "Virtual Machines", 5),
            ("*/providers/Microsoft.Storage/storageAccounts/*", "Storage Accounts", 6)
        ]
    
    @classmethod
    def get_test_environment_vars(cls) -> Dict[str, str]:
        """Get environment variables for testing"""
        return {
            'AZURE_ENROLLMENT_NUMBER': cls.DEFAULT_TEST_ENROLLMENT,
            'AZURE_API_KEY': cls.DEFAULT_TEST_API_KEY,
            'AZURE_API_BASE_URL': cls.DEFAULT_TEST_BASE_URL,
            'TEST_MODE': 'true',
            'LOG_LEVEL': 'INFO'
        }


class MockDataGenerator:
    """Utility class for generating mock test data"""
    
    @staticmethod
    def generate_billing_records(count: int = 10) -> List[Dict[str, Any]]:
        """Generate mock billing records for testing"""
        records = []
        
        for i in range(count):
            record = {
                'id': f'billing-record-{i+1:04d}',
                'instance_id': TestConfig.SAMPLE_INSTANCE_IDS[i % len(TestConfig.SAMPLE_INSTANCE_IDS)],
                'account_name': f'Test Account {i+1}',
                'subscription_guid': TestConfig.SAMPLE_SUBSCRIPTION_GUIDS[i % len(TestConfig.SAMPLE_SUBSCRIPTION_GUIDS)],
                'date': date(2024, 1, 15),
                'month_date': date(2024, 1, 1),
                'extended_cost': 100.0 + (i * 25.5),
                'consumed_quantity': 10.0 + i,
                'meter_category': 'Virtual Machines' if i % 2 == 0 else 'Storage',
                'product': 'Standard_D2s_v3 VM' if i % 2 == 0 else 'Standard LRS',
                'resource_group': TestConfig.SAMPLE_RESOURCE_GROUPS[i % len(TestConfig.SAMPLE_RESOURCE_GROUPS)],
                'tags': {
                    'app': 'web-service' if i % 2 == 0 else 'data-service',
                    'cost_center': 'IT' if i % 2 == 0 else 'Engineering',
                    'environment': 'prod' if i % 2 == 0 else 'test'
                },
                'additional_info': {
                    'resourceType': 'VirtualMachine' if i % 2 == 0 else 'StorageAccount',
                    'location': 'eastus'
                }
            }
            records.append(record)
        
        return records
    
    @staticmethod
    def generate_api_error_responses() -> List[Dict[str, Any]]:
        """Generate mock API error responses for testing"""
        return [
            {
                'status_code': 503,
                'error': 'Service Unavailable',
                'message': 'The service is temporarily unavailable',
                'retryable': True
            },
            {
                'status_code': 401,
                'error': 'Unauthorized',
                'message': 'Invalid API key',
                'retryable': False
            },
            {
                'status_code': 429,
                'error': 'Too Many Requests',
                'message': 'Rate limit exceeded',
                'retryable': True
            },
            {
                'status_code': 500,
                'error': 'Internal Server Error',
                'message': 'An internal error occurred',
                'retryable': True
            }
        ]


class TestAssertions:
    """Custom assertion helpers for Azure Billing Connector tests"""
    
    @staticmethod
    def assert_billing_record_valid(record: Dict[str, Any]) -> None:
        """Assert that a billing record has required fields"""
        required_fields = ['instance_id', 'month_date']
        
        for field in required_fields:
            assert field in record, f"Required field '{field}' missing from record"
            assert record[field] is not None, f"Required field '{field}' is None"
    
    @staticmethod
    def assert_connector_config_valid(config: Any) -> None:
        """Assert that connector configuration is valid"""
        assert hasattr(config, 'azure_enrollment_number'), "Config missing enrollment number"
        assert hasattr(config, 'azure_api_key'), "Config missing API key"
        assert config.azure_enrollment_number is not None, "Enrollment number is None"
        assert config.azure_api_key is not None, "API key is None"
    
    @staticmethod
    def assert_memory_usage_reasonable(memory_mb: float, threshold_mb: float = 500) -> None:
        """Assert that memory usage is within reasonable limits"""
        assert memory_mb > 0, "Memory usage should be positive"
        assert memory_mb < threshold_mb, f"Memory usage {memory_mb}MB exceeds threshold {threshold_mb}MB"
    
    @staticmethod
    def assert_processing_time_reasonable(processing_time: float, max_time: float = 60) -> None:
        """Assert that processing time is reasonable"""
        assert processing_time > 0, "Processing time should be positive"
        assert processing_time < max_time, f"Processing time {processing_time}s exceeds maximum {max_time}s"


# Test data constants
TEST_ENROLLMENT_NUMBER = TestConfig.DEFAULT_TEST_ENROLLMENT
TEST_API_KEY = TestConfig.DEFAULT_TEST_API_KEY
TEST_BASE_URL = TestConfig.DEFAULT_TEST_BASE_URL
TEST_START_DATE = TestConfig.DEFAULT_START_DATE
TEST_END_DATE = TestConfig.DEFAULT_END_DATE
TEST_BATCH_SIZE = TestConfig.DEFAULT_BATCH_SIZE

# Export commonly used items
__all__ = [
    'TestConfig',
    'MockDataGenerator', 
    'TestAssertions',
    'TEST_ENROLLMENT_NUMBER',
    'TEST_API_KEY',
    'TEST_BASE_URL',
    'TEST_START_DATE',
    'TEST_END_DATE',
    'TEST_BATCH_SIZE'
]