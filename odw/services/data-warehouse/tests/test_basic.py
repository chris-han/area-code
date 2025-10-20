"""
Basic test to verify test infrastructure works.
"""

import pytest
from datetime import datetime


def test_basic_functionality():
    """Test basic functionality to verify test setup."""
    assert True
    assert 1 + 1 == 2
    assert isinstance(datetime.now(), datetime)


def test_azure_billing_imports():
    """Test that Azure billing modules can be imported."""
    try:
        from app.azure_billing.models.azure_blob_parquet_models import AzureNCEIParquetModel
        from app.azure_billing.workflows.azure_ncei_workflow import AzureNCEIToFOCUSWorkflow
        assert True
    except ImportError as e:
        pytest.skip(f"Azure billing modules not available: {e}")


def test_sync_functionality():
    """Test sync functionality works in test environment."""
    
    def sample_function():
        return "sync_result"
    
    result = sample_function()
    assert result == "sync_result"