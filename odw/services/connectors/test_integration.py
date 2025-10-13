#!/usr/bin/env python3
"""
Quick integration test to verify the reorganized Azure Billing Connector works with ConnectorFactory
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_connector_factory_integration():
    """Test that ConnectorFactory can create Azure Billing Connector"""
    try:
        from connector_factory import ConnectorFactory, ConnectorType
        from azure_billing import AzureBillingConnectorConfig
        from datetime import datetime
        
        print("✓ Imports successful")
        
        # Create configuration
        config = AzureBillingConnectorConfig(
            azure_enrollment_number="123456789",
            azure_api_key="test-api-key",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            batch_size=100
        )
        print("✓ Configuration created")
        
        # Create connector through factory
        connector = ConnectorFactory.create(ConnectorType.AzureBilling, config)
        print("✓ Connector created through factory")
        
        # Test component initialization
        connector._initialize_components()
        print("✓ Components initialized")
        
        print("\n🎉 Integration test successful!")
        print("The reorganized Azure Billing Connector works correctly with ConnectorFactory")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connector_factory_integration()
    sys.exit(0 if success else 1)