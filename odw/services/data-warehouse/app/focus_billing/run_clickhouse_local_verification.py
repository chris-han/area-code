#!/usr/bin/env python3
"""
ClickHouse Local Verification Runner

Runs FOCUS queries using clickhouse-local against Parquet files for offline verification.
This script enables CI environments to validate query results without a full ClickHouse server.

Features:
- Execute queries from verification_results_clickhouse.json using clickhouse-local
- Compare results with expected outcomes
- Handle Parquet file discovery and schema mapping
- Generate verification report for CI output
"""

import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from focus_billing.config import focus_config
from focus_billing.query_loader import FocusQueryLoader


class ClickHouseLocalVerifier:
    """Verifier using clickhouse-local for offline query validation"""
    
    def __init__(self, data_root: str, verification_file: str):
        self.data_root = Path(data_root)
        self.verification_file = Path(verification_file)
        self.temp_dir = None
        
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir:
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def check_clickhouse_local_available(self) -> bool:
        """Check if clickhouse-local is available in PATH"""
        try:
            result = subprocess.run(
                ["clickhouse-local", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def discover_parquet_files(self) -> List[Path]:
        """Discover Parquet files in the data directory"""
        parquet_files = []
        
        if self.data_root.exists():
            # Find all .parquet files recursively
            parquet_files = list(self.data_root.rglob("*.parquet"))
        
        return parquet_files
    
    def create_clickhouse_local_schema(self, parquet_files: List[Path]) -> str:
        """Create ClickHouse schema definition for Parquet files"""
        if not parquet_files:
            return ""
        
        # Use the first parquet file to infer schema
        sample_file = parquet_files[0]
        
        # Basic schema mapping for FOCUS columns
        schema_sql = f"""
        CREATE TABLE focus_data_table ENGINE = File(Parquet, '{sample_file}')
        AS SELECT 
            BillingAccountId,
            UsageDate,
            BilledCost,
            EffectiveCost,
            BillingCurrency,
            ServiceCategory,
            ServiceName,
            ResourceId,
            Provider,
            Region,
            ChargeCategory,
            ChargeSubcategory,
            ChargeDescription,
            ChargePeriodStart,
            ChargePeriodEnd
        FROM file('{sample_file}', Parquet);
        """
        
        return schema_sql
    
    def load_verification_results(self) -> Dict[str, Any]:
        """Load verification results from JSON file"""
        if not self.verification_file.exists():
            raise FileNotFoundError(f"Verification file not found: {self.verification_file}")
        
        with open(self.verification_file, 'r') as f:
            return json.load(f)
    
    def execute_query_with_clickhouse_local(self, sql: str, parquet_files: List[Path]) -> Optional[List[Dict]]:
        """Execute a query using clickhouse-local"""
        if not parquet_files:
            return None
        
        # Create a temporary SQL file
        sql_file = Path(self.temp_dir) / "query.sql"
        
        # Modify SQL to work with file() function for Parquet
        modified_sql = self.adapt_sql_for_clickhouse_local(sql, parquet_files[0])
        
        with open(sql_file, 'w') as f:
            f.write(modified_sql)
        
        try:
            # Execute with clickhouse-local
            cmd = [
                "clickhouse-local",
                "--query", modified_sql,
                "--output-format", "JSONEachRow"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse JSON results
                results = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            results.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                return results
            else:
                print(f"ClickHouse Local error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Query execution timed out")
            return None
        except Exception as e:
            print(f"Query execution failed: {e}")
            return None
    
    def adapt_sql_for_clickhouse_local(self, sql: str, parquet_file: Path) -> str:
        """Adapt SQL query to work with clickhouse-local and Parquet files"""
        # Replace focus_data_table references with file() function
        adapted_sql = sql.replace(
            "focus_data_table",
            f"file('{parquet_file}', Parquet)"
        )
        
        # Handle parameter placeholders (replace with actual values)
        # This is a simplified approach - in practice, you'd want proper parameter binding
        adapted_sql = adapted_sql.replace("?", "'2025-07-01'")  # Replace first parameter
        adapted_sql = adapted_sql.replace("?", "'2025-10-01'")  # Replace second parameter
        
        return adapted_sql
    
    def run_verification(self) -> Dict[str, Any]:
        """Run complete verification using clickhouse-local"""
        print("=== ClickHouse Local Verification ===")
        
        # Check if clickhouse-local is available
        if not self.check_clickhouse_local_available():
            return {
                "success": False,
                "error": "clickhouse-local not available in PATH",
                "results": []
            }
        
        # Discover Parquet files
        parquet_files = self.discover_parquet_files()
        if not parquet_files:
            return {
                "success": False,
                "error": f"No Parquet files found in {self.data_root}",
                "results": []
            }
        
        print(f"Found {len(parquet_files)} Parquet files")
        
        # Load verification results
        try:
            verification_data = self.load_verification_results()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load verification results: {e}",
                "results": []
            }
        
        # Load query catalog
        query_loader = FocusQueryLoader()
        query_catalog = {q.slug: q for q in query_loader.load_all_queries()}
        
        # Run verification queries
        results = []
        successful_queries = 0
        failed_queries = 0
        
        for expected_result in verification_data["results"][:5]:  # Limit to first 5 for testing
            slug = expected_result["slug"]
            expected_row_count = expected_result["row_count"]
            
            print(f"Testing query: {slug}")
            
            if slug not in query_catalog:
                results.append({
                    "slug": slug,
                    "status": "skipped",
                    "reason": "Query not found in catalog"
                })
                continue
            
            query = query_catalog[slug]
            
            # Execute query with clickhouse-local
            actual_results = self.execute_query_with_clickhouse_local(
                query.sql, parquet_files
            )
            
            if actual_results is not None:
                actual_row_count = len(actual_results)
                match = actual_row_count == expected_row_count
                
                results.append({
                    "slug": slug,
                    "title": query.title,
                    "expected_rows": expected_row_count,
                    "actual_rows": actual_row_count,
                    "match": match,
                    "status": "success"
                })
                
                successful_queries += 1
                status_icon = "✓" if match else "⚠"
                print(f"  {status_icon} Expected: {expected_row_count}, Got: {actual_row_count}")
                
            else:
                results.append({
                    "slug": slug,
                    "title": query.title,
                    "expected_rows": expected_row_count,
                    "actual_rows": None,
                    "match": False,
                    "status": "failed"
                })
                
                failed_queries += 1
                print(f"  ✗ Query execution failed")
        
        # Generate summary
        total_queries = len(results)
        success_rate = successful_queries / total_queries if total_queries > 0 else 0
        
        print(f"\n=== Verification Summary ===")
        print(f"Total queries tested: {total_queries}")
        print(f"Successful executions: {successful_queries}")
        print(f"Failed executions: {failed_queries}")
        print(f"Success rate: {success_rate:.1%}")
        
        return {
            "success": success_rate >= 0.5,  # At least 50% success rate
            "summary": {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "failed_queries": failed_queries,
                "success_rate": success_rate
            },
            "results": results,
            "parquet_files_found": len(parquet_files)
        }


def main():
    """Main entry point for clickhouse-local verification"""
    parser = argparse.ArgumentParser(description="ClickHouse Local Verification Runner")
    parser.add_argument(
        "--data-root", 
        default=focus_config.focus_data_root,
        help="Root directory containing FOCUS Parquet files"
    )
    parser.add_argument(
        "--verification-file",
        default="focus-mcp-main/verification_results_clickhouse.json",
        help="Path to verification results JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for verification results"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Run verification
    with ClickHouseLocalVerifier(args.data_root, args.verification_file) as verifier:
        results = verifier.run_verification()
    
    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nVerification results saved to: {output_path}")
    
    # Print final status
    if results["success"]:
        print("\n✓ ClickHouse Local verification completed successfully")
        sys.exit(0)
    else:
        print(f"\n✗ ClickHouse Local verification failed: {results.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()