#!/bin/bash

# ABI Development Environment Setup Script

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
    echo -e "${BLUE}[ABI-SETUP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[ABI-SETUP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[ABI-SETUP]${NC} $1"
}

print_error() {
    echo -e "${RED}[ABI-SETUP]${NC} $1"
}

check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | sed 's/Python //')
    major=$(echo "$python_version" | cut -d. -f1)
    minor=$(echo "$python_version" | cut -d. -f2)
    
    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 12 ]); then
        print_error "Python version $python_version is too old (minimum: 3.12)"
        exit 1
    fi
    
    print_success "Python version: $python_version"
    
    # Check UV
    if ! command -v uv &> /dev/null; then
        print_error "UV package manager not found"
        print_status "Install UV: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    
    print_success "UV package manager: $(uv --version)"
    
    # Check Bun
    if ! command -v bun &> /dev/null; then
        print_error "Bun not found"
        print_status "Install Bun: https://bun.sh/docs/installation"
        exit 1
    fi
    
    print_success "Bun version: $(bun --version)"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose not found"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

setup_python_environment() {
    print_status "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        print_status "Creating Python virtual environment..."
        uv venv .venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    uv sync
    print_success "Python dependencies installed"
    
    # Install development dependencies
    print_status "Installing development dependencies..."
    uv sync --dev
    print_success "Development dependencies installed"
}

setup_environment_file() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            print_status "Copying env.example to .env..."
            cp env.example .env
            print_warning "Please edit .env file with your actual credentials"
        else
            print_status "Creating basic .env file..."
            cat > .env << 'EOF'
# Azure EA API Configuration
AZURE_ENROLLMENT_NUMBER=
AZURE_API_KEY=

# ClickHouse Connection (External PaaS)
CLICKHOUSE_DB_NAME=finops-odw
CLICKHOUSE_USER=finops
CLICKHOUSE_PASSWORD=
CLICKHOUSE_HOST=ck.mightytech.cn
CLICKHOUSE_USE_SSL=true
CLICKHOUSE_HOST_PORT=8443
CLICKHOUSE_NATIVE_PORT=9000

# Temporal/PostgreSQL Connection (External PaaS)
TEMPORAL_DB_USER=maradmin
TEMPORAL_DB_PASSWORD=
TEMPORAL_DB_HOST=marspbi.postgres.database.chinacloudapi.cn
TEMPORAL_DB_PORT=5432
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233
TEMPORAL_UI_PORT=8080

# LLM Configuration
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-20250514
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000
LLM_STRICT_FIELD_VALIDATION=true
LLM_ENABLE_BATCH_PROCESSING=true
EOF
            print_warning "Created .env file - please add your credentials"
        fi
    else
        print_success ".env file already exists"
    fi
}

validate_configuration() {
    print_status "Validating configuration..."
    
    # Run the validation script
    if [ -f "scripts/validate-config.py" ]; then
        python3 scripts/validate-config.py
    else
        print_warning "Configuration validation script not found"
    fi
}

setup_git_hooks() {
    print_status "Setting up Git hooks..."
    
    # Create pre-commit hook for code formatting
    if [ -d ".git" ]; then
        mkdir -p .git/hooks
        
        cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for ABI development

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run code formatting
echo "Running code formatting..."
black app/ plugins/ --check --diff
if [ $? -ne 0 ]; then
    echo "Code formatting issues found. Run: black app/ plugins/"
    exit 1
fi

# Run linting
echo "Running linting..."
ruff check app/ plugins/
if [ $? -ne 0 ]; then
    echo "Linting issues found. Fix them before committing."
    exit 1
fi

echo "Pre-commit checks passed!"
EOF
        
        chmod +x .git/hooks/pre-commit
        print_success "Git pre-commit hook installed"
    else
        print_warning "Not in a Git repository - skipping Git hooks"
    fi
}

print_next_steps() {
    print_success "ABI development environment setup complete!"
    echo ""
    print_status "Next steps:"
    echo "1. Edit .env file with your actual credentials"
    echo "2. Run configuration validation: python3 scripts/validate-config.py"
    echo "3. Start development services: bun run abi:dev"
    echo "4. Access services:"
    echo "   - Moose API: http://localhost:4200"
    echo "   - Temporal UI: http://localhost:8080"
    echo "   - Kafdrop UI: http://localhost:9999"
    echo "   - MinIO Console: http://localhost:9501"
    echo ""
    print_status "For more information, see ABI_README.md"
}

main() {
    print_status "Setting up Azure Billing Intelligence development environment..."
    echo ""
    
    check_prerequisites
    setup_python_environment
    setup_environment_file
    setup_git_hooks
    validate_configuration
    
    echo ""
    print_next_steps
}

main "$@"