# Setup Guide - Transactional Base Service

This guide will help you set up and run the Transactional Base Service locally.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v18 or higher) - [Download here](https://nodejs.org/)
- **pnpm** (recommended package manager) - Install with `npm install -g pnpm`
- **Docker** and **Docker Compose** - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)

## Step-by-Step Setup

### 1. Navigate to the Service Directory

```bash
cd services/transactional-base
```

### 2. Install Dependencies

```bash
pnpm install
```

This will install all required dependencies including:
- Fastify (web framework)
- Drizzle ORM (database toolkit)
- PostgreSQL client
- TypeScript and development tools

### 3. Start the Database

```bash
pnpm db:setup
```

This command:
- Starts a PostgreSQL container on port 5433
- Includes PostgREST API on port 3001
- Includes Supabase Auth on port 9998
- Creates necessary volumes for data persistence

**Note**: The database runs on port 5433 to avoid conflicts with other PostgreSQL instances.

### 4. Generate Database Schema

```bash
pnpm db:generate
```

This creates migration files based on your schema definitions in `src/database/schema.ts`.

### 5. Run Database Migrations

```bash
pnpm db:migrate
```

This applies the generated migrations to create the `foo`, `bar`, and `foo_bar` tables.

### 6. Seed the Database (Optional)

```bash
pnpm db:seed
```

This populates the database with sample data:
- 4 foo items (Alpha, Beta, Gamma, Delta)
- 5 bar items with various relationships
- 3 foo-bar many-to-many relationships

### 7. Start the Development Server

```bash
pnpm dev
```

The service will start on `http://localhost:8081` with hot reload enabled.

## Verification

### Check the Service is Running

1. **API Information**: Visit `http://localhost:8081`
2. **Health Check**: Visit `http://localhost:8081/health`

### Test the API Endpoints

```bash
# Get all foo items
curl http://localhost:8081/api/foo

# Get all bar items
curl http://localhost:8081/api/bar

# Get all foo-bar relationships
curl http://localhost:8081/api/foo-bar
```

### Access Database Tools

1. **Drizzle Studio**: Run `pnpm db:studio` to open the database management interface
2. **PostgREST**: Access the auto-generated REST API at `http://localhost:3001`

## Troubleshooting

### Port Conflicts

If you encounter port conflicts:

1. **Database (5433)**: Modify `docker-compose.yml` and `drizzle.config.ts`
2. **API Server (8081)**: Set `PORT` environment variable
3. **PostgREST (3001)**: Modify `docker-compose.yml`

### Database Connection Issues

1. Ensure Docker is running
2. Check if containers are healthy: `docker ps`
3. View logs: `docker logs transactional-base-db`

### Migration Errors

1. Reset database: `pnpm db:reset`
2. Regenerate migrations: `pnpm db:generate`
3. Apply migrations: `pnpm db:migrate`

## Development Workflow

### Making Schema Changes

1. Modify `src/database/schema.ts`
2. Generate migration: `pnpm db:generate`
3. Review generated migration in `migrations/` folder
4. Apply migration: `pnpm db:migrate`

### Adding New Routes

1. Create route file in `src/routes/`
2. Register route in `src/server.ts`
3. Add types and validation schemas

### Testing Changes

1. Use `pnpm dev` for development with hot reload
2. Test endpoints with curl, Postman, or your preferred tool
3. Use `pnpm db:studio` to inspect database changes

## Environment Configuration

Create a `.env` file in the service root for custom configuration:

```env
# Database
DATABASE_URL=postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:5433/postgres

# Server
PORT=8081
HOST=0.0.0.0
NODE_ENV=development
```

## Database Management Commands

### Start/Stop Database
```bash
pnpm db:setup    # Start database
pnpm db:stop     # Stop database
pnpm db:reset    # Reset (WARNING: Deletes all data!)
```

### Schema Management
```bash
pnpm db:generate # Generate migrations
pnpm db:migrate  # Apply migrations
pnpm db:studio   # Open database studio
```

### Data Management
```bash
pnpm db:seed     # Seed with sample data
```

## Production Deployment

### Build the Service
```bash
pnpm build
```

### Start Production Server
```bash
pnpm start
```

### Environment Variables for Production
- `DATABASE_URL`: Production database connection string
- `PORT`: Production port
- `NODE_ENV=production`

## Next Steps

1. **Customize Models**: Rename `foo` and `bar` to your domain entities
2. **Add Business Logic**: Implement validation, calculations, and workflows
3. **Add Authentication**: Integrate with your auth system
4. **Add Tests**: Write unit and integration tests
5. **Add Monitoring**: Implement logging and metrics

## Support

If you encounter issues:

1. Check the logs: `docker logs transactional-base-db`
2. Verify port availability: `netstat -an | grep :5433`
3. Review the database schema in Drizzle Studio
4. Check the API documentation at `http://localhost:8081`

For development questions, refer to:
- [Fastify Documentation](https://fastify.dev/)
- [Drizzle ORM Documentation](https://orm.drizzle.team/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/) 