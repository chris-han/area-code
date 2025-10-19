#!/usr/bin/env python3
"""
Configuration validation script for ABI development environment.

This script validates that all required environment variables and dependencies
are properly configured for Azure Billing Intelligence development.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import List, Tuple, Dict, Any
import configparser


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_status(message: str):
    print(f"{Colors.BLUE}[ABI-CONFIG]{Colors.NC} {message}")


def print_success(message: str):
    print(f"{Colors.GREEN}[ABI-CONFIG]{Colors.NC} {message}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}[ABI-CONFIG]{Colors.NC} {message}")


def print_error(message: str):
    print(f"{Colors.RED}[ABI-CONFIG]{Colors.NC} {message}")


def check_python_version() -> bool:
    """Check if Python version is >= 3.12"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 12):
        print_error(f"Python {version.major}.{version.minor} is too old (minimum: 3.12)")
        return False
    
    print_success(f"Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_uv_installation() -> bool:
    """Check if UV package manager is installed"""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"UV package manager: {result.stdout.strip()}")
            return True
        else:
            print_error("UV package manager not found")
            return False
    except FileNotFoundError:
        print_error("UV package manager not installed")
        print_status("Install UV: https://docs.astral.sh/uv/getting-started/installation/")
        return False


def check_bun_installation() -> bool:
    """Check if Bun is installed"""
    try:
        result = subprocess.run(['bun', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Bun version: {result.stdout.strip()}")
            return True
        else:
            print_error("Bun not found")
            return False
    except FileNotFoundError:
        print_error("Bun not installed")
        print_status("Install Bun: https://bun.sh/docs/installation")
        return False


def check_docker_installation() -> bool:
    """Check if Docker and Docker Compose are installed"""
    docker_ok = False
    compose_ok = False
    
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker: {result.stdout.strip()}")
            docker_ok = True
        else:
            print_error("Docker not found")
    except FileNotFoundError:
        print_error("Docker not installed")
    
    try:
        result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker Compose: {result.stdout.strip()}")
            compose_ok = True
        else:
            print_error("Docker Compose not found")
    except FileNotFoundError:
        print_error("Docker Compose not installed")
    
    return docker_ok and compose_ok


def check_moose_cli() -> bool:
    """Check if Moose CLI is installed"""
    try:
        result = subprocess.run(['moose-cli', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Moose CLI: {result.stdout.strip()}")
            return True
        else:
            print_error("Moose CLI not found")
            return False
    except FileNotFoundError:
        print_error("Moose CLI not installed")
        return False


def check_env_file() -> Tuple[bool, Dict[str, Any]]:
    """Check if .env file exists and contains required variables"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print_error(".env file not found")
        print_status("Copy env.example to .env and configure your credentials")
        return False, {}
    
    # Load environment variables
    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip('"\'')
    
    required_vars = [
        'AZURE_ENROLLMENT_NUMBER',
        'AZURE_API_KEY',
        'CLICKHOUSE_DB_NAME',
        'CLICKHOUSE_USER',
        'CLICKHOUSE_PASSWORD',
        'CLICKHOUSE_HOST'
    ]
    
    missing_vars = []
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            missing_vars.append(var)
    
    if missing_vars:
        print_error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False, env_vars
    
    print_success(".env file configured with required variables")
    return True, env_vars


def check_moose_config() -> bool:
    """Check if moose.config.toml is properly configured"""
    config_path = Path('moose.config.toml')
    
    if not config_path.exists():
        print_error("moose.config.toml not found")
        return False
    
    try:
        # Simple text-based check for TOML sections
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check for ABI-specific configuration sections
        required_sections = [
            '[data_model]',
            '[plugin_system]',
            '[focus_config]',
            '[datalens_config]'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section.strip('[]'))
        
        if missing_sections:
            print_warning(f"Missing ABI configuration sections: {', '.join(missing_sections)}")
        else:
            print_success("Moose configuration includes ABI sections")
        
        # Check FOCUS specification
        if 'specification = "focus"' in content:
            print_success("FOCUS specification enabled")
        else:
            print_warning("FOCUS specification not configured")
        
        return len(missing_sections) == 0
        
    except Exception as e:
        print_error(f"Error reading moose.config.toml: {e}")
        return False


def check_python_dependencies() -> bool:
    """Check if required Python dependencies are installed"""
    # Use pip list to check installed packages instead of importlib
    try:
        result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            print_error("Failed to get pip package list")
            return False
        
        installed_packages = result.stdout.lower()
        
        required_packages = [
            'fastapi',
            'pydantic', 
            'clickhouse-driver',
            'redis',
            'aiohttp'
        ]
        
        missing_packages = []
        for package in required_packages:
            if package.lower() not in installed_packages:
                missing_packages.append(package)
        
        if missing_packages:
            print_error(f"Missing Python packages: {', '.join(missing_packages)}")
            print_status("Run: uv pip install -e .")
            return False
        
        print_success("All required Python dependencies are installed")
        return True
        
    except Exception as e:
        print_error(f"Error checking Python dependencies: {e}")
        return False


def check_port_availability() -> bool:
    """Check if required ports are available"""
    import socket
    
    required_ports = {
        4200: "Moose API",
        18123: "ClickHouse HTTP",
        9000: "ClickHouse Native",
        7233: "Temporal Server",
        8080: "Temporal UI",
        9999: "Kafdrop UI",
        9500: "MinIO API",
        9501: "MinIO Console",
        6379: "Redis",
        5432: "PostgreSQL",
        19092: "RedPanda"
    }
    
    occupied_ports = []
    for port, service in required_ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            occupied_ports.append(f"{port} ({service})")
    
    if occupied_ports:
        print_warning(f"Ports in use: {', '.join(occupied_ports)}")
        print_status("Some services may already be running")
    else:
        print_success("All required ports are available")
    
    return True


def main():
    """Main validation function"""
    print_status("Validating ABI development environment...")
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("UV Package Manager", check_uv_installation),
        ("Bun Runtime", check_bun_installation),
        ("Docker & Compose", check_docker_installation),
        ("Moose CLI", check_moose_cli),
        ("Environment File", lambda: check_env_file()[0]),
        ("Moose Configuration", check_moose_config),
        ("Python Dependencies", check_python_dependencies),
        ("Port Availability", check_port_availability)
    ]
    
    results = []
    for name, check_func in checks:
        print_status(f"Checking {name}...")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Error checking {name}: {e}")
            results.append((name, False))
        print()
    
    # Summary
    print_status("Validation Summary:")
    print("=" * 50)
    
    passed = 0
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.NC} {name}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print_success("All checks passed! ABI development environment is ready.")
        return 0
    else:
        print_error("Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())