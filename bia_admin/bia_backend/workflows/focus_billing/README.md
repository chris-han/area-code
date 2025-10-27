# FOCUS Billing Integration Module

This module provides FOCUS-compliant billing data integration for the Moose data warehouse. It implements the FinOps Open Cost and Usage Specification (FOCUS) for standardized cloud billing data.

## Overview

The FOCUS billing module includes:

- **Core Data Models**: Pydantic models for FOCUS Cost & Usage and Contract Commitment datasets
- **Schema Management**: Automatic loading of FOCUS column specifications from YAML files
- **Configuration Management**: Centralized configuration for data paths and ClickHouse connections
- **Type Mapping**: Utilities for converting between FOCUS and ClickHouse data types
- **Interfaces**: Abstract interfaces for extensible data ingestion and query processing

## Directory Structure

```
app/focus_billing/
├── __init__.py                 # Module exports
├── README.md                   # This file
├── config.py                   # Configuration management
├── constants.py                # FOCUS-specific constants and enums
├── models.py                   # Pydantic data models
├── validate_setup.py           # Setup validation script
├── focus_standard/             # FOCUS specification files
│   ├── queries/                # FOCUS query YAML files
│   └── specifications/         # FOCUS column specifications
├── interfaces/                 # Abstract interfaces
│   ├── __init__.py
│   ├── data_ingestion.py       # Data ingestion interface
│   ├── ddl_generator.py        # DDL generation interface
│   ├── query_loader.py         # Query loading interface
│   └── schema_loader.py        # Schema loading interface
├── schema/                     # Schema management
│   ├── __init__.py
│   └── loader.py               # Schema loader implementation
├── tests/                      # Test suite
│   ├── __init__.py
│   └── test_config.py          # Configuration tests
└── utils/                      # Utility functions
    ├── __init__.py
    ├── naming.py               # Naming convention utilities
    ├── type_mapping.py         # Type conversion utilities
    └── validation.py           # Data validation utilities
```

## Key Components

### Data Models

- **FocusCostUsage**: Represents FOCUS Cost & Usage dataset rows
- **FocusContractCommitment**: Represents FOCUS Contract Commitment dataset rows
- **FocusColumn**: Metadata for FOCUS column specifications
- **FocusDataset**: Complete dataset schema information
- **FocusQuery**: Query definitions from YAML files

### Configuration

The `FocusBillingConfig` class manages:
- FOCUS data file paths
- ClickHouse connection settings
- Processing parameters (batch size, workers, etc.)
- Table and view naming conventions

### Schema Management

The schema loader automatically reads FOCUS column specifications from:
- `focus_standard/specifications/columns.yaml` - Column metadata
- `focus_standard/queries/` - Query definitions

### Interfaces

Abstract interfaces provide extensibility for:
- **ISchemaLoader**: Loading FOCUS specifications
- **IDataIngestionEngine**: Processing Parquet files
- **IDDLGenerator**: Generating ClickHouse DDL
- **IQueryLoader**: Managing FOCUS queries

## Usage

### Basic Import

```python
from app.focus_billing import (
    FocusBillingConfig,
    FocusCostUsage,
    FocusTableNames
)

# Create configuration
config = FocusBillingConfig()

# Load schema
from app.focus_billing.schema import FocusSchemaLoader
loader = FocusSchemaLoader()
schema = loader.load_dataset_schema('cost_and_usage')
```

### Configuration

```python
# Environment variables (optional)
export FOCUS_DATA_ROOT="/path/to/focus/data"
export CLICKHOUSE_HOST="your-clickhouse-host"
export CLICKHOUSE_PASSWORD="your-password"

# Or use defaults from config
config = FocusBillingConfig()
print(config.get_clickhouse_url())
```

## Validation

Run the setup validation to ensure everything is working:

```bash
cd odw/services/data-warehouse
python -m app.focus_billing.validate_setup
```

## FOCUS Specification

This module implements the FinOps Open Cost and Usage Specification (FOCUS):
- **Version**: 1.0+
- **Datasets**: Cost & Usage, Contract Commitment
- **Columns**: 57 standardized columns with proper typing
- **Features**: Mandatory, Recommended, and Conditional columns

## Next Steps

This module provides the foundation for:
1. **Data Ingestion**: Processing FOCUS Parquet files
2. **DDL Generation**: Creating ClickHouse tables and views
3. **Query Catalog**: Managing FOCUS use case queries
4. **API Integration**: Consumption APIs for FOCUS data

## Dependencies

- `pydantic>=2.0.0` - Data validation and serialization
- `PyYAML>=6.0.0` - YAML file parsing
- `clickhouse-connect` - ClickHouse database connectivity
- `pyarrow>=16.1.0` - Parquet file processing