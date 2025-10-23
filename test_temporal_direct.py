#!/usr/bin/env python3
"""
Direct test of Temporal client to debug workflow listing
"""
import asyncio
from temporalio.client import Client

async def test_temporal_connection():
    """Test direct Temporal connection and workflow listing"""
    try:
        # Connect to Temporal
        client = await Client.connect("172.18.0.3:7233")

        print("✅ Connected to Temporal successfully")

        # List workflows directly
        print("\n🔍 Listing workflows from Temporal:")
        count = 0
        async for workflow_execution in client.list_workflows(""):
            if count >= 5:
                break

            print(f"\n--- Workflow {count + 1} ---")
            print(f"ID: {workflow_execution.id}")
            print(f"Type: {workflow_execution.workflow_type}")
            print(f"Status: {workflow_execution.status}")
            print(f"Start Time: {workflow_execution.start_time}")
            print(f"Close Time: {workflow_execution.close_time}")
            print(f"Run ID: {workflow_execution.run_id}")
            print(f"Task Queue: {workflow_execution.task_queue}")

            count += 1

        if count == 0:
            print("❌ No workflows found in Temporal")
        else:
            print(f"\n✅ Found {count} workflows")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_temporal_connection())