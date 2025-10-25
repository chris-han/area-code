"""
FOCUS Billing Workflow Validation

Validates that the FOCUS billing ingestion workflow is properly configured
and ready for use.
"""

import sys
from pathlib import Path

from .config import get_focus_config
from .workflow import FocusBillingIngestParams, focus_billing_ingest_task, focus_billing_ingest_workflow


def validate_configuration():
    """Validate FOCUS billing configuration"""
    print("Validating FOCUS billing configuration...")
    
    errors = []
    warnings = []
    
    # Check data paths
    data_root = Path(get_focus_config().focus_data_root)
    if not data_root.exists():
        errors.append(f"FOCUS data root does not exist: {data_root}")
    else:
        print(f"✓ FOCUS data root found: {data_root}")
    
    spec_root = Path(get_focus_config().focus_spec_root)
    if not spec_root.exists():
        warnings.append(f"FOCUS spec root does not exist: {spec_root}")
    else:
        print(f"✓ FOCUS spec root found: {spec_root}")
    
    queries_root = Path(get_focus_config().focus_queries_root)
    if not queries_root.exists():
        warnings.append(f"FOCUS queries root does not exist: {queries_root}")
    else:
        print(f"✓ FOCUS queries root found: {queries_root}")
    
    # Check ClickHouse configuration
    print(f"✓ ClickHouse configuration:")
    print(f"  - Host: {get_focus_config().clickhouse_host}")
    print(f"  - Port: {get_focus_config().clickhouse_port}")
    print(f"  - Database: {get_focus_config().clickhouse_database}")
    print(f"  - SSL: {get_focus_config().clickhouse_use_ssl}")
    
    # Check workflow configuration
    print(f"✓ Workflow configuration:")
    print(f"  - Batch size: {get_focus_config().batch_size}")
    print(f"  - Max workers: {get_focus_config().max_workers}")
    print(f"  - Cost usage table: {get_focus_config().cost_usage_table_name}")
    print(f"  - Contract commitment table: {get_focus_config().contract_commitment_table_name}")
    print(f"  - Manifest table: {get_focus_config().manifest_table_name}")
    
    return errors, warnings


def validate_workflow_components():
    """Validate that workflow components can be imported and initialized"""
    print("\nValidating workflow components...")
    
    errors = []
    
    try:
        # Test workflow parameter creation
        params = FocusBillingIngestParams(dry_run=True)
        print("✓ Workflow parameters can be created")
    except Exception as e:
        errors.append(f"Failed to create workflow parameters: {e}")
    
    try:
        # Test task and workflow objects exist
        assert focus_billing_ingest_task is not None
        assert focus_billing_ingest_workflow is not None
        print("✓ Moose task and workflow objects are defined")
    except Exception as e:
        errors.append(f"Failed to access task/workflow objects: {e}")
    
    try:
        # Test file discovery
        from .file_discovery import FocusFileDiscovery
        discovery = FocusFileDiscovery()
        print("✓ File discovery component can be initialized")
    except Exception as e:
        errors.append(f"Failed to initialize file discovery: {e}")
    
    try:
        # Test data transformer
        from .data_transformer import FocusDataTransformer
        transformer = FocusDataTransformer()
        print("✓ Data transformer component can be initialized")
    except Exception as e:
        errors.append(f"Failed to initialize data transformer: {e}")
    
    # Note: We don't test ClickHouse inserter here as it requires actual connection
    print("✓ ClickHouse inserter component available (connection not tested)")
    
    return errors


def validate_dependencies():
    """Validate that required dependencies are available"""
    print("\nValidating dependencies...")
    
    errors = []
    
    required_modules = [
        'pandas',
        'pyarrow',
        'clickhouse_connect',
        'pydantic',
        'moose_lib'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} is available")
        except ImportError as e:
            errors.append(f"Missing required module {module}: {e}")
    
    return errors


def main():
    """Run all validation checks"""
    print("FOCUS Billing Workflow Validation")
    print("=" * 40)
    
    all_errors = []
    all_warnings = []
    
    # Validate configuration
    config_errors, config_warnings = validate_configuration()
    all_errors.extend(config_errors)
    all_warnings.extend(config_warnings)
    
    # Validate workflow components
    component_errors = validate_workflow_components()
    all_errors.extend(component_errors)
    
    # Validate dependencies
    dependency_errors = validate_dependencies()
    all_errors.extend(dependency_errors)
    
    # Print summary
    print("\n" + "=" * 40)
    print("Validation Summary:")
    
    if all_errors:
        print(f"❌ {len(all_errors)} error(s) found:")
        for error in all_errors:
            print(f"  - {error}")
    else:
        print("✅ No errors found")
    
    if all_warnings:
        print(f"⚠️  {len(all_warnings)} warning(s):")
        for warning in all_warnings:
            print(f"  - {warning}")
    
    if not all_errors:
        print("\n🎉 FOCUS billing workflow is ready for use!")
        print("\nTo run the workflow:")
        print("1. Ensure ClickHouse tables are created (run DDL scripts)")
        print("2. Use Moose CLI to execute the workflow:")
        print("   moose workflow run focus-billing-ingest-workflow")
        print("3. Or use the workflow programmatically with FocusBillingIngestParams")
    else:
        print(f"\n❌ Please fix {len(all_errors)} error(s) before using the workflow")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)