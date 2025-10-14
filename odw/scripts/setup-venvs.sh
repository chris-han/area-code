#!/bin/bash
set -e

echo "🚀 Setting up service-level virtual environments for ODW..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to setup a service venv
setup_service_venv() {
    local service_path=$1
    local service_name=$2
    
    echo -e "${BLUE}📦 Setting up ${service_name}...${NC}"
    
    cd "$service_path"
    
    # Create venv if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "  Creating virtual environment..."
        uv venv  # Creates .venv by default
    fi
    
    # Activate and install dependencies
    echo "  Installing dependencies..."
    source .venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        uv pip install -r requirements.txt
    fi
    
    if [ -f "setup.py" ]; then
        uv pip install -e .
    fi
    
    echo -e "${GREEN}  ✅ ${service_name} setup complete${NC}"
    cd - > /dev/null
}

# Store original directory
ORIGINAL_DIR=$(pwd)

# Setup Backend Services (Shared venv)
echo -e "${BLUE}📦 Setting up Backend Services (Shared)...${NC}"
cd "services"

# Create shared venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "  Creating shared virtual environment..."
    uv venv  # Creates .venv by default
fi

# Activate and install dependencies
echo "  Installing dependencies..."
source .venv/bin/activate

# Install connectors package first (editable)
if [ -d "connectors" ]; then
    echo "  Installing connectors package (editable)..."
    uv pip install -e connectors
fi

# Install data-warehouse package (editable)
if [ -d "data-warehouse" ]; then
    echo "  Installing data-warehouse package (editable)..."
    cd data-warehouse
    if [ -f "requirements.txt" ]; then
        uv pip install -r requirements.txt
    fi
    if [ -f "setup.py" ]; then
        uv pip install -e .
    fi
    cd ..
fi

echo -e "${GREEN}  ✅ Backend Services (Shared) setup complete${NC}"
cd "$ORIGINAL_DIR"

# Setup DW Frontend App  
setup_service_venv "apps/dw-frontend" "DW Frontend App"

# Return to original directory
cd "$ORIGINAL_DIR"

echo -e "${GREEN}🎉 All virtual environments setup complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Open VSCode workspace: code odw/.vscode/odw.code-workspace"
echo "2. Select Python interpreter for each service folder"
echo "3. Run development: bun run odw:dev"
echo ""
echo -e "${YELLOW}🔧 Service .venv locations:${NC}"
echo "  • Backend Services: services/.venv/ (shared by data-warehouse + connectors)"
echo "  • DW Frontend:      apps/dw-frontend/.venv/"