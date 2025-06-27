# Transactional Base Service

A generic transactional service built with Node.js, TypeScript, Fastify, PostgreSQL, and Drizzle ORM. This service provides a foundation for building transactional applications with generic `foo` and `bar` data models.

## Features

- **Generic Data Models**: `foo`, `bar`, and `fooBar` entities that can be customized for specific use cases
- **RESTful API**: Complete CRUD operations for all entities
- **Relationship Management**: One-to-many (foo→bar) and many-to-many (foo↔bar) relationships
- **Database Operations**: PostgreSQL with Drizzle ORM for type-safe database operations
- **Data Validation**: Zod schemas for request validation
- **Development Tools**: Hot reload, database migrations, seeding, and studio

## Data Models

### Foo Entity
- `id`: UUID primary key
- `name`: Required string (255 chars max)
- `description`: Optional text
- `status`: String with default "active" (50 chars max)
- `priority`: Integer with default 1
- `isActive`: Boolean with default true
- `createdAt`, `updatedAt`: Timestamps

### Bar Entity
- `id`: UUID primary key
- `fooId`: Foreign key reference to Foo
- `value`: Required integer
- `label`: Optional string (100 chars max)
- `notes`: Optional text
- `isEnabled`: Boolean with default true
- `createdAt`, `updatedAt`: Timestamps

### FooBar Junction Table
- `id`: UUID primary key
- `fooId`: Foreign key reference to Foo
- `barId`: Foreign key reference to Bar
- `relationshipType`: String with default "default" (50 chars max)
- `metadata`: Optional JSON string for additional data
- `createdAt`: Timestamp

## API Endpoints

### Foo Routes
- `GET /api/foo` - List all foo items
- `GET /api/foo/:id` - Get foo by ID
- `POST /api/foo` - Create new foo
- `PUT /api/foo/:id` - Update foo
- `DELETE /api/foo/:id` - Delete foo

### Bar Routes
- `GET /api/bar` - List all bar items with foo details
- `GET /api/bar/:id` - Get bar by ID with foo details
- `POST /api/bar` - Create new bar
- `PUT /api/bar/:id` - Update bar
- `DELETE /api/bar/:id` - Delete bar
- `GET /api/foo/:fooId/bars` - Get all bars for a specific foo

### FooBar Relationship Routes
- `GET /api/foo-bar` - List all foo-bar relationships
- `POST /api/foo-bar` - Create new foo-bar relationship
- `DELETE /api/foo-bar/:id` - Delete foo-bar relationship
- `GET /api/foo/:fooId/relationships` - Get relationships for a foo
- `GET /api/bar/:barId/relationships` - Get relationships for a bar

### Utility Routes
- `GET /` - API information
- `GET /health` - Health check

## Getting Started

### Prerequisites
- Node.js (v18 or higher)
- Docker and Docker Compose
- pnpm (recommended)

### Installation

1. **Install dependencies**:
   ```bash
   pnpm install
   ```

2. **Start the database**:
   ```bash
   pnpm db:setup
   ```

3. **Generate and run migrations**:
   ```bash
   pnpm db:generate
   pnpm db:migrate
   ```

4. **Seed the database** (optional):
   ```bash
   pnpm db:seed
   ```

5. **Start the development server**:
   ```bash
   pnpm dev
   ```

The service will be available at `http://localhost:8081`.

## Database Management

### Available Scripts

- `pnpm db:setup` - Start PostgreSQL with Docker
- `pnpm db:stop` - Stop the database
- `pnpm db:reset` - Reset database (removes all data!)
- `pnpm db:generate` - Generate new migrations
- `pnpm db:migrate` - Run pending migrations
- `pnpm db:seed` - Seed database with sample data
- `pnpm db:studio` - Open Drizzle Studio for database management

### Database Configuration

The service uses PostgreSQL running on port 5433 (to avoid conflicts with other services). You can modify the connection string in:
- `drizzle.config.ts`
- `src/database/connection.ts`
- `docker-compose.yml`

## Development

### Project Structure

```
src/
├── database/
│   ├── connection.ts    # Database connection setup
│   └── schema.ts        # Drizzle schema definitions
├── routes/
│   ├── foo.ts          # Foo entity routes
│   ├── bar.ts          # Bar entity routes
│   └── fooBar.ts       # FooBar relationship routes
├── scripts/
│   ├── migrate.ts      # Migration script
│   └── seed.ts         # Database seeding script
└── server.ts           # Main server file
```

### Adding New Fields

1. Update the schema in `src/database/schema.ts`
2. Generate migration: `pnpm db:generate`
3. Run migration: `pnpm db:migrate`
4. Update routes and validation schemas as needed

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `PORT`: Server port (default: 8081)
- `HOST`: Server host (default: 0.0.0.0)
- `NODE_ENV`: Environment (development/production)

## Example Usage

### Create a Foo
```bash
curl -X POST http://localhost:8081/api/foo \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Foo",
    "description": "A sample foo entity",
    "status": "active",
    "priority": 1
  }'
```

### Create a Bar
```bash
curl -X POST http://localhost:8081/api/bar \
  -H "Content-Type: application/json" \
  -d '{
    "fooId": "uuid-of-foo",
    "value": 42,
    "label": "My Bar",
    "notes": "A sample bar entity"
  }'
```

### Create a FooBar Relationship
```bash
curl -X POST http://localhost:8081/api/foo-bar \
  -H "Content-Type: application/json" \
  -d '{
    "fooId": "uuid-of-foo",
    "barId": "uuid-of-bar",
    "relationshipType": "special",
    "metadata": "{\"strength\": \"strong\"}"
  }'
```

## Customization

This service is designed to be generic and easily customizable:

1. **Rename Entities**: Replace `foo` and `bar` with your domain-specific names
2. **Add Fields**: Extend the schema with additional fields
3. **Business Logic**: Add validation, business rules, and custom endpoints
4. **Authentication**: Integrate with your authentication system
5. **Permissions**: Add role-based access control

## License

This project is licensed under the MIT License. 