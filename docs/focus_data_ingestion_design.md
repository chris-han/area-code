# Focus Data Ingestion Workflow Design

## Overview

The focus data ingestion workflow automates schema discovery, ClickHouse table management, and data migration for Azure billing exports that adhere to the FOCUS specification. The Temporal workflow coordinates a set of lightweight activities backed by the shared `parquet_to_clickhouse_schema_py` converter to keep SQL DDL and Pydantic models in sync. Dynamic dispatch keeps runtime behaviour extensible while allowing schema execution logic to live outside the worker.

## Flow Overview

```mermaid
flowchart TD
    A[Trigger Workflow] --> B[Detect Schema Diff]
    B -->|No drift| C[Return Current Version]
    B -->|Drift| D[Generate Schema Artifacts]
    D --> E[Persist SQL & Pydantic Model]
    E --> F[Dynamic Dispatch Activity]
    F --> G[Execute ClickHouse DDL]
    G --> H[Generate Transformation SQL]
    H --> I[Apply Transformation & Load Data]
    I --> J[Emit Observability + Results]
```

## Temporal Sequence

```mermaid
sequenceDiagram
    participant Client
    participant Workflow as SchemaMigrationWorkflow
    participant Detect as detect_schema_diff()
    participant Generator as generate_schema_artifacts_activity()
    participant Dispatcher as dynamic_dispatch()
    participant ClickHouse
    participant Transform as generate_transformation_code()
    participant Loader as apply_transformation_and_load_data()

    Client->>Workflow: start(source_parquet_path, canonical_schema_path, version)
    Workflow->>Detect: execute_activity(...)
    Detect-->>Workflow: diff_dict
    alt Requires migration
        Workflow->>Generator: execute_activity(...)
        Generator-->>Workflow: {ddl_path, model_path}
        Workflow->>Dispatcher: execute_activity("execute_clickhouse_schema", ddl_path)
        Dispatcher->>ClickHouse: DROP/CREATE statements
        ClickHouse-->>Dispatcher: execution status
        Dispatcher-->>Workflow: {"executed_statements": n}
        Workflow->>Transform: execute_activity(diff_dict)
        Transform-->>Workflow: transform_sql
        Workflow->>Loader: execute_activity(transform_sql, new_version)
        Loader-->>Workflow: {"rows_migrated": m}
    else No migration
        Workflow-->>Client: {"migration_needed": false, "version": version}
    end
    Workflow-->>Client: migration summary + artifact paths
```

## Class Structure

```mermaid
classDiagram
    class SchemaMigrationWorkflow {
        +run(source, canonical, current_version) dict
        -Path artifacts_dir
    }
    class SchemaArtifacts {
        +Path ddl_path
        +Path model_path
    }
    class SchemaArtifactsGenerator {
        +generate_schema_artifacts(parquet, output_dir, table, pk, class) SchemaArtifacts
    }
    class DynamicDispatcher {
        +dynamic_dispatch(activity_name, payload) dict
        -load_logic_from_db(name) Callable
    }
    class FocusBillingConfig {
        +get_clickhouse_connection_params() dict
        +focus_data_root: str
    }
    class FocusCostUsageRecord {
        +FOCUS columns...
    }

    SchemaMigrationWorkflow --> SchemaArtifactsGenerator : uses
    SchemaMigrationWorkflow --> DynamicDispatcher : delegates
    DynamicDispatcher --> FocusBillingConfig : reads connection
    SchemaArtifactsGenerator --> FocusCostUsageRecord : emits model
```

## Implementation Notes

- **Schema generation**: `generate_schema_artifacts_activity` wraps `generate_schema_artifacts` (which uses the shared converter) and persists artifacts to `bia_admin/bia_backend/workflows/focus_billing/schema_migration/generated/`.
- **Version control**: Generated SQL (`focus_cost_usage.sql`) and the matching Pydantic model (`FocusCostUsageRecord.py`) are checked into the repository to make schema deltas reviewable.
- **Dynamic dispatch**: The dispatcher activity keeps a registry (`execute_clickhouse_schema`) that can be extended to invoke different operations stored in a metadata store.
- **Config isolation**: ClickHouse credentials are resolved through `FocusBillingConfig` so no secrets are hardcoded into activities.
- **Testing**: `tests/test_dynamic_dispatch.py` stubs the ClickHouse client to verify that generated statements are executed without requiring a running cluster.
- **Extensibility**: The same pattern supports additional datasets by pointing the artifact generator at new Parquet samples and registering new activity handlers.
