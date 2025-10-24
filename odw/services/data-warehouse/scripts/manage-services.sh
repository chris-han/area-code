#!/bin/bash

# bia Docker Services Management Script

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

print_status() {
    echo -e "${BLUE}[bia-SERVICES]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[bia-SERVICES]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[bia-SERVICES]${NC} $1"
}

print_error() {
    echo -e "${RED}[bia-SERVICES]${NC} $1"
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

start_services() {
    print_status "Starting bia Docker services..."
    
    load_env_file
    
    # Export required environment variables
    export CLICKHOUSE_DB_NAME="${CLICKHOUSE_DB_NAME:-finops-odw}"
    export CLICKHOUSE_USER="${CLICKHOUSE_USER:-finops}"
    export CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD}"
    export TEMPORAL_DB_USER="${TEMPORAL_DB_USER:-temporal}"
    export TEMPORAL_DB_PASSWORD="${TEMPORAL_DB_PASSWORD:-temporal}"
    export TEMPORAL_DB_PORT="${TEMPORAL_DB_PORT:-5432}"
    export TEMPORAL_PORT="${TEMPORAL_PORT:-7233}"
    export TEMPORAL_UI_PORT="${TEMPORAL_UI_PORT:-8080}"
    export TEMPORAL_VERSION="${TEMPORAL_VERSION:-1.29.0}"
    export TEMPORAL_ADMINTOOLS_VERSION="${TEMPORAL_ADMINTOOLS_VERSION:-1.29}"
    export TEMPORAL_UI_VERSION="${TEMPORAL_UI_VERSION:-2.41.0}"
    export POSTGRESQL_VERSION="${POSTGRESQL_VERSION:-13}"
    
    # Start services with override
    docker compose -f .moose/docker-compose.yml -f .moose/docker-compose.override.yml up -d
    
    print_success "Services started successfully"
    print_status "Use 'scripts/check-services.sh' to verify service health"
}

stop_services() {
    print_status "Stopping bia Docker services..."
    
    docker compose -f .moose/docker-compose.yml -f .moose/docker-compose.override.yml down
    
    print_success "Services stopped successfully"
}

restart_services() {
    print_status "Restarting bia Docker services..."
    
    stop_services
    sleep 2
    start_services
}

show_logs() {
    local service=${1:-}
    
    if [ -n "$service" ]; then
        print_status "Showing logs for service: $service"
        docker compose -f .moose/docker-compose.yml -f .moose/docker-compose.override.yml logs -f "$service"
    else
        print_status "Showing logs for all services"
        docker compose -f .moose/docker-compose.yml -f .moose/docker-compose.override.yml logs -f
    fi
}

show_status() {
    print_status "Service Status:"
    docker compose -f .moose/docker-compose.yml -f .moose/docker-compose.override.yml ps
}

cleanup_services() {
    print_warning "This will remove all containers, networks, and volumes"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up bia Docker services..."
        docker compose -f .moose/docker-compose.yml -f .moose/docker-compose.override.yml down -v --remove-orphans
        print_success "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

show_help() {
    echo "bia Docker Services Management"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  start     Start all services"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  status    Show service status"
    echo "  logs      Show service logs [service_name]"
    echo "  cleanup   Remove all containers and volumes"
    echo "  health    Check service health"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs temporal"
    echo "  $0 status"
}

main() {
    local command=${1:-help}
    
    case "$command" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        cleanup)
            cleanup_services
            ;;
        health)
            ./scripts/check-services.sh
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"