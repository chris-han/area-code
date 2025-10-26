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

from app.focus_billing.temporal_workflow import (
    FocusBillingTemporalWorkflow,
    run_focus_billing_ingest_activity,
)
from app.focus_billing.schema_migration import (
    SchemaMigrationWorkflow,
    detect_schema_diff,
    generate_transformation_code,
    apply_transformation_and_load_data,
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

            # Configure sandbox to passthrough focus_billing (avoids complex dependencies with moose_lib, clickhouse_connect)
            from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions

            sandbox_restrictions = SandboxRestrictions.default.with_passthrough_modules(
                "app.focus_billing",
                "moose_lib",
                "clickhouse_connect",
            )

            self.worker = Worker(
                self.client,
                task_queue=task_queue,
                workflow_runner=SandboxedWorkflowRunner(restrictions=sandbox_restrictions),
                workflows=[
                    FocusBillingTemporalWorkflow,
                    SchemaMigrationWorkflow,
                ],
                activities=[
                    run_focus_billing_ingest_activity,
                    detect_schema_diff,
                    generate_transformation_code,
                    apply_transformation_and_load_data,
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
