#!/bin/bash

# Launch the complete application (ABI + Moose) on a dedicated port.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SERVICE_DIR"

UV_CACHE_DIR="$SERVICE_DIR/.uv-cache"
export UV_CACHE_DIR
mkdir -p "$UV_CACHE_DIR"

PORT="${ABI_HTTP_PORT:-4300}"
HOST="${ABI_HTTP_HOST:-0.0.0.0}"
export ABI_ENABLE_MOCK_WORKFLOWS="${ABI_ENABLE_MOCK_WORKFLOWS:-1}"

if lsof -ti ":$PORT" >/dev/null 2>&1; then
  echo "Port $PORT is in use; attempting to terminate conflicting process(es)..."
  PIDS="$(lsof -ti ":$PORT" 2>/dev/null || true)"
  if [ -n "$PIDS" ]; then
    echo "Killing PID(s): $PIDS"
    # shellcheck disable=SC2086 # word splitting intentional for kill
    kill $PIDS 2>/dev/null || true
    sleep 1
  fi

  if lsof -ti ":$PORT" >/dev/null 2>&1; then
    echo "Unable to free port $PORT; please resolve the conflict manually." >&2
    exit 1
  fi
fi

# Activate virtualenv if present
PYTHON_BIN="python"
if [ -d .venv ]; then
  PYTHON_BIN=".venv/bin/python"
fi

exec "$PYTHON_BIN" -m uvicorn bia_backend.main:app --reload --host "$HOST" --port "$PORT"
