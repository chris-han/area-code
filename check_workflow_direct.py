#!/usr/bin/env python3
"""
Direct check of Temporal workflow status
"""
import asyncio
import sys
from temporalio.client import Client

async def check_workflow_status(workflow_id: str):
    """Check workflow status directly through Temporal client"""
    try:
        # Connect to Temporal
        client = await Client.connect("172.18.0.3:7233")

        # Get workflow handle
        handle = client.get_workflow_handle(workflow_id)

        # Get workflow description
        try:
            description = await handle.describe()
            print(f"Workflow ID: {workflow_id}")
            print(f"Status: {description.status.name}")
            print(f"Workflow Type: {description.workflow_type.name if description.workflow_type else 'Unknown'}")
            print(f"Start Time: {description.start_time}")
            print(f"Close Time: {description.close_time}")
            print(f"Run ID: {description.run_id}")

            # Try to get result if completed
            if description.status.name == "WORKFLOW_EXECUTION_STATUS_COMPLETED":
                try:
                    result = await handle.result()
                    print(f"Result: {result}")
                except Exception as e:
                    print(f"Could not get result: {e}")

        except Exception as e:
            print(f"Could not get workflow description: {e}")

        # List all recent workflows
        print("\n--- Recent Workflows ---")
        count = 0
        async for workflow_execution in client.list_workflows(""):
            if count >= 10:
                break
            print(f"ID: {workflow_execution.workflow_execution.workflow_id}")
            print(f"Type: {workflow_execution.workflow_type.name if workflow_execution.workflow_type else 'Unknown'}")
            print(f"Status: {workflow_execution.status.name}")
            print(f"Start: {workflow_execution.start_time}")
            print("---")
            count += 1

    except Exception as e:
        print(f"Error connecting to Temporal: {e}")

if __name__ == "__main__":
    workflow_id = sys.argv[1] if len(sys.argv) > 1 else "wf_test_workflow_20251023_122821"
    asyncio.run(check_workflow_status(workflow_id))