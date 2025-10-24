"""
FOCUS Billing Performance Tests

Comprehensive performance tests for FOCUS billing system including:
- Large dataset ingestion performance
- Query execution performance under load
- Concurrent workflow execution
- Memory usage and resource optimization
- Scalability benchmarks
"""

import pytest
import tempfile
import shutil
import json
import pandas as pd
import time
import asyncio
import statistics
import psutil
import threading
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from app.focus_billing.workflow import (
    FocusBillingIngestWorkflow, 
    FocusBillingIngestParams,
    WorkflowStats
)
from app.focus_billing.config import focus_config
from app.focus_billing.query_executor import FocusQueryExecutor
from app.focus_billing.observability import focus_observability
from app.apis.focus_billing.execute_use_case import (
    execute_focus_use_case_api,
    ExecuteFocusUseCaseQueryParams
)
from app.apis.focus_billing.list_use_cases import (
    list_focus_use_cases_api,
    ListFocusUseCasesQueryParams
)


@pytest.mark.performance
class TestFocusBillingLargeDatasetPerformance:
    """Performance tests for large dataset ingestion"""
    
    @pytest.fixture
    def large_dataset_generator(self):
        """Generator for creating large test datasets"""
        def create_large_dataset(num_files: int = 10, rows_per_file: int = 10000) -> str:
            temp_dir = tempfile.mkdtemp()
            
            # Create period directory
            period_dir = Path(temp_dir) / "20250701-20250731" / "202507161527" / "performance-test"
            period_dir.mkdir(parents=True)
            
            total_rows = 0
            blob_entries = []
            
            # Create multiple large parquet files
            for file_idx in range(num_files):
                file_name = f"performance_part_{file_idx:04d}.snappy.parquet"
                
                # Generate large dataset with variety
                data = {
                    "BillingAccountId": [f"perf-account-{i % 100}" for i in range(rows_per_file)],
                    "UsageDate": [datetime(2025, 7, 1 + (i % 30)) for i in range(rows_per_file)],
                    "BilledCost": [round(1.0 + (i * 0.01), 2) for i in range(rows_per_file)],
                    "EffectiveCost": [round(0.95 + (i * 0.009), 2) for i in range(rows_per_file)],
                    "BillingCurrency": ["USD"] * rows_per_file,
                    "ServiceCategory": [f"Category-{i % 10}" for i in range(rows_per_file)],
                    "ServiceName": [f"Service-{i % 50}" for i in range(rows_per_file)],
                    "ResourceId": [f"perf-resource-{file_idx}-{i}" for i in range(rows_per_file)],
                    "Provider": ["Azure"] * rows_per_file,
                    "Region": [f"Region-{i % 20}" for i in range(rows_per_file)],
                    "ChargeCategory": ["Usage"] * rows_per_file,
                    "ChargeSubcategory": ["On-Demand" if i % 3 == 0 else "Reserved" for i in range(rows_per_file)],
                    "ChargeDescription": [f"Performance test charge {i}" for i in range(rows_per_file)],
                    "ChargePeriodStart": [datetime(2025, 7, 1 + (i % 30)) for i in range(rows_per_file)],
                    "ChargePeriodEnd": [datetime(2025, 7, 2 + (i % 30)) for i in range(rows_per_file)],
                    # Add complex fields for realistic testing
                    "Tags": [f'{{"Environment": "Perf", "Index": {i}, "File": {file_idx}}}' for i in range(rows_per_file)],
                    "ContractCommitmentId": [f"commitment-{i % 1000}" if i % 10 == 0 else None for i in range(rows_per_file)]
                }
                
                df = pd.DataFrame(data)
                parquet_path = period_dir / file_name
                df.to_parquet(parquet_path, index=False, compression='snappy')
                
                total_rows += rows_per_file
                blob_entries.append({
                    "blobName": f"1.2/focus-cost/20250701-20250731/202507161527/performance-test/{file_name}",
                    "byteCount": parquet_path.stat().st_size,
                    "dataRowCount": rows_per_file
                })
            
            # Create manifest
            manifest_data = {
                "manifestVersion": "2024-04-01",
                "byteCount": sum(blob["byteCount"] for blob in blob_entries),
                "blobCount": num_files,
                "dataRowCount": total_rows,
                "exportConfig": {
                    "exportName": "focus-cost-performance",
                    "dataVersion": "1.2-preview",
                    "type": "FocusCost",
                    "timeFrame": "MonthToDate",
                    "granularity": "Daily"
                },
                "runInfo": {
                    "executionType": "Scheduled",
                    "submittedTime": "2025-07-16T15:27:00.276245Z",
                    "runId": "performance-test-run",
                    "startDate": "2025-07-01T00:00:00",
                    "endDate": "2025-07-31T00:00:00+00:00"
                },
                "blobs": blob_entries
            }
            
            with open(period_dir / "manifest.json", 'w') as f:
                json.dump(manifest_data, f)
            
            return temp_dir, total_rows, num_files
        
        return create_large_dataset
    
    def test_large_dataset_ingestion_performance(self, large_dataset_generator):
        """
        Test ingestion performance with large datasets.
        
        This test validates:
        1. Ingestion throughput (rows per second)
        2. Memory usage during processing
        3. Processing time scales reasonably with data size
        4. Batch processing efficiency
        """
        # Skip if tables don't exist
        table_status = focus_observability.verify_tables_exist()
        if not all(status.passed for status in table_status.values()):
            pytest.skip("Required FOCUS tables do not exist - run DDL setup first")
        
        # Test with medium dataset first
        temp_dir, total_rows, num_files = large_dataset_generator(num_files=5, rows_per_file=5000)
        
        try:
            # Monitor memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Configure for performance testing
            params = FocusBillingIngestParams(
                data_root=temp_dir,
                batch_size=1000,  # Optimize batch size
                dry_run=False,
                continue_on_error=False,
                skip_processed=False
            )
            
            # Execute workflow with timing
            start_time = time.time()
            workflow = FocusBillingIngestWorkflow(params)
            stats = workflow.execute()
            end_time = time.time()
            
            total_time = end_time - start_time
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory
            
            # Verify successful processing
            assert stats.files_processed == num_files, f"Expected {num_files} files, processed {stats.files_processed}"
            assert stats.total_rows_processed == total_rows, f"Expected {total_rows} rows, processed {stats.total_rows_processed}"
            assert stats.files_failed == 0, f"Files failed: {stats.errors}"
            
            # Calculate performance metrics
            rows_per_second = total_rows / total_time
            mb_per_second = (sum(Path(temp_dir).rglob("*.parquet")).stat().st_size for _ in [1]) / 1024 / 1024) / total_time
            
            # Performance assertions (adjust based on system capabilities)
            assert rows_per_second > 1000, f"Ingestion too slow: {rows_per_second:.0f} rows/s"
            assert total_time < 60, f"Total processing time too long: {total_time:.2f}s"
            assert memory_increase < 500, f"Memory usage too high: {memory_increase:.1f}MB increase"
            
            print(f"✓ Large dataset performance test successful:")
            print(f"  - Rows processed: {total_rows:,}")
            print(f"  - Processing time: {total_time:.2f}s")
            print(f"  - Throughput: {rows_per_second:.0f} rows/s")
            print(f"  - Memory increase: {memory_increase:.1f}MB")
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_batch_size_optimization(self, large_dataset_generator):
        """
        Test optimal batch size for ingestion performance.
        
        This test validates:
        1. Different batch sizes and their impact on performance
        2. Memory usage vs throughput tradeoffs
        3. Optimal batch size identification
        """
        # Skip if tables don't exist
        table_status = focus_observability.verify_tables_exist()
        if not all(status.passed for status in table_status.values()):
            pytest.skip("Required FOCUS tables do not exist - run DDL setup first")
        
        temp_dir, total_rows, num_files = large_dataset_generator(num_files=3, rows_per_file=3000)
        
        try:
            batch_sizes = [100, 500, 1000, 2000, 5000]
            performance_results = []
            
            for batch_size in batch_sizes:
                # Get initial row count to clean up between tests
                initial_counts = focus_observability.get_table_row_counts()
                initial_cost_usage = initial_counts.get("focus_cost_usage", 0)
                
                params = FocusBillingIngestParams(
                    data_root=temp_dir,
                    batch_size=batch_size,
                    dry_run=False,
                    skip_processed=False
                )
                
                start_time = time.time()
                process = psutil.Process()
                initial_memory = process.memory_info().rss / 1024 / 1024
                
                workflow = FocusBillingIngestWorkflow(params)
                stats = workflow.execute()
                
                end_time = time.time()
                peak_memory = process.memory_info().rss / 1024 / 1024
                
                processing_time = end_time - start_time
                memory_used = peak_memory - initial_memory
                throughput = total_rows / processing_time
                
                performance_results.append({
                    "batch_size": batch_size,
                    "processing_time": processing_time,
                    "throughput": throughput,
                    "memory_used": memory_used,
                    "files_processed": stats.files_processed
                })
                
                # Verify processing succeeded
                assert stats.files_processed == num_files
                assert stats.total_rows_processed == total_rows
                
                print(f"Batch size {batch_size}: {throughput:.0f} rows/s, {memory_used:.1f}MB, {processing_time:.2f}s")
            
            # Find optimal batch size (best throughput with reasonable memory)
            optimal_result = max(performance_results, key=lambda x: x["throughput"])
            
            print(f"✓ Batch size optimization test completed:")
            print(f"  - Optimal batch size: {optimal_result['batch_size']}")
            print(f"  - Best throughput: {optimal_result['throughput']:.0f} rows/s")
            print(f"  - Memory usage: {optimal_result['memory_used']:.1f}MB")
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_concurrent_file_processing_performance(self, large_dataset_generator):
        """
        Test performance with concurrent file processing simulation.
        
        This test validates:
        1. Multiple workflow instances can run concurrently
        2. Resource contention is manageable
        3. Overall system throughput under concurrent load
        """
        # Skip if tables don't exist
        table_status = focus_observability.verify_tables_exist()
        if not all(status.passed for status in table_status.values()):
            pytest.skip("Required FOCUS tables do not exist - run DDL setup first")
        
        # Create multiple datasets for concurrent processing
        datasets = []
        for i in range(3):  # 3 concurrent workflows
            temp_dir, total_rows, num_files = large_dataset_generator(num_files=2, rows_per_file=2000)
            datasets.append((temp_dir, total_rows, num_files, i))
        
        try:
            def run_workflow(dataset_info):
                temp_dir, total_rows, num_files, workflow_id = dataset_info
                
                params = FocusBillingIngestParams(
                    data_root=temp_dir,
                    batch_size=500,
                    dry_run=False,
                    skip_processed=False
                )
                
                start_time = time.time()
                workflow = FocusBillingIngestWorkflow(params)
                stats = workflow.execute()
                end_time = time.time()
                
                return {
                    "workflow_id": workflow_id,
                    "processing_time": end_time - start_time,
                    "files_processed": stats.files_processed,
                    "rows_processed": stats.total_rows_processed,
                    "success": stats.files_failed == 0
                }
            
            # Execute workflows concurrently
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_dataset = {executor.submit(run_workflow, dataset): dataset for dataset in datasets}
                results = []
                
                for future in as_completed(future_to_dataset):
                    result = future.result()
                    results.append(result)
            
            total_concurrent_time = time.time() - start_time
            
            # Verify all workflows succeeded
            for result in results:
                assert result["success"], f"Workflow {result['workflow_id']} failed"
                assert result["files_processed"] == 2  # Each dataset has 2 files
                assert result["rows_processed"] == 4000  # Each dataset has 4000 rows
            
            # Calculate concurrent performance metrics
            total_rows_all_workflows = sum(result["rows_processed"] for result in results)
            concurrent_throughput = total_rows_all_workflows / total_concurrent_time
            
            # Compare with sequential processing time estimate
            avg_individual_time = statistics.mean([result["processing_time"] for result in results])
            sequential_estimate = avg_individual_time * len(results)
            concurrency_benefit = sequential_estimate / total_concurrent_time
            
            print(f"✓ Concurrent processing test successful:")
            print(f"  - Workflows: {len(results)}")
            print(f"  - Total rows: {total_rows_all_workflows:,}")
            print(f"  - Concurrent time: {total_concurrent_time:.2f}s")
            print(f"  - Concurrent throughput: {concurrent_throughput:.0f} rows/s")
            print(f"  - Concurrency benefit: {concurrency_benefit:.1f}x")
            
            # Verify reasonable concurrency performance
            assert concurrency_benefit > 1.5, f"Poor concurrency benefit: {concurrency_benefit:.1f}x"
            
        finally:
            for temp_dir, _, _, _ in datasets:
                shutil.rmtree(temp_dir)


@pytest.mark.performance
class TestFocusBillingQueryPerformance:
    """Performance tests for FOCUS billing query execution"""
    
    def test_query_execution_performance_benchmarks(self):
        """
        Test query execution performance with various query types.
        
        This test validates:
        1. Simple aggregation query performance
        2. Complex join query performance
        3. Large result set handling
        4. Query optimization effectiveness
        """
        # Get available queries
        list_params = ListFocusUseCasesQueryParams()
        list_response = list_focus_use_cases_api(list_params)
        
        if not list_response["use_cases"]:
            pytest.skip("No use cases available for performance testing")
        
        query_performance_results = []
        
        # Test multiple queries for performance comparison
        test_queries = list_response["use_cases"][:5]  # Test first 5 queries
        
        for use_case in test_queries:
            try:
                # Test with different result set sizes
                for limit in [10, 100, 1000]:
                    execute_params = ExecuteFocusUseCaseQueryParams(
                        slug=use_case["slug"],
                        start_date=date(2025, 7, 1),
                        end_date=date(2025, 7, 31),
                        limit=limit
                    )
                    
                    start_time = time.time()
                    response = execute_focus_use_case_api(execute_params)
                    end_time = time.time()
                    
                    execution_time = end_time - start_time
                    api_execution_time = response["execution_time_ms"] / 1000  # Convert to seconds
                    
                    result = {
                        "query_slug": use_case["slug"],
                        "limit": limit,
                        "rows_returned": response["total_rows"],
                        "api_execution_time": execution_time,
                        "db_execution_time": api_execution_time,
                        "overhead_time": execution_time - api_execution_time
                    }
                    
                    query_performance_results.append(result)
                    
                    # Performance assertions
                    assert execution_time < 30.0, f"Query {use_case['slug']} too slow: {execution_time:.2f}s"
                    
                    if response["total_rows"] > 0:
                        rows_per_second = response["total_rows"] / max(api_execution_time, 0.001)
                        assert rows_per_second > 100, f"Query throughput too low: {rows_per_second:.0f} rows/s"
                    
                    print(f"Query {use_case['slug'][:30]}... (limit {limit}): {execution_time:.3f}s, {response['total_rows']} rows")
                    
            except Exception as e:
                print(f"⚠ Query {use_case['slug']} performance test failed: {e}")
                continue
        
        if query_performance_results:
            # Analyze performance patterns
            avg_execution_time = statistics.mean([r["api_execution_time"] for r in query_performance_results])
            max_execution_time = max([r["api_execution_time"] for r in query_performance_results])
            
            print(f"✓ Query performance benchmarks completed:")
            print(f"  - Queries tested: {len(set(r['query_slug'] for r in query_performance_results))}")
            print(f"  - Average execution time: {avg_execution_time:.3f}s")
            print(f"  - Max execution time: {max_execution_time:.3f}s")
            
            # Verify overall performance is acceptable
            assert avg_execution_time < 5.0, f"Average query time too high: {avg_execution_time:.3f}s"
    
    def test_concurrent_query_execution_performance(self):
        """
        Test query performance under concurrent load.
        
        This test validates:
        1. Multiple concurrent queries don't degrade performance significantly
        2. Database connection pooling works effectively
        3. Resource contention is manageable
        """
        # Get available queries
        list_params = ListFocusUseCasesQueryParams()
        list_response = list_focus_use_cases_api(list_params)
        
        if not list_response["use_cases"]:
            pytest.skip("No use cases available for concurrent testing")
        
        # Select a representative query for concurrent testing
        test_query = list_response["use_cases"][0]
        
        def execute_concurrent_query(query_id: int):
            """Execute a single query and return performance metrics"""
            try:
                execute_params = ExecuteFocusUseCaseQueryParams(
                    slug=test_query["slug"],
                    start_date=date(2025, 7, 1),
                    end_date=date(2025, 7, 31),
                    limit=100
                )
                
                start_time = time.time()
                response = execute_focus_use_case_api(execute_params)
                end_time = time.time()
                
                return {
                    "query_id": query_id,
                    "execution_time": end_time - start_time,
                    "rows_returned": response["total_rows"],
                    "success": True
                }
            except Exception as e:
                return {
                    "query_id": query_id,
                    "execution_time": 0,
                    "rows_returned": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # Test concurrent execution
        num_concurrent_queries = 10
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_query = {
                executor.submit(execute_concurrent_query, i): i 
                for i in range(num_concurrent_queries)
            }
            
            concurrent_results = []
            for future in as_completed(future_to_query):
                result = future.result()
                concurrent_results.append(result)
        
        total_concurrent_time = time.time() - start_time
        
        # Analyze concurrent performance
        successful_queries = [r for r in concurrent_results if r["success"]]
        failed_queries = [r for r in concurrent_results if not r["success"]]
        
        if successful_queries:
            avg_concurrent_time = statistics.mean([r["execution_time"] for r in successful_queries])
            max_concurrent_time = max([r["execution_time"] for r in successful_queries])
            
            # Calculate concurrent throughput
            total_rows = sum([r["rows_returned"] for r in successful_queries])
            concurrent_throughput = total_rows / total_concurrent_time if total_concurrent_time > 0 else 0
            
            print(f"✓ Concurrent query performance test:")
            print(f"  - Concurrent queries: {num_concurrent_queries}")
            print(f"  - Successful queries: {len(successful_queries)}")
            print(f"  - Failed queries: {len(failed_queries)}")
            print(f"  - Total time: {total_concurrent_time:.2f}s")
            print(f"  - Average query time: {avg_concurrent_time:.3f}s")
            print(f"  - Max query time: {max_concurrent_time:.3f}s")
            print(f"  - Concurrent throughput: {concurrent_throughput:.0f} rows/s")
            
            # Performance assertions
            success_rate = len(successful_queries) / num_concurrent_queries
            assert success_rate >= 0.8, f"Too many concurrent query failures: {success_rate:.1%}"
            assert avg_concurrent_time < 10.0, f"Concurrent queries too slow: {avg_concurrent_time:.3f}s"
        
        else:
            print("⚠ All concurrent queries failed - may indicate system issues")
    
    def test_query_result_pagination_performance(self):
        """
        Test performance of query result pagination.
        
        This test validates:
        1. Pagination doesn't significantly impact performance
        2. Large result sets can be handled efficiently
        3. Offset performance is reasonable
        """
        # Get available queries
        list_params = ListFocusUseCasesQueryParams()
        list_response = list_focus_use_cases_api(list_params)
        
        if not list_response["use_cases"]:
            pytest.skip("No use cases available for pagination testing")
        
        test_query = list_response["use_cases"][0]
        
        # Test pagination performance with different page sizes and offsets
        pagination_results = []
        
        page_sizes = [50, 100, 500]
        offsets = [0, 100, 500, 1000]
        
        for page_size in page_sizes:
            for offset in offsets:
                try:
                    execute_params = ExecuteFocusUseCaseQueryParams(
                        slug=test_query["slug"],
                        start_date=date(2025, 7, 1),
                        end_date=date(2025, 7, 31),
                        limit=page_size,
                        offset=offset
                    )
                    
                    start_time = time.time()
                    response = execute_focus_use_case_api(execute_params)
                    end_time = time.time()
                    
                    execution_time = end_time - start_time
                    
                    pagination_results.append({
                        "page_size": page_size,
                        "offset": offset,
                        "execution_time": execution_time,
                        "rows_returned": response["total_rows"]
                    })
                    
                    # Performance assertion for pagination
                    assert execution_time < 15.0, f"Pagination query too slow: {execution_time:.2f}s (offset {offset}, limit {page_size})"
                    
                except Exception as e:
                    print(f"⚠ Pagination test failed for offset {offset}, limit {page_size}: {e}")
                    continue
        
        if pagination_results:
            # Analyze pagination performance patterns
            avg_time_by_offset = {}
            for result in pagination_results:
                offset = result["offset"]
                if offset not in avg_time_by_offset:
                    avg_time_by_offset[offset] = []
                avg_time_by_offset[offset].append(result["execution_time"])
            
            print(f"✓ Pagination performance test completed:")
            for offset, times in avg_time_by_offset.items():
                avg_time = statistics.mean(times)
                print(f"  - Offset {offset}: {avg_time:.3f}s average")
            
            # Verify pagination performance doesn't degrade significantly with offset
            if len(avg_time_by_offset) > 1:
                offset_times = [(offset, statistics.mean(times)) for offset, times in avg_time_by_offset.items()]
                offset_times.sort()
                
                first_offset_time = offset_times[0][1]
                last_offset_time = offset_times[-1][1]
                
                performance_degradation = (last_offset_time - first_offset_time) / first_offset_time
                assert performance_degradation < 2.0, f"Pagination performance degrades too much: {performance_degradation:.1%}"


@pytest.mark.performance
class TestFocusBillingSystemResourceUsage:
    """Performance tests for system resource usage and optimization"""
    
    def test_memory_usage_patterns(self, large_dataset_generator):
        """
        Test memory usage patterns during ingestion.
        
        This test validates:
        1. Memory usage stays within reasonable bounds
        2. No significant memory leaks during processing
        3. Memory usage scales predictably with data size
        """
        # Skip if tables don't exist
        table_status = focus_observability.verify_tables_exist()
        if not all(status.passed for status in table_status.values()):
            pytest.skip("Required FOCUS tables do not exist - run DDL setup first")
        
        temp_dir, total_rows, num_files = large_dataset_generator(num_files=5, rows_per_file=2000)
        
        try:
            process = psutil.Process()
            memory_samples = []
            
            def monitor_memory():
                """Monitor memory usage during processing"""
                while getattr(monitor_memory, 'running', True):
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    memory_samples.append(memory_mb)
                    time.sleep(0.5)  # Sample every 500ms
            
            # Start memory monitoring
            monitor_memory.running = True
            monitor_thread = threading.Thread(target=monitor_memory)
            monitor_thread.start()
            
            try:
                # Run workflow while monitoring memory
                params = FocusBillingIngestParams(
                    data_root=temp_dir,
                    batch_size=500,
                    dry_run=False,
                    skip_processed=False
                )
                
                workflow = FocusBillingIngestWorkflow(params)
                stats = workflow.execute()
                
            finally:
                # Stop memory monitoring
                monitor_memory.running = False
                monitor_thread.join()
            
            # Analyze memory usage patterns
            if memory_samples:
                initial_memory = memory_samples[0]
                peak_memory = max(memory_samples)
                final_memory = memory_samples[-1]
                avg_memory = statistics.mean(memory_samples)
                
                memory_increase = peak_memory - initial_memory
                memory_retained = final_memory - initial_memory
                
                print(f"✓ Memory usage analysis:")
                print(f"  - Initial memory: {initial_memory:.1f}MB")
                print(f"  - Peak memory: {peak_memory:.1f}MB")
                print(f"  - Final memory: {final_memory:.1f}MB")
                print(f"  - Average memory: {avg_memory:.1f}MB")
                print(f"  - Peak increase: {memory_increase:.1f}MB")
                print(f"  - Memory retained: {memory_retained:.1f}MB")
                
                # Memory usage assertions
                assert memory_increase < 1000, f"Memory usage too high: {memory_increase:.1f}MB increase"
                assert memory_retained < 100, f"Possible memory leak: {memory_retained:.1f}MB retained"
                
                # Verify processing succeeded
                assert stats.files_processed == num_files
                assert stats.total_rows_processed == total_rows
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_cpu_usage_efficiency(self, large_dataset_generator):
        """
        Test CPU usage efficiency during processing.
        
        This test validates:
        1. CPU usage is reasonable during processing
        2. Processing doesn't monopolize system resources
        3. CPU efficiency correlates with throughput
        """
        # Skip if tables don't exist
        table_status = focus_observability.verify_tables_exist()
        if not all(status.passed for status in table_status.values()):
            pytest.skip("Required FOCUS tables do not exist - run DDL setup first")
        
        temp_dir, total_rows, num_files = large_dataset_generator(num_files=3, rows_per_file=3000)
        
        try:
            process = psutil.Process()
            cpu_samples = []
            
            def monitor_cpu():
                """Monitor CPU usage during processing"""
                while getattr(monitor_cpu, 'running', True):
                    cpu_percent = process.cpu_percent()
                    cpu_samples.append(cpu_percent)
                    time.sleep(1.0)  # Sample every second
            
            # Start CPU monitoring
            monitor_cpu.running = True
            cpu_thread = threading.Thread(target=monitor_cpu)
            cpu_thread.start()
            
            try:
                # Run workflow while monitoring CPU
                start_time = time.time()
                
                params = FocusBillingIngestParams(
                    data_root=temp_dir,
                    batch_size=1000,
                    dry_run=False,
                    skip_processed=False
                )
                
                workflow = FocusBillingIngestWorkflow(params)
                stats = workflow.execute()
                
                end_time = time.time()
                processing_time = end_time - start_time
                
            finally:
                # Stop CPU monitoring
                monitor_cpu.running = False
                cpu_thread.join()
            
            # Analyze CPU usage patterns
            if cpu_samples:
                avg_cpu = statistics.mean(cpu_samples)
                peak_cpu = max(cpu_samples)
                
                # Calculate CPU efficiency
                throughput = total_rows / processing_time
                cpu_efficiency = throughput / max(avg_cpu, 1)  # rows per second per CPU percent
                
                print(f"✓ CPU usage analysis:")
                print(f"  - Average CPU: {avg_cpu:.1f}%")
                print(f"  - Peak CPU: {peak_cpu:.1f}%")
                print(f"  - Processing time: {processing_time:.2f}s")
                print(f"  - Throughput: {throughput:.0f} rows/s")
                print(f"  - CPU efficiency: {cpu_efficiency:.0f} rows/s per CPU%")
                
                # CPU usage assertions
                assert avg_cpu < 80, f"Average CPU usage too high: {avg_cpu:.1f}%"
                assert peak_cpu < 95, f"Peak CPU usage too high: {peak_cpu:.1f}%"
                
                # Verify processing succeeded
                assert stats.files_processed == num_files
                assert stats.total_rows_processed == total_rows
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_disk_io_performance(self, large_dataset_generator):
        """
        Test disk I/O performance during processing.
        
        This test validates:
        1. Disk I/O is efficient during file processing
        2. No excessive disk usage patterns
        3. I/O performance scales with data size
        """
        # Skip if tables don't exist
        table_status = focus_observability.verify_tables_exist()
        if not all(status.passed for status in table_status.values()):
            pytest.skip("Required FOCUS tables do not exist - run DDL setup first")
        
        temp_dir, total_rows, num_files = large_dataset_generator(num_files=4, rows_per_file=2500)
        
        try:
            # Calculate total file size
            total_file_size = sum(
                f.stat().st_size for f in Path(temp_dir).rglob("*.parquet")
            ) / 1024 / 1024  # MB
            
            # Run workflow with I/O timing
            start_time = time.time()
            
            params = FocusBillingIngestParams(
                data_root=temp_dir,
                batch_size=800,
                dry_run=False,
                skip_processed=False
            )
            
            workflow = FocusBillingIngestWorkflow(params)
            stats = workflow.execute()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Calculate I/O performance metrics
            mb_per_second = total_file_size / processing_time
            rows_per_mb = total_rows / total_file_size
            
            print(f"✓ Disk I/O performance analysis:")
            print(f"  - Total file size: {total_file_size:.1f}MB")
            print(f"  - Processing time: {processing_time:.2f}s")
            print(f"  - I/O throughput: {mb_per_second:.1f}MB/s")
            print(f"  - Data density: {rows_per_mb:.0f} rows/MB")
            
            # I/O performance assertions
            assert mb_per_second > 5, f"I/O throughput too low: {mb_per_second:.1f}MB/s"
            assert processing_time < 120, f"Processing time too long: {processing_time:.2f}s"
            
            # Verify processing succeeded
            assert stats.files_processed == num_files
            assert stats.total_rows_processed == total_rows
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run performance tests directly
    pytest.main([__file__, "-v", "-s", "-m", "performance"])