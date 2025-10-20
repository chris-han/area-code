# DataLens Backend with ABI Extensions
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --install-dir /usr/local/bin
ENV PATH="/usr/local/bin:${PATH}"
ENV UV_LINK_MODE=copy

# Copy the DataLens backend source
COPY services/datalens/datalens-backend/ /app/

# Install Python dependencies using uv
RUN uv pip install --system --no-cache .

# Create ABI configuration directory
RUN mkdir -p /app/abi-config

# Copy ABI-specific configuration
COPY services/datalens/config/connections.yaml /app/abi-config/
COPY services/datalens/config/dashboards.yaml /app/abi-config/

# Set environment variables for DataLens
ENV DL_CORE_CONNECTOR_WHITELIST=clickhouse
ENV DL_CORE_LOGGING_LEVEL=INFO
ENV DL_CORE_PORT=8080
ENV DL_CORE_HOST=0.0.0.0

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/ping || exit 1

# Create startup script
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting DataLens Backend with ABI Extensions..."

# Wait for Redis
echo "⏳ Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done

echo "✅ Dependencies ready, starting DataLens backend..."

# Start the application
exec python -m dl_core.app
EOF

RUN chmod +x /app/start.sh

# Start application
CMD ["/app/start.sh"]
