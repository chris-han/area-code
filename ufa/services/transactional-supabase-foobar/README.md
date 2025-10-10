# Transactional Backend

A Fastify API service providing CRUD operations for Foo and Bar entities using Drizzle ORM and PostgreSQL.

## Setup

### Environment Variables

This service requires an Anthropic API key to enable AI chat functionality with Sloan MCP (Model Context Protocol) tools:

1. **Get an Anthropic API key**: Visit [console.anthropic.com](https://console.anthropic.com) to create an account and generate an API key
2. **Create a `.env.local` file** in this service directory (`ufa/services/transactional-supabase-foobar/`):
   ```bash
   ANTHROPIC_API_KEY=your-api-key-here
   ```

The Sloan MCP provides AI-powered tools for interacting with your Moose analytical backend, enabling intelligent data querying and analysis through the chat interface.

## Available Scripts

```bash
# Development
bun run dev                 # Start with database setup
bun run ufa:dev            # Alias for dev script
bun run dev:server-only    # Start server only (skip DB setup)
bun run dev:migrate        # Run database migrations in dev mode

# Production
bun run build              # Compile TypeScript
bun run start              # Start production server

# Database
bun run db:generate        # Generate Drizzle schema
bun run db:migrate         # Run database migrations
bun run db:studio          # Open Drizzle Studio

# Utilities
bun run clean              # Remove build artifacts
bun run typecheck          # Type checking without build
```
