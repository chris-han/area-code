# FOCUS Billing Ingestion Workflow

This document describes the FOCUS billing data ingestion workflow implementation that processes FOCUS Parquet exports and loads them into ClickHouse for analytical queries.

## Overview

The FOCUS billing ingestion workflow provides a complete pipeline for:

1. **File Discovery**: Automatically discovers FOCUS Parquet files in the configured data directory
2. **Data Transformation**: Transforms Parquet data for ClickHouse compatibility (column naming, type conversions)
3. **Batch Insertion**: Efficiently inserts data into ClickHouse tables with error handling
4. **Manifest Tracking**: Tracks processed files to avoid duplicates and provide audit trails

## Architecture

### Components

- **`file_discovery.py`**: Discovers and catalogs FOCUS Parquet files with manifest metadata
- **`data_transformer.py`**: Transforms data from PascalCase to snake_case with type conversions
- **`clickhouse_inserter.py`**: Handles chunked insertion into ClickHouse with error handling
- **`workflow.py`**: Orchestrates the complete ingestion process with logging and statistics

### Data Flow

```
FOCUS Parquet Files → File Discovery → Data Transformation → ClickHouse Insertion → Manifest Tracking
```

## Configuration

The workflow uses the `FocusBillingConfig` class for configuration:

```python
from app.focus_billing.config import focus_config

# Key configuration options:
focus_config.focus_data_root        # Path to FOCUS Parquet exports
focus_config.batch_size             # ClickHouse insertion batch size (default: 10000)
focus_config.clickhouse_host        # ClickHouse server host
focus_config.clickhouse_database    # Target database name
```

### Environment Variables

- `FOCUS_DATA_ROOT`: Override default FOCUS data directory
- `CLICKHOUSE_HOST`: ClickHouse server hostname
- `CLICKHOUSE_DATABASE`: Target database name
- `CLICKHOUSE_USER`: ClickHouse username
- `CLICKHOUSE_PASSWORD`: ClickHouse password

## Usage

### Via Moose CLI

```bash
# Run the complete ingestion workflow
moose workflow run focus-billing-ingest-workflow

# The workflow will use default parameters and process all unprocessed files
```

### Programmatic Usage

```python
from app.focus_billing.workflow import FocusBillingIngestParams, FocusBillingIngestWorkflow

# Configure workflow parameters
params = FocusBillingIngestParams(
    dry_run=False,                    # Set to True for testing
    batch_size=5000,                  # Override default batch size
    max_files=10,                     # Limit number of files to process
    dataset_type_filter="cost_usage", # Process only cost & usage files
    period_filter="20250701-20250731", # Process only specific period
    continue_on_error=True,           # Continue processing on file errors
    skip_processed=True               # Skip already processed files
)

# Execute workflow
workflow = FocusBillingIngestWorkflow(params)
stats = workflow.execute()

print(f"Processed {stats.files_processed} files, {stats.total_rows_processed} rows")
```

### Dry Run Mode

For testing and validation:

```python
params = FocusBillingIngestParams(dry_run=True, max_files=5)
workflow = FocusBillingIngestWorkflow(params)
stats = workflow.execute()
# Will discover and transform data but not insert into ClickHouse
```

## Data Transformation

### Column Name Conversion

- **Input**: PascalCase columns from FOCUS spec (`BillingAccountId`, `UsageDate`)
- **Output**: snake_case columns for ClickHouse (`billing_account_id`, `usage_date`)

### Type Conversions

- **Timestamps**: INT96 Parquet timestamps → ClickHouse DateTime64
- **Decimals**: Parquet decimals → ClickHouse Decimal(38,18)
- **Booleans**: Boolean values → UInt8 (0/1)
- **JSON**: Complex objects → JSON strings for compatibility

### Computed Columns

Added automatically to each row:

- `id`: Deterministic hash based on key columns
- `source_system`: Always "focus_parquet"
- `created_at`: Processing timestamp
- `updated_at`: Processing timestamp

## Error Handling

### File-Level Errors

- Invalid Parquet files are skipped with error logging
- Transformation failures are logged to manifest table
- ClickHouse insertion errors are retried per batch

### Workflow-Level Errors

- `continue_on_error=True`: Process remaining files after errors
- `continue_on_error=False`: Stop workflow on first error
- All errors are collected in workflow statistics

### Manifest Tracking

The `focus_ingest_manifest` table tracks:

- File processing status (processing, success, failed)
- Row counts and processing times
- Error messages for failed files
- File checksums for change detection

## Performance

### Batch Processing

- Default batch size: 10,000 rows per ClickHouse insert
- Configurable via `batch_size` parameter
- Memory usage scales with batch size

### Parallel Processing

- Single-threaded file processing (sequential)
- Future enhancement: parallel file processing with `max_workers`

### Typical Performance

- ~1,000-5,000 rows/second depending on data complexity
- Memory usage: ~5-10 MB per 1,000 rows during transformation

## Monitoring

### Workflow Statistics

```python
stats = workflow.execute()
print(f"Files discovered: {stats.files_discovered}")
print(f"Files processed: {stats.files_processed}")
print(f"Files failed: {stats.files_failed}")
print(f"Total rows: {stats.total_rows_processed}")
print(f"Processing time: {stats.total_processing_time:.2f}s")
```

### CLI Logging

The workflow provides detailed CLI logging:

```
[INFO] FocusBillingIngest: Starting FOCUS billing ingestion workflow
[INFO] FocusBillingIngest: Discovered 92 Parquet files
[INFO] FocusBillingIngest: Processing file 1/3: 20250701-20250731/...
[INFO] FocusBillingIngest: Transformed 1594 rows
[INFO] FocusBillingIngest: Successfully processed 1594 rows in 2.34 seconds
```

## Validation

### Pre-Flight Checks

```bash
# Validate workflow configuration and dependencies
python -m app.focus_billing.validate_workflow
```

### Integration Testing

```bash
# Test with actual FOCUS data (dry run)
python -m app.focus_billing.test_integration
```

## Troubleshooting

### Common Issues

1. **"FOCUS data root does not exist"**
   - Check `FOCUS_DATA_ROOT` environment variable
   - Verify FOCUS Parquet exports are available

2. **"Failed to connect to ClickHouse"**
   - Verify ClickHouse credentials and network connectivity
   - Check `moose.config.toml` configuration

3. **"Target table does not exist"**
   - Run DDL scripts to create FOCUS tables
   - Verify table names match configuration

4. **"Transformation failed"**
   - Check Parquet file format and schema
   - Review transformation error messages in logs

### Debug Mode

Enable detailed logging by setting log level in the workflow:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- Parallel file processing with configurable worker pools
- Incremental processing based on file modification times
- Data quality validation and reporting
- Integration with data lineage tracking
- Support for streaming ingestion from cloud storage

## Dependencies

- `pandas>=2.0.0`: Data manipulation and transformation
- `pyarrow>=16.1.0`: Parquet file reading and Arrow integration
- `clickhouse-connect`: ClickHouse database connectivity
- `pydantic>=2.0.0`: Configuration and data validation
- `moose-lib`: Moose workflow framework integration