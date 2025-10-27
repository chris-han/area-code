"""
Test FOCUS Billing Ingestion Workflow

Basic tests to verify workflow components can be imported and initialized.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from .workflow import (
    FocusBillingIngestParams,
    FocusBillingIngestWorkflow,
    WorkflowStats,
    run_focus_billing_ingest_task
)
from .file_discovery import FocusFileDiscovery, ParquetFileInfo
from .data_transformer import FocusDataTransformer
from .clickhouse_inserter import ClickHouseInserter


def test_workflow_params_creation():
    """Test that workflow parameters can be created with defaults"""
    params = FocusBillingIngestParams()
    
    assert params.data_root is None
    assert params.batch_size is None
    assert params.max_files is None
    assert params.dry_run is False
    assert params.dataset_type_filter is None
    assert params.period_filter is None
    assert params.continue_on_error is True
    assert params.skip_processed is True


def test_workflow_params_with_values():
    """Test that workflow parameters can be created with custom values"""
    params = FocusBillingIngestParams(
        data_root="/custom/path",
        batch_size=5000,
        max_files=10,
        dry_run=True,
        dataset_type_filter="cost_usage",
        period_filter="20250701-20250731",
        continue_on_error=False,
        skip_processed=False
    )
    
    assert params.data_root == "/custom/path"
    assert params.batch_size == 5000
    assert params.max_files == 10
    assert params.dry_run is True
    assert params.dataset_type_filter == "cost_usage"
    assert params.period_filter == "20250701-20250731"
    assert params.continue_on_error is False
    assert params.skip_processed is False


def test_workflow_stats_creation():
    """Test that workflow statistics can be created"""
    stats = WorkflowStats()
    
    assert stats.files_discovered == 0
    assert stats.files_processed == 0
    assert stats.files_skipped == 0
    assert stats.files_failed == 0
    assert stats.total_rows_processed == 0
    assert stats.total_processing_time == 0.0
    assert stats.errors == []


def test_workflow_initialization():
    """Test that workflow can be initialized"""
    params = FocusBillingIngestParams(dry_run=True)
    workflow = FocusBillingIngestWorkflow(params)
    
    assert workflow.params == params
    assert isinstance(workflow.stats, WorkflowStats)
    assert workflow.file_discovery is not None
    assert workflow.file_tracker is not None
    assert workflow.data_transformer is not None
    assert workflow.clickhouse_inserter is None  # Not initialized until needed


@patch('app.focus_billing.workflow.FocusFileDiscovery')
@patch('app.focus_billing.workflow.ProcessedFileTracker')
def test_workflow_dry_run_execution(mock_tracker, mock_discovery):
    """Test workflow execution in dry run mode"""
    # Mock file discovery to return empty list
    mock_discovery_instance = MagicMock()
    mock_discovery_instance.discover_parquet_files.return_value = []
    mock_discovery.return_value = mock_discovery_instance
    
    # Mock file tracker
    mock_tracker_instance = MagicMock()
    mock_tracker.return_value = mock_tracker_instance
    
    # Create workflow with dry run
    params = FocusBillingIngestParams(dry_run=True)
    workflow = FocusBillingIngestWorkflow(params)
    
    # Execute workflow
    stats = workflow.execute()
    
    # Verify results
    assert isinstance(stats, WorkflowStats)
    assert stats.files_discovered == 0
    assert stats.files_processed == 0
    
    # Verify discovery was called
    mock_discovery_instance.discover_parquet_files.assert_called_once()


def test_file_discovery_initialization():
    """Test that file discovery can be initialized"""
    discovery = FocusFileDiscovery("/test/path")
    assert discovery.data_root == Path("/test/path")


def test_data_transformer_initialization():
    """Test that data transformer can be initialized"""
    transformer = FocusDataTransformer()
    assert transformer.source_system == "focus_parquet"


@patch('app.focus_billing.clickhouse_inserter.clickhouse_connect')
def test_clickhouse_inserter_initialization_failure(mock_connect):
    """Test ClickHouse inserter handles connection failures gracefully"""
    # Mock connection failure
    mock_connect.get_client.side_effect = Exception("Connection failed")
    
    with pytest.raises(ConnectionError, match="Failed to connect to ClickHouse"):
        ClickHouseInserter()


def test_run_task_function():
    """Test that the task function can be called"""
    params = FocusBillingIngestParams(dry_run=True, max_files=0)
    
    # This should not raise an exception even with minimal setup
    # The actual execution will be mocked in integration tests
    with patch('app.focus_billing.workflow.FocusBillingIngestWorkflow') as mock_workflow_class:
        mock_workflow = MagicMock()
        mock_workflow.execute.return_value = WorkflowStats()
        mock_workflow_class.return_value = mock_workflow
        
        # Should not raise an exception
        run_focus_billing_ingest_task(params)
        
        # Verify workflow was created and executed
        mock_workflow_class.assert_called_once_with(params)
        mock_workflow.execute.assert_called_once()


if __name__ == "__main__":
    # Run basic tests
    test_workflow_params_creation()
    test_workflow_params_with_values()
    test_workflow_stats_creation()
    test_workflow_initialization()
    test_file_discovery_initialization()
    test_data_transformer_initialization()
    test_run_task_function()
    
    print("All basic workflow tests passed!")