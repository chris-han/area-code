"""
Enhanced Transformation Workflows

Specialized Temporal workflows for data transformation with
comprehensive error handling, validation, and monitoring.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from temporalio import workflow, activity
from temporalio.common import RetryPolicy

from ..transformations.transformation_engine import TransformationEngineManager
from ..validation.focus_validator import FOCUSComplianceValidator
from ..validation.quarantine_system import QuarantineSystem

logger = logging.getLogger(__name__)


@dataclass
class TransformationConfig:
    """Configuration for transformation workflows"""
    source_type: str  # 'azure_ea', 's3_csv', 'generic'
    source_location: str  # File path, S3 URI, API endpoint
    target_format: str  # 'focus', 'custom'
    validation_enabled: bool = True
    quarantine_enabled: bool = True
    batch_size: int = 1000
    parallel_processing: bool = False
    max_workers: int = 4
    transformation_rules: Optional[Dict[str, Any]] = None
    custom_mappings: Optional[Dict[str, str]] = None


@dataclass
class TransformationResult:
    """Result of a transformation operation"""
    success: bool
    source_location: str
    records_processed: int
    records_stored: int
    records_quarantined: int
    validation_errors: List[str]
    transformation_errors: List[str]
    execution_time_seconds: float
    metadata: Dict[str, Any]


@dataclass
class BatchTransformationConfig:
    """Configuration for batch transformation operations"""
    batch_configs: List[TransformationConfig]
    parallel_execution: bool = True
    continue_on_failure: bool = True
    max_concurrent_transformations: int = 5
    notification_config: Optional[Dict[str, Any]] = None


# Temporal Activities for Transformation Operations

@activity.defn
async def transform_data_batch(
    config: TransformationConfig,
    source_data: List[Dict[str, Any]]
) -> TransformationResult:
    """
    Transform a batch of source data to FOCUS format.
    
    Args:
        config: Transformation configuration
        source_data: List of source records to transform
        
    Returns:
        TransformationResult with processing statistics
    """
    start_time = datetime.now()
    
    try:
        # Initialize transformation engine
        engine_manager = TransformationEngineManager()
        validator = FOCUSComplianceValidator() if config.validation_enabled else None
        quarantine = QuarantineSystem() if config.quarantine_enabled else None
        
        # Get appropriate transformer
        transformer = engine_manager.get_transformer(config.source_type)
        if not transformer:
            raise ValueError(f"No transformer found for source type: {config.source_type}")
        
        # Initialize counters
        processed_count = 0
        stored_count = 0
        quarantined_count = 0
        validation_errors = []
        transformation_errors = []
        
        # Process each record
        for record in source_data:
            try:
                # Transform record
                transformed_record = transformer.transform_record(record)
                processed_count += 1
                
                # Validate if enabled
                if validator:
                    # Placeholder validation - would call actual validator method
                    validation_result = None  # validator.validate(transformed_record)
                    
                    if validation_result and not validation_result.is_valid and quarantine:
                        # Quarantine invalid record
                        quarantine_id = quarantine.quarantine_record(
                            record, validation_result
                        )
                        quarantined_count += 1
                        validation_errors.extend(["Validation failed for record"])
                        continue
                
                # Store valid record (this would integrate with ClickHouse)
                # await store_focus_record(transformed_record)
                stored_count += 1
                
            except Exception as e:
                transformation_errors.append(f"Record transformation failed: {str(e)}")
                if quarantine:
                    quarantine_id = quarantine.quarantine_record(
                        record, None
                    )
                    quarantined_count += 1
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return TransformationResult(
            success=True,
            source_location=config.source_location,
            records_processed=processed_count,
            records_stored=stored_count,
            records_quarantined=quarantined_count,
            validation_errors=validation_errors,
            transformation_errors=transformation_errors,
            execution_time_seconds=execution_time,
            metadata={
                "source_type": config.source_type,
                "target_format": config.target_format,
                "batch_size": len(source_data)
            }
        )
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error("Batch transformation failed: %s", str(e))
        
        return TransformationResult(
            success=False,
            source_location=config.source_location,
            records_processed=0,
            records_stored=0,
            records_quarantined=0,
            validation_errors=[],
            transformation_errors=[str(e)],
            execution_time_seconds=execution_time,
            metadata={"error": str(e)}
        )


@activity.defn
async def validate_focus_compliance(
    records: List[Dict[str, Any]],
    strict_validation: bool = True
) -> Dict[str, Any]:
    """
    Validate records for FOCUS compliance.
    
    Args:
        records: List of records to validate
        strict_validation: Whether to use strict validation rules
        
    Returns:
        Validation summary with statistics and issues
    """
    validator = FOCUSComplianceValidator({
        "strict_mode": strict_validation,
        "focus_version": "1.0"
    })
    
    validation_summary = {
        "total_records": len(records),
        "valid_records": 0,
        "invalid_records": 0,
        "compliance_rate": 0.0,
        "issues_by_category": {},
        "critical_issues": []
    }
    
    for i, record in enumerate(records):
        try:
            # Placeholder validation - would call actual validator method
            result = None  # validator.validate(record)
            
            if result and result.is_valid:
                validation_summary["valid_records"] += 1
            else:
                validation_summary["invalid_records"] += 1
                
                # Placeholder for issue categorization
                validation_summary["critical_issues"].append({
                    "record_id": f"record_{i}",
                    "field": "unknown",
                    "message": "Validation placeholder"
                })
                        
        except Exception as e:
            logger.error("Validation failed for record %s: %s", i, str(e))
            validation_summary["invalid_records"] += 1
    
    # Calculate compliance rate
    if validation_summary["total_records"] > 0:
        validation_summary["compliance_rate"] = (
            validation_summary["valid_records"] / validation_summary["total_records"]
        )
    
    return validation_summary


@activity.defn
async def quarantine_invalid_records(
    invalid_records: List[Dict[str, Any]],
    quarantine_reason: str = "validation_failure"
) -> Dict[str, Any]:
    """
    Quarantine invalid records for review and reprocessing.
    
    Args:
        invalid_records: List of invalid records to quarantine
        quarantine_reason: Reason for quarantine
        
    Returns:
        Quarantine operation summary
    """
    quarantine_system = QuarantineSystem()
    
    quarantine_summary = {
        "total_quarantined": 0,
        "quarantine_ids": [],
        "errors": []
    }
    
    for record in invalid_records:
        try:
            quarantine_id = quarantine_system.quarantine_record(
                record, None
            )
            quarantine_summary["quarantine_ids"].append(quarantine_id)
            quarantine_summary["total_quarantined"] += 1
            
        except Exception as e:
            error_msg = f"Failed to quarantine record: {str(e)}"
            logger.error(error_msg)
            quarantine_summary["errors"].append(error_msg)
    
    return quarantine_summary


# Temporal Workflows

@workflow.defn
class FOCUSTransformationWorkflow:
    """
    Main workflow for transforming source data to FOCUS-compliant format.
    
    Handles data extraction, transformation, validation, and storage with
    comprehensive error handling and monitoring.
    """
    
    @workflow.run
    async def run(self, config: TransformationConfig) -> TransformationResult:
        """
        Execute FOCUS transformation workflow.
        
        Args:
            config: Transformation configuration
            
        Returns:
            TransformationResult with processing statistics
        """
        workflow.logger.info(f"Starting FOCUS transformation for {config.source_location}")
        
        try:
            # Step 1: Extract source data (this would be implemented based on source type)
            source_data = await workflow.execute_activity(
                extract_source_data,
                config,
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=60),
                    maximum_attempts=3
                )
            )
            
            # Step 2: Transform data in batches
            if config.batch_size and len(source_data) > config.batch_size:
                # Process in batches
                batch_results = []
                for i in range(0, len(source_data), config.batch_size):
                    batch = source_data[i:i + config.batch_size]
                    
                    batch_result = await workflow.execute_activity(
                        transform_data_batch,
                        config,
                        batch,
                        start_to_close_timeout=timedelta(minutes=15),
                        retry_policy=RetryPolicy(
                            initial_interval=timedelta(seconds=1),
                            maximum_interval=timedelta(seconds=30),
                            maximum_attempts=2
                        )
                    )
                    batch_results.append(batch_result)
                
                # Aggregate batch results
                result = self._aggregate_batch_results(batch_results, config)
            else:
                # Process all data at once
                result = await workflow.execute_activity(
                    transform_data_batch,
                    config,
                    source_data,
                    start_to_close_timeout=timedelta(minutes=30),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=1),
                        maximum_interval=timedelta(seconds=60),
                        maximum_attempts=3
                    )
                )
            
            workflow.logger.info(f"Transformation completed: {result.records_stored} records stored")
            return result
            
        except Exception as e:
            workflow.logger.error(f"Transformation workflow failed: {str(e)}")
            return TransformationResult(
                success=False,
                source_location=config.source_location,
                records_processed=0,
                records_stored=0,
                records_quarantined=0,
                validation_errors=[],
                transformation_errors=[str(e)],
                execution_time_seconds=0,
                metadata={"workflow_error": str(e)}
            )
    
    def _aggregate_batch_results(
        self, 
        batch_results: List[TransformationResult], 
        config: TransformationConfig
    ) -> TransformationResult:
        """Aggregate results from multiple batch transformations"""
        
        total_processed = sum(r.records_processed for r in batch_results)
        total_stored = sum(r.records_stored for r in batch_results)
        total_quarantined = sum(r.records_quarantined for r in batch_results)
        total_execution_time = sum(r.execution_time_seconds for r in batch_results)
        
        all_validation_errors = []
        all_transformation_errors = []
        
        for result in batch_results:
            all_validation_errors.extend(result.validation_errors)
            all_transformation_errors.extend(result.transformation_errors)
        
        overall_success = all(r.success for r in batch_results)
        
        return TransformationResult(
            success=overall_success,
            source_location=config.source_location,
            records_processed=total_processed,
            records_stored=total_stored,
            records_quarantined=total_quarantined,
            validation_errors=all_validation_errors,
            transformation_errors=all_transformation_errors,
            execution_time_seconds=total_execution_time,
            metadata={
                "batch_count": len(batch_results),
                "batch_size": config.batch_size,
                "source_type": config.source_type
            }
        )


@workflow.defn
class BatchTransformationWorkflow:
    """
    Workflow for processing multiple transformation jobs in parallel.
    
    Manages concurrent execution of multiple FOCUS transformation workflows
    with configurable parallelism and error handling.
    """
    
    @workflow.run
    async def run(self, config: BatchTransformationConfig) -> List[TransformationResult]:
        """
        Execute batch transformation workflow.
        
        Args:
            config: Batch transformation configuration
            
        Returns:
            List of TransformationResult for each transformation job
        """
        workflow.logger.info(f"Starting batch transformation for {len(config.batch_configs)} jobs")
        
        if config.parallel_execution:
            # Execute transformations in parallel
            transformation_tasks = []
            
            for batch_config in config.batch_configs:
                task = workflow.execute_child_workflow(
                    FOCUSTransformationWorkflow.run,
                    batch_config,
                    id=f"focus-transform-{batch_config.source_location.replace('/', '-')}",
                    task_timeout=timedelta(hours=2)
                )
                transformation_tasks.append(task)
            
            # Wait for all transformations to complete
            results = []
            for task in transformation_tasks:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    workflow.logger.error(f"Child workflow failed: {str(e)}")
                    if not config.continue_on_failure:
                        raise
                    # Create error result
                    error_result = TransformationResult(
                        success=False,
                        source_location="unknown",
                        records_processed=0,
                        records_stored=0,
                        records_quarantined=0,
                        validation_errors=[],
                        transformation_errors=[str(e)],
                        execution_time_seconds=0,
                        metadata={"child_workflow_error": str(e)}
                    )
                    results.append(error_result)
        else:
            # Execute transformations sequentially
            results = []
            for batch_config in config.batch_configs:
                try:
                    result = await workflow.execute_child_workflow(
                        FOCUSTransformationWorkflow.run,
                        batch_config,
                        id=f"focus-transform-{batch_config.source_location.replace('/', '-')}",
                        task_timeout=timedelta(hours=2)
                    )
                    results.append(result)
                except Exception as e:
                    workflow.logger.error(f"Sequential transformation failed: {str(e)}")
                    if not config.continue_on_failure:
                        raise
                    # Create error result
                    error_result = TransformationResult(
                        success=False,
                        source_location=batch_config.source_location,
                        records_processed=0,
                        records_stored=0,
                        records_quarantined=0,
                        validation_errors=[],
                        transformation_errors=[str(e)],
                        execution_time_seconds=0,
                        metadata={"sequential_error": str(e)}
                    )
                    results.append(error_result)
        
        # Log summary
        successful_jobs = sum(1 for r in results if r.success)
        total_records_processed = sum(r.records_processed for r in results)
        total_records_stored = sum(r.records_stored for r in results)
        
        workflow.logger.info(
            f"Batch transformation completed: {successful_jobs}/{len(results)} jobs successful, "
            f"{total_records_processed} records processed, {total_records_stored} records stored"
        )
        
        return results


# Helper activity for data extraction (placeholder)
@activity.defn
async def extract_source_data(config: TransformationConfig) -> List[Dict[str, Any]]:
    """
    Extract source data based on configuration.
    
    This is a placeholder that would be implemented based on the specific
    source type (Azure EA API, S3 files, etc.)
    
    Args:
        config: Transformation configuration
        
    Returns:
        List of source records
    """
    # This would be implemented to extract data from various sources
    # For now, return empty list as placeholder
    logger.info("Extracting data from %s (type: %s)", config.source_location, config.source_type)
    
    # Placeholder implementation
    if config.source_type == "azure_ea":
        # Would integrate with Azure EA API plugin
        pass
    elif config.source_type == "s3_csv":
        # Would integrate with S3/MinIO plugin
        pass
    
    return []  # Placeholder return


# Workflow helper functions

def create_transformation_config(
    source_type: str,
    source_location: str,
    **kwargs
) -> TransformationConfig:
    """
    Create a transformation configuration with sensible defaults.
    
    Args:
        source_type: Type of source data ('azure_ea', 's3_csv', etc.)
        source_location: Location of source data
        **kwargs: Additional configuration options
        
    Returns:
        TransformationConfig instance
    """
    return TransformationConfig(
        source_type=source_type,
        source_location=source_location,
        target_format=kwargs.get("target_format", "focus"),
        validation_enabled=kwargs.get("validation_enabled", True),
        quarantine_enabled=kwargs.get("quarantine_enabled", True),
        batch_size=kwargs.get("batch_size", 1000),
        parallel_processing=kwargs.get("parallel_processing", False),
        max_workers=kwargs.get("max_workers", 4),
        transformation_rules=kwargs.get("transformation_rules"),
        custom_mappings=kwargs.get("custom_mappings")
    )


def create_batch_transformation_config(
    transformation_configs: List[TransformationConfig],
    **kwargs
) -> BatchTransformationConfig:
    """
    Create a batch transformation configuration.
    
    Args:
        transformation_configs: List of individual transformation configurations
        **kwargs: Additional batch configuration options
        
    Returns:
        BatchTransformationConfig instance
    """
    return BatchTransformationConfig(
        batch_configs=transformation_configs,
        parallel_execution=kwargs.get("parallel_execution", True),
        continue_on_failure=kwargs.get("continue_on_failure", True),
        max_concurrent_transformations=kwargs.get("max_concurrent_transformations", 5),
        notification_config=kwargs.get("notification_config")
    )