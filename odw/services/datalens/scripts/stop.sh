#!/bin/bash

# DataLens Stop Script
# Stops DataLens services while preserving Moose infrastructure

set -e

echo "🛑 Stopping DataLens services..."

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

# Function to determine compose files
get_compose_files() {
    local compose_files=()
    
    if [ ! -d "datalens-backend" ] || [ ! -d "datalens-ui" ]; then
        compose_files+=("-f" "docker-compose.simple.yml")
    else
        compose_files+=("-f" "docker-compose.yml")
    fi
    
    if [ -f "docker-compose.override.yml" ]; then
        compose_files+=("-f" "docker-compose.override.yml")
    fi
    
    echo "${compose_files[*]}"
}

# Get compose files
COMPOSE_FILES=$(get_compose_files)

# Stop DataLens services
echo "🐳 Stopping DataLens containers..."
eval "${DOCKER_COMPOSE_CMD[@]}" ${COMPOSE_FILES} down

# Optional: Remove DataLens volumes (uncomment if needed)
# echo "🗑️  Removing DataLens volumes..."
# eval "${DOCKER_COMPOSE_CMD[@]}" ${COMPOSE_FILES} down -v

echo ""
echo "✅ DataLens services stopped!"
echo "ℹ️  Moose services (Redis, Redpanda, ClickHouse) are still running"
echo ""
echo "🔧 To stop Moose services as well:"
echo "   cd ../data-warehouse && docker compose -f .moose/docker-compose.yml down"
echo ""
echo "📡 DataLens Kafka topics are preserved in Redpanda"
echo "   List topics: docker exec data-warehouse_redpanda_1 rpk topic list | grep datalens_"