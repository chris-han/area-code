# DataLens Platform for Azure Billing Intelligence

This service provides the DataLens-based frontend platform for Azure Billing Intelligence (ABI) with FOCUS-compliant data visualization and custom extensions.

## Overview

DataLens is configured to connect to the ClickHouse database using credentials from the data-warehouse service and provides:

- **FOCUS-compliant dashboards** for Azure billing analytics
- **Custom ABI extensions** with specialized widgets
- **Port conflict resolution** with Temporal UI through reverse proxy
- **Real-time data visualization** from ClickHouse analytics

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │ DataLens Frontend│   │ DataLens Backend│
│   Port: 9080    │────│   Port: 8081     │───│   Port: 8082    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│Existing Temporal│    │  ABI Extensions │    │   ClickHouse    │
│ UI (Port 8080)  │    │ FOCUS Widgets   │    │ External PaaS   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                             │
         │              ┌─────────────────┐            │
         └──────────────│Existing Temporal│────────────┘
                        │ PostgreSQL      │
                        │ (Shared DB)     │
                        └─────────────────┘
```

## Port Configuration & Infrastructure Reuse

DataLens integrates with existing data-warehouse infrastructure:

- **DataLens Frontend**: Port 8081
- **DataLens Backend**: Port 8082  
- **Nginx Reverse Proxy**: Port 9080 (unified access)
- **Temporal UI**: Port 8080 (existing data-warehouse service)
- **PostgreSQL**: Reuses existing Temporal PostgreSQL (no new container)
- **ClickHouse**: External PaaS (shared with data-warehouse)

## Quick Start

### 1. Setup DataLens Platform

```bash
# Initialize DataLens repositories and configuration
./scripts/setup-minimal.sh
```

This will:
- Load ClickHouse configuration from ../data-warehouse/.env
- Load Temporal PostgreSQL configuration from ../data-warehouse/.env
- Create DataLens configuration files
- Configure integration with existing infrastructure

### 2. Initialize Database

```bash
# Create DataLens database in existing Temporal PostgreSQL
./scripts/init-database.sh
```

This will:
- Create `datalens` database in existing Temporal PostgreSQL
- Create `abi_registry` database for plugin metadata
- Set up plugin registry schema
- Verify connectivity to existing infrastructure

### 3. Clone Repositories (if needed)

```bash
# Clone DataLens repositories for full customization
git clone --depth 1 https://github.com/chris-han/datalens-backend.git datalens-backend
git clone --depth 1 https://github.com/chris-han/datalens-ui.git frontend/datalens-ui
```

### 4. Integrate ABI Extensions

```bash
# Integrate ABI extensions with DataLens repositories
./scripts/integrate-abi.sh
```

### 5. Build Platform

```bash
# Build DataLens with ABI extensions
./scripts/build.sh
```

### 6. Start Development Environment

```bash
# Start DataLens services (connects to existing data-warehouse infrastructure)
./scripts/dev.sh
```

### 7. Access Interfaces

- **DataLens Platform**: http://localhost:8081
- **Unified Interface**: http://localhost:9080
- **Temporal UI**: http://localhost:8080 (existing data-warehouse service)
- **Temporal UI via Proxy**: http://localhost:9080/temporal
- **DataLens API**: http://localhost:8082

## Configuration

### ClickHouse Connection

DataLens automatically loads configuration from `../data-warehouse/moose.config.toml`:

```toml
[clickhouse_config]
host = "ck.mightytech.cn"
host_port = 8443
user = "finops"
password = "cU2f947&9T{6d"
db_name = "finops-odw"
use_ssl = true

[temporal_config]
db_user = "temporal"
db_password = "temporal"
db_port = 5432
temporal_host = "localhost"
temporal_port = 7233
ui_port = 8080
```

### DataLens Configuration

Configuration is stored in `config/datalens.env`:

```env
DATALENS_PORT=8081
DATALENS_BACKEND_PORT=8082
ENABLE_ABI_EXTENSIONS=true
FOCUS_SPECIFICATION_VERSION=1.0
```

## ABI Extensions

### FOCUS-Compliant Widgets

Located in `frontend/abi-extensions/src/widgets/`:

- **FOCUSCostTrendWidget**: Interactive cost trend analysis
- **ResourceUtilizationHeatmap**: Resource efficiency visualization  
- **ServiceCategoryBreakdown**: Service cost distribution
- **BudgetTrackingWidget**: Budget vs actual spending

### Pre-built Dashboards

Configured in `config/dashboards.yaml`:

- **Cost Optimization Dashboard**: Comprehensive cost analysis
- **Resource Utilization Dashboard**: Efficiency metrics
- **Budget Tracking Dashboard**: Budget monitoring and forecasting

### Custom Extensions Development

```typescript
// Example ABI extension widget
import { FOCUSBillingData } from '../types/focus-types';
import { buildFOCUSQuery } from '../utils/focus-helpers';

const MyCustomWidget: React.FC = () => {
  // Widget implementation using FOCUS data types
};
```

## Data Sources

### FOCUS Billing Data

Primary dataset: `focus_billing_data`

Key fields:
- `billing_account_id`: Account identifier
- `usage_date`: Usage date
- `billed_cost`: Cost amount
- `service_category`: Service category
- `resource_type`: Resource type
- `region`: Geographic region

### Dimension Tables

- `focus_service_categories`: Service category lookup
- `focus_resource_types`: Resource type lookup

## Development

### Hot Reload

ABI extensions support hot reload during development:

```bash
# Watch for changes in ABI extensions
cd frontend/abi-extensions
bun run dev
```

### Adding New Widgets

1. Create widget in `frontend/abi-extensions/src/widgets/`
2. Export from `frontend/abi-extensions/src/index.ts`
3. Add to dashboard configuration in `config/dashboards.yaml`
4. Rebuild: `bun run build`

### Custom Queries

Use FOCUS helper functions for consistent querying:

```typescript
import { buildFOCUSQuery } from '../utils/focus-helpers';

const query = buildFOCUSQuery({
  dateRange: { start: '2024-01-01', end: '2024-01-31' },
  subscriptionIds: ['sub-123'],
  serviceCategories: ['Compute']
});
```

## Troubleshooting

### Port Conflicts

If you encounter port conflicts:

1. Check running services: `docker ps`
2. Stop conflicting services: `docker-compose down`
3. Use unified access via port 9080

### ClickHouse Connection Issues

1. Verify data-warehouse moose.config.toml file exists
2. Check ClickHouse credentials and connectivity in moose.config.toml
3. Review DataLens backend logs: `docker-compose logs datalens-backend`

### ABI Extensions Not Loading

1. Ensure extensions are built: `cd frontend/abi-extensions && bun run build`
2. Check frontend logs: `docker-compose logs datalens-frontend`
3. Verify ENABLE_ABI_EXTENSIONS=true in configuration

## Scripts

- `./scripts/setup.sh`: Initialize DataLens platform
- `./scripts/build.sh`: Build platform and extensions
- `./scripts/dev.sh`: Start development environment
- `./scripts/dev-clean.sh`: Clean and restart environment

## Integration with ABI System

DataLens integrates with other ABI components:

- **ClickHouse**: Primary data source for analytics
- **Temporal UI**: Accessible via reverse proxy at /temporal
- **Plugin System**: Visualizes plugin marketplace data
- **Moose API**: Backend integration for real-time data

## Production Deployment

For production deployment:

1. Update configuration for production ClickHouse
2. Configure SSL certificates for HTTPS
3. Set up proper authentication and authorization
4. Configure monitoring and logging
5. Use production-grade reverse proxy (nginx/traefik)

## Support

For issues and questions:

1. Check logs: `docker-compose logs`
2. Review configuration files in `config/`
3. Verify ClickHouse connectivity
4. Check ABI system documentation