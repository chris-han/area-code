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
**New**: Moose-native ingestion using data models in `app/ingest/focus/` with automatic schema sync

### Benefits of Moose-Native Approach
1. **Automatic Schema Management**: Moose handles table creation, migrations, and schema sync from Pydantic models
2. **Type Safety**: Pydantic models provide validation and type checking aligned with FOCUS spec
3. **Streaming + Batch**: Support both streaming ingestion APIs and batch Parquet processing
4. **Consistent Patterns**: Aligns with existing Moose app architecture (see `app/ingest/models.py`)
5. **Built-in Monitoring**: Leverage Moose's observability for ingestion metrics

### Data Model Structure
Create Moose data models in `app/ingest/focus/models.py`:

```python
from moose_lib import Key, IngestPipeline, IngestPipelineConfig
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime

class FocusCostUsage(BaseModel):
    """FOCUS 1.2 Cost and Usage dataset - snake_case for ClickHouse storage"""

    # Primary key - deterministic hash
    id: Key[str] = Field(description="Deterministic hash: billing_account_id + charge_period_start + resource_id + sku_meter")

    # Mandatory dimensions (FOCUS spec)
    billing_account_id: str = Field(description="FOCUS: BillingAccountId (Mandatory)")
    billing_account_name: Optional[str] = Field(description="FOCUS: BillingAccountName (Mandatory, allows nulls)")
    billing_currency: str = Field(description="FOCUS: BillingCurrency (Mandatory)")
    billing_period_start: datetime = Field(description="FOCUS: BillingPeriodStart (Mandatory)")
    billing_period_end: datetime = Field(description="FOCUS: BillingPeriodEnd (Mandatory)")
    charge_period_start: datetime = Field(description="FOCUS: ChargePeriodStart (Mandatory)")
    charge_period_end: datetime = Field(description="FOCUS: ChargePeriodEnd (Mandatory)")
    charge_category: str = Field(description="FOCUS: ChargeCategory (Mandatory)")
    provider_name: str = Field(description="FOCUS: Provider (Mandatory)")
    publisher_name: str = Field(description="FOCUS: Publisher (Mandatory)")
    invoice_issuer_name: str = Field(description="FOCUS: InvoiceIssuer (Mandatory)")
    service_category: str = Field(description="FOCUS: ServiceCategory (Mandatory)")
    service_name: str = Field(description="FOCUS: ServiceName (Mandatory)")

    # Mandatory metrics (FOCUS spec)
    billed_cost: Decimal = Field(description="FOCUS: BilledCost (Mandatory, Decimal(38,18))")
    contracted_cost: Decimal = Field(description="FOCUS: ContractedCost (Mandatory, Decimal(38,18))")
    effective_cost: Decimal = Field(description="FOCUS: EffectiveCost (Mandatory, Decimal(38,18))")
    list_cost: Decimal = Field(description="FOCUS: ListCost (Mandatory, Decimal(38,18))")
    pricing_quantity: Optional[Decimal] = Field(description="FOCUS: PricingQuantity (Mandatory, allows nulls)")
    pricing_unit: Optional[str] = Field(description="FOCUS: PricingUnit (Mandatory, allows nulls)")

    # Conditional/Recommended dimensions (FOCUS spec - allows nulls)
    charge_class: Optional[str] = Field(description="FOCUS: ChargeClass (Mandatory, allows nulls)")
    charge_description: Optional[str] = Field(description="FOCUS: ChargeDescription (Mandatory, allows nulls)")
    charge_frequency: Optional[str] = Field(description="FOCUS: ChargeFrequency (Recommended)")
    availability_zone: Optional[str] = Field(description="FOCUS: AvailabilityZone (Recommended)")
    region_id: Optional[str] = Field(description="FOCUS: RegionId (Conditional)")
    region_name: Optional[str] = Field(description="FOCUS: RegionName (Conditional)")
    resource_id: Optional[str] = Field(description="FOCUS: ResourceId (Conditional)")
    resource_name: Optional[str] = Field(description="FOCUS: ResourceName (Conditional)")
    resource_type: Optional[str] = Field(description="FOCUS: ResourceType (Conditional)")
    service_subcategory: Optional[str] = Field(description="FOCUS: ServiceSubcategory (Recommended)")
    sku_id: Optional[str] = Field(description="FOCUS: SkuId (Conditional)")
    sku_meter: Optional[str] = Field(description="FOCUS: SkuMeter (Conditional)")
    sku_price_id: Optional[str] = Field(description="FOCUS: SkuPriceId (Conditional)")

    # JSON fields (FOCUS spec)
    tags: Optional[str] = Field(description="FOCUS: Tags (Conditional, JSON as String)")
    sku_price_details: Optional[str] = Field(description="FOCUS: SkuPriceDetails (Conditional, JSON as String)")

    # Extended provider columns (x_* fields from Azure)
    x_account_id: Optional[str] = None
    x_billed_cost_in_usd: Optional[Decimal] = None
    x_effective_cost_in_usd: Optional[Decimal] = None
    # ... (additional x_* fields as needed from parquet schema)

    # Audit fields
    source_system: str = Field(default="focus_parquet")
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

# Create Moose IngestPipeline
focusCostUsageModel = IngestPipeline[FocusCostUsage](
    "FocusCostUsage",
    IngestPipelineConfig(
        ingest=True,      # Enable HTTP ingestion endpoint
        stream=True,      # Create Kafka/Redpanda topic
        table=True,       # Create ClickHouse table
        dead_letter_queue=True
    )
)
```

**Key Design Decisions:**
- **Column names**: Use `snake_case` in Pydantic models → Moose generates ClickHouse tables with `snake_case`
- **FOCUS metadata**: Capture in Field `description` for documentation and introspection
- **Type mapping**:
  - FOCUS `Decimal` → Python `Decimal` → ClickHouse `Decimal(38,18)`
  - FOCUS `Date/Time` → Python `datetime` → ClickHouse `DateTime64(3)`
  - FOCUS `JSON` → Python `str` (JSON string) → ClickHouse `Nullable(String)`
  - Extended `x_*` columns → Optional fields for Azure-specific metadata
- **Primary key**: Deterministic hash `id` as `Key[str]` for deduplication
- **Nullability**: Use `Optional[T]` for FOCUS columns with "Allows Nulls = True"

### PascalCase View for YAML Queries
Create ClickHouse view `focus_data_table` that aliases `snake_case` → `PascalCase`:

```sql
CREATE VIEW focus_data_table AS
SELECT
    id,
    billing_account_id AS BillingAccountId,
    billing_account_name AS BillingAccountName,
    billing_currency AS BillingCurrency,
    billing_period_start AS BillingPeriodStart,
    billing_period_end AS BillingPeriodEnd,
    charge_period_start AS ChargePeriodStart,
    charge_period_end AS ChargePeriodEnd,
    billed_cost AS BilledCost,
    effective_cost AS EffectiveCost,
    -- ... (all columns renamed to PascalCase)
FROM FocusCostUsage_0_0;
```

This view enables FOCUS YAML queries to run without modification.

### Workflow Steps (Revised)
`FocusBillingIngestWorkflow` in `app/focus_billing/workflow.py`:

1. **Discover Parquet files** under `FOCUS_DATA_ROOT` (env var or default path)
2. **Read manifest metadata** (period, dataset type, row count)
3. **Transform Parquet → Moose format**:
   - Load with `pyarrow.parquet.read_table()`
   - Map PascalCase → snake_case column names
   - Convert types: timestamps, decimals, booleans, JSON strings
   - Generate deterministic `id` hash
   - Add `source_system`, `ingested_at` audit fields
4. **Batch ingestion to Moose**:
   - Convert to list of Pydantic `FocusCostUsage` instances
   - POST batches to Moose HTTP API: `POST /ingest/FocusCostUsage`
   - Moose validates schema, writes to ClickHouse `FocusCostUsage_0_0` table
5. **Track processing** in `focus_ingest_manifest` table
6. **Skip already-processed files** (checksum-based deduplication)

### Ingestion Code Pattern
```python
import httpx
from .ingest.focus.models import FocusCostUsage

async def ingest_focus_batch(records: List[FocusCostUsage]):
    """Send batch to Moose ingestion API"""
    moose_url = "http://localhost:4200/ingest/FocusCostUsage"
    payload = [record.model_dump(mode='json') for record in records]

    async with httpx.AsyncClient() as client:
        response = await client.post(moose_url, json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json()
```

### Schema Management
- **Source of Truth**: Pydantic models in `app/ingest/focus/models.py` define schema
- **Automatic DDL**: Moose CLI generates and applies ClickHouse DDL on startup
- **Schema Evolution**: Version models (e.g., `FocusCostUsage_0_1`) for breaking changes
- **Views**: Create PascalCase view manually or via Moose aggregations

### Error Handling
- **Validation**: Pydantic validates data before ingestion (type errors, required fields)
- **DLQ**: Moose routes failed records to dead-letter queue for inspection
- **Retry Logic**: Temporal workflow retries on transient failures (network, ClickHouse unavailable)
- **Dry-Run Mode**: Workflow parameter to validate transformations without sending to Moose

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
