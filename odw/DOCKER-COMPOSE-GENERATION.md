# Docker Compose Generation Flow for ODW

This document explains how Docker Compose files and overrides are generated when running `bun run odw:dev`.

## Overview

The ODW system uses a dynamic Docker Compose configuration that adapts based on whether services are local or external (PaaS). The `render-config.sh` script analyzes environment variables and generates appropriate overrides.

## Configuration Flow

```mermaid
flowchart TD
    A[bun run odw:dev] --> B[data-warehouse/scripts/dev.sh]
    B --> C[render-config.sh]
    C --> D[Load .env file]
    D --> E[Set default values]
    E --> F[Check ClickHouse Host]
    F --> G{MOOSE_CLICKHOUSE_HOST}
    G -->|localhost/127.*| H[ClickHouse: Local]
    G -->|External Host| I[ClickHouse: External]
    
    E --> J[Check Temporal DB Host]
    J --> K{TEMPORAL_DB_HOST}
    K -->|localhost/127.*| L[Temporal DB: Local]
    K -->|External Host| M[Temporal DB: External]
    
    H --> N[Generate moose.config.toml]
    I --> N
    L --> N
    M --> N
    
    N --> O[Generate Docker Compose Override]
    O --> P[Start Moose CLI]
    P --> Q[Moose generates base docker-compose.yml]
    Q --> R[Apply override configuration]
    R --> S[Start containers based on profiles]
```

## Environment Variable Analysis

### ClickHouse Configuration
```mermaid
flowchart LR
    A[MOOSE_CLICKHOUSE_HOST] --> B{Host Value}
    B -->|localhost<br/>127.*<br/>clickhousedb| C[Local ClickHouse]
    B -->|ck.mightytech.cn<br/>Other external| D[External ClickHouse]
    
    C --> E[Enable clickhouse profile<br/>Start local containers]
    D --> F[Disable ClickHouse containers<br/>Use external service]
```

### Temporal Configuration
```mermaid
flowchart LR
    A[TEMPORAL_DB_HOST] --> B{Host Value}
    B -->|localhost<br/>127.*<br/>postgresql| C[Local PostgreSQL]
    B -->|marspbi.postgres...<br/>Other external| D[External PostgreSQL]
    
    C --> E[Enable temporal-db profile<br/>Start local PostgreSQL]
    D --> F[Disable PostgreSQL container<br/>Configure external connection]
    
    F --> G[Update Temporal service env:<br/>POSTGRES_SEEDS=external_host]
```

## Docker Compose Override Generation

### Current Configuration (.env)
```bash
# ClickHouse: External PaaS
MOOSE_CLICKHOUSE_HOST=ck.mightytech.cn
MOOSE_CLICKHOUSE_HOST_PORT=8443

# Temporal: Hybrid Configuration (Local server + External database)
TEMPORAL_DB_HOST=marspbi.postgres.database.chinacloudapi.cn
TEMPORAL_DB_PORT=5432

# Temporal Server: Local Temporal service
MOOSE_TEMPORAL_HOST=localhost  # ✅ Correct: Points to local Temporal server
```

### Generated Override Structure (Current Setup)

```mermaid
flowchart TD
    A[docker-compose.override.yml] --> B[ClickHouse Services]
    A --> C[Temporal Services]
    
    B --> D{ClickHouse External?}
    D -->|Yes ✅| E[✅ Disable clickhousedb<br/>✅ Disable clickhouse-keeper<br/>✅ Remove port mappings<br/>Use ck.mightytech.cn]
    D -->|No| F[Enable clickhouse profile<br/>Start local containers]
    
    C --> G{Temporal DB External?}
    G -->|Yes ✅| H[✅ Disable postgresql container<br/>✅ Configure external DB connection<br/>✅ Start local Temporal server]
    G -->|No| I[Enable temporal-db profile<br/>Start local PostgreSQL]
    
    H --> J[✅ temporal service:<br/>- POSTGRES_SEEDS=marspbi.postgres...<br/>- No postgresql dependency<br/>- Connects to external DB]
    I --> K[temporal service:<br/>- depends_on: postgresql<br/>- Local connection]
    
    style E fill:#c8e6c9
    style H fill:#c8e6c9
    style J fill:#c8e6c9
```

## Service Profiles and Dependencies

### Hybrid Architecture (Current Config)
```mermaid
graph TB
    subgraph "External PaaS Services"
        EXT_CH[ClickHouse<br/>ck.mightytech.cn:8443<br/>Database: finops-odw]
        EXT_PG[PostgreSQL<br/>marspbi.postgres...cn:5432<br/>Temporal Metadata Storage]
    end
    
    subgraph "Local Docker Services"
        REDIS[Redis<br/>localhost:6379]
        REDPANDA[Redpanda<br/>localhost:19092]
        TEMPORAL[Temporal Server<br/>localhost:17233]
        TEMPORAL_UI[Temporal UI<br/>localhost:8081]
        TEMPORAL_ADMIN[Temporal Admin Tools]
        MOOSE[Moose API<br/>localhost:4200]
        MINIO[MinIO<br/>localhost:9500/9501]
        KAFDROP[Kafdrop UI<br/>localhost:9999]
        STREAMLIT[Streamlit Frontend<br/>localhost:8501]
    end
    
    TEMPORAL -.->|Metadata Storage| EXT_PG
    MOOSE -.->|Analytics Queries| EXT_CH
    MOOSE --> TEMPORAL
    MOOSE --> REDIS
    MOOSE --> REDPANDA
    TEMPORAL_UI --> TEMPORAL
    TEMPORAL_ADMIN --> TEMPORAL
    STREAMLIT --> MOOSE
    KAFDROP --> REDPANDA
    
    style EXT_CH fill:#e1f5fe
    style EXT_PG fill:#e1f5fe
    style TEMPORAL fill:#f3e5f5
    style MOOSE fill:#e8f5e8
```

### Docker Compose Profiles Used
```mermaid
flowchart LR
    A[Profiles Enabled] --> B[temporal]
    A --> C[No clickhouse profile]
    A --> D[No temporal-db profile]
    
    B --> E[temporal service<br/>temporal-ui<br/>temporal-admin-tools]
    C --> F[ClickHouse containers disabled]
    D --> G[PostgreSQL container disabled]
```

## Generated Files

### 1. moose.config.toml Generation Process

The `moose.config.toml` file is generated from `moose.config.template.toml` using environment variable substitution:

```mermaid
flowchart LR
    A[moose.config.template.toml] --> B[envsubst]
    C[.env variables] --> B
    B --> D[moose.config.toml]
    D --> E[Moose CLI reads config]
    E --> F[Generates base docker-compose.yml]
```

#### Template Variables Substitution:
```toml
# Template (moose.config.template.toml)
[clickhouse_config]
host = "${MOOSE_CLICKHOUSE_HOST}"
host_port = ${MOOSE_CLICKHOUSE_HOST_PORT}
use_ssl = ${MOOSE_CLICKHOUSE_USE_SSL}

[temporal_config]
temporal_host = "${MOOSE_TEMPORAL_HOST}"
db_user = "${MOOSE_TEMPORAL_DB_USER}"
db_password = "${MOOSE_TEMPORAL_DB_PASSWORD}"
```

#### Generated Result (moose.config.toml):
```toml
# Generated from .env variables
[clickhouse_config]
host = "ck.mightytech.cn"           # External ClickHouse PaaS
host_port = 8443
use_ssl = true

[temporal_config]
temporal_host = "localhost"         # Local Temporal server
db_user = "maradmin"               # External PostgreSQL credentials
db_password = "XQdaYh^4q&K9"
```

#### Key Configuration Sections:
- **`clickhouse_config`**: Tells Moose where to connect for analytics queries
- **`temporal_config`**: Configures Temporal workflow engine connection
- **`redpanda_config`**: Message broker for streaming (always local)
- **`redis_config`**: Caching layer (always local)
- **`s3_config`**: Object storage for unstructured data

### 2. How moose.config.toml Influences Docker Compose Generation

```mermaid
flowchart TD
    A[moose.config.toml] --> B[Moose CLI reads config]
    B --> C[Generates base docker-compose.yml]
    C --> D[render-config.sh analyzes .env]
    D --> E[Generates docker-compose.override.yml]
    E --> F[Docker Compose merges files]
    F --> G[Final container configuration]
    
    subgraph "Config Analysis"
        H[clickhouse_config.host] --> I{External Host?}
        I -->|Yes| J[Disable ClickHouse containers]
        I -->|No| K[Enable ClickHouse containers]
        
        L[temporal_config.temporal_host] --> M{localhost?}
        M -->|Yes| N[Enable local Temporal server]
        M -->|No| O[Configure external Temporal]
    end
```

#### Base Docker Compose (Generated by Moose CLI):
Moose CLI reads `moose.config.toml` and generates a base `docker-compose.yml` with all possible services:

```yaml
# Generated by moose-cli based on moose.config.toml
services:
  clickhousedb:
    image: clickhouse/clickhouse-server:25.6
    ports:
      - "18123:8123"  # Uses MOOSE_CLICKHOUSE_HOST_PORT from config
  
  temporal:
    image: temporalio/auto-setup:1.22.3
    ports:
      - "17233:7233"  # Uses MOOSE_TEMPORAL_PORT from config
    environment:
      - POSTGRES_USER=${MOOSE_TEMPORAL_DB_USER}  # From config
```

### 3. docker-compose.override.yml (Generated by render-config.sh)

The override file modifies the base configuration based on external service detection:

```yaml
# Generated override based on .env analysis
services:
  # ClickHouse disabled - using external ck.mightytech.cn
  clickhousedb:
    deploy:
      replicas: 0
    profiles:
      - disabled-never-start
  
  # PostgreSQL disabled - using external marspbi.postgres...
  postgresql:
    profiles:
      - disabled
  
  # Temporal configured for external DB but local server
  temporal:
    profiles:
      - temporal
    depends_on: []  # No local PostgreSQL dependency
    environment:
      - POSTGRES_SEEDS=marspbi.postgres.database.chinacloudapi.cn
      - POSTGRES_USER=maradmin
      - POSTGRES_PWD=XQdaYh^4q&K9
```

## Configuration Validation

### Current Configuration Status
```mermaid
flowchart TD
    A[MOOSE_TEMPORAL_HOST] --> B[localhost]
    B --> C[✅ Points to local Temporal server]
    C --> D[Temporal server runs in Docker]
    
    E[TEMPORAL_DB_HOST] --> F[marspbi.postgres.database.chinacloudapi.cn]
    F --> G[✅ Points to external PostgreSQL]
    G --> H[Temporal connects to external database for metadata]
    
    I[Hybrid Architecture] --> J[Local Temporal Server<br/>+ External PostgreSQL]
    J --> K[✅ Optimal Configuration]
```

### Final Configuration
```bash
# In .env file - CURRENT CORRECT SETUP:
MOOSE_TEMPORAL_HOST=localhost                                    # ✅ Local Temporal server
TEMPORAL_DB_HOST=marspbi.postgres.database.chinacloudapi.cn     # ✅ External PostgreSQL for Temporal metadata
MOOSE_CLICKHOUSE_HOST=ck.mightytech.cn                          # ✅ External ClickHouse PaaS
```

## Complete Configuration Flow

### Configuration to Container Mapping

```mermaid
flowchart TD
    subgraph "Configuration Generation"
        A[.env] --> B[render-config.sh]
        B --> C[moose.config.toml]
        B --> D[docker-compose.override.yml]
    end
    
    subgraph "Moose CLI Processing"
        C --> E[moose-cli dev]
        E --> F[Base docker-compose.yml]
    end
    
    subgraph "Docker Compose Merge"
        F --> G[Docker Compose]
        D --> G
        G --> H[Final Configuration]
    end
    
    subgraph "Container Decisions"
        H --> I{ClickHouse Config}
        I -->|host=external| J[Skip ClickHouse containers]
        I -->|host=localhost| K[Start ClickHouse containers]
        
        H --> L{Temporal Config}
        L -->|temporal_host=localhost<br/>db_host=external| M[Local Temporal + External DB]
        L -->|temporal_host=localhost<br/>db_host=localhost| N[Full Local Temporal Stack]
    end
```

### Container Startup Sequence

```mermaid
sequenceDiagram
    participant Dev as bun run odw:dev
    participant Script as dev.sh
    participant Render as render-config.sh
    participant Moose as moose-cli
    participant Docker as Docker Compose
    
    Dev->>Script: Execute
    Script->>Render: Generate config files
    
    Note over Render: Step 1: Template Processing
    Render->>Render: Load .env variables
    Render->>Render: envsubst moose.config.template.toml
    Render->>Render: Generate moose.config.toml
    
    Note over Render: Step 2: Service Detection
    Render->>Render: Analyze MOOSE_CLICKHOUSE_HOST
    Render->>Render: Analyze TEMPORAL_DB_HOST
    Render->>Render: Generate docker-compose.override.yml
    
    Script->>Moose: moose-cli dev
    
    Note over Moose: Step 3: Base Generation
    Moose->>Moose: Read moose.config.toml
    Moose->>Docker: Generate base docker-compose.yml
    
    Note over Docker: Step 4: Configuration Merge
    Docker->>Docker: Merge base + override files
    Docker->>Docker: Apply profiles: temporal
    Docker->>Docker: Skip disabled services
    
    Note over Docker: Step 5: Container Startup
    Docker->>Docker: Start Redis (local)
    Docker->>Docker: Start Redpanda (local)
    Docker->>Docker: Start Temporal (local → external DB)
    Docker->>Docker: Start Temporal UI (local)
    Docker->>Docker: Skip ClickHouse (external)
    Docker->>Docker: Skip PostgreSQL (external)
```

### Configuration Impact on Services

| Service | Config Source | Decision Logic | Result |
|---------|---------------|----------------|---------|
| **ClickHouse** | `MOOSE_CLICKHOUSE_HOST=ck.mightytech.cn` | External host detected | ❌ Container disabled |
| **PostgreSQL** | `TEMPORAL_DB_HOST=marspbi.postgres...` | External host detected | ❌ Container disabled |
| **Temporal Server** | `MOOSE_TEMPORAL_HOST=localhost` | Local host specified | ✅ Container enabled |
| **Redis** | Hard-coded `localhost:6379` | Always local | ✅ Container enabled |
| **Redpanda** | Hard-coded `localhost:19092` | Always local | ✅ Container enabled |
| **Temporal UI** | Depends on Temporal Server | Temporal enabled | ✅ Container enabled |

## Summary

The ODW system intelligently configures Docker Compose based on environment variables to create an optimal hybrid architecture:

### ✅ **Current Configuration Benefits:**
- **External ClickHouse PaaS**: Production-grade analytics database with existing data
- **External PostgreSQL PaaS**: Reliable metadata storage for Temporal workflows  
- **Local Temporal Server**: Fast, reliable workflow engine without external dependencies
- **Local Supporting Services**: Redis, Redpanda, MinIO for development flexibility

### **Service Profiles Enabled:**
- `temporal` - Enables Temporal server, UI, and admin tools
- No `clickhouse` profile - ClickHouse containers disabled
- No `temporal-db` profile - PostgreSQL container disabled

### **Key Architecture Decisions:**
1. **Hybrid Approach**: Combines PaaS reliability with local development speed
2. **Smart Profiles**: Docker Compose profiles automatically enable/disable services
3. **External Connections**: Temporal and Moose connect to external databases seamlessly
4. **Port Management**: All services use fixed ports to prevent conflicts

### **Configuration Variables:**
- `MOOSE_TEMPORAL_HOST=localhost` ✅ - Temporal server location (local Docker)
- `TEMPORAL_DB_HOST=external` ✅ - Database location (external PaaS)
- `MOOSE_CLICKHOUSE_HOST=external` ✅ - Analytics database (external PaaS)

This setup provides the best balance of performance, reliability, and development experience.