#!/bin/bash

# ABI Docker Services Health Check Script

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
    echo -e "${BLUE}[ABI-HEALTH]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[ABI-HEALTH]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[ABI-HEALTH]${NC} $1"
}

print_error() {
    echo -e "${RED}[ABI-HEALTH]${NC} $1"
}

# Service configuration
declare -A SERVICES=(
    ["clickhousedb"]="ClickHouse Database:localhost:18123:/ping"
    ["postgresql"]="PostgreSQL:localhost:5432"
    ["redis"]="Redis:localhost:6379"
    ["redpanda"]="RedPanda:localhost:19092"
    ["temporal"]="Temporal Server:localhost:7233"
    ["temporal-ui"]="Temporal UI:localhost:8080"
    ["kafdrop"]="Kafdrop UI:localhost:9999"
    ["minio"]="MinIO:localhost:9500:/minio/health/live"
)

check_service_health() {
    local service_name=$1
    local service_info=${SERVICES[$service_name]}
    local display_name=$(echo "$service_info" | cut -d: -f1)
    local host=$(echo "$service_info" | cut -d: -f2)
    local port=$(echo "$service_info" | cut -d: -f3)
    local health_path=$(echo "$service_info" | cut -d: -f4)
    
    print_status "Checking $display_name..."
    
    # Check if port is open
    if ! nc -z ${host#localhost:} $port 2>/dev/null; then
        print_error "$display_name is not responding on port $port"
        return 1
    fi
    
    # If there's a health path, check HTTP endpoint
    if [ -n "$health_path" ] && [ "$health_path" != "$port" ]; then
        if curl -f -s "http://$host:$port$health_path" >/dev/null 2>&1; then
            print_success "$display_name is healthy"
            return 0
        else
            print_warning "$display_name port is open but health check failed"
            return 1
        fi
    else
        print_success "$display_name is responding on port $port"
        return 0
    fi
}

check_docker_compose() {
    print_status "Checking Docker Compose services..."
    
    if [ ! -f ".moose/docker-compose.yml" ]; then
        print_error "Docker Compose file not found"
        return 1
    fi
    
    # Check if services are running
    local running_services=$(docker compose -f .moose/docker-compose.yml -f .moose/docker-compose.override.yml ps --services --filter "status=running" 2>/dev/null || echo "")
    
    if [ -z "$running_services" ]; then
        print_warning "No Docker Compose services are currently running"
        print_status "To start services: bun run abi:dev"
        return 1
    fi
    
    print_success "Docker Compose services are running:"
    echo "$running_services" | while read -r service; do
        if [ -n "$service" ]; then
            echo "  - $service"
        fi
    done
    
    return 0
}

check_service_urls() {
    print_status "Service URLs:"
    echo "=================================="
    echo "🔧 Management Interfaces:"
    echo "  • Temporal UI:     http://localhost:8080"
    echo "  • Kafdrop UI:      http://localhost:9999"
    echo "  • MinIO Console:   http://localhost:9501"
    echo ""
    echo "🔌 API Endpoints:"
    echo "  • Moose API:       http://localhost:4200"
    echo "  • ClickHouse HTTP: http://localhost:18123"
    echo "  • MinIO API:       http://localhost:9500"
    echo ""
    echo "🔗 Direct Connections:"
    echo "  • ClickHouse Native: localhost:9000"
    echo "  • PostgreSQL:        localhost:5432"
    echo "  • Redis:             localhost:6379"
    echo "  • RedPanda:          localhost:19092"
    echo "  • Temporal gRPC:     localhost:7233"
    echo "=================================="
}

main() {
    print_status "Azure Billing Intelligence - Service Health Check"
    echo ""
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running"
        exit 1
    fi
    
    # Check Docker Compose services
    check_docker_compose
    echo ""
    
    # Check individual service health
    local failed_services=0
    local total_services=${#SERVICES[@]}
    
    for service in "${!SERVICES[@]}"; do
        if ! check_service_health "$service"; then
            ((failed_services++))
        fi
    done
    
    echo ""
    
    # Summary
    local healthy_services=$((total_services - failed_services))
    print_status "Health Check Summary:"
    echo "  Healthy: $healthy_services/$total_services services"
    
    if [ $failed_services -eq 0 ]; then
        print_success "All services are healthy!"
    else
        print_warning "$failed_services service(s) have issues"
    fi
    
    echo ""
    check_service_urls
    
    return $failed_services
}

# Handle command line arguments
case "${1:-}" in
    --urls)
        check_service_urls
        exit 0
        ;;
    --docker)
        check_docker_compose
        exit $?
        ;;
    --help|-h)
        echo "Usage: $0 [--urls|--docker|--help]"
        echo ""
        echo "Options:"
        echo "  --urls    Show service URLs only"
        echo "  --docker  Check Docker Compose services only"
        echo "  --help    Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac