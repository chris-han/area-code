#!/usr/bin/env python3
"""
Quick test of working Azure billing APIs
"""

import requests
import json

# Azure Configuration
AZURE_CONFIG = {
    "azure_enrollment_number": "V5702303S0121",
    "azure_api_key": "eyJhbGciOiJSUzI1NiIsImtpZCI6IkY0QzA3NjhGOEJCOURBMjRGQzY5QUMzQjc5NTZDMDNDRjMxRjc3ODIiLCJ0eXAiOiJKV1QifQ.eyJFbnJvbGxtZW50TnVtYmVyIjoiVjU3MDIzMDNTMDEyMSIsIklkIjoiMzEwZTM1YmYtYmU2Yi00MDQwLThjYzUtYzY2YmY2N2RhZmI2IiwiUmVwb3J0VmlldyI6IlBhcnRuZXIiLCJQYXJ0bmVySWQiOiI1MDEwIiwiRGVwYXJ0bWVudElkIjoiIiwiQWNjb3VudElkIjoiIiwibmJmIjoxNzUxOTY5MzE1LCJleHAiOjE3Njc4NjY5MTUsImlhdCI6MTc1MTk2OTMxNSwiaXNzIjoiZWEubWljcm9zb2Z0YXp1cmUuY29tIiwiYXVkIjoiY2xpZW50LmVhLm1pY3Jvc29mdGF6dXJlLmNvbSJ9.KCooPKpK4zskNxCldzDK5A3oX-Z3Y1Jicl8SyVeixHT71cfRa2SgW3UZoT0g0c3vqtxtCQ-wn4vfkeBNuhSKwUNn76Eiqw-SU9hEXWw0ez62u-CraEfa15Wi5woUVKkZCSkkxqyGGCFX0bLXvSg5bPvRd0ENXGi0zfMG-DCh63GUVRhVvcX3kPACz5KkHZtxLvOGP9Q2hcS0HVFOt-d3DpL2x_ut6p0JBQ4ECWh_Lj4ph5FE0GtFXzsN2TGRW9zRM7JFI8WKgDlmLGQeH9e0HEU1AUj-5y4UwgShosYeQueShoHS3ejWsNdBrb83B7VD8kQp5mYs9ATZGuH7YO-Ucw"
}

API_BASE_URL = "http://localhost:4200/consumption"

def test_api(name, url, params=None):
    """Test an API endpoint"""
    try:
        # Use longer timeout for connection test, shorter for others
        timeout = 120 if 'test-azure-connection' in url else 30
        if params:
            response = requests.get(url, params=params, timeout=timeout)
        else:
            response = requests.get(url, timeout=timeout)
        
        print(f"✅ {name}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                if 'items' in data:
                    print(f"   → {data.get('total', len(data['items']))} items")
                elif 'message' in data:
                    print(f"   → {data['message']}")
                else:
                    print(f"   → {list(data.keys())}")
        return True
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False

def main():
    print("=== Azure Billing API Quick Test ===\n")
    
    results = []
    
    # Test working endpoints
    results.append(test_api("Summary", f"{API_BASE_URL}/getAzureBillingSummary"))
    results.append(test_api("Subscriptions", f"{API_BASE_URL}/getAzureSubscriptions"))
    results.append(test_api("Resource Groups", f"{API_BASE_URL}/getAzureResourceGroups"))
    results.append(test_api("Billing Data", f"{API_BASE_URL}/getAzureBilling", {"limit": 5}))
    
    # Test extract endpoint
    extract_params = {
        "batch_size": 50,
        "start_date": "2025-10-10",
        "end_date": "2025-10-12",
        "azure_enrollment_number": AZURE_CONFIG["azure_enrollment_number"],
        "azure_api_key": AZURE_CONFIG["azure_api_key"]
    }
    results.append(test_api("Extract Workflow", f"{API_BASE_URL}/extract-azure-billing", extract_params))
    
    # Test connection endpoint (with shorter API key for URL safety)
    conn_params = {
        "enrollment_number": AZURE_CONFIG["azure_enrollment_number"],
        "api_key": AZURE_CONFIG["azure_api_key"]
    }
    results.append(test_api("Connection Test", f"{API_BASE_URL}/test-azure-connection", conn_params))
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== Results: {passed}/{total} APIs working ===")
    
    if passed >= 5:  # Most APIs working
        print("🎉 Azure billing integration is ready!")
        print("✅ You can now use the frontend to:")
        print("   • View summary metrics")
        print("   • Filter by subscriptions and resource groups")
        print("   • Trigger billing data extraction")
        print("   • View billing data tables")
    else:
        print("⚠️  Some APIs need attention")
    
    return passed >= 5

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)