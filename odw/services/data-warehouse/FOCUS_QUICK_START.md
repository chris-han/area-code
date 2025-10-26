# FOCUS Billing - Quick Start Guide

## 🚀 What's Been Implemented

✅ **Moose Data Models** - FOCUS 1.2 Cost and Usage schema
✅ **Ingestion Pipeline** - Parquet → Moose HTTP API → ClickHouse
✅ **Consumption APIs** - 5 FOCUS supported features
✅ **Pytest Tests** - 17 tests for VSCode Test Explorer
✅ **Test Data** - 97 parquet files ready to ingest

## ⚡ Quick Commands

### 1. Start Moose (Required for Testing)
```bash
cd /home/chris/repo/area-code/odw/services/data-warehouse
source .venv/bin/activate
.venv/bin/moose-cli dev --port 4200
```
**Wait for**: "Server listening on port 4200" + table creation logs

### 2. Run Unit Tests (VSCode or CLI)
```bash
# VSCode: Open Test Explorer (Flask icon) → Click play button

# CLI:
pytest app/focus_billing/tests/ -m "not integration" -v
```
**Result**: ✅ 6 tests pass (no Moose needed)

### 3. Run Integration Tests (Moose Required)
```bash
# Terminal 1: Moose running
# Terminal 2:
source .venv/bin/activate
pytest app/focus_billing/tests/ -m integration -v
```
**Result**: 🟡 Tests will skip if Moose not running, ✅ pass if running

### 4. Ingest Test Data
```bash
source .venv/bin/activate
python app/focus_billing/test_moose_ingestion.py
```
**Result**: Ingests 1 file (~2-5 rows) to test the pipeline

### 5. Query Consumption APIs
```bash
# Cost Comparison
curl -X POST http://localhost:4200/consumption/CostComparison \
  -H "Content-Type: application/json" \
  -d '{"billing_period_start":"2025-07-01","billing_period_end":"2025-08-01"}'

# Effective Cost Analysis
curl -X POST http://localhost:4200/consumption/EffectiveCostAnalysis \
  -H "Content-Type: application/json" \
  -d '{"billing_period_start":"2025-07-01","billing_period_end":"2025-08-01"}'
```

## 📁 Key Files

### Code
```
app/
├── ingest/focus/models.py          ← Moose data model (FOCUS schema)
├── focus_billing/
│   ├── workflow.py                 ← Ingestion orchestration
│   ├── moose_ingestion_adapter.py  ← HTTP API client
│   └── data_transformer.py         ← Parquet → Pydantic
└── apis/focus_features.py          ← Consumption APIs
```

### Tests
```
app/focus_billing/tests/
├── test_moose_ingestion_workflow.py  ← 8 ingestion tests
└── test_moose_consumption_apis.py    ← 9 API tests
```

### Docs
```
IMPLEMENTATION_SUMMARY.md              ← Complete overview
FOCUS_QUICK_START.md                   ← This file
app/focus_billing/
├── README_MOOSE_TESTING.md           ← Testing guide
├── VSCODE_TEST_SETUP.md              ← VSCode test setup
└── tests/README.md                   ← Test documentation
```

### Config
```
pytest.ini                            ← Pytest configuration
.vscode/settings.json                 ← VSCode test settings
.kiro/specs/focus_billing/design.md  ← Design spec
```

## 🎯 Test Data Locations

**Sample file** (used in tests):
```
app/focus_billing/data/focus/20250701-20250731/202507161527/cc47e41e-a6ab-462e-9b26-fe7237024648/part_0_0001.snappy.parquet
```

**All available data**:
- July 2025: 22 files
- August 2025: 38 files
- September 2025: 37 files
- **Total**: 97 parquet files

## 🔍 VSCode Test Explorer

### View Tests
1. Click **Flask icon** in left sidebar
2. See 17 tests under `app/focus_billing/tests/`
3. Click play button to run

### Test Categories
- 🟢 **Unit** (6 tests) - Fast, no Moose needed
- 🟡 **Integration** (9 tests) - Requires Moose
- 🔴 **E2E** (1 test) - Full stack + data
- ⏭️ **Slow** (1 test) - Performance benchmarks

### Filter Tests
```bash
# Unit only
pytest -m "not integration" -v

# Integration only
pytest -m integration -v

# Specific test
pytest app/focus_billing/tests/test_moose_ingestion_workflow.py::TestMooseIngestionWorkflow::test_workflow_initialization -v
```

## 🏗️ Architecture Flow

```
┌─────────────┐
│ Parquet     │  FOCUS 1.2 Azure export
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ File Discovery  │  Scan directories, read manifests
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Data Transform  │  PascalCase → snake_case, types
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Moose Adapter   │  POST /ingest/FocusCostUsage
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Moose API       │  Validate, stream, write
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ ClickHouse      │  FocusCostUsage_0_0 table
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Consumption API │  5 FOCUS features
└─────────────────┘
```

## 📊 Consumption APIs

### 1. Cost Comparison
**Endpoint**: `/consumption/CostComparison`
**Purpose**: Compare BilledCost, ContractedCost, EffectiveCost, ListCost
**Returns**: Discount percentages by service

### 2. Effective Cost Analysis
**Endpoint**: `/consumption/EffectiveCostAnalysis`
**Purpose**: Track spending after discounts and amortization
**Returns**: Cost aggregated by service, region, pricing unit

### 3. Commitment Discount Purchases
**Endpoint**: `/consumption/CommitmentDiscountPurchases`
**Purpose**: Report on reservation/savings plan purchases
**Returns**: Commitment details and costs

### 4. Correction Charges
**Endpoint**: `/consumption/CorrectionCharges`
**Purpose**: Identify billing adjustments
**Returns**: Corrections grouped by service

### 5. Recurring Charges
**Endpoint**: `/consumption/RecurringCharges`
**Purpose**: Analyze recurring commitment fees
**Returns**: Commitment recurring charges

## 🐛 Common Issues

### Issue: Tests not in VSCode Test Explorer
**Fix**:
1. Select Python interpreter: `.venv/bin/python`
2. Reload window: `Cmd/Ctrl + Shift + P` → "Reload Window"

### Issue: Integration tests skipping
**Fix**: Start Moose service first
```bash
.venv/bin/moose-cli dev --port 4200
```

### Issue: "No files discovered"
**Fix**: Check test data exists
```bash
ls app/focus_billing/data/focus/20250701-20250731/
```

### Issue: Import errors
**Fix**: Run from correct directory
```bash
cd /home/chris/repo/area-code/odw/services/data-warehouse
pytest app/focus_billing/tests/ -v
```

## 📚 Documentation Links

- **Design Spec**: `.kiro/specs/focus_billing/design.md`
- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Test Setup**: `app/focus_billing/VSCODE_TEST_SETUP.md`
- **Testing Guide**: `app/focus_billing/README_MOOSE_TESTING.md`
- **Test Docs**: `app/focus_billing/tests/README.md`

## ✅ Success Checklist

- [ ] Moose starts successfully on port 4200
- [ ] 17 tests appear in VSCode Test Explorer
- [ ] 6 unit tests pass (no Moose)
- [ ] 9 integration tests pass (with Moose)
- [ ] Test ingestion script runs successfully
- [ ] ClickHouse table `FocusCostUsage_0_0` created
- [ ] Sample data ingested (2-5 rows)
- [ ] Consumption APIs return 200 OK

## 🎉 What's Working

✅ Complete FOCUS 1.2 data model (100+ fields)
✅ Moose-native ingestion pipeline
✅ Automatic ClickHouse schema generation
✅ Type-safe Pydantic validation
✅ HTTP API ingestion with batching
✅ 5 consumption APIs for FOCUS features
✅ Pytest tests for VSCode integration
✅ 97 test parquet files ready
✅ Comprehensive documentation

## 🚧 Next Steps

1. Create PascalCase view for YAML queries
2. Add Contract Commitment data model
3. Implement additional FOCUS features (location, resource usage)
4. Set up continuous ingestion workflow
5. Configure production deployment

---

**Quick Support**: See `VSCODE_TEST_SETUP.md` for troubleshooting
