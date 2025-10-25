"""
FOCUS DDL Executor

Handles execution of DDL statements against ClickHouse using Moose MCP tools.
Provides verification and error handling for DDL operations.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from .ddl_generator import FocusClickHouseDDLGenerator, generate_all_focus_ddl
from .schema.loader import FocusSchemaLoader
from .config import get_focus_config


logger = logging.getLogger(__name__)


class FocusDDLExecutor:
    """Executes FOCUS DDL statements against ClickHouse"""

    def __init__(self):
        self.ddl_generator = FocusClickHouseDDLGenerator()
        self.schema_loader = FocusSchemaLoader()

    def execute_ddl_statement(self, ddl: str, description: str = "") -> Tuple[bool, str]:
        """
        Execute a single DDL statement against ClickHouse
        
        Args:
            ddl: DDL statement to execute
            description: Description of the operation for logging
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate DDL syntax first
            if not self.ddl_generator.validate_ddl_syntax(ddl):
                return False, f"Invalid DDL syntax: {ddl[:100]}..."
            
            logger.info(f"Executing DDL: {description}")
            logger.debug(f"DDL Statement: {ddl}")
            
            # Execute using Moose MCP tools
            from kiro import mcp_moose_dev_query_olap
            
            result = mcp_moose_dev_query_olap(query=ddl, limit=1)
            
            logger.info(f"Successfully executed DDL: {description}")
            return True, f"Successfully executed: {description}"
            
        except Exception as e:
            error_msg = f"Failed to execute DDL {description}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def verify_table_exists(self, table_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verify that a table exists and get its schema
        
        Args:
            table_name: Name of the table to verify
            
        Returns:
            Tuple of (exists: bool, schema: Optional[Dict])
        """
        try:
            describe_sql = f"DESCRIBE TABLE {table_name}"
            logger.debug(f"Verifying table exists: {table_name}")
            
            # Execute using Moose MCP tools
            from kiro import mcp_moose_dev_query_olap
            
            result = mcp_moose_dev_query_olap(query=describe_sql, limit=100)
            
            # If we get here without exception, table exists
            columns = []
            if hasattr(result, 'rows') and result.rows:
                columns = result.rows
            elif isinstance(result, list):
                columns = result
            
            return True, {"columns": columns, "engine": "MergeTree"}
            
        except Exception as e:
            logger.warning(f"Table {table_name} does not exist or is not accessible: {e}")
            return False, None

    def verify_view_exists(self, view_name: str) -> Tuple[bool, Optional[str]]:
        """
        Verify that a view exists and get its definition
        
        Args:
            view_name: Name of the view to verify
            
        Returns:
            Tuple of (exists: bool, definition: Optional[str])
        """
        try:
            show_sql = f"SHOW CREATE VIEW {view_name}"
            logger.debug(f"Verifying view exists: {view_name}")
            
            # Execute using Moose MCP tools
            from kiro import mcp_moose_dev_query_olap
            
            result = mcp_moose_dev_query_olap(query=show_sql, limit=1)
            
            # Extract view definition from result
            definition = None
            if hasattr(result, 'rows') and result.rows:
                definition = result.rows[0].get('statement', '')
            elif isinstance(result, list) and result:
                definition = result[0].get('statement', '')
            
            return True, definition
            
        except Exception as e:
            logger.warning(f"View {view_name} does not exist or is not accessible: {e}")
            return False, None

    def create_focus_tables(self, force_recreate: bool = False) -> Dict[str, Tuple[bool, str]]:
        """
        Create all FOCUS tables and views
        
        Args:
            force_recreate: If True, drop existing objects before creating
            
        Returns:
            Dict mapping object names to (success, message) tuples
        """
        results = {}
        
        # Generate all DDL statements
        ddl_statements = generate_all_focus_ddl()
        
        # Get datasets for proper ordering
        datasets = [self.schema_loader.load_dataset_schema(name) 
                   for name in self.schema_loader.get_available_datasets()]
        
        # If force recreate, drop objects first (in reverse order)
        if force_recreate:
            logger.info("Force recreate requested - dropping existing objects")
            
            # Drop views first
            for dataset in datasets:
                if dataset.view_name in ddl_statements:
                    drop_view_sql = f"DROP VIEW IF EXISTS {dataset.view_name}"
                    success, msg = self.execute_ddl_statement(drop_view_sql, f"Drop view {dataset.view_name}")
                    results[f"drop_{dataset.view_name}"] = (success, msg)
            
            # Drop tables
            for dataset in datasets:
                if dataset.table_name in ddl_statements:
                    drop_table_sql = f"DROP TABLE IF EXISTS {dataset.table_name}"
                    success, msg = self.execute_ddl_statement(drop_table_sql, f"Drop table {dataset.table_name}")
                    results[f"drop_{dataset.table_name}"] = (success, msg)
            
            # Drop manifest table
            drop_manifest_sql = "DROP TABLE IF EXISTS focus_ingest_manifest"
            success, msg = self.execute_ddl_statement(drop_manifest_sql, "Drop manifest table")
            results["drop_focus_ingest_manifest"] = (success, msg)
        
        # Create tables first
        table_order = ["focus_cost_usage", "focus_contract_commitment", "focus_ingest_manifest"]
        
        for table_name in table_order:
            if table_name in ddl_statements:
                ddl = ddl_statements[table_name]
                success, msg = self.execute_ddl_statement(ddl, f"Create table {table_name}")
                results[table_name] = (success, msg)
                
                if not success:
                    logger.error(f"Failed to create table {table_name}, stopping creation process")
                    return results
        
        # Create views
        view_order = ["focus_data_table", "focus_contract_commitment_view"]
        
        for view_name in view_order:
            if view_name in ddl_statements:
                ddl = ddl_statements[view_name]
                success, msg = self.execute_ddl_statement(ddl, f"Create view {view_name}")
                results[view_name] = (success, msg)
        
        # Create indexes
        for dataset in datasets:
            index_ddls = self.ddl_generator.generate_indexes_ddl(dataset)
            for i, index_ddl in enumerate(index_ddls):
                index_name = f"{dataset.table_name}_index_{i+1}"
                success, msg = self.execute_ddl_statement(index_ddl, f"Create index {index_name}")
                results[index_name] = (success, msg)
        
        return results

    def verify_focus_schema(self) -> Dict[str, bool]:
        """
        Verify that all FOCUS tables and views exist
        
        Returns:
            Dict mapping object names to existence status
        """
        verification_results = {}
        
        # Check tables
        tables_to_check = ["focus_cost_usage", "focus_contract_commitment", "focus_ingest_manifest"]
        
        for table_name in tables_to_check:
            exists, _ = self.verify_table_exists(table_name)
            verification_results[table_name] = exists
        
        # Check views
        views_to_check = ["focus_data_table", "focus_contract_commitment_view"]
        
        for view_name in views_to_check:
            exists, _ = self.verify_view_exists(view_name)
            verification_results[view_name] = exists
        
        return verification_results

    def get_table_schema_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed schema information for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with schema information or None if table doesn't exist
        """
        exists, schema = self.verify_table_exists(table_name)
        
        if not exists:
            return None
        
        try:
            # Get additional table information
            info_sql = f"""
            SELECT 
                engine,
                partition_key,
                sorting_key,
                primary_key,
                total_rows,
                total_bytes
            FROM system.tables 
            WHERE name = '{table_name}' AND database = currentDatabase()
            """
            
            # TODO: Execute using Moose MCP tools
            # result = moose_mcp_query_olap(info_sql)
            
            # Placeholder return
            return {
                "exists": True,
                "engine": "MergeTree",
                "partition_key": "toYYYYMM(usage_date)" if "cost_usage" in table_name else "",
                "sorting_key": "usage_date, billing_account_id",
                "primary_key": "",
                "total_rows": 0,
                "total_bytes": 0,
                "columns": schema.get("columns", []) if schema else []
            }
            
        except Exception as e:
            logger.error(f"Error getting schema info for {table_name}: {e}")
            return {"exists": True, "error": str(e)}

    def save_ddl_to_file(self, output_path: Optional[str] = None) -> str:
        """
        Save all generated DDL statements to a file for reapplication
        
        Args:
            output_path: Optional path to save DDL file
            
        Returns:
            Path to the saved DDL file
        """
        if output_path is None:
            output_path = Path(__file__).parent / "generated_ddl.sql"
        else:
            output_path = Path(output_path)
        
        # Generate all DDL statements
        ddl_statements = generate_all_focus_ddl()
        
        # Create SQL file content
        sql_content = []
        sql_content.append("-- FOCUS Billing Integration DDL Statements")
        sql_content.append("-- Generated automatically from FOCUS specifications")
        sql_content.append("-- This file can be used to recreate FOCUS tables and views")
        sql_content.append("")
        
        # Add drop statements first
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
        
        # Add index statements
        datasets = [self.schema_loader.load_dataset_schema(name) 
                   for name in self.schema_loader.get_available_datasets()]
        
        sql_content.append("-- Indexes")
        for dataset in datasets:
            index_ddls = self.ddl_generator.generate_indexes_ddl(dataset)
            for index_ddl in index_ddls:
                sql_content.append(index_ddl + ";")
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_content))
        
        logger.info(f"DDL statements saved to: {output_path}")
        return str(output_path)


def create_focus_schema(force_recreate: bool = False) -> Dict[str, Tuple[bool, str]]:
    """
    Convenience function to create FOCUS schema
    
    Args:
        force_recreate: If True, drop existing objects before creating
        
    Returns:
        Dict mapping object names to (success, message) tuples
    """
    executor = FocusDDLExecutor()
    return executor.create_focus_tables(force_recreate=force_recreate)


def verify_focus_schema() -> Dict[str, bool]:
    """
    Convenience function to verify FOCUS schema exists
    
    Returns:
        Dict mapping object names to existence status
    """
    executor = FocusDDLExecutor()
    return executor.verify_focus_schema()