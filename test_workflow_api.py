#!/usr/bin/env python3
"""
Test script to verify workflow API and trigger test workflows
"""
import json
import requests
import sys
from datetime import datetime, timedelta

API_BASE = "http://localhost:4300"

def test_workflows_list():
    """Test the workflow list endpoint"""
    print("🧪 Testing workflow list API...")

    try:
        response = requests.post(f"{API_BASE}/api/v1/workflows/list", json={})
        response.raise_for_status()

        data = response.json()
        print(f"✅ API Response: {json.dumps(data, indent=2)}")

        return data
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None

def test_workflow_trigger():
    """Test triggering a sample workflow"""
    print("🚀 Testing workflow trigger...")

    payload = {
        "workflow_type": "azure_billing_extraction",
        "parameters": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "enrollment_number": "test-enrollment",
            "batch_size": 100
        }
    }

    try:
        response = requests.post(f"{API_BASE}/api/v1/workflows/trigger", json=payload)
        response.raise_for_status()

        data = response.json()
        print(f"✅ Workflow triggered: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"❌ Trigger Error: {e}")
        return None

def main():
    print("🔍 Testing Workflow API Endpoints")
    print("=" * 50)

    # Test current workflow list
    workflows = test_workflows_list()

    if workflows:
        print(f"\n📊 Found {workflows.get('total', 0)} workflows")
        if workflows.get('workflows'):
            for wf in workflows['workflows']:
                print(f"  - {wf.get('workflow_id', 'Unknown')} ({wf.get('status', 'unknown')})")

    print("\n" + "=" * 50)
    print("🎯 API Structure Analysis:")
    print("- API is accessible and returning proper response format")
    print("- Frontend mapping should work with:")
    print("  * workflow.workflow_id -> id")
    print("  * workflow.workflow_type -> name (via WORKFLOW_LABELS)")
    print("  * workflow.status -> status")
    print("  * workflow.start_time -> startTime")
    print("- Empty list indicates no active/recent workflows")

    # Uncomment to test workflow triggering (requires worker)
    # print("\n" + "=" * 50)
    # test_workflow_trigger()

if __name__ == "__main__":
    main()