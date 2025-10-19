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
