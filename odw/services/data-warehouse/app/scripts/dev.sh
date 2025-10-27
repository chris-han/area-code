#!/bin/bash

# Data Warehouse Service Development Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$SERVICE_DIR"

UV_CACHE_DIR="$SERVICE_DIR/.uv-cache"
export UV_CACHE_DIR
mkdir -p "$UV_CACHE_DIR"

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

create_venv_if_missing() {
    if ! check_venv_exists; then
        print_status "Creating Python virtual environment..."

        if uv venv .venv; then
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
        source .venv/bin/activate

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

install_connectors_package() {
    local connectors_path="../connectors"
    if [ ! -d "$connectors_path" ]; then
        print_warning "Connectors package not found at $connectors_path. Skipping configuration."
        return
    fi

    print_status "Configuring local connectors package..."
    # Prepend the package root so Python can resolve the connectors package directly from the source tree.
    case ":$PYTHONPATH:" in
        *":$connectors_path:"*) ;;
        *) export PYTHONPATH="$connectors_path${PYTHONPATH:+:$PYTHONPATH}" ;;
    esac
    print_success "Connectors package available from $connectors_path"
}

configure_focus_billing_shim() {
    local repo_root
    repo_root="$(cd "$SERVICE_DIR/../../.." && pwd)"

    case ":$PYTHONPATH:" in
        *":$SERVICE_DIR:"*) ;;
        *) export PYTHONPATH="$SERVICE_DIR${PYTHONPATH:+:$PYTHONPATH}" ;;
    esac

    case ":$PYTHONPATH:" in
        *":$repo_root:"*) ;;
        *) export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}" ;;
    esac

    print_success "Focus billing shim configured (PYTHONPATH includes $SERVICE_DIR and $repo_root)"
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

    install_connectors_package
    configure_focus_billing_shim

    print_status "Installing data-warehouse dependencies in virtual environment..."
    uv pip install . --offline 2>/dev/null || uv pip install .
    print_success "Data warehouse dependencies installed successfully in virtual environment"

    # Check Moose CLI
    if ! command -v moose-cli &> /dev/null; then
        print_error "Moose CLI is not installed."
        exit 1
    fi

    print_status "Moose CLI path: $(which moose-cli 2>/dev/null || echo 'not found')"
    print_status "Moose CLI version: $(moose-cli --version 2>/dev/null || echo 'unknown')"
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

# Temporal/PostgreSQL defaults to the local dockerised instance unless overridden
host = os.getenv("TEMPORAL_DB_HOST") or "postgresql"
user = os.getenv("TEMPORAL_DB_USER") or "temporal"
password = os.getenv("TEMPORAL_DB_PASSWORD") or "temporal"

if host:
    safe_host = host.replace('"', '\\"')
    text = re.sub(r"POSTGRES_SEEDS=postgresql", f"POSTGRES_SEEDS={safe_host}", text)

if user:
    safe_user = user.replace('"', '\\"')
    # Replace both TEMPORAL_DB_USER and legacy MOOSE_TEMPORAL_DB_USER patterns
    text = re.sub(r"POSTGRES_USER=\$\{TEMPORAL_DB_USER:-[^}]+\}", f"POSTGRES_USER={safe_user}", text)
    text = re.sub(r"POSTGRES_USER: \$\{TEMPORAL_DB_USER:-[^}]+\}", f"POSTGRES_USER: {safe_user}", text)
    text = re.sub(r"POSTGRES_USER=\$\{MOOSE_TEMPORAL_DB_USER:-[^}]+\}", f"POSTGRES_USER={safe_user}", text)
    text = re.sub(r"POSTGRES_USER: \$\{MOOSE_TEMPORAL_DB_USER:-[^}]+\}", f"POSTGRES_USER: {safe_user}", text)

if password:
    safe_password = password.replace('"', '\\"').replace("'", "\\'")
    # Replace both TEMPORAL_DB_PASSWORD and legacy MOOSE_TEMPORAL_DB_PASSWORD patterns
    text = re.sub(r"POSTGRES_PWD=\$\{TEMPORAL_DB_PASSWORD:-[^}]+\}", f"POSTGRES_PWD={safe_password}", text)
    text = re.sub(r"POSTGRES_PASSWORD: \$\{TEMPORAL_DB_PASSWORD:-[^}]+\}", f"POSTGRES_PASSWORD: {safe_password}", text)
    text = re.sub(r"POSTGRES_PWD=\$\{MOOSE_TEMPORAL_DB_PASSWORD:-[^}]+\}", f"POSTGRES_PWD={safe_password}", text)
    text = re.sub(r"POSTGRES_PASSWORD: \$\{MOOSE_TEMPORAL_DB_PASSWORD:-[^}]+\}", f"POSTGRES_PASSWORD: {safe_password}", text)

compose_path.write_text(text)
PY
}

generate_override_file() {
    local override_file="./.moose/docker-compose.override.yml"
    mkdir -p "$(dirname "$override_file")"

    cat > "$override_file" <<'EOF'
# Auto-generated overrides for local development.
services:
  postgresql:
    # Use local PostgreSQL for Temporal since Azure PostgreSQL doesn't support btree_gin extension
    image: postgres:13
    environment:
      - POSTGRES_DB=temporal
      - POSTGRES_USER=temporal
      - POSTGRES_PASSWORD=temporal
    volumes:
      - postgresql-data:/var/lib/postgresql/data
    networks:
      - temporal-network
    ports:
      - "${TEMPORAL_DB_PORT:-5432}:5432"
  temporal:
    environment:
      - DB=postgres12
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgresql
    restart: always
    depends_on:
      - postgresql
  temporal-admin-tools:
    environment:
      - TEMPORAL_ADDRESS=${TEMPORAL_ADDRESS:-temporal:${TEMPORAL_PORT:-7233}}
      - TEMPORAL_CLI_ADDRESS=${TEMPORAL_CLI_ADDRESS:-temporal:${TEMPORAL_PORT:-7233}}
  temporal-ui:
    environment:
      - TEMPORAL_ADDRESS=${TEMPORAL_ADDRESS:-temporal:${TEMPORAL_PORT:-7233}}
  clickhouse-server:
    environment:
      CLICKHOUSE_DB: "${CLICKHOUSE_DB_NAME}"
      CLICKHOUSE_USER: "${CLICKHOUSE_USER}"
      CLICKHOUSE_PASSWORD: "${CLICKHOUSE_PASSWORD}"
    command:
      - sh
      - -c
      - |
        mkdir -p /etc/clickhouse-server/config.d
        cat > /etc/clickhouse-server/config.d/keeper.xml <<'EOF_KEEPER'
        <clickhouse>
          <zookeeper>
            <node>
              <host>clickhouse-keeper</host>
              <port>9181</port>
            </node>
          </zookeeper>
          <distributed_ddl>
            <path>/clickhouse/task_queue/ddl</path>
          </distributed_ddl>
          <macros>
            <shard>01</shard>
            <replica>replica_1</replica>
            <database>local</database>
          </macros>
          <!-- Macros are used for ReplicatedMergeTree default paths -->
          <!-- Default path: /clickhouse/tables/{uuid}/{shard} works with Atomic database (default) -->
        </clickhouse>
        EOF_KEEPER

        mkdir -p /etc/clickhouse-server/users.d
        cat > /etc/clickhouse-server/users.d/default-user.xml <<EOF_USER
        <clickhouse>
          <!-- Docs: <https://clickhouse.com/docs/operations/settings/settings_users/> -->
          <users>
            <!-- Remove default user -->
            <default remove="remove">
            </default>

            <${CLICKHOUSE_USER}>
              <profile>default</profile>
              <networks>
                <ip>::/0</ip>
              </networks>
              <password><![CDATA[${CLICKHOUSE_PASSWORD}]]></password>
              <quota>default</quota>
              <access_management>1</access_management>
            </${CLICKHOUSE_USER}>
          </users>
        </clickhouse>
        EOF_USER

        exec /entrypoint.sh
EOF
}

start_data_warehouse_service() {
    ensure_venv_activated

    # Check if port is in use
    if is_port_in_use $DATA_WAREHOUSE_PORT; then
        print_error "Port $DATA_WAREHOUSE_PORT is already in use!"
        print_status "To find what's using port $DATA_WAREHOUSE_PORT: lsof -i :$DATA_WAREHOUSE_PORT"
        exit 1
    fi

    print_status "Starting moose-cli dev on port $DATA_WAREHOUSE_PORT..."
    echo ""

    load_env_file

    # Ensure Docker Compose picks up ClickHouse credentials
    if [ -n "$CLICKHOUSE_DB_NAME" ]; then
        export DB_NAME="$CLICKHOUSE_DB_NAME"
    fi

    # Determine Temporal/PostgreSQL connection details (defaults to local Docker instance)
    local temporal_db_host="${TEMPORAL_DB_HOST:-postgresql}"
    local temporal_db_user="${TEMPORAL_DB_USER:-temporal}"
    local temporal_db_password="${TEMPORAL_DB_PASSWORD:-temporal}"
    local temporal_db_port="${TEMPORAL_DB_PORT:-5432}"

    export TEMPORAL_DB_HOST="$temporal_db_host"
    export TEMPORAL_DB_USER="$temporal_db_user"
    export TEMPORAL_DB_PASSWORD="$temporal_db_password"
    export TEMPORAL_DB_PORT="$temporal_db_port"

    # Export Temporal version variables from moose.config.toml
    export TEMPORAL_VERSION="1.29.0"
    export TEMPORAL_ADMINTOOLS_VERSION="1.29"
    export TEMPORAL_UI_VERSION="2.41.0"

    print_status "Temporal/PostgreSQL: $TEMPORAL_DB_USER@$TEMPORAL_DB_HOST:$TEMPORAL_DB_PORT"

    generate_override_file
    patch_temporal_compose

    moose-cli dev
}

main() {
    print_status "Starting Data Warehouse service..."

    check_environment
    install_dependencies
    start_data_warehouse_service
}

main "$@"
