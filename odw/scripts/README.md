# ODW Scripts

This directory contains setup and utility scripts for the ODW (Open Data Warehouse) project.

## Plugin Configuration Setup

### `setup-plugin-config.sh` & `setup-plugin-config.py`

These scripts initialize the plugin registry database and set up default plugin configurations for the Azure Billing Intelligence system.

#### What it does:

1. **Creates Database Schema**: Sets up the `plugin_registry` schema in the `bia_config` database
2. **Creates Tables**:
   - `plugin_configurations` - Stores active plugin settings and parameters
   - `plugin_market` - Stores plugin marketplace information (metadata, ratings, installation status)
3. **Populates Plugin Marketplace**: Adds 6 plugins including Azure Blob Storage Connector, FOCUS 1.2 Transformer, ClickHouse Sink
4. **Sets Default Configurations**: Creates default configurations for installed plugins using settings from `moose.config.toml`

#### Prerequisites:

- PostgreSQL running in Docker (data-warehouse-postgresql-1 container)
- Python 3 with `psycopg2-binary` and `toml` packages
- Database `bia_config` must exist (script will create it if needed)

#### Usage:

```bash
# From ODW root directory
./scripts/setup-plugin-config.sh
```

#### Database Configuration:

The script uses the `plugin_registry_db` configuration from `moose.config.toml`:

```toml
[plugin_registry_db]
host = "localhost"
port = 5432
database = "bia_config"
user = "temporal"
password = "temporal"
schema = "plugin_registry"
```

#### Created Plugins:

| Plugin Name | Version | Category | Status | Rating |
|-------------|---------|----------|--------|--------|
| Azure Blob Storage Connector | 1.3.0 | Data Connector | ✅ Installed | ⭐ 4.9 |
| FOCUS 1.2 Transformer | 2.2.0 | Transformer | ✅ Installed | ⭐ 4.9 |
| ClickHouse Sink | 1.4.0 | Data Sink | ✅ Installed | ⭐ 4.8 |
| Azure EA Connector | 1.2.0 | Data Connector | ✅ Installed | ⭐ 4.8 |
| GCP Billing Export | 0.9.2 | Data Connector | ✅ Installed | ⭐ 4.6 |
| AWS Cost Explorer | 1.0.1 | Data Connector | ❌ Available | ⭐ 4.5 |

#### Verification:

After running the script, you can verify the setup:

```bash
# Check plugin marketplace
docker exec -it data-warehouse-postgresql-1 psql -U temporal -d bia_config -c "SELECT display_name, version, category, is_installed FROM plugin_registry.plugin_market ORDER BY display_name;"

# Check plugin configurations
docker exec -it data-warehouse-postgresql-1 psql -U temporal -d bia_config -c "SELECT plugin_name, is_active, created_at FROM plugin_registry.plugin_configurations WHERE is_active = true;"
```

#### Integration:

The plugin registry database integrates with:

- **ABI Frontend**: Plugin management UI at `http://localhost:3003/admin/plugins`
- **FastAPI Backend**: Plugin configuration APIs (`/configurePlugin`, `/getPluginConfiguration`, etc.)
- **Workflow System**: Plugin selection and configuration in workflow creation

#### Troubleshooting:

1. **Database Connection Failed**: Ensure PostgreSQL container is running
2. **Permission Denied**: Run script with `sudo` for system package installation
3. **Database Not Found**: Script will show command to create `bia_config` database
4. **Python Packages**: Script automatically installs required packages using `uv` or `pip`

## Other Scripts

### `dev-seed.sh`
Development data seeding script for the ODW system.

### `seed-data.py`
Python script for seeding development data into the system.