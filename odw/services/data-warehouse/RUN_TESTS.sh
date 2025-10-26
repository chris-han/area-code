#!/bin/bash
# Run FOCUS billing tests
#
# Usage:
#   ./RUN_TESTS.sh                    # All tests
#   ./RUN_TESTS.sh unit              # Unit tests only (no Moose needed)
#   ./RUN_TESTS.sh integration       # Integration tests (Moose required)

cd "$(dirname "$0")"
source .venv/bin/activate

MODE="${1:-all}"

case "$MODE" in
    unit)
        echo "Running unit tests (no Moose required)..."
        pytest app/focus_billing/tests/ -m "not integration and not slow" -v
        ;;
    integration)
        echo "Running integration tests (Moose required)..."
        echo "Checking if Moose is running..."
        if ! curl -s http://localhost:4200/health > /dev/null 2>&1; then
            echo "❌ Moose not running. Start it first:"
            echo "   ./START_MOOSE_FOR_TESTS.sh"
            exit 1
        fi
        echo "✅ Moose is running"
        pytest app/focus_billing/tests/ -m integration -v
        ;;
    all)
        echo "Running all tests..."
        pytest app/focus_billing/tests/ -v
        ;;
    *)
        echo "Usage: $0 [unit|integration|all]"
        exit 1
        ;;
esac
