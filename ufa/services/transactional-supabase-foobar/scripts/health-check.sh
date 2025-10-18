#!/bin/bash

# Health Check Script for Transactional Service
# Checks if all required services are running and ready

check_postgres() {
    echo "Checking PostgreSQL connection..."
    if command -v pg_isready > /dev/null 2>&1; then
        if pg_isready -h localhost -p 54322 > /dev/null 2>&1; then
            echo "✓ PostgreSQL is ready"
            return 0
        fi
    else
        # Fallback: try to connect with psql
        if PGPASSWORD=postgres psql -h localhost -p 54322 -U postgres -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
            echo "✓ PostgreSQL is ready"
            return 0
        fi
    fi
    echo "✗ PostgreSQL is not ready"
    return 1
}

check_supabase_api() {
    echo "Checking Supabase API..."
    if curl -s http://localhost:54321/rest/v1/ > /dev/null 2>&1; then
        echo "✓ Supabase API is ready"
        return 0
    else
        echo "✗ Supabase API is not ready"
        return 1
    fi
}

check_supabase_studio() {
    echo "Checking Supabase Studio..."
    if curl -s http://localhost:54323 > /dev/null 2>&1; then
        echo "✓ Supabase Studio is ready"
        return 0
    else
        echo "✗ Supabase Studio is not ready"
        return 1
    fi
}

main() {
    echo "=== Supabase Health Check ==="
    
    local all_healthy=true
    
    if ! check_postgres; then
        all_healthy=false
    fi
    
    if ! check_supabase_api; then
        all_healthy=false
    fi
    
    if ! check_supabase_studio; then
        all_healthy=false
    fi
    
    echo ""
    if [ "$all_healthy" = true ]; then
        echo "✓ All services are healthy and ready!"
        exit 0
    else
        echo "✗ Some services are not ready. Please check the logs."
        exit 1
    fi
}

main "$@"