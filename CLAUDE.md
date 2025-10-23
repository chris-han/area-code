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