# FOCUS Billing End-to-End Testing Guide

This document describes the comprehensive end-to-end testing suite for the FOCUS billing integration, including smoke tests, verification tests, and system validation.

## Overview

The end-to-end testing suite validates the complete FOCUS billing integration workflow:

1. **Smoke Tests** - Basic functionality validation with minimal test data
2. **Verification Tests** - Comparison against existing FOCUS MCP server results
3. **System Health Checks** - Configuration and connectivity validation
4. **ClickHouse Local Verification** - Offline query validation for CI environments

## Test Components

### 1. Smoke Test Suite (`test_smoke_suite.py`)

Validates core functionality with minimal sample data:

- **Data Ingestion**: Ingest small Parquet sample and verify table population
- **API Functionality**: Execute YAML queries via API to confirm round-trip functionality
- **Data Integrity**: Validate data transformation correctness and computed columns
- **Error Handling**: Test API error handling for invalid inputs
- **Performance Baseline**: Establish performance benchmarks for key operations

**Key Features:**
- Creates minimal test data (10 rows) for fast execution
- Tests complete data flow from Parquet ingestion to query execution
- Validates data transformation (PascalCase → snake_case)
- Checks computed columns (id, source_system, created_at, updated_at)
- Measures performance baselines for optimization tracking

### 2. Verification Test Suite (`test_verification_suite.py`)

Compares results against existing FOCUS MCP server validation:

- **Query Catalog Coverage**: Verify our queries match verification results
- **Result Comparison**: Execute queries and compare row counts with expected results
- **Zero-Row Cases**: Document expected zero-row cases (contracted savings)
- **ClickHouse Local Compatibility**: Check compatibility with offline verification
- **Sample Data Validation**: Validate sample data format consistency

**Key Features:**
- Uses `verification_results_clickhouse.json` as ground truth
- Handles expected zero-row cases for contracted savings queries
- Provides detailed comparison reports
- Identifies queries missing from catalog or verification results
- Documents compatibility issues for CI environments

### 3. System Health Checks

Validates system configuration and connectivity:

- **Configuration Validation**: Check all required configuration parameters
- **ClickHouse Connectivity**: Verify database connection and table existence
- **Query Catalog Health**: Validate query loading and structure
- **Data Path Accessibility**: Check file system paths and permissions

### 4. ClickHouse Local Verification (`run_clickhouse_local_verification.py`)

Enables offline query validation for CI environments:

- **Parquet File Discovery**: Find and validate FOCUS Parquet files
- **Schema Adaptation**: Adapt queries to work with `file()` function
- **Query Execution**: Run queries using clickhouse-local
- **Result Comparison**: Compare with expected verification results

## Running Tests

### Quick Start

```bash
# Run complete test suite
cd odw/services/data-warehouse
python app/focus_billing/run_end_to_end_tests.py

# Run with verbose output
python app/focus_billing/run_end_to_end_tests.py --verbose

# Run specific test suites
python app/focus_billing/run_end_to_end_tests.py --smoke-only
python app/focus_billing/run_end_to_end_tests.py --verification-only
python app/focus_billing/run_end_to_end_tests.py --health-only
```

### CI Mode

```bash
# CI mode (continue on failures, generate reports)
python app/focus_billing/run_end_to_end_tests.py --ci --output test_results.json
```

### ClickHouse Local Verification

```bash
# Run offline verification (requires clickhouse-local in PATH)
python app/focus_billing/run_clickhouse_local_verification.py

# Specify custom data directory
python app/focus_billing/run_clickhouse_local_verification.py \
  --data-root /path/to/focus/data \
  --output verification_results.json
```

### Individual Test Files

```bash
# Run smoke tests only
python -m pytest app/focus_billing/tests/test_smoke_suite.py -v

# Run verification tests only  
python -m pytest app/focus_billing/tests/test_verification_suite.py -v

# Run with specific test method
python -m pytest app/focus_billing/tests/test_smoke_suite.py::TestFocusBillingSmokeTests::test_smoke_data_ingestion_and_table_population -v
```

## Test Data Requirements

### Smoke Tests
- Creates temporary test data automatically
- Requires ClickHouse connection for actual ingestion tests
- Uses minimal 10-row dataset for fast execution

### Verification Tests
- Requires `focus-mcp-main/verification_results_clickhouse.json`
- Uses existing FOCUS query catalog
- May require actual FOCUS data for meaningful comparisons

### ClickHouse Local Tests
- Requires `clickhouse-local` binary in PATH
- Requires FOCUS Parquet files in configured data directory
- Works offline without ClickHouse server

## Expected Results

### Success Criteria

**Smoke Tests:**
- All ingestion workflows complete successfully
- APIs respond with valid data structures
- Data transformation produces expected column names and types
- Performance metrics within acceptable ranges

**Verification Tests:**
- At least 70% of queries execute successfully
- Row count differences documented and explained
- Zero-row cases properly identified and documented
- Query catalog coverage above 80%

**System Health:**
- All configuration parameters loaded correctly
- ClickHouse connectivity established
- Query catalog loads without errors
- Critical data paths accessible

### Expected Failures

Some test failures are expected and acceptable:

1. **Zero-Row Queries**: Many contracted savings queries return zero rows with test data
2. **Missing Data**: Some queries require specific data not present in test datasets
3. **Environment Differences**: Local vs production schema differences
4. **ClickHouse Local Limitations**: Some queries may not work with clickhouse-local

## Troubleshooting

### Common Issues

**"No Parquet files found"**
- Check `FOCUS_DATA_ROOT` environment variable
- Verify FOCUS data directory structure
- Ensure Parquet files exist in expected locations

**"ClickHouse connection failed"**
- Verify ClickHouse server is running
- Check connection parameters in `moose.config.toml`
- Ensure database and tables exist

**"Query catalog empty"**
- Check `focus-mcp-main/resources/queries/` directory exists
- Verify YAML query files are properly formatted
- Check file permissions

**"clickhouse-local not found"**
- Install ClickHouse client tools
- Add clickhouse-local to PATH
- Use alternative verification methods

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Set debug environment variables
export FOCUS_DEBUG=true
export CLICKHOUSE_LOG_LEVEL=debug

# Run tests with maximum verbosity
python app/focus_billing/run_end_to_end_tests.py --verbose
```

### Manual Verification

For manual testing and debugging:

```python
# Test configuration loading
from app.focus_billing.config import focus_config
print(focus_config.validate_paths())

# Test query catalog
from app.focus_billing.query_loader import FocusQueryLoader
loader = FocusQueryLoader()
queries = loader.load_all_queries()
print(f"Loaded {len(queries)} queries")

# Test ClickHouse connectivity
from app.focus_billing.observability import focus_observability
status = focus_observability.verify_tables_exist()
print(status)
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: FOCUS Billing Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          
      - name: Install ClickHouse Local
        run: |
          curl https://clickhouse.com/ | sh
          sudo ./clickhouse install
          
      - name: Run FOCUS Tests
        run: |
          cd odw/services/data-warehouse
          python app/focus_billing/run_end_to_end_tests.py --ci --output test_results.json
          
      - name: Upload Test Results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: test_results.json
```

### Test Result Artifacts

The test runner generates JSON reports with detailed results:

```json
{
  "start_time": "2025-01-01T12:00:00",
  "smoke_tests": {
    "success": true,
    "exit_code": 0
  },
  "verification_tests": {
    "success": true,
    "exit_code": 0
  },
  "system_health": {
    "configuration": {"success": true},
    "clickhouse_connectivity": {"success": true}
  },
  "summary": {
    "overall_success": true,
    "recommendations": ["All tests passed - FOCUS billing integration is healthy"]
  }
}
```

## Performance Benchmarks

The test suite establishes performance baselines:

- **Query Catalog Loading**: < 5 seconds
- **API Response Time**: < 2 seconds  
- **Simple Query Execution**: < 10 seconds
- **Data Ingestion (10 rows)**: < 30 seconds

Monitor these metrics over time to detect performance regressions.

## Contributing

When adding new tests:

1. Follow existing test patterns and naming conventions
2. Add appropriate fixtures for test data
3. Include both positive and negative test cases
4. Document expected failures and their reasons
5. Update this documentation with new test descriptions

For questions or issues with the testing suite, refer to the main FOCUS billing documentation or create an issue in the project repository.