#!/usr/bin/env python3
"""
Debug workflow type mapping
"""
import asyncio
from temporalio.client import Client

# Import the TemporalClient to test its mapping
import sys
import os
sys.path.append('/home/chris/repo/area-code/odw/services/data-warehouse')
from bia_backend.services.temporal_client import TemporalClient

async def debug_workflow_mapping():
    """Debug workflow type mapping"""
    try:
        # Connect to Temporal
        client = await Client.connect("172.18.0.3:7233")

        print("🔍 Testing workflow type mapping")

        # List workflows and test mapping
        count = 0
        async for workflow_execution in client.list_workflows(""):
            if count >= 3:
                break

            workflow_type_str = str(workflow_execution.workflow_type)
            print(f"\n--- Workflow {count + 1} ---")
            print(f"ID: {workflow_execution.id}")
            print(f"Raw Type: {workflow_type_str}")
            print(f"Type Attr: {type(workflow_execution.workflow_type)}")

            # Test the resolve function
            resolved = TemporalClient.resolve_workflow_type(workflow_type_str)
            print(f"Resolved Type: {resolved}")

            # Show the mapping that should work
            print(f"WORKFLOW_CLASS_MAP: {TemporalClient.WORKFLOW_CLASS_MAP}")

            count += 1

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_workflow_mapping())