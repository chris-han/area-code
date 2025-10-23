#!/usr/bin/env python3
"""
Script to trigger a sample workflow for testing frontend display
"""
import requests
import json

def trigger_sample_workflow():
    """Trigger a sample workflow for testing"""

    API_BASE = "http://localhost:4300"

    payload = {
        "workflow_type": "azure_billing_extraction",
        "parameters": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "enrollment_number": "test-enrollment-123",
            "batch_size": 100
        }
    }

    print("🚀 Triggering sample workflow...")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(f"{API_BASE}/api/v1/workflows/trigger", json=payload)
        response.raise_for_status()

        result = response.json()
        print(f"✅ Workflow triggered: {json.dumps(result, indent=2)}")

        print("\n📝 Next steps:")
        print("1. Visit http://localhost:3003/workflows")
        print("2. Refresh the page to see the new workflow")
        print("3. Check Temporal UI at http://localhost:8080")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure the API server is running on port 4300")

if __name__ == "__main__":
    trigger_sample_workflow()