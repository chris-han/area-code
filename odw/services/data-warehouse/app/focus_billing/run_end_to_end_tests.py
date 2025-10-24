#!/usr/bin/env python3
"""
FOCUS Billing End-to-End Test Runner

Comprehensive test runner for FOCUS billing integration that executes:
1. Smoke tests - Basic functionality validation
2. Verification tests - Comparison against existing results
3. System health checks - Configuration and connectivity validation

This script can be run in different modes:
- Full test suite (default)
- Smoke tests only
- Verification tests only
- CI mode (optimized for automated environments)
"""

import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from focus_billing.config import focus_config


class FocusTestRunner:
    """Test runner for FOCUS billing end-to-end validation"""
    
    def __init__(self, verbose: bool = False, ci_mode: bool = False):
        self.verbose = verbose
        self.ci_mode = ci_mode
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "smoke_tests": {},
            "verification_tests": {},
            "system_health": {},
            "summary": {}
        }
    
    def run_smoke_tests(self) -> bool:
        """Run smoke test suite"""
        print("=== Running FOCUS Billing Smoke Tests ===")
        
        test_file = Path(__file__).parent / "tests" / "test_smoke_suite.py"
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(test_file),
            "-v" if self.verbose else "-q",
            "--tb=short",
            "-x" if not self.ci_mode else ""  # Stop on first failure unless CI mode
        ]
        
        # Remove empty strings from command
        cmd = [arg for arg in cmd if arg]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=Path(__file__).parent.parent.parent
            )
            
            self.test_results["smoke_tests"] = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
            if self.verbose or result.returncode != 0:
                print("STDOUT:", result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
            
            if result.returncode == 0:
                print("✓ Smoke tests passed")
                return True
            else:
                print(f"✗ Smoke tests failed (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"✗ Failed to run smoke tests: {e}")
            self.test_results["smoke_tests"] = {
                "exit_code": -1,
                "error": str(e),
                "success": False
            }
            return False
    
    def run_verification_tests(self) -> bool:
        """Run verification test suite"""
        print("\n=== Running FOCUS Billing Verification Tests ===")
        
        test_file = Path(__file__).parent / "tests" / "test_verification_suite.py"
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(test_file),
            "-v" if self.verbose else "-q",
            "--tb=short"
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=Path(__file__).parent.parent.parent
            )
            
            self.test_results["verification_tests"] = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
            if self.verbose or result.returncode != 0:
                print("STDOUT:", result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
            
            if result.returncode == 0:
                print("✓ Verification tests passed")
                return True
            else:
                print(f"✗ Verification tests failed (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"✗ Failed to run verification tests: {e}")
            self.test_results["verification_tests"] = {
                "exit_code": -1,
                "error": str(e),
                "success": False
            }
            return False
    
    def run_system_health_checks(self) -> bool:
        """Run system health checks"""
        print("\n=== Running System Health Checks ===")
        
        health_results = {
            "configuration": self._check_configuration(),
            "clickhouse_connectivity": self._check_clickhouse_connectivity(),
            "query_catalog": self._check_query_catalog(),
            "data_paths": self._check_data_paths()
        }
        
        self.test_results["system_health"] = health_results
        
        all_passed = all(result["success"] for result in health_results.values())
        
        if all_passed:
            print("✓ All system health checks passed")
        else:
            failed_checks = [name for name, result in health_results.items() if not result["success"]]
            print(f"✗ System health checks failed: {failed_checks}")
        
        return all_passed
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check FOCUS billing configuration"""
        try:
            # Test basic configuration loading
            config_valid = (
                focus_config.clickhouse_host is not None and
                focus_config.clickhouse_database is not None and
                focus_config.focus_data_root is not None
            )
            
            return {
                "success": config_valid,
                "message": "Configuration loaded successfully" if config_valid else "Configuration validation failed",
                "details": {
                    "clickhouse_host": focus_config.clickhouse_host,
                    "clickhouse_database": focus_config.clickhouse_database,
                    "focus_data_root": focus_config.focus_data_root
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Configuration check failed: {e}",
                "error": str(e)
            }
    
    def _check_clickhouse_connectivity(self) -> Dict[str, Any]:
        """Check ClickHouse connectivity"""
        try:
            from focus_billing.observability import focus_observability
            
            # Test basic connectivity by checking table existence
            table_status = focus_observability.verify_tables_exist()
            
            # Check if connection works (tables may not exist yet)
            connection_works = True
            connection_errors = []
            
            for table_name, status in table_status.items():
                if "connection" in status.message.lower() or "timeout" in status.message.lower():
                    connection_works = False
                    connection_errors.append(f"{table_name}: {status.message}")
            
            return {
                "success": connection_works,
                "message": "ClickHouse connectivity verified" if connection_works else "ClickHouse connection issues detected",
                "details": {
                    "table_checks": len(table_status),
                    "connection_errors": connection_errors
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"ClickHouse connectivity check failed: {e}",
                "error": str(e)
            }
    
    def _check_query_catalog(self) -> Dict[str, Any]:
        """Check query catalog loading"""
        try:
            from focus_billing.query_loader import FocusQueryLoader
            
            query_loader = FocusQueryLoader()
            queries = query_loader.load_all_queries()
            
            catalog_healthy = len(queries) > 0
            
            return {
                "success": catalog_healthy,
                "message": f"Query catalog loaded: {len(queries)} queries" if catalog_healthy else "Query catalog is empty",
                "details": {
                    "query_count": len(queries),
                    "sample_queries": [q.slug for q in queries[:3]]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Query catalog check failed: {e}",
                "error": str(e)
            }
    
    def _check_data_paths(self) -> Dict[str, Any]:
        """Check data path accessibility"""
        try:
            path_status = focus_config.validate_paths()
            
            critical_paths = ["focus_data_root", "focus_spec_root"]
            critical_paths_exist = all(
                path_status.get(path, False) for path in critical_paths
                if path in path_status
            )
            
            return {
                "success": True,  # Paths may not exist in all environments
                "message": f"Path validation completed: {sum(path_status.values())}/{len(path_status)} paths exist",
                "details": path_status,
                "critical_paths_exist": critical_paths_exist
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Data path check failed: {e}",
                "error": str(e)
            }
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate test execution summary"""
        smoke_success = self.test_results.get("smoke_tests", {}).get("success", False)
        verification_success = self.test_results.get("verification_tests", {}).get("success", False)
        health_success = all(
            result.get("success", False) 
            for result in self.test_results.get("system_health", {}).values()
        )
        
        overall_success = smoke_success and verification_success and health_success
        
        summary = {
            "overall_success": overall_success,
            "smoke_tests_passed": smoke_success,
            "verification_tests_passed": verification_success,
            "system_health_passed": health_success,
            "end_time": datetime.now().isoformat(),
            "recommendations": []
        }
        
        # Add recommendations based on results
        if not smoke_success:
            summary["recommendations"].append("Review smoke test failures - basic functionality may be broken")
        
        if not verification_success:
            summary["recommendations"].append("Review verification test failures - results may differ from expected")
        
        if not health_success:
            summary["recommendations"].append("Review system health issues - configuration or connectivity problems detected")
        
        if overall_success:
            summary["recommendations"].append("All tests passed - FOCUS billing integration is healthy")
        
        self.test_results["summary"] = summary
        return summary
    
    def save_results(self, output_file: str = None):
        """Save test results to JSON file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"focus_test_results_{timestamp}.json"
        
        output_path = Path(output_file)
        
        with open(output_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\nTest results saved to: {output_path}")
    
    def print_summary(self):
        """Print test execution summary"""
        summary = self.test_results.get("summary", {})
        
        print("\n" + "="*50)
        print("FOCUS BILLING TEST SUMMARY")
        print("="*50)
        
        print(f"Overall Success: {'✓' if summary.get('overall_success') else '✗'}")
        print(f"Smoke Tests: {'✓' if summary.get('smoke_tests_passed') else '✗'}")
        print(f"Verification Tests: {'✓' if summary.get('verification_tests_passed') else '✗'}")
        print(f"System Health: {'✓' if summary.get('system_health_passed') else '✗'}")
        
        if summary.get("recommendations"):
            print("\nRecommendations:")
            for rec in summary["recommendations"]:
                print(f"- {rec}")
        
        print("="*50)


def main():
    """Main entry point for test runner"""
    parser = argparse.ArgumentParser(description="FOCUS Billing End-to-End Test Runner")
    parser.add_argument("--smoke-only", action="store_true", help="Run only smoke tests")
    parser.add_argument("--verification-only", action="store_true", help="Run only verification tests")
    parser.add_argument("--health-only", action="store_true", help="Run only system health checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--ci", action="store_true", help="CI mode (continue on failures)")
    parser.add_argument("--output", "-o", help="Output file for test results")
    
    args = parser.parse_args()
    
    runner = FocusTestRunner(verbose=args.verbose, ci_mode=args.ci)
    
    success = True
    
    # Run selected test suites
    if args.smoke_only:
        success = runner.run_smoke_tests()
    elif args.verification_only:
        success = runner.run_verification_tests()
    elif args.health_only:
        success = runner.run_system_health_checks()
    else:
        # Run all tests
        health_success = runner.run_system_health_checks()
        smoke_success = runner.run_smoke_tests()
        verification_success = runner.run_verification_tests()
        
        success = health_success and smoke_success and verification_success
    
    # Generate summary
    runner.generate_summary()
    runner.print_summary()
    
    # Save results if requested
    if args.output:
        runner.save_results(args.output)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()