#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for Azure Billing Connector

This script runs all available tests for the Azure Billing Connector implementation,
providing a unified test execution interface and comprehensive reporting.
"""

import sys
import os
import logging
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any
import subprocess
import importlib.util

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSuiteRunner:
    """Comprehensive test suite runner for Azure Billing Connector"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def run_test_script(self, script_path: str, test_name: str) -> Tuple[bool, str, float]:
        """Run a test script and return results"""
        logger.info(f"Running {test_name}...")
        
        start_time = time.time()
        try:
            # Run the test script as a subprocess
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                return True, result.stdout, execution_time
            else:
                return False, result.stderr or result.stdout, execution_time
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return False, "Test timed out after 5 minutes", execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            return False, f"Test execution failed: {str(e)}", execution_time
    
    def run_import_test(self, test_name: str) -> Tuple[bool, str, float]:
        """Test that all Azure billing modules can be imported"""
        start_time = time.time()
        
        try:
            # Test core module imports
            import azure_billing
            from azure_billing import (
                AzureBillingConnector,
                AzureBillingConnectorConfig,
                AzureEAApiClient,
                AzureBillingTransformer,
                ResourceTrackingEngine,
                ErrorHandler,
                AzureBillingDetail
            )
            
            # Test connector factory integration
            from connector_factory import ConnectorFactory, ConnectorType
            
            execution_time = time.time() - start_time
            return True, "All imports successful", execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            return False, f"Import failed: {str(e)}", execution_time
    
    def run_configuration_test(self, test_name: str) -> Tuple[bool, str, float]:
        """Test configuration and basic instantiation"""
        start_time = time.time()
        
        try:
            from azure_billing import AzureBillingConnectorConfig, AzureBillingConnector
            from datetime import datetime
            
            # Test configuration creation
            config = AzureBillingConnectorConfig(
                azure_enrollment_number="123456789",
                azure_api_key="test-api-key",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                batch_size=100
            )
            
            # Test connector creation
            connector = AzureBillingConnector(config)
            
            # Test component initialization
            connector._initialize_components()
            
            execution_time = time.time() - start_time
            return True, "Configuration and instantiation successful", execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            return False, f"Configuration test failed: {str(e)}", execution_time
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all available tests"""
        self.start_time = datetime.now()
        logger.info("=" * 80)
        logger.info("AZURE BILLING CONNECTOR - COMPREHENSIVE TEST SUITE")
        logger.info("=" * 80)
        logger.info(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        
        # Define test suite
        test_suite = [
            # Basic functionality tests
            ("Import Test", self.run_import_test),
            ("Configuration Test", self.run_configuration_test),
            
            # Existing test scripts
            ("Simple Azure Test", lambda name: self.run_test_script("test_azure_only_simple.py", name)),
            ("Integration Test", lambda name: self.run_test_script("test_integration.py", name)),
            ("Azure Components Test", lambda name: self.run_test_script("tests/test_azure_only.py", name)),
            ("Full Component Test", lambda name: self.run_test_script("tests/test_azure_billing_connector.py", name)),
        ]
        
        # Run each test
        for test_name, test_func in test_suite:
            try:
                success, output, execution_time = test_func(test_name)
                
                self.test_results[test_name] = {
                    'success': success,
                    'output': output,
                    'execution_time': execution_time,
                    'timestamp': datetime.now()
                }
                
                status = "PASS" if success else "FAIL"
                logger.info(f"{test_name:<30} {status:<6} ({execution_time:.2f}s)")
                
                if not success:
                    logger.error(f"  Error: {output[:200]}...")
                
            except Exception as e:
                self.test_results[test_name] = {
                    'success': False,
                    'output': f"Test runner error: {str(e)}",
                    'execution_time': 0,
                    'timestamp': datetime.now()
                }
                logger.error(f"{test_name:<30} ERROR  Test runner failed: {str(e)}")
            
            logger.info("")
        
        self.end_time = datetime.now()
        return self.generate_summary()
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        total_time = (self.end_time - self.start_time).total_seconds()
        execution_time = sum(result['execution_time'] for result in self.test_results.values())
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_time': total_time,
            'execution_time': execution_time,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'test_results': self.test_results
        }
        
        # Print summary
        logger.info("=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests:     {total_tests}")
        logger.info(f"Passed:          {passed_tests}")
        logger.info(f"Failed:          {failed_tests}")
        logger.info(f"Success Rate:    {summary['success_rate']:.1f}%")
        logger.info(f"Total Time:      {total_time:.2f}s")
        logger.info(f"Execution Time:  {execution_time:.2f}s")
        logger.info("")
        
        # Detailed results
        logger.info("DETAILED RESULTS:")
        logger.info("-" * 80)
        for test_name, result in self.test_results.items():
            status = "PASS" if result['success'] else "FAIL"
            logger.info(f"{test_name:<30} {status:<6} ({result['execution_time']:.2f}s)")
            
            if not result['success']:
                # Show first few lines of error
                error_lines = result['output'].split('\n')[:3]
                for line in error_lines:
                    if line.strip():
                        logger.info(f"  {line}")
        
        logger.info("=" * 80)
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! Azure Billing Connector is ready for deployment.")
        else:
            logger.warning(f"⚠️  {failed_tests} test(s) failed. Review the detailed output above.")
        
        logger.info(f"Completed at: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return summary
    
    def save_test_report(self, filename: str = None) -> str:
        """Save detailed test report to file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"azure_billing_test_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w') as f:
                f.write("AZURE BILLING CONNECTOR - COMPREHENSIVE TEST REPORT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Test Duration: {(self.end_time - self.start_time).total_seconds():.2f}s\n")
                f.write("\n")
                
                # Summary
                total_tests = len(self.test_results)
                passed_tests = sum(1 for result in self.test_results.values() if result['success'])
                f.write(f"SUMMARY: {passed_tests}/{total_tests} tests passed\n")
                f.write("\n")
                
                # Detailed results
                for test_name, result in self.test_results.items():
                    f.write(f"TEST: {test_name}\n")
                    f.write(f"Status: {'PASS' if result['success'] else 'FAIL'}\n")
                    f.write(f"Execution Time: {result['execution_time']:.2f}s\n")
                    f.write(f"Timestamp: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("Output:\n")
                    f.write(result['output'])
                    f.write("\n" + "-" * 80 + "\n")
            
            logger.info(f"Test report saved to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save test report: {str(e)}")
            return None


def main():
    """Main test runner entry point"""
    runner = TestSuiteRunner()
    
    try:
        # Run all tests
        summary = runner.run_all_tests()
        
        # Save detailed report
        report_file = runner.save_test_report()
        
        # Exit with appropriate code
        if summary['failed_tests'] == 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\nTest execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test runner failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()