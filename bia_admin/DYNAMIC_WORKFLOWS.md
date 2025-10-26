# End-to-End Dynamic Workflow System

## Overview

The BIA Admin system now features **fully dynamic workflow discovery** from backend to frontend. Workflows are discovered at runtime, eliminating all hardcoded workflow types across the entire stack.

## Architecture Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. Workflow Definition (data-warehouse)                         │
│    app/workflows/temporal_worker.py                             │
│                                                                   │
│    Worker(workflows=[                                           │
│      FocusBillingTemporalWorkflow,    # ← Define once          │
│      SchemaMigrationWorkflow,         # ← Define once          │
│    ])                                                            │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. Runtime Discovery (bia_backend)                              │
│    services/workflow_registry.py                                │
│                                                                   │
│    • Scans temporal_worker.py source code                       │
│    • Extracts workflow class names via regex                    │
│    • Converts to workflow_type identifiers                      │
│    • Generates metadata (names, descriptions, durations)        │
│    • Caches in singleton registry                               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. REST API Exposure (bia_backend)                              │
│    routers/workflow_management_router.py                        │
│                                                                   │
│    GET /api/v1/workflows/types                                  │
│    {                                                             │
│      "workflows": [                                              │
│        {                                                         │
│          "workflow_type": "focus_billing_ingest",               │
│          "display_name": "FOCUS Billing Ingest",                │
│          "description": "Ingest FOCUS billing data...",         │
│          "estimated_duration": "10-20 minutes"                  │
│        }                                                         │
│      ]                                                           │
│    }                                                             │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. Frontend Consumption (bia-frontend)                          │
│    app/workflows/new/page.tsx                                   │
│                                                                   │
│    • Fetches from /api/v1/workflows/types on mount             │
│    • Dynamically renders workflow cards                         │
│    • Shows loading/error states                                 │
│    • Auto-generates icons and tags                              │
│    • Displays workflow metadata                                 │
└──────────────────────────────────────────────────────────────────┘
```

## Complete Data Flow

### 1. Workflow Registration (Data Warehouse)

```python
# app/workflows/temporal_worker.py
from app.focus_billing.temporal_workflow import FocusBillingTemporalWorkflow
from app.focus_billing.schema_migration import SchemaMigrationWorkflow

Worker(
    client,
    task_queue='bia-workflows',
    workflows=[
        FocusBillingTemporalWorkflow,  # Registered here
        SchemaMigrationWorkflow,       # Registered here
    ]
)
```

### 2. Backend Discovery (BIA Backend)

```python
# services/workflow_registry.py
registry = get_workflow_registry()
workflows = registry.get_workflows()

# Result:
[
    {
        'workflow_type': 'focus_billing_ingest',
        'workflow_class': 'FocusBillingTemporalWorkflow',
        'display_name': 'FOCUS Billing Ingest',
        'description': 'Ingest FOCUS billing data from Parquet files',
        'estimated_duration': '10-20 minutes'
    },
    {
        'workflow_type': 'schema_migration',
        'workflow_class': 'SchemaMigrationWorkflow',
        'display_name': 'Schema Migration',
        'description': 'Detect and apply schema migrations',
        'estimated_duration': '5-30 minutes'
    }
]
```

### 3. API Endpoint (BIA Backend)

```typescript
// GET http://localhost:4300/api/v1/workflows/types

{
  "success": true,
  "workflows": [
    {
      "workflow_type": "focus_billing_ingest",
      "workflow_class": "FocusBillingTemporalWorkflow",
      "display_name": "FOCUS Billing Ingest",
      "description": "Ingest FOCUS billing data from Parquet files into ClickHouse",
      "estimated_duration": "10-20 minutes"
    },
    {
      "workflow_type": "schema_migration",
      "workflow_class": "SchemaMigrationWorkflow",
      "display_name": "Schema Migration",
      "description": "Detect and apply schema migrations for FOCUS data",
      "estimated_duration": "5-30 minutes"
    }
  ],
  "total": 2,
  "message": "Found 2 registered workflow types"
}
```

### 4. Frontend Display (BIA Frontend)

```typescript
// app/workflows/new/page.tsx
const [workflowTypes, setWorkflowTypes] = useState<WorkflowType[]>([])

useEffect(() => {
  fetch('http://localhost:4300/api/v1/workflows/types')
    .then(res => res.json())
    .then(data => setWorkflowTypes(data.workflows))
}, [])

// Renders workflow cards dynamically:
// - FOCUS Billing Ingest (10-20 minutes)
// - Schema Migration (5-30 minutes)
```

## Key Features

### 🎯 Single Source of Truth
- Workflows defined **once** in `temporal_worker.py`
- No duplication across backend/frontend
- Changes propagate automatically

### 🔄 Runtime Discovery
- No hardcoded workflow lists
- New workflows auto-register
- Backend scans temporal_worker at startup

### 🎨 Smart UI Generation
- Icons chosen based on workflow type
- Complexity calculated from duration
- Tags extracted from workflow name
- All metadata from backend

### 🛡️ Resilient Design
- Fallback to hardcoded workflows if discovery fails
- Loading states in frontend
- Error handling with retry
- Graceful degradation

## Adding New Workflows

### Step 1: Create Workflow Class

```python
# app/my_feature/my_workflow.py
from temporalio import workflow

@workflow.defn
class DataExportWorkflow:
    """Export data to external systems"""

    @workflow.run
    async def run(self, params):
        # Implementation
        pass
```

### Step 2: Register in Temporal Worker

```python
# app/workflows/temporal_worker.py
from app.my_feature.my_workflow import DataExportWorkflow

Worker(
    client,
    workflows=[
        FocusBillingTemporalWorkflow,
        SchemaMigrationWorkflow,
        DataExportWorkflow,  # ← Add here
    ]
)
```

### Step 3: Done! 🎉

The workflow is now:
- ✅ Discovered by backend registry
- ✅ Exposed via `/api/v1/workflows/types`
- ✅ Displayed in frontend UI
- ✅ Available for triggering

**No changes needed in:**
- ❌ workflow_management.py
- ❌ WorkflowType enum
- ❌ Frontend page.tsx
- ❌ API endpoints

## Frontend Implementation Details

### TypeScript Interfaces

```typescript
interface WorkflowType {
  workflow_type: string        // "focus_billing_ingest"
  workflow_class: string        // "FocusBillingTemporalWorkflow"
  display_name: string          // "FOCUS Billing Ingest"
  description: string           // Full description
  estimated_duration: string    // "10-20 minutes"
}

interface WorkflowTypesResponse {
  success: boolean
  workflows: WorkflowType[]
  total: number
  message: string
}
```

### Dynamic Rendering

```typescript
// Icons based on workflow type
const getIconForWorkflowType = (workflowType: string) => {
  if (workflowType.includes('ingest')) return <Database />
  if (workflowType.includes('migration')) return <Settings />
  if (workflowType.includes('transformation')) return <Zap />
  return <Workflow />
}

// Complexity from duration
const getComplexityForWorkflow = (duration: string) => {
  if (duration.includes('5-')) return 'Low'
  if (duration.includes('10-20')) return 'Medium'
  return 'High'
}

// Tags from workflow type
const getTagsForWorkflowType = (workflowType: string) => {
  const tags = []
  if (workflowType.includes('focus')) tags.push('FOCUS')
  if (workflowType.includes('billing')) tags.push('Billing')
  if (workflowType.includes('ingest')) tags.push('Ingestion')
  return tags
}
```

### Loading States

```typescript
{loading && (
  <div className="flex items-center justify-center py-8">
    <Loader2 className="h-8 w-8 animate-spin" />
    <span>Loading workflow types...</span>
  </div>
)}

{error && (
  <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
    <p>Failed to load workflow types</p>
    <Button onClick={fetchWorkflowTypes}>Retry</Button>
  </div>
)}
```

## Benefits Summary

### For Developers
- ✅ Define workflows once in temporal_worker.py
- ✅ No frontend/backend synchronization needed
- ✅ Add workflows without touching UI code
- ✅ Type-safe interfaces throughout

### For Operations
- ✅ Workflows auto-register on deployment
- ✅ No manual configuration updates
- ✅ Single point of workflow management
- ✅ Audit trail of registered workflows

### For End Users
- ✅ Always see current available workflows
- ✅ Accurate metadata and descriptions
- ✅ Clear estimated durations
- ✅ Consistent UI experience

## Testing the Complete Flow

### 1. Test Backend API

```bash
curl http://localhost:4300/api/v1/workflows/types | jq
```

Expected:
```json
{
  "success": true,
  "workflows": [
    {
      "workflow_type": "focus_billing_ingest",
      "display_name": "FOCUS Billing Ingest",
      ...
    }
  ],
  "total": 2
}
```

### 2. Test Frontend

1. Start BIA frontend: `cd bia-frontend && npm run dev`
2. Navigate to: `http://localhost:3003/workflows/new`
3. Verify:
   - ✅ Workflow cards load dynamically
   - ✅ Shows "Loading workflow types..." initially
   - ✅ Displays FOCUS Billing Ingest
   - ✅ Displays Schema Migration
   - ✅ Shows metadata (duration, description)
   - ✅ Auto-generated icons and tags

### 3. Test Adding New Workflow

1. Add new workflow to temporal_worker.py
2. Restart BIA backend
3. Refresh frontend page
4. New workflow appears automatically!

## Files Modified

### Backend
- ✅ `services/workflow_registry.py` - New discovery system
- ✅ `services/workflow_management.py` - Uses registry
- ✅ `routers/workflow_management_router.py` - Added `/types` endpoint

### Frontend
- ✅ `app/workflows/new/page.tsx` - Converted to client component, fetches dynamically

## Migration from Old System

### Before (Hardcoded)

**Backend:**
```python
class WorkflowType(str, Enum):
    AZURE_BILLING = "azure_billing_extraction"
    FOCUS_TRANSFORM = "focus_transformation"
    # ... 5+ hardcoded types
```

**Frontend:**
```typescript
const workflowTypes = [
  { id: 'azure_billing', name: '...' },
  { id: 'focus_transform', name: '...' },
  // ... 5+ hardcoded types
]
```

### After (Dynamic)

**Backend:**
```python
# No hardcoded types needed!
registry = get_workflow_registry()
workflows = registry.get_workflows()  # Discovered at runtime
```

**Frontend:**
```typescript
// No hardcoded types needed!
const [workflows, setWorkflows] = useState([])
fetch('/api/v1/workflows/types')  // Fetched from backend
```

## Troubleshooting

### Issue: Frontend shows "No workflow types available"

**Solution:**
1. Check BIA backend is running on port 4300
2. Test API: `curl http://localhost:4300/api/v1/workflows/types`
3. Check browser console for CORS errors
4. Verify CORS middleware in backend app.py

### Issue: Workflows not discovered

**Solution:**
1. Check temporal_worker.py has workflows registered
2. Restart BIA backend to reload registry
3. Check backend logs for discovery errors
4. Verify fallback workflows are loaded

### Issue: Frontend shows old Azure workflows

**Solution:**
1. Hard refresh browser (Ctrl+Shift+R)
2. Clear browser cache
3. Verify page.tsx has been updated with 'use client'
4. Check fetch URL is correct (port 4300)
