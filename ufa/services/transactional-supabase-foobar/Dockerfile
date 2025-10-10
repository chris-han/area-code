# Simple Dockerfile that replicates development environment
FROM oven/bun:1.2.21

WORKDIR /app

# Copy package files
COPY package.json turbo.json ./
COPY ufa/services/transactional-supabase-foobar/package.json ./ufa/services/transactional-supabase-foobar/
COPY ufa/packages/models/package.json ./ufa/packages/models/
COPY ufa/packages/eslint-config/package.json ./ufa/packages/eslint-config/
COPY ufa/packages/typescript-config/package.json ./ufa/packages/typescript-config/

# Copy packages source code (needed before install due to postinstall build scripts)
COPY ufa/packages ./ufa/packages

# Install all dependencies (including dev dependencies like tsx)
RUN bun install

# Copy service source code
COPY ufa/services/transactional-supabase-foobar ./ufa/services/transactional-supabase-foobar

# Set working directory to the service
WORKDIR /app/ufa/services/transactional-supabase-foobar

# Build the TypeScript code
RUN bun run build

# Set production environment
ENV NODE_ENV=production

# Expose port
EXPOSE 8082

# Run the bundled JavaScript
CMD ["node", "dist/server.js"]
