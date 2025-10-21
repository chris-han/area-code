#!/bin/bash
#
# Run Complete Application (ABI + Moose)
#
# This script starts the complete application with:
# - ABI APIs (billing, workflows, plugins, health checks)
# - Moose framework (data ingestion, consumption, workflows)
#
# Environment Variables:
#   HOST - Host to bind to (default: 0.0.0.0)
#   PORT - Port to bind to (default: 8000)
#

set -e

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$PROJECT_DIR"

# Set default environment variables
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"

echo "=========================================="
echo "Starting ABI/Moose Application"
echo "=========================================="
echo "Host: $HOST"
echo "Port: $PORT"
echo "=========================================="

# Start the application using uvicorn
uvicorn bia_backend.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --reload \
    --log-level info

# Alternative: Run with gunicorn for production
# gunicorn bia_backend.main:app \
#     --bind "$HOST:$PORT" \
#     --workers 4 \
#     --worker-class uvicorn.workers.UvicornWorker \
#     --access-logfile - \
#     --error-logfile -
