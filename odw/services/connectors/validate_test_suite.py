#!/usr/bin/env python3
"""
Test Suite Validation Script

This script validates that the comprehensive test suite is properly structured
and ready for execution when dependencies are available.
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSuiteValidator:
    """Validates the test suite structure and configuration"""
    
    def __init__(self):
        self.validation_results = {}
        
    def validate_file_structure(self) -> Tuple[bool, str]:
        """Validate that all test files exist"""
        required_files = [
            'run_comprehensive_tests.py',
            'test_config.py',
            'test_utils.py',
            'TEST_SUITE_README.md',
            'test_azure_only_simple.py',
            'test_integration.py',
            'tests/test_azure_only.py',
            'tests/test_azure_billing_connector.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            return False, f"Missing files: {', '.join(missing_files)}"
        else:
            return True, "All required test files present"
    
    def validate_test_config(self) -> Tuple[bool, str]:
        """Validate test configuration module"""
        try:
            # Try to import test_config
            import test_config
            
            # Check for required classes and constants
            required_items = [
                'TestConfig',
                'MockDataGenerator',
                'TestAssertions',
                'TEST_ENROLLMENT_NUMBER',
                'TEST_API_KEY'
            ]
            
            missing_items = []
            for item in required_items:
                if not hasattr(test_config, item):
                    missing_items.append(item)
            
            if missing_items:
                return False, f"Missing test_config items: {', '.join(missing_items)}"
            
            # Test basic functionality
            config = test_config.TestConfig.get_test_connector_config()
            mock_data = test_config.MockDataGenerator.generate_billing_records(5)
            
            if not config or not mock_data:
                return False, "Test config methods not working properly"
            
            return True, "Test configuration module valid"
            
        except Exception as e:
            return False, f"Test config validation failed: {str(e)}"
    
    def validate_test_utils(self) -> Tuple[bool, str]:
        """Validate test utilities module"""
        try:
            # Try to import test_utils
            import test_utils
            
            # Check for required classes
            required_classes = [
                'TestTimer',
                'MemoryMonitor',
                'MockAzureApiClient',
                'TestDataValidator',
                'TestReporter'
            ]
            
            missing_classes = []
            for cls_name in required_classes:
                if not hasattr(test_utils, cls_name):
                    missing_classes.append(cls_name)
            
            if missing_classes:
                return False, f"Missing test_utils classes: {', '.join(missing_classes)}"
            
            # Test basic instantiation
            timer = test_utils.TestTimer("test")
            validator = test_utils.TestDataValidator()
            reporter = test_utils.TestReporter()
            
            return True, "Test utilities module valid"
            
        except Exception as e:
            return False, f"Test utils validation failed: {str(e)}"
    
    def validate_test_scripts(self) -> Tuple[bool, str]:
        """Validate that test scripts are syntactically correct"""
        test_scripts = [
            'run_comprehensive_tests.py',
            'test_azure_only_simple.py',
            'test_integration.py',
            'tests/test_azure_only.py',
            'tests/test_azure_billing_connector.py'
        ]
        
        syntax_errors = []
        
        for script in test_scripts:
            try:
                with open(script, 'r') as f:
                    code = f.read()
                
                # Compile to check syntax
                compile(code, script, 'exec')
                
            except SyntaxError as e:
                syntax_errors.append(f"{script}: {str(e)}")
            except Exception as e:
                syntax_errors.append(f"{script}: {str(e)}")
        
        if syntax_errors:
            return False, f"Syntax errors: {'; '.join(syntax_errors)}"
        else:
            return True, "All test scripts have valid syntax"
    
    def validate_documentation(self) -> Tuple[bool, str]:
        """Validate test documentation"""
        try:
            with open('TEST_SUITE_README.md', 'r') as f:
                content = f.read()
            
            # Check for key sections
            required_sections = [
                '# Azure Billing Connector - Comprehensive Test Suite',
                '## Test Suite Overview',
                '## Running the Test Suite',
                '## Test Configuration',
                '## Test Categories'
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                return False, f"Missing documentation sections: {', '.join(missing_sections)}"
            
            # Check minimum length (should be comprehensive)
            if len(content) < 5000:
                return False, "Documentation appears incomplete (too short)"
            
            return True, "Test documentation is comprehensive"
            
        except Exception as e:
            return False, f"Documentation validation failed: {str(e)}"
    
    def validate_mock_data_generation(self) -> Tuple[bool, str]:
        """Validate mock data generation capabilities"""
        try:
            import test_config
            
            # Test mock API response generation
            api_response = test_config.TestConfig.get_mock_api_response(5)
            if not api_response or 'value' not in api_response:
                return False, "Mock API response generation failed"
            
            if len(api_response['value']) != 5:
                return False, "Mock API response count incorrect"
            
            # Test mock billing records
            billing_records = test_config.MockDataGenerator.generate_billing_records(10)
            if not billing_records or len(billing_records) != 10:
                return False, "Mock billing records generation failed"
            
            # Test mock resource patterns
            patterns = test_config.TestConfig.get_mock_resource_patterns()
            if not patterns or len(patterns) < 3:
                return False, "Mock resource patterns generation failed"
            
            return True, "Mock data generation working correctly"
            
        except Exception as e:
            return False, f"Mock data validation failed: {str(e)}"
    
    def run_all_validations(self) -> Dict[str, Tuple[bool, str]]:
        """Run all validation checks"""
        logger.info("=" * 70)
        logger.info("AZURE BILLING CONNECTOR - TEST SUITE VALIDATION")
        logger.info("=" * 70)
        logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        
        validations = [
            ("File Structure", self.validate_file_structure),
            ("Test Configuration", self.validate_test_config),
            ("Test Utilities", self.validate_test_utils),
            ("Test Scripts Syntax", self.validate_test_scripts),
            ("Documentation", self.validate_documentation),
            ("Mock Data Generation", self.validate_mock_data_generation)
        ]
        
        results = {}
        passed = 0
        
        for validation_name, validation_func in validations:
            try:
                success, message = validation_func()
                results[validation_name] = (success, message)
                
                status = "PASS" if success else "FAIL"
                logger.info(f"{validation_name:<25} {status}")
                
                if success:
                    passed += 1
                else:
                    logger.error(f"  {message}")
                
            except Exception as e:
                results[validation_name] = (False, f"Validation error: {str(e)}")
                logger.error(f"{validation_name:<25} ERROR")
                logger.error(f"  {str(e)}")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total Validations: {len(validations)}")
        logger.info(f"Passed:           {passed}")
        logger.info(f"Failed:           {len(validations) - passed}")
        logger.info(f"Success Rate:     {(passed / len(validations) * 100):.1f}%")
        
        if passed == len(validations):
            logger.info("")
            logger.info("🎉 ALL VALIDATIONS PASSED!")
            logger.info("The comprehensive test suite is properly structured and ready for use.")
            logger.info("")
            logger.info("Next steps:")
            logger.info("1. Install required dependencies (requests, polars, clickhouse-connect, etc.)")
            logger.info("2. Set up Azure EA API credentials for integration testing")
            logger.info("3. Configure ClickHouse connection for resource tracking tests")
            logger.info("4. Run the full test suite: python run_comprehensive_tests.py")
        else:
            logger.warning("")
            logger.warning(f"⚠️  {len(validations) - passed} validation(s) failed.")
            logger.warning("Please fix the issues above before running the test suite.")
        
        logger.info("=" * 70)
        
        return results


def main():
    """Main validation entry point"""
    validator = TestSuiteValidator()
    
    try:
        results = validator.run_all_validations()
        
        # Count failures
        failures = sum(1 for success, _ in results.values() if not success)
        
        # Exit with appropriate code
        sys.exit(0 if failures == 0 else 1)
        
    except KeyboardInterrupt:
        logger.info("\nValidation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()