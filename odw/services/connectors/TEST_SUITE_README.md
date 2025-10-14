# Azure Billing Connector - Comprehensive Test Suite

This directory contains a comprehensive test suite for the Azure Billing Connector implementation. The test suite is designed to validate all components of the connector and ensure reliable operation in production environments.

## Test Suite Overview

The test suite consists of multiple layers of testing:

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions and workflows
3. **End-to-End Tests** - Test complete data processing flows
4. **Performance Tests** - Test memory usage and processing performance

## Test Files Structure

```
odw/services/connectors/
├── run_comprehensive_tests.py     # Main test suite runner
├── test_config.py                 # Test configuration and mock data
├── test_utils.py                  # Test utilities and helpers
├── TEST_SUITE_README.md          # This documentation file
├── test_azure_only_simple.py     # Simple component tests
├── test_integration.py           # Integration tests
└── tests/
    ├── test_azure_only.py        # Azure-specific component tests
    └── test_azure_billing_connector.py  # Comprehensive component tests
```

## Running the Test Suite

### Prerequisites

Before running the test suite, install the required dependencies:

```bash
cd odw/services/connectors

# Option 1: Use the setup script (recommended)
python setup_test_environment.py

# Option 2: Manual installation with uv (fastest)
uv pip install -r requirements.txt

# Option 3: Manual installation with pip
pip install -r requirements.txt

# Option 4: Development environment (includes additional tools)
uv pip install -r requirements-dev.txt
```

### VS Code Integration

For VS Code users, the test suite includes pytest-compatible tests that integrate with VS Code's test explorer:

1. **Install VS Code Python extension**
2. **Open the connectors directory in VS Code**
3. **Tests will appear in the Test Explorer panel**
4. **Run individual tests or entire suites with one click**

See `VSCODE_TESTING_GUIDE.md` for detailed setup instructions.

### Quick Test Run

#### Option 1: Comprehensive Test Suite (All Tests)
```bash
cd odw/services/connectors
python run_comprehensive_tests.py
```

#### Option 2: Pytest (VS Code Compatible)
```bash
cd odw/services/connectors
python -m pytest tests/test_azure_billing_pytest.py -v
```

#### Option 3: Individual Test Scripts
```bash
cd odw/services/connectors
python tests/test_azure_only.py
```

### Individual Test Scripts

You can also run individual test scripts:

```bash
# Simple component validation
python test_azure_only_simple.py

# Integration tests
python test_integration.py

# Azure-specific tests
python tests/test_azure_only.py

# Full component tests
python tests/test_azure_billing_connector.py
```

## Test Configuration

The test suite uses `test_config.py` for configuration management:

- **Mock Data**: Predefined test data for consistent testing
- **Test Settings**: Timeouts, batch sizes, and other test parameters
- **Environment Variables**: Test-specific environment configuration

### Key Configuration Options

```python
# Test data settings
DEFAULT_TEST_ENROLLMENT = "123456789"
DEFAULT_TEST_API_KEY = "test-api-key-12345"
DEFAULT_BATCH_SIZE = 100

# Test timeouts
TEST_TIMEOUT_SECONDS = 300  # 5 minutes
API_TIMEOUT_SECONDS = 30

# Memory limits
MEMORY_THRESHOLD_MB = 500
```

## Test Categories

### 1. Configuration and Model Tests

Tests the Pydantic models and configuration classes:

- `AzureBillingConnectorConfig` validation
- `AzureBillingDetail` model creation
- Configuration parameter validation
- Default value handling

### 2. API Client Tests

Tests the Azure EA API client functionality:

- URL building and header construction
- Retry logic and exponential backoff
- Error handling for different HTTP status codes
- Pagination handling
- Timeout management

### 3. Resource Tracking Tests

Tests the resource tracking engine:

- Pattern loading from mock data
- Wildcard pattern matching
- Vectorized tracking application
- Audit log generation
- Conflict resolution

### 4. Data Transformation Tests

Tests the data transformation pipeline:

- Field mapping from API response to internal model
- Data type conversions
- JSON field parsing (tags, additional_info)
- Computed field derivation
- VM-specific business logic

### 5. Error Handling Tests

Tests error handling and recovery:

- API error classification
- Data processing error recovery
- Memory monitoring and cleanup
- Structured error logging

### 6. Integration Tests

Tests component integration:

- Connector factory integration
- Component initialization
- Memory monitoring
- End-to-end data flow simulation

## Test Data and Mocking

The test suite uses comprehensive mocking to avoid dependencies on external services:

### Mock Azure API Responses

```python
{
    'value': [
        {
            'instanceId': '/subscriptions/.../virtualMachines/vm1',
            'accountName': 'Test Account',
            'extendedCost': 150.75,
            'date': '2024-01-15',
            # ... additional fields
        }
    ],
    'nextLink': None
}
```

### Mock Resource Patterns

```python
[
    ("*/subscriptions/12345678-1234-1234-1234-123456789012/*", "Production App", 1),
    ("*/resourceGroups/rg-production/*", "Production Resources", 2),
    ("*/providers/Microsoft.Compute/virtualMachines/*", "Virtual Machines", 3)
]
```

## Test Utilities

The `test_utils.py` module provides helpful utilities:

### TestTimer
```python
with TestTimer("my_test") as timer:
    # Test code here
    pass
# Automatically logs execution time
```

### MemoryMonitor
```python
with MemoryMonitor("memory_test") as monitor:
    # Code that might use memory
    pass
# Automatically tracks memory usage
```

### MockAzureApiClient
```python
mock_client = MockAzureApiClient(config)
mock_client.set_responses([mock_response])
mock_client.set_failure_mode(should_fail=True, fail_after_calls=3)
```

## Test Reporting

The comprehensive test runner generates detailed reports:

### Console Output
- Real-time test execution status
- Summary statistics (pass/fail counts, success rate)
- Execution times for each test
- Memory usage monitoring

### Test Report File
- Detailed test results saved to timestamped file
- Complete output from each test
- Error details and stack traces
- Performance metrics

### Example Output
```
AZURE BILLING CONNECTOR - COMPREHENSIVE TEST SUITE
================================================================================
Started at: 2024-01-15 10:30:00

Import Test                    PASS   (0.12s)
Configuration Test             PASS   (0.08s)
Simple Azure Test              PASS   (2.45s)
Integration Test               PASS   (1.23s)
Azure Components Test          PASS   (5.67s)
Full Component Test            PASS   (8.91s)

================================================================================
TEST SUMMARY
================================================================================
Total Tests:     6
Passed:          6
Failed:          0
Success Rate:    100.0%
Total Time:      18.46s
Execution Time:  18.46s

🎉 ALL TESTS PASSED! Azure Billing Connector is ready for deployment.
```

## Performance Monitoring

The test suite includes performance monitoring:

### Memory Usage
- Tracks memory consumption during test execution
- Alerts on excessive memory usage (>500MB threshold)
- Monitors for memory leaks between tests

### Execution Time
- Times individual test execution
- Identifies slow-running tests
- Validates processing performance meets requirements

### Resource Utilization
- CPU usage monitoring during intensive operations
- I/O monitoring for file and network operations
- Garbage collection tracking

## Test Data Validation

The test suite includes comprehensive data validation:

### Billing Record Validation
- Required field presence checks
- Data type validation
- Business rule validation (positive costs, valid dates)
- JSON field structure validation

### Configuration Validation
- Required parameter checks
- Parameter type and range validation
- Default value verification
- Environment variable handling

## Continuous Integration

The test suite is designed for CI/CD integration:

### Exit Codes
- `0`: All tests passed
- `1`: One or more tests failed
- `130`: Test execution interrupted

### Test Artifacts
- Detailed test reports saved to files
- Performance metrics logged
- Error details captured for debugging

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure `src` directory is in Python path
   - Check that all required dependencies are installed

2. **Memory Issues**
   - Reduce batch sizes in test configuration
   - Check for memory leaks in test data cleanup

3. **Timeout Issues**
   - Increase timeout values in `test_config.py`
   - Check for infinite loops in test code

### Debug Mode

Enable debug logging for detailed test execution information:

```bash
export LOG_LEVEL=DEBUG
python run_comprehensive_tests.py
```

## Contributing to Tests

When adding new functionality to the Azure Billing Connector:

1. **Add Unit Tests** - Test new components in isolation
2. **Update Integration Tests** - Ensure new components integrate properly
3. **Add Mock Data** - Provide realistic test data for new scenarios
4. **Update Documentation** - Document new test cases and expected behavior

### Test Naming Conventions

- Test functions: `test_<component>_<functionality>()`
- Test files: `test_<component_name>.py`
- Mock classes: `Mock<ComponentName>`
- Test data: `get_mock_<data_type>()`

## Performance Benchmarks

The test suite establishes performance benchmarks:

- **API Response Processing**: < 1 second per 1000 records
- **Memory Usage**: < 500MB for typical batch sizes
- **Resource Tracking**: < 2 seconds per 10000 records
- **Data Transformation**: < 3 seconds per 10000 records

## Security Considerations

The test suite handles security appropriately:

- **No Real Credentials**: All tests use mock credentials
- **Data Sanitization**: Test data contains no real PII
- **Environment Isolation**: Tests don't affect production systems
- **Secure Defaults**: Test configurations use secure default values

## Future Enhancements

Planned improvements to the test suite:

1. **Property-Based Testing** - Generate random test data for edge cases
2. **Load Testing** - Test with large datasets (100k+ records)
3. **Chaos Testing** - Test resilience to random failures
4. **Performance Regression Testing** - Track performance over time
5. **Integration with Real Azure Sandbox** - Optional real API testing

---

For questions or issues with the test suite, please refer to the main Azure Billing Connector documentation or contact the development team.