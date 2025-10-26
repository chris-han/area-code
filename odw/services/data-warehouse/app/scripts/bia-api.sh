#!/bin/bash
set -e

# Start BIA Admin API with correct PYTHONPATH
export PYTHONPATH=/home/chris/repo/area-code/bia_admin:$PYTHONPATH

# Change to data warehouse directory where moose.config.toml exists
cd /home/chris/repo/area-code/odw/services/data-warehouse

# Activate venv and start uvicorn
source .venv/bin/activate
exec python -m uvicorn bia_backend.main:app --host 0.0.0.0 --port 4300
