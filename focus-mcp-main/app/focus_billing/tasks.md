# Focus Billing Integration Tasks

1. **Schema Materialization**
   - [ ] Author ClickHouse DDL module (`tables.py`) that defines `focus_billing_data`, supporting indexes, and the `focus_data_table` view (snake_case → PascalCase projection).
   - [ ] Execute DDL against `finops-odw` using the Moose MCP ClickHouse tool; capture success via `DESCRIBE` checks.
   - [ ] Create `focus_ingest_manifest` table for tracking processed Parquet files.

2. **Query Catalog + APIs**
   - [ ] Implement YAML loader (`queries.py`) that parses `resources/queries/*.yaml` into typed models and normalizes table references.
   - [ ] Build API modules under `app/apis/focus_billing/`:
       - `list_focus_use_cases` (metadata index)
       - `get_focus_use_case` (single query detail)
       - `execute_focus_use_case` (run query with params, optional pagination)
   - [ ] Register APIs in app startup (e.g., `app/apis/__init__.py`).
   - [ ] Add unit tests covering loader validation and a happy-path query execution (mock ClickHouse client).

3. **Ingestion Workflow**
   - [ ] Create workflow module (`workflow.py`) that:
       - Discovers Parquet exports under `FOCUS_DATA_ROOT`.
       - Skips files already logged in `focus_ingest_manifest`.
       - Loads Parquet via `pyarrow`, applies schema mapping, and batches inserts using `clickhouse_connect`.
       - Writes success/failure entries to manifest table.
   - [ ] Expose workflow via Moose `Workflow` object and add CLI logging.
   - [ ] Provide configuration hook (env + dataclass params) for data root and batch size.
   - [ ] Add integration-style test (can mock file discovery and ClickHouse insert).

4. **Documentation & Ops**
   - [ ] Update repo README or new `focus_billing/README` with run instructions.
   - [ ] Document env vars (`FOCUS_DATA_ROOT`, optional `FOCUS_BATCH_SIZE`).
   - [ ] Add checklist for applying DDL + running workflow in dev.

5. **Validation**
   - [ ] Run smoke test: ingest a small Parquet sample, then execute at least one YAML query via API to confirm round trip.
   - [ ] Capture follow-up enhancements (dimension tables, compliance checks) in issue tracker.
