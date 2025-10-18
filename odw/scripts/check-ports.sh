#!/bin/bash

# ODW Port Status Checker
# Checks if all ODW service ports are free or in use

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ODW Port Status Check ===${NC}"
echo

# Define ODW service ports
declare -A ODW_PORTS=(
    [4200]="Moose API"
    [8501]="Streamlit Frontend"
    [9999]="Kafdrop UI"
    [9500]="MinIO API"
    [9501]="MinIO Console"
)

# Additional infrastructure ports
declare -A INFRA_PORTS=(
    [18123]="ClickHouse HTTP"
    [9000]="ClickHouse Native"
    [19092]="Redpanda"
    [17233]="Temporal Server"
    [7233]="Temporal Internal"
    [8081]="Temporal UI"
    [8080]="Temporal UI Internal"
    [5432]="PostgreSQL (Temporal)"
    [6379]="Redis"
)

check_port() {
    local port=$1
    local service=$2
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo -e "Port ${YELLOW}$port${NC} (${service}): ${RED}IN USE${NC} (PIDs: $pids)"
        return 1
    else
        echo -e "Port ${YELLOW}$port${NC} (${service}): ${GREEN}FREE${NC}"
        return 0
    fi
}

echo -e "${BLUE}Main ODW Services:${NC}"
all_free=true
for port in "${!ODW_PORTS[@]}"; do
    if ! check_port "$port" "${ODW_PORTS[$port]}"; then
        all_free=false
    fi
done

echo
echo -e "${BLUE}Infrastructure Services:${NC}"
for port in "${!INFRA_PORTS[@]}"; do
    check_port "$port" "${INFRA_PORTS[$port]}" >/dev/null || true
done

echo
if [ "$all_free" = true ]; then
    echo -e "${GREEN}✅ All main ODW service ports are free!${NC}"
    echo -e "Ready to run: ${YELLOW}bun run odw:dev${NC}"
else
    echo -e "${RED}❌ Some ODW service ports are in use!${NC}"
    echo -e "Run cleanup first: ${YELLOW}bun run odw:dev:clean${NC}"
fi