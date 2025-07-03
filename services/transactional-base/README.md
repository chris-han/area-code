# Transactional Base Service - Supabase Setup

A Supabase deployment following official self-hosting best practices.

## Services

This setup includes the core Supabase services:

1. **PostgreSQL Database** - The core database with logical replication enabled
2. **PostgREST** - RESTful API for your PostgreSQL database
3. **Realtime** - WebSocket server for real-time database changes

## Quick Start

1. Start all services:
   ```bash
   docker-compose up -d
   ```

2. Check service health:
   ```bash
   docker-compose ps
   ```

3. Access the services:
   - PostgreSQL: `localhost:5434`
   - REST API: `http://localhost:3001`
   - Realtime: `ws://localhost:4002`

## Database Access

Connect to PostgreSQL:
```bash
psql postgres://postgres:your-super-secret-and-long-postgres-password@localhost:5434/postgres
```

## API Access

The REST API is available at `http://localhost:3001`. Example:

```bash
# Get all tables
curl http://localhost:3001/

# Create a simple table
psql postgres://postgres:your-super-secret-and-long-postgres-password@localhost:5434/postgres -c "
CREATE TABLE items (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);"

# Insert some data
curl -X POST http://localhost:3001/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item"}'

# Query data
curl http://localhost:3001/items
```

## Realtime Access

The Realtime service provides WebSocket connections for live database updates. You can connect using the Supabase client libraries:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('http://localhost:3001', 'your-anon-key')

// Subscribe to changes
const channel = supabase
  .channel('db-changes')
  .on(
    'postgres_changes',
    { event: '*', schema: 'public', table: 'items' },
    (payload) => console.log('Change received!', payload)
  )
  .subscribe()
```

## Environment Variables

Create a `.env` file with the following variables:

```env
POSTGRES_PASSWORD=your-secure-password
JWT_SECRET=your-jwt-secret-at-least-32-chars
SECRET_KEY_BASE=your-secret-key-base
```

## Security Notes

⚠️ **Important**: The default passwords and secrets are for development only. Always change them before deploying to production!

## Stopping Services

```bash
docker-compose down
```

To also remove volumes:
```bash
docker-compose down -v
```

## Troubleshooting

If services fail to start:
1. Check logs: `docker-compose logs [service-name]`
2. Ensure ports 5434, 3001, and 4002 are not in use
3. Verify the database is healthy before dependent services start

### Realtime Connection Issues

If the realtime service fails to connect:
1. Check that the database has the `_realtime` schema
2. Verify the `supabase_realtime` publication exists
3. Ensure the database user has proper permissions

## Next Steps

To complete the Supabase stack, you would need to add:
1. GoTrue for authentication
2. Kong as an API gateway
3. Storage API for file uploads
4. Supabase Studio for a web interface 