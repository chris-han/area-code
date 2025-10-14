#!/usr/bin/env python3
"""
Setup Test Environment for Azure Billing Connector

This script helps set up the test environment by installing dependencies
and validating the installation.
"""

import sys
import subprocess
import os
import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command: List[str], description: str) -> Tuple[bool, str]:
    """Run a command and return success status and output"""
    try:
        logger.info(f"Running: {description}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr or e.stdout}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def check_python_version() -> bool:
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error(f"Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    
    logger.info(f"Python version: {version.major}.{version.minor}.{version.micro} ✓")
    return True


def install_requirements(requirements_file: str = "requirements.txt") -> bool:
    """Install requirements from file using uv or pip"""
    if not os.path.exists(requirements_file):
        logger.error(f"Requirements file not found: {requirements_file}")
        return False
    
    # Try uv first, fall back to pip
    uv_success, uv_output = run_command(
        ["uv", "pip", "install", "-r", requirements_file],
        f"Installing requirements from {requirements_file} using uv"
    )
    
    if uv_success:
        logger.info("Requirements installed successfully with uv ✓")
        return True
    else:
        logger.warning("uv failed, trying pip...")
        pip_success, pip_output = run_command(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            f"Installing requirements from {requirements_file} using pip"
        )
        
        if pip_success:
            logger.info("Requirements installed successfully with pip ✓")
        else:
            logger.error(f"Failed to install requirements with both uv and pip:")
            logger.error(f"uv error: {uv_output}")
            logger.error(f"pip error: {pip_output}")
        
        return pip_success


def install_development_requirements() -> bool:
    """Install development requirements"""
    if os.path.exists("requirements-dev.txt"):
        return install_requirements("requirements-dev.txt")
    else:
        logger.warning("Development requirements file not found, skipping")
        return True


def validate_installation() -> bool:
    """Validate that key packages are installed"""
    required_packages = [
        "requests",
        "polars", 
        "pydantic",
        "clickhouse_connect",
        "psutil",
        "pytest"
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"Package {package}: ✓")
        except ImportError:
            failed_imports.append(package)
            logger.error(f"Package {package}: ✗")
    
    if failed_imports:
        logger.error(f"Failed to import: {', '.join(failed_imports)}")
        return False
    
    logger.info("All required packages imported successfully ✓")
    return True


def run_test_validation() -> bool:
    """Run the test suite validation"""
    if not os.path.exists("validate_test_suite.py"):
        logger.warning("Test validation script not found, skipping")
        return True
    
    success, output = run_command(
        [sys.executable, "validate_test_suite.py"],
        "Running test suite validation"
    )
    
    if success:
        logger.info("Test suite validation passed ✓")
    else:
        logger.error(f"Test suite validation failed: {output}")
    
    return success


def setup_environment_variables() -> None:
    """Set up environment variables for testing"""
    env_vars = {
        'PYTHONPATH': os.path.join(os.getcwd(), 'src'),
        'TEST_MODE': 'true',
        'LOG_LEVEL': 'INFO'
    }
    
    logger.info("Setting up environment variables:")
    for key, value in env_vars.items():
        os.environ[key] = value
        logger.info(f"  {key}={value}")


def main():
    """Main setup function"""
    logger.info("=" * 60)
    logger.info("AZURE BILLING CONNECTOR - TEST ENVIRONMENT SETUP")
    logger.info("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Set up environment variables
    setup_environment_variables()
    
    # Install requirements
    logger.info("\n📦 Installing Dependencies")
    logger.info("-" * 30)
    
    if not install_requirements():
        logger.error("Failed to install base requirements")
        sys.exit(1)
    
    # Ask user about development requirements
    install_dev = input("\nInstall development requirements? (y/N): ").lower().startswith('y')
    if install_dev:
        if not install_development_requirements():
            logger.warning("Failed to install development requirements, continuing...")
    
    # Validate installation
    logger.info("\n🔍 Validating Installation")
    logger.info("-" * 30)
    
    if not validate_installation():
        logger.error("Package validation failed")
        sys.exit(1)
    
    # Run test validation
    logger.info("\n🧪 Validating Test Suite")
    logger.info("-" * 30)
    
    if not run_test_validation():
        logger.error("Test suite validation failed")
        sys.exit(1)
    
    # Success message
    logger.info("\n🎉 SETUP COMPLETE!")
    logger.info("-" * 30)
    logger.info("The test environment is ready. You can now:")
    logger.info("1. Run test validation: python validate_test_suite.py")
    logger.info("2. Run comprehensive tests: python run_comprehensive_tests.py")
    logger.info("3. Run individual tests: python tests/test_azure_only.py")
    logger.info("")
    logger.info("Next steps:")
    logger.info("- Configure Azure EA API credentials")
    logger.info("- Set up ClickHouse connection for resource tracking")
    logger.info("- Run the full test suite")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nSetup interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        sys.exit(1)