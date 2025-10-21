#!/bin/bash

# Combined development script: runs Moose dev stack and ABI FastAPI API together.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SERVICE_DIR"

MOOSE_PID=""
API_PID=""

cleanup() {
    local exit_code=$?
    trap - EXIT INT TERM
    if [[ -n "$MOOSE_PID" ]]; then
        kill "$MOOSE_PID" 2>/dev/null || true
        wait "$MOOSE_PID" 2>/dev/null || true
        MOOSE_PID=""
    fi
    if [[ -n "$API_PID" ]]; then
        kill "$API_PID" 2>/dev/null || true
        wait "$API_PID" 2>/dev/null || true
        API_PID=""
    fi
    exit $exit_code
}

trap cleanup EXIT INT TERM

echo "[ABI DEV] Starting Moose development stack..."
./scripts/dev.sh &
MOOSE_PID=$!

echo "[ABI DEV] Starting ABI FastAPI server..."
ABI_HTTP_PORT="${ABI_HTTP_PORT:-4300}" \
    ./scripts/abi-api.sh &
API_PID=$!

# Wait until either process exits
wait -n "$MOOSE_PID" "$API_PID"
# cleanup trap will handle remaining process
