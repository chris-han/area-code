#!/usr/bin/env python
"""
Test script for dynamic workflow registry

Demonstrates how workflows are discovered at runtime from the temporal_worker
configuration instead of being hardcoded.
"""

import json
from bia_backend.services.workflow_registry import get_workflow_registry

def main():
    print("=" * 80)
    print("Dynamic Workflow Registry Test")
    print("=" * 80)
    print()

    # Get the workflow registry
    registry = get_workflow_registry()

    # List all discovered workflow types
    workflow_types = registry.get_workflow_types()
    print(f"✅ Discovered {len(workflow_types)} workflow types:")
    for wf_type in workflow_types:
        print(f"   - {wf_type}")
    print()

    # Show detailed metadata for each workflow
    print("📋 Workflow Metadata:")
    print("-" * 80)
    workflows = registry.get_workflows()
    for workflow in workflows:
        print()
        print(f"Workflow Type: {workflow['workflow_type']}")
        print(f"Display Name:  {workflow['display_name']}")
        print(f"Class Name:    {workflow['workflow_class']}")
        print(f"Duration:      {workflow['estimated_duration']}")
        print(f"Description:   {workflow['description']}")
        print("-" * 80)

    print()
    print("🔍 Testing Workflow Lookup:")
    print("-" * 80)

    # Test workflow lookups
    test_types = ['focus_billing_ingest', 'schema_migration', 'non_existent']
    for wf_type in test_types:
        workflow = registry.get_workflow(wf_type)
        if workflow:
            print(f"✅ Found: {wf_type} → {workflow['display_name']}")
        else:
            print(f"❌ Not found: {wf_type}")

    print()
    print("🔄 Testing Class Name Conversions:")
    print("-" * 80)

    # Test class name to workflow type conversion
    test_classes = ['FocusBillingTemporalWorkflow', 'SchemaMigrationWorkflow']
    for class_name in test_classes:
        wf_type = registry.class_name_to_workflow_type(class_name)
        print(f"{class_name} → {wf_type}")

    print()
    print("=" * 80)
    print("✅ Workflow Registry Test Complete")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Workflows are discovered dynamically from temporal_worker.py")
    print(f"  - No hardcoded workflow types needed in workflow_management.py")
    print(f"  - New workflows auto-register when added to temporal_worker")
    print(f"  - Fallback to hardcoded values if discovery fails")
    print()


if __name__ == "__main__":
    main()
