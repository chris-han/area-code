#!/usr/bin/env python3
"""
Test runner for Azure Billing Connector

This script runs the Azure billing connector tests with proper module imports.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the test
if __name__ == "__main__":
    from tests.test_azure_only import main
    success = main()
    sys.exit(0 if success else 1)