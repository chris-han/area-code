# Plugin API Endpoints

## Configuration Management

### Configure Plugin
Save plugin configuration to database.

```http
POST /configurePlugin
Content-Type: application/json

{
  "plugin_name": "ClickHouse Sink",
  "config": {
    "dbName": "finops-odw",
    "user": "finops",
    "password": "cU2f947&9T{6d",
    "host": "ck.mightytech.cn",
    "port": 8443,
    "useSSL": true,
    "tableName": "focus_billing_data",
    "batchSize": 1000
  },
  "database": "plugin_registry_db"
}
```

### Get Plugin Configuration
Load existing plugin configuration.

```http
GET /getPluginConfiguration?plugin_name=ClickHouse%20Sink&database=plugin_registry_db
```

### Get All Plugin Configurations
List all active plugin configurations.

```http
GET /getPluginConfigurations?database=plugin_registry_db
```

## Marketplace Management

### Get Plugin Marketplace
Retrieve all available plugins with metadata.

```http
GET /getPluginMarketplace?database=plugin_registry_db
```

### Install Plugin
Mark a plugin as installed and active.

```http
POST /installPlugin
Content-Type: application/json

{
  "plugin_name": "aws-cost-explorer",
  "database": "plugin_registry_db"
}
```

### Update Plugin Market Status
Update plugin installation and activation status.

```http
POST /updatePluginMarketStatus
Content-Type: application/json

{
  "plugin_name": "aws-cost-explorer",
  "is_installed": true,
  "is_active": true,
  "database": "plugin_registry_db"
}
```

## Plugin Operations

### Test Plugin Connection
Test plugin connectivity and configuration.

```http
POST /testPlugin
Content-Type: application/json

{
  "plugin_name": "ClickHouse Sink"
}
```

### Get Plugin Status
Check plugin operational status.

```http
GET /getPluginStatus?plugin_name=ClickHouse%20Sink
```

## Frontend Integration

The frontend uses these APIs through:

- `pluginsApi.configurePlugin(name, config)`
- `pluginsApi.getPluginConfiguration(name)`
- `pluginsApi.testPlugin(name)`
- `usePluginConfiguration(name)` React hook
- `usePlugins()` React hook for marketplace data