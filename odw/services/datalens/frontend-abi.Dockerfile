# DataLens Frontend with ABI Extensions
FROM oven/bun:1.1.16-alpine as builder

WORKDIR /app

# Copy source code and dependencies
COPY datalens-ui/package*.json ./
RUN if ls package*.json >/dev/null 2>&1; then bun install --production; fi

# Copy full source after installing deps
COPY datalens-ui/ .

# Copy ABI extensions
COPY services/datalens/frontend/abi-extensions /app/src/abi-extensions

# Create ABI configuration
RUN mkdir -p /app/src/ui/constants/abi
COPY services/datalens/config/connections.yaml /app/src/ui/constants/abi/
COPY services/datalens/config/dashboards.yaml /app/src/ui/constants/abi/

# Build application with ABI extensions
ENV NODE_ENV=production
ENV ENABLE_ABI_EXTENSIONS=true
RUN if ls package*.json >/dev/null 2>&1; then bun run build; fi

# Production stage
FROM oven/bun:1.1.16-alpine

WORKDIR /app

# Install serve for production
RUN bun install -g serve

# Copy built application
COPY --from=builder /app/dist /app/dist

# Create serve configuration
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
