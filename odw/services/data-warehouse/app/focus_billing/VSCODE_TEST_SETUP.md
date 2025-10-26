# VSCode Test Explorer Setup - FOCUS Billing

## ✅ Tests Now Available in VSCode Test Explorer

Your FOCUS billing tests are now pytest-compatible and will show in VSCode's Test Explorer!

## What Was Created

### Test Files
1. **`tests/test_moose_ingestion_workflow.py`** - 8 tests for ingestion workflow
2. **`tests/test_moose_consumption_apis.py`** - 9 tests for consumption APIs

### Configuration Files
1. **`pytest.ini`** - Pytest configuration at project root
2. **`.vscode/settings.json`** - VSCode Python test settings

## How to View Tests in VSCode

### 1. Open Test Explorer
- Click the **Flask/Beaker icon** in the left sidebar, OR
- Press `Cmd/Ctrl + Shift + T`

### 2. Refresh Tests
- Click the **Refresh** button in Test Explorer
- Tests should appear under:
  ```
  data-warehouse
  └── app
      └── focus_billing
          └── tests
              ├── test_moose_ingestion_workflow.py (8 tests)
              └── test_moose_consumption_apis.py (9 tests)
  ```

### 3. Run Tests
- **Single test**: Click play button next to test name
- **All tests in file**: Click play button next to file name
- **All tests**: Click play button at top of Test Explorer

## Test Categories

### 🟢 Unit Tests (Fast - No External Dependencies)
```
✓ test_workflow_initialization
✓ test_workflow_execution (discovers files)
✓ test_dry_run_mode
✓ test_file_filtering_by_period
✓ test_max_files_limit
```
**Run these first** - they don't require Moose to be running

### 🟡 Integration Tests (Require Moose Service)
```
⚠ test_moose_ingestion_with_real_data
⚠ test_moose_service_health
⚠ test_cost_comparison_api
⚠ test_effective_cost_analysis_api
⚠ test_commitment_discount_purchases_api
⚠ test_correction_charges_api
⚠ test_recurring_charges_api
⚠ test_api_with_filters
⚠ test_api_validation
```
**Requires**: Moose running on localhost:4200

### 🔴 E2E Tests (Full Stack)
```
🔴 test_full_ingestion_to_query_flow
```
**Requires**: Moose + ClickHouse + Data ingested

## Quick Commands

### Run Unit Tests Only (No Moose Required)
```bash
source .venv/bin/activate
pytest app/focus_billing/tests/ -m "not integration and not slow" -v
```

### Run Integration Tests (Moose Required)
```bash
# Start Moose first
.venv/bin/moose-cli dev --port 4200

# In another terminal
source .venv/bin/activate
pytest app/focus_billing/tests/ -m integration -v
```

### Run All Tests
```bash
pytest app/focus_billing/tests/ -v
```

### Run Single Test
```bash
pytest app/focus_billing/tests/test_moose_ingestion_workflow.py::TestMooseIngestionWorkflow::test_workflow_initialization -v
```

## Test Status Indicators in VSCode

- ✅ **Green checkmark** - Test passed
- ❌ **Red X** - Test failed
- 🟡 **Yellow circle** - Test skipped (e.g., Moose not running)
- ⚪ **Gray circle** - Test not run yet

## Troubleshooting

### Tests Not Showing in Test Explorer

**Problem**: Test Explorer is empty or not discovering tests

**Solutions**:
1. **Select Python Interpreter**
   - `Cmd/Ctrl + Shift + P` → "Python: Select Interpreter"
   - Choose `.venv/bin/python`

2. **Reload Window**
   - `Cmd/Ctrl + Shift + P` → "Developer: Reload Window"

3. **Check Test Configuration**
   - Open `.vscode/settings.json`
   - Verify `python.testing.pytestEnabled: true`

4. **Check Output Panel**
   - View → Output
   - Select "Python Test Log" from dropdown
   - Look for errors

5. **Manually Discover Tests**
   ```bash
   pytest --collect-only app/focus_billing/tests/
   ```

### Integration Tests Skipping

**Problem**: Tests marked as "skipped" (yellow)

**Cause**: Moose service not running

**Solution**:
```bash
# Terminal 1: Start Moose
cd /home/chris/repo/area-code/odw/services/data-warehouse
source .venv/bin/activate
.venv/bin/moose-cli dev --port 4200

# Wait for:
# - "Server listening on port 4200"
# - ClickHouse table creation logs

# Terminal 2: Run tests
source .venv/bin/activate
pytest app/focus_billing/tests/ -m integration -v
```

### Import Errors

**Problem**: `ModuleNotFoundError` when running tests

**Solutions**:
1. Check working directory:
   ```bash
   cd /home/chris/repo/area-code/odw/services/data-warehouse
   ```

2. Verify `__init__.py` files exist:
   ```bash
   ls app/focus_billing/__init__.py
   ls app/focus_billing/tests/__init__.py
   ```

3. Check Python path in test file:
   ```python
   sys.path.insert(0, str(Path(__file__).parent.parent.parent))
   ```

### Test Data Not Found

**Problem**: Tests fail with "no files discovered"

**Solution**: Verify test data exists
```bash
ls app/focus_billing/data/focus/20250701-20250731/
```

Should show multiple timestamp folders with parquet files.

## VSCode Python Extension Settings

Ensure these are set in `.vscode/settings.json`:

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "app/focus_billing/tests",
    "-v",
    "--tb=short",
    "--color=yes"
  ],
  "python.testing.autoTestDiscoverOnSaveEnabled": true,
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
}
```

## Keyboard Shortcuts

- `Cmd/Ctrl + Shift + T` - Open Test Explorer
- Click test → `F5` - Debug test
- Click test → `Cmd/Ctrl + ;` - Run test

## Next Steps

1. ✅ Open Test Explorer in VSCode
2. ✅ Verify 17 tests are discovered
3. ✅ Run unit tests (no Moose required)
4. 🟡 Start Moose service
5. 🟡 Run integration tests
6. 🟡 Run E2E test after data ingestion

## Need Help?

- See `tests/README.md` for detailed test documentation
- See `README_MOOSE_TESTING.md` for Moose setup guide
- Check VSCode Output panel → "Python Test Log" for errors
