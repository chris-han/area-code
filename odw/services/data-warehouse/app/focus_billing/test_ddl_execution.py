#!/usr/bin/env python3
"""
Test script for FOCUS DDL generation and execution
"""

import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from focus_billing.ddl_generator import generate_all_focus_ddl
from focus_billing.ddl_executor import FocusDDLExecutor
from focus_billing.schema.tables import get_companion_ddl_for_reapplication

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ddl_generation():
    """Test DDL generation"""
    logger.info("Testing DDL generation...")
    
    try:
        ddl_statements = generate_all_focus_ddl()
        
        logger.info(f"Generated {len(ddl_statements)} DDL statements:")
        for name, ddl in ddl_statements.items():
            logger.info(f"- {name}: {len(ddl)} characters")
            
        return True
    except Exception as e:
        logger.error(f"DDL generation failed: {e}")
        return False


def test_ddl_validation():
    """Test DDL validation"""
    logger.info("Testing DDL validation...")
    
    try:
        executor = FocusDDLExecutor()
        ddl_statements = generate_all_focus_ddl()
        
        validation_results = {}
        for name, ddl in ddl_statements.items():
            is_valid = executor.ddl_generator.validate_ddl_syntax(ddl)
            validation_results[name] = is_valid
            logger.info(f"- {name}: {'VALID' if is_valid else 'INVALID'}")
            
        all_valid = all(validation_results.values())
        logger.info(f"All DDL statements valid: {all_valid}")
        
        return all_valid
    except Exception as e:
        logger.error(f"DDL validation failed: {e}")
        return False


def test_companion_ddl():
    """Test companion DDL generation"""
    logger.info("Testing companion DDL generation...")
    
    try:
        companion_ddl = get_companion_ddl_for_reapplication()
        logger.info(f"Generated companion DDL: {len(companion_ddl)} characters")
        
        # Save to file for inspection
        output_path = Path(__file__).parent / "companion_ddl.sql"
        with open(output_path, 'w') as f:
            f.write(companion_ddl)
        
        logger.info(f"Companion DDL saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Companion DDL generation failed: {e}")
        return False


def test_table_verification():
    """Test table verification (without actual execution)"""
    logger.info("Testing table verification...")
    
    try:
        executor = FocusDDLExecutor()
        
        # Test verification methods (they will fail gracefully if tables don't exist)
        tables_to_check = ["focus_cost_usage", "focus_contract_commitment", "focus_ingest_manifest"]
        
        for table_name in tables_to_check:
            exists, schema = executor.verify_table_exists(table_name)
            logger.info(f"- {table_name}: {'EXISTS' if exists else 'NOT FOUND'}")
        
        return True
    except Exception as e:
        logger.error(f"Table verification test failed: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("Starting FOCUS DDL tests...")
    
    tests = [
        ("DDL Generation", test_ddl_generation),
        ("DDL Validation", test_ddl_validation),
        ("Companion DDL", test_companion_ddl),
        ("Table Verification", test_table_verification)
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    logger.info(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())