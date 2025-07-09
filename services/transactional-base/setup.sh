#!/bin/bash -e -x

########################################################
# Check dependencies
########################################################

# Function to check if a command exists
check_dependency() {
    local cmd="$1"
    local name="$2"
    
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ Error: $name is not installed or not in PATH"
        echo "Please install $name and try again."
        exit 1
    else
        echo "✅ $name is available: $(command -v "$cmd")"
    fi
}

# Check required dependencies
echo "🔍 Checking required dependencies..."
check_dependency "git" "Git"
check_dependency "docker" "Docker"
check_dependency "docker" "Docker Compose"  # docker compose is a subcommand of docker
check_dependency "node" "Node.js"
check_dependency "pnpm" "pnpm"

# Verify docker compose specifically
if ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not working properly"
    echo "Please ensure Docker Compose is properly installed."
    exit 1
else
    echo "✅ Docker Compose is working: $(docker compose version)"
fi

echo "✅ All dependencies are available. Proceeding with setup..."

########################################################
# Setup environment
########################################################

# Check if .env file exists, if not copy from env.example
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo "📋 .env file not found. Copying env.example to .env..."
        cp env.example .env
        echo "✅ .env file created from env.example"
    else
        echo "❌ Error: .env file not found and env.example does not exist"
        echo "Please create a .env file with the required environment variables."
        exit 1
    fi
else
    echo "✅ .env file already exists"
fi

# Check if .env.secrets file exists, if not generate it
if [ ! -f ".env.secrets" ] || [[ " $@ " =~ " --reset-secrets" ]]; then
    if [ -f "generate-jwt.mjs" ]; then
        echo "🔐 .env.secrets file missing or --reset-secrets passed. Generating secrets..."
        node generate-jwt.mjs -o .env.secrets
        if [ $? -eq 0 ]; then
            echo "✅ .env.secrets file generated successfully"
        else
            echo "❌ Error: Failed to generate .env.secrets file"
            exit 1
        fi
    else
        echo "❌ Error: .env.secrets file not found and generate-jwt.mjs does not exist"
        echo "Please ensure generate-jwt.mjs is available to create secrets."
        exit 1
    fi
else
    echo "✅ .env.secrets file already exists"
fi

ENV_FILES="--env-file .env --env-file .env.secrets"
DOCKER_COMPOSE_CMD="docker compose $ENV_FILES"


if [[ " $@ " =~ " --reset" ]] || [[ " $@ " =~ " --reset-secrets" ]]; then
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
fi

if [[ " $@ " =~ " --restart" ]]; then
    echo "Restart flag detected: stopping all running containers..."
    $DOCKER_COMPOSE_CMD stop
fi

if [[ " $@ " =~ " --stop" ]]; then
    echo "Stop flag detected: stopping all running containers..."
    $DOCKER_COMPOSE_CMD stop
    exit 0
fi
if [[ " $@ " =~ " --status" ]]; then
    echo "Showing status of all containers..."
    $DOCKER_COMPOSE_CMD ps
    exit 0
fi

if [[ " $@ " =~ " --logs" ]]; then
    echo "Showing logs for supavisor service..."
    $DOCKER_COMPOSE_CMD logs supavisor
    exit 0
fi

$DOCKER_COMPOSE_CMD pull
$DOCKER_COMPOSE_CMD up -d

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

