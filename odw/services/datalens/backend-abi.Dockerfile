# DataLens Backend with ABI Extensions
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire DataLens backend source
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Create ABI configuration directory
RUN mkdir -p /app/abi-config

# Copy ABI-specific configuration
COPY ../../config/connections.yaml /app/abi-config/
COPY ../../config/dashboards.yaml /app/abi-config/

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