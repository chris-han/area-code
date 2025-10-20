#!/bin/bash

# DataLens Status Script
# Shows status of DataLens and Moose integration

set -e

echo "📊 DataLens & Moose Integration Status"
echo "======================================"

# Function to check if service is running
check_service() {
    local service_name="$1"
    local port="$2"
    local endpoint="${3:-/}"
    
    if curl -f -s "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
        echo "✅ ${service_name} (port ${port}) - Running"
        return 0
    else
        echo "❌ ${service_name} (port ${port}) - Not accessible"
        return 1
    fi
}

# Function to check docker container
check_container() {
    local container_pattern="$1"
    local service_name="$2"
    
    if docker ps --format "table {{.Names}}" | grep -q "${container_pattern}"; then
        echo "✅ ${service_name} - Container running"
        return 0
    else
        echo "❌ ${service_name} - Container not found"
        return 1
    fi
}

echo ""
echo "🔍 DataLens Services:"
check_service "DataLens Frontend" "8081"
check_service "DataLens Backend" "8083" "/health"
check_service "DataLens Unified Access" "9081" "/health"

echo ""
echo "🔍 Moose Services:"
check_service "Temporal UI" "8080"
check_service "Redpanda Proxy" "18082"
check_container "data-warehouse.*redis" "Redis"
check_container "data-warehouse.*redpanda" "Redpanda"
check_container "data-warehouse.*temporal" "Temporal"

echo ""
echo "🔗 Integration Tests:"

# Test Redis connection
if docker exec datalens_datalens-backend_1 redis-cli -h redis -p 6379 -n 1 ping 2>/dev/null | grep -q "PONG"; then
    echo "✅ Redis (database 1) - Connected"
else
    echo "❌ Redis (database 1) - Connection failed"
fi

# Test Redpanda topics
echo ""
echo "📡 DataLens Kafka Topics:"
if docker exec data-warehouse_redpanda_1 rpk topic list 2>/dev/null | grep "datalens_"; then
    echo "✅ DataLens topics found"
else
    echo "⚠️  No DataLens topics found (this is normal on first run)"
fi

# Test external ClickHouse (if configured)
echo ""
echo "🗄️  ClickHouse Configuration:"
if [ -n "$CLICKHOUSE_HOST" ] && [ -n "$CLICKHOUSE_HOST_PORT" ]; then
    echo "   Host: ${CLICKHOUSE_HOST}:${CLICKHOUSE_HOST_PORT}"
    if curl -f -s "${CLICKHOUSE_HOST}:${CLICKHOUSE_HOST_PORT}/ping" > /dev/null 2>&1; then
        echo "✅ External ClickHouse - Connected"
    else
        echo "❌ External ClickHouse - Connection failed"
    fi
else
    echo "⚠️  ClickHouse environment variables not set"
fi

echo ""
echo "📋 Container Status:"
echo "DataLens containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "datalens" || echo "   No DataLens containers running"

echo ""
echo "Moose containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "data-warehouse" || echo "   No Moose containers running"

echo ""
echo "🔧 Quick Commands:"
echo "   Start: ./scripts/dev.sh"
echo "   Stop: ./scripts/stop.sh"
echo "   Logs: docker compose logs -f"
echo "   Topics: docker exec data-warehouse_redpanda_1 rpk topic list"