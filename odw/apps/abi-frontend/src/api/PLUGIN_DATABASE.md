# Plugin Database Schema

## Database Configuration

**Location**: `moose.config.toml`
```toml
[plugin_registry_db]
host = "localhost"
port = 5432
database = "bia_config"
user = "temporal"
password = "temporal"
schema = "plugin_registry"
```

## Tables

### plugin_market

Stores plugin marketplace information and metadata.

```sql
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
```

### plugin_configurations

Stores active plugin configurations and settings.

```sql
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
```

## Indexes

```sql
-- Plugin market indexes
CREATE INDEX idx_plugin_market_name ON plugin_registry.plugin_market(plugin_name);
CREATE INDEX idx_plugin_market_category ON plugin_registry.plugin_market(category);
CREATE INDEX idx_plugin_market_installed ON plugin_registry.plugin_market(is_installed);
CREATE INDEX idx_plugin_market_rating ON plugin_registry.plugin_market(rating DESC);
CREATE INDEX idx_plugin_market_tags ON plugin_registry.plugin_market USING GIN(tags);

-- Plugin configuration indexes
CREATE INDEX idx_plugin_configurations_name ON plugin_registry.plugin_configurations(plugin_name);
CREATE INDEX idx_plugin_configurations_active ON plugin_registry.plugin_configurations(is_active);

-- Unique constraint for active configurations
CREATE UNIQUE INDEX unique_active_plugin_config 
ON plugin_registry.plugin_configurations(plugin_name) 
WHERE is_active = true;
```

## Setup

Run the setup script to initialize the database:

```bash
./scripts/setup-plugin-config.sh
```