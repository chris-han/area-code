# FOCUS Billing Tests - VSCode Test Explorer

## Test Files

The tests are now pytest-compatible and will show in VSCode's Test Explorer:

### 1. `test_moose_ingestion_workflow.py`
**Unit & Integration tests for data ingestion**

Tests:
- ✓ `test_workflow_initialization` - Workflow setup
- ✓ `test_workflow_execution` - Basic execution
- ✓ `test_moose_ingestion_with_real_data` - Full ingestion (requires Moose)
- ✓ `test_dry_run_mode` - Dry-run validation
- ✓ `test_file_filtering_by_period` - Period filter logic
- ✓ `test_max_files_limit` - File limit enforcement

Markers:
- `@pytest.mark.integration` - Requires Moose service running
- `@pytest.mark.slow` - Performance tests

### 2. `test_moose_consumption_apis.py`
**Integration tests for FOCUS consumption APIs**

Tests:
- ✓ `test_moose_service_health` - Service availability
- ✓ `test_cost_comparison_api` - Cost Comparison API
- ✓ `test_effective_cost_analysis_api` - Effective Cost Analysis API
- ✓ `test_commitment_discount_purchases_api` - Commitment Purchases API
- ✓ `test_correction_charges_api` - Corrections API
- ✓ `test_recurring_charges_api` - Recurring Charges API
- ✓ `test_api_with_filters` - Filter parameters
- ✓ `test_api_validation` - Input validation
- ✓ `test_full_ingestion_to_query_flow` - End-to-end flow

Markers:
- `@pytest.mark.integration` - Requires Moose service
- `@pytest.mark.asyncio` - Async test
- `@pytest.mark.e2e` - End-to-end test

## Running Tests

### VSCode Test Explorer
1. Open Test Explorer panel (flask icon in sidebar)
2. Tests should appear under `app/focus_billing/tests/`
3. Click play button to run individual or all tests

### Command Line

```bash
# Run all tests
pytest app/focus_billing/tests/ -v

# Run only unit tests (fast, no external services)
pytest app/focus_billing/tests/ -v -m "not integration and not slow"

# Run only integration tests (requires Moose)
pytest app/focus_billing/tests/ -v -m integration

# Run specific test file
pytest app/focus_billing/tests/test_moose_ingestion_workflow.py -v

# Run specific test
pytest app/focus_billing/tests/test_moose_ingestion_workflow.py::TestMooseIngestionWorkflow::test_workflow_initialization -v

# Run with output
pytest app/focus_billing/tests/ -v -s

# Run async tests
pytest app/focus_billing/tests/test_moose_consumption_apis.py -v
```

## Test Markers

Markers help categorize tests:

```python
@pytest.mark.unit          # Fast unit tests (default)
@pytest.mark.integration   # Requires external services (Moose, ClickHouse)
@pytest.mark.slow          # Takes >5 seconds
@pytest.mark.e2e           # End-to-end workflow tests
@pytest.mark.asyncio       # Async test with httpx
```

Filter by markers:
```bash
# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Run E2E tests only
pytest -m e2e
```

## Prerequisites

### For Unit Tests (no markers)
- Python 3.12+
- pytest installed
- Test data at `app/focus_billing/data/focus/`

### For Integration Tests (@pytest.mark.integration)
- **Moose service running** on `localhost:4200`
  ```bash
  .venv/bin/moose-cli dev --port 4200
  ```
- ClickHouse accessible (managed by Moose)
- FocusCostUsage table created

### For E2E Tests (@pytest.mark.e2e)
- All integration prerequisites
- Data already ingested in ClickHouse
- Consumption APIs registered

## VSCode Configuration

### .vscode/settings.json
```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "app/focus_billing/tests",
    "-v",
    "--tb=short"
  ],
  "python.testing.autoTestDiscoverOnSaveEnabled": true
}
```

## Troubleshooting

### Tests not appearing in VSCode
1. Ensure Python extension is installed
2. Select correct Python interpreter (`.venv/bin/python`)
3. Reload window: `Cmd/Ctrl + Shift + P` → "Reload Window"
4. Check Output panel → "Python Test Log" for errors

### Integration tests failing
- Verify Moose is running: `curl http://localhost:4200/health`
- Check Moose logs for errors
- Ensure test data exists: `ls app/focus_billing/data/focus/20250701-20250731/`

### Async tests failing
- Install `pytest-asyncio`: `pip install pytest-asyncio`
- Check `pytest.ini` has `asyncio_mode = auto`

### Import errors
- Ensure working directory is correct
- Check PYTHONPATH includes app directory
- Verify all `__init__.py` files exist

## Test Data

Tests use real parquet files from:
```
app/focus_billing/data/focus/
├── 20250701-20250731/ (22 files)
├── 20250801-20250831/ (38 files)
└── 20250901-20250930/ (37 files)
```

Default test period: `20250701-20250731`

## CI/CD Integration

For CI pipelines:
```bash
# Install dependencies
pip install pytest pytest-asyncio httpx

# Run unit tests only (no external services)
pytest -m "not integration and not slow" --junitxml=test-results.xml

# Run with coverage
pytest --cov=app/focus_billing --cov-report=html --cov-report=term
```

## Next Steps

1. Run unit tests to verify setup
2. Start Moose service
3. Run integration tests
4. Check results in Test Explorer
5. Add more test cases as needed
