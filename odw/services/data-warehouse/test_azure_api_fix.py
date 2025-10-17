#!/usr/bin/env python3
"""
Test script to verify Azure EA API connection with the correct credentials and endpoint format.
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Real Azure credentials from the test file
AZURE_CONFIG = {
    "enrollment_number": "V5702303S0121",
    "api_key": "eyJhbGciOiJSUzI1NiIsImtpZCI6IkY0QzA3NjhGOEJCOURBMjRGQzY5QUMzQjc5NTZDMDNDRjMxRjc3ODIiLCJ0eXAiOiJKV1QifQ.eyJFbnJvbGxtZW50TnVtYmVyIjoiVjU3MDIzMDNTMDEyMSIsIklkIjoiMzEwZTM1YmYtYmU2Yi00MDQwLThjYzUtYzY2YmY2N2RhZmI2IiwiUmVwb3J0VmlldyI6IlBhcnRuZXIiLCJQYXJ0bmVySWQiOiI1MDEwIiwiRGVwYXJ0bWVudElkIjoiIiwiQWNjb3VudElkIjoiIiwibmJmIjoxNzUxOTY5MzE1LCJleHAiOjE3Njc4NjY5MTUsImlhdCI6MTc1MTk2OTMxNSwiaXNzIjoiZWEubWljcm9zb2Z0YXp1cmUuY29tIiwiYXVkIjoiY2xpZW50LmVhLm1pY3Jvc29mdGF6dXJlLmNvbSJ9.KCooPKpK4zskNxCldzDK5A3oX-Z3Y1Jicl8SyVeixHT71cfRa2SgW3UZoT0g0c3vqtxtCQ-wn4vfkeBNuhSKwUNn76Eiqw-SU9hEXWw0ez62u-CraEfa15Wi5woUVKkZCSkkxqyGGCFX0bLXvSg5bPvRd0ENXGi0zfMG-DCh63GUVRhVvcX3kPACz5KkHZtxLvOGP9Q2hcS0HVFOt-d3DpL2x_ut6p0JBQ4ECWh_Lj4ph5FE0GtFXzsN2TGRW9zRM7JFI8WKgDlmLGQeH9e0HEU1AUj-5y4UwgShosYeQueShoHS3ejWsNdBrb83B7VD8kQp5mYs9ATZGuH7YO-Ucw",
    "base_url": "https://ea.azure.cn/rest"
}

def test_api_endpoints():
    """Test different Azure EA API endpoints to find the working one."""
    
    headers = {
        'Authorization': f'bearer {AZURE_CONFIG["api_key"]}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Test different months and endpoint formats
    test_months = ["2025-09", "2025-08", "2024-12", "2024-01"]
    
    print("🔍 Testing Azure EA API Endpoints")
    print("=" * 50)
    
    for month in test_months:
        print(f"\n📅 Testing month: {month}")
        
        # Test 1: Original billingPeriods endpoint (the one that's failing)
        url1 = f"{AZURE_CONFIG['base_url']}/{AZURE_CONFIG['enrollment_number']}/billingPeriods/{month}/usagedetails"
        print(f"🔗 Testing: {url1}")
        
        try:
            response = requests.get(url1, headers=headers, timeout=30)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success! Found {len(data.get('value', []))} records")
                break
            elif response.status_code == 404:
                print(f"   ❌ 404 Not Found - billing period may not exist")
            else:
                print(f"   ⚠️  Error: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        # Test 2: Paginated V3 endpoint (newer format)
        url2 = f"{AZURE_CONFIG['base_url']}/{AZURE_CONFIG['enrollment_number']}/usage-report/paginatedV3?month={month}&pageindex=0&fmt=json"
        print(f"🔗 Testing: {url2}")
        
        try:
            response = requests.get(url2, headers=headers, timeout=30)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                records = data.get('data', [])
                print(f"   ✅ Success! Found {len(records)} records")
                if records:
                    print(f"   📊 Sample record keys: {list(records[0].keys())[:5]}")
                break
            elif response.status_code == 404:
                print(f"   ❌ 404 Not Found - month may not have data")
            else:
                print(f"   ⚠️  Error: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        # Test 3: Simple usage report endpoint
        url3 = f"{AZURE_CONFIG['base_url']}/{AZURE_CONFIG['enrollment_number']}/usage-report?month={month}"
        print(f"🔗 Testing: {url3}")
        
        try:
            response = requests.get(url3, headers=headers, timeout=30)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Success! Response length: {len(response.text)}")
                break
            elif response.status_code == 404:
                print(f"   ❌ 404 Not Found")
            else:
                print(f"   ⚠️  Error: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")

def test_enrollment_info():
    """Test basic enrollment information endpoint."""
    
    headers = {
        'Authorization': f'bearer {AZURE_CONFIG["api_key"]}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print("\n🏢 Testing Enrollment Information")
    print("=" * 50)
    
    # Test enrollment details
    url = f"{AZURE_CONFIG['base_url']}/{AZURE_CONFIG['enrollment_number']}"
    print(f"🔗 Testing: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Enrollment information retrieved successfully!")
            print(f"📋 Response keys: {list(data.keys())}")
        else:
            print(f"❌ Error: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def main():
    """Main test function."""
    print("🚀 Azure EA API Connection Test")
    print("Testing with real credentials from the working test file")
    print(f"Enrollment: {AZURE_CONFIG['enrollment_number']}")
    print(f"API Key: {AZURE_CONFIG['api_key'][:50]}...")
    print(f"Base URL: {AZURE_CONFIG['base_url']}")
    
    # Test enrollment info first
    test_enrollment_info()
    
    # Test different API endpoints
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("🎯 Recommendations:")
    print("1. If paginatedV3 endpoint works, update the connector to use it")
    print("2. If no recent months have data, try older months")
    print("3. Check if the enrollment has billing data for the requested periods")
    print("4. Verify the API token hasn't expired (current token expires Jan 2026)")

if __name__ == "__main__":
    main()