#!/bin/bash

# Data Warehouse Service Development Script

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

configure_docker_timeouts() {
    export DOCKER_CLIENT_TIMEOUT="${DOCKER_CLIENT_TIMEOUT:-900}"
    export COMPOSE_HTTP_TIMEOUT="${COMPOSE_HTTP_TIMEOUT:-900}"
    local base_compose="$SERVICE_DIR/.moose/docker-compose.yml"
    local override_compose="$SERVICE_DIR/.moose/docker-compose.override.yml"

    local clickhouse_host=""
    local temporal_host=""
    local temporal_db_host=""
    if [[ -f "$SERVICE_DIR/.env" ]]; then
        set -a
        # shellcheck disable=SC1090
        source "$SERVICE_DIR/.env"
        set +a
        clickhouse_host="${MOOSE_CLICKHOUSE_HOST:-}"
        temporal_host="${MOOSE_TEMPORAL_HOST:-}"
        temporal_db_host="${TEMPORAL_DB_HOST:-}"
    fi

    if [[ -f "$override_compose" ]]; then
        export COMPOSE_FILE="$base_compose:$override_compose"
        print_status "Using Docker Compose files: $COMPOSE_FILE"
    else
        export COMPOSE_FILE="$base_compose"
        print_status "Using Docker Compose file: $COMPOSE_FILE"
    fi

    local profiles=()

    local include_clickhouse=true
    if [[ -n "$clickhouse_host" ]]; then
        case "$clickhouse_host" in
            localhost|127.*|clickhousedb)
                include_clickhouse=true
                ;;
            *)
                include_clickhouse=false
                ;;
        esac
    fi

    if [[ "$include_clickhouse" == true ]]; then
        profiles+=(clickhouse)
        print_status "Local ClickHouse container enabled"
    else
        print_status "Skipping local ClickHouse container; using external host: ${clickhouse_host:-remote}"
    fi

    local include_temporal=true
    if [[ -n "$temporal_host" ]]; then
        case "$temporal_host" in
            localhost|127.*|temporal)
                include_temporal=true
                ;;
            *)
                include_temporal=false
                ;;
        esac
    fi

    if [[ "$include_temporal" == true ]]; then
        profiles+=(temporal)
        print_status "Local Temporal services enabled"
    else
        print_status "Skipping local Temporal services; using external host: ${temporal_host:-remote}"
    fi

    local include_temporal_db=true
    if [[ -n "$temporal_db_host" ]]; then
        case "$temporal_db_host" in
            localhost|127.*|postgresql|temporal-postgresql)
                include_temporal_db=true
                ;;
            *)
                include_temporal_db=false
                ;;
        esac
    fi

    if [[ "$include_temporal_db" == true ]]; then
        profiles+=(temporal-db)
        print_status "Local Temporal PostgreSQL enabled"
    else
        print_status "Skipping local Temporal PostgreSQL; using external host: ${temporal_db_host:-remote}"
    fi

    if [[ ${#profiles[@]} -gt 0 ]]; then
        local profiles_joined
        profiles_joined="$(IFS=,; echo "${profiles[*]}")"
        export COMPOSE_PROFILES="$profiles_joined"
        print_status "Docker Compose profiles enabled: $COMPOSE_PROFILES"
    else
        unset COMPOSE_PROFILES
        print_status "No optional Docker Compose profiles enabled"
    fi

    print_status "Docker timeouts set to ${DOCKER_CLIENT_TIMEOUT}s (client) / ${COMPOSE_HTTP_TIMEOUT}s (compose)"
}

docker_compose_command() {
    if docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
    else
        return 1
    fi
}

pre_pull_images() {
    local compose_base="$SERVICE_DIR/.moose/docker-compose.yml"
    if [ ! -f "$compose_base" ]; then
        print_warning "Compose file not found at $compose_base; skipping pre-pull"
        return
    fi

    local compose_cmd
    if ! compose_cmd="$(docker_compose_command)"; then
        print_warning "Docker Compose CLI not available; skipping image pre-pull"
        return
    fi

    local pull_args=(pull --no-parallel)
    if [ "$compose_cmd" = "docker compose" ]; then
        pull_args+=(--progress plain)
    fi

    print_status "Pre-pulling Docker images (serial download for slow connections)..."
    if ! $compose_cmd "${pull_args[@]}"; then
        print_warning "Docker image pre-pull encountered errors. Containers will retry during startup."
    else
        print_success "Docker images pulled successfully"
    fi
}

# Render moose.config.toml from template
render_moose_config() {
    local renderer="$SERVICE_DIR/scripts/render-config.sh"

    if [ ! -x "$renderer" ]; then
        print_error "Config renderer not found or not executable: $renderer"
        exit 1
    fi

    print_status "Rendering moose.config.toml from template..."
    if "$renderer" >/dev/null; then
        print_success "moose.config.toml generated"
    else
        print_error "Failed to render moose.config.toml"
        exit 1
    fi
}

# Port configuration
DATA_WAREHOUSE_PORT=4200

# Virtual environment utility functions
check_venv_exists() {
    if [ -d "venv" ]; then
        return 0  # venv exists
    else
        return 1  # venv does not exist
    fi
}

create_venv_if_missing() {
    if ! check_venv_exists; then
        print_status "Creating Python virtual environment..."

        if python3 -m venv venv; then
            print_success "Virtual environment created successfully at ./venv"
        else
            print_error "Failed to create virtual environment"
            exit 1
        fi
    else
        print_success "Virtual environment already exists at ./venv"
    fi
}

ensure_venv_activated() {
    # First check if venv exists
    if ! check_venv_exists; then
        print_error "Virtual environment not found. Creating it now..."
        create_venv_if_missing
    fi

    # Check if we're already in the virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate

        if [ -n "$VIRTUAL_ENV" ]; then
            print_success "Virtual environment activated: $VIRTUAL_ENV"
        else
            print_error "Failed to activate virtual environment"
            exit 1
        fi
    else
        print_success "Virtual environment already active: $VIRTUAL_ENV"
    fi
}

is_port_in_use() {
    local port=$1
    if lsof -i ":$port" >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is available
    fi
}

check_environment() {
    print_status "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    else
        # Get Python version
        python_version=$(python3 --version 2>&1 | sed 's/Python //')
        major=$(echo "$python_version" | cut -d. -f1)
        minor=$(echo "$python_version" | cut -d. -f2)

        # Check if version is >= 3.12
        if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 12 ]); then
            print_error "Python version $python_version is too old (minimum: 3.12)"
            exit 1
        else
            print_success "Python version: $python_version"
        fi
    fi
}

install_dependencies() {
    print_status "Installing dependencies..."

    create_venv_if_missing
    ensure_venv_activated

    print_status "Installing data-warehouse dependencies in virtual environment..."
    pip install .
    print_success "Data warehouse dependencies installed successfully in virtual environment"

    render_moose_config

    # Check Moose CLI
    if ! command -v moose-cli &> /dev/null; then
        print_error "Moose CLI is not installed."
        exit 1
    fi

    print_status "Moose CLI path: $(which moose-cli 2>/dev/null || echo 'not found')"
    print_status "Moose CLI version: $(moose-cli --version 2>/dev/null || echo 'unknown')"
}

start_data_warehouse_service() {
    ensure_venv_activated

    render_moose_config

    # Check if port is in use
    if is_port_in_use $DATA_WAREHOUSE_PORT; then
        print_error "Port $DATA_WAREHOUSE_PORT is already in use!"
        print_status "To find what's using port $DATA_WAREHOUSE_PORT: lsof -i :$DATA_WAREHOUSE_PORT"
        exit 1
    fi

    print_status "Starting moose-cli dev on port $DATA_WAREHOUSE_PORT..."
    echo ""

    exec moose-cli dev
}

main() {
    print_status "Starting Data Warehouse service..."

    check_environment
    configure_docker_timeouts
    install_dependencies
    pre_pull_images
    start_data_warehouse_service
}

main "$@"
