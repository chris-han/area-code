#!/usr/bin/env python3
"""
Test runner for Azure Billing Intelligence test suite.

Usage:
    python tests/run_tests.py                    # Run all tests
    python tests/run_tests.py --integration      # Run integration tests only
    python tests/run_tests.py --focus           # Run FOCUS compliance tests only
    python tests/run_tests.py --performance     # Run performance tests only
    python tests/run_tests.py --monitoring      # Run monitoring tests only
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_pytest(test_path: str, verbose: bool = True) -> int:
    """Run pytest with specified path and options."""
    
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    # Add coverage reporting
    cmd.extend([
        "--cov=app.azure_billing",
        "--cov-report=term-missing",
        "--cov-report=html:tests/coverage_html"
    ])
    
    # Add test path
    cmd.append(test_path)
    
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def main():
    """Main test runner function."""
    
    parser = argparse.ArgumentParser(description="Run Azure Billing Intelligence tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--focus", action="store_true", help="Run FOCUS compliance tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--monitoring", action="store_true", help="Run monitoring tests only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Determine test path based on arguments
    if args.integration:
        test_path = "tests/integration/"
    elif args.focus:
        test_path = "tests/focus/"
    elif args.performance:
        test_path = "tests/performance/"
    elif args.monitoring:
        test_path = "tests/monitoring/"
    else:
        test_path = "tests/"
    
    # Run tests
    exit_code = run_pytest(test_path, args.verbose)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())