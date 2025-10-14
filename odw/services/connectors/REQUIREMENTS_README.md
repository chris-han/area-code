# Requirements Files for Azure Billing Connector

This directory contains multiple requirements files for different use cases:

## Files Overview

### `requirements.txt`
**Core production dependencies** - Essential packages needed to run the Azure Billing Connector in production.

```bash
pip install -r requirements.txt
```

**Key dependencies:**
- `requests` - HTTP client for Azure EA API
- `polars` - High-performance data processing
- `pydantic` - Data validation and models
- `clickhouse-connect` - Database connectivity
- `psutil` - System monitoring

### `requirements-dev.txt`
**Development and testing dependencies** - Includes all production dependencies plus development tools.

```bash
pip install -r requirements-dev.txt
```

**Additional tools:**
- `pytest` - Testing framework
- `black`, `flake8`, `mypy` - Code quality tools
- `sphinx` - Documentation generation
- `jupyter` - Interactive development
- `hypothesis` - Property-based testing

### `setup_test_environment.py`
**Automated setup script** - Interactive installer that handles dependency installation and validation.

```bash
python setup_test_environment.py
```

**Features:**
- Checks Python version compatibility
- Installs dependencies with error handling
- Validates installation success
- Runs test suite validation
- Sets up environment variables

## Installation Options

### Option 1: Automated Setup (Recommended)
```bash
cd odw/services/connectors
python setup_test_environment.py
```

### Option 2: Production Only (uv - fastest)
```bash
cd odw/services/connectors
uv pip install -r requirements.txt
```

### Option 3: Production Only (pip)
```bash
cd odw/services/connectors
pip install -r requirements.txt
```

### Option 4: Development Environment (uv)
```bash
cd odw/services/connectors
uv pip install -r requirements-dev.txt
```

### Option 5: Development Environment (pip)
```bash
cd odw/services/connectors
pip install -r requirements-dev.txt
```

### Option 4: Virtual Environment (Recommended for Development)
```bash
cd odw/services/connectors
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Dependency Categories

### Core Runtime Dependencies
- **HTTP/API**: `requests`, `urllib3`
- **Data Processing**: `polars`, `numpy`, `pandas`
- **Data Validation**: `pydantic`
- **Database**: `clickhouse-connect`
- **System**: `psutil`, `python-dateutil`

### Testing Dependencies
- **Framework**: `pytest`, `pytest-cov`, `pytest-mock`
- **Mocking**: `responses`, `factory-boy`, `hypothesis`
- **Data Generation**: `faker`

### Development Tools
- **Code Quality**: `black`, `flake8`, `mypy`, `isort`, `pylint`
- **Documentation**: `sphinx`, `sphinx-rtd-theme`
- **Debugging**: `ipython`, `jupyter`, `pdb++`
- **Profiling**: `py-spy`, `memory-profiler`

### Optional Dependencies
- **Temporal**: `temporalio` (for workflow orchestration)
- **AWS**: `boto3` (for S3 integration)
- **Monitoring**: `prometheus-client`, `opentelemetry-api`
- **Performance**: `orjson`, `xxhash`

## Version Compatibility

### Python Version
- **Minimum**: Python 3.8
- **Recommended**: Python 3.9+
- **Tested**: Python 3.8, 3.9, 3.10, 3.11

### Key Package Versions
- `requests >= 2.32.4` - Security updates
- `polars >= 0.20.0` - Performance improvements
- `pydantic >= 2.0.0` - Modern validation features
- `pytest >= 7.0.0` - Latest testing features

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure packages are installed
pip list | grep -E "(requests|polars|pydantic)"

# Reinstall if missing
pip install -r requirements.txt --force-reinstall
```

#### 2. Version Conflicts
```bash
# Check for conflicts
pip check

# Create clean environment
python -m venv fresh_env
source fresh_env/bin/activate
pip install -r requirements.txt
```

#### 3. System Dependencies
Some packages may require system libraries:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install build-essential python3-dev
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel
```

**macOS:**
```bash
xcode-select --install
brew install python
```

#### 4. Memory Issues
For large datasets, you may need to increase memory limits:

```bash
# Set environment variables
export POLARS_MAX_THREADS=4
export PYTHONHASHSEED=0
```

### Performance Optimization

#### 1. Faster Package Installation
```bash
# Use pip cache
pip install -r requirements.txt --cache-dir ~/.pip/cache

# Use conda for scientific packages (alternative)
conda install -c conda-forge polars numpy pandas
pip install -r requirements.txt --no-deps
```

#### 2. Minimal Installation
For production environments, install only core dependencies:

```bash
pip install requests polars pydantic clickhouse-connect psutil python-dateutil
```

## Updating Dependencies

### Check for Updates
```bash
pip list --outdated
```

### Update All Packages
```bash
pip install -r requirements.txt --upgrade
```

### Update Specific Package
```bash
pip install --upgrade polars
```

### Generate New Requirements
```bash
pip freeze > requirements-frozen.txt
```

## Security Considerations

### Vulnerability Scanning
```bash
# Install safety (included in requirements-dev.txt)
pip install safety

# Scan for vulnerabilities
safety check -r requirements.txt
```

### Secure Installation
```bash
# Verify package integrity
pip install -r requirements.txt --require-hashes

# Use trusted hosts only
pip install -r requirements.txt --trusted-host pypi.org
```

## Contributing

When adding new dependencies:

1. **Add to appropriate file**:
   - Core functionality → `requirements.txt`
   - Development/testing → `requirements-dev.txt`

2. **Specify minimum versions**:
   ```
   new-package>=1.2.3
   ```

3. **Test installation**:
   ```bash
   python setup_test_environment.py
   ```

4. **Update documentation**:
   - Add to this README
   - Update setup script if needed

## Support

For issues with dependencies or installation:

1. Check this README for troubleshooting steps
2. Run the setup script for automated diagnosis
3. Check the test suite validation output
4. Review package documentation for specific issues

---

**Note**: Always use virtual environments for development to avoid conflicts with system packages.