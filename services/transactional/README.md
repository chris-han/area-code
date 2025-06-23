# Transactional Service

A RESTful API service built with Fastify, TypeScript, Drizzle ORM, and PostgreSQL. This service provides transactional operations for users, products, and orders with full CRUD functionality.

## Features

- 🚀 **Fastify** - Fast and low overhead web framework
- 🔒 **TypeScript** - Full type safety
- 🗃️ **Drizzle ORM** - Type-safe SQL toolkit
- 🐘 **PostgreSQL** - Robust relational database
- 🔄 **Database Transactions** - ACID compliance for complex operations
- ✅ **Zod Validation** - Runtime type validation
- 📝 **Comprehensive API** - Full CRUD operations
- 🐳 **Docker Support** - Easy development setup

## Quick Start

### 1. Prerequisites

- Node.js 18+
- pnpm
- Docker and Docker Compose
- Git

### 2. Setup

```bash
# Install dependencies
pnpm install

# Start the database
pnpm db:setup

# Wait for database to be ready, then run migrations
pnpm db:generate
pnpm db:migrate

# Start the development server
pnpm dev
```

### 3. Environment Variables

Copy `.env.template` to `.env` and update the values:

```bash
cp .env.template .env
```

### 4. Database Management

```bash
# Start database
pnpm db:setup

# Stop database
pnpm db:stop

# Reset database (removes all data)
pnpm db:reset

# Generate migrations
pnpm db:generate

# Run migrations
pnpm db:migrate

# Open Drizzle Studio
pnpm db:studio
```

## API Endpoints

The API is available at `http://localhost:8080`

### General Endpoints

- `GET /` - API information
- `GET /health` - Health check

### Users

- `GET /api/users` - List all users
- `GET /api/users/:id` - Get user by ID
- `POST /api/users` - Create new user
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user

### Products

- `GET /api/products` - List all products
- `GET /api/products/:id` - Get product by ID
- `POST /api/products` - Create new product
- `PUT /api/products/:id` - Update product
- `DELETE /api/products/:id` - Delete product

### Orders

- `GET /api/orders` - List all orders with user information
- `GET /api/orders/:id` - Get order by ID with full details
- `POST /api/orders` - Create new order with items (transactional)
- `PUT /api/orders/:id/status` - Update order status

## Example Usage

### Create a User

```bash
curl -X POST http://localhost:8080/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "firstName": "John",
    "lastName": "Doe"
  }'
```

### Create a Product

```bash
curl -X POST http://localhost:8080/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "description": "High-performance laptop",
    "price": 99999
  }'
```

### Create an Order

```bash
curl -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user-uuid-here",
    "items": [
      {
        "productId": "product-uuid-here",
        "quantity": 2
      }
    ]
  }'
```

## Database Schema

### Users Table
- `id` - UUID (Primary Key)
- `email` - String (Unique)
- `firstName` - String (Optional)
- `lastName` - String (Optional)
- `isActive` - Boolean (Default: true)
- `createdAt` - Timestamp
- `updatedAt` - Timestamp

### Products Table
- `id` - UUID (Primary Key)
- `name` - String
- `description` - Text (Optional)
- `price` - Integer (in cents)
- `isAvailable` - Boolean (Default: true)
- `createdAt` - Timestamp
- `updatedAt` - Timestamp

### Orders Table
- `id` - UUID (Primary Key)
- `userId` - UUID (Foreign Key to Users)
- `status` - String (pending, confirmed, processing, shipped, delivered, cancelled)
- `totalAmount` - Integer (in cents)
- `createdAt` - Timestamp
- `updatedAt` - Timestamp

### Order Items Table
- `id` - UUID (Primary Key)
- `orderId` - UUID (Foreign Key to Orders)
- `productId` - UUID (Foreign Key to Products)
- `quantity` - Integer
- `pricePerItem` - Integer (in cents, snapshot at time of order)
- `createdAt` - Timestamp

## Development

### Scripts

- `pnpm dev` - Start development server with hot reload
- `pnpm build` - Build for production
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint

### Docker Services

The `docker-compose.yml` includes:
- PostgreSQL database
- PostgREST API
- GoTrue authentication

### Architecture

```
src/
├── database/
│   ├── connection.ts    # Database connection setup
│   └── schema.ts       # Drizzle schema definitions
├── routes/
│   ├── users.ts        # User CRUD operations
│   ├── products.ts     # Product CRUD operations
│   └── orders.ts       # Order operations with transactions
├── scripts/
│   └── migrate.ts      # Database migration script
└── server.ts           # Main Fastify server
```

## Production Considerations

1. **Environment Variables**: Use a secure secret manager
2. **Database Connection**: Configure connection pooling
3. **Logging**: Set up structured logging
4. **Monitoring**: Add health checks and metrics
5. **Security**: Implement authentication and authorization
6. **Rate Limiting**: Add rate limiting for API endpoints
7. **Error Handling**: Improve error messages and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT 