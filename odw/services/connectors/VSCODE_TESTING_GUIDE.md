# VS Code Testing Guide for Azure Billing Connector

This guide explains how to set up and use VS Code's built-in test discovery and execution features with the Azure Billing Connector test suite.

## Quick Setup

### 1. Install Required Extensions

Install these VS Code extensions:

- **Python** (ms-python.python) - Core Python support
- **Python Test Explorer** (littlefoxteam.vscode-python-test-adapter) - Enhanced test UI
- **Test Explorer UI** (hbenl.vscode-test-explorer) - Test explorer interface

### 2. Configure Python Interpreter

1. Open Command Palette (`Ctrl+Shift+P`)
2. Type "Python: Select Interpreter"
3. Choose your Python environment (preferably a virtual environment with dependencies installed)

### 3. Install Dependencies

```bash
cd odw/services/connectors
python setup_test_environment.py
# OR
uv pip install -r requirements-dev.txt
```

## Test Discovery

VS Code will automatically discover tests when you:

### File Patterns

Tests are discovered in files matching:

- `test_*.py`
- `*_test.py`

### Function Patterns

Test functions must:

- Start with `test_`
- Be in classes starting with `Test`
- Use pytest or unittest format

### Current Test Files

✅ **Discoverable by VS Code:**

- `tests/test_azure_billing_pytest.py` - Main pytest-compatible tests
- `tests/conftest.py` - Pytest configuration and fixtures

❌ **Not discoverable (standalone scripts):**

- `test_azure_only_simple.py`
- `test_integration.py`
- `tests/test_azure_only.py`
- `tests/test_azure_billing_connector.py`

## VS Code Test Interface

### Test Explorer Panel

1. Open Test Explorer: `View > Test Explorer` or `Ctrl+Shift+T`
2. Tests appear in a tree structure:
   ```
   📁 Azure Billing Connector Tests
   ├── 📁 TestAzureBillingConfiguration
   │   ├── ✅ test_azure_api_config_creation
   │   ├── ✅ test_connector_config_creation
   │   └── ✅ test_billing_detail_model
   ├── 📁 TestAzureApiClient
   │   ├── ✅ test_api_client_creation
   │   ├── ✅ test_url_building
   │   └── ✅ test_header_building
   └── 📁 TestMockDataGeneration
       ├── ✅ test_mock_api_response_generation
       ├── ✅ test_mock_billing_records_generation
       └── ✅ test_mock_resource_patterns
   ```

### Running Tests

#### Individual Tests

- Click the ▶️ button next to any test
- Right-click test → "Run Test"
- Use `Ctrl+F5` when cursor is in test function

#### Test Classes

- Click ▶️ next to class name to run all tests in class
- Right-click class → "Run Test"

#### All Tests

- Click ▶️ at root level
- Command Palette → "Test: Run All Tests"
- Terminal: `python -m pytest`

#### Debug Tests

- Click 🐛 button next to test
- Right-click → "Debug Test"
- Set breakpoints in test code

### Test Status Icons

- ✅ **Passed** - Test completed successfully
- ❌ **Failed** - Test failed with error
- ⏸️ **Skipped** - Test was skipped (e.g., missing dependencies)
- ⏳ **Running** - Test is currently executing
- ❓ **Unknown** - Test hasn't been run yet

## Configuration Files

### `.vscode/settings.json`

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["tests", "--verbose", "--tb=short"],
  "python.testing.cwd": "${workspaceFolder}/odw/services/connectors"
}
```

### `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --tb=short --color=yes
```

### `tests/conftest.py`

Contains pytest fixtures and configuration shared across all tests.

## Test Categories and Markers

Tests are organized with pytest markers:

### Available Markers

- `@pytest.mark.azure_billing` - Azure Billing Connector tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.mock` - Tests using mock data

### Running Specific Categories

```bash
# Run only unit tests
python -m pytest -m unit

# Run only mock data tests
python -m pytest -m mock

# Skip slow tests
python -m pytest -m "not slow"
```

## Troubleshooting

### Tests Not Appearing

1. **Check Python Interpreter**
   - Ensure correct interpreter is selected
   - Verify dependencies are installed in that environment

2. **Refresh Test Discovery**
   - Command Palette → "Test: Refresh Tests"
   - Or restart VS Code

3. **Check File Patterns**
   - Ensure test files follow naming conventions
   - Verify files are in `tests/` directory

4. **Check Syntax**
   - Ensure no syntax errors in test files
   - Run `python -m pytest --collect-only` to verify

### Import Errors

1. **Python Path Issues**

   ```json
   "python.analysis.extraPaths": [
       "./src",
       "./tests",
       "."
   ]
   ```

2. **Missing Dependencies**

   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Module Not Found**
   - Check that `src` directory is in Python path
   - Verify `conftest.py` is setting up paths correctly

### Test Execution Failures

1. **Environment Variables**
   - Tests automatically set `TEST_MODE=true`
   - Check `.env` file if using environment-specific config

2. **Working Directory**
   - Tests run from connector directory
   - Relative paths should be from `odw/services/connectors/`

3. **Dependencies**
   - Some tests skip automatically if dependencies missing
   - Install full requirements for complete test coverage

## Advanced Features

### Test Coverage

Install pytest-cov for coverage reporting:

```bash
pip install pytest-cov
python -m pytest --cov=src --cov-report=html
```

### Parallel Testing

Install pytest-xdist for parallel execution:

```bash
pip install pytest-xdist
python -m pytest -n auto
```

### Test Debugging

1. Set breakpoints in test code
2. Click 🐛 debug button in Test Explorer
3. Use VS Code debugger features:
   - Step through code
   - Inspect variables
   - Evaluate expressions

### Custom Test Configuration

Create `.vscode/launch.json` for custom debug configurations:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Current Test",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}::${function}", "-v"],
      "cwd": "${workspaceFolder}/odw/services/connectors",
      "console": "integratedTerminal"
    }
  ]
}
```

## Best Practices

### Writing VS Code-Compatible Tests

1. **Use pytest format**:

   ```python
   class TestMyComponent:
       def test_my_function(self):
           assert my_function() == expected_result
   ```

2. **Use fixtures**:

   ```python
   def test_with_fixture(mock_data):
       result = process_data(mock_data)
       assert result is not None
   ```

3. **Add descriptive names**:

   ```python
   def test_api_client_handles_503_errors_with_retry(self):
       # Clear test purpose from name
   ```

4. **Use markers for organization**:
   ```python
   @pytest.mark.unit
   @pytest.mark.mock
   def test_mock_data_generation(self):
       pass
   ```

### Test Organization

1. **Group related tests in classes**
2. **Use descriptive class and method names**
3. **Keep tests focused and independent**
4. **Use fixtures for common setup**
5. **Add docstrings for complex tests**

## Integration with CI/CD

The pytest configuration works with continuous integration:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    cd odw/services/connectors
    python -m pytest --junitxml=test-results.xml
```

## Summary

With this setup, VS Code will:

- ✅ Automatically discover tests in `tests/test_azure_billing_pytest.py`
- ✅ Show tests in Test Explorer with clear hierarchy
- ✅ Allow running individual tests or test classes
- ✅ Provide debugging capabilities with breakpoints
- ✅ Display test results with clear pass/fail status
- ✅ Support test filtering by markers
- ✅ Integrate with pytest fixtures and configuration

The test suite is now fully compatible with VS Code's testing features while maintaining all the comprehensive testing capabilities of the original implementation.
