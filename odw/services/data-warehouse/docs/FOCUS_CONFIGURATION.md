# FOCUS Billing Integration - Configuration Reference

This document provides comprehensive configuration reference for the FOCUS billing integration, including all environment variables, configuration options, and setup procedures.

## 📋 Configuration Overview

The FOCUS billing integration uses a layered configuration approach:

1. **Default Values**: Sensible defaults for most use cases
2. **moose.config.toml**: ClickHouse connection settings (shared with ODW)
3. **Environment Variables**: Runtime overrides and customization
4. **Workflow Parameters**: Per-execution configuration

## 🌍 Environment Variables

### Core Data Paths

#### `FOCUS_DATA_ROOT`
- **Purpose**: Root directory containing FOCUS Parquet export files
- **Default**: Auto-detected from common locations
- **Format**: Absolute path to directory
- **Example**: `/data/focus` or `/home/user/focus-exports`
- **Structure Expected**:
  ```
  FOCUS_DATA_ROOT/
  ├── 20250701-20250731/
  │   ├── cost_and_usage/
  │   │   ├── part_1_0001.snappy.parquet
  │   │   └── manifest.json
  │   └── contract_commitment/
  │       ├── part_1_0001.snappy.parquet
  │       └── manifest.json
  └── 20250801-20250831/
      └── ...
  ```

#### `FOCUS_SPEC_ROOT`
- **Purpose**: Directory containing FOCUS specification files
- **Default**: Auto-detected relative to project structure
- **Format**: Absolute path to FOCUS_Spec/specification directory
- **Example**: `/path/to/FOCUS_Spec/specification`
- **Required Files**:
  - `datasets/cost_and_usage/dataset.md`
  - `datasets/contract_commitment/dataset.md`
  - `supported_features/*.md`

#### `FOCUS_QUERIES_ROOT`
- **Purpose**: Directory containing FOCUS query YAML files
- **Default**: Auto-detected relative to project structure
- **Format**: Absolute path to queries directory
- **Example**: `/path/to/focus-mcp-main/resources/queries`
- **Required Files**:
  - `focus_use_cases.yaml`
  - `focus_use_cases_adjustments.yaml`

#### `FOCUS_SPECIFICATIONS_ROOT`
- **Purpose**: Directory containing FOCUS specification YAML files
- **Default**: Auto-detected relative to project structure
- **Format**: Absolute path to specifications directory
- **Example**: `/path/to/focus-mcp-main/resources/specifications`
- **Required Files**:
  - `columns.yaml`
  - `attributes.yaml`

### ClickHouse Connection Settings

> **Note**: These settings override values from `moose.config.toml`. In most cases, the defaults from moose.config.toml are sufficient.

#### `CLICKHOUSE_HOST`
- **Purpose**: ClickHouse server hostname or IP address
- **Default**: From `moose.config.toml` (`ck.mightytech.cn`)
- **Format**: Hostname or IP address
- **Example**: `localhost`, `clickhouse.company.com`, `192.168.1.100`

#### `CLICKHOUSE_PORT`
- **Purpose**: ClickHouse HTTP port
- **Default**: From `moose.config.toml` (`8443`)
- **Format**: Port number
- **Example**: `8123` (HTTP), `8443` (HTTPS), `9000` (Native)

#### `CLICKHOUSE_USER`
- **Purpose**: ClickHouse username
- **Default**: From `moose.config.toml` (`finops`)
- **Format**: Username string
- **Example**: `default`, `focus_user`, `analytics`

#### `CLICKHOUSE_PASSWORD`
- **Purpose**: ClickHouse password
- **Default**: From `moose.config.toml`
- **Format**: Password string
- **Security**: Store securely, avoid logging

#### `CLICKHOUSE_DATABASE`
- **Purpose**: ClickHouse database name
- **Default**: From `moose.config.toml` (`finops-odw`)
- **Format**: Database name
- **Example**: `focus_billing`, `analytics`, `warehouse`

#### `CLICKHOUSE_USE_SSL`
- **Purpose**: Enable SSL/TLS for ClickHouse connections
- **Default**: From `moose.config.toml` (`true`)
- **Format**: `true` or `false`
- **Example**: `true` for production, `false` for local development

### Workflow Performance Settings

#### `FOCUS_BATCH_SIZE`
- **Purpose**: Number of rows to insert in each ClickHouse batch
- **Default**: `10000`
- **Range**: `1000` - `100000`
- **Format**: Integer
- **Tuning**: 
  - Smaller values: Lower memory usage, more network overhead
  - Larger values: Higher memory usage, better throughput
- **Example**: `5000` for memory-constrained environments, `20000` for high-performance systems

#### `FOCUS_MAX_WORKERS`
- **Purpose**: Maximum number of concurrent processing workers
- **Default**: `4`
- **Range**: `1` - `32`
- **Format**: Integer
- **Tuning**: Should not exceed CPU cores; consider I/O bottlenecks
- **Example**: `2` for small systems, `8` for high-performance systems

#### `FOCUS_CONNECTION_TIMEOUT`
- **Purpose**: ClickHouse connection timeout in seconds
- **Default**: `30`
- **Range**: `5` - `300`
- **Format**: Integer (seconds)
- **Tuning**: Increase for slow networks or overloaded servers
- **Example**: `60` for remote connections, `10` for local development

#### `FOCUS_SEND_RECEIVE_TIMEOUT`
- **Purpose**: ClickHouse query execution timeout in seconds
- **Default**: `300` (5 minutes)
- **Range**: `30` - `3600`
- **Format**: Integer (seconds)
- **Tuning**: Increase for large data processing operations
- **Example**: `600` for large ingestion batches, `120` for quick queries

### Workflow Behavior Settings

#### `FOCUS_DRY_RUN`
- **Purpose**: Enable dry-run mode (no actual data insertion)
- **Default**: `false`
- **Format**: `true` or `false`
- **Use Cases**: Testing, validation, debugging
- **Example**: `true` for testing new configurations

## ⚙️ Configuration Files

### moose.config.toml

The FOCUS integration inherits ClickHouse settings from the main Moose configuration:

```toml
[clickhouse_config]
host = "ck.mightytech.cn"
host_port = 8443
user = "finops"
password = "cU2f947&9T{6d"
db_name = "finops-odw"
use_ssl = true
```

### .env File (Optional)

Create a `.env` file in `odw/services/data-warehouse/` for local overrides:

```bash
# FOCUS Data Paths
FOCUS_DATA_ROOT=/custom/path/to/focus/data
FOCUS_SPEC_ROOT=/custom/path/to/FOCUS_Spec/specification

# Performance Tuning
FOCUS_BATCH_SIZE=15000
FOCUS_MAX_WORKERS=6

# Development Settings
FOCUS_DRY_RUN=false

# ClickHouse Overrides (if needed)
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USE_SSL=false
```

## 🔧 Configuration Validation

### Automated Validation

The system provides built-in configuration validation:

```python
from app.focus_billing.config import focus_config

# Validate all paths exist
paths_status = focus_config.validate_paths()
for path_name, exists in paths_status.items():
    print(f"{path_name}: {'✓' if exists else '✗'}")

# Test ClickHouse connection
connection_ok = focus_config.validate_clickhouse_connection()
print(f"ClickHouse connection: {'✓' if connection_ok else '✗'}")

# Display current configuration
print("Current configuration:")
print(f"  Data root: {focus_config.focus_data_root}")
print(f"  Batch size: {focus_config.batch_size}")
print(f"  ClickHouse: {focus_config.get_clickhouse_url()}")
```

### Manual Validation Steps

#### 1. Verify FOCUS Data Structure
```bash
# Check data directory structure
ls -la $FOCUS_DATA_ROOT/
# Should show period folders like: 20250701-20250731/

# Check for required files in each period
ls -la $FOCUS_DATA_ROOT/20250701-20250731/
# Should show: cost_and_usage/ and contract_commitment/ directories

# Verify Parquet files exist
find $FOCUS_DATA_ROOT -name "*.parquet" | head -5
```

#### 2. Test ClickHouse Connectivity
```bash
# Direct connection test
curl -u $CLICKHOUSE_USER:$CLICKHOUSE_PASSWORD \
  $CLICKHOUSE_HOST:$CLICKHOUSE_PORT/ping

# Query test
curl -u $CLICKHOUSE_USER:$CLICKHOUSE_PASSWORD \
  -d "SELECT version()" \
  $CLICKHOUSE_HOST:$CLICKHOUSE_PORT/
```

#### 3. Validate FOCUS Specifications
```bash
# Check specification files
ls -la $FOCUS_SPEC_ROOT/datasets/
# Should show: cost_and_usage/ and contract_commitment/

# Check query files
ls -la $FOCUS_QUERIES_ROOT/
# Should show: focus_use_cases.yaml and other query files
```

## 🎯 Configuration Profiles

### Development Profile
```bash
# Local development with minimal resources
export FOCUS_DATA_ROOT="./test_data/focus"
export FOCUS_BATCH_SIZE=1000
export FOCUS_MAX_WORKERS=2
export FOCUS_DRY_RUN=true
export CLICKHOUSE_HOST=localhost
export CLICKHOUSE_PORT=8123
export CLICKHOUSE_USE_SSL=false
```

### Testing Profile
```bash
# Automated testing environment
export FOCUS_DATA_ROOT="/test/fixtures/focus"
export FOCUS_BATCH_SIZE=500
export FOCUS_MAX_WORKERS=1
export FOCUS_DRY_RUN=true
export FOCUS_CONNECTION_TIMEOUT=10
export FOCUS_SEND_RECEIVE_TIMEOUT=30
```

### Production Profile
```bash
# High-performance production environment
export FOCUS_DATA_ROOT="/data/focus/exports"
export FOCUS_BATCH_SIZE=20000
export FOCUS_MAX_WORKERS=8
export FOCUS_DRY_RUN=false
export FOCUS_CONNECTION_TIMEOUT=60
export FOCUS_SEND_RECEIVE_TIMEOUT=600
export CLICKHOUSE_USE_SSL=true
```

### Memory-Constrained Profile
```bash
# Limited memory environment
export FOCUS_BATCH_SIZE=2000
export FOCUS_MAX_WORKERS=2
export FOCUS_CONNECTION_TIMEOUT=45
export FOCUS_SEND_RECEIVE_TIMEOUT=300
```

## 🔍 Configuration Troubleshooting

### Common Configuration Issues

#### 1. Path Not Found Errors
**Symptoms**: "Path does not exist" errors during startup
**Diagnosis**:
```bash
# Check each path
echo "FOCUS_DATA_ROOT: $FOCUS_DATA_ROOT"
ls -la "$FOCUS_DATA_ROOT" 2>/dev/null || echo "Path not found"

echo "FOCUS_SPEC_ROOT: $FOCUS_SPEC_ROOT"  
ls -la "$FOCUS_SPEC_ROOT" 2>/dev/null || echo "Path not found"
```
**Solutions**:
- Verify paths are absolute and accessible
- Check file permissions (readable by application user)
- Ensure directories exist and contain expected files

#### 2. ClickHouse Connection Failures
**Symptoms**: Connection timeout or authentication errors
**Diagnosis**:
```bash
# Test network connectivity
ping $CLICKHOUSE_HOST

# Test port accessibility
telnet $CLICKHOUSE_HOST $CLICKHOUSE_PORT

# Test authentication
curl -u $CLICKHOUSE_USER:$CLICKHOUSE_PASSWORD \
  $CLICKHOUSE_HOST:$CLICKHOUSE_PORT/ping
```
**Solutions**:
- Verify credentials in moose.config.toml
- Check network connectivity and firewall rules
- Validate SSL certificate if using HTTPS

#### 3. Performance Issues
**Symptoms**: Slow ingestion or memory errors
**Diagnosis**:
```bash
# Check current batch size
echo "Batch size: $FOCUS_BATCH_SIZE"

# Monitor memory usage during ingestion
docker stats --no-stream $(docker ps -q --filter name=data-warehouse)
```
**Solutions**:
- Reduce batch size for memory-constrained environments
- Adjust worker count based on available CPU cores
- Increase timeouts for slow networks

#### 4. Permission Issues
**Symptoms**: "Permission denied" errors when accessing files
**Diagnosis**:
```bash
# Check file permissions
ls -la $FOCUS_DATA_ROOT/
ls -la $FOCUS_SPEC_ROOT/

# Check process user
whoami
id
```
**Solutions**:
- Ensure application user has read access to all FOCUS directories
- Fix permissions: `chmod -R 755 $FOCUS_DATA_ROOT`
- Consider running with appropriate user context

## 📊 Configuration Monitoring

### Configuration Health Checks

Create a health check script to validate configuration:

```bash
#!/bin/bash
# focus_config_health.sh

echo "=== FOCUS Configuration Health Check ==="

# Check environment variables
echo "Environment Variables:"
echo "  FOCUS_DATA_ROOT: ${FOCUS_DATA_ROOT:-'(default)'}"
echo "  FOCUS_BATCH_SIZE: ${FOCUS_BATCH_SIZE:-'(default)'}"
echo "  FOCUS_DRY_RUN: ${FOCUS_DRY_RUN:-'(default)'}"

# Check paths
echo -e "\nPath Validation:"
for path in "$FOCUS_DATA_ROOT" "$FOCUS_SPEC_ROOT" "$FOCUS_QUERIES_ROOT"; do
  if [ -d "$path" ]; then
    echo "  ✓ $path"
  else
    echo "  ✗ $path (not found)"
  fi
done

# Test ClickHouse connection
echo -e "\nClickHouse Connection:"
if curl -s -u "$CLICKHOUSE_USER:$CLICKHOUSE_PASSWORD" \
   "$CLICKHOUSE_HOST:$CLICKHOUSE_PORT/ping" > /dev/null; then
  echo "  ✓ Connection successful"
else
  echo "  ✗ Connection failed"
fi

echo -e "\n=== Health Check Complete ==="
```

### Runtime Configuration Monitoring

Monitor configuration changes and their impact:

```python
# config_monitor.py
import time
import json
from app.focus_billing.config import focus_config

def monitor_config():
    """Monitor configuration and validate periodically"""
    while True:
        # Validate paths
        paths_ok = all(focus_config.validate_paths().values())
        
        # Test ClickHouse
        ch_ok = focus_config.validate_clickhouse_connection()
        
        # Log status
        status = {
            'timestamp': time.time(),
            'paths_valid': paths_ok,
            'clickhouse_connected': ch_ok,
            'batch_size': focus_config.batch_size,
            'max_workers': focus_config.max_workers
        }
        
        print(json.dumps(status))
        
        # Sleep for 5 minutes
        time.sleep(300)

if __name__ == "__main__":
    monitor_config()
```

## 🔄 Configuration Updates

### Updating Configuration

#### Runtime Updates (Environment Variables)
```bash
# Update environment variable
export FOCUS_BATCH_SIZE=15000

# Restart application to pick up changes
docker restart $(docker ps -q --filter name=data-warehouse)
```

#### Persistent Updates (.env file)
```bash
# Edit .env file
echo "FOCUS_BATCH_SIZE=15000" >> odw/services/data-warehouse/.env

# Restart services
cd odw/services/data-warehouse
docker-compose restart
```

#### ClickHouse Configuration Updates
```bash
# Edit moose.config.toml
vim odw/services/data-warehouse/moose.config.toml

# Restart entire stack
cd odw
bun run odw:dev:clean
bun run odw:dev
```

### Configuration Rollback

Keep configuration backups for easy rollback:

```bash
# Backup current configuration
cp odw/services/data-warehouse/.env odw/services/data-warehouse/.env.backup
cp odw/services/data-warehouse/moose.config.toml odw/services/data-warehouse/moose.config.toml.backup

# Rollback if needed
cp odw/services/data-warehouse/.env.backup odw/services/data-warehouse/.env
cp odw/services/data-warehouse/moose.config.toml.backup odw/services/data-warehouse/moose.config.toml
```

This configuration reference provides comprehensive guidance for setting up and managing the FOCUS billing integration. Keep this document updated as new configuration options are added.