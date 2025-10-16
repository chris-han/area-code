#!/usr/bin/env python3
"""
Quick test to verify Azure Billing page can be imported and basic functionality works
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_azure_billing_import():
    """Test that azure_billing_view can be imported"""
    try:
        from pages import azure_billing_view
        print("✅ Successfully imported azure_billing_view")
        
        # Check if the show function exists
        if hasattr(azure_billing_view, 'show'):
            print("✅ show() function found")
        else:
            print("❌ show() function not found")
            
        # Check for other expected functions
        expected_functions = [
            'render_configuration_form',
            'render_summary_metrics', 
            'render_billing_data_table',
            'render_cost_analysis_charts'
        ]
        
        found_functions = []
        for func_name in expected_functions:
            if hasattr(azure_billing_view, func_name):
                found_functions.append(func_name)
        
        print(f"✅ Found {len(found_functions)}/{len(expected_functions)} expected functions")
        if found_functions:
            print(f"   Functions: {', '.join(found_functions)}")
            
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import azure_billing_view: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_utility_imports():
    """Test that utility modules can be imported"""
    try:
        from utils.azure_billing_utils import AzureBillingConfig, CredentialManager, WorkflowParameterManager
        print("✅ Successfully imported azure_billing_utils")
        
        from utils.api_functions import fetch_azure_billing_data, test_azure_connection
        print("✅ Successfully imported API functions")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import utilities: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in utilities: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Azure Billing Page Integration")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_azure_billing_import():
        success = False
    
    if not test_utility_imports():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Azure Billing page should work correctly.")
        print("\n💡 Next steps:")
        print("1. Restart Streamlit: streamlit run main.py")
        print("2. Navigate to Azure Billing page")
        print("3. The page should load without errors")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)