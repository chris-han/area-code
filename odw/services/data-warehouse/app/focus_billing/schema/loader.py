"""
FOCUS Schema Loader Implementation

Concrete implementation of schema loading interfaces for FOCUS datasets.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..interfaces.schema_loader import ISchemaLoader, IColumnMetadataLoader
from ..models import FocusColumn, FocusDataset, FocusColumnType, FocusFeatureLevel, FocusDataType
from ..utils.naming import pascal_to_snake_case
from ..utils.type_mapping import map_focus_to_clickhouse_type
from ..config import focus_config
from ..constants import FocusTableNames, FocusViewNames


class FocusColumnMetadataLoader(IColumnMetadataLoader):
    """Loads FOCUS column metadata from specification files"""

    def __init__(self, spec_root: Optional[str] = None):
        self.spec_root = Path(spec_root or focus_config.focus_spec_root)
        self.specifications_root = Path(focus_config.focus_specifications_root)

    def load_column_metadata(self, dataset_name: str) -> List[FocusColumn]:
        """Load column metadata for a specific FOCUS dataset"""
        columns = []

        # Load from YAML specifications
        columns_yaml_path = self.specifications_root / "columns.yaml"
        if columns_yaml_path.exists():
            with open(columns_yaml_path, "r") as f:
                columns_data = yaml.safe_load(f)

            # The YAML contains a list of column definitions
            if isinstance(columns_data, list):
                for column_info in columns_data:
                    column_id = column_info.get("column_id", "")
                    snake_name = pascal_to_snake_case(column_id)

                    # Map data types
                    data_type = column_info.get("data_type", "String")
                    if data_type == "Date/Time":
                        data_type = "DateTime"

                    # Parse allows_nulls (it's a string in the YAML)
                    allows_nulls_str = column_info.get("allows_nulls", "True")
                    allows_nulls = allows_nulls_str.lower() == "true"

                    column = FocusColumn(
                        name=column_id,
                        snake_case_name=snake_name,
                        column_type=FocusColumnType(column_info.get("column_type", "Dimension")),
                        feature_level=FocusFeatureLevel(
                            column_info.get("feature_level", "Recommended")
                        ),
                        data_type=FocusDataType(data_type),
                        allows_nulls=allows_nulls,
                        description=column_info.get("description"),
                        clickhouse_type=self.get_clickhouse_type_mapping(data_type, allows_nulls),
                    )
                    columns.append(column)

        # If no YAML data or requesting all columns, return all loaded columns
        if not columns or dataset_name == "all":
            if columns:  # If we loaded from YAML, return all
                return columns
            else:  # Otherwise create defaults
                columns = self._create_default_columns(dataset_name)

        return columns

    def get_clickhouse_type_mapping(self, focus_data_type: str, allows_nulls: bool) -> str:
        """Map FOCUS data type to ClickHouse type"""
        return map_focus_to_clickhouse_type(focus_data_type, allows_nulls)

    def _load_from_markdown_spec(self, dataset_name: str) -> List[FocusColumn]:
        """Load column metadata from markdown specification files"""
        columns = []

        # Path to dataset specification
        dataset_path = self.spec_root / "datasets" / dataset_name
        if not dataset_path.exists():
            return columns

        # Look for dataset.md file
        dataset_md_path = dataset_path / "dataset.md"
        if dataset_md_path.exists():
            # This would require parsing markdown tables
            # For now, return basic structure
            columns = self._create_default_columns(dataset_name)

        return columns

    def _create_default_columns(self, dataset_name: str) -> List[FocusColumn]:
        """Create default column definitions for a dataset"""
        columns = []

        if dataset_name == "cost_and_usage":
            # Core mandatory columns
            mandatory_columns = [
                ("BillingAccountId", "String", "Billing Account ID"),
                ("UsageDate", "Date", "Usage Date"),
                ("BilledCost", "Decimal", "Billed Cost"),
            ]

            for name, data_type, description in mandatory_columns:
                snake_name = pascal_to_snake_case(name)
                column = FocusColumn(
                    name=name,
                    snake_case_name=snake_name,
                    column_type=(
                        FocusColumnType.DIMENSION
                        if data_type != "Decimal"
                        else FocusColumnType.METRIC
                    ),
                    feature_level=FocusFeatureLevel.MANDATORY,
                    data_type=FocusDataType(data_type),
                    allows_nulls=False,
                    description=description,
                    clickhouse_type=self.get_clickhouse_type_mapping(data_type, False),
                )
                columns.append(column)

        elif dataset_name == "contract_commitment":
            # Contract commitment columns based on FOCUS 1.3 specification
            contract_columns = [
                ("BillingCurrency", "String", "Dimension", "Mandatory", True, "Billing Currency"),
                (
                    "ContractCommitmentId",
                    "String",
                    "Dimension",
                    "Mandatory",
                    False,
                    "Contract Commitment ID",
                ),
                ("ContractId", "String", "Dimension", "Mandatory", False, "Contract ID"),
                (
                    "ContractPeriodStart",
                    "DateTime",
                    "Dimension",
                    "Mandatory",
                    False,
                    "Contract Period Start",
                ),
                (
                    "ContractPeriodEnd",
                    "DateTime",
                    "Dimension",
                    "Mandatory",
                    False,
                    "Contract Period End",
                ),
                (
                    "ContractCommitmentPeriodStart",
                    "DateTime",
                    "Dimension",
                    "Mandatory",
                    False,
                    "Contract Commitment Period Start",
                ),
                (
                    "ContractCommitmentPeriodEnd",
                    "DateTime",
                    "Dimension",
                    "Mandatory",
                    False,
                    "Contract Commitment Period End",
                ),
                (
                    "ContractCommitmentDescription",
                    "String",
                    "Dimension",
                    "Mandatory",
                    True,
                    "Contract Commitment Description",
                ),
                (
                    "ContractCommitmentType",
                    "String",
                    "Dimension",
                    "Mandatory",
                    False,
                    "Contract Commitment Type",
                ),
                (
                    "ContractCommitmentCategory",
                    "String",
                    "Dimension",
                    "Mandatory",
                    False,
                    "Contract Commitment Category",
                ),
                (
                    "ContractCommitmentUnit",
                    "String",
                    "Dimension",
                    "Mandatory",
                    True,
                    "Contract Commitment Unit",
                ),
                (
                    "ContractCommitmentQuantity",
                    "Decimal",
                    "Metric",
                    "Mandatory",
                    True,
                    "Contract Commitment Quantity",
                ),
                (
                    "ContractCommitmentCost",
                    "Decimal",
                    "Metric",
                    "Mandatory",
                    True,
                    "Contract Commitment Cost",
                ),
            ]

            for (
                name,
                data_type,
                col_type,
                feature_level,
                allows_nulls,
                description,
            ) in contract_columns:
                snake_name = pascal_to_snake_case(name)
                column = FocusColumn(
                    name=name,
                    snake_case_name=snake_name,
                    column_type=FocusColumnType(col_type),
                    feature_level=FocusFeatureLevel(feature_level),
                    data_type=FocusDataType(data_type),
                    allows_nulls=allows_nulls,
                    description=description,
                    clickhouse_type=self.get_clickhouse_type_mapping(data_type, allows_nulls),
                )
                columns.append(column)

        return columns


class FocusSchemaLoader(ISchemaLoader):
    """Loads complete FOCUS dataset schemas"""

    def __init__(self, spec_root: Optional[str] = None):
        self.column_loader = FocusColumnMetadataLoader(spec_root)

    def load_dataset_schema(self, dataset_name: str) -> FocusDataset:
        """Load complete schema for a FOCUS dataset"""
        columns = self.column_loader.load_column_metadata(dataset_name)

        # Determine table and view names
        if dataset_name == "cost_and_usage":
            table_name = FocusTableNames.COST_USAGE
            view_name = FocusViewNames.COST_USAGE
            description = "FOCUS Cost & Usage dataset containing billing and usage information"
        elif dataset_name == "contract_commitment":
            table_name = FocusTableNames.CONTRACT_COMMITMENT
            view_name = FocusViewNames.CONTRACT_COMMITMENT
            description = "FOCUS Contract Commitment dataset containing commitment information"
        else:
            table_name = f"focus_{dataset_name}"
            view_name = f"focus_{dataset_name}_view"
            description = f"FOCUS {dataset_name} dataset"

        return FocusDataset(
            name=dataset_name,
            description=description,
            columns=columns,
            table_name=table_name,
            view_name=view_name,
        )

    def get_available_datasets(self) -> List[str]:
        """Get list of available FOCUS datasets"""
        return ["cost_and_usage", "contract_commitment"]

    def load_columns_specification(self) -> List[FocusColumn]:
        """Load all FOCUS column specifications from YAML"""
        return self.column_loader.load_column_metadata("all")

    def validate_schema_compatibility(
        self, dataset_name: str, parquet_schema: Dict[str, Any]
    ) -> bool:
        """Validate that a Parquet file schema is compatible with FOCUS specification"""
        focus_schema = self.load_dataset_schema(dataset_name)

        # Get required columns
        required_columns = [
            col.name
            for col in focus_schema.columns
            if col.feature_level == FocusFeatureLevel.MANDATORY
        ]

        # Check if all required columns are present in Parquet schema
        parquet_columns = set(parquet_schema.keys())
        missing_columns = set(required_columns) - parquet_columns

        return len(missing_columns) == 0
