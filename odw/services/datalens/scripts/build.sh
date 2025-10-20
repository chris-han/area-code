#!/bin/bash

# DataLens Build Script
# Builds DataLens backend and frontend with ABI extensions

set -e

echo "🔨 Building DataLens platform with ABI extensions..."

# Load configuration
if [ -f "config/datalens.env" ]; then
    source config/datalens.env
    echo "✅ Configuration loaded"
else
    echo "❌ Configuration not found. Running setup first..."
    ./scripts/setup.sh
    source config/datalens.env
fi

# Build backend
if [ -d "datalens-backend" ]; then
    echo "🔨 Building DataLens backend..."
    
    # Check if backend has proper structure
    if [ -f "datalens-backend/pyproject.toml" ]; then
        echo "✅ DataLens backend repository structure verified"
    else
        echo "❌ DataLens backend repository structure invalid"
        exit 1
    fi
    
    echo "✅ DataLens backend build configuration ready"
else
    echo "❌ DataLens backend not found. Run setup first."
    exit 1
fi

# Build frontend
if [ -d "datalens-ui" ]; then
    echo "🔨 Building DataLens frontend..."
    
    # Check if frontend has proper structure
    if [ -f "datalens-ui/package.json" ]; then
        echo "✅ DataLens frontend repository structure verified"
    else
        echo "❌ DataLens frontend repository structure invalid"
        exit 1
    fi
    
    echo "✅ DataLens frontend build configuration ready"
else
    echo "❌ DataLens frontend not found. Run setup first."
    exit 1
fi

# Build ABI extensions
echo "🔨 Building ABI extensions..."
cd frontend/abi-extensions
if [ -f "package.json" ]; then
    bun install
    bun run build
    echo "✅ ABI extensions built successfully"
else
    echo "⚠️  ABI extensions package.json not found, skipping build"
fi
cd ../..

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose build

echo "✅ DataLens platform build completed!"
echo "📋 Next steps:"
echo "   - Run: ./scripts/dev.sh to start development environment"
echo "   - Access DataLens: http://localhost:8081"
echo "   - Access unified interface: http://localhost:9080"
echo "   - Access Temporal UI: http://localhost:9080/temporal"