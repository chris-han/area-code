#!/bin/bash -e

########################################################
# ODW Development Data Seeding Script
########################################################

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the ODW root (parent of scripts directory)
ODW_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_ENV_DIR="$ODW_ROOT/.odw-venv"
PYTHON_BIN="$PYTHON_ENV_DIR/bin/python"

# Configuration
BUCKET_NAME="unstructured-data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[ODW-SEED]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[ODW-SEED]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[ODW-SEED]${NC} $1"
}

print_error() {
    echo -e "${RED}[ODW-SEED]${NC} $1"
}

render_moose_config() {
    local renderer="$ODW_ROOT/services/data-warehouse/scripts/render-config.sh"

    if [[ ! -x "$renderer" ]]; then
        print_error "Config renderer not found: $renderer"
        exit 1
    fi

    print_status "Rendering moose.config.toml from template..."

    if ! "$renderer" >/dev/null; then
        print_error "Failed to render moose.config.toml"
        exit 1
    fi
}

# Ensure the MinIO client is available on the current platform
ensure_minio_client() {
    if command -v mc >/dev/null 2>&1; then
        print_success "MinIO client already installed"
        return
    fi

    case "$(uname -s)" in
        Darwin)
            if command -v brew >/dev/null 2>&1; then
                print_status "Installing MinIO client via Homebrew..."
                brew install minio/stable/mc
            else
                print_error "Homebrew is not installed. Please install MinIO client manually."
                exit 1
            fi
            ;;
        Linux)
            print_status "Installing MinIO client for Linux..."

            arch="$(uname -m)"
            case "$arch" in
                x86_64|amd64)
                    download_arch="linux-amd64"
                    ;;
                arm64|aarch64)
                    download_arch="linux-arm64"
                    ;;
                *)
                    print_error "Unsupported CPU architecture: $arch"
                    exit 1
                    ;;
            esac

            if ! command -v curl >/dev/null 2>&1; then
                print_error "curl is required to download the MinIO client. Please install curl and retry."
                exit 1
            fi

            tmp_file="$(mktemp)"
            curl -fsSL "https://dl.min.io/client/mc/release/${download_arch}/mc" -o "$tmp_file"
            chmod +x "$tmp_file"

            install_dir="$HOME/.local/bin"
            mkdir -p "$install_dir"
            install -m 755 "$tmp_file" "$install_dir/mc"
            rm -f "$tmp_file"

            if [[ ":$PATH:" != *":$install_dir:"* ]]; then
                print_warning "MinIO client installed to $install_dir; ensure this directory is in your PATH."
            fi
            ;;
        *)
            print_error "Unsupported operating system: $(uname -s)"
            exit 1
            ;;
    esac

    if ! command -v mc >/dev/null 2>&1; then
        print_error "MinIO client installation failed. Please install it manually and rerun the script."
        exit 1
    fi
}

ensure_python_deps() {
    local requirements="$ODW_ROOT/scripts/requirements.txt"

    if [[ ! -f "$requirements" ]]; then
        print_error "Python requirements file not found: $requirements"
        exit 1
    fi

    if ! command -v uv >/dev/null 2>&1; then
        print_error "uv CLI is required. Install it from https://github.com/astral-sh/uv and retry."
        exit 1
    fi

    if [[ ! -x "$PYTHON_BIN" ]]; then
        print_status "Creating Python virtual environment..."
        if ! uv venv "$PYTHON_ENV_DIR"; then
            print_error "Failed to create Python virtual environment."
            exit 1
        fi
    fi

    print_status "Installing Python dependencies with uv..."
    if ! uv pip install --python "$PYTHON_BIN" --quiet --requirement "$requirements"; then
        print_error "Failed to install Python dependencies via uv."
        exit 1
    fi
}

# Load S3 configuration from moose.config.toml using the Python helper
load_s3_settings() {
    "$PYTHON_BIN" - "$ODW_ROOT" <<'PY'
import importlib.util
import shlex
import sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.stderr.write("Missing ODW root path\n")
    sys.exit(1)

odw_root = Path(sys.argv[1]).resolve()
config_path = odw_root / "services" / "data-warehouse" / "moose.config.toml"
seed_script = odw_root / "scripts" / "seed-data.py"
requirements_path = odw_root / "scripts" / "requirements.txt"

try:
    spec = importlib.util.spec_from_file_location("odw_seed_data", str(seed_script))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = module.load_moose_config(str(config_path)) or {}
except ModuleNotFoundError as exc:
    missing = getattr(exc, 'name', str(exc))
    sys.stderr.write(
        f"Missing Python dependency '{missing}'.\n"
        f"Run 'uv pip install --python {sys.executable} -r {requirements_path}' and rerun.\n"
    )
    sys.exit(1)
except FileNotFoundError:
    sys.stderr.write(f"Unable to locate configuration at {config_path}\n")
    sys.exit(1)
except Exception as exc:
    sys.stderr.write(f"Failed to load S3 configuration: {exc}\n")
    sys.exit(1)

def emit(name, value):
    value = "" if value is None else str(value)
    print(f"{name}={shlex.quote(value)}")

emit("S3_ENDPOINT_URL", config.get("endpoint_url", ""))
emit("S3_BUCKET_NAME", config.get("bucket_name", ""))
emit("S3_ACCESS_KEY_ID", config.get("access_key_id", ""))
emit("S3_SECRET_ACCESS_KEY", config.get("secret_access_key", ""))
PY
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "This script seeds data for the Operation Data Warehouse."
    echo "It sets up MinIO buckets and populates them with unstructured data."
    echo ""
    echo "Options:"
    echo "  --help              Show this help message"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

main() {
    print_status "Starting ODW data seeding process..."

    render_moose_config

    ensure_python_deps

    if ! S3_SETTINGS_OUTPUT="$(load_s3_settings)"; then
        print_error "Failed to load S3 configuration."
        exit 1
    fi

    eval "$S3_SETTINGS_OUTPUT"

    if [[ -n "$S3_BUCKET_NAME" ]]; then
        BUCKET_NAME="$S3_BUCKET_NAME"
    fi

    if [[ -n "$S3_ENDPOINT_URL" ]]; then
        print_status "Detected custom S3 endpoint: $S3_ENDPOINT_URL"
        ensure_minio_client

        if [[ -z "$S3_ACCESS_KEY_ID" || -z "$S3_SECRET_ACCESS_KEY" ]]; then
            print_error "Access key or secret key missing for S3 endpoint."
            exit 1
        fi

        print_status "Setting up MinIO connection..."
        if ! mc alias set localminio "$S3_ENDPOINT_URL" "$S3_ACCESS_KEY_ID" "$S3_SECRET_ACCESS_KEY"; then
            print_error "Failed to configure MinIO alias."
            exit 1
        fi

        print_status "Creating $BUCKET_NAME bucket..."
        if mc mb localminio/$BUCKET_NAME 2>/dev/null; then
            print_success "Bucket created successfully"
        else
            print_warning "Bucket already exists, skipping creation"
        fi

        print_status "Setting bucket permissions..."
        mc anonymous set public localminio/$BUCKET_NAME || true
        mc anonymous set download localminio/$BUCKET_NAME || true
    else
        print_status "Using AWS S3; skipping MinIO client setup"
    fi

    # Run the seed data script
    print_status "Running seed data script..."
    if [ ! -f "$ODW_ROOT/scripts/seed-data.py" ]; then
        print_error "Seed data script not found: $ODW_ROOT/scripts/seed-data.py"
        exit 1
    fi

    cd "$ODW_ROOT/scripts"
    "$PYTHON_BIN" ./seed-data.py

    print_success "ODW data seeding completed successfully!"
}

main "$@"
