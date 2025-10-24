# Claude Development Notes

## Important Configuration Rules

### Docker Images & Containers
❌ **DO NOT** change Docker image versions or configurations:
- Keep existing image tags (e.g., `temporalio/auto-setup:1.29.0`)
- Don't modify docker-compose files or container configurations
- Don't update image versions from specific tags to `latest`
- Work with existing Docker setup as-is

### Development Guidelines
✅ Focus on application-level fixes rather than infrastructure changes
✅ Use existing service endpoints and configurations
✅ Test with current container setup
❌ **NEVER** use hardcoded IP addresses in code

## Current Infrastructure
- Temporal Server: `temporalio/auto-setup:1.29.0` at `172.18.0.3:7233`
- API Server: Running on port 4300
- Frontend: Expected on port 3000
- Temporal UI: Available at `localhost:8080`

## Workflow System Status
- ✅ API endpoints working (`/api/v1/workflows/list`)
- ✅ Frontend mapping logic functional
- ✅ Temporal server running in Docker
- ✅ Worker connection to `172.18.0.3:7233` established
- ❌ Worker fails due to FastAPI imports in workflow sandbox
  - Issue: `app/azure_billing/__init__.py` imports `ncei_api.py` (FastAPI)
  - Temporal sandbox restricts web framework imports
  - Frontend workflow display works correctly - shows empty list (expected)

## Testing Commands
```bash
# Test API
curl -X POST "http://localhost:4300/api/v1/workflows/list" -H "Content-Type: application/json" -d "{}"

# Test worker connection (from data-warehouse directory)
python run_worker_with_correct_host.py
```

## How to Start Temporal Workflows Correctly

### 1. Workflow System Architecture
- **Workflows**: Defined in `app/azure_billing/workflows/temporal_workflows.py`
- **Worker**: `app/azure_billing/workflows/temporal_worker.py`
- **API**: BIA backend at `localhost:4300/api/v1/workflows/`
- **Temporal Server**: Docker container at `172.18.0.3:7233`

### 2. Available Workflow Types
- `test_workflow` → `AzureBillingTestWorkflow` (generates mock data)
- `azure_billing_extraction` → `AzureBillingWorkflow`
- `focus_transformation` → `FOCUSTransformationWorkflow`
- `data_validation` → `DataValidationWorkflow`
- `azure_blob_ingest` → `AzureBlobIngestWorkflow`

### 3. Starting a Workflow
```bash
# AUTOMATIC WORKER STARTUP (NEW DEFAULT)
# The API now automatically starts run_worker_with_correct_host.py when triggering workflows

# 1. Trigger workflow via API (worker starts automatically)
curl -X POST "http://localhost:4300/api/v1/workflows/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "test_workflow",
    "parameters": {
      "record_count": 10,
      "currency": "USD",
      "lookback_days": 3
    }
  }'

# 2. Check workflow status
curl -X POST "http://localhost:4300/api/v1/workflows/status" \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "WORKFLOW_ID_FROM_RESPONSE"}'

# 3. Check worker status (optional)
curl -X GET "http://localhost:4300/api/v1/workflows/worker/status"

# 4. Manual worker management (optional)
curl -X POST "http://localhost:4300/api/v1/workflows/worker/start"   # Start worker
curl -X POST "http://localhost:4300/api/v1/workflows/worker/restart" # Restart worker
```

### 4. Critical Requirements
✅ **Worker auto-starts** when triggering workflows (uses `run_worker_with_correct_host.py` by default)
✅ **Temporal server** must be accessible at `172.18.0.3:7233`
✅ **BIA backend** must be running on port 4300
✅ **Datetime handling**: Activities must handle both datetime objects and ISO strings
✅ **Connection**: `run_worker_with_correct_host.py` is used automatically for proper Docker network connection

### 5. Common Issues & Solutions
- **Worker connection**: Use container IP (`172.18.0.3:7233`) not localhost
- **Datetime errors**: Ensure activities handle string/datetime conversion properly
- **Import errors**: Avoid FastAPI imports in workflow sandbox (keep in activities only)
- **Worker registration**: All workflows/activities must be registered in `temporal_worker.py`