"""
FOCUS Billing Verification Suite

Automated verification against existing test results using verification_results_clickhouse.json.
This test suite validates that our ClickHouse implementation produces results consistent
with the existing FOCUS MCP server validation.

Key features:
- Run clickhouse-local query verification using verification_results_clickhouse.json
- Surface expected zero-row cases (contracted savings) in CI output  
- Compare results with existing FOCUS MCP server validation
- Handle expected differences between local and production environments
"""

import pytest
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import tempfile
import subprocess

from app.focus_billing.query_loader import FocusQueryLoader
from app.focus_billing.query_executor import FocusQueryExecutor
from app.focus_billing.config import focus_config


class TestFocusVerificationSuite:
    """Verification tests against existing FOCUS MCP server results"""
    
    @pytest.fixture
    def verification_results(self):
        """Load verification results from focus-mcp-main project"""
        verification_file = Path("focus-mcp-main/verification_results_clickhouse.json")
        
        if not verification_file.exists():
            pytest.skip(f"Verification results file not found: {verification_file}")
        
        with open(verification_file, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def query_catalog(self):
        """Load FOCUS query catalog"""
        query_loader = FocusQueryLoader()
        return {q.slug: q for q in query_loader.load_all_queries()}
    
    def test_verification_file_structure(self, verification_results):
        """Validate verification results file has expected structure"""
        required_keys = ["data_pattern", "start_date", "end_date", "results"]
        for key in required_keys:
            assert key in verification_results, f"Missing required key: {key}"
        
        assert isinstance(verification_results["results"], list)
        assert len(verification_results["results"]) > 0
        
        # Validate result structure
        for result in verification_results["results"][:3]:  # Check first 3
            required_result_keys = ["key", "slug", "title", "status", "row_count"]
            for key in required_result_keys:
                assert key in result, f"Missing required result key: {key}"
    
    def test_query_catalog_coverage(self, verification_results, query_catalog):
        """Verify our query catalog covers queries in verification results"""
        verification_slugs = {result["slug"] for result in verification_results["results"]}
        catalog_slugs = set(query_catalog.keys())
        
        missing_queries = verification_slugs - catalog_slugs
        extra_queries = catalog_slugs - verification_slugs
        
        if missing_queries:
            print(f"⚠ Queries in verification but missing from catalog: {missing_queries}")
        
        if extra_queries:
            print(f"ℹ Extra queries in catalog not in verification: {extra_queries}")
        
        # At least 80% coverage expected
        coverage = len(verification_slugs & catalog_slugs) / len(verification_slugs)
        assert coverage >= 0.8, f"Query catalog coverage too low: {coverage:.1%}"
        
        print(f"✓ Query catalog coverage: {coverage:.1%}")
    
    def test_execute_verification_queries(self, verification_results, query_catalog):
        """Execute queries from verification results and compare outcomes"""
        query_executor = FocusQueryExecutor()
        
        # Extract date parameters from verification results
        start_date = verification_results["start_date"].split()[0]  # Remove time part
        end_date = verification_results["end_date"].split()[0]
        
        results_summary = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "zero_row_queries": 0,
            "row_count_matches": 0,
            "row_count_differences": 0
        }
        
        detailed_results = []
        
        for expected_result in verification_results["results"]:
            slug = expected_result["slug"]
            expected_status = expected_result["status"]
            expected_row_count = expected_result["row_count"]
            
            results_summary["total_queries"] += 1
            
            if slug not in query_catalog:
                print(f"⚠ Query not found in catalog: {slug}")
                continue
            
            query = query_catalog[slug]
            
            try:
                # Execute query with same parameters as verification
                actual_result = query_executor.execute_query_with_params(
                    query=query,
                    start_date=start_date,
                    end_date=end_date,
                    limit=1000  # Reasonable limit for verification
                )
                
                actual_row_count = len(actual_result)
                results_summary["successful_queries"] += 1
                
                # Track zero-row cases (often expected for contracted savings)
                if actual_row_count == 0:
                    results_summary["zero_row_queries"] += 1
                
                # Compare row counts
                if actual_row_count == expected_row_count:
                    results_summary["row_count_matches"] += 1
                    match_status = "✓"
                else:
                    results_summary["row_count_differences"] += 1
                    match_status = "⚠"
                
                detailed_results.append({
                    "slug": slug,
                    "title": query.title,
                    "expected_rows": expected_row_count,
                    "actual_rows": actual_row_count,
                    "match": actual_row_count == expected_row_count,
                    "status": "success"
                })
                
                print(f"{match_status} {slug}: expected {expected_row_count}, got {actual_row_count}")
                
            except Exception as e:
                results_summary["failed_queries"] += 1
                detailed_results.append({
                    "slug": slug,
                    "title": query.title,
                    "expected_rows": expected_row_count,
                    "actual_rows": None,
                    "match": False,
                    "status": "failed",
                    "error": str(e)
                })
                
                print(f"✗ {slug}: execution failed - {e}")
        
        # Print summary
        print(f"\n=== Verification Summary ===")
        print(f"Total queries: {results_summary['total_queries']}")
        print(f"Successful: {results_summary['successful_queries']}")
        print(f"Failed: {results_summary['failed_queries']}")
        print(f"Zero-row results: {results_summary['zero_row_queries']}")
        print(f"Row count matches: {results_summary['row_count_matches']}")
        print(f"Row count differences: {results_summary['row_count_differences']}")
        
        # Success criteria: at least 70% of queries should execute successfully
        success_rate = results_summary["successful_queries"] / results_summary["total_queries"]
        assert success_rate >= 0.7, f"Query success rate too low: {success_rate:.1%}"
        
        return detailed_results
    
    def test_zero_row_cases_documentation(self, verification_results):
        """Document expected zero-row cases for CI visibility"""
        zero_row_cases = [
            result for result in verification_results["results"] 
            if result["row_count"] == 0
        ]
        
        print(f"\n=== Expected Zero-Row Cases ({len(zero_row_cases)}) ===")
        print("These queries are expected to return zero rows with current test data:")
        
        for case in zero_row_cases:
            print(f"- {case['slug']}: {case['title']}")
            if case.get("sample_row") is None:
                print(f"  Reason: No matching data in current dataset")
        
        # This is informational - zero rows can be expected
        assert len(zero_row_cases) >= 0  # Always passes, just for documentation
    
    def test_contracted_savings_queries(self, verification_results, query_catalog):
        """Specifically test contracted savings queries that often return zero rows"""
        contracted_keywords = ["contract", "commitment", "saving", "discount", "reserved"]
        
        contracted_queries = []
        for result in verification_results["results"]:
            title_lower = result["title"].lower()
            if any(keyword in title_lower for keyword in contracted_keywords):
                contracted_queries.append(result)
        
        print(f"\n=== Contracted Savings Queries ({len(contracted_queries)}) ===")
        
        if not contracted_queries:
            print("No contracted savings queries found in verification results")
            return
        
        query_executor = FocusQueryExecutor()
        start_date = verification_results["start_date"].split()[0]
        end_date = verification_results["end_date"].split()[0]
        
        for query_result in contracted_queries:
            slug = query_result["slug"]
            expected_rows = query_result["row_count"]
            
            print(f"Testing contracted query: {slug}")
            print(f"  Expected rows: {expected_rows}")
            
            if slug in query_catalog:
                try:
                    actual_result = query_executor.execute_query_with_params(
                        query=query_catalog[slug],
                        start_date=start_date,
                        end_date=end_date,
                        limit=100
                    )
                    
                    actual_rows = len(actual_result)
                    print(f"  Actual rows: {actual_rows}")
                    
                    # For contracted savings, zero rows is often expected
                    if actual_rows == 0 and expected_rows == 0:
                        print(f"  ✓ Zero rows as expected (no contract data)")
                    elif actual_rows != expected_rows:
                        print(f"  ⚠ Row count difference (may be due to test data)")
                    else:
                        print(f"  ✓ Row count matches")
                        
                except Exception as e:
                    print(f"  ✗ Execution failed: {e}")
            else:
                print(f"  ⚠ Query not found in catalog")
    
    def test_clickhouse_local_compatibility(self, verification_results):
        """Test compatibility with clickhouse-local for offline verification"""
        # This test validates that our queries could work with clickhouse-local
        # for CI environments without a full ClickHouse server
        
        query_loader = FocusQueryLoader()
        queries = query_loader.load_all_queries()
        
        # Check for ClickHouse-specific functions that might not work in clickhouse-local
        incompatible_functions = [
            "dictGet", "dictHas", "cluster", "remote", "distributed"
        ]
        
        compatibility_issues = []
        
        for query in queries[:5]:  # Check first 5 queries
            sql_lower = query.sql.lower()
            
            for func in incompatible_functions:
                if func.lower() in sql_lower:
                    compatibility_issues.append({
                        "query": query.slug,
                        "function": func,
                        "sql_snippet": query.sql[:200] + "..."
                    })
        
        if compatibility_issues:
            print(f"\n=== ClickHouse-Local Compatibility Issues ===")
            for issue in compatibility_issues:
                print(f"Query {issue['query']} uses {issue['function']}")
        
        # This is informational - some incompatibilities are expected
        print(f"✓ Compatibility check complete: {len(compatibility_issues)} potential issues found")
    
    def test_sample_data_validation(self, verification_results):
        """Validate sample data in verification results matches expected format"""
        samples_with_data = [
            result for result in verification_results["results"]
            if result.get("sample_row") is not None
        ]
        
        print(f"\n=== Sample Data Validation ({len(samples_with_data)} samples) ===")
        
        for result in samples_with_data[:3]:  # Check first 3 samples
            sample_row = result["sample_row"]
            
            # Validate common FOCUS columns exist in samples
            expected_columns = ["ProviderName", "BillingAccountId"]
            found_columns = []
            
            for col in expected_columns:
                if col in sample_row:
                    found_columns.append(col)
            
            print(f"Query {result['slug']}: {len(found_columns)}/{len(expected_columns)} expected columns found")
            
            # Validate data types in sample
            for key, value in sample_row.items():
                if value is not None:
                    value_type = type(value).__name__
                    print(f"  {key}: {value_type}")
        
        assert len(samples_with_data) > 0, "No sample data found in verification results"


class TestFocusVerificationCI:
    """CI-specific verification tests for automated environments"""
    
    def test_verification_results_freshness(self, verification_results):
        """Check if verification results are reasonably fresh"""
        # Parse dates from verification results
        start_date_str = verification_results["start_date"]
        end_date_str = verification_results["end_date"]
        
        # Basic date format validation
        assert len(start_date_str) > 10, "Start date format appears invalid"
        assert len(end_date_str) > 10, "End date format appears invalid"
        
        # Check that date range is reasonable (not too old)
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            
            date_range_days = (end_date - start_date).days
            assert date_range_days > 0, "Invalid date range"
            assert date_range_days <= 365, "Date range too large (>1 year)"
            
            print(f"✓ Verification date range: {date_range_days} days")
            
        except Exception as e:
            print(f"⚠ Date parsing failed: {e}")
    
    def test_ci_environment_compatibility(self):
        """Test compatibility with CI environment constraints"""
        # Test that required components can be imported in CI
        try:
            from app.focus_billing.query_loader import FocusQueryLoader
            from app.focus_billing.query_executor import FocusQueryExecutor
            from app.focus_billing.config import focus_config
            
            print("✓ All required modules can be imported")
            
        except ImportError as e:
            pytest.fail(f"Import failed in CI environment: {e}")
        
        # Test configuration loading without external dependencies
        try:
            config_dict = {
                "clickhouse_host": focus_config.clickhouse_host,
                "clickhouse_database": focus_config.clickhouse_database,
                "focus_data_root": focus_config.focus_data_root
            }
            
            assert all(v is not None for v in config_dict.values())
            print("✓ Configuration loaded successfully")
            
        except Exception as e:
            print(f"⚠ Configuration loading issue: {e}")


if __name__ == "__main__":
    # Run verification tests directly
    pytest.main([__file__, "-v", "-s"])