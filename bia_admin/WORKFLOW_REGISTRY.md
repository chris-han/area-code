# Dynamic Workflow Registry

## Overview

The BIA Admin backend now uses **dynamic workflow discovery** instead of hardcoding workflow types. Workflows are automatically discovered at runtime by scanning the `temporal_worker.py` configuration in the data-warehouse service.

## Benefits

✅ **No Hardcoding Required**: Workflow types are discovered automatically
✅ **Auto-Registration**: New workflows are detected when added to `temporal_worker.py`
✅ **Metadata Rich**: Includes descriptions, estimated durations, and display names
✅ **Fallback Safe**: Falls back to hardcoded workflows if discovery fails
✅ **Type Safe**: Maintains backward compatibility with existing code

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ data-warehouse/app/workflows/temporal_worker.py             │
│                                                             │
│ Worker(                                                     │
│   workflows=[                                              │
│     FocusBillingTemporalWorkflow,  ←─┐                    │
│     SchemaMigrationWorkflow,       ←─┤                    │
│   ]                                   │                    │
│ )                                     │                    │
└───────────────────────────────────────┼────────────────────┘
                                        │
                                        │ Discovery
                                        │
┌───────────────────────────────────────▼────────────────────┐
│ bia_backend/services/workflow_registry.py                  │
│                                                             │
│ • Scans temporal_worker.py source code                    │
│ • Extracts workflow class names from Worker()             │
│ • Converts class names to workflow_type identifiers       │
│ • Loads metadata (descriptions, durations, display names)  │
│ • Provides singleton registry for fast lookup             │
└────────────────────────────────────────────────────────────┘
                                        │
                                        │ Registry API
                                        │
┌───────────────────────────────────────▼────────────────────┐
│ bia_backend/services/workflow_management.py                │
│                                                             │
│ • Uses registry for workflow validation                    │
│ • Gets metadata for duration estimates                     │
│ • Maintains backward compatibility with WorkflowType enum  │
└────────────────────────────────────────────────────────────┘
                                        │
                                        │ REST API
                                        │
┌───────────────────────────────────────▼────────────────────┐
│ GET /api/v1/workflows/types                                │
│                                                             │
│ Returns:                                                    │
│ {                                                           │
│   "workflows": [                                            │
│     {                                                       │
│       "workflow_type": "focus_billing_ingest",             │
│       "workflow_class": "FocusBillingTemporalWorkflow",    │
│       "display_name": "FOCUS Billing Ingest",              │
│       "description": "Ingest FOCUS billing data...",       │
│       "estimated_duration": "10-20 minutes"                │
│     },                                                      │
│     ...                                                     │
│   ]                                                         │
│ }                                                           │
└────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Workflow Discovery

The `WorkflowRegistry` class automatically discovers workflows:

```python
from bia_backend.services.workflow_registry import get_workflow_registry

registry = get_workflow_registry()
```

Discovery process:
1. Imports `app.workflows.temporal_worker` module
2. Reads the source file and parses `Worker(workflows=[...])` list
3. Extracts workflow class names using regex
4. Converts class names to workflow_type identifiers
5. Loads metadata for each workflow

### 2. Naming Conventions

Workflow class names are automatically converted to identifiers:

```python
FocusBillingTemporalWorkflow → focus_billing_ingest
SchemaMigrationWorkflow      → schema_migration
DataValidationWorkflow       → data_validation
```

Conversion rules:
- Remove `Workflow` and `Temporal` suffixes
- Convert PascalCase to snake_case
- Result is the workflow_type identifier

### 3. Metadata Extraction

Each workflow includes:
- `workflow_type`: Identifier (e.g., `"focus_billing_ingest"`)
- `workflow_class`: Class name (e.g., `"FocusBillingTemporalWorkflow"`)
- `display_name`: Human-readable name (e.g., `"FOCUS Billing Ingest"`)
- `description`: Workflow docstring or default description
- `estimated_duration`: Inferred from workflow type (e.g., `"10-20 minutes"`)

### 4. Fallback Mechanism

If workflow discovery fails (e.g., running outside data-warehouse context):
- Falls back to hardcoded workflow definitions
- Ensures system remains functional
- Logs warning about failed discovery

## API Usage

### List Available Workflows

```bash
curl http://localhost:4300/api/v1/workflows/types
```

Response:
```json
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

### Trigger Workflow (Same as Before)

```bash
curl -X POST http://localhost:4300/api/v1/workflows/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "focus_billing_ingest",
    "parameters": {
      "data_root": "app/focus_billing/data/focus",
      "batch_size": 1000
    }
  }'
```

## Adding New Workflows

To add a new workflow:

1. **Create the workflow class** in data-warehouse:
   ```python
   # app/my_module/my_workflow.py
   from temporalio import workflow

   @workflow.defn
   class MyNewWorkflow:
       """My new workflow description"""

       @workflow.run
       async def run(self, params):
           # Workflow implementation
           pass
   ```

2. **Register in temporal_worker.py**:
   ```python
   from app.my_module.my_workflow import MyNewWorkflow

   Worker(
       self.client,
       task_queue=task_queue,
       workflows=[
           FocusBillingTemporalWorkflow,
           SchemaMigrationWorkflow,
           MyNewWorkflow,  # ← Add here
       ],
       activities=[...]
   )
   ```

3. **That's it!** The workflow is now:
   - ✅ Automatically discovered
   - ✅ Available in `/api/v1/workflows/types`
   - ✅ Can be triggered via `/api/v1/workflows/trigger`
   - ✅ Has metadata populated automatically

## Registry API

### Python API

```python
from bia_backend.services.workflow_registry import get_workflow_registry

registry = get_workflow_registry()

# List all workflow types
workflow_types = registry.get_workflow_types()
# → ['focus_billing_ingest', 'schema_migration']

# Get workflow metadata
workflow = registry.get_workflow('focus_billing_ingest')
# → {
#     'workflow_type': 'focus_billing_ingest',
#     'workflow_class': 'FocusBillingTemporalWorkflow',
#     'display_name': 'FOCUS Billing Ingest',
#     'description': '...',
#     'estimated_duration': '10-20 minutes'
#   }

# Convert class name to workflow_type
wf_type = registry.class_name_to_workflow_type('FocusBillingTemporalWorkflow')
# → 'focus_billing_ingest'

# Convert workflow_type to class name
class_name = registry.workflow_type_to_class_name('focus_billing_ingest')
# → 'FocusBillingTemporalWorkflow'
```

## Backward Compatibility

The `WorkflowType` enum in `workflow_management.py` is maintained for backward compatibility:

```python
class WorkflowType(str, Enum):
    """Workflow type identifiers (dynamically populated)"""

    # Fallback static values for type hints
    FOCUS_BILLING_INGEST = "focus_billing_ingest"
    SCHEMA_MIGRATION = "schema_migration"

    @classmethod
    def _missing_(cls, value):
        """Allow dynamic workflow types not in the enum"""
        registry = _get_registry()
        if value in registry.get_workflow_types():
            return cls._value2member_map_.get(value, None)
        return None
```

This means:
- ✅ Existing code using `WorkflowType.FOCUS_BILLING_INGEST` still works
- ✅ New dynamically discovered workflows are also supported
- ✅ Type hints and IDE autocomplete work correctly

## Testing

Run the test script to verify workflow discovery:

```bash
python test_workflow_registry.py
```

Expected output:
```
================================================================================
Dynamic Workflow Registry Test
================================================================================

✅ Discovered 2 workflow types:
   - focus_billing_ingest
   - schema_migration

📋 Workflow Metadata:
--------------------------------------------------------------------------------

Workflow Type: focus_billing_ingest
Display Name:  FOCUS Billing Ingest
Class Name:    FocusBillingTemporalWorkflow
Duration:      10-20 minutes
Description:   Ingest FOCUS billing data from Parquet files into ClickHouse
...
```

## Files Changed

- ✅ `bia_backend/services/workflow_registry.py` - New workflow discovery system
- ✅ `bia_backend/services/workflow_management.py` - Uses registry for metadata
- ✅ `bia_backend/routers/workflow_management_router.py` - Added `/types` endpoint
- ✅ `test_workflow_registry.py` - Test script demonstrating functionality

## Future Enhancements

Possible future improvements:

1. **PostgreSQL Registry**: Store workflow metadata in PostgreSQL for persistence
2. **Workflow Versioning**: Track workflow versions and migrations
3. **Dependency Tracking**: Auto-discover workflow dependencies
4. **Parameter Schemas**: Extract and validate workflow parameters
5. **Performance Metrics**: Track workflow execution statistics
6. **Hot Reload**: Watch temporal_worker.py for changes and auto-reload
