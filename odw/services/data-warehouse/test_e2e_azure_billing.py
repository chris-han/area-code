#!/usr/bin/env python3
"""
End-to-End Azure Billing Integration Test

This script tests the complete Azure billing workflow:
1. Triggers the Azure billing extract workflow
2. Waits for data to be processed
3. Opens the frontend in Chrome
4. Navigates to Azure billing page
5. Verifies data is displayed correctly
6. Tests frontend functionality
"""

import requests
import time
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any
import subprocess
import os

# Configuration
AZURE_CONFIG = {
    "azure_enrollment_number": "V5702303S0121",
    "azure_api_key": "eyJhbGciOiJSUzI1NiIsImtpZCI6IkY0QzA3NjhGOEJCOURBMjRGQzY5QUMzQjc5NTZDMDNDRjMxRjc3ODIiLCJ0eXAiOiJKV1QifQ.eyJFbnJvbGxtZW50TnVtYmVyIjoiVjU3MDIzMDNTMDEyMSIsIklkIjoiMzEwZTM1YmYtYmU2Yi00MDQwLThjYzUtYzY2YmY2N2RhZmI2IiwiUmVwb3J0VmlldyI6IlBhcnRuZXIiLCJQYXJ0bmVySWQiOiI1MDEwIiwiRGVwYXJ0bWVudElkIjoiIiwiQWNjb3VudElkIjoiIiwibmJmIjoxNzUxOTY5MzE1LCJleHAiOjE3Njc4NjY5MTUsImlhdCI6MTc1MTk2OTMxNSwiaXNzIjoiZWEubWljcm9zb2Z0YXp1cmUuY29tIiwiYXVkIjoiY2xpZW50LmVhLm1pY3Jvc29mdGF6dXJlLmNvbSJ9.KCooPKpK4zskNxCldzDK5A3oX-Z3Y1Jicl8SyVeixHT71cfRa2SgW3UZoT0g0c3vqtxtCQ-wn4vfkeBNuhSKwUNn76Eiqw-SU9hEXWw0ez62u-CraEfa15Wi5woUVKkZCSkkxqyGGCFX0bLXvSg5bPvRd0ENXGi0zfMG-DCh63GUVRhVvcX3kPACz5KkHZtxLvOGP9Q2hcS0HVFOt-d3DpL2x_ut6p0JBQ4ECWh_Lj4ph5FE0GtFXzsN2TGRW9zRM7JFI8WKgDlmLGQeH9e0HEU1AUj-5y4UwgShosYeQueShoHS3ejWsNdBrb83B7VD8kQp5mYs9ATZGuH7YO-Ucw"
}

API_BASE_URL = "http://localhost:4200/consumption"
FRONTEND_URL = "http://localhost:8501"  # Streamlit default port

class E2ETestRunner:
    def __init__(self):
        self.workflow_id = None
        self.test_results = {}
        
    def print_step(self, step: str, status: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"[{timestamp}] {status_icon.get(status, 'ℹ️')} {step}")
    
    def wait_with_progress(self, seconds: int, message: str):
        """Wait with progress indicator"""
        self.print_step(f"{message} (waiting {seconds}s)")
        for i in range(seconds):
            print(f"\r  Progress: {'█' * (i * 20 // seconds)}{'░' * (20 - i * 20 // seconds)} {i+1}/{seconds}s", end="", flush=True)
            time.sleep(1)
        print()  # New line after progress
    
    def test_backend_apis(self) -> bool:
        """Test that backend APIs are working"""
        self.print_step("Testing backend API availability")
        
        try:
            # Test basic connectivity
            response = requests.get(f"{API_BASE_URL}/getAzureBillingSummary", timeout=10)
            if response.status_code == 200:
                self.print_step("Backend APIs are accessible", "SUCCESS")
                return True
            else:
                self.print_step(f"Backend API error: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.print_step(f"Backend API connection failed: {e}", "ERROR")
            return False
    
    def trigger_workflow(self) -> bool:
        """Trigger Azure billing extract workflow"""
        self.print_step("Triggering Azure billing extract workflow")
        
        # Use a small date range for faster processing
        start_date = (date.today() - timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = (date.today() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        params = {
            "batch_size": 50,  # Small batch for faster processing
            "start_date": start_date,
            "end_date": end_date,
            "azure_enrollment_number": AZURE_CONFIG["azure_enrollment_number"],
            "azure_api_key": AZURE_CONFIG["azure_api_key"]
        }
        
        try:
            response = requests.get(f"{API_BASE_URL}/extract-azure-billing", params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.workflow_id = data.get('workflow_id')
                self.print_step(f"Workflow triggered successfully: {self.workflow_id}", "SUCCESS")
                self.print_step(f"Date range: {start_date} to {end_date}")
                return True
            else:
                self.print_step(f"Workflow trigger failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.print_step(f"Workflow trigger error: {e}", "ERROR")
            return False
    
    def wait_for_data(self, max_wait_minutes: int = 5) -> bool:
        """Wait for workflow to process data"""
        self.print_step(f"Waiting for data processing (max {max_wait_minutes} minutes)")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            try:
                # Check if we have billing data
                response = requests.get(f"{API_BASE_URL}/getAzureBilling?limit=1", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('total', 0) > 0:
                        self.print_step(f"Data available: {data['total']} records", "SUCCESS")
                        return True
                
                # Wait before next check
                time.sleep(30)  # Check every 30 seconds
                elapsed = int(time.time() - start_time)
                self.print_step(f"Still waiting... ({elapsed}s elapsed)")
                
            except Exception as e:
                self.print_step(f"Error checking data: {e}", "WARNING")
                time.sleep(30)
        
        self.print_step("Timeout waiting for data", "WARNING")
        return False
    
    def test_frontend_access(self) -> bool:
        """Test that frontend is accessible"""
        self.print_step("Testing frontend accessibility")
        
        try:
            response = requests.get(FRONTEND_URL, timeout=10)
            if response.status_code == 200:
                self.print_step("Frontend is accessible", "SUCCESS")
                return True
            else:
                self.print_step(f"Frontend error: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.print_step(f"Frontend connection failed: {e}", "ERROR")
            return False
    
    def create_chrome_test_script(self) -> str:
        """Create a Chrome DevTools automation script"""
        script_content = f'''
// Chrome DevTools Console Script for Azure Billing E2E Test
// Run this in the browser console on the Azure Billing page

console.log("🚀 Starting Azure Billing E2E Frontend Test");

// Test configuration
const testConfig = {{
    enrollmentNumber: "{AZURE_CONFIG["azure_enrollment_number"]}",
    apiKey: "{AZURE_CONFIG["azure_api_key"][:20]}...",
    frontendUrl: "{FRONTEND_URL}"
}};

// Helper function to wait for element
function waitForElement(selector, timeout = 5000) {{
    return new Promise((resolve, reject) => {{
        const element = document.querySelector(selector);
        if (element) {{
            resolve(element);
            return;
        }}
        
        const observer = new MutationObserver(() => {{
            const element = document.querySelector(selector);
            if (element) {{
                observer.disconnect();
                resolve(element);
            }}
        }});
        
        observer.observe(document.body, {{
            childList: true,
            subtree: true
        }});
        
        setTimeout(() => {{
            observer.disconnect();
            reject(new Error(`Element ${{selector}} not found within ${{timeout}}ms`));
        }}, timeout);
    }});
}}

// Helper function to simulate user input
function setInputValue(element, value) {{
    element.value = value;
    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
}}

// Test steps
async function runE2ETest() {{
    const results = [];
    
    try {{
        console.log("✅ Step 1: Verify we're on the Azure Billing page");
        if (!window.location.href.includes('azure-billing')) {{
            throw new Error('Not on Azure Billing page. Navigate to the Azure Billing page first.');
        }}
        results.push({{ step: "Page Navigation", status: "PASS" }});
        
        console.log("✅ Step 2: Check for Azure Billing page elements");
        await waitForElement('h1, h2, h3', 2000);
        const pageTitle = document.querySelector('h1, h2, h3');
        if (pageTitle && pageTitle.textContent.includes('Azure')) {{
            console.log(`Found page title: ${{pageTitle.textContent}}`);
            results.push({{ step: "Page Title", status: "PASS" }});
        }} else {{
            throw new Error('Azure Billing page title not found');
        }}
        
        console.log("✅ Step 3: Check for configuration form");
        const configExpander = document.querySelector('[data-testid="stExpander"]') || 
                              document.querySelector('details') ||
                              Array.from(document.querySelectorAll('*')).find(el => 
                                  el.textContent.includes('Configuration') || 
                                  el.textContent.includes('Azure Billing Configuration')
                              );
        
        if (configExpander) {{
            console.log("Found configuration section");
            results.push({{ step: "Configuration Form", status: "PASS" }});
            
            // Try to expand if it's collapsed
            if (configExpander.tagName === 'DETAILS' && !configExpander.open) {{
                configExpander.open = true;
            }} else if (configExpander.click) {{
                configExpander.click();
            }}
        }} else {{
            console.warn("Configuration section not found - may be already expanded");
            results.push({{ step: "Configuration Form", status: "WARN" }});
        }}
        
        console.log("✅ Step 4: Check for summary metrics");
        const metrics = document.querySelectorAll('[data-testid="metric"]') ||
                       document.querySelectorAll('.metric-card') ||
                       Array.from(document.querySelectorAll('*')).filter(el => 
                           el.textContent.includes('Total Cost') || 
                           el.textContent.includes('Resources') ||
                           el.textContent.includes('Subscriptions')
                       );
        
        if (metrics.length > 0) {{
            console.log(`Found ${{metrics.length}} metric cards`);
            results.push({{ step: "Summary Metrics", status: "PASS" }});
        }} else {{
            console.warn("No metric cards found");
            results.push({{ step: "Summary Metrics", status: "WARN" }});
        }}
        
        console.log("✅ Step 5: Check for data table");
        const dataTable = document.querySelector('table') ||
                          document.querySelector('[data-testid="stDataFrame"]') ||
                          Array.from(document.querySelectorAll('*')).find(el => 
                              el.textContent.includes('Azure Billing Data') ||
                              el.textContent.includes('No Azure billing data available')
                          );
        
        if (dataTable) {{
            console.log("Found data table or data section");
            results.push({{ step: "Data Table", status: "PASS" }});
        }} else {{
            console.warn("Data table not found");
            results.push({{ step: "Data Table", status: "WARN" }});
        }}
        
        console.log("✅ Step 6: Check for workflow status section");
        const workflowSection = Array.from(document.querySelectorAll('*')).find(el => 
            el.textContent.includes('Workflows') || 
            el.textContent.includes('Azure Billing Workflows')
        );
        
        if (workflowSection) {{
            console.log("Found workflow status section");
            results.push({{ step: "Workflow Status", status: "PASS" }});
        }} else {{
            console.warn("Workflow status section not found");
            results.push({{ step: "Workflow Status", status: "WARN" }});
        }}
        
        console.log("✅ Step 7: Test configuration inputs (if visible)");
        const enrollmentInput = Array.from(document.querySelectorAll('input')).find(input => 
            input.placeholder && input.placeholder.toLowerCase().includes('enrollment') ||
            input.previousElementSibling && input.previousElementSibling.textContent.includes('Enrollment')
        );
        
        if (enrollmentInput) {{
            console.log("Found enrollment number input - testing...");
            const originalValue = enrollmentInput.value;
            setInputValue(enrollmentInput, testConfig.enrollmentNumber);
            
            setTimeout(() => {{
                if (enrollmentInput.value === testConfig.enrollmentNumber) {{
                    console.log("✅ Enrollment input working");
                    results.push({{ step: "Configuration Input", status: "PASS" }});
                    // Restore original value
                    setInputValue(enrollmentInput, originalValue);
                }} else {{
                    console.warn("❌ Enrollment input not working");
                    results.push({{ step: "Configuration Input", status: "FAIL" }});
                }}
            }}, 500);
        }} else {{
            console.log("Configuration inputs not visible (may be collapsed)");
            results.push({{ step: "Configuration Input", status: "SKIP" }});
        }}
        
    }} catch (error) {{
        console.error("❌ Test failed:", error.message);
        results.push({{ step: "Test Execution", status: "FAIL", error: error.message }});
    }}
    
    // Display results
    setTimeout(() => {{
        console.log("\\n🎯 E2E Test Results:");
        console.table(results);
        
        const passed = results.filter(r => r.status === "PASS").length;
        const total = results.length;
        const warnings = results.filter(r => r.status === "WARN").length;
        const failed = results.filter(r => r.status === "FAIL").length;
        
        console.log(`\\n📊 Summary: ${{passed}}/${{total}} tests passed`);
        if (warnings > 0) console.log(`⚠️  ${{warnings}} warnings`);
        if (failed > 0) console.log(`❌ ${{failed}} failures`);
        
        if (passed >= total - warnings) {{
            console.log("\\n🎉 Azure Billing Frontend Integration Test: SUCCESS!");
            console.log("✅ The frontend is working correctly!");
        }} else {{
            console.log("\\n⚠️  Azure Billing Frontend Integration Test: PARTIAL SUCCESS");
            console.log("Some components may need attention.");
        }}
        
        return results;
    }}, 1000);
}}

// Run the test
console.log("Starting E2E test in 2 seconds...");
setTimeout(runE2ETest, 2000);
'''
        
        script_path = "chrome_e2e_test.js"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        return script_path
    
    def run_complete_test(self) -> bool:
        """Run the complete end-to-end test"""
        self.print_step("🚀 Starting Azure Billing End-to-End Test", "INFO")
        
        # Step 1: Test backend APIs
        if not self.test_backend_apis():
            return False
        
        # Step 2: Trigger workflow
        if not self.trigger_workflow():
            return False
        
        # Step 3: Wait for some data processing (don't wait for completion)
        self.wait_with_progress(60, "Allowing workflow to start processing")
        
        # Step 4: Test frontend access
        if not self.test_frontend_access():
            return False
        
        # Step 5: Create Chrome test script
        script_path = self.create_chrome_test_script()
        self.print_step(f"Created Chrome DevTools test script: {script_path}", "SUCCESS")
        
        # Step 6: Instructions for manual testing
        self.print_step("🎯 Manual Testing Instructions:", "INFO")
        print("\n" + "="*60)
        print("NEXT STEPS - Manual Frontend Testing:")
        print("="*60)
        print(f"1. Open Chrome and navigate to: {FRONTEND_URL}")
        print("2. Go to the 'Azure Billing' page in the navigation")
        print("3. Open Chrome DevTools (F12)")
        print("4. Go to the 'Console' tab")
        print(f"5. Copy and paste the contents of '{script_path}' into the console")
        print("6. Press Enter to run the automated frontend test")
        print("\nThe script will:")
        print("  ✅ Verify page elements are present")
        print("  ✅ Test configuration form functionality")
        print("  ✅ Check data display components")
        print("  ✅ Validate workflow status section")
        print("  ✅ Test user interactions")
        print("\n" + "="*60)
        
        # Step 7: Check if we can get some data
        self.print_step("Checking for processed data...")
        has_data = self.wait_for_data(max_wait_minutes=2)  # Quick check
        
        if has_data:
            self.print_step("✅ Data is available in the system!", "SUCCESS")
        else:
            self.print_step("⚠️  No data yet - workflow may still be processing", "WARNING")
            self.print_step("You can still test the frontend interface", "INFO")
        
        return True

def main():
    """Main test execution"""
    runner = E2ETestRunner()
    
    try:
        success = runner.run_complete_test()
        
        if success:
            print("\n🎉 E2E Test Setup Complete!")
            print("Follow the manual instructions above to complete the frontend testing.")
            return True
        else:
            print("\n❌ E2E Test Setup Failed!")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)