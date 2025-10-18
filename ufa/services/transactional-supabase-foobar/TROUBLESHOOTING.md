# Troubleshooting PostgreSQL Startup Issues

## Common Issue: "Database system is starting up"

If you see the error:

```
ERROR   Unable to create SQL database.  {"error": "unable to connect to DB, tried default DB names: postgres,defaultdb, errors: [pq: the database system is starting up pq: the database system is starting up]"
```

This means PostgreSQL is starting but not yet ready to accept connections.

## Solutions

### 1. Use the improved startup script

The `dev-startup.sh` script has been updated to properly wait for PostgreSQL to be ready:

```bash
bun run ufa:dev
```

### 2. Check service health

Use the health check script to verify all services are running:

```bash
bun run health
```

### 3. Manual startup (if needed)

If the automatic startup fails, try these steps:

```bash
# Stop any existing services
bun run db:stop

# Start Supabase services
bun run db:start

# Wait a moment for PostgreSQL to fully start
sleep 10

# Check if services are ready
bun run health

# Run migrations
bun run dev:migrate

# Start the server
bun run dev:fastify
```

### 4. Check service status

```bash
bun run db:status
```

## Prevention

The updated startup script now:

- Uses `pg_isready` to test actual database connectivity
- Waits up to 3 minutes for PostgreSQL to be ready
- Retries migrations if they fail due to timing issues
- Provides better error messages

## Port Configuration

The service uses these fixed ports (as per mono-repo rules):

- PostgreSQL: 54322
- Supabase API: 54321
- Supabase Studio: 54323

These ports are explicitly configured to avoid auto-assignment conflicts.
