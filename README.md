<img width="1074" height="120" alt="Area Code starter repo powered by Moose — Automated setup with Turborepo" src="https://github.com/user-attachments/assets/a860328a-cb75-41a2-ade4-b9a0624918e0" />

# Starter Applications

Area Code is a starter repo with all the necessary building blocks for a feature-rich, enterprise-ready application that requires specialized infrastructure.

There are two sample applications: [User Facing Analytics](/ufa/) and [Operational Data Warehouse](/odw/). Quickstarts for each of those projects live in the readme of their respective folders ([UFA](/ufa/README.md), [ODW](/odw/README.md)).

## User Facing Analytics

The UFA monorepo is a starter kit for building applications with a multi-modal backend that combines transactional (PostgreSQL), analytical (ClickHouse), and search (Elasticsearch) capabilities. The stack is configured for real-time data synchronization across services.

### UFA Stack:

Backend & Data:

- Transactional: PostgreSQL | Fastify | Drizzle ORM
- Analytical: ClickHouse | Moose (API & Ingest)
- Search: Elasticsearch

Sync & Streaming: Moose Workflows (with Temporal) | Moose Stream (with Redpanda) | Supabase Realtime
Frontend: Vite | React 19 | TypeScript | TanStack (Router, Query, Form) | Tailwind CSS

### Reference Architecture

![Reference architecture: User-facing analytics (with AI)](ufa-architecture-diagram.png)

## Operational Data Warehouse

> ⚠️ **ALPHA RELEASE** - This is an early alpha version under active development. We are actively testing on different machines and adding production deployment capabilities. Use at your own risk and expect breaking changes.

The odw project is a production-ready starter kit for an operational data warehouse, using the Moose framework to ingest data from various sources (Blobs, Events, Logs, FOCUS billing data) into an analytical backend (ClickHouse).

### 🚀 Quick Start

Get up and running in minutes with our automated setup:

```bash
# 1. Ensure Docker Desktop is running

# 2. Install dependencies & start development environment
bun run odw:dev

# 3. Seed databases with sample data
bun run odw:dev:seed

# 4. Open the data warehouse frontend
http://localhost:8501/
```

This will:
- Install all Python dependencies and create virtual environment
- Start the data warehouse service (Moose app) on port 4200
- Start the Streamlit frontend on port 8501
- Launch Kafdrop UI for message queue monitoring on port 9999
- Open the dashboard in your browser automatically

### 🛠️ Startup Script Flow

```mermaid
graph TB
    subgraph "Root Entry Point"
        ROOT["bun run odw:dev<br/>/package.json:26"]
    end

    subgraph "Turbo Orchestration"
        TURBO["turbo run odw:dev --ui=tui<br/>Executes odw:dev task in all workspaces in parallel"]
    end

    subgraph "Data Warehouse Service"
        DW_PKG["data-warehouse/package.json:8<br/>odw:dev → ./app/scripts/dev.sh"]
        DW_SCRIPT["data-warehouse/app/scripts/dev.sh"]
        DW_VENV["Create/Activate Python venv"]
        DW_DEPS["pip install -r requirements.txt"]
        DW_MOOSE["Start Moose CLI on port 4200<br/>.venv/bin/moose-cli dev --port 4200"]
    end

    subgraph "Frontend Service"
        FE_PKG["dw-frontend/package.json:8<br/>odw:dev → ./scripts/dev.sh"]
        FE_SCRIPT["dw-frontend/scripts/dev.sh"]
        FE_VENV["Create/Activate Python venv"]
        FE_DEPS["pip install -r requirements.txt"]
        FE_STREAMLIT["Start Streamlit on port 8501<br/>streamlit run main.py --server.port 8501"]
    end

    subgraph "Infrastructure Services (Docker)"
        DOCKER["Docker Compose Services<br/>Started by Moose CLI"]
        CLICKHOUSE["ClickHouse<br/>Port 18123"]
        REDPANDA["Redpanda<br/>Port 19092"]
        TEMPORAL["Temporal<br/>Port 7233"]
        REDIS["Redis<br/>Port 6379"]
        KAFDROP["Kafdrop UI<br/>Port 9999"]
    end

    ROOT --> TURBO
    TURBO --> DW_PKG
    TURBO --> FE_PKG

    DW_PKG --> DW_SCRIPT
    DW_SCRIPT --> DW_VENV
    DW_VENV --> DW_DEPS
    DW_DEPS --> DW_MOOSE
    DW_MOOSE --> DOCKER

    FE_PKG --> FE_SCRIPT
    FE_SCRIPT --> FE_VENV
    FE_VENV --> FE_DEPS
    FE_DEPS --> FE_STREAMLIT

    DOCKER --> CLICKHOUSE
    DOCKER --> REDPANDA
    DOCKER --> TEMPORAL
    DOCKER --> REDIS
    DOCKER --> KAFDROP

    classDef entry fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef orchestration fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef service fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef infra fill:#fff3e0,stroke:#f57c00,stroke-width:2px

    class ROOT entry
    class TURBO orchestration
    class DW_PKG,DW_SCRIPT,DW_VENV,DW_DEPS,DW_MOOSE,FE_PKG,FE_SCRIPT,FE_VENV,FE_DEPS,FE_STREAMLIT service
    class DOCKER,CLICKHOUSE,REDPANDA,TEMPORAL,REDIS,KAFDROP infra
```

**Key Points:**
- **Parallel Execution**: Turbo runs both `data-warehouse` and `dw-frontend` services concurrently (defined in `turbo.json:42-44`)
- **Virtual Environments**: Each service creates and manages its own Python venv
- **Dependency Installation**: Uses `uv pip install` with intelligent caching:
  1. First attempts to install from uv's local cache with `--offline` flag
  2. If packages not in cache, falls back to fetching from PyPI
  3. This ensures resilience against PyPI timeouts by using cached packages when available
- **Port Allocation**:
  - Data Warehouse (Moose): 4200
  - Frontend (Streamlit): 8501
  - ClickHouse: 18123
  - Redpanda: 19092
  - Temporal: 7233
  - Kafdrop: 9999
- **Docker Management**: Moose CLI automatically starts required Docker services

### ODW Stack

| Category             | Technologies                                        |
| -------------------- | --------------------------------------------------- |
| **Frontend**         | Streamlit, Python 3.12+                            |
| **Backend**          | Moose, Python, FastAPI                             |
| **Database**         | ClickHouse (analytical), PostgreSQL (temporal)     |
| **Message Queue**    | Redpanda (Kafka-compatible)                        |
| **Workflow Engine**  | Temporal                                           |
| **Caching**          | Redis                                              |
| **Data Processing**  | Kafka Python, ClickHouse Connect                   |
| **Infrastructure**   | Docker, Docker Compose                             |
| **Build Tool**       | Python setuptools, pip, Turbo                      |

### 🛠️ Available Scripts

```bash
# Development
bun run odw:dev              # Start all services (parallel)
bun run odw:dev:clean        # Clean all services
bun run odw:dev:seed         # Seed databases with sample data

# Individual services
bun run --cwd odw/apps/dw-frontend dev            # Frontend only
bun run --cwd odw/services/data-warehouse dev     # Data Warehouse only
bun run --cwd odw/services/kafdrop dev            # Kafdrop only
```

### 📁 Project Structure

```
area-code/
├── odw/                      # Operational Data Warehouse
│   ├── services/            # Backend services
│   │   ├── data-warehouse/  # Main Moose data warehouse service
│   │   │   ├── app/
│   │   │   │   ├── apis/    # REST API endpoints for data consumption
│   │   │   │   │   └── focus_billing/  # FOCUS billing consumption APIs
│   │   │   │   ├── blobs/   # Blob data extraction workflows
│   │   │   │   ├── events/  # Events data extraction workflows
│   │   │   │   ├── focus_billing/      # FOCUS billing integration
│   │   │   │   │   ├── temporal_workflow.py # Temporal workflow orchestration
│   │   │   │   │   ├── config.py       # Configuration management
│   │   │   │   │   ├── ddl_generator.py # ClickHouse schema generation
│   │   │   │   │   ├── query_loader.py  # YAML query catalog loader
│   │   │   │   │   └── data_transformer.py # Parquet transformation
│   │   │   │   ├── ingest/  # Data models and stream transformations
│   │   │   │   ├── logs/    # Log data extraction workflows
│   │   │   │   └── views/   # Materialized views for analytics
│   │   │   ├── docs/        # Documentation and walkthrough guides
│   │   │   │   ├── FOCUS_OPERATIONS.md    # FOCUS operations guide
│   │   │   │   └── FOCUS_CONFIGURATION.md # FOCUS configuration reference
│   │   │   ├── app/scripts/dev.sh # Data warehouse startup script
│   │   │   ├── moose.config.toml # Moose framework configuration
│   │   │   └── requirements.txt # Python dependencies
│   │   └── connectors/      # External data source connectors
│   │       └── src/
│   │           ├── blob_connector.py    # Blob storage data connector
│   │           ├── events_connector.py  # Events data connector
│   │           ├── logs_connector.py    # Logs data connector
│   │           └── connector_factory.py # Connector factory pattern
│   └── apps/
│       └── dw-frontend/     # Streamlit web application
│           ├── pages/       # Frontend page components
│           ├── utils/       # Frontend utility functions
│           ├── scripts/dev.sh # Frontend startup script
│           └── main.py      # Streamlit application entry point
├── FOCUS_Spec/              # FOCUS specification files (submodule)
│   └── specification/       # FOCUS 1.2 specification documents
└── focus-mcp-main/          # FOCUS MCP server with query catalog (deprecated)
    └── resources/           # FOCUS query definitions and specifications
        ├── queries/         # Pre-built FOCUS use case queries (YAML)
        └── specifications/  # FOCUS column and attribute definitions
```

### ⚙️ Configuration Workflow

The operational data warehouse uses a layered configuration model so that secrets stay local while shared defaults live in version control.

**Key Files**
- `services/data-warehouse/.env`: Local developer secrets (ignored by git). Populate ClickHouse credentials and any machine-specific overrides here.
- `services/data-warehouse/env.example`: Safe template that documents required variables. Update placeholders when the default setup changes.
- `services/data-warehouse/moose.config.toml`: Moose service configuration checked into git. It references `${CLICKHOUSE_*}` placeholders so no credentials are committed.
- `services/data-warehouse/app/scripts/dev.sh`: Loads `.env`, regenerates `.moose/docker-compose.override.yml`, and starts the Moose service. The generated override injects credentials into Docker and rewrites the ClickHouse `default-user.xml` on each run.
- `services/data-warehouse/app/focus_billing/temporal_workflow.py`: Temporal workflow that ingests FOCUS Parquet files into ClickHouse.

```mermaid
flowchart LR
    A[env.example] -. copy & edit .-> B[.env]
    B -->|load| C[app/scripts/dev.sh]
    C -->|templates| D[.moose/docker-compose.override.yml]
    C -->|reads placeholders| E[moose.config.toml]
    D -->|docker compose up| F[ClickHouse container]
    F -->|entrypoint| G["users.d/default-user.xml"]
```

**Updating ClickHouse credentials**
1. Edit `services/data-warehouse/.env` with the new values (and mirror the placeholder in `env.example` if the team needs to know about the change).
2. Rerun `services/data-warehouse/app/scripts/dev.sh` (or `bun run odw:dev`) so the Docker override and container user config are regenerated.
3. Restart the stack; no direct edits to `moose.config.toml` or Docker volumes are required.

This flow keeps credentials out of source control while ensuring the running containers always receive the latest configuration.

### 🏦 FOCUS Billing Integration

The ODW includes a comprehensive FOCUS (FinOps Open Cost and Usage Specification) billing integration that provides automated ingestion, transformation, and querying of FOCUS 1.2 compliant billing data.

#### 🎯 FOCUS Features

- **FOCUS 1.2 Compliance**: Full specification compliance with automated schema generation
- **Parquet Ingestion**: Batch processing of FOCUS Parquet exports with comprehensive transformation
- **Query Catalog**: 50+ pre-built FOCUS use case queries with parameter binding
- **REST APIs**: Complete consumption APIs for listing, executing, and managing FOCUS queries
- **Workflow Orchestration**: Temporal-based workflows for reliable, resumable data processing
- **Real-time Monitoring**: Comprehensive observability, validation, and error handling

#### 🏗️ FOCUS Architecture

```mermaid
sequenceDiagram
    participant P as Parquet Files<br/>(FOCUS_DATA_ROOT)
    participant D as File Discovery
    participant W as FOCUS Workflow
    participant T as Data Transformer
    participant C as ClickHouse<br/>(focus_cost_usage)
    participant Q as Query Catalog<br/>(YAML Queries)
    participant A as REST APIs
    participant U as Frontend/Client

    Note over P,U: FOCUS Data Ingestion Pipeline

    P->>D: Scan for new Parquet files
    D->>W: Discovered files with metadata
    W->>W: Filter by period/dataset type
    W->>T: Transform file data
    T->>T: PascalCase → snake_case
    T->>T: Type conversions (INT96→DateTime64)
    T->>T: Add computed columns (id, timestamps)
    T->>C: Batch insert (10k rows)
    C->>C: Store in focus_cost_usage &<br/>focus_contract_commitment
    W->>W: Update manifest tracking

    Note over Q,U: FOCUS Query Consumption

    Q->>A: Load YAML query definitions
    U->>A: GET /listFocusUseCases
    A->>U: Available queries with metadata
    U->>A: POST /executeFocusUseCase<br/>{slug, start_date, end_date}
    A->>A: Bind parameters & validate
    A->>C: Execute parameterized SQL
    C->>A: Query results
    A->>U: Paginated response with metrics
```

#### 🚀 Quick Start with FOCUS

1. **Configure FOCUS Data Path**:
   ```bash
   # Set environment variable (optional - has intelligent defaults)
   export FOCUS_DATA_ROOT="/path/to/focus/parquet/files"
   ```

2. **Start ODW with FOCUS Support**:
   ```bash
   bun run odw:dev
   ```

3. **Trigger FOCUS Ingestion**:
   ```bash
   # Via BIA Admin UI (recommended)
   open http://localhost:3000
   # Navigate to Workflows → Start New → FOCUS Billing Ingest

   # Or via direct API call
   curl -X POST http://localhost:4200/workflows/focus_billing_ingest \
     -H "Content-Type: application/json" \
     -d '{"data_root": "/path/to/focus/data", "dry_run": false}'
   ```

4. **Query FOCUS Data**:
   ```bash
   # List available use cases
   curl http://localhost:4200/listFocusUseCases

   # Execute a specific use case
   curl -X POST http://localhost:4200/executeFocusUseCase \
     -H "Content-Type: application/json" \
     -d '{
       "slug": "cost-by-service-monthly",
       "start_date": "2025-07-01",
       "end_date": "2025-07-31",
       "limit": 100
     }'
   ```

#### 📚 FOCUS Documentation

For comprehensive FOCUS billing integration documentation:

- **[FOCUS Operations Guide](odw/services/data-warehouse/docs/FOCUS_OPERATIONS.md)**: Complete operational procedures, DDL management, workflow execution, monitoring, and troubleshooting
- **[FOCUS Configuration Reference](odw/services/data-warehouse/docs/FOCUS_CONFIGURATION.md)**: Detailed configuration options, environment variables, and setup procedures

### 🐛 Troubleshooting

> 🔬 **TESTING STATUS** - We are actively testing on various machine configurations. Currently tested on Mac M3 Pro (18GB RAM), M4 Pro, and M4 Max. We're expanding testing to more configurations.

#### Common Issues

1. **Python Version**: Ensure you're using Python 3.12+ (required for Moose)
2. **Docker**: Make sure Docker Desktop is running before setup
3. **Memory Issues**: ClickHouse and Redpanda require significant memory (4GB+ recommended)
4. **Port Conflicts**: Ensure ports 4200, 8501, 9999, 18123, 19092 are available

**Tested Configurations:**
- ✅ Mac M3 Pro (18GB RAM)
- ✅ Mac M4 Pro
- ✅ Mac M4 Max
- 🔄 More configurations being tested

#### Reset Environment

```bash
# Navigate to data warehouse directory
cd odw/services/data-warehouse

# Clean and restart
./setup.sh reset

# Check status
./setup.sh status
```

### 🚀 Production Deployment (Coming Soon)

> 🚧 **UNDER DEVELOPMENT** - Production deployment capabilities are actively being developed and tested. The current focus is on stability and compatibility across different machine configurations.

We're working on a production deployment strategy that will be available soon.

## 📖 Data Warehouse Service - Detailed Guide

**Learn to build operational data warehouses with Moose** - from real-time ingestion to analytics APIs. This hands-on demonstration showcases how to create a complete data pipeline using Moose primitives, with mocked data sources for easy experimentation and clear examples using simple data models.

### Purpose and Scope

This project is **intentionally focused** on demonstrating key concepts rather than implementing the full reference architecture. It provides enough practical insights and working examples to help developers understand how to:

- Build data ingestion pipelines with Moose
- Implement stream processing workflows
- Create analytical APIs and consumption endpoints
- Integrate multiple data sources into a unified warehouse

### Current Implementation

The current state represents a **simplified but functional** implementation that:

- **Uses mocked data sources**: Logs, Blob (storage), and Events integrations are mocked to make this demo self-contained. Developers can easily adapt these patterns for real data sources by configuring appropriate API keys and endpoints for services they want to integrate.

- **Demonstrates Moose primitives**: The project showcases core Moose concepts including data models, ingestion pipelines, stream functions, materialized views, and consumption APIs.

- **Keeps data models simple**: Uses representative data models to make the data flow easy to follow and understand. Moose makes it straightforward to create much richer and more complex data models as your use case requires.

- **Provides a complete workflow**: From data ingestion through processing to consumption, giving developers a full picture of an operational data warehouse built with Moose.

### Key Technical Capabilities

- **Real-time Data Ingestion**: Stream data processing with RedPanda
- **Multi-Source Data Extraction**: Configurable connectors for various data sources
- **REST API**: Query interface for accessing processed data
- **Scalable Storage**: ClickHouse backend optimized for analytical workloads
- **Stream Processing**: Real-time data transformation and enrichment

### 📚 Presenter Walkthrough

For a detailed walkthrough and presentation guide, see [Presenter - walkthrough docs](odw/services/data-warehouse/docs/README.md).

For a high-level architectural overview, see [high-level-overview.md](odw/services/data-warehouse/docs/high-level-overview.md).

## 🤖 LLM Configuration

This project includes **LLM-powered unstructured data extraction** using Anthropic's Claude API. To enable this feature:

### Required Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude LLM integration

### Setup Instructions

1. **Get an Anthropic API key**: Sign up at [console.anthropic.com](https://console.anthropic.com) and create an API key

2. **Configure LLM settings**: Copy the example configuration and customize as needed:

   ```bash
   cd odw/services/data-warehouse
   cp env.example .env
   ```

   Then edit `.env` to set your API key and configure LLM parameters. See `env.example` for detailed configuration options including batch processing, model selection, and validation settings.

3. **Verify setup**: The LLM service will be automatically initialized when processing unstructured data

### LLM Features

- **Extraction**: Convert unstructured documents (text, PDFs, images) to structured JSON using natural language instructions
- **Validation**: Validate extracted data against business rules specified in plain English
- **Transformation**: Modify and enrich extracted data using natural language transformations
- **Routing**: Intelligently route data based on content analysis
- **Batch Processing**: Process multiple files efficiently with configurable batch sizes for improved performance

#### Configuration Options

The LLM service supports extensive configuration through the `.env` file:

- **Model Selection**: Choose from available Claude models (default: `claude-sonnet-4-20250514`)
- **Processing Parameters**: Configure temperature, token limits, and content size limits
- **Batch Processing**: Enable/disable batch processing and set optimal batch sizes
- **Field Validation**: Enable strict field validation for cleaner data extraction
- **Performance Tuning**: Adjust settings to balance speed vs. accuracy for your use case

#### Fallback Behavior

**Note**: LLM features are optional. When the API key is not configured, the system will:

- Return structured metadata about the content (file type, content preview, processing timestamps)
- Preserve original data with informational notes about the disabled LLM service
- Continue processing without intelligent extraction, validation, or transformation
- Provide clear guidance on enabling LLM features through logging messages

This ensures the system remains functional while providing a clear upgrade path to intelligent processing.

## 🗄️ S3/MinIO Configuration

This project now supports **S3-compatible storage** for unstructured data files, allowing you to read documents, images, and other files directly from S3 buckets or MinIO instances instead of local filesystem paths.

### Configuration in `moose.config.toml`

The S3 configuration section has been added to `moose.config.toml`:

```toml
[s3_config]
# S3/MinIO configuration for unstructured data storage
endpoint_url = "http://localhost:9500"  # MinIO endpoint, set to empty string for AWS S3
access_key_id = "minioadmin"
secret_access_key = "minioadmin"
region_name = "us-east-1"
bucket_name = "unstructured-data"
signature_version = "s3v4"
```

### Setup for Different Storage Types

**For MinIO (Development/Testing):**

- Set `endpoint_url` to your MinIO server (e.g., `http://localhost:9500`)
- Use MinIO admin credentials or create specific access keys
- Ensure the bucket exists in MinIO

**For AWS S3 (Production):**

- Set `endpoint_url` to an empty string `""`
- Use your AWS access key and secret key
- Set the appropriate AWS region
- Ensure the S3 bucket exists and your credentials have read access

### Supported Path Formats

The system now accepts multiple path formats for unstructured data:

```bash
# S3 paths
s3://bucket-name/path/to/file.txt

# MinIO paths
minio://bucket-name/path/to/file.txt
```

### File Type Support

The S3 integration supports multiple file types, all processed using Claude's advanced vision and text processing capabilities:

- **Text files**: `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.html` - Processed using standard LLM text extraction
- **PDF files**: `.pdf` - Processed using Claude's vision capabilities for text extraction and OCR
- **Images**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp` - Processed using Claude's vision capabilities for OCR and content analysis
- **Word documents**: `.doc`, `.docx` - Processed using Claude's document processing capabilities

**Note**: All file processing is handled natively through Claude's API without requiring external OCR libraries, PDF parsers, or document processing tools. This provides a unified, simplified architecture where all unstructured data processing flows through the LLM service.

### Usage in APIs

When submitting unstructured data via the `submitUnstructuredData` API, you can now use S3 paths:

```json
{
  "source_file_path": "minio://unstructured-data/memo_001.txt",
  "extracted_data": "{\"extracted\": \"data\"}"
}
```

## 🦌 Installing Aurora AI Support

Aurora AI is an optional enhancement that extends your copilot's AI capabilities with an MCP server with specialized tools for Moose workflows, ClickHouse queries, and RedPanda integration. This provides intelligent assistance for the creation and maintenance of data warehouse operations.

For setup instructions, see [Aurora docs](https://docs.fiveonefour.com/aurora).
