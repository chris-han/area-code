# FOCUS Billing Data Flow - Complete Architecture

## Overview

This document describes the complete data flow for FOCUS billing integration, from Parquet file ingestion through ClickHouse table creation, data transformation, storage, and consumption via APIs.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Table Creation Flow](#table-creation-flow)
3. [Data Ingestion Flow](#data-ingestion-flow)
4. [Data Consumption Flow](#data-consumption-flow)
5. [Schema Migration Flow](#schema-migration-flow)
6. [Component Interactions](#component-interactions)

---

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        A1[Azure FOCUS Parquet Files]
        A2[FOCUS 1.2 Specification]
    end

    subgraph "Ingestion Layer"
        B1[File Discovery Service]
        B2[Data Transformer]
        B3[Moose HTTP API]
    end

    subgraph "Moose Stack"
        C1[Pydantic Models]
        C2[Redpanda Topics]
        C3[Schema Registry]
    end

    subgraph "Storage Layer"
        D1[ClickHouse FocusCostUsage_0_0]
        D2[Materialized Views]
        D3[Aggregation Tables]
    end

    subgraph "Consumption Layer"
        E1[Consumption APIs]
        E2[FinOps Dashboard]
    end

    subgraph "Orchestration"
        F1[Temporal Workflows]
        F2[BIA Backend API]
    end

    A1 --> B1
    A2 --> F1
    B1 --> B2
    B2 --> B3
    B3 --> C1
    C1 --> C2
    C2 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> E1
    E1 --> E2
    F1 --> B1
    F2 --> F1

    classDef source fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    classDef process fill:#fff4e6,stroke:#ff9800,stroke-width:2px
    classDef storage fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    classDef api fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px

    class A1,A2 source
    class B1,B2,B3,C1,C2,C3 process
    class D1,D2,D3 storage
    class E1,E2,F1,F2 api
```

---

## Table Creation Flow

### Flow 1: Moose Auto-Creation from Pydantic Models

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Code as models.py
    participant Moose as Moose CLI
    participant CH as ClickHouse
    participant RP as Redpanda
    participant HTTP as HTTP Server

    Note over Dev,HTTP: Table Creation via Moose Schema Sync

    Dev->>Code: Define FocusCostUsage Pydantic model
    Code->>Code: Add Field() descriptions<br/>with FOCUS metadata

    Dev->>Code: Create IngestPipeline[FocusCostUsage]<br/>with config

    Note over Code: IngestPipelineConfig(<br/>ingest=True,<br/>stream=True,<br/>table=True,<br/>dead_letter_queue=True<br/>)

    Dev->>Moose: moose-cli dev

    Moose->>Code: Discover IngestPipeline definitions
    Moose->>Moose: Parse Pydantic model schema
    Moose->>Moose: Map Python types → ClickHouse types<br/>(Decimal → Decimal(38,18))

    Moose->>CH: Execute DDL
    Note over CH: CREATE TABLE FocusCostUsage_0_0<br/>ENGINE = MergeTree()<br/>ORDER BY (billing_account_id, charge_period_start)<br/>PARTITION BY toYYYYMM(charge_period_start)

    CH-->>Moose: ✅ Table created

    Moose->>RP: Create topic 'FocusCostUsage'
    RP-->>Moose: ✅ Topic created

    Moose->>HTTP: Register endpoint /ingest/FocusCostUsage
    HTTP-->>Moose: ✅ Endpoint ready

    Moose-->>Dev: ✅ Infrastructure ready<br/>Port 4200 (main), 4201 (consumption)
```

### Detailed Table Creation Steps

```mermaid
flowchart TD
    A[Start: moose-cli dev] --> B[Scan app/ingest/ directory]
    B --> C{"Find IngestPipeline
    definitions?"}

    C -->|Yes| D[Load Pydantic model: FocusCostUsage]
    C -->|No| Z[Exit: No models found]

    D --> E[Parse model fields and types]
    E --> F[Generate ClickHouse DDL]

    F --> G{Table exists?}
    G -->|No| H[CREATE TABLE FocusCostUsage_0_0]
    G -->|Yes| I{Schema changed?}

    I -->|Yes| J[Increment version → FocusCostUsage_0_1]
    I -->|No| K[Use existing table]

    H --> L[Set engine: MergeTree]
    J --> L
    K --> L

    L --> M["Define ORDER BY:
    billing_account_id, charge_period_start"]
    M --> N["Define PARTITION BY:
    toYYYYMM(charge_period_start)"]

    N --> O[Map Pydantic types to ClickHouse]
    O --> P["Type mappings:
    str → String
    Decimal → Decimal(38,18)
    datetime → DateTime64(3)
    Optional → Nullable"]

    P --> Q[Execute DDL on ClickHouse]
    Q --> R[Create Redpanda topic]
    R --> S[Register HTTP endpoint]
    S --> T[Start sync consumer:<br/>Topic → Table]

    T --> U[✅ Ready for ingestion]

    style A fill:#e3f2fd
    style U fill:#c8e6c9
    style Z fill:#ffcdd2
```

---

## Data Ingestion Flow

### Flow 2: Parquet to ClickHouse via Moose

```mermaid
sequenceDiagram
    participant WF as Temporal Workflow
    participant FD as File Discovery
    participant DT as Data Transformer
    participant MA as Moose Adapter
    participant HTTP as Moose HTTP API<br/>(Port 4200)
    participant RP as Redpanda Topic
    participant CH as ClickHouse<br/>FocusCostUsage_0_0

    Note over WF,CH: FOCUS Billing Ingestion Workflow

    WF->>FD: discover_parquet_files()
    FD->>FD: Scan /focus-mcp-main/data/focus/
    FD->>FD: Filter by period (20250701-20250731)
    FD-->>WF: List[ParquetFileInfo] (92 files)

    loop For each Parquet file
        WF->>DT: transform_parquet(file_path)

        DT->>DT: Load with pyarrow.parquet.read_table()
        DT->>DT: Convert to pandas DataFrame

        DT->>DT: Map PascalCase → snake_case<br/>(BillingAccountId → billing_account_id)

        DT->>DT: Convert types:<br/>- Decimal → float (JSON safe)<br/>- DateTime → ISO string<br/>- Boolean → 0/1

        DT->>DT: Generate deterministic ID:<br/>hash(billing_account_id + charge_period_start<br/>+ resource_id + sku_meter)

        DT->>DT: Add audit fields:<br/>source_system='focus_parquet'<br/>ingested_at=now()

        DT-->>WF: TransformationResult<br/>(10,000 rows)

        WF->>MA: ingest_batch(records, batch_size=500)

        loop Batch of 500 rows
            MA->>MA: Validate Pydantic model
            MA->>MA: Serialize to JSON

            MA->>HTTP: POST /ingest/FocusCostUsage<br/>Content-Type: application/json<br/>Body: [{"id": "...", "billing_account_id": "..."}]

            HTTP->>HTTP: Validate schema
            HTTP->>HTTP: Apply transformations

            HTTP->>RP: Publish to 'FocusCostUsage' topic
            RP-->>HTTP: ✅ Ack

            HTTP-->>MA: 200 OK
            MA-->>WF: ✅ Batch ingested (500 rows)
        end

        Note over RP,CH: Background Sync (Moose Consumer)

        RP->>CH: Consume messages (batched)
        CH->>CH: INSERT INTO FocusCostUsage_0_0
        CH-->>RP: ✅ Committed

        WF->>WF: Update manifest:<br/>file_path, checksum, row_count
        WF->>WF: Update stats: files_processed++
    end

    WF-->>WF: ✅ Ingestion complete<br/>92 files, 1.2M rows
```

### Detailed Ingestion Process

```mermaid
flowchart TD
    A[Start: Trigger Workflow] --> B["Get Config:
    data_root, batch_size, dry_run"]

    B --> C[File Discovery Phase]
    C --> D[Scan /focus-mcp-main/data/focus/]
    D --> E[Find *.parquet files]
    E --> F{Filter by period?}

    F -->|Yes| G["Apply period filter:
    20250701-20250731"]
    F -->|No| H[Use all files]

    G --> I["Load manifest:
    processed_files.json"]
    H --> I

    I --> J{Skip processed?}
    J -->|Yes| K[Filter out processed files]
    J -->|No| L[Process all files]

    K --> M[Remaining files: 92]
    L --> M

    M --> N{Files found?}
    N -->|No| Z1[Exit: No files to process]
    N -->|Yes| O[Start processing loop]

    O --> P[Read Parquet with pyarrow]
    P --> Q[Convert to pandas DataFrame]

    Q --> R[Data Transformation Phase]
    R --> S["Column name mapping:
    PascalCase → snake_case"]

    S --> T[Type conversions]
    T --> T1["Decimal → float
    (Scientific notation fix)"]
    T1 --> T2[DateTime → ISO string]
    T2 --> T3["Boolean → 0/1
    (ClickHouse UInt8)"]
    T3 --> T4[Empty strings → None]

    T4 --> U[Generate deterministic ID]
    U --> V["Add audit fields:
    source_system, ingested_at"]

    V --> W{Dry run?}
    W -->|Yes| X[Log transformed data]
    W -->|No| Y[Prepare batches: 500 rows each]

    X --> AA[Update stats only]
    Y --> AB[Ingestion Phase]

    AB --> AC[Validate with Pydantic model]
    AC --> AD{Validation passed?}

    AD -->|No| AE[Send to Dead Letter Queue]
    AD -->|Yes| AF[Serialize to JSON]

    AE --> AG[Log validation errors]
    AF --> AH[POST to Moose HTTP API]

    AH --> AI[Moose publishes to Redpanda]
    AI --> AJ[Background consumer syncs to ClickHouse]

    AJ --> AK{More batches?}
    AK -->|Yes| AB
    AK -->|No| AL[Update manifest]

    AG --> AL
    AA --> AL

    AL --> AM{Continue on error?}
    AM -->|Yes| AN{More files?}
    AM -->|No| Z2[Exit: Error occurred]

    AN -->|Yes| O
    AN -->|No| AO[Generate workflow stats]

    AO --> AP["✅ Complete:
    files_processed, total_rows, duration"]

    style A fill:#e3f2fd
    style AP fill:#c8e6c9
    style Z1 fill:#ffcdd2
    style Z2 fill:#ffcdd2
    style AE fill:#fff9c4
```

---

## Data Consumption Flow

### Flow 3: Query via Consumption APIs

```mermaid
sequenceDiagram
    participant UI as FinOps Dashboard<br/>(React)
    participant API as Moose Consumption API<br/>(Port 4201)
    participant CH as ClickHouse
    participant MV as Materialized View<br/>focus_data_table
    participant AGG as Aggregation Table<br/>daily_cost_summary

    Note over UI,AGG: Cost Comparison Query

    UI->>API: POST /api/consumption/CostComparison<br/>{"billing_period_start": "2025-07-01",<br/>"billing_period_end": "2025-07-31"}

    API->>API: Parse CostComparisonRequest
    API->>API: Validate Pydantic schema

    API->>CH: Execute SQL query

    Note over CH: SELECT provider_name,<br/>billing_account_id,<br/>service_name,<br/>SUM(effective_cost) as total_effective_cost,<br/>SUM(billed_cost) as total_billed_cost,<br/>SUM(list_cost) as total_list_cost<br/>FROM focus_data_table<br/>WHERE billing_period_start >= '2025-07-01'<br/>GROUP BY provider_name, billing_account_id, service_name

    CH->>MV: Query focus_data_table view
    MV->>MV: Alias snake_case → PascalCase<br/>(billing_account_id → BillingAccountId)

    MV->>CH: SELECT from FocusCostUsage_0_0
    CH-->>API: Query results (100 rows)

    API->>API: Map to CostComparisonRow[]
    API->>API: Calculate effective_discount:<br/>(1 - effective_cost / list_cost) * 100

    API-->>UI: 200 OK<br/>JSON: [{"provider_name": "Azure",<br/>"total_effective_cost": 45000.50, ...}]

    UI->>UI: Render cost comparison chart

    Note over UI,AGG: Daily Cost Summary Query (Aggregated)

    UI->>API: POST /api/consumption/DailyCostSummary<br/>{"billing_account_id": "EA-12345",<br/>"start_date": "2025-07-01"}

    API->>CH: Query aggregation table

    Note over CH: SELECT billing_account_id,<br/>cost_date,<br/>sumMerge(total_effective_cost) as effective_cost,<br/>uniqMerge(unique_services) as service_count<br/>FROM daily_cost_summary<br/>WHERE billing_account_id = 'EA-12345'<br/>GROUP BY billing_account_id, cost_date

    CH->>AGG: Query pre-aggregated table
    AGG->>AGG: Merge aggregate states<br/>(sumMerge, uniqMerge)

    AGG-->>CH: Aggregated results (31 days)
    CH-->>API: Query results

    API-->>UI: 200 OK<br/>JSON: [{"cost_date": "2025-07-01",<br/>"effective_cost": 1500.00, ...}]

    UI->>UI: Render daily cost timeline
```

### API Request/Response Flow

```mermaid
flowchart LR
    A[Frontend Request] --> B{Direct or Proxied?}

    B -->|Direct CORS| C[Browser → Port 4201]
    B -->|Proxied| D[Browser → Next.js API Route]

    D --> E[Next.js → Port 4201]
    C --> F[Moose Consumption API]
    E --> F

    F --> G[Parse Request Params]
    G --> H[Validate Pydantic Schema]

    H --> I{Validation OK?}
    I -->|No| J[400 Bad Request]
    I -->|Yes| K[Execute query_function]

    K --> L[Build SQL Query]
    L --> M[Query ClickHouse]

    M --> N{Query Type?}
    N -->|Raw Table| O[Query FocusCostUsage_0_0]
    N -->|View| P[Query focus_data_table]
    N -->|Aggregation| Q[Query daily_cost_summary]

    O --> R[Map Results]
    P --> R
    Q --> R

    R --> S[Serialize to JSON]
    S --> T[Return Response]

    J --> U[Error Response]
    T --> V[Frontend Renders]
    U --> V

    style A fill:#e3f2fd
    style V fill:#c8e6c9
    style J fill:#ffcdd2
    style U fill:#ffcdd2
```

---

## Schema Migration Flow

### Flow 4: Automatic Schema Drift Detection & Migration

```mermaid
sequenceDiagram
    participant WF as Schema Migration<br/>Workflow
    participant PA as Parquet Analyzer
    participant SP as Spec Parser
    participant TG as Transformation<br/>Generator
    participant CH as ClickHouse
    participant PR as Plugin Registry<br/>(PostgreSQL)

    Note over WF,PR: Detect Schema Drift and Apply Migration

    WF->>PA: analyze_parquet_schema(sample.parquet)
    PA->>PA: Read with pyarrow.parquet
    PA->>PA: Extract schema:<br/>column names, types, nullability
    PA-->>WF: ParquetSchema (150 columns)

    WF->>SP: parse_focus_spec(FOCUS_Spec/datasets/)
    SP->>SP: Read dataset.md
    SP->>SP: Parse column definitions
    SP->>SP: Extract: Column Type, Data Type,<br/>Feature Level, Allows Nulls
    SP-->>WF: FocusSchema (120 columns)

    WF->>WF: compare_schemas(parquet_schema, focus_schema)

    WF->>WF: Detect differences:<br/>- Added: x_partner_credit_rate<br/>- Removed: (none)<br/>- Type changes: (none)

    WF->>WF: Calculate new version:<br/>0_0 → 0_1

    alt Schema drift detected
        WF->>TG: generate_transformation_sql(diff)

        TG->>TG: Generate column mappings
        TG->>TG: Generate type casts
        TG->>TG: Generate default values for added columns

        TG-->>WF: Transformation SQL

        WF->>PR: get_clickhouse_config()
        PR->>PR: Query plugin_configurations<br/>WHERE plugin_name = 'ClickHouse Sink'
        PR-->>WF: ClickHouse connection config

        WF->>CH: CREATE TABLE FocusCostUsage_0_1<br/>(schema with new columns)
        CH-->>WF: ✅ Table created

        WF->>CH: CREATE MATERIALIZED VIEW<br/>FocusCostUsage_0_1_migration_mv<br/>AS SELECT *, NULL as x_partner_credit_rate<br/>FROM FocusCostUsage_0_0
        CH-->>WF: ✅ Materialized view created

        WF->>CH: Wait for backfill to complete
        CH->>CH: Background merge populates new table

        WF->>CH: Validate row counts:<br/>0_0 vs 0_1
        CH-->>WF: ✅ Counts match

        WF->>CH: CREATE OR REPLACE VIEW focus_data_table<br/>AS SELECT * FROM FocusCostUsage_0_1
        CH-->>WF: ✅ View updated

        WF->>WF: Record migration in<br/>focus_schema_versions table

        WF-->>WF: ✅ Migration complete:<br/>version 0_0 → 0_1
    else No drift detected
        WF-->>WF: ℹ️ Schema unchanged:<br/>using version 0_0
    end
```

### Schema Migration Decision Tree

```mermaid
flowchart TD
    A[Start: Schema Migration Workflow] --> B[Read sample Parquet file]
    B --> C[Extract Parquet schema]

    C --> D[Parse FOCUS specification]
    D --> E[Compare schemas]

    E --> F{Schema differences?}

    F -->|No| G[✅ No migration needed]
    F -->|Yes| H[Analyze differences]

    H --> I{Type of change?}

    I -->|Added columns| J[Generate NULL defaults]
    I -->|Removed columns| K[Drop from SELECT]
    I -->|Type changes| L[Generate CAST expressions]

    J --> M[Calculate new version:<br/>major_minor++]
    K --> M
    L --> M

    M --> N[Get ClickHouse config<br/>from Plugin Registry]

    N --> O{Plugin config found?}
    O -->|No| Z1[❌ Error: Config not found]
    O -->|Yes| P[Connect to ClickHouse]

    P --> Q[Create new versioned table:<br/>FocusCostUsage_0_1]

    Q --> R{Table exists?}
    R -->|Yes| Z2[❌ Error: Version conflict]
    R -->|No| S[Create table with new schema]

    S --> T[Create materialized view for migration]
    T --> U[Execute transformation SQL]

    U --> V[Wait for backfill:<br/>Poll row counts]

    V --> W{Backfill complete?}
    W -->|No| V
    W -->|Yes| X[Validate row counts match]

    X --> Y{Counts match?}
    Y -->|No| Z3[❌ Error: Data loss detected]
    Y -->|Yes| AA[Update focus_data_table view<br/>to point to new version]

    AA --> AB[Record migration in<br/>focus_schema_versions]

    AB --> AC[✅ Migration complete]

    G --> AD[Return: no_migration_needed]
    AC --> AE[Return: migration_success]

    style A fill:#e3f2fd
    style AD fill:#c8e6c9
    style AE fill:#c8e6c9
    style Z1 fill:#ffcdd2
    style Z2 fill:#ffcdd2
    style Z3 fill:#ffcdd2
```

---

## Component Interactions

### Complete System Interaction Map

```mermaid
graph TB
    subgraph "Frontend Layer"
        A1[FinOps Dashboard<br/>Port 3003]
    end

    subgraph "API Layer"
        B1[BIA Backend API<br/>Port 4300]
        B2[Moose Main Server<br/>Port 4200]
        B3[Moose Consumption API<br/>Port 4201]
    end

    subgraph "Orchestration Layer"
        C1[Temporal Server<br/>172.18.0.3:7233]
        C2[Temporal Worker<br/>run_worker.py]
        C3[Workflow Registry]
    end

    subgraph "Ingestion Layer"
        D1[File Discovery<br/>file_discovery.py]
        D2[Data Transformer<br/>data_transformer.py]
        D3[Moose Adapter<br/>moose_ingestion_adapter.py]
    end

    subgraph "Moose Stack"
        E1[Pydantic Models<br/>app/ingest/focus/models.py]
        E2[IngestPipeline<br/>focusCostUsageModel]
        E3[HTTP Endpoints<br/>/ingest/FocusCostUsage]
        E4[Redpanda Topics]
        E5[Background Consumers]
    end

    subgraph "Storage Layer"
        F1[ClickHouse Tables<br/>FocusCostUsage_0_0]
        F2[Materialized Views<br/>focus_data_table]
        F3[Aggregation Tables<br/>daily_cost_summary]
    end

    subgraph "Configuration"
        G1[Plugin Registry<br/>PostgreSQL]
        G2[moose.config.toml]
        G3[Environment Variables]
    end

    subgraph "External Data"
        H1[Azure FOCUS Parquet<br/>/focus-mcp-main/data/]
        H2[FOCUS Specification<br/>/FOCUS_Spec/]
    end

    A1 -->|Workflow Trigger| B1
    A1 -->|Query Data| B3

    B1 -->|Start Workflow| C1
    C1 -->|Execute Activities| C2
    C2 -->|Discover Files| D1
    C2 -->|Transform Data| D2
    C2 -->|Ingest Data| D3

    D1 -->|Scan| H1
    D2 -->|Read| H1
    D2 -->|Reference| H2
    D3 -->|POST| E3

    E1 -->|Define Schema| E2
    E2 -->|Register| E3
    E3 -->|Publish| E4
    E4 -->|Consume| E5
    E5 -->|Insert| F1

    F1 -->|Create| F2
    F2 -->|Aggregate| F3
    F3 -->|Query| B3

    B1 -->|Get Config| G1
    C2 -->|Get Config| G1
    B2 -->|Read Config| G2

    classDef frontend fill:#e1f5ff,stroke:#0066cc
    classDef api fill:#fff4e6,stroke:#ff9800
    classDef orchestration fill:#f3e5f5,stroke:#9c27b0
    classDef ingestion fill:#fce4ec,stroke:#e91e63
    classDef moose fill:#e8f5e9,stroke:#4caf50
    classDef storage fill:#e0f2f1,stroke:#009688
    classDef config fill:#fff9c4,stroke:#fbc02d
    classDef external fill:#efebe9,stroke:#795548

    class A1 frontend
    class B1,B2,B3 api
    class C1,C2,C3 orchestration
    class D1,D2,D3 ingestion
    class E1,E2,E3,E4,E5 moose
    class F1,F2,F3 storage
    class G1,G2,G3 config
    class H1,H2 external
```

---

## Key Data Structures

### 1. FocusCostUsage Pydantic Model

```python
# app/ingest/focus/models.py
class FocusCostUsage(BaseModel):
    # Primary key
    id: Key[str]  # Deterministic hash

    # Mandatory FOCUS fields
    billing_account_id: str
    billing_currency: str
    charge_period_start: datetime
    effective_cost: Decimal  # Decimal(38,18)
    billed_cost: Decimal

    # Extended Azure fields (x_*)
    x_partner_credit_rate: Optional[Decimal]
    x_sku_meter_category: Optional[str]

    # Audit fields
    source_system: str = "focus_parquet"
    ingested_at: datetime
```

### 2. IngestPipeline Configuration

```python
focusCostUsageModel = IngestPipeline[FocusCostUsage](
    "FocusCostUsage",
    IngestPipelineConfig(
        ingest=True,       # HTTP endpoint: /ingest/FocusCostUsage
        stream=True,       # Redpanda topic: FocusCostUsage
        table=True,        # ClickHouse table: FocusCostUsage_0_0
        dead_letter_queue=True  # DLQ for validation failures
    )
)
```

### 3. ClickHouse Table DDL (Auto-Generated)

```sql
CREATE TABLE FocusCostUsage_0_0 (
    id String,
    billing_account_id String,
    billing_currency String,
    charge_period_start DateTime64(3),
    effective_cost Decimal(38, 18),
    billed_cost Decimal(38, 18),
    x_partner_credit_rate Nullable(Decimal(38, 18)),
    x_sku_meter_category Nullable(String),
    source_system String DEFAULT 'focus_parquet',
    ingested_at DateTime64(3)
) ENGINE = MergeTree()
ORDER BY (billing_account_id, charge_period_start)
PARTITION BY toYYYYMM(charge_period_start);
```

### 4. Materialized View (PascalCase Alias)

```sql
CREATE VIEW focus_data_table AS
SELECT
    id,
    billing_account_id AS BillingAccountId,
    billing_currency AS BillingCurrency,
    charge_period_start AS ChargePeriodStart,
    effective_cost AS EffectiveCost,
    billed_cost AS BilledCost
FROM FocusCostUsage_0_0;
```

---

## Performance Characteristics

### Ingestion Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Batch size | 500 rows | Optimized for 10MB Moose limit |
| Files processed | 92 files | FOCUS 1.2 export (1 month) |
| Total rows | ~1.2M rows | Typical Azure Enterprise Agreement |
| Processing time | ~45 minutes | Single-threaded workflow |
| Throughput | ~450 rows/sec | Network and validation overhead |

### Query Performance

| Query Type | Latency | Notes |
|------------|---------|-------|
| Raw table query (1 day) | ~200ms | Full scan 30K rows |
| View query (1 month) | ~2s | Full scan 1.2M rows |
| Aggregated query (1 month) | ~50ms | Pre-aggregated table (31 rows) |
| Consumption API overhead | ~10ms | Pydantic validation + serialization |

### Storage Efficiency

| Component | Size | Compression |
|-----------|------|-------------|
| Raw Parquet files | ~800MB | Native compression |
| ClickHouse table | ~450MB | LZ4 compression (~45%) |
| Aggregation tables | ~2MB | Highly compressed aggregates |
| Redpanda topics | ~100MB | Retention: 30 seconds |

---

## Error Handling & Resilience

### Data Validation Pipeline

```mermaid
flowchart LR
    A[Raw Data] --> B[Pydantic Validation]

    B -->|Invalid| C[Dead Letter Queue]
    B -->|Valid| D[Moose HTTP API]

    D -->|Timeout| E[Retry with backoff]
    D -->|Success| F[Redpanda Topic]

    E -->|Max retries| C
    E -->|Retry OK| F

    F -->|Consumer error| G[DLQ Topic]
    F -->|Success| H[ClickHouse Insert]

    C --> I[Manual Review]
    G --> I

    H --> J[✅ Data stored]

    style A fill:#e3f2fd
    style J fill:#c8e6c9
    style C fill:#ffcdd2
    style G fill:#ffcdd2
    style I fill:#fff9c4
```

### Failure Modes & Recovery

| Failure Mode | Detection | Recovery Strategy |
|--------------|-----------|-------------------|
| Invalid Parquet schema | File read error | Skip file, log error, continue |
| Pydantic validation failure | Model validation | Send to DLQ, log details |
| Moose API 413 (too large) | HTTP status | Reduce batch size, retry |
| Moose API timeout | Connection timeout | Exponential backoff retry (3x) |
| ClickHouse connection loss | Insert error | Reconnect, replay from Redpanda offset |
| Temporal workflow crash | Activity timeout | Temporal auto-retry with history |
| Schema drift detected | Migration workflow | Auto-generate migration, apply versioned schema |

---

## Monitoring & Observability

### Key Metrics Tracked

```mermaid
graph LR
    A[Workflow Stats] --> B[Files Discovered]
    A --> C[Files Processed]
    A --> D[Files Failed]
    A --> E[Total Rows]
    A --> F[Processing Time]

    G[Ingestion Metrics] --> H[Batches Sent]
    G --> I[Validation Errors]
    G --> J[API Latency]
    G --> K[DLQ Count]

    L[Table Metrics] --> M[Row Count]
    L --> N[Storage Size]
    L --> O[Query Latency]
    L --> P[Partition Health]

    style A fill:#e3f2fd
    style G fill:#fff4e6
    style L fill:#e8f5e9
```

### Logs & Tracing

- **Temporal Workflow History**: Complete execution trace with replay capability
- **Moose Server Logs**: HTTP API requests, validation errors, topic publishes
- **ClickHouse Query Logs**: `system.query_log` for performance analysis
- **Application Logs**: Structured JSON logs with correlation IDs

---

## Summary

### FocusCostUsage_0_0 Table Lifecycle

1. **Creation**: Moose auto-generates from Pydantic model on `moose-cli dev`
2. **Schema**: Snake_case storage, PascalCase view for YAML query compatibility
3. **Ingestion**: Parquet → Transform → HTTP API → Redpanda → ClickHouse
4. **Consumption**: Materialized views + aggregations for fast queries
5. **Evolution**: Schema migration workflow handles version upgrades (0_0 → 0_1)

### Data Flow Path

```
Parquet Files → File Discovery → Data Transformer
    → Moose HTTP API → Redpanda Topics → ClickHouse FocusCostUsage_0_0
    → Materialized Views → Aggregation Tables → Consumption APIs → Frontend
```

### Key Benefits

✅ **Type-safe**: Pydantic validation at ingestion boundary
✅ **Scalable**: Streaming architecture with batch processing
✅ **Resilient**: Dead letter queues + Temporal retry logic
✅ **Observable**: Comprehensive metrics and logging
✅ **Maintainable**: Schema-driven with automatic migrations
✅ **Performant**: Pre-aggregated tables for sub-50ms queries

---

## References

- **Design Document**: `/home/chris/repo/area-code/.kiro/specs/focus_billing/design.md`
- **Pydantic Models**: `/home/chris/repo/area-code/odw/services/data-warehouse/app/ingest/focus/models.py`
- **Ingestion Workflow**: `/home/chris/repo/area-code/odw/services/data-warehouse/app/focus_billing/workflow.py`
- **Schema Migration**: `/home/chris/repo/area-code/odw/services/data-warehouse/app/focus_billing/schema_migration/`
- **Moose Configuration**: `/home/chris/repo/area-code/odw/services/data-warehouse/moose.config.toml`
