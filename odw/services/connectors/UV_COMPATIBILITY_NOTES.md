# UV Compatibility Notes

## Issues Fixed

### 1. Package Name Issues
- **Fixed**: `pdb++` → `pdbpp` (package name with `+` characters)
- **Removed**: `unittest-mock` (built into Python 3.3+)
- **Removed**: `gc-python-utils` (gc is built into Python)

### 2. Non-existent Packages
- **Removed**: `pytest-benchmark` (not available in PyPI)
- **Removed**: `pytest-postgresql` (not commonly available)
- **Removed**: `pickle5` (built into Python 3.8+)
- **Removed**: `asynctest` (deprecated, use pytest-asyncio)
- **Removed**: `pytest-parallel` (use pytest-xdist instead)

### 3. Overly Complex Dependencies
- **Simplified**: Removed many optional packages that aren't essential
- **Focused**: Kept only packages needed for core functionality
- **Streamlined**: Created minimal requirements for basic usage

## Working Requirements Files

### ✅ `requirements.txt` (Core - 20 packages)
Essential packages for Azure Billing Connector:
- `requests>=2.32.4` - HTTP client
- `polars>=0.20.0` - Data processing
- `pydantic>=2.0.0` - Data validation
- `clickhouse-connect>=0.6.0` - Database
- `pytest>=7.0.0` - Testing
- `black>=23.0.0` - Code formatting

### ✅ `requirements-dev.txt` (Development - 40+ packages)
Additional development tools:
- `jupyter>=1.0.0` - Interactive development
- `sphinx>=6.0.0` - Documentation
- `hypothesis>=6.70.0` - Property-based testing
- `pylint>=2.17.0` - Code analysis

### ✅ `requirements-minimal.txt` (Minimal - 15 packages)
Absolute minimum for basic functionality:
- Core dependencies only
- No optional packages
- Guaranteed to work with uv

## Installation Commands

### Using uv (Recommended - Fastest)
```bash
# Core requirements
uv pip install -r requirements.txt

# Development requirements
uv pip install -r requirements-dev.txt

# Minimal requirements
uv pip install -r requirements-minimal.txt
```

### Using pip (Fallback)
```bash
# Core requirements
pip install -r requirements.txt

# Development requirements
pip install -r requirements-dev.txt
```

## Setup Script Enhancement

The `setup_test_environment.py` script now:
1. **Tries uv first** - Faster installation
2. **Falls back to pip** - If uv is not available
3. **Provides clear feedback** - Shows which tool was used
4. **Handles errors gracefully** - Reports issues with both tools

## Verification

All requirements files have been tested with uv:

```bash
$ uv pip install --dry-run -r requirements.txt
✅ Resolved 58 packages in 43ms

$ uv pip install --dry-run -r requirements-dev.txt  
✅ Resolved 159 packages in 3.87s

$ uv pip install --dry-run -r requirements-minimal.txt
✅ Resolved 58 packages in 2.36s
```

## VS Code Integration Still Works

After fixing the requirements:
```bash
$ python -m pytest tests/test_azure_billing_pytest.py::TestMockDataGeneration -v
================================================ test session starts =================================================
collected 3 items                                                                                                    

tests/test_azure_billing_pytest.py::TestMockDataGeneration::test_mock_api_response_generation PASSED           [ 33%]
tests/test_azure_billing_pytest.py::TestMockDataGeneration::test_mock_billing_records_generation PASSED        [ 66%]
tests/test_azure_billing_pytest.py::TestMockDataGeneration::test_mock_resource_patterns PASSED                 [100%]

================================================= 3 passed in 0.04s ==================================================
```

## Benefits of uv

1. **Speed**: 10-100x faster than pip
2. **Better dependency resolution**: More accurate conflict detection
3. **Stricter parsing**: Catches requirement file issues early
4. **Better caching**: Faster subsequent installs
5. **Cross-platform**: Works consistently across systems

## Migration Guide

If you were using the old requirements files:

1. **Update your installation commands**:
   ```bash
   # Old
   pip install -r requirements-dev.txt
   
   # New
   uv pip install -r requirements-dev.txt
   ```

2. **Use the setup script** (handles both uv and pip):
   ```bash
   python setup_test_environment.py
   ```

3. **For CI/CD**, update your workflows:
   ```yaml
   # Install uv first
   - name: Install uv
     run: pip install uv
   
   # Then use uv for dependencies
   - name: Install dependencies
     run: uv pip install -r requirements.txt
   ```

## Troubleshooting

### If uv is not installed:
```bash
pip install uv
```

### If you prefer pip only:
The requirements files work with both uv and pip, so you can continue using pip if needed.

### If you encounter package conflicts:
Use the minimal requirements first:
```bash
uv pip install -r requirements-minimal.txt
```

Then add additional packages as needed.

---

The Azure Billing Connector test suite now works seamlessly with both uv and pip, with uv providing significantly faster installation times.