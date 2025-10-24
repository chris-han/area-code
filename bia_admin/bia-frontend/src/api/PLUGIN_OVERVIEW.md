# Plugin System Overview

## Architecture

The Azure Billing Intelligence (bia) plugin system provides a modular architecture for data ingestion, transformation, and output operations.

### Core Components

1. **Plugin Registry Database** - Stores plugin metadata and configurations
2. **Plugin Marketplace** - UI for discovering and managing plugins  
3. **Configuration Management** - Persistent storage of plugin settings
4. **API Integration** - RESTful endpoints for plugin operations

### Plugin Categories

- **Data Connectors** - Ingest data from external sources (Azure Blob, AWS, GCP)
- **Transformers** - Process and transform data (FOCUS 1.2 compliance)
- **Data Sinks** - Output data to storage systems (ClickHouse, databases)
- **Analytics** - Generate insights and reports from processed data

### Database Schema

Two main tables in the `plugin_registry` schema:

- `plugin_market` - Plugin metadata, ratings, installation status
- `plugin_configurations` - Active plugin settings and parameters

### Integration Points

- **Frontend**: React-based plugin management UI
- **Backend**: FastAPI endpoints for plugin operations
- **Workflows**: Plugin selection in ETL pipeline creation
- **Configuration**: Persistent storage in PostgreSQL database