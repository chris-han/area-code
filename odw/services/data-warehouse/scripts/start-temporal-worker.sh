#!/bin/bash
#
# Start Temporal Worker for bia Workflows
#
# This script starts the Temporal worker that processes the bia-workflows task queue.
# The worker handles Azure billing data extraction, transformation, and validation workflows.
#

set -e

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$PROJECT_DIR"

# Set default environment variables
export TEMPORAL_HOST="${TEMPORAL_HOST:-localhost:7233}"
export TASK_QUEUE="${TASK_QUEUE:-bia-workflows}"

echo "=========================================="
echo "Starting Temporal Worker"
echo "=========================================="
echo "Temporal Host: $TEMPORAL_HOST"
echo "Task Queue: $TASK_QUEUE"
echo "Project Dir: $PROJECT_DIR"
echo "=========================================="

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Start the Temporal worker
python -m app.azure_billing.workflows.temporal_worker