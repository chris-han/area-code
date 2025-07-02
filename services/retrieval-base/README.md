# Retrieval Base Service

A search service that uses Elasticsearch to enable full-text search for Foo and Bar entities.

## Features

- Full-text search with fuzzy matching
- Filtering by entity properties
- Sorting capabilities
- Bulk indexing support
- Health check endpoint with Elasticsearch status
- OpenAPI/Swagger documentation

## Prerequisites

- Node.js 20+
- pnpm
- Docker and Docker Compose

## Getting Started

### 1. Install Dependencies

```bash
pnpm install
```

### 2. Start Elasticsearch

```bash
pnpm es:setup
```

This will start:
- Elasticsearch on port 9200
- Kibana on port 5601 (for debugging/exploring data)

### 3. Initialize Indices

```bash
pnpm es:init-indices
```

This creates the necessary Elasticsearch indices with proper mappings.

### 4. Seed Sample Data (Optional)

```bash
pnpm es:seed
```

This will populate the indices with sample Foo and Bar documents for testing.

### 5. Start the Service

```bash
pnpm dev
```

The service will be available at `http://localhost:8082`

## API Endpoints

### Search Endpoints

- `GET /api/search` - Search across all entities
- `GET /api/search/foos` - Search only Foo entities  
- `GET /api/search/bars` - Search only Bar entities

#### Query Parameters

- `q` - Search query (optional)
- `from` - Pagination offset (default: 0)
- `size` - Number of results (default: 10, max: 100)
- `sortBy` - Field to sort by
- `sortOrder` - Sort direction: "asc" or "desc" (default: "desc")

#### Filters for Foos
- `status` - Filter by status
- `priority` - Filter by priority number
- `isActive` - Filter by active state (true/false)

#### Filters for Bars
- `fooId` - Filter by associated Foo ID
- `isEnabled` - Filter by enabled state (true/false)

### Other Endpoints

- `GET /` - API information
- `GET /health` - Health check with Elasticsearch status
- `GET /docs` - Swagger UI documentation
- `GET /documentation/json` - OpenAPI JSON specification
- `GET /documentation/yaml` - OpenAPI YAML specification

## Examples

### Search for Foos containing "urgent"
```bash
curl "http://localhost:8082/api/search/foos?q=urgent"
```

### Search for active Foos with high priority
```bash
curl "http://localhost:8082/api/search/foos?status=active&priority=1"
```

### Search for Bars associated with a specific Foo
```bash
curl "http://localhost:8082/api/search/bars?fooId=foo-1"
```

### Search all entities with pagination
```bash
curl "http://localhost:8082/api/search?q=test&from=10&size=20"
```

## Development

### Reset Elasticsearch Data
```bash
pnpm es:reset
```

This will stop containers, remove volumes, and restart with fresh data.

### View Logs
```bash
docker logs retrieval-base-elasticsearch
```

### Access Kibana
Open `http://localhost:5601` in your browser to explore data using Kibana.

## Architecture

The service uses:
- **Fastify** for the REST API framework
- **Elasticsearch** for full-text search and filtering
- **Zod** for request validation
- **@workspace/models** for shared type definitions

The service is designed to be populated via CDC (Change Data Capture) pipelines in production, but includes seeding scripts for development and testing. 