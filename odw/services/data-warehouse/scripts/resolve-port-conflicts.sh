#!/bin/bash

# ABI Port Conflict Resolution Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[PORT-CHECK]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PORT-CHECK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[PORT-CHECK]${NC} $1"
}

print_error() {
    echo -e "${RED}[PORT-CHECK]${NC} $1"
}

# ABI required ports
declare -A ABI_PORTS=(
    [4200]="Moose API"
    [18123]="ClickHouse HTTP"
    [9000]="ClickHouse Native"
    [7233]="Temporal Server"
    [8080]="Temporal UI"
    [9999]="Kafdrop UI"
    [9500]="MinIO API"
    [9501]="MinIO Console"
    [6379]="Redis"
    [5432]="PostgreSQL"
    [19092]="RedPanda"
)

check_port() {
    local port=$1
    local service=$2
    
    if lsof -i ":$port" >/dev/null 2>&1; then
        local process_info=$(lsof -i ":$port" -t | head -1 | xargs ps -p | tail -1)
        print_warning "Port $port ($service) is in use:"
        echo "  Process: $process_info"
        return 1
    else
        print_success "Port $port ($service) is available"
        return 0
    fi
}

find_alternative_port() {
    local base_port=$1
    local service=$2
    local port=$base_port
    
    while [ $port -lt $((base_port + 100)) ]; do
        if ! lsof -i ":$port" >/dev/null 2>&1; then
            print_success "Alternative port for $service: $port"
            return $port
        fi
        ((port++))
    done
    
    print_error "No alternative port found for $service"
    return 1
}

kill_process_on_port() {
    local port=$1
    local service=$2
    
    print_warning "Attempting to stop process on port $port ($service)..."
    
    local pids=$(lsof -t -i ":$port" 2>/dev/null || echo "")
    
    if [ -n "$pids" ]; then
        echo "$pids" | while read -r pid; do
            local process_name=$(ps -p "$pid" -o comm= 2>/dev/null || echo "unknown")
            print_status "Stopping process $pid ($process_name)..."
            
            # Try graceful shutdown first
            if kill "$pid" 2>/dev/null; then
                sleep 2
                # Check if process is still running
                if kill -0 "$pid" 2>/dev/null; then
                    print_warning "Process $pid still running, forcing shutdown..."
                    kill -9 "$pid" 2>/dev/null || true
                fi
                print_success "Process $pid stopped"
            else
                print_error "Failed to stop process $pid"
            fi
        done
    else
        print_status "No processes found on port $port"
    fi
}

resolve_temporal_ui_conflict() {
    print_status "Resolving Temporal UI and DataLens port conflict (both use 8080)..."
    
    # Check if port 8080 is in use
    if lsof -i ":8080" >/dev/null 2>&1; then
        print_warning "Port 8080 is in use"
        
        # Suggest using port 8081 for DataLens
        if ! lsof -i ":8081" >/dev/null 2>&1; then
            print_success "Suggested solution: Configure DataLens to use port 8081"
            echo "  Update datalens_config.base_url in moose.config.toml to 'http://localhost:8081'"
        else
            print_warning "Port 8081 is also in use, finding alternative..."
            find_alternative_port 8082 "DataLens"
        fi
    else
        print_success "Port 8080 is available for Temporal UI"
    fi
}

check_all_ports() {
    print_status "Checking ABI required ports..."
    echo ""
    
    local conflicts=0
    local available=0
    
    for port in "${!ABI_PORTS[@]}"; do
        service=${ABI_PORTS[$port]}
        if check_port "$port" "$service"; then
            ((available++))
        else
            ((conflicts++))
        fi
    done
    
    echo ""
    print_status "Port Check Summary:"
    echo "  Available: $available/${#ABI_PORTS[@]} ports"
    echo "  Conflicts: $conflicts/${#ABI_PORTS[@]} ports"
    
    if [ $conflicts -gt 0 ]; then
        echo ""
        print_warning "Port conflicts detected. Options:"
        echo "  1. Stop conflicting processes: $0 --kill-conflicts"
        echo "  2. Find alternative ports: $0 --alternatives"
        echo "  3. Manual resolution required"
        return 1
    else
        print_success "All required ports are available!"
        return 0
    fi
}

kill_all_conflicts() {
    print_warning "This will attempt to stop all processes using ABI ports"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for port in "${!ABI_PORTS[@]}"; do
            service=${ABI_PORTS[$port]}
            if lsof -i ":$port" >/dev/null 2>&1; then
                kill_process_on_port "$port" "$service"
            fi
        done
        
        echo ""
        print_status "Rechecking ports after cleanup..."
        check_all_ports
    else
        print_status "Operation cancelled"
    fi
}

show_alternatives() {
    print_status "Finding alternative ports for conflicts..."
    echo ""
    
    for port in "${!ABI_PORTS[@]}"; do
        service=${ABI_PORTS[$port]}
        if lsof -i ":$port" >/dev/null 2>&1; then
            find_alternative_port "$port" "$service"
        fi
    done
}

show_help() {
    echo "ABI Port Conflict Resolution"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --check           Check all required ports (default)"
    echo "  --kill-conflicts  Stop processes using ABI ports"
    echo "  --alternatives    Find alternative ports for conflicts"
    echo "  --resolve-ui      Resolve Temporal UI / DataLens conflict"
    echo "  --help           Show this help message"
    echo ""
    echo "Required Ports:"
    for port in $(echo "${!ABI_PORTS[@]}" | tr ' ' '\n' | sort -n); do
        printf "  %-5s %s\n" "$port" "${ABI_PORTS[$port]}"
    done
}

main() {
    local action=${1:-check}
    
    case "$action" in
        --check|check)
            check_all_ports
            ;;
        --kill-conflicts)
            kill_all_conflicts
            ;;
        --alternatives)
            show_alternatives
            ;;
        --resolve-ui)
            resolve_temporal_ui_conflict
            ;;
        --help|-h|help)
            show_help
            ;;
        *)
            print_error "Unknown option: $action"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"