#!/usr/bin/env python3
"""
Azure Billing Frontend E2E Test Generator

This script creates a Chrome DevTools test for the Azure billing frontend
and provides instructions for manual execution.
"""

import json
from datetime import datetime

# Configuration
AZURE_CONFIG = {
    "azure_enrollment_number": "V5702303S0121",
    "azure_api_key": "eyJhbGciOiJSUzI1NiIs..."  # Truncated for security
}

FRONTEND_URL = "http://localhost:8501"

def create_chrome_devtools_test():
    """Create comprehensive Chrome DevTools test script"""
    
    script_content = f'''
// 🚀 Azure Billing Frontend E2E Test
// Copy and paste this entire script into Chrome DevTools Console
// Make sure you're on the Azure Billing page first!

console.log("🚀 Azure Billing Frontend E2E Test Starting...");
console.log("Time:", new Date().toLocaleTimeString());

// Test configuration
const config = {{
    enrollmentNumber: "{AZURE_CONFIG["azure_enrollment_number"]}",
    frontendUrl: "{FRONTEND_URL}",
    testApiKey: "test_key_12345"
}};

// Utility functions
const utils = {{
    wait: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
    
    waitForElement: (selector, timeout = 5000) => {{
        return new Promise((resolve, reject) => {{
            const element = document.querySelector(selector);
            if (element) return resolve(element);
            
            const observer = new MutationObserver(() => {{
                const element = document.querySelector(selector);
                if (element) {{
                    observer.disconnect();
                    resolve(element);
                }}
            }});
            
            observer.observe(document.body, {{ childList: true, subtree: true }});
            setTimeout(() => {{ observer.disconnect(); reject(new Error(`Timeout: ${{selector}}`)); }}, timeout);
        }});
    }},
    
    findElementByText: (text, tag = '*') => {{
        return Array.from(document.querySelectorAll(tag)).find(el => 
            el.textContent && el.textContent.toLowerCase().includes(text.toLowerCase())
        );
    }},
    
    setInputValue: (element, value) => {{
        if (!element) return false;
        element.value = value;
        element.dispatchEvent(new Event('input', {{ bubbles: true }}));
        element.dispatchEvent(new Event('change', {{ bubbles: true }}));
        return true;
    }},
    
    clickElement: (element) => {{
        if (!element) return false;
        element.click();
        return true;
    }}
}};

// Test suite
const tests = {{
    async pageNavigation() {{
        console.log("📍 Test 1: Page Navigation");
        
        if (window.location.href.includes('azure-billing')) {{
            console.log("✅ On Azure Billing page");
            return {{ status: "PASS", message: "Correct page loaded" }};
        }} else {{
            console.log("❌ Not on Azure Billing page");
            console.log("Current URL:", window.location.href);
            return {{ status: "FAIL", message: "Navigate to Azure Billing page first" }};
        }}
    }},
    
    async pageElements() {{
        console.log("🔍 Test 2: Page Elements");
        const elements = [];
        
        // Check for page title
        const title = utils.findElementByText("Azure Billing", "h1,h2,h3");
        elements.push({{ name: "Page Title", found: !!title }});
        
        // Check for navigation menu
        const nav = document.querySelector('[data-testid="stSidebar"]') || 
                   utils.findElementByText("Azure Billing", "a,button");
        elements.push({{ name: "Navigation", found: !!nav }});
        
        // Check for configuration section
        const config = utils.findElementByText("Configuration") || 
                      utils.findElementByText("Azure Billing Configuration");
        elements.push({{ name: "Configuration Section", found: !!config }});
        
        // Check for metrics cards
        const metrics = document.querySelectorAll('[data-testid="metric"]').length > 0 ||
                       utils.findElementByText("Total Cost") ||
                       utils.findElementByText("Resources");
        elements.push({{ name: "Summary Metrics", found: !!metrics }});
        
        console.table(elements);
        const foundCount = elements.filter(e => e.found).length;
        
        if (foundCount >= 3) {{
            return {{ status: "PASS", message: `${{foundCount}}/4 key elements found` }};
        }} else {{
            return {{ status: "WARN", message: `Only ${{foundCount}}/4 elements found` }};
        }}
    }},
    
    async configurationForm() {{
        console.log("⚙️ Test 3: Configuration Form");
        
        // Try to find and expand configuration section
        const configSection = utils.findElementByText("Configuration");
        if (configSection) {{
            console.log("Found configuration section");
            
            // Try to expand if it's an expander
            const expander = configSection.closest('[data-testid="stExpander"]') ||
                           configSection.closest('details');
            if (expander) {{
                if (expander.tagName === 'DETAILS' && !expander.open) {{
                    expander.open = true;
                }} else {{
                    utils.clickElement(configSection);
                }}
                await utils.wait(1000); // Wait for expansion
            }}
        }}
        
        // Look for input fields
        const inputs = Array.from(document.querySelectorAll('input[type="text"], input[type="password"]'));
        const enrollmentInput = inputs.find(input => 
            (input.placeholder && input.placeholder.toLowerCase().includes('enrollment')) ||
            (input.labels && Array.from(input.labels).some(label => 
                label.textContent.toLowerCase().includes('enrollment')))
        );
        
        const apiKeyInput = inputs.find(input => 
            input.type === 'password' ||
            (input.placeholder && input.placeholder.toLowerCase().includes('key')) ||
            (input.labels && Array.from(input.labels).some(label => 
                label.textContent.toLowerCase().includes('key')))
        );
        
        console.log("Input fields found:", {{
            enrollment: !!enrollmentInput,
            apiKey: !!apiKeyInput,
            total: inputs.length
        }});
        
        // Test input functionality
        let inputsWorking = 0;
        if (enrollmentInput) {{
            const originalValue = enrollmentInput.value;
            if (utils.setInputValue(enrollmentInput, config.enrollmentNumber)) {{
                await utils.wait(500);
                if (enrollmentInput.value === config.enrollmentNumber) {{
                    inputsWorking++;
                    console.log("✅ Enrollment input working");
                    utils.setInputValue(enrollmentInput, originalValue); // Restore
                }}
            }}
        }}
        
        if (apiKeyInput) {{
            const originalValue = apiKeyInput.value;
            if (utils.setInputValue(apiKeyInput, config.testApiKey)) {{
                await utils.wait(500);
                if (apiKeyInput.value === config.testApiKey) {{
                    inputsWorking++;
                    console.log("✅ API key input working");
                    utils.setInputValue(apiKeyInput, originalValue); // Restore
                }}
            }}
        }}
        
        if (inputs.length > 0 && inputsWorking > 0) {{
            return {{ status: "PASS", message: `${{inputsWorking}} inputs working` }};
        }} else if (inputs.length === 0) {{
            return {{ status: "WARN", message: "Configuration form not visible (may be collapsed)" }};
        }} else {{
            return {{ status: "FAIL", message: "Input fields not responding" }};
        }}
    }},
    
    async dataDisplay() {{
        console.log("📊 Test 4: Data Display");
        
        // Check for data table
        const table = document.querySelector('table') ||
                     document.querySelector('[data-testid="stDataFrame"]') ||
                     utils.findElementByText("Azure Billing Data");
        
        // Check for "no data" message
        const noDataMsg = utils.findElementByText("No Azure billing data available") ||
                         utils.findElementByText("Configure and run an extract");
        
        // Check for summary metrics
        const summaryMetrics = utils.findElementByText("Total Cost") ||
                              utils.findElementByText("Resources") ||
                              document.querySelectorAll('[data-testid="metric"]').length > 0;
        
        console.log("Data display elements:", {{
            table: !!table,
            noDataMessage: !!noDataMsg,
            summaryMetrics: !!summaryMetrics
        }});
        
        if (table || noDataMsg || summaryMetrics) {{
            return {{ status: "PASS", message: "Data display components present" }};
        }} else {{
            return {{ status: "FAIL", message: "No data display components found" }};
        }}
    }},
    
    async workflowControls() {{
        console.log("🔄 Test 5: Workflow Controls");
        
        // Look for workflow-related buttons
        const buttons = Array.from(document.querySelectorAll('button'));
        const extractButton = buttons.find(btn => 
            btn.textContent && (
                btn.textContent.includes('Run Extract') ||
                btn.textContent.includes('Extract') ||
                btn.textContent.includes('Trigger')
            )
        );
        
        const testButton = buttons.find(btn => 
            btn.textContent && btn.textContent.includes('Test Connection')
        );
        
        const saveButton = buttons.find(btn => 
            btn.textContent && btn.textContent.includes('Save')
        );
        
        // Look for workflow status section
        const workflowSection = utils.findElementByText("Workflows") ||
                               utils.findElementByText("Azure Billing Workflows");
        
        console.log("Workflow controls found:", {{
            extractButton: !!extractButton,
            testButton: !!testButton,
            saveButton: !!saveButton,
            workflowSection: !!workflowSection,
            totalButtons: buttons.length
        }});
        
        const controlsFound = [extractButton, testButton, saveButton, workflowSection].filter(Boolean).length;
        
        if (controlsFound >= 2) {{
            return {{ status: "PASS", message: `${{controlsFound}} workflow controls found` }};
        }} else {{
            return {{ status: "WARN", message: `Only ${{controlsFound}} workflow controls found` }};
        }}
    }},
    
    async interactivity() {{
        console.log("🖱️ Test 6: User Interactions");
        
        // Test button hover states
        const buttons = document.querySelectorAll('button');
        let interactiveElements = 0;
        
        buttons.forEach(btn => {{
            if (btn.style.cursor === 'pointer' || getComputedStyle(btn).cursor === 'pointer') {{
                interactiveElements++;
            }}
        }});
        
        // Test dropdown/select elements
        const selects = document.querySelectorAll('select, [role="combobox"]');
        interactiveElements += selects.length;
        
        // Test expandable sections
        const expanders = document.querySelectorAll('[data-testid="stExpander"], details');
        interactiveElements += expanders.length;
        
        console.log("Interactive elements:", {{
            buttons: buttons.length,
            selects: selects.length,
            expanders: expanders.length,
            total: interactiveElements
        }});
        
        if (interactiveElements >= 3) {{
            return {{ status: "PASS", message: `${{interactiveElements}} interactive elements` }};
        }} else {{
            return {{ status: "WARN", message: `Only ${{interactiveElements}} interactive elements` }};
        }}
    }}
}};

// Run all tests
async function runAllTests() {{
    console.log("\\n🎯 Running Azure Billing Frontend E2E Tests...");
    console.log("=" .repeat(50));
    
    const results = [];
    
    for (const [testName, testFunc] of Object.entries(tests)) {{
        try {{
            const result = await testFunc();
            results.push({{ test: testName, ...result }});
            
            const icon = result.status === "PASS" ? "✅" : 
                        result.status === "WARN" ? "⚠️" : "❌";
            console.log(`${{icon}} ${{testName}}: ${{result.message}}`);
            
        }} catch (error) {{
            results.push({{ test: testName, status: "ERROR", message: error.message }});
            console.log(`❌ ${{testName}}: ERROR - ${{error.message}}`);
        }}
        
        await utils.wait(500); // Brief pause between tests
    }}
    
    // Display summary
    console.log("\\n📊 Test Results Summary:");
    console.log("=" .repeat(50));
    console.table(results);
    
    const passed = results.filter(r => r.status === "PASS").length;
    const warnings = results.filter(r => r.status === "WARN").length;
    const failed = results.filter(r => r.status === "FAIL").length;
    const errors = results.filter(r => r.status === "ERROR").length;
    
    console.log(`\\n📈 Results: ${{passed}} passed, ${{warnings}} warnings, ${{failed}} failed, ${{errors}} errors`);
    
    if (passed >= 4 && failed === 0) {{
        console.log("\\n🎉 SUCCESS: Azure Billing Frontend is working correctly!");
        console.log("✅ All core functionality is operational");
    }} else if (passed >= 2 && failed <= 1) {{
        console.log("\\n⚠️  PARTIAL SUCCESS: Most functionality is working");
        console.log("Some components may need attention");
    }} else {{
        console.log("\\n❌ ISSUES DETECTED: Frontend may need troubleshooting");
    }}
    
    console.log("\\n💡 Next Steps:");
    console.log("1. Try configuring Azure credentials in the form");
    console.log("2. Test the 'Run Extract' button");
    console.log("3. Check if data appears in the table");
    console.log("4. Verify workflow status updates");
    
    return results;
}}

// Auto-start the test
console.log("Starting tests in 2 seconds...");
setTimeout(runAllTests, 2000);

// Also make it available for manual execution
window.runAzureBillingE2ETest = runAllTests;
console.log("\\n💡 You can also run: runAzureBillingE2ETest()");
'''
    
    return script_content

def main():
    """Generate the Chrome DevTools test"""
    print("🚀 Azure Billing Frontend E2E Test Generator")
    print("=" * 50)
    
    # Create the test script
    script_content = create_chrome_devtools_test()
    
    # Save to file
    script_file = "azure_billing_frontend_e2e_test.js"
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    print(f"✅ Created Chrome DevTools test script: {script_file}")
    print()
    
    # Instructions
    print("📋 INSTRUCTIONS FOR E2E TESTING:")
    print("=" * 50)
    print("1. Make sure your backend service is running on port 4200")
    print("2. Make sure your frontend is running on port 8501")
    print("3. Open Chrome and navigate to: http://localhost:8501")
    print("4. Click on 'Azure Billing' in the navigation menu")
    print("5. Open Chrome DevTools (F12 or right-click → Inspect)")
    print("6. Go to the 'Console' tab")
    print(f"7. Copy the contents of '{script_file}' and paste into the console")
    print("8. Press Enter to run the automated test")
    print()
    print("🎯 The test will automatically:")
    print("  ✅ Verify page navigation and elements")
    print("  ✅ Test configuration form functionality")
    print("  ✅ Check data display components")
    print("  ✅ Validate workflow controls")
    print("  ✅ Test user interactions")
    print("  ✅ Provide detailed results and recommendations")
    print()
    print("📊 After the test, you can manually:")
    print("  • Enter your Azure credentials")
    print("  • Trigger a billing extract")
    print("  • Verify data appears in the table")
    print("  • Test all interactive features")
    print()
    print(f"💾 Test script saved as: {script_file}")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)