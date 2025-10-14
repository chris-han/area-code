# Azure Billing Connector

This package provides a comprehensive Azure Enterprise Agreement (EA) billing data connector for the ODW ETL pipeline.

## Components

### Core Connector
- **`azure_billing_connector.py`** - Main connector class with configuration models
- **`azure_ea_api_client.py`** - Azure EA API client with pagination and retry logic

### Data Processing
- **`azure_billing_transformer.py`** - Data transformation pipeline with JSON processing
- **`resource_tracking_engine.py`** - Resource tracking with pattern matching and audit logging

### Infrastructure
- **`error_handler.py`** - Comprehensive error handling and classification
- **`extract_azure_billing.py`** - Temporal workflow integration

## Usage

```python
from azure_billing import (
    AzureBillingConnector,
    AzureBillingConnectorConfig
)

# Configure the connector
config = AzureBillingConnectorConfig(
    azure_enrollment_number="123456789",
    azure_api_key="your-api-key",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    batch_size=1000
)

# Create and use the connector
connector = AzureBillingConnector(config)
billing_records = connector.extract()
```

## Features

- **Azure EA API Integration** with automatic pagination
- **Resource Tracking** with priority-based pattern matching
- **Data Transformation** with field mapping and type conversion
- **JSON Processing** with robust error handling
- **VM-Specific Logic** for SKU derivation and AKS handling
- **Memory Management** with monitoring and garbage collection
- **Comprehensive Error Handling** with classification and recovery
- **Audit Logging** for resource tracking conflicts

## Testing

Run the test suite from the connectors directory:

```bash
PYTHONPATH=src python tests/test_azure_only.py
```

## Integration

The connector integrates with:
- **Temporal Workflows** for orchestration
- **ClickHouse** for data warehouse storage
- **ConnectorFactory** for standardized creation
- **Ingest API** for data loading