#!/usr/bin/env python3
"""
Test Utilities for Azure Billing Connector Test Suite

This module provides utility functions and classes to support testing
of the Azure Billing Connector implementation.
"""

import sys
import os
import time
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Callable, Union
from contextlib import contextmanager
from unittest.mock import Mock, MagicMock
import json

# Optional dependency handling
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logger = logging.getLogger(__name__)


class TestTimer:
    """Context manager for timing test execution"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.debug(f"Starting test: {self.test_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
        if exc_type is None:
            logger.debug(f"Test completed: {self.test_name} ({self.duration:.2f}s)")
        else:
            logger.debug(f"Test failed: {self.test_name} ({self.duration:.2f}s) - {exc_type.__name__}: {exc_val}")


class MemoryMonitor:
    """Monitor memory usage during tests"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_memory = None
        self.end_memory = None
        self.peak_memory = None
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process()
        else:
            self.process = None
    
    def __enter__(self):
        self.start_memory = self.get_memory_usage()
        self.peak_memory = self.start_memory
        if self.start_memory is not None:
            logger.debug(f"Memory at start of {self.test_name}: {self.start_memory:.1f}MB")
        else:
            logger.debug(f"Memory monitoring not available for {self.test_name} (psutil not installed)")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_memory = self.get_memory_usage()
        
        if self.start_memory is not None and self.end_memory is not None:
            memory_delta = self.end_memory - self.start_memory
            logger.debug(f"Memory at end of {self.test_name}: {self.end_memory:.1f}MB (Δ{memory_delta:+.1f}MB)")
            
            if memory_delta > 100:  # Alert if memory increased by more than 100MB
                logger.warning(f"High memory usage in {self.test_name}: {memory_delta:.1f}MB increase")
    
    def get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB"""
        if not PSUTIL_AVAILABLE or self.process is None:
            return None
        try:
            return self.process.memory_info().rss / 1024 / 1024
        except Exception:
            return None
    
    def update_peak(self):
        """Update peak memory usage"""
        current = self.get_memory_usage()
        if current is not None and (self.peak_memory is None or current > self.peak_memory):
            self.peak_memory = current


class MockAzureApiClient:
    """Mock Azure EA API client for testing"""
    
    def __init__(self, config: Any):
        self.config = config
        self.call_count = 0
        self.responses = []
        self.should_fail = False
        self.fail_after_calls = None
        
    def set_responses(self, responses: List[Dict[str, Any]]):
        """Set mock responses to return"""
        self.responses = responses
    
    def set_failure_mode(self, should_fail: bool, fail_after_calls: Optional[int] = None):
        """Configure failure behavior"""
        self.should_fail = should_fail
        self.fail_after_calls = fail_after_calls
    
    def fetch_billing_data(self, month: str, page_url: Optional[str] = None) -> tuple:
        """Mock fetch billing data method"""
        self.call_count += 1
        
        # Check if we should fail
        if self.should_fail:
            if self.fail_after_calls is None or self.call_count > self.fail_after_calls:
                raise Exception(f"Mock API failure after {self.call_count} calls")
        
        # Return mock response
        if self.responses:
            response_index = (self.call_count - 1) % len(self.responses)
            response = self.responses[response_index]
            return response.get('value', []), response.get('nextLink')
        else:
            # Default response
            return [], None
    
    def get_billing_data_url(self, month: str) -> str:
        """Mock URL building"""
        return f"{self.config.base_url}/{self.config.enrollment_number}/billingPeriods/{month}/usagedetails"
    
    def _build_headers(self) -> Dict[str, str]:
        """Mock header building"""
        return {'Authorization': f'bearer {self.config.api_key}'}


class MockResourceTrackingEngine:
    """Mock resource tracking engine for testing"""
    
    def __init__(self):
        self.patterns = [
            ("*/subscriptions/12345678-1234-1234-1234-123456789012/*", "Production App", 1),
            ("*/resourceGroups/rg-production/*", "Production Resources", 2),
            ("*/providers/Microsoft.Compute/virtualMachines/*", "Virtual Machines", 3)
        ]
        self.load_patterns_called = False
        self.apply_tracking_called = False
    
    def load_patterns(self) -> List[tuple]:
        """Mock pattern loading"""
        self.load_patterns_called = True
        return self.patterns
    
    def apply_tracking(self, df: Any) -> tuple:
        """Mock tracking application"""
        self.apply_tracking_called = True
        
        # Create mock tracking series (all records get "Production App")
        import polars as pl
        tracking_series = pl.Series("resource_tracking", ["Production App"] * len(df))
        
        # Create mock audit DataFrame
        audit_df = pl.DataFrame({
            'instance_id': [],
            'matched_patterns': [],
            'selected_tracking': [],
            'conflict_count': []
        })
        
        return tracking_series, audit_df


class TestDataValidator:
    """Validate test data and results"""
    
    @staticmethod
    def validate_billing_record(record: Dict[str, Any]) -> List[str]:
        """Validate a billing record and return list of errors"""
        errors = []
        
        # Required fields
        required_fields = ['instance_id', 'month_date']
        for field in required_fields:
            if field not in record:
                errors.append(f"Missing required field: {field}")
            elif record[field] is None:
                errors.append(f"Required field is None: {field}")
        
        # Data type validations
        if 'extended_cost' in record and record['extended_cost'] is not None:
            if not isinstance(record['extended_cost'], (int, float)):
                errors.append("extended_cost must be numeric")
            elif record['extended_cost'] < 0:
                errors.append("extended_cost cannot be negative")
        
        if 'consumed_quantity' in record and record['consumed_quantity'] is not None:
            if not isinstance(record['consumed_quantity'], (int, float)):
                errors.append("consumed_quantity must be numeric")
            elif record['consumed_quantity'] < 0:
                errors.append("consumed_quantity cannot be negative")
        
        # Date validations
        if 'month_date' in record and record['month_date'] is not None:
            if not isinstance(record['month_date'], date):
                errors.append("month_date must be a date object")
        
        return errors
    
    @staticmethod
    def validate_connector_config(config: Any) -> List[str]:
        """Validate connector configuration"""
        errors = []
        
        required_attrs = ['azure_enrollment_number', 'azure_api_key']
        for attr in required_attrs:
            if not hasattr(config, attr):
                errors.append(f"Missing required attribute: {attr}")
            elif getattr(config, attr) is None:
                errors.append(f"Required attribute is None: {attr}")
        
        # Validate batch size
        if hasattr(config, 'batch_size') and config.batch_size is not None:
            if not isinstance(config.batch_size, int) or config.batch_size <= 0:
                errors.append("batch_size must be a positive integer")
        
        return errors
    
    @staticmethod
    def validate_api_response(response: Dict[str, Any]) -> List[str]:
        """Validate API response structure"""
        errors = []
        
        if 'value' not in response:
            errors.append("API response missing 'value' field")
        elif not isinstance(response['value'], list):
            errors.append("API response 'value' must be a list")
        
        # Validate individual records
        if 'value' in response:
            for i, record in enumerate(response['value']):
                if not isinstance(record, dict):
                    errors.append(f"Record {i} is not a dictionary")
                    continue
                
                # Check for essential fields
                essential_fields = ['instanceId', 'date', 'extendedCost']
                for field in essential_fields:
                    if field not in record:
                        errors.append(f"Record {i} missing essential field: {field}")
        
        return errors


class TestReporter:
    """Generate test reports and summaries"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def start_test_run(self):
        """Mark the start of a test run"""
        self.start_time = datetime.now()
        self.test_results = {}
    
    def end_test_run(self):
        """Mark the end of a test run"""
        self.end_time = datetime.now()
    
    def record_test_result(self, test_name: str, success: bool, 
                          execution_time: float, output: str = "", 
                          error: Optional[Exception] = None):
        """Record the result of a test"""
        self.test_results[test_name] = {
            'success': success,
            'execution_time': execution_time,
            'output': output,
            'error': str(error) if error else None,
            'timestamp': datetime.now()
        }
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate test run summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        total_time = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        execution_time = sum(result['execution_time'] for result in self.test_results.values())
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_time': total_time,
            'execution_time': execution_time,
            'start_time': self.start_time,
            'end_time': self.end_time
        }
    
    def print_summary(self):
        """Print test summary to console"""
        summary = self.generate_summary()
        
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests:     {summary['total_tests']}")
        print(f"Passed:          {summary['passed_tests']}")
        print(f"Failed:          {summary['failed_tests']}")
        print(f"Success Rate:    {summary['success_rate']:.1f}%")
        print(f"Total Time:      {summary['total_time']:.2f}s")
        print(f"Execution Time:  {summary['execution_time']:.2f}s")
        print("=" * 60)


@contextmanager
def temporary_environment_vars(env_vars: Dict[str, str]):
    """Temporarily set environment variables for testing"""
    original_values = {}
    
    # Save original values and set new ones
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        yield
    finally:
        # Restore original values
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


def run_test_with_timeout(test_func: Callable, timeout_seconds: int = 60) -> tuple:
    """Run a test function with timeout"""
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Test timed out after {timeout_seconds} seconds")
    
    # Set up timeout
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        start_time = time.time()
        result = test_func()
        execution_time = time.time() - start_time
        return True, result, execution_time, None
    except Exception as e:
        execution_time = time.time() - start_time
        return False, None, execution_time, e
    finally:
        # Clean up timeout
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def compare_dataframes(df1: Any, df2: Any, tolerance: float = 0.001) -> List[str]:
    """Compare two DataFrames and return list of differences"""
    differences = []
    
    # Check shapes
    if df1.shape != df2.shape:
        differences.append(f"Shape mismatch: {df1.shape} vs {df2.shape}")
        return differences
    
    # Check columns
    if set(df1.columns) != set(df2.columns):
        differences.append(f"Column mismatch: {set(df1.columns)} vs {set(df2.columns)}")
    
    # Check data (simplified comparison)
    try:
        for col in df1.columns:
            if col in df2.columns:
                # For numeric columns, use tolerance
                if df1[col].dtype in ['float64', 'float32', 'int64', 'int32']:
                    if not df1[col].equals(df2[col]):
                        differences.append(f"Data mismatch in column: {col}")
                else:
                    if not df1[col].equals(df2[col]):
                        differences.append(f"Data mismatch in column: {col}")
    except Exception as e:
        differences.append(f"Error comparing data: {str(e)}")
    
    return differences


# Export commonly used utilities
__all__ = [
    'TestTimer',
    'MemoryMonitor', 
    'MockAzureApiClient',
    'MockResourceTrackingEngine',
    'TestDataValidator',
    'TestReporter',
    'temporary_environment_vars',
    'run_test_with_timeout',
    'compare_dataframes'
]