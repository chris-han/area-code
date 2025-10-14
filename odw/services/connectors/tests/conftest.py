#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for Azure Billing Connector tests

This file contains pytest fixtures and configuration that are shared
across all test files in the test suite.
"""

import sys
import os
import pytest
from datetime import datetime, date
from typing import Dict, Any, List

# Add src and parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import test utilities
try:
    from test_config import TestConfig, MockDataGenerator, TestAssertions
    from test_utils import TestTimer, MemoryMonitor, MockAzureApiClient
except ImportError as e:
    pytest.skip(f"Test utilities not available: {e}", allow_module_level=True)


# Session-scoped fixtures (created once per test session)
@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration for the entire test session"""
    return TestConfig()


@pytest.fixture(scope="session")
def mock_data_generator():
    """Provide mock data generator for the entire test session"""
    return MockDataGenerator()


# Function-scoped fixtures (created for each test function)
@pytest.fixture
def azure_config():
    """Provide mock Azure configuration"""
    return TestConfig.get_test_connector_config()


@pytest.fixture
def mock_api_response():
    """Provide mock Azure EA API response"""
    return TestConfig.get_mock_api_response(5)


@pytest.fixture
def mock_billing_records():
    """Provide mock billing records"""
    return MockDataGenerator.generate_billing_records(10)


@pytest.fixture
def mock_resource_patterns():
    """Provide mock resource tracking patterns"""
    return TestConfig.get_mock_resource_patterns()


@pytest.fixture
def mock_azure_api_client(azure_config):
    """Provide mock Azure API client"""
    try:
        from azure_billing import AzureApiConfig
        config = AzureApiConfig(**azure_config)
        return MockAzureApiClient(config)
    except ImportError:
        pytest.skip("Azure billing modules not available")


@pytest.fixture
def memory_monitor():
    """Provide memory monitor for performance tests"""
    def _create_monitor(test_name: str):
        return MemoryMonitor(test_name)
    return _create_monitor


@pytest.fixture
def test_timer():
    """Provide test timer for performance tests"""
    def _create_timer(test_name: str):
        return TestTimer(test_name)
    return _create_timer


# Parametrized fixtures for testing multiple scenarios
@pytest.fixture(params=[1, 5, 10, 50])
def record_counts(request):
    """Provide different record counts for testing"""
    return request.param


@pytest.fixture(params=[
    {"batch_size": 10},
    {"batch_size": 100},
    {"batch_size": 1000}
])
def batch_sizes(request):
    """Provide different batch sizes for testing"""
    return request.param


@pytest.fixture(params=[
    datetime(2024, 1, 1),
    datetime(2024, 6, 15),
    datetime(2024, 12, 31)
])
def test_dates(request):
    """Provide different test dates"""
    return request.param


# Conditional fixtures based on available modules
@pytest.fixture
def polars_available():
    """Check if Polars is available"""
    try:
        import polars as pl
        return True
    except ImportError:
        return False


@pytest.fixture
def clickhouse_available():
    """Check if ClickHouse client is available"""
    try:
        import clickhouse_connect
        return True
    except ImportError:
        return False


@pytest.fixture
def requests_available():
    """Check if requests library is available"""
    try:
        import requests
        return True
    except ImportError:
        return False


# Test environment setup fixtures
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for each test"""
    # Set environment variables
    os.environ['TEST_MODE'] = 'true'
    os.environ['LOG_LEVEL'] = 'INFO'
    
    # Add src to Python path if not already there
    src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    yield
    
    # Cleanup after test
    # Remove test-specific environment variables if needed
    pass


@pytest.fixture
def temp_directory(tmp_path):
    """Provide temporary directory for tests that need file operations"""
    return tmp_path


# Error handling fixtures
@pytest.fixture
def mock_api_errors():
    """Provide mock API error responses"""
    return MockDataGenerator.generate_api_error_responses()


# Performance testing fixtures
@pytest.fixture
def performance_thresholds():
    """Provide performance thresholds for testing"""
    return {
        'max_memory_mb': 500,
        'max_execution_time_seconds': 60,
        'max_api_response_time_seconds': 30
    }


# Pytest hooks for test customization
def pytest_configure(config):
    """Configure pytest with custom settings"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "azure_billing: mark test as Azure Billing Connector test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "mock: mark test as using mock data"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers"""
    for item in items:
        # Add azure_billing marker to all tests in this suite
        item.add_marker(pytest.mark.azure_billing)
        
        # Add slow marker to tests with "integration" in name
        if "integration" in item.name.lower():
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.integration)
        
        # Add unit marker to other tests
        elif "test_" in item.name:
            item.add_marker(pytest.mark.unit)
        
        # Add mock marker to tests using mock data
        if "mock" in item.name.lower():
            item.add_marker(pytest.mark.mock)


def pytest_runtest_setup(item):
    """Setup for each test run"""
    # Skip tests if required modules are not available
    if item.get_closest_marker("requires_polars"):
        try:
            import polars
        except ImportError:
            pytest.skip("Polars not available")
    
    if item.get_closest_marker("requires_clickhouse"):
        try:
            import clickhouse_connect
        except ImportError:
            pytest.skip("ClickHouse client not available")
    
    if item.get_closest_marker("requires_requests"):
        try:
            import requests
        except ImportError:
            pytest.skip("Requests library not available")


def pytest_runtest_teardown(item, nextitem):
    """Cleanup after each test run"""
    # Force garbage collection after each test
    import gc
    gc.collect()


# Custom pytest markers for skipping tests based on conditions
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "requires_polars: mark test as requiring Polars library"
    )
    config.addinivalue_line(
        "markers", "requires_clickhouse: mark test as requiring ClickHouse client"
    )
    config.addinivalue_line(
        "markers", "requires_requests: mark test as requiring Requests library"
    )