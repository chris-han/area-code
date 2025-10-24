#!/usr/bin/env python3
"""
Plugin Configuration Setup Script

This script initializes the plugin registry database and sets up default configurations
for the Azure Billing Intelligence plugins based on the moose.config.toml settings.
"""

import os
import sys
import json
import uuid
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import toml

def load_moose_config():
    """Load configuration from moose.config.toml"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'data-warehouse', 'moose.config.toml')
    
    if not os.path.exists(config_path):
        print(f"❌ Moose config not found at: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = toml.load(f)
    
    print(f"✅ Loaded moose configuration from: {config_path}")
    return config

def get_db_connection(config):
    """Create database connection using plugin_registry_db config"""
    db_config = config.get('plugin_registry_db', {})
    
    conn_params = {
        'host': db_config.get('host', 'localhost'),
        'port': db_config.get('port', 5432),
        'database': db_config.get('database', 'bia_config'),
        'user': db_config.get('user', 'temporal'),
        'password': db_config.get('password', 'temporal')
    }
    
    try:
        conn = psycopg2.connect(**conn_params)
        print(f"✅ Connected to database: {conn_params['database']} at {conn_params['host']}:{conn_params['port']}")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Failed to connect to database: {e}")
        print(f"💡 Tip: Make sure PostgreSQL is running and the database '{conn_params['database']}' exists")
        print(f"💡 You can create it with: docker exec -it data-warehouse-postgresql-1 psql -U temporal -c \"CREATE DATABASE {conn_params['database']};\"")
        sys.exit(1)

def create_plugin_registry_schema(conn):
    """Create the plugin registry schema and tables"""
    schema_name = 'plugin_registry'
    
    with conn.cursor() as cur:
        # Create schema
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        print(f"✅ Created schema: {schema_name}")
        
        # Create plugin_configurations table
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {schema_name}.plugin_configurations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plugin_name VARCHAR(255) NOT NULL,
            configuration JSONB NOT NULL,
            description TEXT,
            version VARCHAR(50),
            created_by VARCHAR(255) DEFAULT 'system',
            updated_by VARCHAR(255),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        cur.execute(create_table_sql)
        print(f"✅ Created table: {schema_name}.plugin_configurations")

        # Ensure required columns exist with defaults for legacy tables
        migrations = [
            f"ALTER TABLE {schema_name}.plugin_configurations ADD COLUMN IF NOT EXISTS description TEXT;",
            f"ALTER TABLE {schema_name}.plugin_configurations ADD COLUMN IF NOT EXISTS version VARCHAR(50);",
            f"ALTER TABLE {schema_name}.plugin_configurations ADD COLUMN IF NOT EXISTS created_by VARCHAR(255) DEFAULT 'system';",
            f"ALTER TABLE {schema_name}.plugin_configurations ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255);",
            f"ALTER TABLE {schema_name}.plugin_configurations ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;",
            f"ALTER TABLE {schema_name}.plugin_configurations ALTER COLUMN created_at SET DEFAULT NOW();",
            f"ALTER TABLE {schema_name}.plugin_configurations ALTER COLUMN updated_at SET DEFAULT NOW();"
        ]

        for migration_sql in migrations:
            cur.execute(migration_sql)
        
        # Create plugin_market table
        create_market_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {schema_name}.plugin_market (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plugin_name VARCHAR(255) NOT NULL UNIQUE,
            display_name VARCHAR(255) NOT NULL,
            version VARCHAR(50) NOT NULL,
            author VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            long_description TEXT,
            category VARCHAR(100) NOT NULL,
            tags TEXT[] DEFAULT '{{}}',
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
        """
        cur.execute(create_market_table_sql)
        print(f"✅ Created table: {schema_name}.plugin_market")
        
        # Create indexes
        indexes = [
            f"""
            CREATE UNIQUE INDEX IF NOT EXISTS unique_active_plugin_config 
            ON {schema_name}.plugin_configurations(plugin_name) 
            WHERE is_active = true;
            """,
            f"CREATE INDEX IF NOT EXISTS idx_plugin_configurations_name ON {schema_name}.plugin_configurations(plugin_name);",
            f"CREATE INDEX IF NOT EXISTS idx_plugin_configurations_active ON {schema_name}.plugin_configurations(is_active);",
            f"CREATE INDEX IF NOT EXISTS idx_plugin_configurations_created_at ON {schema_name}.plugin_configurations(created_at);",
            f"CREATE INDEX IF NOT EXISTS idx_plugin_market_name ON {schema_name}.plugin_market(plugin_name);",
            f"CREATE INDEX IF NOT EXISTS idx_plugin_market_category ON {schema_name}.plugin_market(category);",
            f"CREATE INDEX IF NOT EXISTS idx_plugin_market_installed ON {schema_name}.plugin_market(is_installed);",
            f"CREATE INDEX IF NOT EXISTS idx_plugin_market_rating ON {schema_name}.plugin_market(rating DESC);",
            f"CREATE INDEX IF NOT EXISTS idx_plugin_market_tags ON {schema_name}.plugin_market USING GIN(tags);"
        ]
        
        for index_sql in indexes:
            cur.execute(index_sql)
        
        print(f"✅ Created indexes for plugin tables")
        
        conn.commit()

def insert_plugin_configuration(conn, plugin_name, config, description=""):
    """Insert or update a plugin configuration"""
    schema_name = 'plugin_registry'
    
    with conn.cursor() as cur:
        # First, deactivate any existing active configuration for this plugin
        deactivate_sql = f"""
        UPDATE {schema_name}.plugin_configurations 
        SET is_active = false, updated_at = NOW()
        WHERE plugin_name = %s AND is_active = true;
        """
        cur.execute(deactivate_sql, (plugin_name,))
        
        # Insert new configuration
        insert_sql = f"""
        INSERT INTO {schema_name}.plugin_configurations 
        (plugin_name, configuration, description, created_by, updated_by)
        VALUES (%s, %s, %s, %s, %s);
        """
        cur.execute(insert_sql, (plugin_name, json.dumps(config), description, 'setup-script', 'setup-script'))
        
        conn.commit()
        print(f"✅ Configured plugin: {plugin_name}")

def populate_plugin_market(conn):
    """Populate the plugin_market table with available plugins"""
    schema_name = 'plugin_registry'
    
    plugins_data = [
        {
            'plugin_name': 'azure-blob-storage-connector',
            'display_name': 'Azure Blob Storage Connector',
            'version': '1.3.0',
            'author': 'Microsoft',
            'description': 'Connect to Azure Blob Storage for FOCUS-compliant parquet files',
            'long_description': 'The Azure Blob Storage Connector enables seamless integration with Azure Blob Storage to ingest FOCUS-compliant billing data stored in parquet format. This plugin supports SAS token authentication, automatic file discovery, and batch processing for optimal performance.',
            'category': 'Data Connector',
            'tags': ['Azure', 'Blob Storage', 'FOCUS', 'Parquet'],
            'rating': 4.9,
            'downloads': '15k+',
            'license': 'MIT',
            'requirements': ['Azure Storage Account with Blob service', 'Valid SAS token with read permissions', 'FOCUS-compliant parquet files', 'Network connectivity to Azure'],
            'features': ['SAS token authentication', 'Automatic parquet file discovery', 'Batch processing support', 'Container path filtering', 'Connection testing', 'Error handling and retry logic'],
            'is_installed': True,
            'is_active': True,
            'is_configurable': True,
            'last_updated': '2024-01-15'
        },
        {
            'plugin_name': 'focus-12-transformer',
            'display_name': 'FOCUS 1.2 Transformer',
            'version': '2.2.0',
            'author': 'FinOps Foundation',
            'description': 'Transform FOCUS parquet files to Moose model FOCUS 1.2 data tables',
            'long_description': 'The FOCUS 1.2 Transformer converts FOCUS-compliant parquet files into canonical FOCUS 1.2 data tables optimized for analytics and reporting. It includes comprehensive schema validation, data type conversion, and performance optimization features.',
            'category': 'Transformer',
            'tags': ['FOCUS', 'Transform', '1.2', 'Moose', 'Schema'],
            'rating': 4.9,
            'downloads': '12k+',
            'license': 'Apache-2.0',
            'requirements': ['FOCUS-compliant input data', 'ClickHouse database connection', 'Sufficient memory for batch processing', 'Valid FOCUS schema definitions'],
            'features': ['FOCUS 1.2 schema compliance', 'Automatic data type conversion', 'Schema validation and error reporting', 'Batch processing with configurable size', 'Multiple compression formats', 'Performance optimization'],
            'is_installed': True,
            'is_active': True,
            'is_configurable': True,
            'last_updated': '2024-01-18'
        },
        {
            'plugin_name': 'clickhouse-sink',
            'display_name': 'ClickHouse Sink',
            'version': '1.4.0',
            'author': 'ClickHouse Inc.',
            'description': 'Write transformed data to ClickHouse database with SSL support',
            'long_description': 'The ClickHouse Sink plugin provides high-performance data ingestion into ClickHouse databases with support for SSL/TLS encryption, batch processing, and automatic table creation. Optimized for FOCUS 1.2 data models with Moose integration.',
            'category': 'Data Sink',
            'tags': ['ClickHouse', 'Database', 'SSL', 'Batch Processing'],
            'rating': 4.8,
            'downloads': '8k+',
            'license': 'Apache-2.0',
            'requirements': ['ClickHouse server (version 21.3+)', 'Valid database credentials', 'Network connectivity to ClickHouse host', 'SSL certificate (if using SSL)'],
            'features': ['SSL/TLS encrypted connections', 'Configurable batch processing', 'Automatic table creation', 'Connection pooling and retry logic', 'Moose model compatibility', 'Performance monitoring and metrics'],
            'is_installed': True,
            'is_active': True,
            'is_configurable': True,
            'last_updated': '2024-01-20'
        },
        {
            'plugin_name': 'azure-ea-connector',
            'display_name': 'Azure EA Connector',
            'version': '1.2.0',
            'author': 'Microsoft',
            'description': 'Connect to Azure Enterprise Agreement billing data',
            'long_description': 'Extract comprehensive billing data from Azure Enterprise Agreement accounts with support for usage details, marketplace charges, and cost management APIs.',
            'category': 'Data Connector',
            'tags': ['Azure', 'EA', 'Enterprise Agreement', 'Billing'],
            'rating': 4.8,
            'downloads': '10k+',
            'license': 'MIT',
            'requirements': ['Azure EA enrollment', 'Valid API key', 'Enterprise Agreement access'],
            'features': ['EA billing data extraction', 'Usage details', 'Marketplace charges', 'Cost management integration'],
            'is_installed': True,
            'is_active': True,
            'is_configurable': True,
            'last_updated': '2024-01-10'
        },
        {
            'plugin_name': 'gcp-billing-export',
            'display_name': 'GCP Billing Export',
            'version': '0.9.2',
            'author': 'Google',
            'description': 'Export Google Cloud Platform billing data',
            'long_description': 'Connect to Google Cloud Platform billing export data stored in BigQuery with support for detailed usage and cost analysis.',
            'category': 'Data Connector',
            'tags': ['GCP', 'Google Cloud', 'BigQuery', 'Billing'],
            'rating': 4.6,
            'downloads': '3k+',
            'license': 'Apache-2.0',
            'requirements': ['GCP project with billing enabled', 'Service account credentials', 'BigQuery access'],
            'features': ['BigQuery integration', 'Detailed usage data', 'Cost analysis', 'Service-level breakdown'],
            'is_installed': True,
            'is_active': True,
            'is_configurable': True,
            'last_updated': '2024-01-05'
        },
        {
            'plugin_name': 'aws-cost-explorer',
            'display_name': 'AWS Cost Explorer',
            'version': '1.0.1',
            'author': 'Amazon',
            'description': 'Connect to AWS Cost Explorer API for billing data',
            'long_description': 'Extract comprehensive AWS billing and cost data using the Cost Explorer API with support for detailed cost breakdowns and usage analysis.',
            'category': 'Data Connector',
            'tags': ['AWS', 'Cost Explorer', 'Billing', 'Usage'],
            'rating': 4.5,
            'downloads': '15k+',
            'license': 'Apache-2.0',
            'requirements': ['AWS account with Cost Explorer enabled', 'IAM credentials with Cost Explorer permissions'],
            'features': ['Cost Explorer API integration', 'Detailed cost breakdowns', 'Usage analysis', 'Service-level costs'],
            'is_installed': False,
            'is_active': False,
            'is_configurable': True,
            'last_updated': '2024-01-12'
        }
    ]
    
    with conn.cursor() as cur:
        for plugin in plugins_data:
            # Check if plugin already exists
            cur.execute(f"SELECT id FROM {schema_name}.plugin_market WHERE plugin_name = %s", (plugin['plugin_name'],))
            if cur.fetchone():
                continue  # Skip if already exists
            
            insert_sql = f"""
            INSERT INTO {schema_name}.plugin_market 
            (plugin_name, display_name, version, author, description, long_description, 
             category, tags, rating, downloads, license, requirements, features, 
             is_installed, is_active, is_configurable, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            cur.execute(insert_sql, (
                plugin['plugin_name'], plugin['display_name'], plugin['version'], 
                plugin['author'], plugin['description'], plugin['long_description'],
                plugin['category'], plugin['tags'], plugin['rating'], plugin['downloads'],
                plugin['license'], plugin['requirements'], plugin['features'],
                plugin['is_installed'], plugin['is_active'], plugin['is_configurable'],
                plugin['last_updated']
            ))
        
        conn.commit()
        print(f"✅ Populated plugin marketplace with {len(plugins_data)} plugins")

def setup_default_plugin_configurations(conn, moose_config):
    """Set up default configurations for all plugins"""
    
    # Azure Blob Storage Connector
    azure_blob_config = {
        "storageAccount": "",
        "sasToken": "",
        "dataContainer": "focus-data",
        "pathPrefix": "billing/"
    }
    insert_plugin_configuration(
        conn, 
        "Azure Blob Storage Connector", 
        azure_blob_config,
        "Default configuration for Azure Blob Storage connector"
    )
    
    # FOCUS 1.2 Transformer
    focus_transformer_config = {
        "inputFormat": "parquet",
        "outputModel": "moose",
        "focusVersion": "1.2",
        "compressionType": "snappy",
        "batchSize": 10000,
        "enableValidation": True,
        "sinkPlugin": "ClickHouse Sink"
    }
    insert_plugin_configuration(
        conn, 
        "FOCUS 1.2 Transformer", 
        focus_transformer_config,
        "Default configuration for FOCUS 1.2 transformer with Moose model output"
    )
    
    # ClickHouse Sink - Use values from moose.config.toml
    clickhouse_config = moose_config.get('clickhouse_config', {})
    clickhouse_sink_config = {
        "dbName": clickhouse_config.get('db_name', 'finops-odw'),
        "user": clickhouse_config.get('user', 'finops'),
        "password": clickhouse_config.get('password', 'cU2f947&9T{6d'),
        "host": clickhouse_config.get('host', 'ck.mightytech.cn'),
        "port": clickhouse_config.get('host_port', 8443),
        "useSSL": clickhouse_config.get('use_ssl', True),
        "tableName": "focus_billing_data",
        "createTableIfNotExists": True,
        "batchSize": 1000
    }
    insert_plugin_configuration(
        conn, 
        "ClickHouse Sink", 
        clickhouse_sink_config,
        "ClickHouse sink configuration from moose.config.toml"
    )
    
    # Azure EA Connector
    azure_ea_config = {
        "enrollmentId": "",
        "apiKey": "",
        "apiVersion": "2023-05-01",
        "billingPeriod": "current",
        "includeUsageDetails": True,
        "includeMarketplaceCharges": True
    }
    insert_plugin_configuration(
        conn, 
        "Azure EA Connector", 
        azure_ea_config,
        "Default configuration for Azure Enterprise Agreement connector"
    )
    
    # GCP Billing Export
    gcp_config = {
        "projectId": "",
        "serviceAccountKey": "",
        "datasetId": "billing_export",
        "tableId": "gcp_billing_export",
        "location": "US"
    }
    insert_plugin_configuration(
        conn, 
        "GCP Billing Export", 
        gcp_config,
        "Default configuration for Google Cloud Platform billing export"
    )

def verify_setup(conn):
    """Verify the plugin configurations were set up correctly"""
    schema_name = 'plugin_registry'
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check plugin market
        cur.execute(f"""
        SELECT display_name, version, category, is_installed, is_active, rating
        FROM {schema_name}.plugin_market 
        ORDER BY display_name;
        """)
        
        market_plugins = cur.fetchall()
        
        print(f"\n📋 Plugin Marketplace Summary:")
        print(f"{'Plugin Name':<30} {'Version':<10} {'Category':<15} {'Installed':<10} {'Rating':<8}")
        print("-" * 80)
        
        for plugin in market_plugins:
            installed = "✅ Yes" if plugin['is_installed'] else "❌ No"
            rating = f"⭐ {plugin['rating']}"
            print(f"{plugin['display_name']:<30} {plugin['version']:<10} {plugin['category']:<15} {installed:<10} {rating:<8}")
        
        print(f"\n✅ Total marketplace plugins: {len(market_plugins)}")
        
        # Check configurations
        cur.execute(f"""
        SELECT plugin_name, created_at, is_active, description
        FROM {schema_name}.plugin_configurations 
        WHERE is_active = true
        ORDER BY plugin_name;
        """)
        
        configurations = cur.fetchall()
        
        print(f"\n📋 Plugin Configurations Summary:")
        print(f"{'Plugin Name':<30} {'Status':<10} {'Created':<20}")
        print("-" * 65)
        
        for config in configurations:
            status = "✅ Active" if config['is_active'] else "❌ Inactive"
            created = config['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            print(f"{config['plugin_name']:<30} {status:<10} {created:<20}")
        
        print(f"\n✅ Total active configurations: {len(configurations)}")

def main():
    """Main setup function"""
    print("🚀 Starting Plugin Configuration Setup...")
    print("=" * 60)
    
    # Load moose configuration
    moose_config = load_moose_config()
    
    # Connect to database
    conn = get_db_connection(moose_config)
    
    try:
        # Create schema and tables
        create_plugin_registry_schema(conn)
        
        # Populate plugin marketplace
        populate_plugin_market(conn)
        
        # Set up default plugin configurations
        setup_default_plugin_configurations(conn, moose_config)
        
        # Verify setup
        verify_setup(conn)
        
        print("\n🎉 Plugin configuration setup completed successfully!")
        print("\nNext steps:")
        print("1. Update plugin configurations through the bia frontend UI")
        print("2. Add your Azure storage account and SAS token")
        print("3. Verify ClickHouse connection settings")
        print("4. Test plugin connections in the admin panel")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        conn.rollback()
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
