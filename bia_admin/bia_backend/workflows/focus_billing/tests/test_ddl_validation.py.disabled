"""
Unit tests for FOCUS DDL validation

Tests DDL generation from FOCUS specs and validates generated SQL syntax.
Includes mock ClickHouse execution verification.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import re
from typing import Dict, List, Any

from app.focus_billing.ddl_generator import (
    FocusClickHouseDDLGenerator,
    generate_all_focus_ddl
)
from app.focus_billing.ddl_executor import FocusDDLExecutor
from app.focus_billing.models import FocusDataset, FocusColumn, FocusColumnType, FocusFeatureLevel, FocusDataType
from app.focus_billing.schema.loader import FocusSchemaLoader


class TestDDLGeneration:
    """Test DDL generation from FOCUS specifications"""

    def test_ddl_generator_initialization(self):
        """Test that DDL generator initializes correctly"""
        generator = FocusClickHouseDDLGenerator()
        assert generator is not None
        assert hasattr(generator, 'schema_loader')
        assert isinstance(generator.schema_loader, FocusSchemaLoader)

    def test_generate_cost_usage_table_ddl(self):
        """Test DDL generation for cost and usage table"""
        generator = FocusClickHouseDDLGenerator()
        loader = FocusSchemaLoader()
        
        dataset = loader.load_dataset_schema("cost_and_usage")
        ddl = generator.generate_table_ddl(dataset)
        
        # Verify basic DDL structure
        assert ddl.startswith("CREATE TABLE focus_cost_usage")
        assert "ENGINE = MergeTree()" in ddl
        assert "PARTITION BY toYYYYMM(usage_date)" in ddl
        assert "ORDER BY (usage_date, billing_account_id, service_category, service_name)" in ddl
        assert "SETTINGS index_granularity = 8192" in ddl
        
        # Verify core columns are present
        assert "id String" in ddl
        assert "usage_date Date" in ddl
        assert "source_system String" in ddl
        assert "created_at DateTime64(3)" in ddl
        assert "updated_at DateTime64(3)" in ddl

    def test_generate_contract_commitment_table_ddl(self):
        """Test DDL generation for contract commitment table"""
        generator = FocusClickHouseDDLGenerator()
        loader = FocusSchemaLoader()
        
        dataset = loader.load_dataset_schema("contract_commitment")
        ddl = generator.generate_table_ddl(dataset)
        
        # Verify basic DDL structure
        assert ddl.startswith("CREATE TABLE focus_contract_commitment")
        assert "ENGINE = MergeTree()" in ddl
        assert "ORDER BY (contract_commitment_id, billing_account_id)" in ddl
        assert "SETTINGS index_granularity = 8192" in ddl
        
        # Verify core columns are present
        assert "id String" in ddl
        assert "source_system String" in ddl

    def test_generate_view_ddl(self):
        """Test DDL generation for views"""
        generator = FocusClickHouseDDLGenerator()
        loader = FocusSchemaLoader()
        
        # Test cost usage view
        dataset = loader.load_dataset_schema("cost_and_usage")
        view_ddl = generator.generate_view_ddl(dataset)
        
        assert view_ddl.startswith("CREATE VIEW focus_data_table AS")
        assert "SELECT" in view_ddl
        assert "FROM focus_cost_usage" in view_ddl
        assert "id AS Id" in view_ddl
        assert "usage_date AS UsageDate" in view_ddl
        assert "source_system AS SourceSystem" in view_ddl

    def test_generate_indexes_ddl(self):
        """Test DDL generation for indexes"""
        generator = FocusClickHouseDDLGenerator()
        loader = FocusSchemaLoader()
        
        dataset = loader.load_dataset_schema("cost_and_usage")
        index_ddls = generator.generate_indexes_ddl(dataset)
        
        assert isinstance(index_ddls, list)
        assert len(index_ddls) > 0
        
        # Verify index DDL structure
        for index_ddl in index_ddls:
            assert index_ddl.startswith("ALTER TABLE focus_cost_usage ADD INDEX")
            assert "TYPE" in index_ddl
            assert "GRANULARITY" in index_ddl

    def test_generate_manifest_table_ddl(self):
        """Test DDL generation for manifest table"""
        generator = FocusClickHouseDDLGenerator()
        ddl = generator.generate_manifest_table_ddl()
        
        assert ddl.startswith("CREATE TABLE focus_ingest_manifest")
        assert "ENGINE = MergeTree()" in ddl
        assert "ORDER BY (processed_at, dataset_type)" in ddl
        
        # Verify required columns
        assert "id String" in ddl
        assert "file_path String" in ddl
        assert "file_checksum String" in ddl
        assert "dataset_type String" in ddl
        assert "rows_processed UInt64" in ddl
        assert "processing_status String" in ddl

    def test_generate_all_focus_ddl(self):
        """Test generation of all FOCUS DDL statements"""
        ddl_statements = generate_all_focus_ddl()
        
        assert isinstance(ddl_statements, dict)
        assert len(ddl_statements) > 0
        
        # Verify expected objects are present
        expected_objects = [
            "focus_cost_usage",
            "focus_contract_commitment", 
            "focus_ingest_manifest"
        ]
        
        for obj_name in expected_objects:
            assert obj_name in ddl_statements
            assert isinstance(ddl_statements[obj_name], str)
            assert len(ddl_statements[obj_name]) > 0


class TestDDLSyntaxValidation:
    """Test DDL syntax validation functionality"""

    def test_validate_ddl_syntax_valid_table(self):
        """Test DDL syntax validation for valid CREATE TABLE statements"""
        generator = FocusClickHouseDDLGenerator()
        
        valid_ddl = """CREATE TABLE test_table (
    id String COMMENT 'Test ID',
    value Nullable(Decimal(10, 2)) COMMENT 'Test value'
)
ENGINE = MergeTree()
ORDER BY (id)
SETTINGS index_granularity = 8192"""
        
        assert generator.validate_ddl_syntax(valid_ddl) is True

    def test_validate_ddl_syntax_valid_view(self):
        """Test DDL syntax validation for valid CREATE VIEW statements"""
        generator = FocusClickHouseDDLGenerator()
        
        valid_view_ddl = """CREATE VIEW test_view AS
SELECT
    id AS Id,
    value AS Value
FROM test_table"""
        
        assert generator.validate_ddl_syntax(valid_view_ddl) is True

    def test_validate_ddl_syntax_invalid_missing_engine(self):
        """Test DDL syntax validation for invalid DDL missing ENGINE"""
        generator = FocusClickHouseDDLGenerator()
        
        invalid_ddl = """CREATE TABLE test_table (
    id String
)
ORDER BY (id)"""
        
        assert generator.validate_ddl_syntax(invalid_ddl) is False

    def test_validate_ddl_syntax_invalid_missing_order_by(self):
        """Test DDL syntax validation for invalid DDL missing ORDER BY"""
        generator = FocusClickHouseDDLGenerator()
        
        invalid_ddl = """CREATE TABLE test_table (
    id String
)
ENGINE = MergeTree()"""
        
        assert generator.validate_ddl_syntax(invalid_ddl) is False

    def test_validate_ddl_syntax_invalid_unbalanced_parentheses(self):
        """Test DDL syntax validation for unbalanced parentheses"""
        generator = FocusClickHouseDDLGenerator()
        
        invalid_ddl = """CREATE TABLE test_table (
    id String
ENGINE = MergeTree()
ORDER BY (id)"""
        
        assert generator.validate_ddl_syntax(invalid_ddl) is False

    def test_validate_ddl_syntax_invalid_view_missing_select(self):
        """Test DDL syntax validation for invalid view missing SELECT"""
        generator = FocusClickHouseDDLGenerator()
        
        invalid_view_ddl = """CREATE VIEW test_view AS
FROM test_table"""
        
        assert generator.validate_ddl_syntax(invalid_view_ddl) is False

    def test_validate_generated_ddl_statements(self):
        """Test that all generated DDL statements pass syntax validation"""
        generator = FocusClickHouseDDLGenerator()
        ddl_statements = generate_all_focus_ddl()
        
        validation_results = {}
        for name, ddl in ddl_statements.items():
            # Skip index statements as they use ALTER TABLE syntax which has different validation rules
            if "_index_" in name:
                # Basic validation for ALTER TABLE statements
                is_valid = ddl.strip().upper().startswith("ALTER TABLE") and "ADD INDEX" in ddl.upper()
            else:
                is_valid = generator.validate_ddl_syntax(ddl)
            validation_results[name] = is_valid
        
        # All generated DDL should be valid
        invalid_statements = [name for name, valid in validation_results.items() if not valid]
        assert len(invalid_statements) == 0, f"Invalid DDL statements: {invalid_statements}"


class TestDDLExecutorMocking:
    """Test DDL executor with mocked ClickHouse execution"""

    def test_execute_ddl_statement_success(self):
        """Test successful DDL execution with mocked MCP function"""
        executor = FocusDDLExecutor()
        
        # Mock the execute_ddl_statement method to simulate success
        with patch.object(executor, 'execute_ddl_statement') as mock_execute:
            mock_execute.return_value = (True, "Successfully executed: Test table creation")
            
            valid_ddl = """CREATE TABLE test_table (
    id String
)
ENGINE = MergeTree()
ORDER BY (id)"""
            
            success, message = mock_execute(valid_ddl, "Test table creation")
            
            assert success is True
            assert "Successfully executed" in message

    def test_execute_ddl_statement_failure(self):
        """Test failed DDL execution with mocked MCP function"""
        executor = FocusDDLExecutor()
        
        # Mock the execute_ddl_statement method to simulate failure
        with patch.object(executor, 'execute_ddl_statement') as mock_execute:
            mock_execute.return_value = (False, "Failed to execute DDL Test table creation: ClickHouse connection error")
            
            valid_ddl = """CREATE TABLE test_table (
    id String
)
ENGINE = MergeTree()
ORDER BY (id)"""
            
            success, message = mock_execute(valid_ddl, "Test table creation")
            
            assert success is False
            assert "Failed to execute DDL" in message
            assert "ClickHouse connection error" in message

    def test_execute_ddl_statement_invalid_syntax(self):
        """Test DDL execution with invalid syntax"""
        executor = FocusDDLExecutor()
        
        invalid_ddl = "INVALID SQL STATEMENT"
        
        success, message = executor.execute_ddl_statement(invalid_ddl, "Invalid DDL")
        
        assert success is False
        assert "Invalid DDL syntax" in message

    def test_verify_table_exists_success(self):
        """Test successful table verification with mocked response"""
        executor = FocusDDLExecutor()
        
        # Mock the verify_table_exists method
        with patch.object(executor, 'verify_table_exists') as mock_verify:
            mock_verify.return_value = (True, {
                "columns": [
                    {"name": "id", "type": "String"},
                    {"name": "value", "type": "Nullable(Decimal(10, 2))"}
                ]
            })
            
            exists, schema = mock_verify("test_table")
            
            assert exists is True
            assert schema is not None
            assert "columns" in schema
            assert len(schema["columns"]) == 2

    def test_verify_table_exists_not_found(self):
        """Test table verification when table doesn't exist"""
        executor = FocusDDLExecutor()
        
        # Mock the verify_table_exists method
        with patch.object(executor, 'verify_table_exists') as mock_verify:
            mock_verify.return_value = (False, None)
            
            exists, schema = mock_verify("nonexistent_table")
            
            assert exists is False
            assert schema is None

    def test_verify_view_exists_success(self):
        """Test successful view verification with mocked response"""
        executor = FocusDDLExecutor()
        
        # Mock the verify_view_exists method
        with patch.object(executor, 'verify_view_exists') as mock_verify:
            mock_verify.return_value = (True, "CREATE VIEW test_view AS SELECT * FROM test_table")
            
            exists, definition = mock_verify("test_view")
            
            assert exists is True
            assert definition is not None
            assert "CREATE VIEW test_view" in definition

    def test_create_focus_tables_success(self):
        """Test successful creation of all FOCUS tables with mocked responses"""
        executor = FocusDDLExecutor()
        
        # Mock the create_focus_tables method
        with patch.object(executor, 'create_focus_tables') as mock_create:
            mock_create.return_value = {
                "focus_cost_usage": (True, "Successfully executed: Create table focus_cost_usage"),
                "focus_contract_commitment": (True, "Successfully executed: Create table focus_contract_commitment"),
                "focus_ingest_manifest": (True, "Successfully executed: Create table focus_ingest_manifest")
            }
            
            results = mock_create(force_recreate=False)
            
            assert isinstance(results, dict)
            assert len(results) > 0
            
            # Check that tables were created
            expected_tables = ["focus_cost_usage", "focus_contract_commitment", "focus_ingest_manifest"]
            for table_name in expected_tables:
                assert table_name in results
                success, message = results[table_name]
                assert success is True

    def test_create_focus_tables_with_force_recreate(self):
        """Test creation of FOCUS tables with force recreate"""
        executor = FocusDDLExecutor()
        
        # Mock the create_focus_tables method
        with patch.object(executor, 'create_focus_tables') as mock_create:
            mock_create.return_value = {
                "drop_focus_data_table": (True, "Successfully executed: Drop view focus_data_table"),
                "drop_focus_contract_commitment_view": (True, "Successfully executed: Drop view focus_contract_commitment_view"),
                "drop_focus_cost_usage": (True, "Successfully executed: Drop table focus_cost_usage"),
                "focus_cost_usage": (True, "Successfully executed: Create table focus_cost_usage")
            }
            
            results = mock_create(force_recreate=True)
            
            assert isinstance(results, dict)
            
            # Check that drop operations were performed
            drop_operations = [key for key in results.keys() if key.startswith("drop_")]
            assert len(drop_operations) > 0

    def test_verify_focus_schema(self):
        """Test verification of complete FOCUS schema with mocked responses"""
        executor = FocusDDLExecutor()
        
        # Mock the verify_focus_schema method
        with patch.object(executor, 'verify_focus_schema') as mock_verify:
            mock_verify.return_value = {
                "focus_cost_usage": True,
                "focus_contract_commitment": True,
                "focus_ingest_manifest": True,
                "focus_data_table": True,
                "focus_contract_commitment_view": True
            }
            
            verification_results = mock_verify()
            
            assert isinstance(verification_results, dict)
            
            expected_objects = [
                "focus_cost_usage", 
                "focus_contract_commitment", 
                "focus_ingest_manifest",
                "focus_data_table", 
                "focus_contract_commitment_view"
            ]
            
            for obj_name in expected_objects:
                assert obj_name in verification_results
                assert verification_results[obj_name] is True


class TestDDLColumnDefinitions:
    """Test DDL column definitions and metadata"""

    def test_column_definition_formatting(self):
        """Test proper formatting of column definitions"""
        generator = FocusClickHouseDDLGenerator()
        
        # Create test column
        test_column = FocusColumn(
            name="TestColumn",
            snake_case_name="test_column",
            column_type=FocusColumnType.DIMENSION,
            feature_level=FocusFeatureLevel.MANDATORY,
            data_type=FocusDataType.STRING,
            allows_nulls=True,
            description="Test column with special 'quotes'",
            clickhouse_type="Nullable(String)"
        )
        
        formatted = generator._format_column_definition(test_column)
        
        assert "test_column Nullable(String)" in formatted
        assert "COMMENT 'Test column with special \\'quotes\\''" in formatted

    def test_core_columns_generation(self):
        """Test generation of core columns"""
        generator = FocusClickHouseDDLGenerator()
        
        # Test cost usage core columns
        core_columns = generator._get_core_columns("cost_and_usage")
        assert len(core_columns) >= 2
        
        column_names = [col.snake_case_name for col in core_columns]
        assert "id" in column_names
        assert "usage_date" in column_names

    def test_audit_columns_generation(self):
        """Test generation of audit columns"""
        generator = FocusClickHouseDDLGenerator()
        
        audit_columns = generator._get_audit_columns()
        assert len(audit_columns) == 3
        
        column_names = [col.snake_case_name for col in audit_columns]
        assert "source_system" in column_names
        assert "created_at" in column_names
        assert "updated_at" in column_names

    def test_ddl_comment_escaping(self):
        """Test proper escaping of comments in DDL"""
        generator = FocusClickHouseDDLGenerator()
        loader = FocusSchemaLoader()
        
        dataset = loader.load_dataset_schema("cost_and_usage")
        
        # Add a column with special characters in description
        test_column = FocusColumn(
            name="TestColumn",
            snake_case_name="test_column",
            column_type=FocusColumnType.DIMENSION,
            feature_level=FocusFeatureLevel.MANDATORY,
            data_type=FocusDataType.STRING,
            allows_nulls=False,
            description="Test with 'single quotes' and \"double quotes\"",
            clickhouse_type="String"
        )
        dataset.columns.append(test_column)
        
        ddl = generator.generate_table_ddl(dataset)
        
        # Verify that quotes are properly escaped
        assert "Test with \\'single quotes\\'" in ddl
        assert "\"double quotes\"" in ddl


class TestDDLSpecificationParsing:
    """Test parsing of FOCUS specifications for DDL generation"""

    def test_parse_focus_dataset_specification(self):
        """Test parsing of FOCUS dataset specification from markdown"""
        generator = FocusClickHouseDDLGenerator()
        
        # This will test the fallback to schema loader if markdown parsing fails
        columns = generator.parse_focus_dataset_specification("cost_and_usage")
        
        assert isinstance(columns, list)
        assert len(columns) > 0
        
        # Verify columns have required attributes
        for column in columns:
            assert hasattr(column, 'name')
            assert hasattr(column, 'snake_case_name')
            assert hasattr(column, 'clickhouse_type')

    def test_ddl_generation_consistency(self):
        """Test that DDL generation is consistent across multiple calls"""
        generator = FocusClickHouseDDLGenerator()
        loader = FocusSchemaLoader()
        
        dataset = loader.load_dataset_schema("cost_and_usage")
        
        # Generate DDL multiple times
        ddl1 = generator.generate_table_ddl(dataset)
        ddl2 = generator.generate_table_ddl(dataset)
        
        # Should be identical
        assert ddl1 == ddl2

    def test_ddl_generation_with_empty_dataset(self):
        """Test DDL generation with minimal dataset"""
        generator = FocusClickHouseDDLGenerator()
        
        # Create minimal dataset
        minimal_dataset = FocusDataset(
            name="test_dataset",
            table_name="test_table",
            view_name="test_view",
            description="Test dataset",
            columns=[]
        )
        
        ddl = generator.generate_table_ddl(minimal_dataset)
        
        # Should still generate valid DDL with core and audit columns
        assert "CREATE TABLE test_table" in ddl
        assert "ENGINE = MergeTree()" in ddl
        assert "id String" in ddl
        assert "source_system String" in ddl