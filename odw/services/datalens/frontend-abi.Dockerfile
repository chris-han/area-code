# DataLens Frontend with ABI Extensions
FROM node:18-alpine as builder

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache git python3 make g++

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Copy ABI extensions
COPY ../../frontend/abi-extensions /app/src/abi-extensions

# Create ABI configuration
RUN mkdir -p /app/src/ui/constants/abi
COPY ../../config/connections.yaml /app/src/ui/constants/abi/
COPY ../../config/dashboards.yaml /app/src/ui/constants/abi/

# Build application with ABI extensions
ENV NODE_ENV=production
ENV ENABLE_ABI_EXTENSIONS=true
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve for production
RUN npm install -g serve

# Copy built application
COPY --from=builder /app/dist /app/dist

# Create nginx-like configuration for serve
RUN cat > /app/serve.json << 'EOF'
{
  "public": "dist",
  "rewrites": [
    { "source": "/api/*", "destination": "http://datalens-backend:8080/api/*" },
    { "source": "**", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "**/*",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "no-cache"
        }
      ]
    }
  ]
}
EOF

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

# Start application
CMD ["serve", "-c", "serve.json", "-l", "8080"]