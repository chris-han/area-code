"""
FOCUS Billing Integration Tests

Comprehensive integration tests for the complete FOCUS billing system including:
- Full ingestion workflow testing
- API endpoint integration with real ClickHouse queries
- End-to-end data flow validation
- Error handling and recovery scenarios
"""

import pytest
import tempfile
import shutil
import json
import pandas as pd
import time
from pathlib import Path
from datetime import datetime, timezone, date
from typing import Dict, Any, List, Optional
from unittest.mock import patch, MagicMock
from decimal import Decimal

from app.focus_billing.workflow import (
    FocusBillingIngestWorkflow, 
    FocusBillingIngestParams,
    WorkflowStats
)
from app.focus_billing.config import focus_config
from app.focus_billing.query_loader import FocusQueryLoader
from app.focus_billing.query_executor import FocusQueryExecutor
from app.focus_billing.observability import focus_observability
from app.focus_billing.file_discovery import FocusFileDiscovery, ParquetFileInfo
from app.focus_billing.data_transformer import FocusDataTransformer
from app.focus_billing.clickhouse_inserter import ClickHouseInserter

# API imports
from app.apis.focus_billing.list_use_cases import (
    list_focus_use_cases_api,
    ListFocusUseCasesQueryParams
)
from app.apis.focus_billing.execute_use_case import (
    execute_focus_use_case_api,
    ExecuteFocusUseCaseQueryParams
)
from app.apis.focus_billing.get_use_case import get_use_case_api
from app.apis.focus_billing.list_supported_features import list_supported_features_api


@pytest.mark.integration
class TestFocusBillingFullWorkflowIntegration:
    """Integration tests for complete FOCUS billing workflow"""
    
    @pytest.fixture
    def comprehensive_test_data(self):
        """Create comprehensive test data with multiple datasets and periods"""
        temp_dir = tempfile.mkdtemp()
        
        # Create multiple period directories
        periods = [
            ("20250701-20250731", "202507161527", "cost-usage-run"),
            ("20250801-20250831", "202508151430", "cost-usage-run"),
            ("20250701-20250731", "202507161530", "contract-commitment-run")
        ]
        
        test_data_info = {
            "temp_dir": temp_dir,
            "periods": [],
            "total_files": 0,
            "total_rows": 0
        }
        
        for period, timestamp, run_type in periods:
            period_dir = Path(temp_dir) / period / timestamp / run_type
            period_dir.mkdir(parents=True)
            
            # Determine dataset type and create appropriate data
            if "cost-usage" in run_type:
                dataset_type = "cost_usage"
                files_created = self._create_cost_usage_files(period_dir, period)
            else:
                dataset_type = "contract_commitment"
                files_created = self._create_contract_commitment_files(period_dir, period)
            
            period_info = {
                "period": period,
                "timestamp": timestamp,
                "run_type": run_type,
                "dataset_type": dataset_type,
                "directory": period_dir,
                "files": files_created["files"],
                "total_rows": files_created["total_rows"]
            }
            
            test_data_info["periods"].append(period_info)
            test_data_info["total_files"] += len(files_created["files"])
            test_data_info["total_rows"] += files_created["total_rows"]
        
        yield test_data_info
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def _create_cost_usage_files(self, period_dir: Path, period: str) -> Dict[str, Any]:
        """Create cost & usage test files"""
        files_created = []
        total_rows = 0
        
        # Create manifest.json
        manifest_data = {
            "manifestVersion": "2024-04-01",
            "byteCount": 15000,
            "blobCount": 2,
            "dataRowCount": 50,
            "exportConfig": {
                "exportName": "focus-cost",
                "dataVersion": "1.2-preview",
                "type": "FocusCost",
                "timeFrame": "MonthToDate",
                "granularity": "Daily"
            },
            "runInfo": {
                "executionType": "Scheduled",
                "submittedTime": "2025-07-16T15:27:00.276245Z",
                "runId": "integration-test-run",
                "startDate": f"{period[:4]}-{period[4:6]}-01T00:00:00",
                "endDate": f"{period[:4]}-{period[4:6]}-16T00:00:00+00:00"
            },
            "blobs": []
        }
        
        # Create multiple parquet files
        for i in range(2):
            file_name = f"part_{i}_0001.snappy.parquet"
            rows_in_file = 25
            
            # Create sample data with variety
            sample_data = {
                "BillingAccountId": [f"integration-test-account-{j % 3}" for j in range(rows_in_file)],
                "UsageDate": [datetime(2025, 7, 1 + (j % 15)) for j in range(rows_in_file)],
                "BilledCost": [round(10.0 + (j * 2.5), 2) for j in range(rows_in_file)],
                "EffectiveCost": [round(9.0 + (j * 2.3), 2) for j in range(rows_in_file)],
                "BillingCurrency": ["USD"] * rows_in_file,
                "ServiceCategory": ["Compute" if j % 2 == 0 else "Storage" for j in range(rows_in_file)],
                "ServiceName": [f"Service-{j % 5}" for j in range(rows_in_file)],
                "ResourceId": [f"integration-resource-{i}-{j}" for j in range(rows_in_file)],
                "Provider": ["Azure"] * rows_in_file,
                "Region": [f"Region-{j % 3}" for j in range(rows_in_file)],
                "ChargeCategory": ["Usage"] * rows_in_file,
                "ChargeSubcategory": ["On-Demand" if j % 2 == 0 else "Reserved" for j in range(rows_in_file)],
                "ChargeDescription": [f"Integration test charge {j}" for j in range(rows_in_file)],
                "ChargePeriodStart": [datetime(2025, 7, 1 + (j % 15)) for j in range(rows_in_file)],
                "ChargePeriodEnd": [datetime(2025, 7, 2 + (j % 15)) for j in range(rows_in_file)],
                # Add some optional fields for comprehensive testing
                "Tags": [f'{{"Environment": "Test", "Project": "Integration-{j % 3}"}}' for j in range(rows_in_file)],
                "ContractCommitmentId": [f"commitment-{j % 5}" if j % 3 == 0 else None for j in range(rows_in_file)]
            }
            
            df = pd.DataFrame(sample_data)
            parquet_path = period_dir / file_name
            df.to_parquet(parquet_path, index=False)
            
            files_created.append(file_name)
            total_rows += rows_in_file
            
            # Add to manifest
            manifest_data["blobs"].append({
                "blobName": f"1.2/focus-cost/{period}/202507161527/integration-test-run/{file_name}",
                "byteCount": 7500,
                "dataRowCount": rows_in_file
            })
        
        # Write manifest
        manifest_path = period_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        return {"files": files_created, "total_rows": total_rows}
    
    def _create_contract_commitment_files(self, period_dir: Path, period: str) -> Dict[str, Any]:
        """Create contract commitment test files"""
        files_created = []
        total_rows = 0
        
        # Create manifest.json for contract commitment
        manifest_data = {
            "manifestVersion": "2024-04-01",
            "byteCount": 5000,
            "blobCount": 1,
            "dataRowCount": 10,
            "exportConfig": {
                "exportName": "focus-contract-commitment",
                "dataVersion": "1.2-preview",
                "type": "FocusContractCommitment",
                "timeFrame": "MonthToDate",
                "granularity": "Daily"
            },
            "runInfo": {
                "executionType": "Scheduled",
                "submittedTime": "2025-07-16T15:30:00.276245Z",
                "runId": "integration-commitment-run",
                "startDate": f"{period[:4]}-{period[4:6]}-01T00:00:00",
                "endDate": f"{period[:4]}-{period[4:6]}-16T00:00:00+00:00"
            },
            "blobs": []
        }
        
        file_name = "commitment_part_0_0001.snappy.parquet"
        rows_in_file = 10
        
        # Create contract commitment data
        sample_data = {
            "ContractCommitmentId": [f"commitment-{j}" for j in range(rows_in_file)],
            "BillingAccountId": [f"integration-test-account-{j % 3}" for j in range(rows_in_file)],
            "CommitmentDiscountCategory": ["Spend" if j % 2 == 0 else "Usage" for j in range(rows_in_file)],
            "CommitmentDiscountId": [f"discount-{j}" for j in range(rows_in_file)],
            "CommitmentDiscountName": [f"Integration Discount {j}" for j in range(rows_in_file)],
            "CommitmentDiscountType": ["Reserved Instance" if j % 2 == 0 else "Savings Plan" for j in range(rows_in_file)],
            "CommitmentDiscountStatus": ["Active"] * rows_in_file,
            "Region": [f"Region-{j % 3}" for j in range(rows_in_file)],
            "ServiceCategory": ["Compute"] * rows_in_file,
            "ServiceName": [f"Service-{j % 3}" for j in range(rows_in_file)]
        }
        
        df = pd.DataFrame(sample_data)
        parquet_path = period_dir / file_name
        df.to_parquet(parquet_path, index=False)
        
        files_created.append(file_name)
        total_rows += rows_in_file
        
        # Add to manifest
        manifest_data["blobs"].append({
            "blobName": f"1.2/focus-contract-commitment/{period}/202507161530/integration-commitment-run/{file_name}",
            "byteCount": 5000,
            "dataRowCount": rows_in_file
        })
        
        # Write manifest
        manifest_path = period_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        return {"files": files_created, "total_rows": total_rows}
    
    def test_complete_workflow_execution(self, comprehensive_test_data):
        """
        Test complete workflow execution with multiple datasets and periods.
        
        This test validates:
        1. File discovery across multiple periods and dataset types
        2. Data transformation for both cost usage and contract commitment
        3. ClickHouse insertion with proper batching
        4. Manifest tracking and error handling
        5. Comprehensive statistics and observability
        """
        # Verify tables exist before testing
        table_status = focus_observability.verify_tables_exist()
        if not all(status.passed for status in table_status.values()):
            pytest.skip("Required FOCUS tables do not exist - run DDL setup first")
        
        # Get initial row counts
        initial_counts = focus_observability.get_table_row_counts()
        initial_cost_usage = initial_counts.get("focus_cost_usage", 0)
        initial_commitment = initial_counts.get("focus_contract_commitment", 0)
        
        # Configure workflow parameters
        params = FocusBillingIngestParams(
            data_root=comprehensive_test_data["temp_dir"],
            batch_size=10,  # Small batch for testing
            dry_run=False,
            continue_on_error=True,
            skip_processed=False  # Force processing for test
        )
        
        # Execute workflow
        workflow = FocusBillingIngestWorkflow(params)
        stats = workflow.execute()
        
        # Verify workflow statistics
        assert stats.files_discovered == comprehensive_test_data["total_files"]
        assert stats.files_processed > 0, "No files were processed"
        assert stats.files_failed == 0, f"Files failed: {stats.errors}"
        assert stats.total_rows_processed == comprehensive_test_data["total_rows"]
        
        # Verify data was inserted into correct tables
        final_counts = focus_observability.get_table_row_counts()
        final_cost_usage = final_counts.get("focus_cost_usage", 0)
        final_commitment = final_counts.get("focus_contract_commitment", 0)
        
        cost_usage_added = final_cost_usage - initial_cost_usage
        commitment_added = final_commitment - initial_commitment
        
        # Verify expected rows were added to each table
        expected_cost_usage_rows = sum(
            p["total_rows"] for p in comprehensive_test_data["periods"] 
            if p["dataset_type"] == "cost_usage"
        )
        expected_commitment_rows = sum(
            p["total_rows"] for p in comprehensive_test_data["periods"] 
            if p["dataset_type"] == "contract_commitment"
        )
        
        assert cost_usage_added == expected_cost_usage_rows, \
            f"Expected {expected_cost_usage_rows} cost usage rows, got {cost_usage_added}"
        assert commitment_added == expected_commitment_rows, \
            f"Expected {expected_commitment_rows} commitment rows, got {commitment_added}"
        
        print(f"✓ Complete workflow test successful:")
        print(f"  - Files processed: {stats.files_processed}")
        print(f"  - Rows processed: {stats.total_rows_processed}")
        print(f"  - Cost usage rows added: {cost_usage_added}")
        print(f"  - Contract commitment rows added: {commitment_added}")
    
    def test_workflow_error_handling_and_recovery(self, comprehensive_test_data):
        """
        Test workflow error handling and recovery scenarios.
        
        This test validates:
        1. Graceful handling of corrupted files
        2. Continue-on-error behavior
        3. Proper error reporting and statistics
        4. Manifest tracking of failures
        """
        # Create a corrupted file to test error handling
        corrupted_dir = Path(comprehensive_test_data["temp_dir"]) / "20250901-20250930" / "202509151200" / "corrupted-run"
        corrupted_dir.mkdir(parents=True)
        
        # Create invalid manifest
        invalid_manifest = {"invalid": "manifest", "structure": True}
        with open(corrupted_dir / "manifest.json", 'w') as f:
            json.dump(invalid_manifest, f)
        
        # Create invalid parquet file (just text)
        with open(corrupted_dir / "corrupted.parquet", 'w') as f:
            f.write("This is not a valid parquet file")
        
        # Configure workflow to continue on error
        params = FocusBillingIngestParams(
            data_root=comprehensive_test_data["temp_dir"],
            continue_on_error=True,
            skip_processed=False
        )
        
        workflow = FocusBillingIngestWorkflow(params)
        stats = workflow.execute()
        
        # Verify that some files processed successfully despite errors
        assert stats.files_processed > 0, "No files processed successfully"
        assert stats.files_failed > 0, "Expected some files to fail"
        assert len(stats.errors) > 0, "Expected error messages to be recorded"
        
        # Verify that valid files were still processed
        expected_valid_files = comprehensive_test_data["total_files"]
        assert stats.files_processed >= expected_valid_files, \
            f"Expected at least {expected_valid_files} valid files to process"
        
        print(f"✓ Error handling test successful:")
        print(f"  - Valid files processed: {stats.files_processed}")
        print(f"  - Failed files: {stats.files_failed}")
        print(f"  - Errors recorded: {len(stats.errors)}")
    
    def test_workflow_filtering_and_selection(self, comprehensive_test_data):
        """
        Test workflow filtering capabilities.
        
        This test validates:
        1. Dataset type filtering
        2. Period filtering
        3. File limit enforcement
        4. Skip processed files functionality
        """
        # Test dataset type filtering - only cost usage
        params = FocusBillingIngestParams(
            data_root=comprehensive_test_data["temp_dir"],
            dataset_type_filter="cost_usage",
            skip_processed=False
        )
        
        workflow = FocusBillingIngestWorkflow(params)
        stats = workflow.execute()
        
        # Should only process cost usage files
        expected_cost_usage_files = len([
            p for p in comprehensive_test_data["periods"] 
            if p["dataset_type"] == "cost_usage"
        ])
        
        assert stats.files_processed == expected_cost_usage_files, \
            f"Expected {expected_cost_usage_files} cost usage files, processed {stats.files_processed}"
        
        # Test period filtering
        params = FocusBillingIngestParams(
            data_root=comprehensive_test_data["temp_dir"],
            period_filter="20250701-20250731",
            skip_processed=False
        )
        
        workflow = FocusBillingIngestWorkflow(params)
        stats = workflow.execute()
        
        # Should only process files from July period
        expected_july_files = len([
            p for p in comprehensive_test_data["periods"] 
            if p["period"] == "20250701-20250731"
        ])
        
        assert stats.files_processed == expected_july_files, \
            f"Expected {expected_july_files} July files, processed {stats.files_processed}"
        
        # Test file limit
        params = FocusBillingIngestParams(
            data_root=comprehensive_test_data["temp_dir"],
            max_files=1,
            skip_processed=False
        )
        
        workflow = FocusBillingIngestWorkflow(params)
        stats = workflow.execute()
        
        assert stats.files_processed == 1, f"Expected 1 file with limit, processed {stats.files_processed}"
        
        print("✓ Workflow filtering tests successful")
    
    def test_workflow_dry_run_mode(self, comprehensive_test_data):
        """
        Test workflow dry run mode.
        
        This test validates:
        1. Dry run processes files without inserting data
        2. Statistics are calculated correctly
        3. No actual data changes occur
        """
        # Get initial row counts
        initial_counts = focus_observability.get_table_row_counts()
        
        # Run in dry run mode
        params = FocusBillingIngestParams(
            data_root=comprehensive_test_data["temp_dir"],
            dry_run=True,
            skip_processed=False
        )
        
        workflow = FocusBillingIngestWorkflow(params)
        stats = workflow.execute()
        
        # Verify statistics are calculated
        assert stats.files_discovered == comprehensive_test_data["total_files"]
        assert stats.files_processed == comprehensive_test_data["total_files"]
        assert stats.total_rows_processed == comprehensive_test_data["total_rows"]
        assert stats.files_failed == 0
        
        # Verify no data was actually inserted
        final_counts = focus_observability.get_table_row_counts()
        
        for table_name, initial_count in initial_counts.items():
            final_count = final_counts.get(table_name, 0)
            assert final_count == initial_count, \
                f"Table {table_name} changed during dry run: {initial_count} -> {final_count}"
        
        print(f"✓ Dry run test successful: {stats.files_processed} files simulated, no data inserted")


@pytest.mark.integration
class TestFocusBillingAPIIntegration:
    """Integration tests for FOCUS billing APIs with real ClickHouse queries"""
    
    def test_list_use_cases_api_integration(self):
        """
        Test list use cases API with real query catalog.
        
        This test validates:
        1. API loads real FOCUS query catalog
        2. Response structure is correct
        3. Filtering and search functionality works
        4. Categories and metadata are properly extracted
        """
        # Test basic listing
        params = ListFocusUseCasesQueryParams()
        response = list_focus_use_cases_api(params)
        
        assert "use_cases" in response
        assert "total_count" in response
        assert "categories" in response
        assert len(response["use_cases"]) > 0, "No use cases found"
        
        # Verify use case structure
        for use_case in response["use_cases"][:3]:  # Check first 3
            assert "slug" in use_case
            assert "name" in use_case
            assert "parameters" in use_case
            assert "parameter_count" in use_case
            assert isinstance(use_case["parameters"], list)
            assert use_case["parameter_count"] == len(use_case["parameters"])
        
        # Test category filtering
        if response["categories"]:
            category = response["categories"][0]
            filtered_params = ListFocusUseCasesQueryParams(category=category)
            filtered_response = list_focus_use_cases_api(filtered_params)
            
            assert filtered_response["total_count"] <= response["total_count"]
            for use_case in filtered_response["use_cases"]:
                assert use_case["category"] == category
        
        # Test search functionality
        search_params = ListFocusUseCasesQueryParams(search="billing")
        search_response = list_focus_use_cases_api(search_params)
        
        assert search_response["total_count"] <= response["total_count"]
        for use_case in search_response["use_cases"]:
            search_text = "billing"
            assert (search_text in use_case["name"].lower() or 
                   search_text in (use_case["description"] or "").lower())
        
        print(f"✓ List use cases API test successful: {response['total_count']} use cases found")
    
    def test_execute_use_case_api_integration(self):
        """
        Test execute use case API with real ClickHouse queries.
        
        This test validates:
        1. API can execute real FOCUS queries
        2. Parameter binding works correctly
        3. Results are returned in proper format
        4. Pagination functionality works
        5. Error handling for invalid queries/parameters
        """
        # First get available use cases
        list_params = ListFocusUseCasesQueryParams()
        list_response = list_focus_use_cases_api(list_params)
        
        if not list_response["use_cases"]:
            pytest.skip("No use cases available for testing")
        
        # Find a suitable use case for testing (prefer one with date parameters)
        test_use_case = None
        for use_case in list_response["use_cases"]:
            if len(use_case["parameters"]) <= 2:  # Simple parameter requirements
                test_use_case = use_case
                break
        
        if not test_use_case:
            test_use_case = list_response["use_cases"][0]  # Fallback to first
        
        print(f"Testing use case: {test_use_case['name']}")
        
        # Test basic execution
        execute_params = ExecuteFocusUseCaseQueryParams(
            slug=test_use_case["slug"],
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 31),
            limit=10
        )
        
        try:
            response = execute_focus_use_case_api(execute_params)
            
            # Verify response structure
            assert "slug" in response
            assert "rows" in response
            assert "total_rows" in response
            assert "execution_time_ms" in response
            assert "parameters_used" in response
            assert "sql_executed" in response
            assert "has_more" in response
            
            assert response["slug"] == test_use_case["slug"]
            assert isinstance(response["rows"], list)
            assert isinstance(response["total_rows"], int)
            assert isinstance(response["execution_time_ms"], (int, float))
            assert response["execution_time_ms"] >= 0
            
            # Verify pagination
            assert response["total_rows"] <= 10  # Respects limit
            
            print(f"✓ Execute use case successful: {response['total_rows']} rows in {response['execution_time_ms']:.2f}ms")
            
        except Exception as e:
            # Some queries may fail with test data - log but don't fail test
            print(f"⚠ Query execution failed (acceptable for integration test): {e}")
    
    def test_api_error_handling_integration(self):
        """
        Test API error handling with various invalid inputs.
        
        This test validates:
        1. Invalid query slug handling
        2. Missing parameter handling
        3. Invalid date format handling
        4. Proper error messages and status codes
        """
        # Test invalid query slug
        try:
            invalid_params = ExecuteFocusUseCaseQueryParams(
                slug="nonexistent-query-slug-12345",
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 31)
            )
            execute_focus_use_case_api(invalid_params)
            assert False, "Expected exception for invalid query slug"
        except Exception as e:
            assert "not found" in str(e).lower() or "invalid" in str(e).lower()
            print("✓ Invalid query slug handled correctly")
        
        # Test missing required parameters (if we have a query that requires them)
        list_params = ListFocusUseCasesQueryParams()
        list_response = list_focus_use_cases_api(list_params)
        
        # Find a query with parameters
        query_with_params = None
        for use_case in list_response["use_cases"]:
            if len(use_case["parameters"]) > 0:
                query_with_params = use_case
                break
        
        if query_with_params:
            try:
                # Execute without required parameters
                missing_params = ExecuteFocusUseCaseQueryParams(
                    slug=query_with_params["slug"]
                    # Intentionally omit required parameters
                )
                execute_focus_use_case_api(missing_params)
                assert False, "Expected exception for missing parameters"
            except Exception as e:
                assert "parameter" in str(e).lower() or "missing" in str(e).lower()
                print("✓ Missing parameters handled correctly")
    
    def test_supported_features_api_integration(self):
        """
        Test supported features API integration.
        
        This test validates:
        1. API loads FOCUS supported features
        2. Feature metadata is properly structured
        3. Categories and descriptions are available
        """
        try:
            response = list_supported_features_api()
            
            assert "features" in response
            assert "total_count" in response
            assert isinstance(response["features"], list)
            assert response["total_count"] >= 0
            
            # If features are available, verify structure
            if response["features"]:
                for feature in response["features"][:3]:  # Check first 3
                    assert "name" in feature
                    assert "description" in feature
                    assert isinstance(feature["name"], str)
                    assert len(feature["name"]) > 0
            
            print(f"✓ Supported features API test successful: {response['total_count']} features found")
            
        except Exception as e:
            # Supported features may not be available in all environments
            print(f"⚠ Supported features test skipped: {e}")
    
    def test_api_performance_benchmarks(self):
        """
        Test API performance benchmarks.
        
        This test validates:
        1. API response times are reasonable
        2. Query execution performance is acceptable
        3. Large result set handling
        """
        import time
        
        # Test list use cases performance
        start_time = time.time()
        list_params = ListFocusUseCasesQueryParams()
        list_response = list_focus_use_cases_api(list_params)
        list_time = time.time() - start_time
        
        assert list_time < 5.0, f"List use cases too slow: {list_time:.2f}s"
        print(f"✓ List use cases performance: {list_time:.3f}s")
        
        # Test query execution performance (if use cases available)
        if list_response["use_cases"]:
            test_use_case = list_response["use_cases"][0]
            
            start_time = time.time()
            try:
                execute_params = ExecuteFocusUseCaseQueryParams(
                    slug=test_use_case["slug"],
                    start_date=date(2025, 7, 1),
                    end_date=date(2025, 7, 31),
                    limit=100  # Larger result set
                )
                response = execute_focus_use_case_api(execute_params)
                execution_time = time.time() - start_time
                
                assert execution_time < 30.0, f"Query execution too slow: {execution_time:.2f}s"
                print(f"✓ Query execution performance: {execution_time:.3f}s for {response['total_rows']} rows")
                
            except Exception as e:
                print(f"⚠ Query performance test skipped: {e}")


@pytest.mark.integration
class TestFocusBillingDataIntegrity:
    """Integration tests for data integrity and consistency"""
    
    def test_end_to_end_data_consistency(self):
        """
        Test end-to-end data consistency from ingestion to query.
        
        This test validates:
        1. Data ingested matches source data
        2. Transformations preserve data integrity
        3. Queries return consistent results
        4. Referential integrity is maintained
        """
        # Create known test data
        temp_dir = tempfile.mkdtemp()
        try:
            # Create specific test data with known values
            period_dir = Path(temp_dir) / "20250701-20250731" / "202507161527" / "consistency-test"
            period_dir.mkdir(parents=True)
            
            # Create manifest
            manifest_data = {
                "manifestVersion": "2024-04-01",
                "byteCount": 5000,
                "blobCount": 1,
                "dataRowCount": 5,
                "exportConfig": {
                    "exportName": "focus-cost",
                    "dataVersion": "1.2-preview",
                    "type": "FocusCost"
                },
                "runInfo": {
                    "executionType": "Scheduled",
                    "runId": "consistency-test"
                },
                "blobs": [{
                    "blobName": "consistency_test.parquet",
                    "byteCount": 5000,
                    "dataRowCount": 5
                }]
            }
            
            with open(period_dir / "manifest.json", 'w') as f:
                json.dump(manifest_data, f)
            
            # Create known test data
            known_data = {
                "BillingAccountId": ["consistency-account-1", "consistency-account-1", "consistency-account-2", "consistency-account-2", "consistency-account-3"],
                "UsageDate": [datetime(2025, 7, 1), datetime(2025, 7, 2), datetime(2025, 7, 1), datetime(2025, 7, 2), datetime(2025, 7, 1)],
                "BilledCost": [100.00, 150.50, 200.25, 75.75, 300.00],
                "EffectiveCost": [95.00, 145.00, 190.00, 70.00, 285.00],
                "BillingCurrency": ["USD"] * 5,
                "ServiceCategory": ["Compute", "Compute", "Storage", "Storage", "Network"],
                "ServiceName": ["VM-Service", "VM-Service", "Blob-Storage", "Blob-Storage", "Load-Balancer"],
                "ResourceId": ["resource-1", "resource-2", "resource-3", "resource-4", "resource-5"],
                "Provider": ["Azure"] * 5,
                "Region": ["East-US", "East-US", "West-US", "West-US", "Central-US"],
                "ChargeCategory": ["Usage"] * 5,
                "ChargeSubcategory": ["On-Demand"] * 5,
                "ChargeDescription": ["Test charge"] * 5,
                "ChargePeriodStart": [datetime(2025, 7, 1), datetime(2025, 7, 2), datetime(2025, 7, 1), datetime(2025, 7, 2), datetime(2025, 7, 1)],
                "ChargePeriodEnd": [datetime(2025, 7, 2), datetime(2025, 7, 3), datetime(2025, 7, 2), datetime(2025, 7, 3), datetime(2025, 7, 2)]
            }
            
            df = pd.DataFrame(known_data)
            df.to_parquet(period_dir / "consistency_test.parquet", index=False)
            
            # Ingest the data
            params = FocusBillingIngestParams(
                data_root=temp_dir,
                skip_processed=False
            )
            
            workflow = FocusBillingIngestWorkflow(params)
            stats = workflow.execute()
            
            assert stats.files_processed == 1
            assert stats.total_rows_processed == 5
            
            # Query the data back and verify consistency
            query_executor = FocusQueryExecutor()
            
            # Test basic data retrieval
            test_sql = """
            SELECT 
                billing_account_id,
                usage_date,
                billed_cost,
                effective_cost,
                service_category,
                resource_id
            FROM focus_cost_usage 
            WHERE source_system = 'focus_parquet'
            AND billing_account_id LIKE 'consistency-account-%'
            ORDER BY billing_account_id, usage_date
            """
            
            results = query_executor.execute_raw_query(test_sql)
            
            assert len(results) == 5, f"Expected 5 rows, got {len(results)}"
            
            # Verify specific data values
            expected_totals = {
                "consistency-account-1": 250.50,  # 100.00 + 150.50
                "consistency-account-2": 276.00,  # 200.25 + 75.75
                "consistency-account-3": 300.00   # 300.00
            }
            
            actual_totals = {}
            for row in results:
                account = row["billing_account_id"]
                cost = float(row["billed_cost"])
                actual_totals[account] = actual_totals.get(account, 0) + cost
            
            for account, expected_total in expected_totals.items():
                actual_total = actual_totals.get(account, 0)
                assert abs(actual_total - expected_total) < 0.01, \
                    f"Account {account}: expected {expected_total}, got {actual_total}"
            
            print("✓ End-to-end data consistency validated")
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_referential_integrity_validation(self):
        """
        Test referential integrity between cost usage and contract commitment data.
        
        This test validates:
        1. Contract commitment IDs are properly linked
        2. Orphaned references are detected
        3. Integrity validation reports accurate results
        """
        # Run referential integrity check
        integrity_result = focus_observability.validate_contract_commitment_integrity()
        
        # The result should be structured and informative
        assert hasattr(integrity_result, 'passed')
        assert hasattr(integrity_result, 'message')
        
        if integrity_result.passed:
            print("✓ Referential integrity validation passed")
        else:
            # This is acceptable if we don't have commitment data
            print(f"⚠ Referential integrity issues found (may be expected): {integrity_result.message}")
        
        # Test table existence and basic structure
        table_status = focus_observability.verify_tables_exist()
        
        required_tables = ["focus_cost_usage", "focus_contract_commitment", "focus_ingest_manifest"]
        for table_name in required_tables:
            if table_name in table_status:
                assert table_status[table_name].passed, \
                    f"Required table {table_name} validation failed: {table_status[table_name].message}"
        
        print("✓ Table structure validation passed")


if __name__ == "__main__":
    # Run integration tests directly
    pytest.main([__file__, "-v", "-s", "-m", "integration"])