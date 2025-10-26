#!/bin/bash
# Start Moose service for running FOCUS billing tests

cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════════════"
echo "Starting Moose service for FOCUS billing tests"
echo "════════════════════════════════════════════════════════════════"
echo ""

source .venv/bin/activate

echo "Starting Moose on port 4200..."
echo "(Press Ctrl+C to stop when done testing)"
echo ""

.venv/bin/moose-cli dev --port 4200
