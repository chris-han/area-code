# FOCUS Billing - Moose Stack Testing Guide

## Prerequisites

1. **Moose service running** on port 4200
2. **ClickHouse** accessible (managed by Moose)
3. **Test data** at `app/focus_billing/data/focus/`

## Quick Start

### 1. Start Moose Service

```bash
cd /home/chris/repo/area-code/odw/services/data-warehouse
source .venv/bin/activate
.venv/bin/moose-cli dev --port 4200
```

Wait for:
- ClickHouse table creation: `FocusCostUsage_0_0`
- Ingestion endpoint ready: `/ingest/FocusCostUsage`
- Consumption APIs registered: `/consumption/*`

### 2. Verify Moose is Running

```bash
curl http://localhost:4200/health
```

Expected: `200 OK`

### 3. Run Ingestion Test

```bash
source .venv/bin/activate
python app/focus_billing/test_moose_ingestion.py
```

This will:
- Discover FOCUS parquet files
- Transform data (PascalCase → snake_case)
- Ingest via Moose HTTP API
- Report statistics

Expected output:
```
Files discovered: 22
Files processed: 1
Total rows: 2-5 (depends on test file)
✓ Test PASSED
```

### 4. Verify Data in ClickHouse

```bash
# Via Moose MCP or direct ClickHouse client
clickhouse-client --query "SELECT COUNT(*) FROM FocusCostUsage_0_0"
```

### 5. Test Consumption APIs

```bash
# Cost Comparison API
curl -X POST http://localhost:4200/consumption/CostComparison \
  -H "Content-Type: application/json" \
  -d '{
    "billing_period_start": "2025-07-01",
    "billing_period_end": "2025-08-01"
  }'

# Effective Cost Analysis API
curl -X POST http://localhost:4200/consumption/EffectiveCostAnalysis \
  -H "Content-Type: application/json" \
  -d '{
    "billing_period_start": "2025-07-01",
    "billing_period_end": "2025-08-01"
  }'
```

### 6. Run End-to-End Test

```bash
source .venv/bin/activate
python app/focus_billing/test_end_to_end_moose.py
```

This validates:
1. ✓ Moose service health
2. ✓ Data ingestion workflow
3. ✓ ClickHouse data presence
4. ✓ Consumption API responses

## Test Data Locations

```
app/focus_billing/data/focus/
├── 20250701-20250731/
│   ├── 202507161527/cc47e41e-a6ab-462e-9b26-fe7237024648/
│   │   └── part_0_0001.snappy.parquet  ← Used in tests
│   ├── 202507170944/...
│   └── ... (22 files total)
├── 20250801-20250831/ (38 files)
└── 20250901-20250930/ (37 files)
```

## Troubleshooting

### Issue: "No files discovered"
- Check data path: `ls app/focus_billing/data/focus/20250701-20250731/`
- Update test script `data_root` parameter if needed

### Issue: "Failed to connect to Moose"
- Verify Moose is running: `curl http://localhost:4200/health`
- Check port 4200 is not in use: `lsof -i :4200`
- Review Moose logs for errors

### Issue: "Table FocusCostUsage_0_0 does not exist"
- Ensure `app/ingest/__init__.py` imports `focusCostUsageModel`
- Restart Moose service to trigger table creation
- Check Moose logs for schema errors

### Issue: "Moose ingestion failed: 400 Bad Request"
- Check data types match Pydantic model
- Review Moose validation errors in response body
- Ensure `id` field is generated correctly

### Issue: "Consumption API not found: 404"
- Verify `app/apis/focus_features.py` is loaded by Moose
- Check API registration in Moose startup logs
- Ensure API names match exactly (case-sensitive)

## Configuration

### Test Parameters

Edit `test_moose_ingestion.py`:

```python
params = FocusBillingIngestParams(
    data_root="/path/to/focus/data",
    batch_size=100,         # Records per batch
    max_files=1,           # Limit files for testing
    dry_run=False,         # Set True to skip ingestion
    period_filter="20250701-20250731",
    continue_on_error=True,
    skip_processed=False   # Reprocess for testing
)
```

### Moose Endpoint

Update in `moose_ingestion_adapter.py`:

```python
def __init__(self, batch_size=1000, moose_url="http://localhost:4200"):
```

## Data Model

The `FocusCostUsage` Pydantic model includes:

**Mandatory FOCUS columns:**
- `billing_account_id`, `billing_currency`
- `billed_cost`, `contracted_cost`, `effective_cost`, `list_cost`
- `service_category`, `service_name`
- `provider_name`, `publisher_name`, `invoice_issuer_name`
- Date fields: `billing_period_start/end`, `charge_period_start/end`

**Conditional/Recommended:**
- `region_id`, `region_name`, `resource_id`, `sku_meter`
- `pricing_quantity`, `pricing_unit`
- `commitment_discount_*` fields

**Azure Extended (x_*):**
- `x_account_id`, `x_billed_cost_in_usd`
- `x_sku_*`, `x_billing_profile_*`
- 50+ Azure-specific fields

**Audit:**
- `id` (SHA-256 hash), `source_system`, `ingested_at`

## Success Criteria

✓ Moose creates `FocusCostUsage_0_0` table
✓ Test ingests data without errors
✓ ClickHouse contains expected row count
✓ Consumption APIs return data
✓ No validation errors in Moose logs

## Next Steps

1. Create PascalCase view for YAML queries
2. Add Contract Commitment model
3. Implement additional FOCUS features
4. Set up continuous ingestion workflow
5. Configure production Moose deployment
