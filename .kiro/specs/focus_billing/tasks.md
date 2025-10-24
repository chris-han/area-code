# Focus Billing Integration Implementation Plan

- [-] 1. Set up project structure and core interfaces
  - Create directory structure for FOCUS billing module under `app/focus_billing/`
  - Define core data models and interfaces for FOCUS datasets
  - Set up configuration management for FOCUS data paths and ClickHouse connections

- [ ] 2. Implement FOCUS dataset schema definitions
- [ ] 2.1 Create Cost & Usage table schema with FOCUS metadata
  - Define `focus_cost_usage` table with snake_case columns and FOCUS metadata tags
  - Implement column type mappings (Decimal(38,18), DateTime64, Nullable types)
  - Add partitioning by `toYYYYMM(usage_date)` and appropriate indexes
  - Include metadata for column_type, feature_level, allows_nulls from FOCUS spec

- [ ] 2.2 Create Contract Commitment table schema with FOCUS metadata
  - Define `focus_contract_commitment` table mirroring FOCUS Contract Commitment dataset
  - Implement 1:1 column mapping with snake_case storage and metadata preservation
  - Set up referential integrity with `contract_commitment_id` as shared key

- [ ] 2.3 Create helper views and manifest table
  - Implement `focus_data_table` view projecting snake_case to PascalCase for YAML compatibility
  - Create `focus_contract_commitment_view` with canonical casing
  - Define `focus_ingest_manifest` table for tracking processed Parquet files

- [ ]* 2.4 Write unit tests for schema definitions
  - Test column metadata extraction and validation
  - Verify type mapping correctness
  - Test view projections and naming conversions

- [ ] 3. Build ClickHouse DDL generation and execution
- [ ] 3.1 Implement DDL generator using FOCUS specifications
  - Create module to generate CREATE TABLE statements from FOCUS dataset specs
  - Parse `FOCUS_Spec/specification/datasets/` to extract column definitions
  - Generate appropriate ClickHouse data types and constraints

- [ ] 3.2 Execute DDL against ClickHouse using Moose MCP tools
  - Use `moose-dev__query_olap` to create tables in ClickHouse
  - Implement verification via DESCRIBE checks
  - Store companion DDL in `app/focus_billing/tables.py` for reapplication

- [ ]* 3.3 Add DDL validation tests
  - Test DDL generation from FOCUS specs
  - Mock ClickHouse execution and verify generated SQL

- [ ] 4. Implement FOCUS query catalog system
- [ ] 4.1 Create YAML query loader and parser
  - Parse `resources/queries/*.yaml` files into `FocusQuery` models
  - Replace `focus_data_table` references with ClickHouse view names
  - Extract and validate parameter specifications (start_date, end_date)

- [ ] 4.2 Build query parameter handling system
  - Convert positional `?` placeholders to named parameters for ClickHouse
  - Implement parameter validation and type coercion
  - Handle date range parameters and optional bind variables

- [ ]* 4.3 Add query loader tests
  - Test YAML parsing and model conversion
  - Verify parameter extraction and validation
  - Test query normalization and table reference replacement

- [ ] 5. Create FOCUS billing consumption APIs
- [ ] 5.1 Implement core API endpoints
  - Build `list_focus_use_cases` API for query metadata index
  - Create `get_focus_use_case` API for single query details
  - Implement `execute_focus_use_case` API with parameter binding and pagination

- [ ] 5.2 Add supported features API
  - Parse `FOCUS_Spec/specification/supported_features/` markdown files
  - Expose structured metadata for UI rendering and API consumers
  - Create `list_supported_features` endpoint

- [ ] 5.3 Register APIs and add request/response validation
  - Register APIs in app startup configuration
  - Implement pydantic models for request/response validation
  - Add error handling and descriptive error messages

- [ ]* 5.4 Write API integration tests
  - Test API endpoints with mock ClickHouse responses
  - Verify parameter validation and error handling
  - Test pagination and result formatting

- [ ] 6. Build FOCUS data ingestion workflow
- [ ] 6.1 Implement Parquet discovery and processing
  - Create file discovery system for `FOCUS_DATA_ROOT` directory
  - Read `manifest.json` metadata for row counts and periods
  - Implement file tracking to skip already processed files

- [ ] 6.2 Create data transformation pipeline
  - Load Parquet files using pyarrow with schema mapping
  - Transform column names from PascalCase to snake_case
  - Apply type conversions (INT96 to DateTime64, decimals, booleans to UInt8)
  - Add computed columns (id, source_system, created_at, updated_at)

- [ ] 6.3 Implement ClickHouse batch insertion
  - Use `clickhouse_connect` client for chunked inserts (10k row batches)
  - Handle both Cost & Usage and Contract Commitment datasets
  - Implement error handling and manifest logging for success/failure

- [ ] 6.4 Create workflow orchestration and configuration
  - Expose workflow via Moose `Workflow` object
  - Add CLI logging and progress reporting
  - Implement configuration via environment variables and dataclass params

- [ ]* 6.5 Add workflow integration tests
  - Mock file discovery and ClickHouse insertion
  - Test error handling and manifest tracking
  - Verify data transformation correctness

- [ ] 7. Implement configuration and environment management
- [ ] 7.1 Set up environment configuration
  - Define `FOCUS_DATA_ROOT` environment variable with fallback
  - Reuse ClickHouse credentials from `moose.config.toml`
  - Add optional workflow parameters (batch size, concurrency)

- [ ] 7.2 Add observability and validation features
  - Implement metrics emission (rows ingested, files processed, duration)
  - Add table existence verification before ingestion
  - Validate `contract_commitment_id` referential integrity between datasets

- [ ]* 7.3 Write configuration tests
  - Test environment variable handling and defaults
  - Verify ClickHouse credential reuse
  - Test configuration validation

- [ ] 8. Create documentation and operational guides
- [ ] 8.1 Write comprehensive documentation
  - Update repo README with FOCUS billing integration instructions
  - Document all environment variables and configuration options
  - Create operational checklist for DDL application and workflow execution

- [ ] 8.2 Document dataset caveats and limitations
  - Note missing contracted metrics in sample Parquet files
  - Document JSON type differences between local and production environments
  - Provide troubleshooting guide for common issues

- [ ] 9. Implement end-to-end validation and testing
- [ ] 9.1 Create smoke test suite
  - Ingest small Parquet sample and verify table population
  - Execute YAML queries via API to confirm round-trip functionality
  - Validate data integrity and query result accuracy

- [ ] 9.2 Automate verification against existing test results
  - Run `clickhouse-local` query verification using `verification_results_clickhouse.json`
  - Surface expected zero-row cases (contracted savings) in CI output
  - Compare results with existing FOCUS MCP server validation

- [ ]* 9.3 Add comprehensive test coverage
  - Integration tests for full ingestion workflow
  - API endpoint testing with real ClickHouse queries
  - Performance testing for large dataset ingestion
