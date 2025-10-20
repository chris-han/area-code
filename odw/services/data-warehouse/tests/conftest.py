"""
Pytest configuration and fixtures for ABI tests.
"""

import pytest
import asyncio
from typing import Dict, Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
import tempfile
import os
from datetime import datetime, timedelta

try:
    from testcontainers.postgres import PostgresContainer
    from testcontainers.clickhouse import ClickHouseContainer
    from testcontainers.redis import RedisContainer
    TESTCONTAINERS_AVAILABLE = True
except ImportError:
    TESTCONTAINERS_AVAILABLE = False
    PostgresContainer = None
    ClickHouseContainer = None
    RedisContainer = None

try:
    from app.azure_billing.plugins.plugin_integration import PluginIntegrationService
    from app.azure_billing.workflows.azure_ncei_workflow import AzureNCEIToFOCUSWorkflow
    AZURE_BILLING_AVAILABLE = True
except ImportError:
    AZURE_BILLING_AVAILABLE = False
    PluginIntegrationService = None
    AzureNCEIToFOCUSWorkflow = None


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def postgres_container():
    """Start PostgreSQL container for testing."""
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers not available")
    with PostgresContainer("postgres:13") as postgres:
        yield postgres


@pytest.fixture(scope="session")
async def clickhouse_container():
    """Start ClickHouse container for testing."""
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers not available")
    with ClickHouseContainer("clickhouse/clickhouse-server:latest") as clickhouse:
        yield clickhouse


@pytest.fixture(scope="session")
async def redis_container():
    """Start Redis container for testing."""
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers not available")
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture
async def mock_azure_blob_client():
    """Mock Azure Blob Storage client."""
    mock_client = AsyncMock()
    
    # Mock blob list response
    mock_client.list_blobs.return_value = [
        {
            "name": "focus-data/2024/01/billing_data_20240101.parquet",
            "size": 1024000,
            "last_modified": datetime.utcnow(),
            "content_type": "application/parquet"
        },
        {
            "name": "focus-data/2024/01/billing_data_20240102.parquet", 
            "size": 2048000,
            "last_modified": datetime.utcnow(),
            "content_type": "application/parquet"
        }
    ]
    
    # Mock blob download
    mock_client.download_blob.return_value = b"mock_parquet_data"
    
    return mock_client


@pytest.fixture
async def mock_temporal_client():
    """Mock Temporal client for workflow testing."""
    mock_client = AsyncMock()
    
    # Mock workflow execution
    mock_client.execute_workflow.return_value = {
        "status": "completed",
        "workflow_id": "test-workflow-123",
        "files_processed": 2,
        "records_processed": 2000
    }
    
    return mock_client


@pytest.fixture
async def sample_azure_billing_data():
    """Sample Azure billing data for testing."""
    return [
        {
            "billing_account_id": "12345678-1234-1234-1234-123456789012",
            "billing_account_name": "Test Subscription",
            "usage_date": "2024-01-01",
            "billed_cost": 150.75,
            "effective_cost": 150.75,
            "billing_currency": "USD",
            "service_category": "Compute",
            "service_name": "Virtual Machines",
            "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm",
            "resource_name": "test-vm",
            "resource_type": "Microsoft.Compute/virtualMachines",
            "region": "East US",
            "provider": "Azure"
        },
        {
            "billing_account_id": "12345678-1234-1234-1234-123456789012",
            "billing_account_name": "Test Subscription",
            "usage_date": "2024-01-01",
            "billed_cost": 89.25,
            "effective_cost": 89.25,
            "billing_currency": "USD",
            "service_category": "Storage",
            "service_name": "Storage Accounts",
            "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/teststorage",
            "resource_name": "teststorage",
            "resource_type": "Microsoft.Storage/storageAccounts",
            "region": "East US",
            "provider": "Azure"
        }
    ]


@pytest.fixture
async def sample_plugin_config():
    """Sample plugin configuration for testing."""
    return {
        "azure_blob_storage": {
            "account_url": "https://finopsbilling.blob.core.chinacloudapi.cn",
            "container_name": "billing-data",
            "sas_token": "sv=2024-11-04&ss=bfqt&srt=sco&sp=rltfx&se=2045-10-19T12:52:39Z...",
            "path_prefix": "focus-data/",
            "timeout": 30
        },
        "azure_ea_api": {
            "enrollment_number": "V5702303S0121",
            "api_key": "test_api_key",
            "base_url": "https://consumption.azure.com",
            "timeout": 30
        }
    }


@pytest.fixture
async def mock_plugin_integration_service():
    """Mock plugin integration service."""
    if not AZURE_BILLING_AVAILABLE:
        pytest.skip("Azure billing modules not available")
    service = AsyncMock(spec=PluginIntegrationService)
    
    # Mock marketplace plugins
    service.get_marketplace_plugins.return_value = [
        {
            "id": "azure-ea-api",
            "name": "Azure EA API",
            "version": "1.0.0",
            "description": "Azure Enterprise Agreement API connector",
            "author": "ABI Team",
            "category": "billing",
            "tags": ["azure", "billing", "enterprise"],
            "isInstalled": True,
            "isConfigured": True,
            "isActive": True
        },
        {
            "id": "azure-blob-storage",
            "name": "Azure Blob Storage",
            "version": "1.0.0", 
            "description": "Azure Blob Storage connector for parquet files",
            "author": "ABI Team",
            "category": "storage",
            "tags": ["azure", "storage", "parquet"],
            "isInstalled": True,
            "isConfigured": True,
            "isActive": True
        }
    ]
    
    # Mock plugin operations
    service.install_plugin.return_value = True
    service.configure_plugin.return_value = True
    service.test_plugin_connection.return_value = {
        "success": True,
        "message": "Connection test successful",
        "tested_at": datetime.utcnow().isoformat()
    }
    
    return service


@pytest.fixture
async def temp_test_directory():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
async def mock_focus_validation_results():
    """Mock FOCUS validation results."""
    return {
        "valid": True,
        "errors": [],
        "warnings": [],
        "compliance_score": 0.95,
        "required_fields_present": True,
        "data_quality_score": 0.92,
        "validation_timestamp": datetime.utcnow().isoformat()
    }


@pytest.fixture
async def mock_clickhouse_client():
    """Mock ClickHouse client for testing."""
    mock_client = AsyncMock()
    
    # Mock query results
    mock_client.execute.return_value = [
        ("12345678-1234-1234-1234-123456789012", "2024-01-01", 150.75, "USD", "Compute"),
        ("12345678-1234-1234-1234-123456789012", "2024-01-01", 89.25, "USD", "Storage")
    ]
    
    mock_client.query.return_value = {
        "data": [
            {
                "billing_account_id": "12345678-1234-1234-1234-123456789012",
                "usage_date": "2024-01-01",
                "total_cost": 240.00,
                "service_category": "Compute"
            }
        ],
        "rows": 1,
        "statistics": {
            "elapsed": 0.123,
            "rows_read": 1000,
            "bytes_read": 50000
        }
    }
    
    return mock_client


@pytest.fixture
async def workflow_test_params():
    """Test parameters for workflow execution."""
    return {
        "account_url": "https://finopsbilling.blob.core.chinacloudapi.cn",
        "container_name": "billing-data",
        "secondary_container": None,
        "sas_token": "sv=2024-11-04&ss=bfqt&srt=sco&sp=rltfx&se=2045-10-19T12:52:39Z...",
        "path_prefix": "focus-data/",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "batch_size": 10
    }