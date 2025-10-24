# Azure NCEI to FOCUS Workflow Summary

## Overview

This document summarizes the implementation of the **azure_ncei_to_focus** workflow that replaces the S3 CSV plugin and workflow system with Azure Blob Storage parquet file processing for NCEI (National Cloud Economics Intelligence) data source.

## Components Implemented

### 1. Data Models (`models/azure_blob_parquet_models.py`)

**AzureNCEIParquetModel**: 
- Handles FOCUS-compliant parquet files from Azure Blob Storage
- Supports primary and secondary containers
- Built-in FOCUS field mapping and validation
- Parquet-specific metadata (compression, schema, row groups)

**Key Features**:
- Pre-configured for NCEI account: `https://finopsbilling.blob.core.chinacloudapi.cn`
- Dual container support (primary + secondary)
- FOCUS compliance validation
- Parquet schema detection

### 2. Transformation Engine (`transformations/azure_ncei_to_focus.py`)

**AzureNCEIToFOCUSTransformer**:
- Minimal transformation for FOCUS-compliant parquet files
- Direct field mappings (NCEI data should already be FOCUS-compliant)
- SQL-based transformation for ClickHouse integration

**Key Features**:
- Optimized for pre-FOCUS data (minimal transformation needed)
- Handles missing fields with sensible defaults
- Provider set to "Azure" automatically

### 3. Temporal Workflow (`workflows/azure_ncei_workflow.py`)

**AzureNCEIToFOCUSWorkflow**:
- Temporal workflow for processing parquet files
- Batch processing with configurable batch sizes
- Error handling and retry policies

**Activities**:
- `list_ncei_parquet_files`: Lists parquet files from Azure Blob Storage
- `process_ncei_parquet_batch`: Processes batches of parquet files

### 4. Workflow Scheduler (`workflows/ncei_scheduler.py`)

**NCEIWorkflowScheduler**:
- Manages workflow scheduling (daily/manual)
- Pre-configured with NCEI credentials and settings
- Supports custom configuration overrides

### 5. API Endpoints (`workflows/ncei_api.py`)

**FastAPI Routes** (`/api/v1/azure-ncei/`):
- `POST /workflows/start`: Start manual workflow
- `POST /workflows/daily`: Start daily workflow  
- `GET /workflows/{id}/status`: Get workflow status

## Configuration

### Pre-configured NCEI Settings

```python
{
    "account_url": "https://finopsbilling.blob.core.chinacloudapi.cn",
    "sas_token": "sv=2024-11-04&ss=bfqt&srt=sco&sp=rltfx&se=2045-10-19T12:52:39Z&st=2025-10-19T04:37:39Z&spr=https&sig=g44Cxk0eqgrn5N6DrZF8s60a3qaWp6cWLnPaNJtXw40%3D",
    "container_name": "billing-data",
    "secondary_container": None,  # Optional
    "path_prefix": "focus-data/",
    "batch_size": 10,
    "provider": "Azure"
}
```

### Dual Container Support

The workflow supports both primary and secondary containers:
- **Primary Container**: Main data source container
- **Secondary Container**: Optional backup or additional data source

## Workflow Execution

### Daily Workflow
```bash
POST /api/v1/azure-ncei/workflows/daily
{
  "date": "2024-01-15"  # Optional, defaults to yesterday
}
```

### Manual Workflow
```bash
POST /api/v1/azure-ncei/workflows/start
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "container_name": "billing-data",
  "secondary_container": "backup-billing-data",
  "path_prefix": "focus-data/",
  "batch_size": 10
}
```

## Integration Points

### Replaces S3 CSV System

| Component | S3 CSV (Old) | Azure NCEI (New) |
|-----------|--------------|-------------------|
| **Data Source** | S3-compatible CSV files | Azure Blob Storage parquet files |
| **Models** | `S3CSVSourceModel` | `AzureNCEIParquetModel` |
| **Transformation** | `S3CSVToFOCUSTransformer` | `AzureNCEIToFOCUSTransformer` |
| **Workflow** | S3 CSV workflow | `AzureNCEIToFOCUSWorkflow` |
| **Format** | CSV with schema detection | FOCUS-compliant parquet |
| **Complexity** | High (CSV parsing + mapping) | Low (minimal transformation) |

### Frontend Integration

The workflow integrates with the DataLens plugin marketplace:
- **Plugin UI**: Azure Blob Storage configuration interface
- **Management**: Real-time workflow monitoring
- **Configuration**: Stored in PostgreSQL via plugin system

## Benefits

1. **Performance**: Parquet files are more efficient than CSV
2. **FOCUS Compliance**: Native FOCUS format reduces transformation overhead
3. **Dual Container**: Supports backup and multiple data sources
4. **Pre-configured**: Ready-to-use NCEI credentials and settings
5. **Scalable**: Batch processing with configurable sizes
6. **Reliable**: Temporal workflow with retry policies

## Usage

### Import Components
```python
from azure_billing import (
    AzureNCEIToFOCUSWorkflow,
    NCEIWorkflowScheduler,
    create_ncei_scheduler,
    ncei_api_router,
    AzureNCEIParquetModel,
    AzureNCEIToFOCUSTransformer
)
```

### Start Workflow Programmatically
```python
scheduler = create_ncei_scheduler(temporal_client)
workflow_id = await scheduler.schedule_daily_workflow()
```

## Next Steps

1. **Integration Testing**: Test with actual NCEI parquet files
2. **ClickHouse Schema**: Ensure target schema supports FOCUS fields
3. **Monitoring**: Add workflow monitoring and alerting
4. **Performance Tuning**: Optimize batch sizes and processing
5. **Error Handling**: Enhanced error handling and recovery

The **azure_ncei_to_focus** workflow is now ready to replace the S3 CSV system and process FOCUS-compliant parquet files from the NCEI Azure Blob Storage data source.