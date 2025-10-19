#!/bin/bash

# Simple DataLens Development Script
# Starts DataLens with placeholder services

set -e

echo "🚀 Starting DataLens development environment (simple mode)..."

# Load configuration
if [ -f "config/datalens.env" ]; then
    source config/datalens.env
    echo "✅ Configuration loaded"
else
    echo "❌ Configuration not found. Running setup first..."
    ./scripts/setup-minimal.sh
    source config/datalens.env
fi

# Load environment variables for Docker Compose
if [ -f ".env" ]; then
    source .env
    echo "✅ Docker Compose environment loaded"
fi

# Start services using simple Docker Compose
echo "🐳 Starting DataLens services (placeholder mode)..."
docker-compose -f docker-compose.simple.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check service health
echo "🔍 Checking service health..."

# Check nginx proxy
if curl -f http://localhost:9080/health > /dev/null 2>&1; then
    echo "✅ Nginx proxy is healthy (port 9080)"
else
    echo "⚠️  Nginx proxy health check failed"
fi

# Check backend placeholder
if curl -f http://localhost:8082 > /dev/null 2>&1; then
    echo "✅ DataLens backend placeholder is running (port 8082)"
else
    echo "⚠️  DataLens backend placeholder not responding"
fi

# Check frontend placeholder
if curl -f http://localhost:8081 > /dev/null 2>&1; then
    echo "✅ DataLens frontend placeholder is accessible (port 8081)"
else
    echo "⚠️  DataLens frontend placeholder not accessible"
fi

echo ""
echo "🎉 DataLens development environment started (simple mode)!"
echo ""
echo "📊 Access Points:"
echo "   🌐 DataLens Frontend: http://localhost:8081"
echo "   🔧 DataLens Backend: http://localhost:8082"
echo "   🚀 Unified Interface: http://localhost:9080"
echo "   ⚡ Temporal UI: http://localhost:9080/temporal"
echo ""
echo "🔗 ClickHouse Connection:"
echo "   📍 Host: ${CLICKHOUSE_HOST}:${CLICKHOUSE_PORT}"
echo "   🗄️  Database: ${CLICKHOUSE_DB}"
echo "   👤 User: ${CLICKHOUSE_USER}"
echo ""
echo "📋 Management Commands:"
echo "   📊 View logs: docker-compose -f docker-compose.simple.yml logs -f"
echo "   🛑 Stop services: docker-compose -f docker-compose.simple.yml down"
echo "   🔄 Restart: ./scripts/dev-clean.sh"
echo ""
echo "🚀 Next Steps:"
echo "   1. Clone DataLens repositories for full functionality"
echo "   2. Run ./scripts/build.sh to build complete platform"
echo "   3. Use ./scripts/dev.sh for full development environment"