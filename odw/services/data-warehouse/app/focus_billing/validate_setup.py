#!/usr/bin/env python3
"""
FOCUS Billing Setup Validation

Validates that the FOCUS billing module is properly set up with all
core interfaces and data models.
"""

from pathlib import Path
from .config import FocusBillingConfig
from .models import FocusCostUsage, FocusContractCommitment, FocusColumn
from .constants import FocusTableNames, FocusDatasetType
from .utils.naming import snake_to_pascal_case, pascal_to_snake_case
from .utils.type_mapping import map_focus_to_clickhouse_type
from .schema.loader import FocusSchemaLoader


def validate_configuration():
    """Validate FOCUS billing configuration"""
    print("🔧 Validating FOCUS billing configuration...")
    
    config = FocusBillingConfig()
    
    # Test basic configuration
    assert config.batch_size > 0, "Batch size must be positive"
    assert config.cost_usage_table_name, "Cost usage table name must be set"
    assert config.contract_commitment_table_name, "Contract commitment table name must be set"
    
    # Test ClickHouse URL generation
    url = config.get_clickhouse_url()
    assert url.startswith(('http://', 'https://')), "ClickHouse URL must be valid"
    
    print("✓ Configuration validation passed")


def validate_data_models():
    """Validate FOCUS data models"""
    print("📊 Validating FOCUS data models...")
    
    # Test FocusCostUsage model
    cost_usage_data = {
        'id': 'test-id-123',
        'billing_account_id': 'account-123',
        'usage_date': '2024-01-01',
        'billed_cost': '100.50'
    }
    
    try:
        cost_usage = FocusCostUsage(**cost_usage_data)
        assert cost_usage.billing_account_id == 'account-123'
        print("✓ FocusCostUsage model validation passed")
    except Exception as e:
        print(f"❌ FocusCostUsage model validation failed: {e}")
        raise
    
    # Test FocusContractCommitment model
    commitment_data = {
        'id': 'commitment-id-123',
        'contract_commitment_id': 'commitment-456'
    }
    
    try:
        commitment = FocusContractCommitment(**commitment_data)
        assert commitment.contract_commitment_id == 'commitment-456'
        print("✓ FocusContractCommitment model validation passed")
    except Exception as e:
        print(f"❌ FocusContractCommitment model validation failed: {e}")
        raise


def validate_utilities():
    """Validate utility functions"""
    print("🛠️ Validating utility functions...")
    
    # Test naming utilities
    assert snake_to_pascal_case('billing_account_id') == 'BillingAccountId'
    assert pascal_to_snake_case('BillingAccountId') == 'billing_account_id'
    print("✓ Naming utilities validation passed")
    
    # Test type mapping
    clickhouse_type = map_focus_to_clickhouse_type('String', True)
    assert 'String' in clickhouse_type
    print("✓ Type mapping utilities validation passed")


def validate_constants():
    """Validate constants and enums"""
    print("📋 Validating constants...")
    
    # Test table names
    assert FocusTableNames.COST_USAGE == 'focus_cost_usage'
    assert FocusTableNames.CONTRACT_COMMITMENT == 'focus_contract_commitment'
    
    # Test dataset types
    assert FocusDatasetType.COST_USAGE == 'cost_and_usage'
    assert FocusDatasetType.CONTRACT_COMMITMENT == 'contract_commitment'
    
    print("✓ Constants validation passed")


def validate_schema_loader():
    """Validate schema loader functionality"""
    print("📋 Validating schema loader...")
    
    try:
        loader = FocusSchemaLoader()
        
        # Test available datasets
        datasets = loader.get_available_datasets()
        assert 'cost_and_usage' in datasets
        assert 'contract_commitment' in datasets
        # Test loading a dataset schema
        cost_usage_schema = loader.load_dataset_schema('cost_and_usage')
        assert cost_usage_schema.name == 'cost_and_usage'
        assert cost_usage_schema.table_name == FocusTableNames.COST_USAGE
        assert len(cost_usage_schema.columns) > 0
        
        print("✓ Schema loader validation passed")
    except Exception as e:
        print(f"❌ Schema loader validation failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def validate_directory_structure():
    """Validate directory structure"""
    print("📁 Validating directory structure...")
    
    base_path = Path(__file__).parent
    
    required_dirs = [
        'interfaces',
        'utils', 
        'schema',
        'tests'
    ]
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        assert dir_path.exists(), f"Required directory missing: {dir_name}"
        
        # Check for __init__.py
        init_file = dir_path / '__init__.py'
        assert init_file.exists(), f"Missing __init__.py in {dir_name}"
    
    print("✓ Directory structure validation passed")


def main():
    """Run all validations"""
    print("🚀 Starting FOCUS billing module validation...\n")
    
    try:
        validate_configuration()
        validate_data_models()
        validate_utilities()
        validate_constants()
        validate_schema_loader()
        validate_directory_structure()
        
        print("\n🎉 All validations passed! FOCUS billing module is properly set up.")
        return True
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)