# Azure Billing Intelligence (ABI) System

## Overview

The Azure Billing Intelligence (ABI) system is a comprehensive data platform built on the Moose framework that provides real-time analytics, workflow orchestration, and intelligent insights for Azure billing data. The system integrates Azure EA API data sources with ClickHouse analytics, Temporal workflow orchestration, and modern web interfaces to deliver a complete FinOps solution.

## Key Features

- **FOCUS Compliance**: Implements FinOps Open Cost and Usage Specification for standardized billing analytics
- **Plugin Architecture**: Extensible data source connectors with lazy loading
- **Workflow Orchestration**: Temporal-based workflows for reliable data processing
- **Real-time Analytics**: ClickHouse-powered analytics with DataLens visualization
- **Hybrid Architecture**: Local development services with external PaaS databases

## Architecture

The ABI system extends the existing ODW (Operation Data Warehouse) infrastructure with Azure billing-specific capabilities:

```
odw/services/data-warehouse/
├── app/
│   ├── azure_billing/          # ABI core modules
│   │   ├── models/            # FOCUS and source data models
│   │   ├── workflows/         # Temporal workflows
│   │   └── transformations/   # SQL transformation modules
│   └── ...                    # Other ODW modules
├── plugins/                   # Data source plugins
│   ├── azure_ea/             # Azure EA API plugin
│   └── s3_minio/             # S3/MinIO plugin
├── moose.config.toml         # Extended with ABI configuration
└── .env                      # Environment variables
```

## Configuration

### Environment Variables (.env)

```bash
# Azure EA API Configuration
AZURE_ENROLLMENT_NUMBER=V5702303S0121
AZURE_API_KEY=your_azure_ea_api_key

# ClickHouse Connection (External PaaS)
CLICKHOUSE_DB_NAME=finops-odw
CLICKHOUSE_USER=finops
CLICKHOUSE_PASSWORD=your_password
CLICKHOUSE_HOST=ck.mightytech.cn
CLICKHOUSE_USE_SSL=true
CLICKHOUSE_HOST_PORT=8443

# Temporal/PostgreSQL Connection (External PaaS)
TEMPORAL_DB_USER=maradmin
TEMPORAL_DB_PASSWORD=your_password
TEMPORAL_DB_HOST=marspbi.postgres.database.chinacloudapi.cn
```

### Moose Configuration (moose.config.toml)

The configuration includes:
- FOCUS data model specification
- Plugin system settings
- DataLens integration
- External database connections

## Development Workflow

### Prerequisites

- Python 3.12+
- UV package manager
- Bun (for frontend)
- Docker and Docker Compose

### Getting Started

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Configure Environment**:
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

3. **Start Development Services**:
   ```bash
   bun run abi:dev
   ```

4. **Clean and Restart**:
   ```bash
   bun run abi:dev:clean
   ```

### Available Services

| Service | URL | Description |
|---------|-----|-------------|
| Moose API | http://localhost:4200 | Main API server |
| ClickHouse | http://localhost:18123 | Analytics database |
| Temporal UI | http://localhost:8080 | Workflow monitoring |
| Kafdrop | http://localhost:9999 | Message queue UI |
| MinIO Console | http://localhost:9501 | Object storage UI |

## Data Models

### FOCUS Target Model

The system implements FOCUS-compliant data models for standardized billing analytics:

- `FOCUSBillingData`: Main fact table with cost and usage dimensions
- `FOCUSServiceCategory`: Service category dimension
- `FOCUSResourceType`: Resource type dimension
- `FOCUSGeography`: Geographic dimension

### Source Models

- `AzureEABillingDetail`: Azure EA API raw data structure
- `S3CSVSourceModel`: Generic CSV file structure
- Plugin-specific models for custom data sources

## Plugin System

### Available Plugins

1. **Azure EA Plugin** (`azure_ea`):
   - Connects to Azure Enterprise Agreement API
   - Extracts billing and usage data
   - Supports rate limiting and error handling

2. **S3/MinIO Plugin** (`s3_minio`):
   - Processes CSV files from S3-compatible storage
   - Handles variable schema formats
   - Provides data validation and quality checks

### Plugin Development

Plugins implement the `DataSourcePlugin` interface:

```python
class DataSourcePlugin(ABC):
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        pass
    
    @abstractmethod
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def test_connection(self, config: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def extract_data(self, config: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass
```

## Workflows

### Azure Billing Workflow

Automated workflow for Azure EA data extraction:

- **Schedule**: Daily at 2 AM
- **Retries**: 3 attempts with exponential backoff
- **Timeout**: 30 minutes per task, 2 hours total
- **Monitoring**: Real-time status via Temporal UI

### Data Transformation Workflow

FOCUS compliance transformation:

- Source-to-target mapping
- Data validation and quality checks
- Error handling and quarantine
- Batch processing for performance

## Monitoring and Observability

### Health Checks

- Service health endpoints
- Database connectivity monitoring
- Plugin status tracking
- Workflow execution monitoring

### Logging

- Structured JSON logging
- Correlation IDs for request tracking
- Error aggregation and alerting
- Performance metrics collection

## Troubleshooting

### Common Issues

1. **Connection Failures**:
   - Check environment variables
   - Verify network connectivity
   - Review service logs

2. **Plugin Errors**:
   - Validate plugin configuration
   - Test connection endpoints
   - Check API credentials

3. **Workflow Failures**:
   - Review Temporal UI for details
   - Check workflow parameters
   - Verify data source availability

### Support

For issues and questions:
- Check the logs in `moose.log`
- Review Temporal UI for workflow status
- Examine service health endpoints
- Consult the design document for architecture details

## Next Steps

1. Complete plugin marketplace implementation
2. Add DataLens frontend integration
3. Implement advanced analytics features
4. Set up production deployment configuration
5. Add comprehensive monitoring and alerting