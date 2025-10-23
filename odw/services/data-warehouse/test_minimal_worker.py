#!/usr/bin/env python3
"""
Minimal Temporal worker test for debugging connection and import issues
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
    """Get the correct Temporal host using container name or IP"""
    try:
        # Check if we're running in Docker environment
        result = subprocess.run([
            'docker', 'inspect', 'data-warehouse-temporal-1'
        ], capture_output=True, text=True, check=True)

        # First try container name (works if worker is also in Docker network)
        try:
            socket.gethostbyname("data-warehouse-temporal-1")
            logger.info("Using container name resolution")
            return "data-warehouse-temporal-1:7233"
        except socket.gaierror:
            # Container name not resolvable, get container IP
            data = json.loads(result.stdout)
            if data and len(data) > 0:
                networks = data[0].get('NetworkSettings', {}).get('Networks', {})
                for network_name, network_info in networks.items():
                    ip_address = network_info.get('IPAddress')
                    if ip_address:
                        logger.info(f"Using container IP: {ip_address}")
                        return f"{ip_address}:7233"

            # Fallback to localhost
            logger.info("Using localhost fallback")
            return "localhost:7233"

    except Exception as e:
        logger.info(f"Docker container not found, using localhost: {e}")
        return "localhost:7233"

async def test_temporal_connection():
    """Test Temporal client connection without worker initialization"""
    from temporalio.client import Client

    temporal_host = get_temporal_host()
    logger.info(f"🔗 Testing connection to Temporal at: {temporal_host}")

    try:
        client = await Client.connect(temporal_host)
        logger.info("✅ Successfully connected to Temporal!")

        # Test basic client functionality
        workflows = client.list_workflows()
        workflow_count = 0
        async for workflow in workflows:
            workflow_count += 1
            if workflow_count >= 5:  # Limit to first 5
                break

        logger.info(f"📊 Found {workflow_count} workflow executions")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to connect to Temporal: {e}")
        return False

async def test_workflow_imports():
    """Test importing workflow modules without sandbox restrictions"""
    logger.info("🔍 Testing workflow imports...")

    try:
        # Test basic temporal imports
        from temporalio import workflow, activity
        logger.info("✅ Basic Temporal imports successful")

        # Test workflow module imports
        from app.azure_billing.workflows.temporal_workflows import AzureBillingWorkflow
        logger.info("✅ AzureBillingWorkflow import successful")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to import workflows: {e}")
        return False

async def main():
    logger.info("🚀 Starting minimal Temporal worker test...")

    # Test 1: Connection
    connection_ok = await test_temporal_connection()
    if not connection_ok:
        logger.error("Connection test failed, stopping")
        return

    # Test 2: Imports
    imports_ok = await test_workflow_imports()
    if not imports_ok:
        logger.error("Import test failed, stopping")
        return

    logger.info("🎉 All tests passed! Worker should be able to start successfully.")

if __name__ == "__main__":
    asyncio.run(main())