# ODW Cleanup Guide

## Enhanced Cleanup System

The `bun run odw:dev:clean` command provides comprehensive cleanup of all ODW services, containers, and ports.

## What Gets Cleaned

### 🐳 **Docker Containers**
- `data-warehouse-temporal-1` - Main Temporal server
- `data-warehouse-temporal-admin-tools-1` - Temporal admin tools
- `data-warehouse-temporal-ui-1` - Temporal web UI
- `data-warehouse-postgresql-1` - PostgreSQL database for Temporal
- `data-warehouse-clickhousedb-1` - ClickHouse database
- `data-warehouse-clickhouse-keeper-1` - ClickHouse keeper
- `data-warehouse-redpanda-1` - Redpanda message broker
- `data-warehouse-redis-1` - Redis cache
- `data-warehouse-kafdrop` - Kafdrop UI
- `data-warehouse-minio` - MinIO storage

### 🌐 **Docker Networks**
- `data-warehouse_temporal-network`
- `data-warehouse_clickhouse-network` 
- `data-warehouse_default`

### 🔌 **Ports Cleaned**

#### Main ODW Service Ports:
- **4200** - Moose API
- **8501** - Streamlit Frontend
- **9999** - Kafdrop UI
- **9500** - MinIO API
- **9501** - MinIO Console

#### Temporal Ports:
- **17233** - Temporal Server (external)
- **7233** - Temporal Internal
- **8081** - Temporal UI (external)
- **8080** - Temporal UI Internal
- **5432** - PostgreSQL (Temporal database)

#### Infrastructure Ports:
- **18123** - ClickHouse HTTP
- **9000** - ClickHouse Native
- **19092** - Redpanda
- **6379** - Redis

## Usage Commands

```bash
# Full cleanup (recommended before starting)
bun run odw:dev:clean

# Check port status
bun run odw:check-ports

# Start ODW services
bun run odw:dev
```

## Cleanup Process

1. **Moose Infrastructure**: Runs `moose-cli clean` to clean Moose-managed resources
2. **Temporal Containers**: Stops and removes all Temporal-related containers
3. **Docker Networks**: Removes ODW-specific Docker networks
4. **Port Cleanup**: Terminates all processes using ODW ports
   - Tries graceful termination first (SIGTERM)
   - Force kills if needed after 10 seconds (SIGKILL)
5. **Service-Specific Cleanup**: Each service cleans its own resources

## Troubleshooting

### If cleanup fails:
```bash
# Manual Docker cleanup
docker stop $(docker ps -q --filter "name=data-warehouse-")
docker rm $(docker ps -aq --filter "name=data-warehouse-")
docker network prune -f

# Manual port cleanup
sudo lsof -ti :4200,:8501,:9999,:9500,:9501 | xargs -r kill -9
```

### If ports are still in use:
```bash
# Check what's using specific ports
lsof -i :4200
lsof -i :8501

# Kill specific processes
kill -9 <PID>
```

## Port Verification

The cleanup system ensures all ODW ports are freed before starting new services, preventing "port already in use" errors.

Run `bun run odw:check-ports` anytime to verify port status.