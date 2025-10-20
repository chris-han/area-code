#!/bin/bash

# DataLens Development Script
# Starts DataLens integrated with Moose data warehouse backend

set -e

echo "🚀 Starting DataLens development environment (integrated with Moose)..."

detect_compose_command() {
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE_CMD=("docker" "compose")
    elif command -v docker-compose >/dev/null 2>&1; then
        DOCKER_COMPOSE_CMD=("docker-compose")
    else
        echo "❌ Docker Compose not found. Please install Docker Compose v2 or the legacy docker-compose binary."
        exit 1
    fi
}

detect_compose_command

# Function to check if Moose services are running
check_moose_services() {
    echo "🔍 Checking Moose data-warehouse services..."
    
    local missing_services=()
    
    if ! docker ps --format "table {{.Names}}" | grep -q "data-warehouse.*redis"; then
        missing_services+=("redis")
    fi
    
    if ! docker ps --format "table {{.Names}}" | grep -q "data-warehouse.*redpanda"; then
        missing_services+=("redpanda")
    fi
    
    if ! docker ps --format "table {{.Names}}" | grep -q "data-warehouse.*temporal"; then
        missing_services+=("temporal")
    fi
    
    if [ ${#missing_services[@]} -gt 0 ]; then
        echo "❌ Missing Moose services: ${missing_services[*]}"
        echo "🔧 Starting required Moose services..."
        
        cd ../data-warehouse
        if [ -f ".moose/docker-compose.yml" ]; then
            "${DOCKER_COMPOSE_CMD[@]}" -f .moose/docker-compose.yml up -d redis redpanda temporal temporal-ui postgresql
            echo "✅ Moose services started"
        else
            echo "❌ Moose docker-compose.yml not found at ../data-warehouse/.moose/"
            echo "Please start the data-warehouse services first."
            exit 1
        fi
        cd ../datalens
        
        # Wait for services to be ready
        echo "⏳ Waiting for Moose services to start..."
        sleep 15
    else
        echo "✅ All required Moose services are running"
    fi
}

# Function to generate integrated docker-compose configuration
generate_integrated_config() {
    echo "📝 Generating integrated docker-compose configuration..."
    
    # Determine which compose files to use
    local compose_files=()
    
    if [ ! -d "datalens-backend" ] || [ ! -d "datalens-ui" ]; then
        echo "📦 Using simple/placeholder configuration (repositories not found)"
        compose_files+=("-f" "docker-compose.simple.yml")
    else
        echo "📦 Using full DataLens configuration"
        compose_files+=("-f" "docker-compose.yml")
    fi
    
    # Always add override for development
    if [ -f "docker-compose.override.yml" ]; then
        compose_files+=("-f" "docker-compose.override.yml")
    fi
    
    echo "🔧 Compose files: ${compose_files[*]}"
    export COMPOSE_FILES="${compose_files[*]}"
}

# Function to create DataLens Kafka topics
create_datalens_topics() {
    echo "📡 Creating DataLens Kafka topics..."
    
    local topics=("datalens_events" "datalens_metrics" "datalens_user_actions")
    
    for topic in "${topics[@]}"; do
        if docker exec data-warehouse_redpanda_1 rpk topic list 2>/dev/null | grep -q "^${topic}$"; then
            echo "✅ Topic ${topic} already exists"
        else
            echo "🔧 Creating topic: ${topic}"
            docker exec data-warehouse_redpanda_1 rpk topic create "${topic}" --partitions 3 --replicas 1 2>/dev/null || true
        fi
    done
}

# Load configuration
if [ -f "config/datalens.env" ]; then
    source config/datalens.env
    echo "✅ Configuration loaded"
else
    echo "❌ Configuration not found. Running setup first..."
    ./scripts/setup.sh
    source config/datalens.env
fi

# Check Moose services
check_moose_services

# Generate integrated configuration
generate_integrated_config

# Create DataLens topics in Redpanda
create_datalens_topics

# Start DataLens services using integrated configuration
echo "🐳 Starting DataLens services (integrated with Moose)..."
eval "${DOCKER_COMPOSE_CMD[@]}" ${COMPOSE_FILES} up -d

# Wait for services to be ready
echo "⏳ Waiting for DataLens services to start..."
sleep 15

# Check service health
echo "🔍 Checking service health..."
if curl -f http://localhost:8083/health > /dev/null 2>&1 || curl -f http://localhost:8083 > /dev/null 2>&1; then
    echo "✅ DataLens backend is healthy (port 8083)"
else
    echo "⚠️  DataLens backend health check failed (this is normal for placeholder)"
fi

if curl -f http://localhost:8081 > /dev/null 2>&1; then
    echo "✅ DataLens frontend is accessible (port 8081)"
else
    echo "⚠️  DataLens frontend not yet accessible"
fi

if curl -f http://localhost:9081/health > /dev/null 2>&1; then
    echo "✅ DataLens unified access is healthy (port 9081)"
else
    echo "⚠️  DataLens unified access not available (nginx proxy may not be running)"
fi

# Verify Moose integration
echo "🔗 Verifying Moose integration..."
if docker exec datalens_datalens-backend_1 redis-cli -h redis -p 6379 -n 1 ping 2>/dev/null | grep -q "PONG"; then
    echo "✅ Redis connection (database 1) - OK"
else
    echo "⚠️  Redis connection failed"
fi

echo ""
echo "🎉 DataLens development environment started (integrated with Moose)!"
echo ""
echo "📊 Access Points:"
echo "   Frontend: http://localhost:8081"
echo "   Backend API: http://localhost:8083"
echo "   Unified Access: http://localhost:9081"
echo ""
echo "🔗 Moose Integration:"
echo "   Redis: Shared (database 1)"
echo "   Redpanda: Shared (datalens_* topics)"
echo "   ClickHouse: External (shared)"
echo ""
echo "🛠️  Management:"
if [ "${DOCKER_COMPOSE_CMD[0]}" = "docker" ]; then
    echo "   Logs: docker compose ${COMPOSE_FILES} logs -f"
    echo "   Stop: docker compose ${COMPOSE_FILES} down"
else
    echo "   Logs: docker-compose ${COMPOSE_FILES} logs -f"
    echo "   Stop: docker-compose ${COMPOSE_FILES} down"
fi
echo "   Topics: docker exec data-warehouse_redpanda_1 rpk topic list | grep datalens_"
