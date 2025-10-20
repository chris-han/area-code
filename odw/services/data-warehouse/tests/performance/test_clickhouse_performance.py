"""
ClickHouse Query Performance Tests

Performance benchmarks for ClickHouse query optimization and data analytics.
"""

import pytest
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock
import statistics


class TestClickHouseQueryPerformance:
    """Test ClickHouse query performance and optimization."""
    
    @pytest.mark.asyncio
    async def test_large_dataset_query_performance(self, mock_clickhouse_client):
        """Test query performance on large billing datasets."""
        
        # Mock large dataset query results
        mock_clickhouse_client.query.return_value = {
            "data": [
                {
                    "billing_account_id": f"account-{i}",
                    "usage_date": "2024-01-01",
                    "total_cost": 1000.0 + i,
                    "service_category": "Compute" if i % 2 == 0 else "Storage"
                }
                for i in range(100000)  # 100K records
            ],
            "rows": 100000,
            "statistics": {
                "elapsed": 0.250,  # 250ms
                "rows_read": 100000,
                "bytes_read": 5000000  # 5MB
            }
        }
        
        # Test query execution time
        start_time = time.time()
        
        query = """
        SELECT 
            billing_account_id,
            usage_date,
            SUM(billed_cost) as total_cost,
            service_category
        FROM azure_billing_focus
        WHERE usage_date >= '2024-01-01' 
        AND usage_date <= '2024-01-31'
        GROUP BY billing_account_id, usage_date, service_category
        ORDER BY total_cost DESC
        LIMIT 1000
        """
        
        result = await mock_clickhouse_client.query(query)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify query results
        assert result["rows"] == 100000
        assert len(result["data"]) == 100000
        
        # Performance assertions
        assert execution_time < 1.0, f"Query execution too slow: {execution_time}s"
        assert result["statistics"]["elapsed"] < 0.5, "ClickHouse query elapsed time too high"
    
    @pytest.mark.asyncio
    async def test_aggregation_query_performance(self, mock_clickhouse_client):
        """Test performance of complex aggregation queries."""
        
        # Mock aggregation query results
        mock_clickhouse_client.query.return_value = {
            "data": [
                {
                    "month": "2024-01",
                    "service_category": "Compute",
                    "total_cost": 50000.0,
                    "avg_daily_cost": 1612.90,
                    "resource_count": 150
                },
                {
                    "month": "2024-01", 
                    "service_category": "Storage",
                    "total_cost": 25000.0,
                    "avg_daily_cost": 806.45,
                    "resource_count": 75
                }
            ],
            "rows": 2,
            "statistics": {
                "elapsed": 0.180,
                "rows_read": 1000000,
                "bytes_read": 50000000
            }
        }
        
        # Complex aggregation query
        aggregation_query = """
        SELECT 
            toYYYYMM(usage_date) as month,
            service_category,
            SUM(billed_cost) as total_cost,
            AVG(billed_cost) as avg_daily_cost,
            COUNT(DISTINCT resource_id) as resource_count
        FROM azure_billing_focus
        WHERE usage_date >= '2024-01-01'
        GROUP BY month, service_category
        HAVING total_cost > 1000
        ORDER BY total_cost DESC
        """
        
        start_time = time.time()
        result = await mock_clickhouse_client.query(aggregation_query)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Verify aggregation results
        assert result["rows"] == 2
        assert result["statistics"]["rows_read"] == 1000000
        
        # Performance assertions for complex aggregations
        assert execution_time < 2.0, f"Aggregation query too slow: {execution_time}s"
        assert result["statistics"]["elapsed"] < 1.0, "ClickHouse aggregation elapsed time too high"
    
    @pytest.mark.asyncio
    async def test_concurrent_query_performance(self, mock_clickhouse_client):
        """Test performance under concurrent query load."""
        
        # Mock concurrent query responses
        mock_clickhouse_client.query.return_value = {
            "data": [{"result": "success"}],
            "rows": 1,
            "statistics": {
                "elapsed": 0.100,
                "rows_read": 10000,
                "bytes_read": 500000
            }
        }
        
        # Define multiple query types
        queries = [
            "SELECT COUNT(*) FROM azure_billing_focus WHERE usage_date = '2024-01-01'",
            "SELECT SUM(billed_cost) FROM azure_billing_focus WHERE service_category = 'Compute'",
            "SELECT billing_account_id, SUM(billed_cost) FROM azure_billing_focus GROUP BY billing_account_id",
            "SELECT * FROM azure_billing_focus WHERE resource_type LIKE '%VirtualMachines%' LIMIT 100",
            "SELECT service_name, AVG(billed_cost) FROM azure_billing_focus GROUP BY service_name"
        ]
        
        # Execute queries concurrently
        import asyncio
        
        async def execute_query(query):
            start_time = time.time()
            result = await mock_clickhouse_client.query(query)
            end_time = time.time()
            return end_time - start_time, result
        
        start_time = time.time()
        
        # Run 20 concurrent queries (4 of each type)
        tasks = []
        for _ in range(4):
            for query in queries:
                tasks.append(execute_query(query))
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Analyze concurrent performance
        execution_times = [result[0] for result in results]
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        
        # Verify all queries completed successfully
        assert len(results) == 20
        for execution_time, result in results:
            assert result["rows"] >= 0
        
        # Performance assertions for concurrent load
        assert total_time < 10.0, f"Concurrent queries took too long: {total_time}s"
        assert avg_execution_time < 1.0, f"Average query time too high: {avg_execution_time}s"
        assert max_execution_time < 3.0, f"Slowest query too slow: {max_execution_time}s"
    
    @pytest.mark.asyncio
    async def test_data_insertion_performance(self, mock_clickhouse_client):
        """Test performance of bulk data insertion."""
        
        # Mock insertion performance
        mock_clickhouse_client.execute.return_value = {
            "rows_inserted": 50000,
            "elapsed": 2.5,
            "bytes_processed": 25000000
        }
        
        # Simulate bulk insert
        start_time = time.time()
        
        # Mock bulk insert operation
        insert_query = """
        INSERT INTO azure_billing_focus 
        (billing_account_id, usage_date, billed_cost, service_category, provider)
        VALUES
        """
        
        result = await mock_clickhouse_client.execute(insert_query)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Calculate insertion rate
        rows_per_second = result["rows_inserted"] / result["elapsed"]
        mb_per_second = (result["bytes_processed"] / 1024 / 1024) / result["elapsed"]
        
        # Performance assertions for bulk insertion
        assert execution_time < 5.0, f"Bulk insert too slow: {execution_time}s"
        assert rows_per_second > 10000, f"Insertion rate too low: {rows_per_second} rows/s"
        assert mb_per_second > 5.0, f"Throughput too low: {mb_per_second} MB/s"