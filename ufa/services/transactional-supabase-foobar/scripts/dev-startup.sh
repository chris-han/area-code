#!/bin/bash

# Dev Startup Script for Transactional Base
# Checks and starts dependencies, runs migrations, starts server

check_supabase_status() {
    if curl -s http://localhost:54321/rest/v1/ > /dev/null 2>&1; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

check_postgres_ready() {
    # Try pg_isready first, fallback to psql connection test
    if command -v pg_isready > /dev/null 2>&1; then
        pg_isready -h localhost -p 54322 > /dev/null 2>&1
    else
        # Fallback: try to connect with psql
        PGPASSWORD=postgres psql -h localhost -p 54322 -U postgres -d postgres -c "SELECT 1;" > /dev/null 2>&1
    fi
}

start_supabase() {
    echo "Supabase is not started"
    echo "Starting Supabase services..."
    
    if ! bun run db:start; then
        echo "Failed to start Supabase services"
        exit 1
    fi
    
    # Wait for PostgreSQL to be ready to accept connections
    echo "Waiting for PostgreSQL to be ready..."
    for i in {1..60}; do
        # Test actual database connection instead of just status
        if check_postgres_ready; then
            echo "PostgreSQL is ready to accept connections"
            break
        fi
        if [ $i -eq 60 ]; then
            echo "Timeout waiting for PostgreSQL to be ready"
            echo "PostgreSQL may still be starting up. Try running the command again in a few seconds."
            exit 1
        fi
        echo "Waiting for PostgreSQL... (attempt $i/60)"
        sleep 3
    done
    
    # Additional wait for all Supabase services to be fully ready
    echo "Waiting for all Supabase services to be ready..."
    for i in {1..20}; do
        if bun run supabase status --workdir database > /dev/null 2>&1; then
            echo "All Supabase services are ready"
            break
        fi
        if [ $i -eq 20 ]; then
            echo "Warning: Some Supabase services may not be fully ready, but PostgreSQL is available"
            break
        fi
        sleep 2
    done
    
    echo "Supabase services started successfully"
}

run_migrations() {
    echo "Checking database migrations..."
    
    # Retry migrations a few times in case of transient connection issues
    for i in {1..3}; do
        if bun run dev:migrate; then
            echo "Database migrations completed"
            return 0
        fi
        
        if [ $i -lt 3 ]; then
            echo "Migration attempt $i failed, retrying in 5 seconds..."
            sleep 5
        fi
    done
    
    echo "Failed to run database migrations after 3 attempts"
    exit 1
}

start_server() {
    echo "Starting Fastify server..."
    
    # Start server with .env file watching
    NODE_ENV=development bun run dev:fastify
}

# Main execution
main() {
    # Check if Supabase is running
    if check_supabase_status; then
        echo "Supabase is already running"
    else
        start_supabase
    fi
    
    # Run migrations
    run_migrations
    
    # Start the server
    start_server
}

# Handle interruption signals
trap 'echo "Shutting down..."; exit 0' SIGINT SIGTERM

main "$@" 
