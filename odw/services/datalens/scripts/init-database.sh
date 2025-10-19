#!/bin/bash

# Initialize DataLens Database in Existing Temporal PostgreSQL
# Creates the DataLens database and ABI registry schema

set -e

echo "🗄️  Initializing DataLens database in existing Temporal PostgreSQL..."

# Load configuration
if [ -f "config/datalens.env" ]; then
    source config/datalens.env
    echo "✅ Configuration loaded"
else
    echo "❌ Configuration not found. Running setup first..."
    ./scripts/setup-minimal.sh
    source config/datalens.env
fi

# Load environment variables
if [ -f ".env" ]; then
    source .env
    echo "✅ Environment variables loaded"
fi

# Check if PostgreSQL is accessible
echo "🔍 Checking PostgreSQL connectivity..."
if ! nc -z ${TEMPORAL_DB_HOST} ${TEMPORAL_DB_PORT}; then
    echo "❌ Cannot connect to PostgreSQL at ${TEMPORAL_DB_HOST}:${TEMPORAL_DB_PORT}"
    echo "Please ensure data-warehouse services are running"
    exit 1
fi

# Create DataLens database if it doesn't exist
echo "📝 Creating DataLens database..."
export PGPASSWORD="${TEMPORAL_DB_PASSWORD}"

# Check if database exists
DB_EXISTS=$(psql -h ${TEMPORAL_DB_HOST} -p ${TEMPORAL_DB_PORT} -U ${TEMPORAL_DB_USER} -tc "SELECT 1 FROM pg_database WHERE datname = 'datalens'" | grep -c 1 || echo "0")

if [ "$DB_EXISTS" = "0" ]; then
    echo "Creating datalens database..."
    psql -h ${TEMPORAL_DB_HOST} -p ${TEMPORAL_DB_PORT} -U ${TEMPORAL_DB_USER} -c "CREATE DATABASE datalens;"
    echo "✅ DataLens database created"
else
    echo "✅ DataLens database already exists"
fi

# Create ABI registry database if it doesn't exist
ABI_DB_EXISTS=$(psql -h ${TEMPORAL_DB_HOST} -p ${TEMPORAL_DB_PORT} -U ${TEMPORAL_DB_USER} -tc "SELECT 1 FROM pg_database WHERE datname = 'abi_registry'" | grep -c 1 || echo "0")

if [ "$ABI_DB_EXISTS" = "0" ]; then
    echo "Creating abi_registry database..."
    psql -h ${TEMPORAL_DB_HOST} -p ${TEMPORAL_DB_PORT} -U ${TEMPORAL_DB_USER} -c "CREATE DATABASE abi_registry;"
    echo "✅ ABI registry database created"
else
    echo "✅ ABI registry database already exists"
fi

# Create plugin_registry schema in abi_registry database
echo "📝 Creating plugin_registry schema..."
psql -h ${TEMPORAL_DB_HOST} -p ${TEMPORAL_DB_PORT} -U ${TEMPORAL_DB_USER} -d abi_registry -c "
CREATE SCHEMA IF NOT EXISTS plugin_registry;

-- Create plugin metadata table
CREATE TABLE IF NOT EXISTS plugin_registry.plugins (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    category VARCHAR(100),
    config_schema JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create plugin instances table
CREATE TABLE IF NOT EXISTS plugin_registry.plugin_instances (
    id SERIAL PRIMARY KEY,
    plugin_id INTEGER REFERENCES plugin_registry.plugins(id),
    instance_name VARCHAR(255) NOT NULL,
    config JSONB,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_plugins_name ON plugin_registry.plugins(name);
CREATE INDEX IF NOT EXISTS idx_plugins_category ON plugin_registry.plugins(category);
CREATE INDEX IF NOT EXISTS idx_plugin_instances_plugin_id ON plugin_registry.plugin_instances(plugin_id);
"

echo "✅ Plugin registry schema created"

echo ""
echo "🎉 Database initialization completed!"
echo ""
echo "📋 Database Summary:"
echo "   🗄️  Host: ${TEMPORAL_DB_HOST}:${TEMPORAL_DB_PORT}"
echo "   👤 User: ${TEMPORAL_DB_USER}"
echo "   📊 DataLens DB: datalens"
echo "   🔌 ABI Registry DB: abi_registry"
echo "   📁 Plugin Schema: plugin_registry"
echo ""
echo "🔗 Integration Status:"
echo "   ✅ Reuses existing Temporal PostgreSQL infrastructure"
echo "   ✅ No additional PostgreSQL container needed"
echo "   ✅ Shared database infrastructure with data-warehouse"