# Frontend Dynamic Workflow Integration - Complete

## Summary

Successfully removed **all hardcoded workflow types** from the frontend. The workflow dropdown now fetches available workflows dynamically from the BIA backend API at runtime.

## Changes Made

### 1. Updated `components/workflow-form.tsx`

**Before:**
```typescript
// Hardcoded workflow options
import { WORKFLOW_TYPE_OPTIONS } from '@/lib/schemas'

{WORKFLOW_TYPE_OPTIONS.map((option) => (
  <option key={option.value} value={option.value}>
    {option.label}
  </option>
))}
```

**After:**
```typescript
// Dynamic workflow fetching
const [workflowTypes, setWorkflowTypes] = useState<WorkflowType[]>([])

useEffect(() => {
  fetch('http://localhost:4300/api/v1/workflows/types')
    .then(res => res.json())
    .then(data => setWorkflowTypes(data.workflows))
}, [])

{workflowTypes.map((workflow) => (
  <option key={workflow.workflow_type} value={workflow.workflow_type}>
    {workflow.display_name} ({workflow.estimated_duration})
  </option>
))}
```

**Features Added:**
- ✅ Fetches workflows from `/api/v1/workflows/types` on mount
- ✅ Loading state with spinner
- ✅ Error handling with retry button
- ✅ Shows display name and estimated duration
- ✅ Disables form when no workflows available

### 2. Updated `lib/schemas.ts`

**Before:**
```typescript
// Hardcoded enum with 7 workflow types
const workflowTypeEnum = z.enum([
  'azure_billing_extraction',
  'focus_transformation',
  'data_validation',
  'azure_blob_ingest',
  'scheduled_report',
  'test_workflow',
  'focus_billing_ingest',
])

export const WORKFLOW_TYPE_OPTIONS = [
  { value: 'azure_billing_extraction', label: 'Azure Billing Extraction' },
  { value: 'focus_transformation', label: 'FOCUS Transformation' },
  // ... 7 hardcoded options
]
```

**After:**
```typescript
// Dynamic string validation
export const workflowTriggerSchema = z.object({
  workflow_type: z.string().min(1, 'Workflow type is required'),
  parameters: z.record(z.any()).optional().default({}),
  schedule: z.string().optional(),
})

export type WorkflowType = string
```

**Changes:**
- ❌ Removed hardcoded `workflowTypeEnum`
- ❌ Removed hardcoded `WORKFLOW_TYPE_OPTIONS` array
- ✅ Changed to flexible string validation
- ✅ Backend validates actual workflow types

### 3. Updated `app/workflows/new/page.tsx`

**Before:**
```typescript
// Hardcoded array of 5 workflow types
const workflowTypes = [
  {
    id: 'azure_billing_extraction',
    name: 'Azure Billing Data Extraction',
    // ... hardcoded metadata
  },
  // ... 5 hardcoded workflows
]
```

**After:**
```typescript
// Dynamic fetching
const [workflowTypes, setWorkflowTypes] = useState<WorkflowType[]>([])

useEffect(() => {
  fetch('http://localhost:4300/api/v1/workflows/types')
    .then(res => res.json())
    .then(data => setWorkflowTypes(data.workflows))
}, [])
```

## Complete Frontend Architecture

```
┌────────────────────────────────────────────────────────┐
│ User Opens Page                                        │
│ - /workflows (main workflows page)                    │
│ - /workflows/new (new workflow page)                  │
└────────────────────────────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────┐
│ Component Mounts                                       │
│ - WorkflowForm component                              │
│ - NewWorkflowPage component                           │
└────────────────────────────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────┐
│ useEffect Hook Runs                                    │
│ fetchWorkflowTypes()                                   │
└────────────────────────────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────┐
│ API Request                                            │
│ GET http://localhost:4300/api/v1/workflows/types      │
└────────────────────────────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────┐
│ Backend Response                                       │
│ {                                                      │
│   "workflows": [                                       │
│     {                                                  │
│       "workflow_type": "focus_billing_ingest",        │
│       "display_name": "FOCUS Billing Ingest",         │
│       "description": "...",                            │
│       "estimated_duration": "10-20 minutes"           │
│     },                                                 │
│     {                                                  │
│       "workflow_type": "schema_migration",            │
│       "display_name": "Schema Migration",             │
│       "description": "...",                            │
│       "estimated_duration": "5-30 minutes"            │
│     }                                                  │
│   ]                                                    │
│ }                                                      │
└────────────────────────────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────┐
│ State Update                                           │
│ setWorkflowTypes(data.workflows)                      │
└────────────────────────────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────┐
│ UI Renders                                             │
│ - Dropdown shows: FOCUS Billing Ingest (10-20 min)   │
│ - Dropdown shows: Schema Migration (5-30 min)        │
│ - Cards render with metadata                          │
└────────────────────────────────────────────────────────┘
```

## UI States

### Loading State
```
┌─────────────────────────────────────┐
│ Workflow Type                       │
│ ┌─────────────────────────────────┐ │
│ │ ⟳ Loading workflow types...     │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Error State
```
┌─────────────────────────────────────┐
│ Workflow Type                       │
│ ┌─────────────────────────────────┐ │
│ │ ⚠ Failed to load workflow types │ │
│ └─────────────────────────────────┘ │
│ [ Retry ]                           │
└─────────────────────────────────────┘
```

### Success State
```
┌─────────────────────────────────────┐
│ Workflow Type                       │
│ ┌─────────────────────────────────┐ │
│ │ Select a workflow type        ▼ │ │
│ │ ┌─────────────────────────────┐ │ │
│ │ │ FOCUS Billing Ingest (10-20)│ │ │
│ │ │ Schema Migration (5-30 min) │ │ │
│ │ └─────────────────────────────┘ │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## User Experience

### Before (Hardcoded)
- ❌ Showed 7 old Azure workflows
- ❌ Workflows were out of date
- ❌ Included deprecated workflows
- ❌ Required frontend code changes to add workflows
- ❌ Frontend/backend could get out of sync

### After (Dynamic)
- ✅ Shows only current workflows (2 FOCUS workflows)
- ✅ Always up-to-date with backend
- ✅ No deprecated workflows shown
- ✅ New workflows appear automatically
- ✅ Frontend/backend always in sync
- ✅ Loading and error states
- ✅ Better UX with metadata in dropdown

## Testing

### 1. Test Main Workflows Page

```bash
# Start frontend
cd bia_admin/bia-frontend
npm run dev

# Visit: http://localhost:3003/workflows
```

**Expected:**
1. Page loads
2. "Create New Workflow" section shows dropdown
3. Dropdown shows "Loading workflow types..." briefly
4. Dropdown populates with:
   - "FOCUS Billing Ingest (10-20 minutes)"
   - "Schema Migration (5-30 minutes)"

### 2. Test New Workflow Page

```bash
# Visit: http://localhost:3003/workflows/new
```

**Expected:**
1. Page loads with workflow cards
2. Shows "Loading workflow types..." briefly
3. Two workflow cards appear:
   - FOCUS Billing Ingest
   - Schema Migration
4. Each card shows:
   - Display name
   - Description
   - Estimated duration
   - Auto-generated icon
   - Tags (FOCUS, Billing, etc.)
   - Complexity badge

### 3. Test Error Handling

```bash
# Stop BIA backend
# Visit: http://localhost:3003/workflows
```

**Expected:**
1. Dropdown shows "Failed to load workflow types"
2. "Retry" button appears
3. Click retry to fetch again
4. Form is disabled until workflows load

### 4. Test Form Submission

1. Select "FOCUS Billing Ingest" from dropdown
2. Click "Trigger Workflow"
3. Workflow triggers successfully
4. Success message appears

## Benefits

### For Users
- ✅ Always see current available workflows
- ✅ Clear estimated durations in dropdown
- ✅ Better loading experience
- ✅ Error handling with retry option
- ✅ No outdated workflow options

### For Developers
- ✅ No frontend code changes to add workflows
- ✅ Single source of truth (backend registry)
- ✅ Type-safe TypeScript interfaces
- ✅ Reduced maintenance burden
- ✅ Frontend automatically updates with backend

## Migration Impact

### Removed Hardcoded Workflows

These old Azure workflows are no longer shown:
- ❌ `azure_billing_extraction` - Azure Billing Extraction
- ❌ `focus_transformation` - FOCUS Transformation
- ❌ `data_validation` - Data Quality Check
- ❌ `azure_blob_ingest` - Azure Blob Ingest
- ❌ `scheduled_report` - Scheduled Report
- ❌ `test_workflow` - Test Workflow (Mock Ingest)

### Current Dynamic Workflows

Only these FOCUS workflows are shown (dynamically):
- ✅ `focus_billing_ingest` - FOCUS Billing Ingest (10-20 minutes)
- ✅ `schema_migration` - Schema Migration (5-30 minutes)

## Files Modified

### Components
- ✅ `src/components/workflow-form.tsx` - Dynamic dropdown with API fetch
- ✅ `src/app/workflows/new/page.tsx` - Dynamic workflow cards

### Configuration
- ✅ `src/lib/schemas.ts` - Removed hardcoded enums, flexible validation

## Future Enhancements

### 1. Caching
Add workflow types to React Query cache:
```typescript
const { data: workflowTypes } = useQuery({
  queryKey: ['workflowTypes'],
  queryFn: fetchWorkflowTypes,
  staleTime: 5 * 60 * 1000, // 5 minutes
})
```

### 2. Real-time Updates
Use WebSocket to get notified when workflows change:
```typescript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:4300/ws/workflow-types')
  ws.onmessage = (event) => {
    setWorkflowTypes(JSON.parse(event.data))
  }
}, [])
```

### 3. Advanced Metadata
Show more workflow details:
- Prerequisites
- Expected outputs
- Parameter schemas
- Historical execution stats

### 4. Workflow Templates
Pre-fill parameters from templates:
```typescript
<option value="focus_billing_ingest" data-template="monthly">
  FOCUS Billing - Monthly Template
</option>
```

## Troubleshooting

### Issue: Dropdown shows "No workflow types available"

**Solution:**
1. Check BIA backend is running: `curl http://localhost:4300/api/v1/workflows/types`
2. Check browser console for errors
3. Verify CORS is enabled in backend
4. Check network tab in DevTools

### Issue: Old Azure workflows still showing

**Solution:**
1. Hard refresh browser (Ctrl+Shift+R)
2. Clear browser cache
3. Verify files are updated:
   - `components/workflow-form.tsx` fetches dynamically
   - `lib/schemas.ts` has no hardcoded enum
4. Restart Next.js dev server

### Issue: Dropdown shows wrong workflows

**Solution:**
1. Check backend registry: `python test_workflow_registry.py`
2. Verify temporal_worker.py has correct workflows
3. Restart BIA backend to reload registry
4. Check backend logs for discovery errors

## Success Metrics

✅ **Zero hardcoded workflow types in frontend**
✅ **Frontend always in sync with backend**
✅ **Better UX with loading states**
✅ **Error handling with retry**
✅ **Metadata-rich dropdown options**
✅ **Reduced maintenance overhead**
