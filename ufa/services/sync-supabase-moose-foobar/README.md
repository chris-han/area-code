# Sync Service

A MooseJS workflow service that listens to Supabase database changes and syncs data to analytical and retrieval backends.

## Environment Variables

### Development

Development mode uses Supabase CLI defaults and automatically configures the database connection.

### Production

For production deployments, set the following environment variable:

- `SUPABASE_CONNECTION_STRING` - PostgreSQL connection string for your Supabase database
  - Format: `postgresql://postgres:[password]@[host]:[port]/postgres`
  - Example: `postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres`
  - This is used for executing complex SQL scripts (like realtime replication setup)

The service will automatically detect production mode (`NODE_ENV=production`) and use the connection string.

## Available Scripts

```bash
# MooseJS CLI access
bun run moose

# Build Docker image
bun run build

# Start development server
bun run dev
bun run ufa:dev

# Clean development environment
bun run ufa:dev:clean

# Workflow management
bun run dev:workflow        # Run Supabase listener workflow
bun run dev:workflow:stop   # Stop Supabase listener workflow
```
