#!/bin/bash
set -e

echo "🧹 Cleaning all virtual environments..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to clean a service venv
clean_service_venv() {
    local service_path=$1
    local service_name=$2
    
    if [ -d "$service_path/.venv" ]; then
        echo -e "${YELLOW}🗑️  Removing ${service_name} .venv...${NC}"
        rm -rf "$service_path/.venv"
        echo -e "${GREEN}  ✅ ${service_name} .venv removed${NC}"
    else
        echo -e "${YELLOW}  ℹ️  No .venv found for ${service_name}${NC}"
    fi
}

# Clean service venvs
clean_service_venv "services" "Backend Services (Shared)"
clean_service_venv "apps/dw-frontend" "DW Frontend App"

# Clean old root-level venv if it exists
if [ -d ".odw-venv" ]; then
    echo -e "${YELLOW}🗑️  Removing old root-level .odw-venv...${NC}"
    rm -rf ".odw-venv"
    echo -e "${GREEN}  ✅ Old root venv removed${NC}"
fi

echo -e "${GREEN}🎉 All virtual environments cleaned!${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "Run: ./scripts/setup-venvs.sh to recreate clean environments"