# parquet-to-clickhouse-schema-py

Python implementation of the Parquet to ClickHouse schema converter. It mirrors
the behaviour of the original Rust utility while relying on PyArrow to inspect
Parquet files.

## Usage

Activate the virtual environment shipped with the data warehouse service:

```bash
source /home/chris/repo/area-code/odw/services/data-warehouse/.venv/bin/activate
```

Generate a ClickHouse schema:

```bash
python -m parquet_to_clickhouse_schema_py.cli \
  --parquet-path /path/to/file.parquet \
  --clickhouse-schema-path /tmp/schema.sql \
  --table-name focus_billing \
  --primary-key BillingAccountId \
  --pydantic-model-path /tmp/focus_billing_model.py \
  --pydantic-class-name FocusBillingRecord
```

The command writes a DDL file containing a `DROP TABLE` and `CREATE TABLE`
statement using the MergeTree engine, and (optionally) a Pydantic model that is
kept in sync with the inferred schema.
