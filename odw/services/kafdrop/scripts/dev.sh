#!/bin/bash

# Kafdrop Service Development Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SERVICE_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print colored output
print_status() {
    echo -e "${BLUE}[KAFDROP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[KAFDROP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[KAFDROP]${NC} $1"
}

print_error() {
    echo -e "${RED}[KAFDROP]${NC} $1"
}

# Port configuration
REDPANDA_PORT=9092
REDPANDA_ADMIN_PORT=9644
REDPANDA_CONTAINER_NAME=${REDPANDA_CONTAINER_NAME:-"data-warehouse-redpanda-1"}
REDPANDA_WAIT_TIMEOUT=${REDPANDA_WAIT_TIMEOUT:-300}
REDPANDA_WAIT_INTERVAL=${REDPANDA_WAIT_INTERVAL:-2}
KAFDROP_CONTAINER_NAME="data-warehouse-kafdrop"
KAFDROP_PORT=9999

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        return 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        return 1
    fi

    return 0
}

is_port_in_use() {
    local port=$1
    if lsof -i ":$port" >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is available
    fi
}

get_docker_network() {
    local network_name="data-warehouse_default"

    # Check if network exists
    if docker network ls --format "{{.Name}}" | grep -q "^${network_name}$"; then
        echo "$network_name"
    else
        print_warning "Network $network_name not found, using default" >&2
        echo "bridge"  # fallback to bridge network
    fi
}

is_kafdrop_running() {
    if ! check_docker; then
        return 1
    fi
    docker ps --filter "name=$KAFDROP_CONTAINER_NAME" --format "{{.Names}}" | grep -q "$KAFDROP_CONTAINER_NAME"
}

wait_for_redpanda() {
    print_status "Waiting for Redpanda to be ready..."

    local interval=${REDPANDA_WAIT_INTERVAL:-2}
    local timeout=${REDPANDA_WAIT_TIMEOUT:-300}

    if [ "$interval" -le 0 ]; then
        interval=2
    fi

    if [ "$timeout" -le 0 ]; then
        timeout=$((interval * 30))
    fi

    local max_attempts=$((timeout / interval))
    if (( timeout % interval != 0 )); then
        max_attempts=$((max_attempts + 1))
    fi
    if (( max_attempts < 1 )); then
        max_attempts=1
    fi

    local attempts=0

    if ! check_docker; then
        return 1
    fi

    while [ $attempts -lt $max_attempts ]; do
        local attempt_count=$((attempts + 1))
        local inspect_output
        inspect_output=$(docker inspect --format='{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}unknown{{end}}' "$REDPANDA_CONTAINER_NAME" 2>/dev/null || true)

        if [[ -z "$inspect_output" ]]; then
            print_status "Redpanda container not found ($REDPANDA_CONTAINER_NAME) (attempt $attempt_count/$max_attempts)"
        else
            local container_state="${inspect_output%%|*}"
            local health_status="${inspect_output##*|}"

            if [[ "$container_state" == "running" && "$health_status" == "healthy" ]]; then
                print_success "Redpanda is ready!"
                return 0
            fi

            if [[ "$container_state" != "running" ]]; then
                print_status "Redpanda container state: $container_state (attempt $attempt_count/$max_attempts)"
            else
                print_status "Redpanda health status: $health_status (attempt $attempt_count/$max_attempts)"
            fi
        fi

        attempts=$((attempts + 1))
        sleep "$interval"
    done

    print_warning "Redpanda not ready after $max_attempts attempts"
    return 1
}

start_kafdrop() {
    if ! check_docker; then
        print_error "Docker not available, cannot start Kafdrop"
        exit 1
    fi

    if is_kafdrop_running; then
        print_warning "Kafdrop is already running"
        return 0
    fi

    # Remove any leftover stopped container with the same name
    local existing_container_id
    existing_container_id=$(docker ps -aq --filter "name=$KAFDROP_CONTAINER_NAME" | head -n1)
    if [[ -n "$existing_container_id" ]]; then
        print_status "Removing stale Kafdrop container ($existing_container_id)"
        docker rm "$existing_container_id" > /dev/null 2>&1 || true
    fi

    # Check if port is in use
    if is_port_in_use $KAFDROP_PORT; then
        print_error "Port $KAFDROP_PORT is already in use!"
        print_status "To find what's using port $KAFDROP_PORT: lsof -i :$KAFDROP_PORT"
        exit 1
    fi

    print_status "Starting Kafdrop..."

    local network_name=$(get_docker_network)
    print_status "Using Docker network: $network_name"

    # Start Kafdrop container
    local container_output
    if ! container_output=$(docker run -d \
        --name "$KAFDROP_CONTAINER_NAME" \
        --network "$network_name" \
        --rm \
        -p $KAFDROP_PORT:9000 \
        -e KAFKA_BROKERCONNECT=redpanda:$REDPANDA_PORT \
        -e SERVER_SERVLET_CONTEXTPATH="/" \
        obsidiandynamics/kafdrop 2>&1); then
        print_error "Failed to start Kafdrop: $container_output"
        exit 1
    fi

    print_status "Kafdrop container ID: ${container_output%%\n*}"

    # Wait and verify
    sleep 3
    if is_kafdrop_running; then
        print_success "Kafdrop started successfully at http://localhost:$KAFDROP_PORT"
    else
        print_error "Failed to start Kafdrop"
        exit 1
    fi
}

main() {
    print_status "Starting Kafdrop service..."

    if ! wait_for_redpanda; then
        print_warning "Redpanda is not available. Data Warehouse might still be starting up."
        print_status "Kafdrop is not running."
        exit 0
    fi

    start_kafdrop
}

main "$@"
