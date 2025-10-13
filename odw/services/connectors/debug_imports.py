#!/usr/bin/env python3
"""
Debug script to identify import issues
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_individual_imports():
    """Test each import individually to identify the issue"""
    
    try:
        print("Testing connector_factory import...")
        from connector_factory import ConnectorFactory, ConnectorType
        print("✓ connector_factory imported successfully")
    except Exception as e:
        print(f"✗ connector_factory import failed: {e}")
        return False
    
    try:
        print("Testing azure_billing.azure_billing_connector import...")
        import azure_billing.azure_billing_connector as connector_module
        print("✓ azure_billing_connector imported successfully")
    except Exception as e:
        print(f"✗ azure_billing_connector import failed: {e}")
        return False
    
    try:
        print("Testing AzureBillingConnectorConfig creation...")
        config_class = connector_module.AzureBillingConnectorConfig
        print("✓ AzureBillingConnectorConfig accessible")
    except Exception as e:
        print(f"✗ AzureBillingConnectorConfig access failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_individual_imports()
    sys.exit(0 if success else 1)