#!/bin/bash

# DataLens Development Script
# Starts DataLens backend and frontend in development mode

set -e

echo "🚀 Starting DataLens development environment..."

# Load configuration
if [ -f "config/datalens.env" ]; then
    source config/datalens.env
    echo "✅ Configuration loaded"
else
    echo "❌ Configuration not found. Running setup first..."
    ./scripts/setup.sh
    source config/datalens.env
fi

# Check if repositories are cloned
if [ ! -d "backend/datalens-backend" ] || [ ! -d "frontend/datalens-ui" ]; then
    echo "📦 Repositories not found. Running setup..."
    ./scripts/setup.sh
fi

# Check if data-warehouse services are running
echo "🔍 Checking data-warehouse services..."
if ! docker ps | grep -q "data-warehouse.*temporal"; then
    echo "⚠️  Data-warehouse Temporal services not found. Starting them first..."
    cd ../data-warehouse
    if [ -f ".moose/docker-compose.yml" ]; then
        docker-compose -f .moose/docker-compose.yml up -d temporal temporal-ui postgresql
        echo "✅ Data-warehouse services started"
    else
        echo "❌ Data-warehouse docker-compose.yml not found. Please start data-warehouse services first."
        exit 1
    fi
    cd ../datalens
fi

# Start DataLens services using Docker Compose
echo "🐳 Starting DataLens services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
if curl -f http://localhost:8082/health > /dev/null 2>&1; then
    echo "✅ DataLens backend is healthy (port 8082)"
else
    echo "⚠️  DataLens backend health check failed"
fi

if curl -f http://localhost:8081 > /dev/null 2>&1; then
    echo "✅ DataLens frontend is accessible (port 8081)"
else
    echo "⚠️  DataLens frontend not yet accessible"
fi

echo ""
echo "🎉 DataLens development environment started!"
echo "📊 Frontend: http://localhost:8081"
echo "🔧 Backend API: http://localhost:8082"
echo "📋 Logs: docker-compose logs -f"
echo "🛑 Stop: docker-compose down"