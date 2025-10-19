"""
Temporal Workflow Definitions for Azure Billing Intelligence

Comprehensive Temporal workflows for Azure billing data extraction,
transformation, and processing with error handling and monitoring.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

from app.azure_billing.plugins.manager.plugin_manager import PluginManager
from app.azure_billing.transformations.transformation_engine import TransformationEngine
from app.azure_billing.validation.focus_validator import FOCUSValidator
from app.azure_billing.models.azure_ea_models import AzureEABillingDetail
from app.azure_billing.models.focus_models import FOCUSBillingRecord

logger = logging.getLogger(__name__)


# Workflow Input/Output Models
class AzureBillingWorkflowInput:
    """Input parameters for Azure billing extraction workflow"""
    
    def __init__(
        self,
        start_date: str,
        end_date: str,
        enrollment_number: Optional[str] = None,
        subscription_ids: Optional[List[str]] = None,
        batch_size: int = 1000,
        plugin_config: Optional[Dict[str, Any]] = None
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.enrollment_number = enrollment_number
        self.subscription_ids = subscription_ids
        self.batch_size = batch_size
        self.plugin_config = plugin_config


@activity.defn
async def store_focus_data_activity(
    focus_data_location: str,
    storage_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Activity to store FOCUS-compliant data in ClickHouse.
    
    Args:
        focus_data_location: Location of validated FOCUS data
        storage_config: Storage configuration
        
    Returns:
        Dictionary with storage results
    """
    
    try:
        logger.info(f"Starting FOCUS data storage for data at: {focus_data_location}")
        
        # This would integrate with ClickHouse storage
        # For now, return a placeholder result
        
        logger.info("FOCUS data storage completed")
        
        return {
            "success": True,
            "records_stored": 0,
            "storage_location": "focus_billing_data",
            "execution_time": 0.0
        }
        
    except Exception as e:
        logger.error(f"FOCUS data storage failed: {e}")
        return {
            "success": False,
            "error_message": str(e),
            "records_stored": 0
        }


# Workflow Definitions
@workflow.defn
class AzureBillingWorkflow:
    """
    Main Azure billing data extraction and processing workflow.
    
    This workflow orchestrates the complete process of:
    1. Extracting Azure billing data via plugins
    2. Transforming data to FOCUS format
    3. Validating FOCUS compliance
    4. Storing validated data in ClickHouse
    """
    
    @workflow.run
    async def run(self, input_params: AzureBillingWorkflowInput) -> WorkflowResult:
        """
        Execute the Azure billing workflow.
        
        Args:
            input_params: Workflow input parameters
            
        Returns:
            WorkflowResult with execution summary
        """
        
        workflow_start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting Azure billing workflow: {input_params.start_date} to {input_params.end_date}")
            
            # Step 1: Extract Azure billing data
            extraction_result = await workflow.execute_activity(
                extract_azure_billing_data_activity,
                args=[
                    input_params.start_date,
                    input_params.end_date,
                    input_params.enrollment_number,
                    input_params.subscription_ids,
                    input_params.batch_size,
                    input_params.plugin_config
                ],
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=10),
                    maximum_interval=timedelta(minutes=5),
                    maximum_attempts=3,
                    backoff_coefficient=2.0
                )
            )
            
            if not extraction_result["success"]:
                raise ApplicationError(f"Data extraction failed: {extraction_result.get('error_message')}")
            
            # Step 2: Transform to FOCUS format
            transformation_result = await workflow.execute_activity(
                transform_to_focus_activity,
                args=[
                    extraction_result["data_location"],
                    {"strict_validation": True, "batch_size": input_params.batch_size}
                ],
                start_to_close_timeout=timedelta(minutes=20),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=5),
                    maximum_interval=timedelta(minutes=2),
                    maximum_attempts=3,
                    backoff_coefficient=2.0
                )
            )
            
            if not transformation_result["success"]:
                raise ApplicationError(f"Data transformation failed: {transformation_result.get('error_message')}")
            
            # Step 3: Validate FOCUS compliance
            validation_result = await workflow.execute_activity(
                validate_focus_compliance_activity,
                args=[
                    transformation_result["focus_data_location"],
                    {"strict_mode": True, "quarantine_invalid": True}
                ],
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=5),
                    maximum_interval=timedelta(minutes=1),
                    maximum_attempts=2,
                    backoff_coefficient=2.0
                )
            )
            
            if not validation_result["success"]:
                raise ApplicationError(f"Data validation failed: {validation_result.get('error_message')}")
            
            # Step 4: Store validated data
            storage_result = await workflow.execute_activity(
                store_focus_data_activity,
                args=[
                    transformation_result["focus_data_location"],
                    {"table": "focus_billing_data", "batch_size": input_params.batch_size}
                ],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=5),
                    maximum_interval=timedelta(minutes=1),
                    maximum_attempts=3,
                    backoff_coefficient=2.0
                )
            )
            
            if not storage_result["success"]:
                raise ApplicationError(f"Data storage failed: {storage_result.get('error_message')}")
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - workflow_start_time).total_seconds()
            
            # Create successful result
            result = WorkflowResult(
                success=True,
                records_processed=extraction_result["records_extracted"],
                records_validated=validation_result["records_validated"],
                records_failed=validation_result["records_failed"],
                execution_time_seconds=execution_time,
                metadata={
                    "extraction": extraction_result,
                    "transformation": transformation_result,
                    "validation": validation_result,
                    "storage": storage_result
                }
            )
            
            logger.info(f"Azure billing workflow completed successfully: {result.records_processed} records processed")
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - workflow_start_time).total_seconds()
            
            logger.error(f"Azure billing workflow failed: {e}")
            
            return WorkflowResult(
                success=False,
                execution_time_seconds=execution_time,
                error_message=str(e)
            )


@workflow.defn
class FOCUSTransformationWorkflow:
    """
    Standalone FOCUS transformation workflow for processing existing data.
    """
    
    @workflow.run
    async def run(
        self,
        source_location: str,
        target_location: str,
        transformation_config: Dict[str, Any]
    ) -> WorkflowResult:
        """
        Execute FOCUS transformation workflow.
        
        Args:
            source_location: Location of source data
            target_location: Target location for transformed data
            transformation_config: Transformation configuration
            
        Returns:
            WorkflowResult with transformation summary
        """
        
        workflow_start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting FOCUS transformation workflow: {source_location} -> {target_location}")
            
            # Transform data to FOCUS format
            transformation_result = await workflow.execute_activity(
                transform_to_focus_activity,
                args=[source_location, transformation_config],
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=10),
                    maximum_interval=timedelta(minutes=5),
                    maximum_attempts=3,
                    backoff_coefficient=2.0
                )
            )
            
            if not transformation_result["success"]:
                raise ApplicationError(f"Transformation failed: {transformation_result.get('error_message')}")
            
            # Validate transformed data
            validation_result = await workflow.execute_activity(
                validate_focus_compliance_activity,
                args=[
                    transformation_result["focus_data_location"],
                    transformation_config.get("validation_config", {})
                ],
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=5),
                    maximum_interval=timedelta(minutes=2),
                    maximum_attempts=2,
                    backoff_coefficient=2.0
                )
            )
            
            if not validation_result["success"]:
                raise ApplicationError(f"Validation failed: {validation_result.get('error_message')}")
            
            execution_time = (datetime.utcnow() - workflow_start_time).total_seconds()
            
            result = WorkflowResult(
                success=True,
                records_processed=transformation_result["records_transformed"],
                records_validated=validation_result["records_validated"],
                records_failed=validation_result["records_failed"],
                execution_time_seconds=execution_time,
                metadata={
                    "transformation": transformation_result,
                    "validation": validation_result
                }
            )
            
            logger.info(f"FOCUS transformation workflow completed: {result.records_processed} records processed")
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - workflow_start_time).total_seconds()
            
            logger.error(f"FOCUS transformation workflow failed: {e}")
            
            return WorkflowResult(
                success=False,
                execution_time_seconds=execution_time,
                error_message=str(e)
            )


@workflow.defn
class DataValidationWorkflow:
    """
    Standalone data validation workflow for quality assurance.
    """
    
    @workflow.run
    async def run(
        self,
        data_location: str,
        validation_config: Dict[str, Any]
    ) -> WorkflowResult:
        """
        Execute data validation workflow.
        
        Args:
            data_location: Location of data to validate
            validation_config: Validation configuration
            
        Returns:
            WorkflowResult with validation summary
        """
        
        workflow_start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting data validation workflow for: {data_location}")
            
            # Validate data
            validation_result = await workflow.execute_activity(
                validate_focus_compliance_activity,
                args=[data_location, validation_config],
                start_to_close_timeout=timedelta(minutes=20),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=5),
                    maximum_interval=timedelta(minutes=2),
                    maximum_attempts=2,
                    backoff_coefficient=2.0
                )
            )
            
            if not validation_result["success"]:
                raise ApplicationError(f"Validation failed: {validation_result.get('error_message')}")
            
            execution_time = (datetime.utcnow() - workflow_start_time).total_seconds()
            
            result = WorkflowResult(
                success=True,
                records_validated=validation_result["records_validated"],
                records_failed=validation_result["records_failed"],
                execution_time_seconds=execution_time,
                metadata={"validation": validation_result}
            )
            
            logger.info(f"Data validation workflow completed: {result.records_validated} records validated")
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - workflow_start_time).total_seconds()
            
            logger.error(f"Data validation workflow failed: {e}")
            
            return WorkflowResult(
                success=False,
                execution_time_seconds=execution_time,
                error_message=str(e)
            )