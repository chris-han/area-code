#!/bin/bash -e -x

########################################################
# Global variables
########################################################

ENV_FILES="--env-file .env --env-file .env.secrets"
DOCKER_COMPOSE_CMD="docker compose $ENV_FILES"

########################################################
# Utility functions
########################################################

# Function to check if a command exists
check_dependency() {
    local cmd="$1"
    local name="$2"
    
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ Error: $name is not installed or not in PATH"
        echo "Please install $name and try again."
        return 1
    else
        echo "✅ $name is available: $(command -v "$cmd")"
        return 0
    fi
}

# Function to check if a flag is present in arguments
has_flag() {
    local flag="$1"
    shift
    [[ " $@ " =~ " $flag" ]]
}

########################################################
# Core functionality functions
########################################################

check_dependencies() {
    echo "🔍 Checking required dependencies..."
    
    # Check required dependencies
    check_dependency "git" "Git" || return 1
    check_dependency "docker" "Docker" || return 1
    check_dependency "docker" "Docker Compose" || return 1
    check_dependency "node" "Node.js" || return 1
    check_dependency "pnpm" "pnpm" || return 1

    # Verify docker compose specifically
    if ! docker compose version &> /dev/null; then
        echo "❌ Error: Docker Compose is not working properly"
        echo "Please ensure Docker Compose is properly installed."
        return 1
    else
        echo "✅ Docker Compose is working: $(docker compose version)"
    fi

    echo "✅ All dependencies are available."
    return 0
}

setup_environment() {
    echo "🔧 Setting up environment files..."
    
    # Check if .env file exists, if not copy from env.example
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            echo "📋 .env file not found. Copying env.example to .env..."
            cp env.example .env
            echo "✅ .env file created from env.example"
        else
            echo "❌ Error: .env file not found and env.example does not exist"
            echo "Please create a .env file with the required environment variables."
            return 1
        fi
    else
        echo "✅ .env file already exists"
    fi

    # Check if .env.secrets file exists, if not generate it
    if [ ! -f ".env.secrets" ] || has_flag "--reset-secrets" "$@"; then
        if [ -f "generate-jwt.mjs" ]; then
            echo "🔐 .env.secrets file missing or --reset-secrets passed. Generating secrets..."
            node generate-jwt.mjs -o .env.secrets
            if [ $? -eq 0 ]; then
                echo "✅ .env.secrets file generated successfully"
            else
                echo "❌ Error: Failed to generate .env.secrets file"
                return 1
            fi
        else
            echo "❌ Error: .env.secrets file not found and generate-jwt.mjs does not exist"
            echo "Please ensure generate-jwt.mjs is available to create secrets."
            return 1
        fi
    else
        echo "✅ .env.secrets file already exists"
    fi
    
    return 0
}

reset_environment() {
    echo "🔄 Resetting environment..."
    
    echo "Stopping and removing all containers with volumes and orphans..."
    $DOCKER_COMPOSE_CMD down -v --remove-orphans

    BIND_MOUNTS=(
        "./volumes/db/data"
    )

    for DIR in "${BIND_MOUNTS[@]}"; do
        if [ -d "$DIR" ]; then
            echo "Deleting $DIR..."
            rm -rf "$DIR"
        fi
    done

    docker volume prune -f
    echo "✅ Environment reset complete"
}

stop_services() {
    echo "🛑 Stopping all running containers..."
    $DOCKER_COMPOSE_CMD stop
    echo "✅ Services stopped"
}

show_status() {
    echo "📊 Showing status of all containers..."
    $DOCKER_COMPOSE_CMD ps
}

show_logs() {
    echo "📋 Showing logs for supavisor service..."
    $DOCKER_COMPOSE_CMD logs supavisor
}

start_services() {
    echo "🚀 Starting services..."
    $DOCKER_COMPOSE_CMD pull
    $DOCKER_COMPOSE_CMD up -d
    echo "✅ Services started"
}

seed_database() {
    echo "🌱 Seeding database..."
    
    # Wait for database to be ready
    echo "⏳ Waiting for database to be ready..."
    if [ -f "src/scripts/wait-for-services.ts" ]; then
        npx tsx src/scripts/wait-for-services.ts
        if [ $? -ne 0 ]; then
            echo "❌ Error: Database is not ready for seeding"
            return 1
        fi
    fi
    
    # Run migrations first
    echo "📋 Running database migrations..."
    if [ -f "src/scripts/migrate.ts" ]; then
        npx tsx src/scripts/migrate.ts
        if [ $? -ne 0 ]; then
            echo "❌ Error: Database migration failed"
            return 1
        fi
    fi
    
    # Run seeding
    echo "🌱 Running database seeding..."
    if [ -f "src/scripts/seed.ts" ]; then
        npx tsx src/scripts/seed.ts
        if [ $? -eq 0 ]; then
            echo "✅ Database seeding completed successfully"
            return 0
        else
            echo "❌ Error: Database seeding failed"
            return 1
        fi
    else
        echo "❌ Error: Seed script not found at src/scripts/seed.ts"
        return 1
    fi
}

display_dashboard_url() {
    if [ -f ".env.secrets" ]; then
        # Extract username and password from .env.secrets
        DASHBOARD_USERNAME=$(grep -E '^DASHBOARD_USERNAME=' .env.secrets | cut -d '=' -f2-)
        DASHBOARD_PASSWORD=$(grep -E '^DASHBOARD_PASSWORD=' .env.secrets | cut -d '=' -f2-)
        if [ -n "$DASHBOARD_USERNAME" ] && [ -n "$DASHBOARD_PASSWORD" ]; then
            echo ""
            echo "🔗 Supabase Studio URL:"
            echo "    http://$DASHBOARD_USERNAME:$DASHBOARD_PASSWORD@localhost:8000"
            echo ""
        else
            echo "⚠️  Could not find DASHBOARD_USERNAME or DASHBOARD_PASSWORD in .env.secrets"
        fi
    else
        echo "⚠️  .env.secrets file not found, cannot print Supabase Studio URL"
    fi
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help              Show this help message"
    echo "  --stop              Stop all running containers"
    echo "  --restart           Stop and restart all containers"
    echo "  --reset             Reset environment (stop, remove volumes, delete data)"
    echo "  --reset-secrets     Regenerate .env.secrets file"
    echo "  --status            Show status of all containers"
    echo "  --logs              Show logs for supavisor service"
    echo "  --seed              Seed the database with initial data"
    echo ""
    echo "Examples:"
    echo "  $0                  # Normal setup and start"
    echo "  $0 --stop           # Stop services"
    echo "  $0 --restart        # Restart services"
    echo "  $0 --reset          # Complete reset"
    echo "  $0 --status         # Check service status"
    echo "  $0 --seed           # Seed database with initial data"
    echo "  $0 --reset --seed   # Reset and seed database"
}

########################################################
# Main function
########################################################

main() {
    # Handle help flag
    if has_flag "--help" "$@"; then
        show_help
        exit 0
    fi

    # Check dependencies first (unless just showing help/status/logs)
    if ! has_flag "--status" "$@" && ! has_flag "--logs" "$@" && ! has_flag "--help" "$@"; then
        if ! check_dependencies; then
            echo "❌ Dependency check failed. Exiting."
            exit 1
        fi
    fi

    # Handle stop flag
    if has_flag "--stop" "$@"; then
        stop_services
        exit 0
    fi

    # Handle status flag
    if has_flag "--status" "$@"; then
        show_status
        exit 0
    fi

    # Handle logs flag
    if has_flag "--logs" "$@"; then
        show_logs
        exit 0
    fi

    # Setup environment (unless just showing status/logs)
    if ! has_flag "--status" "$@" && ! has_flag "--logs" "$@"; then
        if ! setup_environment "$@"; then
            echo "❌ Environment setup failed. Exiting."
            exit 1
        fi
    fi

    # Handle reset flags
    if has_flag "--reset" "$@" || has_flag "--reset-secrets" "$@"; then
        reset_environment
    fi

    # Handle restart flag
    if has_flag "--restart" "$@"; then
        stop_services
    fi

    # Start services (unless just showing status/logs)
    if ! has_flag "--status" "$@" && ! has_flag "--logs" "$@"; then
        start_services
        
        # Handle seed flag after services are started
        if has_flag "--seed" "$@"; then
            echo "⏳ Waiting for services to be ready before seeding..."
            sleep 5  # Give services a moment to start
            if ! seed_database; then
                echo "❌ Seeding failed. Exiting."
                exit 1
            fi
        fi
        
        display_dashboard_url
    fi

    echo "✅ Setup complete!"
}

########################################################
# Script execution
########################################################

# Call main function with all arguments
main "$@"

