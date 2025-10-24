#!/usr/bin/env python3
"""
Simple validation script to test FOCUS billing API registration
"""

def test_api_imports():
    """Test that all APIs can be imported successfully"""
    try:
        from app.apis.focus_billing.list_use_cases import list_focus_use_cases_api
        print("✓ list_use_cases API imported successfully")
        
        from app.apis.focus_billing.get_use_case import get_focus_use_case_api
        print("✓ get_use_case API imported successfully")
        
        from app.apis.focus_billing.execute_use_case import execute_focus_use_case_api
        print("✓ execute_use_case API imported successfully")
        
        from app.apis.focus_billing.list_supported_features import list_supported_features_api
        print("✓ list_supported_features API imported successfully")
        
        from app.apis.focus_billing.get_supported_feature import get_supported_feature_api
        print("✓ get_supported_feature API imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ API import failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing FOCUS billing API imports...")
    success = test_api_imports()
    if success:
        print("\n✓ All APIs imported successfully!")
    else:
        print("\n✗ Some APIs failed to import")