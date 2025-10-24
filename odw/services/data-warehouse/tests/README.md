# Azure Billing Intelligence Test Suite

Comprehensive test suite for the Azure Billing Intelligence (bia) system, covering integration testing, FOCUS compliance validation, performance testing, and system monitoring.

## Test Structure

```
tests/
├── conftest.py                     # Pytest configuration and fixtures
├── test_basic.py                   # Basic functionality tests
├── run_tests.py                    # Test runner script
├── integration/                    # End-to-end integration tests
│   ├── test_end_to_end_workflow.py # Complete workflow testing
│   └── test_plugin_integration.py  # Plugin system integration
├── focus/                          # FOCUS compliance tests
│   └── test_focus_compliance.py    # FOCUS specification adherence
├── performance/                    # Performance and load tests
│   ├── test_load_testing.py        # High-volume data processing
│   └── test_clickhouse_performance.py # Database performance
└── monitoring/                     # System monitoring tests
    ├── test_system_monitoring.py   # Health checks and metrics
    └── test_alerting_system.py     # Alert generation and handling
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
uv add --dev pytest pytest-asyncio testcontainers black ruff mypy
```

### Run All Tests
```bash
python tests/run_tests.py
```

### Run Specific Test Suites
```bash
# Integration tests only
python tests/run_tests.py --integration

# FOCUS compliance tests only
python tests/run_tests.py --focus

# Performance tests only
python tests/run_tests.py --performance

# Monitoring tests only
python tests/run_tests.py --monitoring
```

### Run Individual Tests
```bash
# Basic functionality
python -m pytest tests/test_basic.py -v

# Specific test class
python -m pytest tests/integration/test_end_to_end_workflow.py::TestEndToEndWorkflow -v

# Specific test method
python -m pytest tests/focus/test_focus_compliance.py::TestFOCUSCompliance::test_required_focus_fields_present -v
```

## Test Categories

### Integration Tests
- **End-to-End Workflow**: Tests complete Azure billing data extraction to analytics flow
- **Plugin Integration**: Tests plugin installation, configuration, and workflow integration
- **Data Transformation**: Tests Azure NCEI to FOCUS data transformation accuracy

### FOCUS Compliance Tests
- **Field Validation**: Ensures all required FOCUS fields are present and correctly formatted
- **Data Type Compliance**: Validates FOCUS data type requirements
- **Business Rules**: Tests FOCUS specification business rules and constraints
- **Transformation Accuracy**: Verifies accurate mapping from Azure data to FOCUS format

### Performance Tests
- **Load Testing**: Tests high-volume billing data processing capabilities
- **Concurrent Execution**: Tests scalability with concurrent workflow execution
- **Memory Management**: Tests memory usage patterns under load
- **ClickHouse Performance**: Tests database query performance and optimization

### Monitoring Tests
- **System Health**: Tests system health monitoring and status checks
- **Performance Metrics**: Tests performance metrics collection and monitoring
- **Alerting System**: Tests alert generation for failures and performance issues
- **Data Quality Monitoring**: Tests data quality issue detection and alerting

## Test Configuration

### Fixtures Available
- `mock_azure_blob_client`: Mock Azure Blob Storage client
- `mock_temporal_client`: Mock Temporal workflow client
- `mock_clickhouse_client`: Mock ClickHouse database client
- `mock_plugin_integration_service`: Mock plugin integration service
- `sample_azure_billing_data`: Sample billing data for testing
- `sample_plugin_config`: Sample plugin configurations
- `workflow_test_params`: Test parameters for workflow execution

### Environment Variables
Set these environment variables for integration testing:
```bash
export AZURE_STORAGE_ACCOUNT_URL="https://test.blob.core.windows.net"
export AZURE_STORAGE_CONTAINER="test-container"
export CLICKHOUSE_HOST="localhost"
export CLICKHOUSE_PORT="8123"
export TEMPORAL_HOST="localhost"
export TEMPORAL_PORT="7233"
```

## Coverage Reports

Test coverage reports are generated in `tests/coverage_html/` when running tests with the test runner script.

## Continuous Integration

These tests are designed to run in CI/CD pipelines with:
- Docker containers for external dependencies (PostgreSQL, ClickHouse, Redis)
- Mock services for Azure APIs
- Configurable test environments
- Parallel test execution support

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Install all test dependencies with `uv add --dev`
2. **Import Errors**: Ensure the Azure billing modules are properly installed
3. **Container Issues**: Ensure Docker is running for testcontainer-based tests
4. **Async Test Issues**: Ensure pytest-asyncio is properly configured

### Debug Mode
Run tests with verbose output and debugging:
```bash
python -m pytest tests/ -v -s --tb=long
```