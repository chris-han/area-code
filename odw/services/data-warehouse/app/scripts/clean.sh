#!/bin/bash

# Data Warehouse Service Cleanup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
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
        return 0  # venv exists
    else
        return 1  # venv does not exist
    fi
}

ensure_venv_activated() {
    # First check if venv exists
    if ! check_venv_exists; then
        print_warning "Virtual environment not found, skipping moose-cli clean"
        return 1
    fi

    # Check if we're already in the virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
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

load_env_file() {
    if [ -f ./.env ]; then
        print_status "Loading environment from .env..."
        set -a
        # shellcheck disable=SC1091
        source ./.env
        set +a
    else
        print_warning ".env file not found; using existing environment variables"
    fi
}

generate_override_file() {
    local override_file="./.moose/docker-compose.override.yml"
    mkdir -p "$(dirname "$override_file")"
    cat <<'EOF' > "$override_file"
# Auto-generated override: route Temporal to external Postgres
services:
  postgresql:
    profiles:
      - disabled
  temporal:
    depends_on: []
    environment:
      - DB=postgres12
      - DB_PORT=${TEMPORAL_DB_PORT:-5432}
      - POSTGRES_USER=${TEMPORAL_DB_USER:-temporal}
      - POSTGRES_PWD=${TEMPORAL_DB_PASSWORD:-temporal}
      - POSTGRES_SEEDS=${TEMPORAL_DB_HOST:-postgresql}
    restart: always
  temporal-admin-tools:
    environment:
      - TEMPORAL_ADDRESS=${TEMPORAL_ADDRESS:-temporal:${TEMPORAL_PORT:-7233}}
      - TEMPORAL_CLI_ADDRESS=${TEMPORAL_CLI_ADDRESS:-temporal:${TEMPORAL_PORT:-7233}}
  temporal-ui:
    environment:
      - TEMPORAL_ADDRESS=${TEMPORAL_ADDRESS:-temporal:${TEMPORAL_PORT:-7233}}
EOF
}

patch_temporal_compose() {
    local compose_file="./.moose/docker-compose.yml"
    if [ ! -f "$compose_file" ]; then
        print_warning "No .moose/docker-compose.yml found; skipping Temporal compose patch"
        return
    fi

    python - "$compose_file" <<'PY'
import os
import re
from pathlib import Path

compose_path = Path(__import__("sys").argv[1])
text = compose_path.read_text()

host = os.getenv("TEMPORAL_DB_HOST")
user = os.getenv("TEMPORAL_DB_USER")
password = os.getenv("TEMPORAL_DB_PASSWORD")

if host:
    safe_host = host.replace('"', '\\"')
    text = re.sub(r"POSTGRES_SEEDS=postgresql", f"POSTGRES_SEEDS=${{TEMPORAL_DB_HOST:-{safe_host}}}", text)

if user:
    safe_user = user.replace('"', '\\"')
    text = re.sub(r"POSTGRES_USER=\$\{TEMPORAL_DB_USER:-[^}]+\}", f"POSTGRES_USER=${{TEMPORAL_DB_USER:-{safe_user}}}", text)
    text = re.sub(r"POSTGRES_USER: \${TEMPORAL_DB_USER:-[^}]+}", f"POSTGRES_USER: ${{TEMPORAL_DB_USER:-{safe_user}}}", text)

if password:
    safe_password = password.replace('"', '\\"')
    text = re.sub(r"POSTGRES_PWD=\$\{TEMPORAL_DB_PASSWORD:-[^}]+\}", f"POSTGRES_PWD=${{TEMPORAL_DB_PASSWORD:-\"{safe_password}\"}}", text)
    text = re.sub(r"POSTGRES_PASSWORD: \${TEMPORAL_DB_PASSWORD:-[^}]+}", f"POSTGRES_PASSWORD: ${{TEMPORAL_DB_PASSWORD:-\"{safe_password}\"}}", text)

compose_path.write_text(text)
PY
}

clean_moose_infrastructure() {
    if ensure_venv_activated; then
        # Check if moose-cli is available
        if command -v moose-cli &> /dev/null; then
            print_status "Cleaning Moose infrastructure..."
            generate_override_file
            patch_temporal_compose
            load_env_file
            moose-cli clean
            print_success "Moose infrastructure cleaned"
        else
            print_warning "moose-cli not found, skipping infrastructure cleanup"
        fi
    else
        print_warning "Could not activate virtual environment, skipping moose-cli clean"
    fi
}

clean_data_warehouse_port() {
    print_status "Checking for process using port $DATA_WAREHOUSE_PORT..."

    local pid=$(lsof -ti :$DATA_WAREHOUSE_PORT 2>/dev/null)

    if [ -n "$pid" ]; then
        print_warning "Found process $pid using port $DATA_WAREHOUSE_PORT"
        print_status "Attempting to terminate process $pid..."

        # Try graceful termination first
        if kill "$pid" 2>/dev/null; then
            print_status "Waiting up to 10 seconds for process $pid to terminate..."

            local attempts=0
            local max_attempts=10
            while [ $attempts -lt $max_attempts ]; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    print_success "Process $pid terminated gracefully"
                    return 0
                fi
                sleep 1
                attempts=$((attempts + 1))
            done

            # Process still running after 10 seconds, force kill
            print_warning "Process $pid still running after 10 seconds, force killing..."
            kill -9 "$pid" 2>/dev/null
            sleep 1

            # Final check after force kill
            if kill -0 "$pid" 2>/dev/null; then
                print_error "Failed to kill process $pid even with force"
            else
                print_success "Process $pid force killed successfully"
            fi
        else
            print_warning "Could not send signal to process $pid (may already be dead)"
        fi
    else
        print_success "No processes found using port $DATA_WAREHOUSE_PORT"
    fi
}

clean_abi_api_port() {
    local abi_port="${ABI_HTTP_PORT:-4300}"
    print_status "Checking for process using ABI API port $abi_port..."

    local pid=$(lsof -ti ":$abi_port" 2>/dev/null || true)

    if [ -n "$pid" ]; then
        print_warning "Found process $pid using ABI API port $abi_port"
        if kill "$pid" 2>/dev/null; then
            sleep 1
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "Process $pid still running, forcing termination..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            print_success "Cleared ABI API port $abi_port"
        else
            print_warning "Could not terminate process $pid on port $abi_port"
        fi
    else
        print_success "No processes found using ABI API port $abi_port"
    fi
}

main() {
    print_status "Cleaning up Data Warehouse service..."

    clean_moose_infrastructure
    clean_data_warehouse_port
    clean_abi_api_port

    print_success "Data Warehouse service cleanup completed"
}

main "$@"
