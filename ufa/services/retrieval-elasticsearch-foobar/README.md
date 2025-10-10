# Retrieval Backend Service

A search service that uses Elasticsearch to enable full-text search for Foo and Bar entities.

## Available Scripts

```bash
# Development
bun run dev                 # Start Elasticsearch and API server (full setup)
bun run ufa:dev            # Alias for dev script used in monorepo context
bun run dev:server-only    # Start only API server (skip Elasticsearch)
bun run ufa:dev:clean      # Stop Elasticsearch containers

# Build and code quality
bun run build              # Compile TypeScript to JavaScript
bun run lint               # Run ESLint on source files

# Elasticsearch management
bun run es:start           # Start Elasticsearch + initialize indices
bun run es:stop            # Stop Elasticsearch containers
bun run es:reset           # Reset Elasticsearch data (full reset)
bun run es:status          # Check Elasticsearch status
bun run es:init-indices    # Initialize Elasticsearch indices
```

---
