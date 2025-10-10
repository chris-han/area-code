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

start_supabase() {
    echo "Supabase is not started"
    echo "Starting Supabase services..."
    
    if ! bun run db:start; then
        echo "Failed to start Supabase services"
        exit 1
    fi
    
    # Wait for services to be ready using supabase status
    echo "Waiting for services to be ready..."
    for i in {1..30}; do
        if bun run supabase status --workdir database > /dev/null 2>&1; then
            echo "Supabase services are ready"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "Timeout waiting for Supabase services"
            exit 1
        fi
        sleep 2
    done
    
    echo "Supabase services started successfully"
}

run_migrations() {
    echo "Checking database migrations..."
    
    if ! bun run dev:migrate; then
        echo "Failed to run database migrations"
        exit 1
    fi
    
    echo "Database migrations completed"
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
