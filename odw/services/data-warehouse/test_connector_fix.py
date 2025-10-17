#!/usr/bin/env python3
"""
Simple test to verify the Azure billing connector works with the updated API client.
"""

import sys
import os
sys.path.append('../../services/connectors/src')

from azure_billing.azure_ea_api_client import AzureEAApiClient
from azure_billing.azure_billing_connector import AzureApiConfig

def test_api_client():
    """Test the updated Azure EA API client."""
    
    print("🔧 Testing Updated Azure EA API Client")
    print("=" * 50)
    
    # Real credentials
    config = AzureApiConfig(
        enrollment_number="V5702303S0121",
        api_key="eyJhbGciOiJSUzI1NiIsImtpZCI6IkY0QzA3NjhGOEJCOURBMjRGQzY5QUMzQjc5NTZDMDNDRjMxRjc3ODIiLCJ0eXAiOiJKV1QifQ.eyJFbnJvbGxtZW50TnVtYmVyIjoiVjU3MDIzMDNTMDEyMSIsIklkIjoiMzEwZTM1YmYtYmU2Yi00MDQwLThjYzUtYzY2YmY2N2RhZmI2IiwiUmVwb3J0VmlldyI6IlBhcnRuZXIiLCJQYXJ0bmVySWQiOiI1MDEwIiwiRGVwYXJ0bWVudElkIjoiIiwiQWNjb3VudElkIjoiIiwibmJmIjoxNzUxOTY5MzE1LCJleHAiOjE3Njc4NjY5MTUsImlhdCI6MTc1MTk2OTMxNSwiaXNzIjoiZWEubWljcm9zb2Z0YXp1cmUuY29tIiwiYXVkIjoiY2xpZW50LmVhLm1pY3Jvc29mdGF6dXJlLmNvbSJ9.KCooPKpK4zskNxCldzDK5A3oX-Z3Y1Jicl8SyVeixHT71cfRa2SgW3UZoT0g0c3vqtxtCQ-wn4vfkeBNuhSKwUNn76Eiqw-SU9hEXWw0ez62u-CraEfa15Wi5woUVKkZCSkkxqyGGCFX0bLXvSg5bPvRd0ENXGi0zfMG-DCh63GUVRhVvcX3kPACz5KkHZtxLvOGP9Q2hcS0HVFOt-d3DpL2x_ut6p0JBQ4ECWh_Lj4ph5FE0GtFXzsN2TGRW9zRM7JFI8WKgDlmLGQeH9e0HEU1AUj-5y4UwgShosYeQueShoHS3ejWsNdBrb83B7VD8kQp5mYs9ATZGuH7YO-Ucw",
        base_url="https://ea.azure.cn/rest"
    )
    
    print(f"Enrollment: {config.enrollment_number}")
    print(f"Base URL: {config.base_url}")
    print(f"API Key: {config.api_key[:50]}...")
    
    # Test URL building
    client = AzureEAApiClient(config)
    
    # Test the new URL format
    test_month = "2025-09"
    url = client.get_billing_data_url(test_month)
    print(f"\n🔗 Generated URL for {test_month}:")
    print(f"   {url}")
    
    expected_url = f"https://ea.azure.cn/rest/V5702303S0121/usage-report/paginatedV3?month={test_month}&pageindex=0&fmt=json"
    if url == expected_url:
        print("   ✅ URL format is correct!")
    else:
        print("   ❌ URL format is incorrect!")
        print(f"   Expected: {expected_url}")
        return False
    
    # Test API call (just first page)
    print(f"\n📡 Testing API call for {test_month}...")
    try:
        records, next_link = client.fetch_billing_data(test_month)
        print(f"   ✅ Success! Retrieved {len(records)} records")
        
        if records:
            sample_record = records[0]
            print(f"   📊 Sample record keys: {list(sample_record.keys())[:8]}...")
            print(f"   💰 Sample cost: {sample_record.get('ExtendedCost', 'N/A')}")
            print(f"   📅 Sample date: {sample_record.get('Date', 'N/A')}")
        
        if next_link:
            print(f"   🔗 Next page available: {next_link[:100]}...")
        else:
            print("   📄 No more pages")
            
        return True
        
    except Exception as e:
        print(f"   ❌ API call failed: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🚀 Azure Billing Connector Fix Test")
    print("Testing the updated API client with real credentials")
    
    try:
        success = test_api_client()
        
        if success:
            print("\n🎉 Test Passed!")
            print("✅ The Azure EA API client has been successfully updated")
            print("✅ The connector should now work with the workflow")
            print("\n📋 Next Steps:")
            print("1. The environment variables have been updated with real credentials")
            print("2. The API client now uses the working paginatedV3 endpoint")
            print("3. The workflow should now succeed when triggered")
            return True
        else:
            print("\n❌ Test Failed!")
            print("The API client still has issues")
            return False
            
    except Exception as e:
        print(f"\n💥 Test Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)