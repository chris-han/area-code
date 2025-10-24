# Plugin System Documentation

This document provides an overview of the plugin system architecture and links to detailed documentation.

## Quick Links

- **[Plugin Overview](./PLUGIN_OVERVIEW.md)** - System architecture and core components
- **[Database Schema](./PLUGIN_DATABASE.md)** - Database tables, indexes, and setup
- **[API Endpoints](./PLUGIN_API.md)** - RESTful API documentation
- **[Configuration Examples](./PLUGIN_CONFIGS.md)** - Plugin configuration samples
- **[Frontend Integration](./PLUGIN_FRONTEND.md)** - React components and hooks

## Database Configuration

Plugin configurations are stored in the `plugin_registry_db` database as defined in the Moose configuration:

**Location**: `/home/chris/repo/area-code/odw/services/data-warehouse/moose.config.toml`

```toml
[plugin_registry_db]
host = "localhost"
port = 5432
database = "bia_config"
user = "temporal"
password = "temporal"
schema = "plugin_registry"
```

## Storage Schema

Plugin configurations and marketplace data are stored in the following table structure:

```sql
-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS plugin_registry;

-- Plugin configurations table
CREATE TABLE plugin_registry.plugin_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_name VARCHAR(255) NOT NULL,
    configuration JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255) DEFAULT 'system',
    is_active BOOLEAN DEFAULT true,
    version VARCHAR(50) DEFAULT '1.0.0',
    description TEXT
);

-- Plugin marketplace table
CREATE TABLE plugin_registry.plugin_market (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    author VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    long_description TEXT,
    category VARCHAR(100) NOT NULL,
    tags TEXT[] DEFAULT '{}',
    rating DECIMAL(2,1) DEFAULT 0.0,
    downloads VARCHAR(20) DEFAULT '0',
    icon_url TEXT,
    documentation_url TEXT,
    repository_url TEXT,
    license VARCHAR(100),
    config_schema JSONB,
    requirements TEXT[],
    features TEXT[],
    is_installed BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT false,
    is_configurable BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated DATE,
    marketplace_url TEXT
);

-- Indexes for faster lookups
CREATE INDEX idx_plugin_configurations_name ON plugin_registry.plugin_configurations(plugin_name);
CREATE INDEX idx_plugin_configurations_active ON plugin_registry.plugin_configurations(is_active);
CREATE INDEX idx_plugin_market_name ON plugin_registry.plugin_market(plugin_name);
CREATE INDEX idx_plugin_market_category ON plugin_registry.plugin_market(category);
CREATE INDEX idx_plugin_market_installed ON plugin_registry.plugin_market(is_installed);
CREATE INDEX idx_plugin_market_rating ON plugin_registry.plugin_market(rating DESC);
CREATE INDEX idx_plugin_market_tags ON plugin_registry.plugin_market USING GIN(tags);

-- Unique constraint for active configurations
CREATE UNIQUE INDEX unique_active_plugin_config 
ON plugin_registry.plugin_configurations(plugin_name) 
WHERE is_active = true;
```

## Configuration Examples

### Azure Blob Storage Connector
```json
{
  "storageAccount": "mystorageaccount",
  "sasToken": "?sv=2022-11-02&ss=bfqt&srt=...",
  "dataContainer": "focus-data",
  "pathPrefix": "billing/"
}
```

### FOCUS 1.2 Transformer
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

### ClickHouse Sink
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

## API Endpoints

The following API endpoints should be implemented in the FastAPI backend:

### Configure Plugin
```
POST /configurePlugin
{
  "plugin_name": "ClickHouse Sink",
  "config": { ... },
  "database": "plugin_registry_db"
}
```

### Get Plugin Configuration
```
GET /getPluginConfiguration?plugin_name=ClickHouse%20Sink&database=plugin_registry_db
```

### Get All Plugin Configurations
```
GET /getPluginConfigurations?database=plugin_registry_db
```

### Get Plugin Marketplace
```
GET /getPluginMarketplace?database=plugin_registry_db
```

### Install Plugin
```
POST /installPlugin
{
  "plugin_name": "aws-cost-explorer",
  "database": "plugin_registry_db"
}
```

### Update Plugin Market Status
```
POST /updatePluginMarketStatus
{
  "plugin_name": "aws-cost-explorer",
  "is_installed": true,
  "is_active": true,
  "database": "plugin_registry_db"
}
```

## Security Considerations

1. **Sensitive Data**: Passwords and tokens should be encrypted before storage
2. **Access Control**: Only authorized users should be able to modify plugin configurations
3. **Audit Trail**: All configuration changes should be logged
4. **Environment Variables**: Consider using environment variables for highly sensitive data like database passwords

## Frontend Integration

The frontend uses the following hooks and APIs:

- `usePluginConfiguration(pluginName)` - Load existing configuration
- `pluginsApi.configurePlugin(name, config)` - Save configuration
- `pluginsApi.getPluginConfiguration(name)` - Get configuration

All configurations are automatically loaded when opening the plugin configuration modal and saved to the plugin registry database when the user clicks "Save Configuration".

## Quick Start

1. **Setup Database**: Run `./scripts/setup-plugin-config.sh` to initialize the plugin registry
2. **Start Frontend**: Navigate to `http://localhost:3003/admin/plugins` to manage plugins
3. **Configure Plugins**: Click "Configure" on any installed plugin to set up connections
4. **Test Connections**: Use the built-in connection testing to verify configurations

## Available Plugins

- **Azure Blob Storage Connector** - Ingest FOCUS parquet files from Azure
- **FOCUS 1.2 Transformer** - Transform data to Moose model format
- **ClickHouse Sink** - Output data to ClickHouse database
- **Azure EA Connector** - Connect to Enterprise Agreement billing
- **GCP Billing Export** - Export Google Cloud billing data
- **AWS Cost Explorer** - Available for installation