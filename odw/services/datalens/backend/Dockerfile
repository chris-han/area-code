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
