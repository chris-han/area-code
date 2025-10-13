#!/usr/bin/env python3
"""
Simple test to verify Azure Billing Connector works in the new structure
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_azure_billing_direct():
    """Test Azure Billing Connector directly without ConnectorFactory"""
    
    try:
        print("Testing direct Azure Billing imports...")
        
        # Test direct imports
        import azure_billing.azure_billing_connector as connector_module
        import azure_billing.azure_ea_api_client as api_module
        import azure_billing.azure_billing_transformer as transformer_module
        import azure_billing.resource_tracking_engine as tracking_module
        import azure_billing.error_handler as error_module
        
        print("✓ All Azure Billing modules imported successfully")
        
        # Test class access
        AzureBillingConnector = connector_module.AzureBillingConnector
        AzureBillingConnectorConfig = connector_module.AzureBillingConnectorConfig
        AzureEAApiClient = api_module.AzureEAApiClient
        AzureBillingTransformer = transformer_module.AzureBillingTransformer
        ResourceTrackingEngine = tracking_module.ResourceTrackingEngine
        ErrorHandler = error_module.ErrorHandler
        
        print("✓ All classes accessible")
        
        # Test configuration creation
        from datetime import datetime
        config = AzureBillingConnectorConfig(
            azure_enrollment_number="123456789",
            azure_api_key="test-api-key",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            batch_size=100
        )
        print("✓ Configuration created successfully")
        
        # Test connector creation
        connector = AzureBillingConnector(config)
        print("✓ Connector created successfully")
        
        # Test component initialization
        connector._initialize_components()
        print("✓ Components initialized successfully")
        
        print("\n🎉 Azure Billing Connector reorganization successful!")
        print("All components work correctly in the new package structure.")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_azure_billing_direct()
    sys.exit(0 if success else 1)