# FOCUS Billing - Moose Stack Implementation Summary

## Overview
Updated the FOCUS billing integration to use the Moose stack for type generation, schema management, and data ingestion. This replaces the previous direct ClickHouse insertion approach with Moose-native patterns.

## Changes Made

### 1. Design Specification Updated
**File**: `.kiro/specs/focus_billing/design.md`

- Updated ingestion workflow to use Moose-native approach
- Defined Pydantic data models with IngestPipeline configuration
- Specified type mapping from FOCUS spec to Python/ClickHouse types
- Added PascalCase view design for YAML query compatibility

### 2. Moose Data Models Created
**File**: `app/ingest/focus/models.py`

Complete FOCUS 1.2 Cost and Usage data model:
- All mandatory columns from FOCUS specification
- All conditional/recommended columns
- Extended Azure x_* columns
- Proper type mapping:
  - `Decimal(38,18)` for monetary values
  - `datetime` for timestamps
  - `Optional[T]` for nullable fields
  - JSON fields as `str`
- Audit fields: `id`, `source_system`, `ingested_at`
- Moose IngestPipeline configuration with table, stream, and DLQ enabled

**Key Features:**
```python
class FocusCostUsage(BaseModel):
    id: Key[str]  # Deterministic hash for deduplication
    billing_account_id: str  # Mandatory
    billed_cost: Decimal  # Mandatory metric
    # ... 100+ fields matching FOCUS spec

focusCostUsageModel = IngestPipeline[FocusCostUsage](
    "FocusCostUsage",
    IngestPipelineConfig(ingest=True, stream=True, table=True, dead_letter_queue=True)
)
```

### 3. Moose Ingestion Adapter
**File**: `app/focus_billing/moose_ingestion_adapter.py`

Replaces `clickhouse_inserter.py` with HTTP API ingestion:
- Converts transformed DataFrame to Pydantic-compatible dictionaries
- Handles type conversion for JSON serialization
- Generates deterministic IDs via SHA-256 hash
- Batches data and POSTs to `/ingest/FocusCostUsage` endpoint
- Async/await pattern for efficient HTTP requests

**Usage Pattern:**
```python
adapter = MooseIngestionAdapter(batch_size=1000)
result = await adapter.ingest_transformed_data(
    transformation_result, file_info, manifest_id
)
```

### 4. Workflow Integration
**File**: `app/focus_billing/workflow.py`

Updated to use Moose ingestion:
- Replaced `ClickHouseInserter` with `MooseIngestionAdapter`
- Uses `asyncio.run()` to execute async ingestion
- Maintains existing error handling and observability
- Compatible with existing file discovery and transformation pipeline

### 5. Consumption APIs for FOCUS Features
**File**: `app/apis/focus_features.py`

Implements 5 consumption APIs based on FOCUS supported features:

1. **Cost Comparison** (`/consumption/CostComparison`)
   - Analyzes BilledCost, ContractedCost, EffectiveCost, ListCost
   - Calculates contracted and effective discounts
   - Groups by provider, account, service

2. **Effective Cost Analysis** (`/consumption/EffectiveCostAnalysis`)
   - Tracks spending trends with amortized costs
   - Aggregates by service, region, pricing unit
   - Supports date range filtering

3. **Commitment Discount Purchases** (`/consumption/CommitmentDiscountPurchases`)
   - Reports on reservation and savings plan purchases
   - Tracks commitment details and costs
   - Filters by charge category = 'Purchase'

4. **Correction Charges** (`/consumption/CorrectionCharges`)
   - Identifies billing adjustments
   - Filters by charge_class = 'Correction'
   - Groups by provider, account, service

5. **Recurring Charges** (`/consumption/RecurringCharges`)
   - Analyzes recurring commitment fees
   - Tracks commitment discount details
   - Filters by charge_frequency = 'Recurring'

All APIs query the `FocusCostUsage_0_0` table (cost_and_usage dataset only, as contract_commitment data not yet available).

### 6. Test Scripts

**File**: `app/focus_billing/test_moose_ingestion.py`
- Tests ingestion workflow with sample data
- Configurable parameters (batch size, file limit, period filter)
- Reports statistics and errors

**File**: `app/focus_billing/test_end_to_end_moose.py`
- End-to-end validation:
  1. Moose service health check
  2. Data ingestion via workflow
  3. ClickHouse data verification
  4. Consumption API calls
- Comprehensive test reporting

## Data Flow

```
┌─────────────────┐
│ Parquet Files   │
│ (FOCUS 1.2)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ File Discovery          │
│ - Scan directories      │
│ - Read manifests        │
│ - Filter by period      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Data Transformer        │
│ - PascalCase→snake_case │
│ - Type conversions      │
│ - Add computed fields   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Moose Ingestion Adapter │
│ - DataFrame→Dict        │
│ - JSON serialization    │
│ - POST batches to API   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Moose HTTP API          │
│ /ingest/FocusCostUsage  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Moose Processing        │
│ - Pydantic validation   │
│ - Stream to Redpanda    │
│ - Write to ClickHouse   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ ClickHouse Table        │
│ FocusCostUsage_0_0      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Consumption APIs        │
│ - Cost Comparison       │
│ - Effective Cost        │
│ - Commitment Purchases  │
│ - Corrections           │
│ - Recurring Charges     │
└─────────────────────────┘
```

## Running the System

### 1. Start Moose Service
```bash
cd /home/chris/repo/area-code/odw/services/data-warehouse
source .venv/bin/activate
.venv/bin/moose-cli dev --port 4200
```

This will:
- Register `FocusCostUsage` data model
- Create ClickHouse table `FocusCostUsage_0_0`
- Expose ingestion endpoint `/ingest/FocusCostUsage`
- Register consumption APIs under `/consumption/*`

### 2. Run Ingestion Test
```bash
cd /home/chris/repo/area-code/odw/services/data-warehouse
source .venv/bin/activate
python app/focus_billing/test_moose_ingestion.py
```

### 3. Run End-to-End Test
```bash
cd /home/chris/repo/area-code/odw/services/data-warehouse
source .venv/bin/activate
python app/focus_billing/test_end_to_end_moose.py
```

### 4. Query Consumption APIs
```bash
# Cost Comparison
curl -X POST http://localhost:4200/consumption/CostComparison \
  -H "Content-Type: application/json" \
  -d '{
    "billing_period_start": "2025-07-01",
    "billing_period_end": "2025-08-01"
  }'

# Effective Cost Analysis
curl -X POST http://localhost:4200/consumption/EffectiveCostAnalysis \
  -H "Content-Type: application/json" \
  -d '{
    "billing_period_start": "2025-07-01",
    "billing_period_end": "2025-08-01",
    "service_category": "Networking"
  }'
```

## Test Data
Sample parquet files available at:
```
/home/chris/repo/area-code/bia_admin/bia_backend/workflows/focus_billing/data/focus/
├── 20250701-20250731/  (22 files)
├── 20250801-20250831/  (38 files)
└── 20250901-20250930/  (37 files)
```

Test with specific file:
```
/home/chris/repo/area-code/bia_admin/bia_backend/workflows/focus_billing/data/focus/20250701-20250731/202507161527/cc47e41e-a6ab-462e-9b26-fe7237024648/part_0_0001.snappy.parquet
```

## Benefits of Moose Stack Approach

1. **Schema Sync**: ClickHouse tables auto-generated from Pydantic models
2. **Type Safety**: Validation happens before data reaches ClickHouse
3. **Streaming**: Data flows through Redpanda for real-time processing
4. **DLQ**: Failed records captured for debugging
5. **Versioning**: Model versions (e.g., `_0_0`, `_0_1`) enable schema evolution
6. **Consistency**: Same patterns as other ingest pipelines (Blob, Event, Log)
7. **Observability**: Built-in metrics and monitoring via Moose

## Next Steps

1. Start Moose service and verify `FocusCostUsage_0_0` table creation
2. Run ingestion workflow to load test data
3. Create PascalCase view `focus_data_table` for YAML query compatibility:
   ```sql
   CREATE VIEW focus_data_table AS
   SELECT
       billing_account_id AS BillingAccountId,
       billed_cost AS BilledCost,
       effective_cost AS EffectiveCost,
       -- ... all columns
   FROM FocusCostUsage_0_0;
   ```
4. Test consumption APIs with ingested data
5. Add Contract Commitment model when data becomes available
6. Implement additional FOCUS supported features (location, resource usage, etc.)

## Files Modified/Created

### Modified
- `.kiro/specs/focus_billing/design.md` - Updated design spec
- `app/focus_billing/workflow.py` - Use Moose ingestion
- `app/ingest/__init__.py` - Import FOCUS models

### Created
- `app/ingest/focus/__init__.py` - Package init
- `app/ingest/focus/models.py` - FOCUS data models
- `app/focus_billing/moose_ingestion_adapter.py` - HTTP API adapter
- `app/apis/focus_features.py` - Consumption APIs
- `app/focus_billing/test_moose_ingestion.py` - Ingestion test
- `app/focus_billing/test_end_to_end_moose.py` - E2E test
- `IMPLEMENTATION_SUMMARY.md` - This document
