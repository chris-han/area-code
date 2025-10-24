"""
ClickHouse Batch Insertion for FOCUS Data

Handles chunked insertion of transformed FOCUS data into ClickHouse tables
with error handling, manifest logging, and batch processing.
"""

import pandas as pd
import clickhouse_connect
from typing import Dict, Any, List, Optional, Tuple, Iterator
from datetime import datetime, timezone
from dataclasses import dataclass
import time
import traceback

from .config import focus_config
from .data_transformer import TransformationResult
from .file_discovery import ParquetFileInfo
from .observability import focus_observability, TimedOperation


@dataclass
class InsertionResult:
    """Result of ClickHouse insertion operation"""
    success: bool
    rows_inserted: int
    batches_processed: int
    insertion_time_seconds: float
    error_message: Optional[str] = None
    manifest_id: Optional[str] = None


class ClickHouseInserter:
    """
    Handles batch insertion of FOCUS data into ClickHouse tables.
    
    Features:
    - Chunked insertion with configurable batch size
    - Error handling and retry logic
    - Manifest table logging for tracking
    - Support for both Cost & Usage and Contract Commitment datasets
    """
    
    def __init__(self, batch_size: Optional[int] = None):
        """
        Initialize ClickHouse inserter.
        
        Args:
            batch_size: Override default batch size for insertions
        """
        self.batch_size = batch_size or focus_config.batch_size
        self.client = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to ClickHouse"""
        try:
            with TimedOperation(focus_observability, "focus.clickhouse.connection_time"):
                self.client = clickhouse_connect.get_client(**focus_config.get_clickhouse_connection_params())
                
                # Test connection
                self.client.ping()
                
                # Emit connection success metric
                focus_observability.emit_counter("focus.clickhouse.connections", 1.0, {'status': 'success'})
            
        except Exception as e:
            focus_observability.emit_counter("focus.clickhouse.connections", 1.0, {'status': 'failed'})
            raise ConnectionError(f"Failed to connect to ClickHouse: {e}")
    
    def insert_transformed_data(
        self,
        transformation_result: TransformationResult,
        file_info: ParquetFileInfo,
        manifest_id: str
    ) -> InsertionResult:
        """
        Insert transformed data into appropriate ClickHouse table.
        
        Args:
            transformation_result: Result from data transformation
            file_info: Information about the source file
            manifest_id: Manifest entry ID for tracking
            
        Returns:
            InsertionResult with insertion statistics and status
        """
        start_time = time.time()
        
        try:
            if not transformation_result.success:
                return InsertionResult(
                    success=False,
                    rows_inserted=0,
                    batches_processed=0,
                    insertion_time_seconds=0,
                    error_message=f"Transformation failed: {transformation_result.error_message}",
                    manifest_id=manifest_id
                )
            
            df = transformation_result.transformed_data
            if df is None or df.empty:
                return InsertionResult(
                    success=True,
                    rows_inserted=0,
                    batches_processed=0,
                    insertion_time_seconds=time.time() - start_time,
                    manifest_id=manifest_id
                )
            
            # Determine target table
            table_name = self._get_target_table(file_info.dataset_type)
            
            # Verify table exists using observability
            table_validation = focus_observability.verify_table_exists(table_name)
            if not table_validation.passed:
                focus_observability.emit_counter("focus.insertion.table_missing", 1.0, {'table': table_name})
                return InsertionResult(
                    success=False,
                    rows_inserted=0,
                    batches_processed=0,
                    insertion_time_seconds=time.time() - start_time,
                    error_message=f"Target table {table_name} does not exist",
                    manifest_id=manifest_id
                )
            
            # Prepare data for insertion
            prepared_df = self._prepare_dataframe_for_insertion(df, table_name)
            
            # Insert data in batches with observability
            total_rows = len(prepared_df)
            batches_processed = 0
            rows_inserted = 0
            
            # Emit pre-insertion metrics
            focus_observability.emit_gauge("focus.insertion.batch_size", self.batch_size)
            focus_observability.emit_gauge("focus.insertion.total_rows", total_rows, {'table': table_name})
            
            with TimedOperation(focus_observability, "focus.insertion.batch_processing_time", {'table': table_name}):
                for batch_df in self._create_batches(prepared_df):
                    try:
                        with TimedOperation(focus_observability, "focus.insertion.single_batch_time", {'table': table_name}):
                            batch_rows = self._insert_batch(batch_df, table_name)
                            rows_inserted += batch_rows
                            batches_processed += 1
                            
                            # Emit batch success metric
                            focus_observability.emit_counter("focus.insertion.batches", 1.0, {'status': 'success', 'table': table_name})
                        
                    except Exception as batch_error:
                        # Emit batch failure metric
                        focus_observability.emit_counter("focus.insertion.batches", 1.0, {'status': 'failed', 'table': table_name})
                        print(f"Warning: Batch insertion failed: {batch_error}")
                        # For now, fail the entire operation on any batch failure
                        # In production, you might want to implement partial success handling
                        raise batch_error
            
            insertion_time = time.time() - start_time
            
            # Emit final insertion metrics
            focus_observability.emit_gauge("focus.insertion.rows_inserted", rows_inserted, {'table': table_name})
            focus_observability.emit_gauge("focus.insertion.batches_processed", batches_processed, {'table': table_name})
            focus_observability.emit_timer("focus.insertion.total_time", insertion_time, {'table': table_name})
            
            if insertion_time > 0:
                rows_per_second = rows_inserted / insertion_time
                focus_observability.emit_gauge("focus.insertion.rows_per_second", rows_per_second, {'table': table_name}, "rows/sec")
            
            return InsertionResult(
                success=True,
                rows_inserted=rows_inserted,
                batches_processed=batches_processed,
                insertion_time_seconds=insertion_time,
                manifest_id=manifest_id
            )
            
        except Exception as e:
            insertion_time = time.time() - start_time
            error_msg = f"Insertion failed: {str(e)}\n{traceback.format_exc()}"
            
            # Emit failure metrics
            focus_observability.emit_counter("focus.insertion.failures", 1.0, {'table': table_name, 'error_type': type(e).__name__})
            focus_observability.emit_timer("focus.insertion.failed_time", insertion_time, {'table': table_name})
            
            return InsertionResult(
                success=False,
                rows_inserted=0,
                batches_processed=0,
                insertion_time_seconds=insertion_time,
                error_message=error_msg,
                manifest_id=manifest_id
            )
    
    def _get_target_table(self, dataset_type: str) -> str:
        """Get target table name for dataset type"""
        if dataset_type == 'cost_usage':
            return focus_config.cost_usage_table_name
        elif dataset_type == 'contract_commitment':
            return focus_config.contract_commitment_table_name
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if table exists in ClickHouse"""
        try:
            query = f"""
            SELECT 1 
            FROM system.tables 
            WHERE database = '{focus_config.clickhouse_database}' 
            AND name = '{table_name}'
            """
            result = self.client.query(query)
            return len(result.result_rows) > 0
        except Exception:
            return False
    
    def _prepare_dataframe_for_insertion(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Prepare DataFrame for ClickHouse insertion by ensuring column compatibility.
        
        Args:
            df: DataFrame to prepare
            table_name: Target table name
            
        Returns:
            Prepared DataFrame with compatible columns and types
        """
        # Get table schema from ClickHouse
        table_columns = self._get_table_columns(table_name)
        
        # Prepare DataFrame copy
        prepared_df = df.copy()
        
        # Ensure all table columns exist in DataFrame (add missing as NULL)
        for col_name, col_type in table_columns.items():
            if col_name not in prepared_df.columns:
                prepared_df[col_name] = None
        
        # Remove DataFrame columns that don't exist in table
        df_columns = set(prepared_df.columns)
        table_column_names = set(table_columns.keys())
        extra_columns = df_columns - table_column_names
        
        if extra_columns:
            print(f"Warning: Dropping columns not in table schema: {extra_columns}")
            prepared_df = prepared_df.drop(columns=list(extra_columns))
        
        # Reorder columns to match table schema
        column_order = list(table_columns.keys())
        prepared_df = prepared_df.reindex(columns=column_order)
        
        # Apply final type conversions for ClickHouse compatibility
        prepared_df = self._apply_clickhouse_type_conversions(prepared_df, table_columns)
        
        return prepared_df
    
    def _get_table_columns(self, table_name: str) -> Dict[str, str]:
        """Get table column names and types from ClickHouse"""
        try:
            query = f"""
            SELECT name, type
            FROM system.columns
            WHERE database = '{focus_config.clickhouse_database}'
            AND table = '{table_name}'
            ORDER BY position
            """
            result = self.client.query(query)
            
            columns = {}
            for row in result.result_rows:
                col_name, col_type = row
                columns[col_name] = col_type
            
            return columns
            
        except Exception as e:
            raise Exception(f"Failed to get table schema for {table_name}: {e}")
    
    def _apply_clickhouse_type_conversions(
        self, 
        df: pd.DataFrame, 
        table_columns: Dict[str, str]
    ) -> pd.DataFrame:
        """Apply final type conversions for ClickHouse compatibility"""
        df = df.copy()
        
        for col_name, clickhouse_type in table_columns.items():
            if col_name not in df.columns:
                continue
            
            try:
                # Handle different ClickHouse types
                if 'DateTime' in clickhouse_type:
                    df[col_name] = pd.to_datetime(df[col_name], errors='coerce')
                elif 'Date' in clickhouse_type and 'DateTime' not in clickhouse_type:
                    df[col_name] = pd.to_datetime(df[col_name], errors='coerce').dt.date
                elif 'Decimal' in clickhouse_type:
                    df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                elif 'UInt8' in clickhouse_type:
                    # Handle boolean columns stored as UInt8
                    df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0).astype('int8')
                elif 'String' in clickhouse_type:
                    df[col_name] = df[col_name].astype('string').where(df[col_name].notna(), None)
                
            except Exception as e:
                print(f"Warning: Failed to convert column {col_name} to {clickhouse_type}: {e}")
                continue
        
        return df
    
    def _create_batches(self, df: pd.DataFrame) -> Iterator[pd.DataFrame]:
        """Create batches of DataFrame for insertion"""
        total_rows = len(df)
        
        for start_idx in range(0, total_rows, self.batch_size):
            end_idx = min(start_idx + self.batch_size, total_rows)
            yield df.iloc[start_idx:end_idx].copy()
    
    def _insert_batch(self, batch_df: pd.DataFrame, table_name: str) -> int:
        """
        Insert a single batch into ClickHouse.
        
        Args:
            batch_df: DataFrame batch to insert
            table_name: Target table name
            
        Returns:
            Number of rows inserted
        """
        if batch_df.empty:
            return 0
        
        try:
            # Convert DataFrame to format suitable for ClickHouse
            data_dict = self._dataframe_to_clickhouse_format(batch_df)
            
            # Insert using clickhouse_connect
            self.client.insert(
                table=table_name,
                data=data_dict,
                column_names=list(batch_df.columns)
            )
            
            return len(batch_df)
            
        except Exception as e:
            raise Exception(f"Batch insertion failed for table {table_name}: {e}")
    
    def _dataframe_to_clickhouse_format(self, df: pd.DataFrame) -> List[List[Any]]:
        """Convert DataFrame to list of lists for ClickHouse insertion"""
        # Replace NaN/None values with None for ClickHouse
        df_clean = df.where(pd.notna(df), None)
        
        # Convert to list of lists (row-wise)
        return df_clean.values.tolist()
    
    def update_manifest_success(
        self,
        manifest_id: str,
        insertion_result: InsertionResult
    ) -> None:
        """
        Update manifest table with successful insertion.
        
        Args:
            manifest_id: Manifest entry ID
            insertion_result: Result of insertion operation
        """
        try:
            if not self._table_exists(focus_config.manifest_table_name):
                print(f"Warning: Manifest table {focus_config.manifest_table_name} does not exist")
                return
            
            update_query = f"""
            ALTER TABLE {focus_config.manifest_table_name}
            UPDATE 
                processing_status = 'success',
                rows_processed = {insertion_result.rows_inserted},
                processed_at = now(),
                error_message = NULL
            WHERE id = '{manifest_id}'
            """
            
            self.client.command(update_query)
            
        except Exception as e:
            print(f"Warning: Failed to update manifest for success: {e}")
    
    def update_manifest_failure(
        self,
        manifest_id: str,
        error_message: str
    ) -> None:
        """
        Update manifest table with failed insertion.
        
        Args:
            manifest_id: Manifest entry ID
            error_message: Error message describing the failure
        """
        try:
            if not self._table_exists(focus_config.manifest_table_name):
                print(f"Warning: Manifest table {focus_config.manifest_table_name} does not exist")
                return
            
            # Escape single quotes in error message
            escaped_error = error_message.replace("'", "''")
            
            update_query = f"""
            ALTER TABLE {focus_config.manifest_table_name}
            UPDATE 
                processing_status = 'failed',
                processed_at = now(),
                error_message = '{escaped_error}'
            WHERE id = '{manifest_id}'
            """
            
            self.client.command(update_query)
            
        except Exception as e:
            print(f"Warning: Failed to update manifest for failure: {e}")
    
    def create_manifest_entry(
        self,
        file_info: ParquetFileInfo,
        manifest_id: str
    ) -> None:
        """
        Create initial manifest entry for file processing.
        
        Args:
            file_info: Information about the file being processed
            manifest_id: Unique manifest entry ID
        """
        try:
            if not self._table_exists(focus_config.manifest_table_name):
                print(f"Warning: Manifest table {focus_config.manifest_table_name} does not exist")
                return
            
            # Prepare manifest data
            manifest_data = {
                'id': manifest_id,
                'file_path': file_info.relative_path,
                'file_checksum': file_info.checksum,
                'dataset_type': file_info.dataset_type,
                'rows_processed': 0,
                'processing_status': 'processing',
                'error_message': None,
                'processed_at': datetime.now(timezone.utc),
                'manifest_metadata': str(file_info.manifest_data)  # Store as JSON string
            }
            
            # Insert manifest entry
            self.client.insert(
                table=focus_config.manifest_table_name,
                data=[list(manifest_data.values())],
                column_names=list(manifest_data.keys())
            )
            
        except Exception as e:
            print(f"Warning: Failed to create manifest entry: {e}")
    
    def close(self) -> None:
        """Close ClickHouse connection"""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None


def insert_focus_data(
    transformation_result: TransformationResult,
    file_info: ParquetFileInfo,
    manifest_id: str,
    batch_size: Optional[int] = None
) -> InsertionResult:
    """
    Convenience function to insert FOCUS data into ClickHouse.
    
    Args:
        transformation_result: Result from data transformation
        file_info: Information about the source file
        manifest_id: Manifest entry ID for tracking
        batch_size: Optional batch size override
        
    Returns:
        InsertionResult with insertion statistics and status
    """
    inserter = ClickHouseInserter(batch_size)
    
    try:
        # Create manifest entry
        inserter.create_manifest_entry(file_info, manifest_id)
        
        # Insert data
        result = inserter.insert_transformed_data(transformation_result, file_info, manifest_id)
        
        # Update manifest based on result
        if result.success:
            inserter.update_manifest_success(manifest_id, result)
        else:
            inserter.update_manifest_failure(manifest_id, result.error_message or "Unknown error")
        
        return result
        
    finally:
        inserter.close()