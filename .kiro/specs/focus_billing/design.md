# Focus Billing Integration Design

## Context
- FOCUS 1.2 exports (Parquet with nested period folders) live in `focus-mcp-main/data/focus`.
- Official column metadata lives in `resources/specifications/columns.yaml`; curated FOCUS use-case SQL lives in `resources/queries/*.yaml`.
- ClickHouse `finops-odw` is the primary analytical store (accessible via the Moose MCP ClickHouse tooling).
- Existing Moose app exposes consumption APIs and workflows through `moose_lib`. No FOCUS-specific module exists yet.

## Objectives
1. Materialize FOCUS-compliant tables in ClickHouse so queries from the YAML library can run without manual rewrites.
2. Expose those queries as Moose consumption APIs (list queries, fetch SQL, execute with runtime parameters).
3. Build a Moose workflow that ingests the local Parquet exports into the new tables and keeps a manifest of processed files.

## Target Schema & Storage Strategy
### Cost & Usage Table (`focus_cost_usage`)
- Capture the full FOCUS export grain (one row per charge line).
- Column naming strategy: store in ClickHouse using snake_case for ergonomics, but expose a view with the canonical FOCUS casing.
- Key columns: `id` (deterministic hash of BillingAccountId + ChargePeriodStart + ResourceId + SkuMeter + row_number), `billing_account_id`, `usage_date`, cost metrics (`billed_cost`, `effective_cost`, etc.), provider metadata, tags payload.
- Data types:
  - Monetary metrics: `Decimal(38, 18)` mapped to ClickHouse `Decimal(38, 18)` (converted to `Decimal(18, 6)` if precision exceeds ClickHouse limits).
  - Dates: convert Parquet `INT96` to `Date`/`DateTime64`.
  - Nullable strings remain `Nullable(String)`.
  - Extended provider columns (`x_*`) inherit their native types (string vs decimal) so downstream rules stay intact.
  - Boolean flags (e.g., `x_sku_is_credit_eligible`) store as `Nullable(UInt8)` for ClickHouse compatibility.
  - JSON payloads (`tags`, `sku_price_details`, etc.) stay in `Nullable(String)` for local development, but production ingestion can cast them into ClickHouse's native `JSON` type so downstream SQL can rely on dot-notation (`tags.ApplicationId`). Document both modes and keep compatibility helpers (e.g., `JSON_VALUE`) until the production schema is finalized.
- Partitions: `PARTITION BY toYYYYMM(usage_date)` (matches common query filters).
- Order by: `(usage_date, billing_account_id, service_category, service_name)` for efficient scans.
- Indexes: min/max on `(billing_account_id, usage_date)`, set indexes on `service_category`, `provider`, `region`.
- Columns stay 1:1 with the Cost and Usage dataset specification (`FOCUS_Spec/specification/datasets/cost_and_usage/dataset.md`).
- Each column definition carries Moose `metadata` tags so we can surface FOCUS semantics alongside schema:
  - `metadata.column_type` = spec "Column Type" (Dimension vs Metric).
  - `metadata.feature_level` = spec "Feature Level" (Mandatory, Recommended, Conditional).
  - `metadata.allows_nulls` and `metadata.data_type` mirror the spec for quick introspection.
- Persist JSON-oriented spec fields (e.g., `allocated_tags`) as `JSONEachRow` compatible `String` columns and validate shape in ingestion.

### Contract Commitment Table (`focus_contract_commitment`)
- Mirrors the FOCUS Contract Commitment dataset (`FOCUS_Spec/specification/datasets/contract_commitment/dataset.md`).
- Columns stay 1:1 with the specification while remaining snake_case in storage; metadata preserves canonical FOCUS casing for API consumers.
- Each column definition carries Moose `metadata` tags so we can surface FOCUS semantics alongside schema:
  - `metadata.column_type` = spec "Column Type" (Dimension vs Metric).
  - `metadata.feature_level` = spec "Feature Level" (Mandatory, Recommended, Conditional).
  - `metadata.allows_nulls` and `metadata.data_type` mirror the spec for quick introspection.
- Use ClickHouse `Nullable` types wherever "Allows Nulls" is `True`; map Decimal/Numeric to `Decimal(38, 18)` and Date/Time to `DateTime64(3)`.
- `contract_commitment_id` serves as the shared key between `focus_cost_usage` and `focus_contract_commitment`, enabling joins without custom SQL.
- Persist JSON-oriented spec fields (e.g., `contract_commitment_description`) as `String` columns while validating shape in ingestion as needed.

### Helper Objects
- `focus_data_table` VIEW: `SELECT ...` projected from `focus_cost_usage`, renaming snake_case columns back to FOCUS PascalCase so YAML SQL works unchanged.
- `focus_contract_commitment_view`: exposes the Contract Commitment table with canonical casing to simplify joins with YAML queries.
- Optional dimensions (phase 2): service category, geography, billing account. For the initial deliverable we can postpone unless queries require them.

### Table Creation Flow
1. Generate DDL using Moose MCP ClickHouse tool (`moose-dev__query_olap`) so schema lives in ClickHouse, not just docs.
2. DDL order:
   - `DROP/CREATE TABLE focus_cost_usage` (with column metadata populated from the Cost and Usage dataset).
   - `DROP/CREATE TABLE focus_contract_commitment` (with column metadata populated from the Contract Commitment dataset).
   - Create supporting views (`focus_data_table`, `focus_contract_commitment_view`).
   - Create indexes.
3. Store companion DDL in repo (`app/focus_billing/tables.py` or SQL file) so engineers can reapply.

## Query Exposure Plan
### Query Catalog Loader
- Add module that reads `resources/queries/*.yaml` at startup and converts entries into `FocusQuery` models.
- Replace placeholder `focus_data_table` reference with ClickHouse view.
- Track parameter specs: majority expect `[start_date, end_date]`. Validate and coerce to `Date`.
- Provide ability to list queries (with metadata) and fetch SQL preview for UI clients.

### Moose Consumption APIs
- Build new APIs under `app/apis/focus_billing/`:
  1. `list_focus_use_cases`: returns metadata for all queries.
  2. `get_focus_use_case`: details + SQL for a given slug.
  3. `execute_focus_use_case`: runs SQL with runtime parameters, returns rows (paged) and metrics (row count, elapsed).
  4. `list_supported_features`: surfaces the contents of `FOCUS_Spec/specification/supported_features` so clients can discover optional capabilities aligned with the spec.
     - Parse individual Markdown files (e.g., `cost_and_usage_attribution.md`) and expose them as structured metadata for UI rendering and API consumers.
- Use `moose_lib.ConsumptionApi` (consistent with existing APIs). Provide pydantic models for request/response validation.
- Parameter handling:
  - Accept `start_date`, `end_date`, optional dict of named bind variables if present.
  - Replace positional `?` placeholders with prepared statement dictionary (ClickHouse client expects named parameters).
  - Validate that required params are supplied before execution; raise descriptive errors otherwise.
- Caching: rely on Moose default caching (optional future enhancement).

## Ingestion Workflow (Updated: Moose-Native Approach)
### Architecture Change
**Previous**: Direct ClickHouse insertion via `clickhouse_connect` with manual DDL management
**New**: Moose-native ingestion using data models in `app/ingest/` with automatic schema sync

### Benefits of Moose-Native Approach
1. **Automatic Schema Management**: Moose handles table creation, migrations, and schema sync
2. **Type Safety**: Pydantic models provide validation and type checking
3. **Streaming + Batch**: Support both streaming ingestion APIs and batch Parquet processing
4. **Consistent Patterns**: Aligns with existing Moose app architecture
5. **Built-in Monitoring**: Leverage Moose's observability for ingestion metrics

### Data Model Structure
Create Moose data models in `app/ingest/focus/`:

```
app/ingest/focus/
├── models.py                    # Pydantic data models
│   ├── FocusCostUsage_0_0      # Version 0.0 (snake_case storage)
│   └── FocusContractCommitment_0_0
├── flow.py                      # Stream functions for transformations
└── views/                       # Materialized views
    ├── focus_data_table.py      # PascalCase view for YAML queries
    └── focus_contract_commitment_view.py
```

### Workflow Steps (Revised)
- Create `FocusBillingIngestWorkflow` under `app/focus_billing/workflow.py`
- Steps per run:
  1. **Discover Parquet files** under configured root (default `focus-mcp-main/data/focus`)
  2. **Read manifest metadata** for row counts and period validation
  3. **Transform to Moose format**:
     - Load Parquet using pandas/pyarrow
     - Map PascalCase → snake_case to match Moose model fields
     - Type conversions: `INT96` → `DateTime64(3)`, decimals, booleans
     - Add audit fields: `id`, `source_system`, `created_at`, `updated_at`
  4. **Ingest via Moose APIs**:
     - Use Moose's `IngestApi` endpoints (HTTP POST to `/ingest/FocusCostUsage_0_0`)
     - OR use Moose's file-based ingestion with Parquet format support
     - Moose handles batching, ClickHouse writes, and schema validation
  5. **Track processing** in `focus_ingest_manifest` table (managed by Moose)
  6. **Skip processed files** based on manifest checksum

### File-Based Ingestion Option
Moose supports direct Parquet ingestion:
```python
# Option 1: Stream through Moose HTTP API
for batch in parquet_batches:
    moose_client.ingest("FocusCostUsage_0_0", batch)

# Option 2: Use Moose file-based ingestion (if supported)
moose_client.ingest_file("FocusCostUsage_0_0", parquet_path)
```

### Schema Management
- **Moose Data Models** define schema with FOCUS metadata in field descriptions
- **Automatic DDL**: Moose generates and applies ClickHouse DDL on model changes
- **Views**: Create Moose aggregations/views for PascalCase column renaming
- **Migrations**: Moose handles version transitions (e.g., `_0_0` → `_0_1`)

### Error Handling
- Moose ingestion APIs provide built-in validation and error responses
- Workflow catches ingestion errors and updates manifest with failure status
- Retry logic leverages Temporal's built-in retry policies
- Testing: Dry-run mode validates transformations without sending to Moose

## Configuration
- Add `FOCUS_DATA_ROOT` env (default to path in focus-mcp project). Document fallback.
- Reuse ClickHouse credentials from `moose.config.toml`; avoid duplicating secrets.
- Optionally allow workflow params (batch size, concurrency).

## Observability & Validation
- Before ingest, verify target table exists (and create if missing).
- Emit metrics: rows ingested, files processed, duration.
- Validate `contract_commitment_id` referential integrity between the two dataset tables, logging gaps for downstream remediation.
- Optionally call existing focus compliance tests after insert (future work).

## Open Questions / Assumptions
- Initial delivery focuses on the two dataset tables + views; dimension tables staged for later if needed.
- Queries in YAML currently use positional `?` parameters for date ranges; assume first two parameters are `start` and `end`.
- Parquet exports might include additional provider-specific columns; ingest pipeline should store them as JSON in `extended_attributes` if they aren't mapped (fallback plan).
- Manifest table retention strategy (basic logging is acceptable for now).
