#!/bin/bash

# DataLens Clean Development Script
# Stops and cleans DataLens services, then restarts

set -e

echo "🧹 Cleaning DataLens development environment..."

# Stop existing services
echo "🛑 Stopping DataLens services..."
docker-compose down -v

# Clean Docker images and containers
echo "🗑️  Cleaning Docker resources..."
docker-compose rm -f
docker system prune -f

# Restart services
echo "🚀 Restarting DataLens services..."
./scripts/dev.sh

echo "✅ DataLens environment cleaned and restarted!"