# Application Frontend

A React dashboard application for managing and visualizing Foo and Bar entities with both transactional and analytical data views.

## Available Scripts

```bash
# Development
bun run dev        # Start development server with Vite
bun run ufa:dev    # Alias for dev script used in monorepo context

# Production
bun run build      # Build for production (TypeScript + Vite build)
bun run preview    # Preview production build locally

# Code quality
bun run lint       # Run ESLint on TypeScript source files
```

## Environment

Create a `.env.development` file in this folder with:

```
VITE_TRANSACTIONAL_API_BASE=http://localhost:8082/api
VITE_ANALYTICAL_CONSUMPTION_API_BASE=http://localhost:4100/consumption
VITE_RETRIEVAL_API_BASE=http://localhost:8083
```
