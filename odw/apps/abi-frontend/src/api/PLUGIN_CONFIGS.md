# Plugin Configuration Examples

## Azure Blob Storage Connector

Connect to Azure Blob Storage for FOCUS-compliant parquet files.

```json
{
  "storageAccount": "mystorageaccount",
  "sasToken": "?sv=2022-11-02&ss=bfqt&srt=...",
  "dataContainer": "focus-data",
  "pathPrefix": "billing/"
}
```

**Required Fields:**
- `storageAccount` - Azure storage account name
- `sasToken` - SAS token with read permissions
- `dataContainer` - Container name containing parquet files

**Optional Fields:**
- `pathPrefix` - Path prefix within container (e.g., "billing/")

## FOCUS 1.2 Transformer

Transform parquet files to Moose model FOCUS 1.2 data tables.

```json
{
  "inputFormat": "parquet",
  "outputModel": "moose",
  "focusVersion": "1.2",
  "compressionType": "snappy",
  "batchSize": 10000,
  "enableValidation": true,
  "sinkPlugin": "ClickHouse Sink"
}
```

**Configuration Options:**
- `inputFormat` - Input data format (parquet, csv, json)
- `outputModel` - Output model type (moose, clickhouse, parquet)
- `focusVersion` - FOCUS specification version (1.0, 1.1, 1.2)
- `compressionType` - Compression format (snappy, gzip, lz4, none)
- `batchSize` - Records per processing batch (1,000 - 1,000,000)
- `enableValidation` - Enable FOCUS schema validation
- `sinkPlugin` - Target sink plugin for output

## ClickHouse Sink

Write transformed data to ClickHouse database with SSL support.

```json
{
  "dbName": "finops-odw",
  "user": "finops",
  "password": "cU2f947&9T{6d",
  "host": "ck.mightytech.cn",
  "port": 8443,
  "useSSL": true,
  "tableName": "focus_billing_data",
  "createTableIfNotExists": true,
  "batchSize": 1000
}
```

**Connection Settings:**
- `dbName` - ClickHouse database name
- `user` - Database username
- `password` - Database password
- `host` - ClickHouse server hostname
- `port` - ClickHouse server port (8443 for HTTPS)
- `useSSL` - Enable SSL/TLS encryption

**Table Settings:**
- `tableName` - Target table name
- `createTableIfNotExists` - Auto-create table if missing
- `batchSize` - Records per insert batch (100 - 100,000)

## Azure EA Connector

Connect to Azure Enterprise Agreement billing data.

```json
{
  "enrollmentId": "12345678",
  "apiKey": "your-ea-api-key",
  "apiVersion": "2023-05-01",
  "billingPeriod": "current",
  "includeUsageDetails": true,
  "includeMarketplaceCharges": true
}
```

## GCP Billing Export

Export Google Cloud Platform billing data from BigQuery.

```json
{
  "projectId": "my-gcp-project",
  "serviceAccountKey": "path/to/service-account.json",
  "datasetId": "billing_export",
  "tableId": "gcp_billing_export",
  "location": "US"
}
```

## Configuration Management

Configurations are stored in the `plugin_registry.plugin_configurations` table as JSONB data with:

- Automatic versioning and timestamps
- Active/inactive status management
- User attribution and audit trail
- Validation against plugin schemas