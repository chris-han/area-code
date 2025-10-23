#!/usr/bin/env python3
"""
Minimal working Temporal worker using tested connection logic
"""
import os
import asyncio
import subprocess
import json
import socket
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_temporal_host():
    """Get the correct Temporal host using container name as requested"""
    try:
        # Check if we're running in Docker environment
        subprocess.run([
            'docker', 'inspect', 'data-warehouse-temporal-1'
        ], capture_output=True, text=True, check=True)

        # Use container name (more stable than IP as requested by user)
        logger.info("Using container name for connection")
        return "data-warehouse-temporal-1:7233"

    except Exception as e:
        logger.info(f"Docker container not found, using localhost: {e}")
        return "localhost:7233"

async def main():
    from temporalio.client import Client
    from temporalio.worker import Worker
    from app.azure_billing.workflows.temporal_workflows import (
        AzureBillingWorkflow,
        FOCUSTransformationWorkflow,
        DataValidationWorkflow,
        AzureBlobIngestWorkflow,
        extract_azure_billing_data_activity,
        transform_to_focus_activity,
        validate_focus_compliance_activity,
        store_focus_data_activity,
        run_azure_blob_ingest_activity,
    )

    temporal_host = get_temporal_host()
    logger.info(f"🔗 Connecting to Temporal at: {temporal_host}")

    try:
        # Connect to Temporal
        client = await Client.connect(temporal_host)
        logger.info("✅ Connected to Temporal successfully!")

        # Create worker
        task_queue = 'abi-workflows'

        worker = Worker(
            client,
            task_queue=task_queue,
            workflows=[
                AzureBillingWorkflow,
                FOCUSTransformationWorkflow,
                DataValidationWorkflow,
                AzureBlobIngestWorkflow,
            ],
            activities=[
                extract_azure_billing_data_activity,
                transform_to_focus_activity,
                validate_focus_compliance_activity,
                store_focus_data_activity,
                run_azure_blob_ingest_activity,
            ]
        )

        logger.info(f"🚀 Starting Temporal worker for task queue: {task_queue}")
        logger.info("🔄 Worker is now polling for tasks...")

        # Run worker (this will run indefinitely)
        await worker.run()

    except Exception as e:
        logger.error(f"❌ Worker failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())