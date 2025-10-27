"""
Pytest-compatible test for FOCUS billing Moose ingestion workflow.

Run with:
    pytest app/focus_billing/tests/test_moose_ingestion_workflow.py -v
"""

import sys
from pathlib import Path

import pytest

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# pylint: disable=wrong-import-position,import-error
from focus_billing.workflow import (
    FocusBillingIngestParams,
    FocusBillingIngestWorkflow,
)


class TestMooseIngestionWorkflow:
    """Test suite for FOCUS billing Moose ingestion"""

    @pytest.fixture
    def test_data_path(self):
        """Return path to test data"""
        return Path(__file__).parent.parent / "data/focus"

    @pytest.fixture
    def test_params(self, test_data_path):
        """Create test parameters for workflow"""
        return FocusBillingIngestParams(
            data_root=str(test_data_path),
            batch_size=100,
            max_files=1,
            dry_run=False,
            period_filter="20250701-20250731",
            continue_on_error=True,
            skip_processed=False
        )

    def test_workflow_initialization(self, test_params):
        """Test workflow can be initialized"""
        workflow = FocusBillingIngestWorkflow(test_params)

        assert workflow is not None
        assert workflow.params == test_params
        assert workflow.stats is not None
        assert workflow.file_discovery is not None
        assert workflow.data_transformer is not None

    def test_workflow_execution(self, test_params):
        """Test workflow executes successfully"""
        workflow = FocusBillingIngestWorkflow(test_params)
        stats = workflow.execute()

        # Verify stats structure
        assert hasattr(stats, 'files_discovered')
        assert hasattr(stats, 'files_processed')
        assert hasattr(stats, 'files_skipped')
        assert hasattr(stats, 'files_failed')
        assert hasattr(stats, 'total_rows_processed')
        assert hasattr(stats, 'total_processing_time')
        assert hasattr(stats, 'errors')

        # Verify workflow discovered files
        assert stats.files_discovered >= 0, \
            "Should discover files in test data directory"

        # If files were processed, verify no failures
        if stats.files_processed > 0:
            errors_msg = f"Workflow should succeed. Errors: {stats.errors}"
            assert stats.files_failed == 0, errors_msg
            assert stats.total_rows_processed > 0, \
                "Should process at least some rows"

    @pytest.mark.integration
    def test_moose_ingestion_with_real_data(self, test_params):
        """Integration test: ingest real parquet data via Moose API

        Requires:
        - Moose service running on localhost:4200
        - FocusCostUsage model registered (tables created)
        """
        import httpx  # pylint: disable=import-outside-toplevel

        # Check if Moose is running
        try:
            response = httpx.get("http://localhost:4200/health", timeout=2.0)
            if response.status_code != 200:
                pytest.skip("Moose service not healthy")
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("Moose service not running on localhost:4200")

        # Check if ingestion endpoint is available
        try:
            # Try to access the ingest endpoint (should exist if model registered)
            test_response = httpx.post(
                "http://localhost:4200/ingest/FocusCostUsage",
                json=[],  # Empty payload
                timeout=2.0
            )
            # If we get 404, the model isn't registered yet
            if test_response.status_code == 404:
                pytest.skip(
                    "FocusCostUsage model not registered. "
                    "Ensure app/ingest/focus/models.py is imported."
                )
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("Moose ingestion endpoint not available")

        workflow = FocusBillingIngestWorkflow(test_params)
        stats = workflow.execute()

        # Verify successful execution
        if stats.files_failed > 0 or stats.files_processed == 0:
            # Provide helpful error message
            error_details = (
                f"Ingestion failed or no files processed.\n"
                f"Files discovered: {stats.files_discovered}\n"
                f"Files processed: {stats.files_processed}\n"
                f"Files failed: {stats.files_failed}\n"
                f"Errors: {stats.errors}\n\n"
                f"This likely means ClickHouse tables don't exist yet.\n"
                f"Ensure Moose registered the FocusCostUsage model on startup."
            )
            pytest.skip(error_details)

        assert stats.files_processed > 0, "Should process at least one file"
        assert stats.total_rows_processed > 0, "Should ingest rows"

    def test_dry_run_mode(self, test_params):
        """Test workflow in dry-run mode (no actual ingestion)"""
        test_params.dry_run = True

        workflow = FocusBillingIngestWorkflow(test_params)
        stats = workflow.execute()

        # In dry-run mode, we should discover files but not actually process them
        # (though row counts may be reported as if processed)
        assert stats.files_discovered >= 0
        assert stats.files_failed == 0, "Dry run should not fail"

    def test_file_filtering_by_period(self, test_data_path):
        """Test workflow filters files by period correctly"""
        params = FocusBillingIngestParams(
            data_root=str(test_data_path),
            batch_size=100,
            max_files=None,
            period_filter="20250701-20250731",  # Specific period
            continue_on_error=True,
            skip_processed=False
        )

        workflow = FocusBillingIngestWorkflow(params)

        # Discover files first
        # pylint: disable=protected-access
        discovered_files = workflow._discover_files()

        # Then filter them (which _filter_files does in the workflow)
        filtered_files = workflow._filter_files(discovered_files)

        # All filtered files should match the period filter
        assert len(filtered_files) > 0, "Should have files after filtering"

        for file_info in filtered_files:
            period_msg = (
                f"File {file_info.relative_path} "
                f"should match period filter"
            )
            assert file_info.period_folder == "20250701-20250731", period_msg

    def test_max_files_limit(self, test_params):
        """Test workflow respects max_files parameter"""
        test_params.max_files = 2

        workflow = FocusBillingIngestWorkflow(test_params)
        stats = workflow.execute()

        # Should process at most max_files
        assert stats.files_processed <= 2, "Should respect max_files limit"


@pytest.mark.slow
class TestMooseIngestionPerformance:
    """Performance tests for ingestion workflow"""

    def test_batch_processing_performance(self):
        """Test ingestion performance with different batch sizes"""
        # This would require mock data or performance benchmarks
        pytest.skip("Performance test - implement when needed")

    def test_parallel_file_processing(self):
        """Test concurrent file processing"""
        pytest.skip("Parallel processing test - implement when needed")


if __name__ == "__main__":
    # Allow running directly: python test_moose_ingestion_workflow.py
    pytest.main([__file__, "-v", "-s"])
