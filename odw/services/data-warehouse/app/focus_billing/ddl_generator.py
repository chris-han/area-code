"""
FOCUS DDL Generator Implementation

Concrete implementation of DDL generation for FOCUS datasets using ClickHouse.
Parses FOCUS specifications and generates appropriate CREATE TABLE statements.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from .interfaces.ddl_generator import IDDLGenerator
from .models import FocusDataset, FocusColumn
from .schema.loader import FocusSchemaLoader
from .utils.naming import to_snake_case
from .utils.type_mapping import map_focus_to_clickhouse_type
from .config import get_focus_config


class FocusClickHouseDDLGenerator(IDDLGenerator):
    """Generates ClickHouse DDL statements from FOCUS specifications"""

    def __init__(self):
        self.schema_loader = FocusSchemaLoader()
        self.focus_spec_root = Path(get_focus_config().focus_spec_root)

    def generate_table_ddl(self, dataset: FocusDataset) -> str:
        """
        Generate CREATE TABLE DDL for a FOCUS dataset
        
        Args:
            dataset: FocusDataset with schema information
            
        Returns:
            CREATE TABLE DDL string
        """
        # Build column definitions
        column_defs = []
        
        # Add core columns first
        core_columns = self._get_core_columns(dataset.name)
        for col in core_columns:
            col_def = self._format_column_definition(col)
            column_defs.append(col_def)
        
        # Add FOCUS specification columns
        for col in dataset.columns:
            col_def = self._format_column_definition(col)
            column_defs.append(col_def)
        
        # Add audit columns
        audit_columns = self._get_audit_columns()
        for col in audit_columns:
            col_def = self._format_column_definition(col)
            column_defs.append(col_def)
        
        columns_sql = ",\n    ".join(column_defs)
        
        # Build table definition
        ddl = f"CREATE TABLE {dataset.table_name} (\n    {columns_sql}\n)"
        
        # Add engine and configuration
        ddl += "\nENGINE = MergeTree()"
        
        # Add partitioning based on dataset type
        if dataset.name == "cost_and_usage":
            ddl += "\nPARTITION BY toYYYYMM(usage_date)"
            ddl += "\nORDER BY (usage_date, billing_account_id, service_category, service_name)"
        elif dataset.name == "contract_commitment":
            ddl += "\nORDER BY (contract_commitment_id, billing_account_id)"
        else:
            ddl += "\nORDER BY (id)"
        
        # Add settings
        ddl += "\nSETTINGS index_granularity = 8192, allow_nullable_key = 1"
        
        # Add table comment
        escaped_description = dataset.description.replace("'", "\\'")
        ddl += f"\nCOMMENT '{escaped_description}'"
        
        return ddl

    def generate_view_ddl(self, dataset: FocusDataset) -> str:
        """
        Generate CREATE VIEW DDL for PascalCase column projection
        
        Args:
            dataset: FocusDataset with schema information
            
        Returns:
            CREATE VIEW DDL string
        """
        # Build column mappings from snake_case to PascalCase
        column_mappings = []
        
        # Add core columns
        if dataset.name == "cost_and_usage":
            column_mappings.extend([
                "id AS Id",
                "usage_date AS UsageDate"
            ])
        else:
            column_mappings.append("id AS Id")
        
        # Add FOCUS columns
        for col in dataset.columns:
            snake_name = col.snake_case_name
            pascal_name = col.name
            column_mappings.append(f"{snake_name} AS {pascal_name}")
        
        # Add audit columns
        column_mappings.extend([
            "source_system AS SourceSystem",
            "created_at AS CreatedAt", 
            "updated_at AS UpdatedAt"
        ])
        
        columns_sql = ",\n    ".join(column_mappings)
        
        return f"""CREATE VIEW {dataset.view_name} AS
SELECT
    {columns_sql}
FROM {dataset.table_name}"""

    def generate_indexes_ddl(self, dataset: FocusDataset) -> List[str]:
        """
        Generate index creation DDL statements
        
        Args:
            dataset: FocusDataset with schema information
            
        Returns:
            List of CREATE INDEX DDL strings
        """
        indexes = []
        
        if dataset.name == "cost_and_usage":
            # Min/max indexes for common query patterns
            indexes.extend([
                f"ALTER TABLE {dataset.table_name} ADD INDEX idx_billing_account_minmax billing_account_id TYPE minmax GRANULARITY 1",
                f"ALTER TABLE {dataset.table_name} ADD INDEX idx_usage_date_minmax usage_date TYPE minmax GRANULARITY 1",
                f"ALTER TABLE {dataset.table_name} ADD INDEX idx_service_category_set service_category TYPE set(100) GRANULARITY 1",
                f"ALTER TABLE {dataset.table_name} ADD INDEX idx_provider_name_set provider_name TYPE set(50) GRANULARITY 1",
                f"ALTER TABLE {dataset.table_name} ADD INDEX idx_region_id_set region_id TYPE set(200) GRANULARITY 1"
            ])
        elif dataset.name == "contract_commitment":
            indexes.extend([
                f"ALTER TABLE {dataset.table_name} ADD INDEX idx_contract_commitment_id_minmax contract_commitment_id TYPE minmax GRANULARITY 1",
                f"ALTER TABLE {dataset.table_name} ADD INDEX idx_billing_account_minmax billing_account_id TYPE minmax GRANULARITY 1"
            ])
        
        return indexes

    def generate_drop_ddl(self, dataset: FocusDataset) -> List[str]:
        """
        Generate DROP statements for cleanup
        
        Args:
            dataset: FocusDataset with schema information
            
        Returns:
            List of DROP DDL strings
        """
        return [
            f"DROP VIEW IF EXISTS {dataset.view_name}",
            f"DROP TABLE IF EXISTS {dataset.table_name}"
        ]

    def validate_ddl_syntax(self, ddl: str) -> bool:
        """
        Validate DDL syntax (basic validation)
        
        Args:
            ddl: DDL string to validate
            
        Returns:
            True if syntax appears valid, False otherwise
        """
        # Basic syntax validation
        ddl_upper = ddl.upper().strip()
        
        # Check for required keywords
        if ddl_upper.startswith("CREATE TABLE"):
            required_patterns = [
                r"CREATE\s+TABLE\s+\w+",
                r"ENGINE\s*=\s*\w+",
                r"ORDER\s+BY\s*\("
            ]
        elif ddl_upper.startswith("CREATE VIEW"):
            required_patterns = [
                r"CREATE\s+VIEW\s+\w+\s+AS",
                r"SELECT\s+",
                r"FROM\s+\w+"
            ]
        else:
            return False
        
        for pattern in required_patterns:
            if not re.search(pattern, ddl_upper):
                return False
        
        # Check for balanced parentheses
        open_count = ddl.count('(')
        close_count = ddl.count(')')
        if open_count != close_count:
            return False
        
        return True

    def execute_ddl(self, ddl: str) -> bool:
        """
        Execute DDL against ClickHouse (placeholder - actual execution in separate module)
        
        Args:
            ddl: DDL string to execute
            
        Returns:
            True if execution would be successful, False otherwise
        """
        # This is a placeholder - actual execution will be handled by the DDL executor
        # For now, just validate syntax
        return self.validate_ddl_syntax(ddl)

    def generate_manifest_table_ddl(self) -> str:
        """
        Generate DDL for the FOCUS ingestion manifest table
        
        Returns:
            CREATE TABLE DDL string for manifest table
        """
        columns = [
            "id String COMMENT 'Unique manifest entry ID'",
            "file_path String COMMENT 'Relative path to processed file'", 
            "file_checksum String COMMENT 'File checksum for change detection'",
            "dataset_type String COMMENT 'Dataset type (cost_usage or contract_commitment)'",
            "rows_processed UInt64 COMMENT 'Number of rows processed'",
            "processing_status String COMMENT 'Processing status (success, failed, skipped)'",
            "error_message Nullable(String) COMMENT 'Error message if processing failed'",
            "processed_at DateTime64(3) COMMENT 'Processing timestamp'",
            "manifest_metadata Nullable(String) COMMENT 'Additional metadata from manifest.json as JSON string'"
        ]
        
        columns_sql = ",\n    ".join(columns)
        
        ddl = f"""CREATE TABLE focus_ingest_manifest (
    {columns_sql}
)
ENGINE = MergeTree()
ORDER BY (processed_at, dataset_type)
SETTINGS index_granularity = 8192
COMMENT 'Manifest table for tracking processed FOCUS Parquet files'"""
        
        return ddl

    def _get_core_columns(self, dataset_name: str) -> List[FocusColumn]:
        """Get core columns for a dataset"""
        from .models import FocusColumnType, FocusFeatureLevel, FocusDataType
        
        core_columns = [
            FocusColumn(
                name="Id",
                snake_case_name="id",
                column_type=FocusColumnType.DIMENSION,
                feature_level=FocusFeatureLevel.MANDATORY,
                data_type=FocusDataType.STRING,
                allows_nulls=False,
                description="Deterministic hash ID for the row",
                clickhouse_type="String"
            )
        ]
        
        if dataset_name == "cost_and_usage":
            core_columns.append(
                FocusColumn(
                    name="UsageDate",
                    snake_case_name="usage_date",
                    column_type=FocusColumnType.DIMENSION,
                    feature_level=FocusFeatureLevel.MANDATORY,
                    data_type=FocusDataType.DATE,
                    allows_nulls=False,
                    description="Date when the usage occurred (derived from ChargePeriodStart)",
                    clickhouse_type="Date"
                )
            )
        
        return core_columns

    def _get_audit_columns(self) -> List[FocusColumn]:
        """Get audit columns for all datasets"""
        from .models import FocusColumnType, FocusFeatureLevel, FocusDataType
        
        return [
            FocusColumn(
                name="SourceSystem",
                snake_case_name="source_system",
                column_type=FocusColumnType.DIMENSION,
                feature_level=FocusFeatureLevel.MANDATORY,
                data_type=FocusDataType.STRING,
                allows_nulls=False,
                description="Source system identifier",
                clickhouse_type="String"
            ),
            FocusColumn(
                name="CreatedAt",
                snake_case_name="created_at",
                column_type=FocusColumnType.DIMENSION,
                feature_level=FocusFeatureLevel.MANDATORY,
                data_type=FocusDataType.DATETIME,
                allows_nulls=False,
                description="Record creation timestamp",
                clickhouse_type="DateTime64(3)"
            ),
            FocusColumn(
                name="UpdatedAt",
                snake_case_name="updated_at",
                column_type=FocusColumnType.DIMENSION,
                feature_level=FocusFeatureLevel.MANDATORY,
                data_type=FocusDataType.DATETIME,
                allows_nulls=False,
                description="Record update timestamp",
                clickhouse_type="DateTime64(3)"
            )
        ]

    def _format_column_definition(self, col: FocusColumn) -> str:
        """Format a column definition for DDL"""
        col_def = f"{col.snake_case_name} {col.clickhouse_type}"
        
        if col.description:
            # Escape single quotes in comments
            escaped_comment = col.description.replace("'", "\\'")
            col_def += f" COMMENT '{escaped_comment}'"
        
        return col_def

    def parse_focus_dataset_specification(self, dataset_name: str) -> List[FocusColumn]:
        """
        Parse FOCUS dataset specification from markdown files
        
        Args:
            dataset_name: Name of the dataset (cost_and_usage or contract_commitment)
            
        Returns:
            List of FocusColumn objects parsed from specification
        """
        dataset_path = self.focus_spec_root / "specification" / "datasets" / dataset_name
        dataset_md_path = dataset_path / "dataset.md"
        
        if not dataset_md_path.exists():
            # Fall back to schema loader
            return self.schema_loader.load_dataset_schema(dataset_name).columns
        
        columns = []
        
        try:
            with open(dataset_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse markdown table for column definitions
            # Look for table with columns: Column | Column Type | Feature Level | Allows Nulls | Data Type
            table_pattern = r'\|.*Column.*\|.*Column Type.*\|.*Feature Level.*\|.*Allows Nulls.*\|.*Data Type.*\|'
            table_match = re.search(table_pattern, content, re.IGNORECASE)
            
            if table_match:
                # Find the table section
                table_start = table_match.start()
                lines = content[table_start:].split('\n')
                
                # Skip header and separator lines
                data_lines = [line for line in lines[2:] if line.strip().startswith('|') and '---' not in line]
                
                for line in data_lines:
                    if not line.strip():
                        continue
                    
                    # Parse table row
                    parts = [part.strip() for part in line.split('|')[1:-1]]  # Remove empty first/last
                    
                    if len(parts) >= 5:
                        # Extract column information
                        column_name_part = parts[0]
                        column_type = parts[1].strip()
                        feature_level = parts[2].strip()
                        allows_nulls = parts[3].strip().lower() == 'true'
                        data_type = parts[4].strip()
                        
                        # Extract column name from markdown link
                        name_match = re.search(r'\[([^\]]+)\]', column_name_part)
                        if name_match:
                            column_name = name_match.group(1)
                        else:
                            column_name = column_name_part.strip()
                        
                        # Map data types
                        if data_type == "Date/Time":
                            data_type = "DateTime"
                        elif data_type == "Numeric":
                            data_type = "Decimal"
                        
                        # Create FocusColumn
                        from .models import FocusColumnType, FocusFeatureLevel, FocusDataType
                        
                        try:
                            col = FocusColumn(
                                name=column_name,
                                snake_case_name=to_snake_case(column_name),
                                column_type=FocusColumnType(column_type),
                                feature_level=FocusFeatureLevel(feature_level),
                                data_type=FocusDataType(data_type),
                                allows_nulls=allows_nulls,
                                description=f"{column_name} from FOCUS specification",
                                clickhouse_type=map_focus_to_clickhouse_type(data_type, allows_nulls)
                            )
                            columns.append(col)
                        except ValueError as e:
                            # Skip invalid columns
                            print(f"Warning: Skipping column {column_name}: {e}")
                            continue
        
        except Exception as e:
            print(f"Error parsing dataset specification for {dataset_name}: {e}")
            # Fall back to schema loader
            return self.schema_loader.load_dataset_schema(dataset_name).columns
        
        return columns if columns else self.schema_loader.load_dataset_schema(dataset_name).columns


def generate_all_focus_ddl() -> Dict[str, str]:
    """
    Generate all DDL statements for FOCUS tables and views
    
    Returns:
        Dict[str, str]: Dictionary mapping object names to DDL statements
    """
    generator = FocusClickHouseDDLGenerator()
    schema_loader = FocusSchemaLoader()
    
    ddl_statements = {}
    
    # Generate DDL for each dataset
    for dataset_name in schema_loader.get_available_datasets():
        dataset = schema_loader.load_dataset_schema(dataset_name)
        
        # Generate table DDL
        table_ddl = generator.generate_table_ddl(dataset)
        ddl_statements[dataset.table_name] = table_ddl
        
        # Generate view DDL
        view_ddl = generator.generate_view_ddl(dataset)
        ddl_statements[dataset.view_name] = view_ddl
        
        # Generate index DDL
        index_ddls = generator.generate_indexes_ddl(dataset)
        for i, index_ddl in enumerate(index_ddls):
            ddl_statements[f"{dataset.table_name}_index_{i+1}"] = index_ddl
    
    # Generate manifest table DDL
    manifest_ddl = generator.generate_manifest_table_ddl()
    ddl_statements["focus_ingest_manifest"] = manifest_ddl
    
    return ddl_statements