#!/bin/bash

# Launch the ABI FastAPI application on a dedicated port without starting Moose infrastructure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SERVICE_DIR"

UV_CACHE_DIR="$SERVICE_DIR/.uv-cache"
export UV_CACHE_DIR
mkdir -p "$UV_CACHE_DIR"

PORT="${ABI_HTTP_PORT:-4300}"
HOST="${ABI_HTTP_HOST:-0.0.0.0}"

if lsof -i ":$PORT" >/dev/null 2>&1; then
  echo "Port $PORT is already in use; set ABI_HTTP_PORT to a free port." >&2
  exit 1
fi

# Activate virtualenv if present
PYTHON_BIN="python"
if [ -d .venv ]; then
  PYTHON_BIN=".venv/bin/python"
fi

exec "$PYTHON_BIN" -m uvicorn app.abi_main:abi_fastapi_app --reload --host "$HOST" --port "$PORT"
