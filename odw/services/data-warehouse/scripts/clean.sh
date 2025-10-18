#!/bin/bash

# Data Warehouse Service Cleanup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SERVICE_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[DATA-WAREHOUSE]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[DATA-WAREHOUSE]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[DATA-WAREHOUSE]${NC} $1"
}

print_error() {
    echo -e "${RED}[DATA-WAREHOUSE]${NC} $1"
}

# Port configuration
DATA_WAREHOUSE_PORT=4200

# Virtual environment utility functions
check_venv_exists() {
    if [ -d ".venv" ]; then
        return 0  # .venv exists
    else
        return 1  # .venv does not exist
    fi
}

ensure_venv_activated() {
    # First check if venv exists
    if ! check_venv_exists; then
        print_warning "Virtual environment not found, skipping moose-cli clean"
        return 1
    fi

    # Check if we're already in the virtual environment
    if [ -z "$VIRTUAL_ENV" ] || [[ "$VIRTUAL_ENV" != *"$(pwd)/.venv" ]]; then
        print_status "Activating virtual environment..."
        source .venv/bin/activate

        if [ -n "$VIRTUAL_ENV" ]; then
            print_success "Virtual environment activated: $VIRTUAL_ENV"
        else
            print_error "Failed to activate virtual environment"
            return 1
        fi
    else
        print_success "Virtual environment already active: $VIRTUAL_ENV"
    fi
}

clean_temporal_containers() {
    print_status "Cleaning Temporal containers..."
    
    # List of Temporal container names
    local temporal_containers=(
        "data-warehouse-temporal-1"
        "data-warehouse-temporal-admin-tools-1" 
        "data-warehouse-temporal-ui-1"
        "data-warehouse-postgresql-1"
    )
    
    for container in "${temporal_containers[@]}"; do
        if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
            print_status "Stopping and removing container: $container"
            docker stop "$container" >/dev/null 2>&1 || true
            docker rm "$container" >/dev/null 2>&1 || true
            print_success "Container $container cleaned"
        fi
    done
    
    # Clean up Temporal networks
    local temporal_networks=(
        "data-warehouse_temporal-network"
        "data-warehouse_clickhouse-network"
        "data-warehouse_default"
    )
    
    for network in "${temporal_networks[@]}"; do
        if docker network ls --format "{{.Name}}" | grep -q "^${network}$"; then
            print_status "Removing network: $network"
            docker network rm "$network" >/dev/null 2>&1 || true
        fi
    done
    
    print_success "Temporal containers and networks cleaned"
}

clean_moose_infrastructure() {
    if ensure_venv_activated; then
        # Check if moose-cli is available
        if command -v moose-cli &> /dev/null; then
            print_status "Cleaning Moose infrastructure..."
            moose-cli clean
            print_success "Moose infrastructure cleaned"
        else
            print_warning "moose-cli not found, skipping infrastructure cleanup"
        fi
    else
        print_warning "Could not activate virtual environment, skipping moose-cli clean"
    fi
    
    # Also clean Temporal containers explicitly
    clean_temporal_containers
}

# Reusable function to clean a specific port
clean_port() {
    local port=$1
    local service_name=$2
    
    print_status "Checking for processes using port $port ($service_name)..."

    # Get all PIDs using the port (both LISTEN and ESTABLISHED)
    local pids=$(lsof -ti :$port 2>/dev/null)

    if [ -n "$pids" ]; then
        for pid in $pids; do
            print_warning "Found process $pid using port $port"
            print_status "Attempting to terminate process $pid..."

            # Try graceful termination first
            if kill "$pid" 2>/dev/null; then
                print_status "Waiting up to 10 seconds for process $pid to terminate..."

                local attempts=0
                local max_attempts=10
                while [ $attempts -lt $max_attempts ]; do
                    if ! kill -0 "$pid" 2>/dev/null; then
                        print_success "Process $pid terminated gracefully"
                        break
                    fi
                    sleep 1
                    attempts=$((attempts + 1))
                done

                # Process still running after 10 seconds, force kill
                if kill -0 "$pid" 2>/dev/null; then
                    print_warning "Process $pid still running after 10 seconds, force killing..."
                    kill -9 "$pid" 2>/dev/null
                    sleep 1

                    # Final check after force kill
                    if kill -0 "$pid" 2>/dev/null; then
                        print_error "Failed to kill process $pid even with force"
                    else
                        print_success "Process $pid force killed successfully"
                    fi
                fi
            else
                print_warning "Could not send signal to process $pid (may already be dead)"
            fi
        done
    else
        print_success "No processes found using port $port ($service_name)"
    fi
}

clean_all_odw_ports() {
    print_status "Cleaning all ODW service ports..."
    
    # Define all ODW ports
    clean_port 4200 "Moose API"
    clean_port 8501 "Streamlit Frontend" 
    clean_port 9999 "Kafdrop UI"
    clean_port 9500 "MinIO API"
    clean_port 9501 "MinIO Console"
    
    # Temporal ports (both internal and external mappings)
    clean_port 17233 "Temporal Server"
    clean_port 7233 "Temporal Internal"
    clean_port 8081 "Temporal UI"
    clean_port 8080 "Temporal UI Internal"
    clean_port 5432 "PostgreSQL (Temporal DB)"
    
    # Other infrastructure ports
    clean_port 18123 "ClickHouse HTTP"
    clean_port 9000 "ClickHouse Native"
    clean_port 19092 "Redpanda"
    clean_port 6379 "Redis"
    
    print_success "All ODW ports cleaned"
}

clean_data_warehouse_port() {
    clean_port $DATA_WAREHOUSE_PORT "Data Warehouse"
}

main() {
    print_status "Cleaning up Data Warehouse service..."

    # Clean Moose infrastructure first
    clean_moose_infrastructure
    
    # Clean all ODW ports to ensure complete cleanup
    clean_all_odw_ports

    print_success "Data Warehouse service cleanup completed"
}

main "$@"