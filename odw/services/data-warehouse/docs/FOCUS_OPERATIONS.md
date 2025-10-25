# FOCUS Billing Integration - Operations Guide

This guide provides comprehensive operational procedures for managing the FOCUS billing integration in the ODW (Operational Data Warehouse).

## 📋 Pre-Deployment Checklist

### Environment Setup
- [ ] **ClickHouse Connection**: Verify ClickHouse credentials in `moose.config.toml`
- [ ] **FOCUS Data Path**: Confirm `FOCUS_DATA_ROOT` points to valid Parquet directory
- [ ] **Specification Files**: Ensure FOCUS specification and query files are accessible
- [ ] **Dependencies**: Verify all Python dependencies are installed (`clickhouse-connect`, `pyarrow`, etc.)
- [ ] **Temporal Worker**: Confirm Temporal worker is running for workflow orchestration

### Path Validation
```bash
# Run path validation check
cd odw/services/data-warehouse
python -c "
from app.focus_billing.config import focus_config
paths = focus_config.validate_paths()
for path, exists in paths.items():
    print(f'{path}: {'✓' if exists else '✗'} {getattr(focus_config, path)}')
"
```

### ClickHouse Connectivity Test
```bash
# Test ClickHouse connection
python -c "
from app.focus_billing.config import focus_config
result = focus_config.validate_clickhouse_connection()
print(f'ClickHouse connection: {'✓' if result else '✗'}')
if not result:
    print('Check credentials in moose.config.toml')
"
```

## 🏗️ DDL Application Procedures

### Initial Schema Creation

The FOCUS tables are created automatically on first workflow execution. For manual creation:

```bash
cd odw/services/data-warehouse

# Create all FOCUS tables
python -c "
from app.focus_billing.ddl_generator import FocusDDLGenerator
from app.focus_billing.config import focus_config

generator = FocusDDLGenerator()
print('Creating FOCUS tables...')

# Create tables in order
tables_created = generator.create_all_tables()
for table, success in tables_created.items():
    print(f'{table}: {'✓' if success else '✗'}')
"
```

### Schema Verification

```bash
# Verify table existence and structure
python -c "
from app.focus_billing.observability import focus_observability

tables = [
    'focus_cost_usage',
    'focus_contract_commitment', 
    'focus_ingest_manifest',
    'focus_data_table',
    'focus_contract_commitment_view'
]

results = focus_observability.verify_tables_exist(tables)
for table, result in results.items():
    print(f'{table}: {'✓' if result.passed else '✗'} {result.message}')
"
```

### Schema Updates

When FOCUS specification changes require schema updates:

```bash
# 1. Backup existing data (if needed)
curl -X POST http://localhost:4200/query \
  -d "CREATE TABLE focus_cost_usage_backup AS SELECT * FROM focus_cost_usage"

# 2. Drop and recreate tables
python -c "
from app.focus_billing.ddl_generator import FocusDDLGenerator
generator = FocusDDLGenerator()
generator.drop_all_tables()
generator.create_all_tables()
"

# 3. Re-run ingestion workflow to repopulate
```

## 🔄 Workflow Execution Procedures

### Standard Ingestion Workflow

#### Method 1: Via BIA Admin UI (Recommended)
1. Open BIA Admin: `http://localhost:3000`
2. Navigate to **Workflows** → **Start New Workflow**
3. Select **FOCUS Billing Ingest**
4. Configure parameters:
   - **Data Root**: Leave default or specify custom path
   - **Batch Size**: Default 10,000 (adjust for performance)
   - **Max Files**: Leave empty for all files
   - **Dry Run**: Enable for testing
5. Click **Start Workflow**
6. Monitor progress in **Workflow Status** page

#### Method 2: Direct API Call
```bash
# Start workflow with default parameters
curl -X POST http://localhost:4200/workflows/focus_billing_ingest \
  -H "Content-Type: application/json" \
  -d '{
    "dry_run": false,
    "continue_on_error": true,
    "skip_processed": true
  }'

# Start workflow with custom parameters
curl -X POST http://localhost:4200/workflows/focus_billing_ingest \
  -H "Content-Type: application/json" \
  -d '{
    "data_root": "/custom/path/to/focus/data",
    "batch_size": 5000,
    "max_files": 10,
    "dataset_type_filter": "cost_usage",
    "period_filter": "20250701-20250731",
    "dry_run": false
  }'
```

#### Method 3: Temporal CLI (Advanced)
```bash
# Start via Temporal CLI
temporal workflow start \
  --type FocusBillingTemporalWorkflow \
  --task-queue focus-billing-queue \
  --workflow-id "focus-ingest-$(date +%Y%m%d-%H%M%S)" \
  --input '{
    "data_root": "/path/to/focus/data",
    "batch_size": 10000,
    "dry_run": false
  }'

# Monitor workflow
temporal workflow show --workflow-id focus-ingest-20250125-143000
```

### Incremental Processing

For regular incremental updates:

```bash
# Process only new files (skips already processed)
curl -X POST http://localhost:4200/workflows/focus_billing_ingest \
  -H "Content-Type: application/json" \
  -d '{
    "skip_processed": true,
    "continue_on_error": true,
    "period_filter": "20250801-20250831"
  }'
```

### Reprocessing Specific Periods

To reprocess specific time periods:

```bash
# 1. Clear manifest entries for the period
curl -X POST http://localhost:4200/query \
  -d "DELETE FROM focus_ingest_manifest 
      WHERE file_path LIKE '%20250701-20250731%'"

# 2. Run workflow with period filter
curl -X POST http://localhost:4200/workflows/focus_billing_ingest \
  -H "Content-Type: application/json" \
  -d '{
    "period_filter": "20250701-20250731",
    "skip_processed": false
  }'
```

## 📊 Monitoring and Validation

### Workflow Status Monitoring

```bash
# Check recent workflow executions
curl http://localhost:4200/workflows/status

# Check Temporal workflow history
temporal workflow list --query 'WorkflowType="FocusBillingTemporalWorkflow"'
```

### Data Validation Checks

#### Row Count Validation
```bash
# Check table row counts
curl -X POST http://localhost:4200/query \
  -d "SELECT 
    'focus_cost_usage' as table_name,
    count() as row_count,
    min(usage_date) as min_date,
    max(usage_date) as max_date
  FROM focus_cost_usage
  UNION ALL
  SELECT 
    'focus_contract_commitment' as table_name,
    count() as row_count,
    min(commitment_start_date) as min_date,
    max(commitment_end_date) as max_date  
  FROM focus_contract_commitment"
```

#### Referential Integrity Check
```bash
# Validate contract commitment relationships
curl -X POST http://localhost:4200/query \
  -d "SELECT 
    count() as total_commitments,
    count(DISTINCT cu.contract_commitment_id) as linked_commitments,
    count() - count(DISTINCT cu.contract_commitment_id) as orphaned_commitments
  FROM focus_contract_commitment cc
  LEFT JOIN focus_cost_usage cu ON cc.contract_commitment_id = cu.contract_commitment_id"
```

#### Data Quality Checks
```bash
# Check for data anomalies
curl -X POST http://localhost:4200/query \
  -d "SELECT 
    'Negative costs' as check_type,
    count() as issue_count
  FROM focus_cost_usage 
  WHERE billed_cost < 0
  UNION ALL
  SELECT 
    'Missing billing accounts' as check_type,
    count() as issue_count
  FROM focus_cost_usage 
  WHERE billing_account_id IS NULL OR billing_account_id = ''"
```

### Ingestion Manifest Monitoring

```bash
# Check processing status by file
curl -X POST http://localhost:4200/query \
  -d "SELECT 
    status,
    count() as file_count,
    sum(rows_processed) as total_rows,
    avg(processing_time_seconds) as avg_processing_time
  FROM focus_ingest_manifest 
  GROUP BY status
  ORDER BY status"

# Check recent processing activity
curl -X POST http://localhost:4200/query \
  -d "SELECT 
    file_path,
    status,
    rows_processed,
    processing_time_seconds,
    created_at
  FROM focus_ingest_manifest 
  WHERE created_at >= now() - INTERVAL 1 DAY
  ORDER BY created_at DESC
  LIMIT 20"

# Identify failed files
curl -X POST http://localhost:4200/query \
  -d "SELECT 
    file_path,
    error_message,
    created_at
  FROM focus_ingest_manifest 
  WHERE status = 'failed'
  ORDER BY created_at DESC"
```

## 🔧 Configuration Management

### Environment Variables Reference

| Variable | Default | Purpose | Example |
|----------|---------|---------|---------|
| `FOCUS_DATA_ROOT` | Auto-detected | Parquet files location | `/data/focus` |
| `FOCUS_SPEC_ROOT` | Auto-detected | FOCUS specification | `/FOCUS_Spec/specification` |
| `FOCUS_QUERIES_ROOT` | Auto-detected | Query YAML files | `/focus-mcp-main/resources/queries` |
| `FOCUS_BATCH_SIZE` | `10000` | Insert batch size | `5000` |
| `FOCUS_MAX_WORKERS` | `4` | Concurrent workers | `8` |
| `FOCUS_DRY_RUN` | `false` | Dry run mode | `true` |
| `FOCUS_CONNECTION_TIMEOUT` | `30` | Connection timeout (s) | `60` |
| `FOCUS_SEND_RECEIVE_TIMEOUT` | `300` | Query timeout (s) | `600` |

### Configuration Validation

```bash
# Validate current configuration
cd odw/services/data-warehouse
python -c "
from app.focus_billing.config import focus_config
import json

config_dict = focus_config.dict()
print(json.dumps(config_dict, indent=2, default=str))

# Test paths
paths = focus_config.validate_paths()
print('\nPath Validation:')
for path, exists in paths.items():
    print(f'  {path}: {'✓' if exists else '✗'}')

# Test ClickHouse
ch_ok = focus_config.validate_clickhouse_connection()
print(f'\nClickHouse Connection: {'✓' if ch_ok else '✗'}')
"
```

### Performance Tuning

#### Batch Size Optimization
```bash
# Test different batch sizes for optimal performance
for batch_size in 5000 10000 20000; do
  echo "Testing batch size: $batch_size"
  time curl -X POST http://localhost:4200/workflows/focus_billing_ingest \
    -H "Content-Type: application/json" \
    -d "{\"batch_size\": $batch_size, \"max_files\": 1, \"dry_run\": true}"
done
```

#### Memory Usage Monitoring
```bash
# Monitor memory usage during ingestion
docker stats $(docker ps -q --filter name=data-warehouse)
```

## 🚨 Troubleshooting Procedures

### Common Issues and Solutions

#### 1. Workflow Fails to Start
**Symptoms**: Workflow creation returns error or times out
**Diagnosis**:
```bash
# Check Temporal worker status
docker logs $(docker ps -q --filter name=temporal-worker)

# Check data warehouse service logs  
docker logs $(docker ps -q --filter name=data-warehouse)
```
**Solutions**:
- Restart Temporal worker: `docker restart $(docker ps -q --filter name=temporal-worker)`
- Verify workflow registration in `app/main.py`
- Check network connectivity between services

#### 2. ClickHouse Connection Failures
**Symptoms**: "Connection refused" or authentication errors
**Diagnosis**:
```bash
# Test direct ClickHouse connection
curl -u finops:cU2f947&9T{6d https://ck.mightytech.cn:8443/ping

# Check moose.config.toml credentials
cat odw/services/data-warehouse/moose.config.toml | grep -A 10 clickhouse_config
```
**Solutions**:
- Verify credentials in `moose.config.toml`
- Check network connectivity to ClickHouse host
- Validate SSL certificate if using HTTPS

#### 3. Parquet File Processing Errors
**Symptoms**: Files discovered but transformation fails
**Diagnosis**:
```bash
# Check file permissions and structure
ls -la $FOCUS_DATA_ROOT/20250701-20250731/

# Validate Parquet file structure
python -c "
import pyarrow.parquet as pq
df = pq.read_table('/path/to/file.parquet')
print(df.schema)
"
```
**Solutions**:
- Verify file permissions (readable by application)
- Check Parquet file integrity
- Validate column schema matches FOCUS specification

#### 4. Memory Issues During Large Ingestion
**Symptoms**: Out of memory errors or slow performance
**Diagnosis**:
```bash
# Monitor memory usage
docker stats --no-stream

# Check batch size configuration
echo $FOCUS_BATCH_SIZE
```
**Solutions**:
- Reduce batch size: `export FOCUS_BATCH_SIZE=5000`
- Increase Docker memory limits
- Process files in smaller chunks using `max_files` parameter

#### 5. Referential Integrity Violations
**Symptoms**: Contract commitment data without matching cost data
**Diagnosis**:
```bash
# Check for orphaned commitments
curl -X POST http://localhost:4200/query \
  -d "SELECT cc.contract_commitment_id, count(cu.contract_commitment_id) as usage_records
      FROM focus_contract_commitment cc
      LEFT JOIN focus_cost_usage cu ON cc.contract_commitment_id = cu.contract_commitment_id  
      GROUP BY cc.contract_commitment_id
      HAVING usage_records = 0"
```
**Solutions**:
- Verify both Cost & Usage and Contract Commitment files are processed
- Check for data consistency in source Parquet files
- Re-run ingestion for missing periods

### Recovery Procedures

#### Full System Recovery
```bash
# 1. Stop all services
docker-compose down

# 2. Clear problematic data (if needed)
curl -X POST http://localhost:4200/query -d "TRUNCATE TABLE focus_ingest_manifest"

# 3. Restart services
docker-compose up -d

# 4. Re-run ingestion
curl -X POST http://localhost:4200/workflows/focus_billing_ingest \
  -H "Content-Type: application/json" \
  -d '{"skip_processed": false}'
```

#### Partial Data Recovery
```bash
# 1. Identify failed files
curl -X POST http://localhost:4200/query \
  -d "SELECT file_path FROM focus_ingest_manifest WHERE status = 'failed'"

# 2. Clear failed entries
curl -X POST http://localhost:4200/query \
  -d "DELETE FROM focus_ingest_manifest WHERE status = 'failed'"

# 3. Reprocess specific period
curl -X POST http://localhost:4200/workflows/focus_billing_ingest \
  -H "Content-Type: application/json" \
  -d '{"period_filter": "20250701-20250731"}'
```

## 📈 Performance Monitoring

### Key Metrics to Monitor

1. **Ingestion Rate**: Rows processed per second
2. **File Processing Time**: Average time per Parquet file
3. **Error Rate**: Percentage of failed files
4. **Memory Usage**: Peak memory during processing
5. **ClickHouse Query Performance**: Average query execution time

### Monitoring Queries

```bash
# Ingestion performance over time
curl -X POST http://localhost:4200/query \
  -d "SELECT 
    toDate(created_at) as date,
    count() as files_processed,
    sum(rows_processed) as total_rows,
    avg(processing_time_seconds) as avg_time_per_file,
    sum(rows_processed) / sum(processing_time_seconds) as rows_per_second
  FROM focus_ingest_manifest 
  WHERE status = 'success'
  GROUP BY date
  ORDER BY date DESC"

# Query performance metrics
curl -X POST http://localhost:4200/query \
  -d "SELECT 
    query_kind,
    count() as query_count,
    avg(query_duration_ms) as avg_duration,
    max(query_duration_ms) as max_duration
  FROM system.query_log 
  WHERE event_date >= today() - 7
    AND query LIKE '%focus_%'
  GROUP BY query_kind
  ORDER BY avg_duration DESC"
```

## 🔄 Maintenance Procedures

### Regular Maintenance Tasks

#### Daily
- [ ] Monitor workflow execution status
- [ ] Check for failed file processing
- [ ] Validate data freshness (latest ingestion date)

#### Weekly  
- [ ] Review ingestion performance metrics
- [ ] Clean up old manifest entries (optional)
- [ ] Validate referential integrity
- [ ] Check ClickHouse table sizes and partitions

#### Monthly
- [ ] Review and optimize ClickHouse table schemas
- [ ] Update FOCUS specification files if new version available
- [ ] Performance testing with larger datasets
- [ ] Backup critical configuration files

### Cleanup Procedures

```bash
# Clean old manifest entries (older than 90 days)
curl -X POST http://localhost:4200/query \
  -d "DELETE FROM focus_ingest_manifest 
      WHERE created_at < now() - INTERVAL 90 DAY"

# Optimize ClickHouse tables
curl -X POST http://localhost:4200/query \
  -d "OPTIMIZE TABLE focus_cost_usage FINAL"
curl -X POST http://localhost:4200/query \
  -d "OPTIMIZE TABLE focus_contract_commitment FINAL"
```

This operations guide provides comprehensive procedures for managing the FOCUS billing integration. Keep this document updated as the system evolves and new operational procedures are developed.