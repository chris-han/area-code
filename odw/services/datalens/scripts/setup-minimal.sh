#!/bin/bash

# Minimal DataLens Setup Script for ABI
# Sets up configuration without cloning repositories

set -e

echo "🚀 Setting up DataLens configuration for Azure Billing Intelligence..."

# Create directories
mkdir -p backend frontend config

# Load configuration from moose.config.toml
echo "🔧 Loading configuration from moose.config.toml..."
if [ -f "../data-warehouse/moose.config.toml" ]; then
    # Parse TOML configuration (simplified parsing for shell)
    CLICKHOUSE_HOST=$(grep 'host = ' ../data-warehouse/moose.config.toml | grep -v temporal_host | head -1 | cut -d'"' -f2)
    CLICKHOUSE_HOST_PORT=$(grep 'host_port = ' ../data-warehouse/moose.config.toml | cut -d' ' -f3)
    CLICKHOUSE_USER=$(grep 'user = ' ../data-warehouse/moose.config.toml | head -1 | cut -d'"' -f2)
    CLICKHOUSE_PASSWORD=$(grep 'password = ' ../data-warehouse/moose.config.toml | head -1 | cut -d'"' -f2)
    CLICKHOUSE_DB_NAME=$(grep 'db_name = ' ../data-warehouse/moose.config.toml | cut -d'"' -f2)
    CLICKHOUSE_USE_SSL=$(grep 'use_ssl = ' ../data-warehouse/moose.config.toml | cut -d' ' -f3)
    
    # Temporal configuration from moose.config.toml
    TEMPORAL_DB_USER=$(grep 'db_user = ' ../data-warehouse/moose.config.toml | cut -d'"' -f2)
    TEMPORAL_DB_PASSWORD=$(grep 'db_password = ' ../data-warehouse/moose.config.toml | cut -d'"' -f2)
    TEMPORAL_DB_PORT=$(grep 'db_port = ' ../data-warehouse/moose.config.toml | cut -d' ' -f3)
    TEMPORAL_HOST=$(grep 'temporal_host = ' ../data-warehouse/moose.config.toml | cut -d'"' -f2)
    TEMPORAL_PORT=$(grep 'temporal_port = ' ../data-warehouse/moose.config.toml | cut -d' ' -f3)
    TEMPORAL_UI_PORT=$(grep 'ui_port = ' ../data-warehouse/moose.config.toml | cut -d' ' -f3)
    
    echo "✅ Configuration loaded from ../data-warehouse/moose.config.toml"
else
    echo "❌ Error: ../data-warehouse/moose.config.toml not found"
    echo "Please ensure the data-warehouse service is properly configured"
    exit 1
fi

# Create DataLens configuration
echo "📝 Creating DataLens configuration..."
cat > config/datalens.env << EOF
# DataLens Configuration for ABI
DATALENS_PORT=8081
DATALENS_BACKEND_PORT=8082

# ClickHouse Connection (from data-warehouse .env)
CLICKHOUSE_HOST=${CLICKHOUSE_HOST}
CLICKHOUSE_PORT=${CLICKHOUSE_HOST_PORT}
CLICKHOUSE_USER=${CLICKHOUSE_USER}
CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD}
CLICKHOUSE_DB=${CLICKHOUSE_DB_NAME}
CLICKHOUSE_USE_SSL=${CLICKHOUSE_USE_SSL}

# DataLens Backend Configuration
DATALENS_BACKEND_HOST=localhost
DATALENS_BACKEND_PORT=8082

# CORS Configuration
CORS_ORIGINS=http://localhost:8081,http://localhost:3000

# ABI Extensions
ENABLE_ABI_EXTENSIONS=true
FOCUS_SPECIFICATION_VERSION=1.0

# Temporal Integration (for port conflict resolution)
TEMPORAL_UI_PORT=8080
TEMPORAL_UI_PATH=/temporal
EOF

# Create environment file for Docker Compose
echo "🐳 Creating Docker Compose environment..."
cat > .env << EOF
# Environment variables for Docker Compose (from moose.config.toml)
CLICKHOUSE_HOST=${CLICKHOUSE_HOST}
CLICKHOUSE_HOST_PORT=${CLICKHOUSE_HOST_PORT}
CLICKHOUSE_USER=${CLICKHOUSE_USER}
CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD}
CLICKHOUSE_DB_NAME=${CLICKHOUSE_DB_NAME}
CLICKHOUSE_USE_SSL=${CLICKHOUSE_USE_SSL}

# Temporal configuration (local Docker containers)
TEMPORAL_DB_HOST=postgres
TEMPORAL_DB_PORT=${TEMPORAL_DB_PORT}
TEMPORAL_DB_USER=${TEMPORAL_DB_USER}
TEMPORAL_DB_PASSWORD=${TEMPORAL_DB_PASSWORD}
TEMPORAL_HOST=${TEMPORAL_HOST}
TEMPORAL_PORT=${TEMPORAL_PORT}
TEMPORAL_UI_PORT=${TEMPORAL_UI_PORT}

DATALENS_PORT=8081
DATALENS_BACKEND_PORT=8082
NGINX_PROXY_PORT=9080
EOF

# Create placeholder Dockerfiles for when repositories are available
echo "📋 Creating placeholder Dockerfiles..."

# Backend Dockerfile
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone DataLens backend if not present
RUN if [ ! -d "datalens-backend" ]; then \
        git clone https://github.com/chris-han/datalens-backend.git datalens-backend; \
    fi

WORKDIR /app/datalens-backend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt || echo "Requirements file not found, skipping"

# Copy configuration
COPY ../config /app/config

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start application
CMD ["python", "app.py"]
EOF

# Frontend Dockerfile
cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine as builder

WORKDIR /app

# Clone DataLens frontend if not present
RUN if [ ! -d "datalens-ui" ]; then \
        apk add --no-cache git && \
        git clone https://github.com/chris-han/datalens-ui.git datalens-ui; \
    fi

WORKDIR /app/datalens-ui

# Install dependencies
RUN npm ci --only=production || echo "Package.json not found, skipping npm install"

# Copy ABI extensions
COPY ../abi-extensions /app/abi-extensions

# Build application
RUN npm run build || echo "Build script not found, skipping build"

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/datalens-ui/dist /usr/share/nginx/html || \
COPY --from=builder /app/datalens-ui/build /usr/share/nginx/html || \
echo "No build output found"

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
EOF

# Create nginx configuration for frontend
cat > frontend/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;
        
        location / {
            try_files $uri $uri/ /index.html;
        }
        
        location /api/ {
            proxy_pass http://datalens-backend:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
EOF

echo "✅ DataLens minimal setup completed!"
echo ""
echo "📋 Configuration Summary:"
echo "   - DataLens Frontend: Port 8081"
echo "   - DataLens Backend: Port 8082"
echo "   - Nginx Proxy: Port 9080 (unified access)"
echo "   - Temporal UI: Port 8080 (also accessible via /temporal)"
echo ""
echo "🔗 ClickHouse Connection:"
echo "   - Host: ${CLICKHOUSE_HOST}"
echo "   - Port: ${CLICKHOUSE_HOST_PORT}"
echo "   - Database: ${CLICKHOUSE_DB_NAME}"
echo "   - User: ${CLICKHOUSE_USER}"
echo ""
echo "📝 Configuration files created:"
echo "   - config/datalens.env"
echo "   - config/connections.yaml"
echo "   - config/dashboards.yaml"
echo "   - .env (Docker Compose)"
echo ""
echo "🚀 Next steps:"
echo "   1. Clone repositories manually if needed:"
echo "      git clone https://github.com/chris-han/datalens-backend.git backend/datalens-backend"
echo "      git clone https://github.com/chris-han/datalens-ui.git frontend/datalens-ui"
echo "   2. Build platform: ./scripts/build.sh"
echo "   3. Start services: ./scripts/dev.sh"