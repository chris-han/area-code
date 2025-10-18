#!/bin/bash

# Connectors Service Development Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SERVICE_DIR"

# Keep uv caches inside the repo so sandboxed environments can install packages.
UV_CACHE_ROOT="$SERVICE_DIR/.uv-cache"
mkdir -p "$UV_CACHE_ROOT" "$UV_CACHE_ROOT/http" "$UV_CACHE_ROOT/persistent"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$UV_CACHE_ROOT}"
export UV_HTTP_CACHE_DIR="${UV_HTTP_CACHE_DIR:-$UV_CACHE_ROOT/http}"
export UV_PERSISTENT_CACHE_DIR="${UV_PERSISTENT_CACHE_DIR:-$UV_CACHE_ROOT/persistent}"
export UV_LINK_MODE="${UV_LINK_MODE:-copy}"
TMP_WORK_DIR="$SERVICE_DIR/.tmp"
mkdir -p "$TMP_WORK_DIR"
export TMPDIR="${TMPDIR:-$TMP_WORK_DIR}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[CONNECTORS]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[CONNECTORS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[CONNECTORS]${NC} $1"
}

print_error() {
    echo -e "${RED}[CONNECTORS]${NC} $1"
}

# Virtual environment utility functions
DEFAULT_VENV_PATH="/home/chris/repo/area-code/odw/services/data-warehouse/.venv"

check_venv_exists() {
    if [ -d ".venv" ]; then
        return 0  # local .venv exists
    else
        return 1  # no local venv exists
    fi
}

check_default_venv_exists() {
    if [ -d "$DEFAULT_VENV_PATH" ]; then
        return 0  # default .venv exists
    else
        return 1  # no default venv exists
    fi
}

create_venv_if_missing() {
    if ! check_venv_exists; then
        if check_default_venv_exists; then
            print_status "No local .venv found, using default data-warehouse .venv at $DEFAULT_VENV_PATH"
            return 0
        else
            print_status "Creating local virtual environment with uv..."
            
            if uv venv .venv; then
                print_success "Virtual environment created successfully at ./.venv"
            else
                print_error "Failed to create virtual environment"
                exit 1
            fi
        fi
    else
        print_success "Virtual environment already exists at ./.venv"
    fi
}

ensure_venv_activated() {
    # Determine which venv to use
    local venv_path
    if check_venv_exists; then
        venv_path="$(pwd)/.venv"
        print_status "Using local virtual environment"
    elif check_default_venv_exists; then
        venv_path="$DEFAULT_VENV_PATH"
        print_status "Using default data-warehouse virtual environment"
    else
        print_error "No virtual environment available"
        exit 1
    fi
    
    # Check if we're already in the correct virtual environment
    if [ -z "$VIRTUAL_ENV" ] || [[ "$VIRTUAL_ENV" != "$venv_path" ]]; then
        print_status "Activating virtual environment at $venv_path..."
        source "$venv_path/bin/activate"
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

    print_status "Installing connectors dependencies in virtual environment..."
    if ! uv pip install -e .; then
        print_warning "uv pip install failed; falling back to legacy setup.py install"
        if ! TMPDIR="${TMPDIR:-$SERVICE_DIR/.tmp}" python setup.py install; then
            print_error "Fallback setup.py install failed"
            exit 1
        fi
    fi
    
    print_success "Connectors dependencies installed successfully in virtual environment"
}

main() {
    print_status "Setting up Connectors service..."

    check_environment
    install_dependencies
    
    print_success "Connectors service setup complete!"
    print_status "Virtual environment: $VIRTUAL_ENV"
    print_status "To activate manually: source .venv/bin/activate"
}

main "$@"
