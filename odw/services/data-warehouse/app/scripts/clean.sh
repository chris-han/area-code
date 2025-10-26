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

# Port configuration defaults; final values loaded from moose.config.toml when available
DEFAULT_DATA_WAREHOUSE_PORT=4200
DEFAULT_PROXY_PORT=4201
MOOSE_CONFIG_PATH="$SERVICE_DIR/moose.config.toml"
declare -a DATA_WAREHOUSE_PORTS=("$DEFAULT_DATA_WAREHOUSE_PORT" "$DEFAULT_PROXY_PORT")

extract_port_from_config() {
    local key="$1"
    local default="$2"
    local config_path="$MOOSE_CONFIG_PATH"

    if [ ! -f "$config_path" ]; then
        echo "$default"
        return
    fi

    awk -v key="$key" -v fallback="$default" '
        BEGIN { in_section=0; found=0; }
        /^\s*\[http_server_config\]\s*$/ { in_section=1; next }
        /^\s*\[.*\]\s*$/ {
            if (in_section && !found) {
                print fallback
                exit
            }
            in_section=0
            next
        }
        in_section {
            line=$0
            sub(/#.*/, "", line)
            if (match(line, "^[ \t]*" key "[ \t]*=[ \t]*([0-9]+)", m)) {
                print m[1]
                found=1
                exit
            }
        }
        END {
            if (!found) {
                print fallback
            }
        }
    ' "$config_path"
}

load_service_ports() {
    if [ ! -f "$MOOSE_CONFIG_PATH" ]; then
        print_warning "moose.config.toml not found; using default ports: ${DATA_WAREHOUSE_PORTS[*]}"
        return
    fi

    local primary_port
    primary_port=$(extract_port_from_config "port" "$DEFAULT_DATA_WAREHOUSE_PORT")
    local proxy_port
    proxy_port=$(extract_port_from_config "proxy_port" "$DEFAULT_PROXY_PORT")

    local resolved_ports=()
    local port
    for port in "$primary_port" "$proxy_port"; do
        if [ -n "$port" ]; then
            local duplicate=false
            for existing in "${resolved_ports[@]}"; do
                if [ "$existing" = "$port" ]; then
                    duplicate=true
                    break
                fi
            done

            if [ "$duplicate" = false ]; then
                resolved_ports+=("$port")
            fi
        fi
    done

    if [ ${#resolved_ports[@]} -eq 0 ]; then
        print_warning "Could not determine data warehouse ports from moose.config.toml; using defaults: ${DATA_WAREHOUSE_PORTS[*]}"
        return
    fi

    DATA_WAREHOUSE_PORTS=("${resolved_ports[@]}")
    print_status "Resolved data warehouse ports: ${DATA_WAREHOUSE_PORTS[*]}"
}

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

clean_port_usage() {
    local port=$1

    if [ -z "$port" ]; then
        return
    fi

    print_status "Checking for process using port $port..."

    local pid
    pid=$(lsof -ti ":$port" -sTCP:LISTEN 2>/dev/null | head -n 1)

    if [ -n "$pid" ]; then
        print_warning "Found process $pid using port $port"
        print_status "Attempting to terminate process $pid..."

        # Try graceful termination first
        if kill "$pid" 2>/dev/null; then
            print_status "Waiting up to 10 seconds for process $pid to terminate..."

            local attempts=0
            local max_attempts=10
            while [ $attempts -lt $max_attempts ]; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    print_success "Process $pid on port $port terminated gracefully"
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
        print_success "No processes found using port $port"
    fi
}

clean_data_warehouse_ports() {
    local port
    for port in "${DATA_WAREHOUSE_PORTS[@]}"; do
        clean_port_usage "$port"
    done
}

clean_abi_api_port() {
    local abi_port="${ABI_HTTP_PORT:-4300}"
    print_status "Checking for process using bia API port $abi_port..."

    local pid=$(lsof -ti ":$abi_port" 2>/dev/null || true)

    if [ -n "$pid" ]; then
        print_warning "Found process $pid using bia API port $abi_port"
        if kill "$pid" 2>/dev/null; then
            sleep 1
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "Process $pid still running, forcing termination..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            print_success "Cleared bia API port $abi_port"
        else
            print_warning "Could not terminate process $pid on port $abi_port"
        fi
    else
        print_success "No processes found using bia API port $abi_port"
    fi
}

main() {
    print_status "Cleaning up Data Warehouse service..."

    load_service_ports
    clean_moose_infrastructure
    clean_data_warehouse_ports
    clean_abi_api_port

    print_success "Data Warehouse service cleanup completed"
}

main "$@"
