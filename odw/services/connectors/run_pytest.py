#!/usr/bin/env python3
"""
Pytest Runner for Azure Billing Connector Tests

This script provides a simple way to run pytest tests with proper configuration
for VS Code test discovery and execution.
"""

import sys
import os
import subprocess
from typing import List, Optional


def run_pytest(args: Optional[List[str]] = None) -> int:
    """Run pytest with appropriate configuration"""
    
    # Default pytest arguments
    default_args = [
        "--verbose",
        "--tb=short",
        "--color=yes",
        "--strict-markers",
        "--strict-config"
    ]
    
    # Add custom arguments if provided
    if args:
        pytest_args = default_args + args
    else:
        pytest_args = default_args + ["tests/"]
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join([
        os.path.join(os.getcwd(), 'src'),
        os.getcwd(),
        env.get('PYTHONPATH', '')
    ])
    env['TEST_MODE'] = 'true'
    
    # Run pytest
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest"] + pytest_args,
            env=env,
            cwd=os.getcwd()
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 130
    except Exception as e:
        print(f"Error running pytest: {e}")
        return 1


def main():
    """Main entry point"""
    # Parse command line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    
    # Run pytest
    exit_code = run_pytest(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()