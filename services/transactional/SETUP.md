# Setup Guide for Transactional Service

This guide will walk you through setting up and running the transactional service locally.

## Prerequisites

Make sure you have the following installed:

- **Node.js 18+** - [Download here](https://nodejs.org/)
- **pnpm** - Install with `npm install -g pnpm`
- **Docker & Docker Compose** - [Download here](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download here](https://git-scm.com/)

## Step-by-Step Setup

### 1. Navigate to the Service Directory

```bash
cd services/transactional
```

### 2. Install Dependencies

```bash
pnpm install
```

### 3. Set Up Environment Variables

Create a `.env` file from the template:

```bash
# Copy the template (create the file with these contents)
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:5432/postgres
POSTGRES_PASSWORD=your-super-secret-and-long-postgres-password
POSTGRES_DB=postgres
POSTGRES_PORT=5432

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-token-with-at-least-32-characters-long

# Supabase Configuration (if using Supabase client)
SUPABASE_URL=http://localhost:3000
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU

# Server Configuration
PORT=8080
HOST=0.0.0.0
NODE_ENV=development
EOF
```

### 4. Start the Database

```bash
# Start PostgreSQL and related services with Docker
pnpm db:setup
```

**Wait for the database to be ready** (about 30-60 seconds). You can check if it's ready by running:

```bash
docker logs supabase-db
```

Look for a message like "database system is ready to accept connections".

### 5. Generate and Run Migrations

```bash
# Generate migration files from schema
pnpm db:generate

# Apply migrations to the database
pnpm db:migrate
```

### 6. Seed the Database (Optional)

Add sample data for testing:

```bash
pnpm db:seed
```

### 7. Start the Development Server

```bash
pnpm dev
```

The API will be available at `http://localhost:8080`

## Testing the API

### Health Check

```bash
curl http://localhost:8080/health
```

### API Information

```bash
curl http://localhost:8080/
```

### List Users

```bash
curl http://localhost:8080/api/users
```

### List Products

```bash
curl http://localhost:8080/api/products
```

### List Orders

```bash
curl http://localhost:8080/api/orders
```

### Create a New User

```bash
curl -X POST http://localhost:8080/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "firstName": "Test",
    "lastName": "User"
  }'
```

### Create a New Product

```bash
curl -X POST http://localhost:8080/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Product",
    "description": "A test product",
    "price": 1999
  }'
```

## Database Management

### View Database in Drizzle Studio

```bash
pnpm db:studio
```

This opens a web interface at `http://localhost:4983` to browse your database.

### Stop the Database

```bash
pnpm db:stop
```

### Reset Database (Delete All Data)

⚠️ **Warning**: This will delete all data!

```bash
pnpm db:reset
# Then run migrations again
pnpm db:migrate
# Optionally seed again
pnpm db:seed
```

## Development Workflow

1. **Make schema changes** in `src/database/schema.ts`
2. **Generate migrations** with `pnpm db:generate`
3. **Apply migrations** with `pnpm db:migrate`
4. **Restart the dev server** (it should auto-restart with tsx watch)

## Troubleshooting

### Database Connection Issues

1. Make sure Docker is running
2. Check if containers are running: `docker ps`
3. Check container logs: `docker logs supabase-db`
4. Verify the DATABASE_URL in your `.env` file

### Port Already in Use

If port 8080 is already in use, change the PORT in your `.env` file:

```bash
PORT=3001
```

### TypeScript Errors

The project uses ESM modules. If you see TypeScript errors, make sure:

1. You have the latest dependencies installed
2. Your Node.js version is 18+
3. Try restarting your IDE/editor

### Database Not Ready

If migrations fail, the database might not be ready yet. Wait a minute and try again:

```bash
# Wait a bit, then try
pnpm db:migrate
```

## Production Deployment

For production deployment, make sure to:

1. Use secure environment variables
2. Set up proper database connection pooling
3. Configure logging and monitoring
4. Set up SSL/TLS
5. Use a reverse proxy (nginx, etc.)
6. Set up database backups

## Additional Resources

- [Fastify Documentation](https://www.fastify.io/)
- [Drizzle ORM Documentation](https://orm.drizzle.team/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

Need help? Check the README.md or create an issue in the repository. 