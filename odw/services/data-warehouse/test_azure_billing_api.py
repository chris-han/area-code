#!/usr/bin/env python3
"""
Azure Billing API Test Script

This script tests the Azure billing API endpoints using the provided configuration.
It tests both the connection test endpoint and the data extraction functionality.
"""

import requests
import json
import time
from datetime import datetime, date, timedelta
from typing import Dict, Any

# Azure Configuration
AZURE_CONFIG = {
    "azure_enrollment_number": "V5702303S0121",
    "azure_api_key": "eyJhbGciOiJSUzI1NiIsImtpZCI6IkY0QzA3NjhGOEJCOURBMjRGQzY5QUMzQjc5NTZDMDNDRjMxRjc3ODIiLCJ0eXAiOiJKV1QifQ.eyJFbnJvbGxtZW50TnVtYmVyIjoiVjU3MDIzMDNTMDEyMSIsIklkIjoiMzEwZTM1YmYtYmU2Yi00MDQwLThjYzUtYzY2YmY2N2RhZmI2IiwiUmVwb3J0VmlldyI6IlBhcnRuZXIiLCJQYXJ0bmVySWQiOiI1MDEwIiwiRGVwYXJ0bWVudElkIjoiIiwiQWNjb3VudElkIjoiIiwibmJmIjoxNzUxOTY5MzE1LCJleHAiOjE3Njc4NjY5MTUsImlhdCI6MTc1MTk2OTMxNSwiaXNzIjoiZWEubWljcm9zb2Z0YXp1cmUuY29tIiwiYXVkIjoiY2xpZW50LmVhLm1pY3Jvc29mdGF6dXJlLmNvbSJ9.KCooPKpK4zskNxCldzDK5A3oX-Z3Y1Jicl8SyVeixHT71cfRa2SgW3UZoT0g0c3vqtxtCQ-wn4vfkeBNuhSKwUNn76Eiqw-SU9hEXWw0ez62u-CraEfa15Wi5woUVKkZCSkkxqyGGCFX0bLXvSg5bPvRd0ENXGi0zfMG-DCh63GUVRhVvcX3kPACz5KkHZtxLvOGP9Q2hcS0HVFOt-d3DpL2x_ut6p0JBQ4ECWh_Lj4ph5FE0GtFXzsN2TGRW9zRM7JFI8WKgDlmLGQeH9e0HEU1AUj-5y4UwgShosYeQueShoHS3ejWsNdBrb83B7VD8kQp5mYs9ATZGuH7YO-Ucw",
}

# API Base URL
API_BASE_URL = "http://localhost:4200/consumption"


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_result(success: bool, message: str, details: Dict[str, Any] = None):
    """Print formatted test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"Details: {json.dumps(details, indent=2)}")
    print("-" * 60)


def test_azure_connection():
    """Test the Azure connection endpoint"""
    print_header("Testing Azure Connection")

    url = f"{API_BASE_URL}/test-azure-connection"
    payload = {
        "enrollment_number": AZURE_CONFIG["azure_enrollment_number"],
        "api_key": AZURE_CONFIG["azure_api_key"],
    }

    print(f"URL: {url}")
    print(
        f"Payload: {{'enrollment_number': '{payload['enrollment_number']}', 'api_key': '{payload['api_key'][:20]}...'}}"
    )

    try:
        start_time = time.time()
        # Try GET request with query parameters (Moose consumption API pattern)
        response = requests.get(
            url, params=payload, timeout=180
        )  # Increased timeout to 3 minutes
        end_time = time.time()

        print(f"Response Time: {(end_time - start_time):.2f} seconds")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_result(
                success=data.get("success", False),
                message=data.get("message", "No message"),
                details={
                    "status_code": data.get("status_code"),
                    "response_time_ms": data.get("response_time_ms"),
                },
            )
            return data.get("success", False)
        else:
            print_result(
                success=False,
                message=f"HTTP {response.status_code}: {response.text}",
                details={"headers": dict(response.headers)},
            )
            return False

    except Exception as e:
        print_result(success=False, message=f"Connection error: {str(e)}")
        return False


def test_azure_billing_extract():
    """Test the Azure billing extract endpoint"""
    print_header("Testing Azure Billing Extract")

    url = f"{API_BASE_URL}/extract-azure-billing"

    # Use a very short date range (just 3 days) to minimize processing time
    today = date.today()
    start_date = today - timedelta(days=3)
    end_date = today - timedelta(days=1)

    payload = {
        "batch_size": 100,  # Smaller batch size
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "azure_enrollment_number": AZURE_CONFIG["azure_enrollment_number"],
        "azure_api_key": AZURE_CONFIG["azure_api_key"],
    }

    print(f"URL: {url}")
    print(f"Date Range: {payload['start_date']} to {payload['end_date']}")
    print(f"Batch Size: {payload['batch_size']}")

    try:
        start_time = time.time()
        # Use GET request with query parameters (Moose consumption API pattern)
        response = requests.get(
            url, params=payload, timeout=180
        )  # Increased timeout to 3 minutes
        end_time = time.time()

        print(f"Response Time: {(end_time - start_time):.2f} seconds")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_result(
                success=True,
                message=data.get("message", "Extract triggered successfully"),
                details={
                    "workflow_id": data.get("workflow_id"),
                    "status": data.get("status"),
                },
            )
            return True
        else:
            print_result(
                success=False,
                message=f"HTTP {response.status_code}: {response.text}",
                details={"headers": dict(response.headers)},
            )
            return False

    except Exception as e:
        print_result(success=False, message=f"Extract error: {str(e)}")
        return False


def test_azure_billing_summary():
    """Test the Azure billing summary endpoint"""
    print_header("Testing Azure Billing Summary")

    url = f"{API_BASE_URL}/getAzureBillingSummary"

    try:
        start_time = time.time()
        response = requests.get(url, timeout=30)
        end_time = time.time()

        print(f"URL: {url}")
        print(f"Response Time: {(end_time - start_time):.2f} seconds")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_result(
                success=True,
                message="Summary data retrieved successfully",
                details=data,
            )
            return True
        else:
            print_result(
                success=False, message=f"HTTP {response.status_code}: {response.text}"
            )
            return False

    except Exception as e:
        print_result(success=False, message=f"Summary error: {str(e)}")
        return False


def test_azure_subscriptions():
    """Test the Azure subscriptions endpoint"""
    print_header("Testing Azure Subscriptions")

    url = f"{API_BASE_URL}/getAzureSubscriptions"

    try:
        start_time = time.time()
        response = requests.get(url, timeout=30)
        end_time = time.time()

        print(f"URL: {url}")
        print(f"Response Time: {(end_time - start_time):.2f} seconds")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_result(
                success=True,
                message=f"Retrieved {data.get('total', 0)} subscriptions",
                details={
                    "total": data.get("total", 0),
                    "sample_items": data.get("items", [])[:3],  # Show first 3 items
                },
            )
            return True
        else:
            print_result(
                success=False, message=f"HTTP {response.status_code}: {response.text}"
            )
            return False

    except Exception as e:
        print_result(success=False, message=f"Subscriptions error: {str(e)}")
        return False


def test_azure_resource_groups():
    """Test the Azure resource groups endpoint"""
    print_header("Testing Azure Resource Groups")

    url = f"{API_BASE_URL}/getAzureResourceGroups"

    try:
        start_time = time.time()
        response = requests.get(url, timeout=30)
        end_time = time.time()

        print(f"URL: {url}")
        print(f"Response Time: {(end_time - start_time):.2f} seconds")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_result(
                success=True,
                message=f"Retrieved {data.get('total', 0)} resource groups",
                details={
                    "total": data.get("total", 0),
                    "sample_items": data.get("items", [])[:3],  # Show first 3 items
                },
            )
            return True
        else:
            print_result(
                success=False, message=f"HTTP {response.status_code}: {response.text}"
            )
            return False

    except Exception as e:
        print_result(success=False, message=f"Resource groups error: {str(e)}")
        return False


def test_azure_billing_data():
    """Test the Azure billing data endpoint"""
    print_header("Testing Azure Billing Data")

    url = f"{API_BASE_URL}/getAzureBilling?limit=10"

    try:
        start_time = time.time()
        response = requests.get(url, timeout=30)
        end_time = time.time()

        print(f"URL: {url}")
        print(f"Response Time: {(end_time - start_time):.2f} seconds")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_result(
                success=True,
                message=f"Retrieved {data.get('total', 0)} billing records",
                details={
                    "total": data.get("total", 0),
                    "sample_record": (
                        data.get("items", [{}])[0] if data.get("items") else None
                    ),
                },
            )
            return True
        else:
            print_result(
                success=False, message=f"HTTP {response.status_code}: {response.text}"
            )
            return False

    except Exception as e:
        print_result(success=False, message=f"Billing data error: {str(e)}")
        return False


def test_direct_azure_api():
    """Test direct Azure EA API connection (bypass our API)"""
    print_header("Testing Direct Azure EA API")

    # Test with a recent month that should have data
    test_month = "2025-09"  # Use a fixed month that we know has data
    url = f"https://ea.azure.cn/rest/{AZURE_CONFIG['azure_enrollment_number']}/usage-report/paginatedV3?month={test_month}&pageindex=0&fmt=json"

    headers = {
        "Authorization": f'bearer {AZURE_CONFIG["azure_api_key"]}',
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    print(f"URL: {url}")
    print(f"Month: {test_month}")

    try:
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=60)
        end_time = time.time()

        print(f"Response Time: {(end_time - start_time):.2f} seconds")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            content = data.get("content", [])
            print_result(
                success=True,
                message=f"Direct Azure API connection successful",
                details={
                    "records_count": len(content),
                    "has_next_link": bool(data.get("nextLink")),
                    "sample_record_keys": list(content[0].keys()) if content else [],
                },
            )
            return True
        else:
            print_result(
                success=False,
                message=f"Direct Azure API failed: HTTP {response.status_code}",
                details={"response_text": response.text[:200]},
            )
            return False

    except Exception as e:
        print_result(success=False, message=f"Direct Azure API error: {str(e)}")
        return False


def main():
    """Run all API tests"""
    print_header("Azure Billing API Test Suite")
    print(f"Testing against: {API_BASE_URL}")
    print(f"Enrollment Number: {AZURE_CONFIG['azure_enrollment_number']}")
    print(f"API Key: {AZURE_CONFIG['azure_api_key'][:20]}...")

    # Track test results
    results = {}

    # Test 1: Direct Azure API (to verify credentials work)
    results["direct_azure"] = test_direct_azure_api()

    # Test 2: Connection test endpoint
    results["connection_test"] = test_azure_connection()

    # Test 3: Billing extract endpoint
    results["extract"] = test_azure_billing_extract()

    # Test 4: Summary endpoint
    results["summary"] = test_azure_billing_summary()

    # Test 5: Subscriptions endpoint
    results["subscriptions"] = test_azure_subscriptions()

    # Test 6: Resource groups endpoint
    results["resource_groups"] = test_azure_resource_groups()

    # Test 7: Billing data endpoint
    results["billing_data"] = test_azure_billing_data()

    # Summary
    print_header("Test Results Summary")
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name.replace('_', ' ').title()}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Azure billing API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
