#!/bin/bash

# DataLens Setup Script for Azure Billing Intelligence
# This script sets up DataLens backend and frontend with ABI extensions

set -e

echo "🚀 Setting up DataLens platform for Azure Billing Intelligence..."

# Create directories
mkdir -p backend frontend config

# Clone DataLens backend
if [ ! -d "datalens-backend" ]; then
    echo "📦 Cloning DataLens backend..."
    cd .
    git clone https://github.com/chris-han/datalens-backend.git
    cd ..
fi

# Clone DataLens frontend
if [ ! -d "datalens-ui" ]; then
    echo "📦 Cloning DataLens frontend..."
    cd .
    git clone https://github.com/chris-han/datalens-ui.git
    cd ..
fi

# Load ClickHouse configuration from data-warehouse .env
echo "🔧 Loading ClickHouse configuration..."
if [ -f "../data-warehouse/.env" ]; then
    source ../data-warehouse/.env
    echo "✅ ClickHouse configuration loaded"
else
    echo "❌ Error: ../data-warehouse/.env not found"
    exit 1
fi

# Create DataLens configuration
echo "📝 Creating DataLens configuration..."
cat > config/datalens.env << EOF
# DataLens Configuration for ABI
DATALENS_PORT=8081
DATALENS_BACKEND_PORT=8082

# ClickHouse Connection (from data-warehouse .env)
CLICKHOUSE_HOST=${CLICKHOUSE_HOST}
CLICKHOUSE_PORT=${CLICKHOUSE_HOST_PORT}
CLICKHOUSE_USER=${CLICKHOUSE_USER}
CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD}
CLICKHOUSE_DB=${CLICKHOUSE_DB_NAME}
CLICKHOUSE_USE_SSL=${CLICKHOUSE_USE_SSL}

# DataLens Backend Configuration
DATALENS_BACKEND_HOST=localhost
DATALENS_BACKEND_PORT=8082

# CORS Configuration
CORS_ORIGINS=http://localhost:8081,http://localhost:3000

# ABI Extensions
ENABLE_ABI_EXTENSIONS=true
FOCUS_SPECIFICATION_VERSION=1.0
EOF

echo "✅ DataLens setup completed!"
echo "📋 Configuration saved to config/datalens.env"
echo "🌐 DataLens will run on port 8081 (avoiding Temporal UI port 8080)"
echo "🔗 Backend will run on port 8082"