"""
FOCUS Billing Comprehensive Test Runner

Orchestrates comprehensive test execution for FOCUS billing system including:
- Integration tests for full ingestion workflow
- API endpoint testing with real ClickHouse queries  
- Performance testing for large dataset ingestion
- Data validation and compliance testing
- Error handling and edge case testing

This script provides organized test execution with proper reporting and
can be used for CI/CD validation or manual testing.
"""

import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import json

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class FocusTestRunner:
    """Comprehensive test runner for FOCUS billing system"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        if self.verbose:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def run_test_suite(self, test_path: str, markers: Optional[List[str]] = None, 
                      description: str = "") -> Dict:
        """Run a specific test suite and return results"""
        self.log(f"Starting {description or test_path}")
        
        # Build pytest command
        cmd = ["python", "-m", "pytest", test_path, "-v"]
        
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])
        
        # Add output options
        cmd.extend(["--tb=short", "--no-header"])
        
        if self.verbose:
            cmd.append("-s")
        
        start_time = time.time()
        
        try:
            # Run the test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=1800  # 30 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            # Parse results
            test_result = {
                "success": result.returncode == 0,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
            # Extract test counts from output
            test_counts = self._extract_test_counts(result.stdout)
            test_result.update(test_counts)
            
            if test_result["success"]:
                self.log(f"✓ {description} completed successfully in {execution_time:.2f}s")
                if test_counts.get("passed", 0) > 0:
                    self.log(f"  Tests passed: {test_counts['passed']}")
                if test_counts.get("failed", 0) > 0:
                    self.log(f"  Tests failed: {test_counts['failed']}")
                if test_counts.get("skipped", 0) > 0:
                    self.log(f"  Tests skipped: {test_counts['skipped']}")
            else:
                self.log(f"✗ {description} failed in {execution_time:.2f}s", "ERROR")
                if self.verbose and result.stderr:
                    self.log(f"Error output: {result.stderr[:500]}...", "ERROR")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            self.log(f"✗ {description} timed out after 30 minutes", "ERROR")
            return {
                "success": False,
                "execution_time": 1800,
                "error": "Test suite timed out",
                "return_code": -1
            }
        except Exception as e:
            self.log(f"✗ {description} failed with exception: {e}", "ERROR")
            return {
                "success": False,
                "execution_time": time.time() - start_time,
                "error": str(e),
                "return_code": -1
            }
    
    def _extract_test_counts(self, output: str) -> Dict[str, int]:
        """Extract test counts from pytest output"""
        counts = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
        
        # Look for pytest summary line
        lines = output.split('\n')
        for line in lines:
            if 'passed' in line or 'failed' in line or 'skipped' in line:
                # Parse lines like "5 passed, 2 skipped in 1.23s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part in counts and i > 0:
                        try:
                            counts[part] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
        
        return counts
    
    def run_comprehensive_tests(self, test_categories: Optional[List[str]] = None) -> Dict:
        """Run comprehensive FOCUS billing tests"""
        self.start_time = time.time()
        self.log("Starting FOCUS Billing Comprehensive Test Suite")
        
        # Define test suites
        test_suites = [
            {
                "name": "integration",
                "path": "tests/integration/test_focus_billing_integration.py",
                "markers": ["integration"],
                "description": "Integration Tests - Full workflow and API testing",
                "required": True
            },
            {
                "name": "performance", 
                "path": "tests/performance/test_focus_billing_performance.py",
                "markers": ["performance"],
                "description": "Performance Tests - Large dataset and scalability testing",
                "required": False
            },
            {
                "name": "focus_comprehensive",
                "path": "tests/focus/test_focus_billing_comprehensive.py", 
                "markers": ["focus"],
                "description": "FOCUS Compliance Tests - API and data validation",
                "required": True
            },
            {
                "name": "smoke_tests",
                "path": "app/focus_billing/tests/test_smoke_suite.py",
                "markers": None,
                "description": "Smoke Tests - Basic functionality validation",
                "required": True
            }
        ]
        
        # Filter test suites if categories specified
        if test_categories:
            test_suites = [ts for ts in test_suites if ts["name"] in test_categories]
        
        self.log(f"Running {len(test_suites)} test suites")
        
        # Run each test suite
        for suite in test_suites:
            suite_result = self.run_test_suite(
                test_path=suite["path"],
                markers=suite["markers"],
                description=suite["description"]
            )
            
            self.test_results[suite["name"]] = suite_result
            
            # Stop on critical failures if required
            if suite["required"] and not suite_result["success"]:
                self.log(f"Critical test suite failed: {suite['name']}", "ERROR")
                if not self._should_continue_on_failure():
                    break
        
        self.end_time = time.time()
        return self._generate_summary()
    
    def _should_continue_on_failure(self) -> bool:
        """Determine if testing should continue after a failure"""
        # For now, continue on failure to get complete picture
        return True
    
    def _generate_summary(self) -> Dict:
        """Generate comprehensive test summary"""
        total_time = self.end_time - self.start_time if self.end_time else 0
        
        summary = {
            "total_execution_time": total_time,
            "suites_run": len(self.test_results),
            "suites_passed": sum(1 for r in self.test_results.values() if r["success"]),
            "suites_failed": sum(1 for r in self.test_results.values() if not r["success"]),
            "total_tests_passed": sum(r.get("passed", 0) for r in self.test_results.values()),
            "total_tests_failed": sum(r.get("failed", 0) for r in self.test_results.values()),
            "total_tests_skipped": sum(r.get("skipped", 0) for r in self.test_results.values()),
            "suite_results": self.test_results
        }
        
        # Calculate overall success
        summary["overall_success"] = (
            summary["suites_failed"] == 0 and 
            summary["total_tests_failed"] == 0
        )
        
        return summary
    
    def print_summary(self, summary: Dict):
        """Print comprehensive test summary"""
        self.log("=" * 80)
        self.log("FOCUS BILLING COMPREHENSIVE TEST SUMMARY")
        self.log("=" * 80)
        
        # Overall results
        status = "✓ PASSED" if summary["overall_success"] else "✗ FAILED"
        self.log(f"Overall Status: {status}")
        self.log(f"Total Execution Time: {summary['total_execution_time']:.2f} seconds")
        self.log("")
        
        # Suite summary
        self.log("Test Suite Summary:")
        self.log(f"  Suites Run: {summary['suites_run']}")
        self.log(f"  Suites Passed: {summary['suites_passed']}")
        self.log(f"  Suites Failed: {summary['suites_failed']}")
        self.log("")
        
        # Test summary
        self.log("Individual Test Summary:")
        self.log(f"  Tests Passed: {summary['total_tests_passed']}")
        self.log(f"  Tests Failed: {summary['total_tests_failed']}")
        self.log(f"  Tests Skipped: {summary['total_tests_skipped']}")
        self.log("")
        
        # Detailed suite results
        self.log("Detailed Suite Results:")
        for suite_name, result in summary["suite_results"].items():
            status_icon = "✓" if result["success"] else "✗"
            self.log(f"  {status_icon} {suite_name}: {result['execution_time']:.2f}s")
            
            if result.get("passed", 0) > 0:
                self.log(f"    Passed: {result['passed']}")
            if result.get("failed", 0) > 0:
                self.log(f"    Failed: {result['failed']}")
            if result.get("skipped", 0) > 0:
                self.log(f"    Skipped: {result['skipped']}")
            
            if not result["success"] and result.get("error"):
                self.log(f"    Error: {result['error']}")
        
        self.log("=" * 80)
    
    def save_results(self, output_file: str, summary: Dict):
        """Save test results to JSON file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            self.log(f"Test results saved to: {output_file}")
        except Exception as e:
            self.log(f"Failed to save results: {e}", "ERROR")


def main():
    """Main entry point for comprehensive test runner"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive FOCUS billing tests"
    )
    
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["integration", "performance", "focus_comprehensive", "smoke_tests"],
        help="Test categories to run (default: all)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for test results (JSON format)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = FocusTestRunner(verbose=not args.quiet)
    
    try:
        # Run comprehensive tests
        summary = runner.run_comprehensive_tests(test_categories=args.categories)
        
        # Print summary
        runner.print_summary(summary)
        
        # Save results if requested
        if args.output:
            runner.save_results(args.output, summary)
        
        # Exit with appropriate code
        exit_code = 0 if summary["overall_success"] else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        runner.log("Test execution interrupted by user", "ERROR")
        sys.exit(130)
    except Exception as e:
        runner.log(f"Test execution failed: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()