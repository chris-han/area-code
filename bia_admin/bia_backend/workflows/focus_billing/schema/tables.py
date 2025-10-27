"""
FOCUS Dataset Table Schema Definitions

This module defines ClickHouse table schemas for FOCUS datasets with proper
metadata, type mappings, and partitioning strategies.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from app.focus_billing.utils.naming import to_snake_case
from app.focus_billing.utils.type_mapping import map_focus_to_clickhouse_type
from app.focus_billing.schema.loader import FocusSchemaLoader


@dataclass
class ClickHouseColumn:
    """Represents a ClickHouse column definition"""

    name: str
    clickhouse_type: str
    nullable: bool = False
    comment: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


@dataclass
class ClickHouseTable:
    """Represents a ClickHouse table definition"""

    name: str
    columns: List[ClickHouseColumn]
    engine: str = "MergeTree"
    partition_by: Optional[str] = None
    order_by: Optional[List[str]] = None
    primary_key: Optional[List[str]] = None
    settings: Optional[Dict[str, str]] = None
    comment: Optional[str] = None


class FocusTableSchemaGenerator:
    """Generates ClickHouse table schemas from FOCUS specifications"""

    def __init__(self):
        self.schema_loader = FocusSchemaLoader()

    def generate_cost_usage_table(self) -> ClickHouseTable:
        """
        Generate ClickHouse table schema for FOCUS Cost & Usage dataset

        Returns:
            ClickHouseTable: Complete table definition with metadata
        """
        # Load FOCUS column specifications
        columns_spec = self.schema_loader.load_columns_specification()

        # Define core columns that are always present
        core_columns = [
            ClickHouseColumn(
                name="id",
                clickhouse_type="String",
                nullable=False,
                comment="Deterministic hash ID for the row",
                metadata={"column_type": "Dimension", "feature_level": "Internal"},
            ),
            ClickHouseColumn(
                name="usage_date",
                clickhouse_type="Date",
                nullable=False,
                comment="Date when the usage occurred (derived from ChargePeriodStart)",
                metadata={"column_type": "Dimension", "feature_level": "Internal"},
            ),
        ]

        # Generate columns from FOCUS specification
        focus_columns = []
        for col_spec in columns_spec:
            # Skip columns that don't belong in Cost & Usage dataset
            if col_spec.name in ["ContractCommitmentId"]:  # This goes in separate table
                continue

            snake_name = to_snake_case(col_spec.name)
            clickhouse_type = map_focus_to_clickhouse_type(
                col_spec.data_type, col_spec.allows_nulls
            )

            focus_columns.append(
                ClickHouseColumn(
                    name=snake_name,
                    clickhouse_type=clickhouse_type,
                    nullable=col_spec.allows_nulls,
                    comment=col_spec.description,
                    metadata={
                        "column_type": col_spec.column_type,
                        "feature_level": col_spec.feature_level,
                        "focus_column_id": col_spec.name,
                        "data_type": col_spec.data_type,
                        "allows_nulls": str(col_spec.allows_nulls),
                    },
                )
            )

        # Add audit columns
        audit_columns = [
            ClickHouseColumn(
                name="source_system",
                clickhouse_type="String",
                nullable=False,
                comment="Source system identifier",
                metadata={"column_type": "Dimension", "feature_level": "Internal"},
            ),
            ClickHouseColumn(
                name="created_at",
                clickhouse_type="DateTime64(3)",
                nullable=False,
                comment="Record creation timestamp",
                metadata={"column_type": "Dimension", "feature_level": "Internal"},
            ),
            ClickHouseColumn(
                name="updated_at",
                clickhouse_type="DateTime64(3)",
                nullable=False,
                comment="Record update timestamp",
                metadata={"column_type": "Dimension", "feature_level": "Internal"},
            ),
        ]

        all_columns = core_columns + focus_columns + audit_columns

        return ClickHouseTable(
            name="focus_cost_usage",
            columns=all_columns,
            engine="MergeTree",
            partition_by="toYYYYMM(usage_date)",
            order_by=["usage_date", "billing_account_id", "service_category", "service_name"],
            settings={"index_granularity": "8192", "allow_nullable_key": "1"},
            comment="FOCUS Cost & Usage dataset with snake_case column names and FOCUS metadata",
        )

    def generate_contract_commitment_table(self) -> ClickHouseTable:
        """
        Generate ClickHouse table schema for FOCUS Contract Commitment dataset

        Returns:
            ClickHouseTable: Complete table definition with metadata
        """
        # Contract commitment specific columns based on FOCUS spec
        # These are the columns that appear in the Contract Commitment dataset
        contract_commitment_columns = [
            "BillingCurrency",
            "ContractCommitmentId",
            "ContractId",
            "ContractPeriodStart",
            "ContractPeriodEnd",
            "ContractCommitmentPeriodStart",
            "ContractCommitmentPeriodEnd",
            "ContractCommitmentDescription",
            "ContractCommitmentType",
            "ContractCommitmentCategory",
            "ContractCommitmentUnit",
            "ContractCommitmentQuantity",
            "ContractCommitmentCost",
        ]

        # Load FOCUS column specifications
        columns_spec = self.schema_loader.load_columns_specification()

        # Define core columns
        core_columns = [
            ClickHouseColumn(
                name="id",
                clickhouse_type="String",
                nullable=False,
                comment="Deterministic hash ID for the row",
                metadata={"column_type": "Dimension", "feature_level": "Internal"},
            )
        ]

        # Generate columns from FOCUS specification for contract commitment
        focus_columns = []
        for col_spec in columns_spec:
            if col_spec.name not in contract_commitment_columns:
                continue

            snake_name = to_snake_case(col_spec.name)
            clickhouse_type = map_focus_to_clickhouse_type(
                col_spec.data_type, col_spec.allows_nulls
            )

            focus_columns.append(
                ClickHouseColumn(
                    name=snake_name,
                    clickhouse_type=clickhouse_type,
                    nullable=col_spec.allows_nulls,
                    comment=col_spec.description,
                    metadata={
                        "column_type": col_spec.column_type,
                        "feature_level": col_spec.feature_level,
                        "focus_column_id": col_spec.name,
                        "data_type": col_spec.data_type,
                        "allows_nulls": str(col_spec.allows_nulls),
                    },
                )
            )

        # Add audit columns
        audit_columns = [
            ClickHouseColumn(
                name="source_system",
                clickhouse_type="String",
                nullable=False,
                comment="Source system identifier",
                metadata={"column_type": "Dimension", "feature_level": "Internal"},
            ),
            ClickHouseColumn(
                name="created_at",
                clickhouse_type="DateTime64(3)",
                nullable=False,
                comment="Record creation timestamp",
                metadata={"column_type": "Dimension", "feature_level": "Internal"},
            ),
            ClickHouseColumn(
                name="updated_at",
                clickhouse_type="DateTime64(3)",
                nullable=False,
                comment="Record update timestamp",
                metadata={"column_type": "Dimension", "feature_level": "Internal"},
            ),
        ]

        all_columns = core_columns + focus_columns + audit_columns

        return ClickHouseTable(
            name="focus_contract_commitment",
            columns=all_columns,
            engine="MergeTree",
            order_by=["contract_commitment_id", "billing_account_id"],
            settings={"index_granularity": "8192", "allow_nullable_key": "1"},
            comment="FOCUS Contract Commitment dataset with snake_case column names and FOCUS metadata",
        )

    def generate_ingest_manifest_table(self) -> ClickHouseTable:
        """
        Generate ClickHouse table schema for FOCUS ingestion manifest

        Returns:
            ClickHouseTable: Complete table definition for tracking processed files
        """
        columns = [
            ClickHouseColumn(
                name="id",
                clickhouse_type="String",
                nullable=False,
                comment="Unique manifest entry ID",
            ),
            ClickHouseColumn(
                name="file_path",
                clickhouse_type="String",
                nullable=False,
                comment="Relative path to processed file",
            ),
            ClickHouseColumn(
                name="file_checksum",
                clickhouse_type="String",
                nullable=False,
                comment="File checksum for change detection",
            ),
            ClickHouseColumn(
                name="dataset_type",
                clickhouse_type="String",
                nullable=False,
                comment="Dataset type (cost_usage or contract_commitment)",
            ),
            ClickHouseColumn(
                name="rows_processed",
                clickhouse_type="UInt64",
                nullable=False,
                comment="Number of rows processed",
            ),
            ClickHouseColumn(
                name="processing_status",
                clickhouse_type="String",
                nullable=False,
                comment="Processing status (success, failed, skipped)",
            ),
            ClickHouseColumn(
                name="error_message",
                clickhouse_type="Nullable(String)",
                nullable=True,
                comment="Error message if processing failed",
            ),
            ClickHouseColumn(
                name="processed_at",
                clickhouse_type="DateTime64(3)",
                nullable=False,
                comment="Processing timestamp",
            ),
            ClickHouseColumn(
                name="manifest_metadata",
                clickhouse_type="Nullable(String)",
                nullable=True,
                comment="Additional metadata from manifest.json as JSON string",
            ),
        ]

        return ClickHouseTable(
            name="focus_ingest_manifest",
            columns=columns,
            engine="MergeTree",
            order_by=["processed_at", "dataset_type"],
            settings={"index_granularity": "8192"},
            comment="Manifest table for tracking processed FOCUS Parquet files",
        )


class FocusViewGenerator:
    """Generates ClickHouse view definitions for FOCUS compatibility"""

    def __init__(self):
        self.schema_loader = FocusSchemaLoader()

    def generate_cost_usage_view(self) -> str:
        """
        Generate view that projects snake_case columns to PascalCase for YAML compatibility

        Returns:
            str: CREATE VIEW SQL statement
        """
        columns_spec = self.schema_loader.load_columns_specification()

        # Build column mappings from snake_case to PascalCase
        column_mappings = []

        # Add core columns
        column_mappings.append("id AS Id")
        column_mappings.append("usage_date AS UsageDate")

        # Add FOCUS columns
        for col_spec in columns_spec:
            if col_spec.name in ["ContractCommitmentId"]:  # Skip contract commitment columns
                continue
            snake_name = to_snake_case(col_spec.name)
            column_mappings.append(f"{snake_name} AS {col_spec.name}")

        # Add audit columns
        column_mappings.extend(
            ["source_system AS SourceSystem", "created_at AS CreatedAt", "updated_at AS UpdatedAt"]
        )

        columns_sql = ",\n    ".join(column_mappings)

        return f"""CREATE VIEW focus_data_table AS
SELECT
    {columns_sql}
FROM focus_cost_usage"""

    def generate_contract_commitment_view(self) -> str:
        """
        Generate view for Contract Commitment table with canonical casing

        Returns:
            str: CREATE VIEW SQL statement
        """
        # Contract commitment columns that should be exposed
        contract_commitment_columns = [
            "BillingCurrency",
            "ContractCommitmentId",
            "ContractId",
            "ContractPeriodStart",
            "ContractPeriodEnd",
            "ContractCommitmentPeriodStart",
            "ContractCommitmentPeriodEnd",
            "ContractCommitmentDescription",
            "ContractCommitmentType",
            "ContractCommitmentCategory",
            "ContractCommitmentUnit",
            "ContractCommitmentQuantity",
            "ContractCommitmentCost",
        ]

        # Build column mappings
        column_mappings = ["id AS Id"]

        for col_id in contract_commitment_columns:
            snake_name = to_snake_case(col_id)
            column_mappings.append(f"{snake_name} AS {col_id}")

        # Add audit columns
        column_mappings.extend(
            ["source_system AS SourceSystem", "created_at AS CreatedAt", "updated_at AS UpdatedAt"]
        )

        columns_sql = ",\n    ".join(column_mappings)

        return f"""CREATE VIEW focus_contract_commitment_view AS
SELECT
    {columns_sql}
FROM focus_contract_commitment"""


def generate_ddl_statements() -> Dict[str, str]:
    """
    Generate all DDL statements for FOCUS tables and views

    Returns:
        Dict[str, str]: Dictionary mapping object names to DDL statements
    """
    table_generator = FocusTableSchemaGenerator()
    view_generator = FocusViewGenerator()

    ddl_statements = {}

    # Generate table DDL
    cost_usage_table = table_generator.generate_cost_usage_table()
    ddl_statements["focus_cost_usage"] = _table_to_ddl(cost_usage_table)

    contract_commitment_table = table_generator.generate_contract_commitment_table()
    ddl_statements["focus_contract_commitment"] = _table_to_ddl(contract_commitment_table)

    manifest_table = table_generator.generate_ingest_manifest_table()
    ddl_statements["focus_ingest_manifest"] = _table_to_ddl(manifest_table)

    # Generate view DDL
    ddl_statements["focus_data_table"] = view_generator.generate_cost_usage_view()
    ddl_statements["focus_contract_commitment_view"] = (
        view_generator.generate_contract_commitment_view()
    )

    return ddl_statements


def get_companion_ddl_for_reapplication() -> str:
    """
    Get companion DDL statements for reapplication in app/focus_billing/tables.py
    
    Returns:
        str: Complete DDL script for reapplication
    """
    ddl_statements = generate_ddl_statements()
    
    # Create SQL file content for reapplication
    sql_content = []
    sql_content.append("-- FOCUS Billing Integration DDL Statements")
    sql_content.append("-- Companion DDL for reapplication")
    sql_content.append("-- Generated from FOCUS specifications")
    sql_content.append("")
    
    # Add drop statements first (in reverse dependency order)
    sql_content.append("-- Drop existing objects (in reverse dependency order)")
    sql_content.append("DROP VIEW IF EXISTS focus_data_table;")
    sql_content.append("DROP VIEW IF EXISTS focus_contract_commitment_view;")
    sql_content.append("DROP TABLE IF EXISTS focus_cost_usage;")
    sql_content.append("DROP TABLE IF EXISTS focus_contract_commitment;")
    sql_content.append("DROP TABLE IF EXISTS focus_ingest_manifest;")
    sql_content.append("")
    
    # Add create statements in proper order
    creation_order = [
        ("focus_cost_usage", "Cost & Usage Table"),
        ("focus_contract_commitment", "Contract Commitment Table"),
        ("focus_ingest_manifest", "Ingestion Manifest Table"),
        ("focus_data_table", "Cost & Usage View (PascalCase)"),
        ("focus_contract_commitment_view", "Contract Commitment View (PascalCase)")
    ]
    
    for obj_name, description in creation_order:
        if obj_name in ddl_statements:
            sql_content.append(f"-- {description}")
            sql_content.append(ddl_statements[obj_name] + ";")
            sql_content.append("")
    
    return '\n'.join(sql_content)


def _table_to_ddl(table: ClickHouseTable) -> str:
    """
    Convert ClickHouseTable to CREATE TABLE DDL statement

    Args:
        table: ClickHouseTable definition

    Returns:
        str: CREATE TABLE SQL statement
    """
    # Build column definitions
    column_defs = []
    for col in table.columns:
        col_def = f"{col.name} {col.clickhouse_type}"
        if col.comment:
            # Escape single quotes in comments
            escaped_comment = col.comment.replace("'", "\\'")
            col_def += f" COMMENT '{escaped_comment}'"
        column_defs.append(col_def)

    columns_sql = ",\n    ".join(column_defs)

    # Build table definition
    ddl = f"CREATE TABLE {table.name} (\n    {columns_sql}\n)"

    # Add engine
    ddl += f"\nENGINE = {table.engine}()"

    # Add partition by
    if table.partition_by:
        ddl += f"\nPARTITION BY {table.partition_by}"

    # Add order by
    if table.order_by:
        order_cols = ", ".join(table.order_by)
        ddl += f"\nORDER BY ({order_cols})"

    # Add primary key if different from order by
    if table.primary_key and table.primary_key != table.order_by:
        primary_cols = ", ".join(table.primary_key)
        ddl += f"\nPRIMARY KEY ({primary_cols})"

    # Add settings
    if table.settings:
        settings_list = [f"{k} = {v}" for k, v in table.settings.items()]
        settings_sql = ", ".join(settings_list)
        ddl += f"\nSETTINGS {settings_sql}"

    # Add table comment
    if table.comment:
        escaped_comment = table.comment.replace("'", "\\'")
        ddl += f"\nCOMMENT '{escaped_comment}'"

    return ddl
