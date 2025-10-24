"""
FOCUS Billing Ingestion Workflow

Orchestrates the complete FOCUS data ingestion process from Parquet discovery
through transformation and ClickHouse insertion with comprehensive logging
and error handling.
"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass
from pydantic import BaseModel

from moose_lib import Task, TaskConfig, Workflow, WorkflowConfig, cli_log, CliLogData

from .config import focus_config
from .file_discovery import FocusFileDiscovery, ProcessedFileTracker, ParquetFileInfo
from .data_transformer import FocusDataTransformer, TransformationResult
from .clickhouse_inserter import ClickHouseInserter, InsertionResult
from .observability import focus_observability, TimedOperation


class FocusBillingIngestParams(BaseModel):
    """Parameters for FOCUS billing ingestion workflow"""
    
    # Data source configuration
    data_root: Optional[str] = None
    
    # Processing configuration
    batch_size: Optional[int] = None
    max_files: Optional[int] = None
    dry_run: bool = False
    
    # Filtering options
    dataset_type_filter: Optional[str] = None  # 'cost_usage' or 'contract_commitment'
    period_filter: Optional[str] = None        # e.g., '20250701-20250731'
    
    # Workflow behavior
    continue_on_error: bool = True
    skip_processed: bool = True


@dataclass
class WorkflowStats:
    """Statistics for workflow execution"""
    files_discovered: int = 0
    files_processed: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    total_rows_processed: int = 0
    total_processing_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class FocusBillingIngestWorkflow:
    """
    Main workflow class for FOCUS billing data ingestion.
    
    Orchestrates the complete process:
    1. Discover Parquet files in configured directory
    2. Filter and validate files
    3. Transform data for ClickHouse compatibility
    4. Insert data in batches with error handling
    5. Update manifest tracking
    6. Report comprehensive statistics
    """
    
    def __init__(self, params: FocusBillingIngestParams):
        """Initialize workflow with parameters"""
        self.params = params
        self.stats = WorkflowStats()
        
        # Initialize components
        self.file_discovery = FocusFileDiscovery(params.data_root)
        self.file_tracker = ProcessedFileTracker()
        self.data_transformer = FocusDataTransformer()
        self.clickhouse_inserter = None
        
        # Setup logging
        self.workflow_start_time = None
    
    def execute(self) -> WorkflowStats:
        """
        Execute the complete FOCUS billing ingestion workflow.
        
        Returns:
            WorkflowStats with execution results and statistics
        """
        self.workflow_start_time = time.time()
        
        try:
            self._log_info("Starting FOCUS billing ingestion workflow")
            self._log_workflow_params()
            
            # Emit workflow start metrics
            focus_observability.emit_counter("focus.workflow.started", 1.0)
            
            # Step 0: Run pre-flight validation
            self._run_preflight_validation()
            
            # Step 1: Discover files
            discovered_files = self._discover_files()
            if not discovered_files:
                self._log_info("No files discovered for processing")
                focus_observability.emit_counter("focus.workflow.completed", 1.0, {'status': 'no_files'})
                return self.stats
            
            # Step 2: Filter files
            files_to_process = self._filter_files(discovered_files)
            if not files_to_process:
                self._log_info("No files remaining after filtering")
                focus_observability.emit_counter("focus.workflow.completed", 1.0, {'status': 'no_files_after_filter'})
                return self.stats
            
            # Step 3: Initialize ClickHouse inserter
            self._initialize_clickhouse_inserter()
            
            # Step 4: Process files
            with TimedOperation(focus_observability, "focus.workflow.file_processing_time"):
                self._process_files(files_to_process)
            
            # Step 5: Generate final statistics
            self._finalize_workflow()
            
            # Emit workflow completion metrics
            focus_observability.emit_counter("focus.workflow.completed", 1.0, {'status': 'success'})
            
            return self.stats
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            self._log_error(error_msg)
            self.stats.errors.append(error_msg)
            
            # Emit workflow failure metrics
            focus_observability.emit_counter("focus.workflow.completed", 1.0, {'status': 'failed'})
            focus_observability.emit_counter("focus.workflow.errors", 1.0, {'error_type': type(e).__name__})
            
            return self.stats
            
        finally:
            self._cleanup()
    
    def _discover_files(self) -> List[ParquetFileInfo]:
        """Discover Parquet files in the configured directory"""
        self._log_info("Discovering FOCUS Parquet files...")
        
        try:
            discovered_files = self.file_discovery.discover_parquet_files()
            self.stats.files_discovered = len(discovered_files)
            
            self._log_info(f"Discovered {len(discovered_files)} Parquet files")
            
            # Log discovery breakdown by dataset type
            type_counts = {}
            for file_info in discovered_files:
                dataset_type = file_info.dataset_type
                type_counts[dataset_type] = type_counts.get(dataset_type, 0) + 1
            
            for dataset_type, count in type_counts.items():
                self._log_info(f"  - {dataset_type}: {count} files")
            
            return discovered_files
            
        except Exception as e:
            error_msg = f"File discovery failed: {str(e)}"
            self._log_error(error_msg)
            self.stats.errors.append(error_msg)
            return []
    
    def _filter_files(self, discovered_files: List[ParquetFileInfo]) -> List[ParquetFileInfo]:
        """Filter files based on workflow parameters"""
        self._log_info("Filtering files for processing...")
        
        filtered_files = discovered_files.copy()
        
        # Filter by dataset type
        if self.params.dataset_type_filter:
            filtered_files = [
                f for f in filtered_files 
                if f.dataset_type == self.params.dataset_type_filter
            ]
            self._log_info(f"Filtered to {len(filtered_files)} files by dataset type: {self.params.dataset_type_filter}")
        
        # Filter by period
        if self.params.period_filter:
            filtered_files = [
                f for f in filtered_files 
                if f.period_folder == self.params.period_filter
            ]
            self._log_info(f"Filtered to {len(filtered_files)} files by period: {self.params.period_filter}")
        
        # Filter out already processed files
        if self.params.skip_processed:
            unprocessed_files = []
            for file_info in filtered_files:
                if self.file_tracker.is_file_processed(file_info):
                    self.stats.files_skipped += 1
                else:
                    unprocessed_files.append(file_info)
            
            filtered_files = unprocessed_files
            self._log_info(f"Filtered to {len(filtered_files)} unprocessed files (skipped {self.stats.files_skipped})")
        
        # Limit number of files if specified
        if self.params.max_files and len(filtered_files) > self.params.max_files:
            filtered_files = filtered_files[:self.params.max_files]
            self._log_info(f"Limited to first {self.params.max_files} files")
        
        return filtered_files
    
    def _initialize_clickhouse_inserter(self) -> None:
        """Initialize ClickHouse inserter with workflow parameters"""
        try:
            batch_size = self.params.batch_size or focus_config.batch_size
            self.clickhouse_inserter = ClickHouseInserter(batch_size)
            self._log_info(f"Initialized ClickHouse inserter with batch size: {batch_size}")
            
        except Exception as e:
            error_msg = f"Failed to initialize ClickHouse inserter: {str(e)}"
            self._log_error(error_msg)
            raise Exception(error_msg)
    
    def _process_files(self, files_to_process: List[ParquetFileInfo]) -> None:
        """Process each file through transformation and insertion"""
        self._log_info(f"Processing {len(files_to_process)} files...")
        
        for i, file_info in enumerate(files_to_process, 1):
            try:
                self._log_info(f"Processing file {i}/{len(files_to_process)}: {file_info.relative_path}")
                
                # Process single file
                success = self._process_single_file(file_info)
                
                if success:
                    self.stats.files_processed += 1
                else:
                    self.stats.files_failed += 1
                    
                    if not self.params.continue_on_error:
                        self._log_error("Stopping workflow due to file processing failure")
                        break
                
            except Exception as e:
                error_msg = f"Failed to process file {file_info.relative_path}: {str(e)}"
                self._log_error(error_msg)
                self.stats.errors.append(error_msg)
                self.stats.files_failed += 1
                
                if not self.params.continue_on_error:
                    break
    
    def _process_single_file(self, file_info: ParquetFileInfo) -> bool:
        """
        Process a single file through the complete pipeline.
        
        Args:
            file_info: Information about the file to process
            
        Returns:
            True if processing succeeded, False otherwise
        """
        file_start_time = time.time()
        
        try:
            # Generate manifest ID for tracking
            manifest_id = self.file_tracker.mark_file_processing_started(file_info)
            
            if self.params.dry_run:
                self._log_info(f"DRY RUN: Would process {file_info.row_count} rows from {file_info.relative_path}")
                self.stats.total_rows_processed += file_info.row_count
                return True
            
            # Step 1: Transform data
            self._log_info(f"Transforming data from {file_info.relative_path}")
            transformation_result = self.data_transformer.transform_parquet_file(file_info)
            
            if not transformation_result.success:
                error_msg = f"Data transformation failed: {transformation_result.error_message}"
                self._log_error(error_msg)
                self.file_tracker.mark_file_processing_failed(manifest_id, error_msg)
                return False
            
            rows_transformed = transformation_result.rows_processed
            self._log_info(f"Transformed {rows_transformed} rows")
            
            # Step 2: Insert into ClickHouse
            self._log_info(f"Inserting data into ClickHouse")
            insertion_result = self.clickhouse_inserter.insert_transformed_data(
                transformation_result, file_info, manifest_id
            )
            
            if not insertion_result.success:
                error_msg = f"ClickHouse insertion failed: {insertion_result.error_message}"
                self._log_error(error_msg)
                self.file_tracker.mark_file_processing_failed(manifest_id, error_msg)
                return False
            
            # Step 3: Update tracking
            processing_time = time.time() - file_start_time
            self.file_tracker.mark_file_processing_success(
                manifest_id, insertion_result.rows_inserted, processing_time
            )
            
            # Update statistics
            self.stats.total_rows_processed += insertion_result.rows_inserted
            self.stats.total_processing_time += processing_time
            
            self._log_info(
                f"Successfully processed {insertion_result.rows_inserted} rows "
                f"in {processing_time:.2f} seconds "
                f"({insertion_result.batches_processed} batches)"
            )
            
            return True
            
        except Exception as e:
            processing_time = time.time() - file_start_time
            error_msg = f"File processing failed: {str(e)}"
            self._log_error(error_msg)
            
            # Try to update manifest with failure
            try:
                manifest_id = self.file_tracker._generate_manifest_id(file_info)
                self.file_tracker.mark_file_processing_failed(manifest_id, error_msg)
            except Exception:
                pass  # Don't fail on manifest update failure
            
            return False
    
    def _run_preflight_validation(self) -> None:
        """Run pre-flight validation checks"""
        self._log_info("Running pre-flight validation...")
        
        with TimedOperation(focus_observability, "focus.workflow.preflight_validation_time"):
            # Validate required tables exist
            required_tables = [
                focus_config.cost_usage_table_name,
                focus_config.contract_commitment_table_name,
                focus_config.manifest_table_name
            ]
            
            validation_results = focus_observability.verify_tables_exist(required_tables)
            
            missing_tables = [
                table for table, result in validation_results.items() 
                if not result.passed
            ]
            
            if missing_tables:
                self._log_error(f"Missing required tables: {missing_tables}")
                focus_observability.emit_counter("focus.workflow.preflight_failures", 1.0, {'reason': 'missing_tables'})
            else:
                self._log_info("All required tables exist")
                focus_observability.emit_counter("focus.workflow.preflight_success", 1.0)
    
    def _finalize_workflow(self) -> None:
        """Generate final workflow statistics and summary"""
        total_time = time.time() - self.workflow_start_time
        
        self._log_info("FOCUS billing ingestion workflow completed")
        self._log_info(f"Total execution time: {total_time:.2f} seconds")
        self._log_info(f"Files discovered: {self.stats.files_discovered}")
        self._log_info(f"Files processed: {self.stats.files_processed}")
        self._log_info(f"Files skipped: {self.stats.files_skipped}")
        self._log_info(f"Files failed: {self.stats.files_failed}")
        self._log_info(f"Total rows processed: {self.stats.total_rows_processed}")
        
        # Emit comprehensive workflow metrics
        focus_observability.measure_ingestion_performance(
            rows_processed=self.stats.total_rows_processed,
            files_processed=self.stats.files_processed,
            duration_seconds=total_time
        )
        
        # Emit individual workflow stats
        focus_observability.emit_gauge("focus.workflow.files_discovered", self.stats.files_discovered)
        focus_observability.emit_gauge("focus.workflow.files_processed", self.stats.files_processed)
        focus_observability.emit_gauge("focus.workflow.files_skipped", self.stats.files_skipped)
        focus_observability.emit_gauge("focus.workflow.files_failed", self.stats.files_failed)
        focus_observability.emit_gauge("focus.workflow.total_rows", self.stats.total_rows_processed)
        focus_observability.emit_timer("focus.workflow.total_time", total_time)
        
        if self.stats.total_rows_processed > 0 and self.stats.total_processing_time > 0:
            rows_per_second = self.stats.total_rows_processed / self.stats.total_processing_time
            self._log_info(f"Average processing rate: {rows_per_second:.0f} rows/second")
        
        if self.stats.errors:
            self._log_error(f"Encountered {len(self.stats.errors)} errors during processing")
            focus_observability.emit_gauge("focus.workflow.error_count", len(self.stats.errors))
        
        # Run post-workflow validation
        self._run_post_workflow_validation()
    
    def _run_post_workflow_validation(self) -> None:
        """Run post-workflow validation checks"""
        if self.stats.files_processed > 0:
            self._log_info("Running post-workflow validation...")
            
            with TimedOperation(focus_observability, "focus.workflow.post_validation_time"):
                # Validate referential integrity
                integrity_result = focus_observability.validate_contract_commitment_integrity()
                
                if integrity_result.passed:
                    self._log_info("Contract commitment referential integrity validated successfully")
                else:
                    self._log_error(f"Referential integrity issues found: {integrity_result.message}")
                
                # Get updated row counts
                row_counts = focus_observability.get_table_row_counts([
                    focus_config.cost_usage_table_name,
                    focus_config.contract_commitment_table_name,
                    focus_config.manifest_table_name
                ])
                
                self._log_info(f"Final table row counts: {row_counts}")
    
    def _cleanup(self) -> None:
        """Clean up resources"""
        if self.clickhouse_inserter:
            try:
                self.clickhouse_inserter.close()
            except Exception:
                pass
        
        # Close observability connections
        try:
            focus_observability.close()
        except Exception:
            pass
    
    def _log_workflow_params(self) -> None:
        """Log workflow parameters for debugging"""
        self._log_info("Workflow parameters:")
        self._log_info(f"  - Data root: {self.params.data_root or focus_config.focus_data_root}")
        self._log_info(f"  - Batch size: {self.params.batch_size or focus_config.batch_size}")
        self._log_info(f"  - Max files: {self.params.max_files or 'unlimited'}")
        self._log_info(f"  - Dry run: {self.params.dry_run}")
        self._log_info(f"  - Dataset filter: {self.params.dataset_type_filter or 'all'}")
        self._log_info(f"  - Period filter: {self.params.period_filter or 'all'}")
        self._log_info(f"  - Continue on error: {self.params.continue_on_error}")
        self._log_info(f"  - Skip processed: {self.params.skip_processed}")
    
    def _log_info(self, message: str) -> None:
        """Log info message"""
        cli_log(CliLogData(
            action="FocusBillingIngest",
            message=message,
            message_type="Info"
        ))
    
    def _log_error(self, message: str) -> None:
        """Log error message"""
        cli_log(CliLogData(
            action="FocusBillingIngest",
            message=message,
            message_type="Error"
        ))


def run_focus_billing_ingest_task(params: FocusBillingIngestParams) -> None:
    """
    Task function for FOCUS billing ingestion workflow.
    
    Args:
        params: Workflow parameters
    """
    workflow = FocusBillingIngestWorkflow(params)
    stats = workflow.execute()
    
    # Log final summary
    if stats.files_failed > 0:
        cli_log(CliLogData(
            action="FocusBillingIngest",
            message=f"Workflow completed with {stats.files_failed} failures out of {stats.files_discovered} files",
            message_type="Warning"
        ))
    else:
        cli_log(CliLogData(
            action="FocusBillingIngest",
            message=f"Workflow completed successfully: {stats.files_processed} files, {stats.total_rows_processed} rows",
            message_type="Info"
        ))


# Moose Task and Workflow definitions
focus_billing_ingest_task = Task[FocusBillingIngestParams, None](
    name="focus-billing-ingest-task",
    config=TaskConfig(run=run_focus_billing_ingest_task)
)

focus_billing_ingest_workflow = Workflow(
    name="focus-billing-ingest-workflow",
    config=WorkflowConfig(starting_task=focus_billing_ingest_task)
)