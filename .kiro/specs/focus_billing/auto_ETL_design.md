Moose OLAP + Temporalio integration for schema-aware transformation orchestration. It’s modular, reproducible, and future-proofed for your FOCUS_Spec pipeline.

---


# 🧠 Moose OLAP + Temporal Workflow for Schema-Aware Transformation

## Overview

This spec defines a modular architecture that integrates Moose OLAP with Temporalio to dynamically detect schema drift, generate transformation logic, and ingest source data into versioned ClickHouse tables aligned with the FOCUS canonical schema.

---

## 🎯 Goals

- Automatically detect schema drift between source data and canonical FOCUS schema
- Generate transformation logic using Moose OLAP
- Apply migration plans safely using versioned ClickHouse tables and materialized views
- Orchestrate the entire process via Temporal workflows for auditability and resilience

---

## 🧩 Components

### 1. Canonical Schema Source

- Location: `/home/chris/repo/area-code/FOCUS_Spec/specification/datasets`
- Format: JSON/YAML spec defining target schema
- Parsed into Moose OLAP Python types using a custom parser

### 2. Sample Source Data

- Format: JSON, Parquet, or CSV
- Used by Moose to infer source schema

### 3. Moose OLAP

- Defines canonical ClickHouse tables and materialized views
- Performs schema diffing and generates transformation logic
- Supports versioned migrations and backfill via materialized views

### 4. Temporal Workflow

- Orchestrates transformation generation and ingestion
- Ensures deterministic replay and modular activity separation

---

## 🛠 Workflow Breakdown

### Workflow: `SchemaMigrationWorkflow`

```python
@workflow.defn
class SchemaMigrationWorkflow:
    @workflow.run
    async def run(self, source_schema_path: str, canonical_schema_path: str):
        diff = await workflow.execute_activity(detect_schema_diff, source_schema_path, canonical_schema_path)
        if diff.requires_migration:
            transform_code = await workflow.execute_activity(generate_transformation_code, diff)
            await workflow.execute_activity(apply_transformation_and_load_data, transform_code)
```

---

## 🔧 Activities

### `detect_schema_diff`

- Loads source and canonical schemas
- Uses Moose to compute a structured diff
- Returns: `SchemaDiff` object

### `generate_transformation_code`

- Accepts `SchemaDiff`
- Uses Moose codegen to scaffold SQL/Python transformation logic
- Returns: transformation code string

### `apply_transformation_and_load_data`

- Applies migration plan to ClickHouse
- Creates versioned tables and materialized views
- Ingests new source data into transformed pipeline

---

## 🧬 Versioning Strategy

- Canonical tables use `config.version` to suffix ClickHouse table names
- Materialized views backfill and migrate data from old → new schema
- Readers/writers cut over after validation

---

## 🧾 Audit & Observability

- Store schema diffs and transformation code in Git or metadata table
- Hash transformation logic for traceability
- Emit Temporal signals/events for downstream observability

---

## 🧰 Optional Enhancements

- Retry logic for failed transformations
- Signal-based schema updates
- Integration with Moose Deploy and Moose Observability

---

## 📦 Deployment Notes

- Temporal Workers must register all activities
- Moose CLI (`moose dev`) can be used to validate schema and run locally
- Boreal (optional) for zero-config deployment of MooseStack apps

---

## 📚 References

- [FOCUS Spec Repository](https://github.com/chris-han/FOCUS_Spec)
- [Moose OLAP Schema Versioning Guide](https://docs.fiveonefour.com/moose/olap/schema-versioning)
- [Temporal Workflow Documentation](https://docs.temporal.io/workflows)


