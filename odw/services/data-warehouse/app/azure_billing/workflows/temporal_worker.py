"""
Temporal Worker for Azure Billing Intelligence

Worker process that executes Temporal workflows and activities
for Azure billing data processing.
"""

import asyncio
import logging
from typing import Dict, Any

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

from .temporal_workflows import (
    AzureBillingWorkflow,
    FOCUSTransformationWorkflow,
    DataValidationWorkflow,
    AzureBlobIngestWorkflow,
    AzureBillingTestWorkflow,
    extract_azure_billing_data_activity,
    transform_to_focus_activity,
    validate_focus_compliance_activity,
    store_focus_data_activity,
    run_azure_blob_ingest_activity,
    generate_mock_azure_billing_data_activity,
    write_mock_azure_billing_data_activity,
)
from app.focus_billing.temporal_workflow import (
    FocusBillingTemporalWorkflow,
    run_focus_billing_ingest_activity,
)

logger = logging.getLogger(__name__)


class TemporalWorkerManager:
    """Manager for Temporal worker processes"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self.worker = None
        
    async def initialize(self):
        """Initialize Temporal client and worker"""
        try:
            # Connect to Temporal server
            temporal_host = self.config.get('temporal_host', 'localhost:7233')
            self.client = await Client.connect(temporal_host)
            
            # Create worker
            task_queue = self.config.get('task_queue', 'bia-workflows')
            
            self.worker = Worker(
                self.client,
                task_queue=task_queue,
                workflows=[
                    AzureBillingWorkflow,
                    FOCUSTransformationWorkflow,
                    DataValidationWorkflow,
                    AzureBlobIngestWorkflow,
                    AzureBillingTestWorkflow,
                    FocusBillingTemporalWorkflow,
                ],
                activities=[
                    extract_azure_billing_data_activity,
                    transform_to_focus_activity,
                    validate_focus_compliance_activity,
                    store_focus_data_activity,
                    run_azure_blob_ingest_activity,
                    generate_mock_azure_billing_data_activity,
                    write_mock_azure_billing_data_activity,
                    run_focus_billing_ingest_activity,
                ]
            )
            
            logger.info(f"Temporal worker initialized for task queue: {task_queue}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Temporal worker: {e}")
            raise
    
    async def start(self):
        """Start the Temporal worker"""
        if not self.worker:
            await self.initialize()
        
        try:
            logger.info("Starting Temporal worker...")
            await self.worker.run()
            
        except Exception as e:
            logger.error(f"Temporal worker error: {e}")
            raise
    
    async def stop(self):
        """Stop the Temporal worker"""
        if self.worker:
            logger.info("Stopping Temporal worker...")
            await self.worker.shutdown()

        if self.client:
            close_method = getattr(self.client, "close", None)
            disconnect_method = getattr(self.client, "disconnect", None)

            if close_method:
                result = close_method()
                if asyncio.iscoroutine(result):
                    await result
            elif disconnect_method:
                result = disconnect_method()
                if asyncio.iscoroutine(result):
                    await result


async def run_worker(config: Dict[str, Any] = None):
    """
    Run the Temporal worker process.
    
    Args:
        config: Worker configuration
    """
    
    if config is None:
        config = {
            'temporal_host': 'localhost:7233',  # This will be overridden by env var
            'task_queue': 'bia-workflows'
        }
    
    worker_manager = TemporalWorkerManager(config)
    
    try:
        await worker_manager.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await worker_manager.stop()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the worker
    asyncio.run(run_worker())
