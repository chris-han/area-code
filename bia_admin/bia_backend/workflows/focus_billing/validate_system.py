#!/usr/bin/env python3
"""
FOCUS Billing System Validation

Standalone script to validate FOCUS billing system configuration,
table existence, data integrity, and performance metrics.
"""

import sys
import argparse
from typing import Dict, Any
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from focus_billing.config import get_focus_config
from focus_billing.observability import focus_observability


def validate_configuration() -> Dict[str, Any]:
    """Validate FOCUS billing configuration"""
    print("=== Configuration Validation ===")
    
    results = {
        'config_valid': True,
        'paths': {},
        'clickhouse': {},
        'errors': []
    }
    
    try:
        # Validate paths
        path_results = get_focus_config().validate_paths()
        results['paths'] = path_results
        
        for path_name, exists in path_results.items():
            status = "✓" if exists else "✗"
            path_value = getattr(focus_config, path_name)
            print(f"{status} {path_name}: {path_value}")
            
            if not exists:
                results['config_valid'] = False
                results['errors'].append(f"Path does not exist: {path_name} = {path_value}")
        
        # Validate ClickHouse connection
        print(f"\n--- ClickHouse Connection ---")
        print(f"Host: {get_focus_config().clickhouse_host}:{get_focus_config().clickhouse_port}")
        print(f"Database: {get_focus_config().clickhouse_database}")
        print(f"User: {get_focus_config().clickhouse_user}")
        print(f"SSL: {get_focus_config().clickhouse_use_ssl}")
        
        ch_connected = get_focus_config().validate_clickhouse_connection()
        results['clickhouse']['connected'] = ch_connected
        
        status = "✓" if ch_connected else "✗"
        print(f"{status} ClickHouse connection: {'Success' if ch_connected else 'Failed'}")
        
        if not ch_connected:
            results['config_valid'] = False
            results['errors'].append("ClickHouse connection failed")
        
        # Validate workflow parameters
        print(f"\n--- Workflow Configuration ---")
        print(f"Batch size: {get_focus_config().batch_size}")
        print(f"Max workers: {get_focus_config().max_workers}")
        print(f"Connection timeout: {get_focus_config().connection_timeout}s")
        print(f"Send/receive timeout: {get_focus_config().send_receive_timeout}s")
        
    except Exception as e:
        results['config_valid'] = False
        results['errors'].append(f"Configuration validation failed: {str(e)}")
        print(f"✗ Configuration validation error: {e}")
    
    return results


def validate_database_schema() -> Dict[str, Any]:
    """Validate database schema and tables"""
    print("\n=== Database Schema Validation ===")
    
    results = {
        'schema_valid': True,
        'tables': {},
        'row_counts': {},
        'errors': []
    }
    
    try:
        # Check required tables exist
        required_tables = [
            get_focus_config().cost_usage_table_name,
            get_focus_config().contract_commitment_table_name,
            get_focus_config().manifest_table_name
        ]
        
        table_results = focus_observability.verify_tables_exist(required_tables)
        results['tables'] = {name: result.passed for name, result in table_results.items()}
        
        for table_name, result in table_results.items():
            status = "✓" if result.passed else "✗"
            print(f"{status} Table exists: {table_name}")
            
            if not result.passed:
                results['schema_valid'] = False
                results['errors'].append(f"Missing table: {table_name}")
        
        # Get row counts for existing tables
        existing_tables = [name for name, result in table_results.items() if result.passed]
        if existing_tables:
            print(f"\n--- Table Row Counts ---")
            row_counts = focus_observability.get_table_row_counts(existing_tables)
            results['row_counts'] = row_counts
            
            for table_name, count in row_counts.items():
                if count >= 0:
                    print(f"{table_name}: {count:,} rows")
                else:
                    print(f"{table_name}: Error getting count")
        
        # Check views exist (if tables exist)
        if results['tables'].get(get_focus_config().cost_usage_table_name, False):
            view_results = focus_observability.verify_tables_exist([
                get_focus_config().cost_usage_view_name,
                get_focus_config().contract_commitment_view_name
            ])
            
            print(f"\n--- Views ---")
            for view_name, result in view_results.items():
                status = "✓" if result.passed else "✗"
                print(f"{status} View exists: {view_name}")
                
                if not result.passed:
                    results['errors'].append(f"Missing view: {view_name}")
    
    except Exception as e:
        results['schema_valid'] = False
        results['errors'].append(f"Schema validation failed: {str(e)}")
        print(f"✗ Schema validation error: {e}")
    
    return results


def validate_data_integrity() -> Dict[str, Any]:
    """Validate data integrity and referential constraints"""
    print("\n=== Data Integrity Validation ===")
    
    results = {
        'integrity_valid': True,
        'checks': {},
        'errors': []
    }
    
    try:
        # Run comprehensive validation
        validation_results = focus_observability.run_comprehensive_validation()
        
        for check_name, result in validation_results.items():
            results['checks'][check_name] = {
                'passed': result.passed,
                'message': result.message,
                'details': result.details
            }
            
            status = "✓" if result.passed else "✗"
            print(f"{status} {check_name}: {result.message}")
            
            if not result.passed:
                results['integrity_valid'] = False
                results['errors'].append(f"{check_name}: {result.message}")
    
    except Exception as e:
        results['integrity_valid'] = False
        results['errors'].append(f"Integrity validation failed: {str(e)}")
        print(f"✗ Integrity validation error: {e}")
    
    return results


def validate_performance() -> Dict[str, Any]:
    """Validate system performance and metrics"""
    print("\n=== Performance Validation ===")
    
    results = {
        'performance_valid': True,
        'metrics': {},
        'errors': []
    }
    
    try:
        # Get metrics summary
        metrics_summary = focus_observability.get_metrics_summary()
        results['metrics'] = metrics_summary
        
        print(f"Total metrics collected: {metrics_summary.get('total_metrics', 0)}")
        
        if 'by_type' in metrics_summary:
            for metric_type, metrics in metrics_summary['by_type'].items():
                print(f"  {metric_type}: {len(metrics)} metrics")
        
        # Check if we have recent metrics
        if metrics_summary.get('total_metrics', 0) == 0:
            print("⚠ No metrics collected yet - run workflow to generate performance data")
        else:
            print("✓ Metrics collection working")
    
    except Exception as e:
        results['performance_valid'] = False
        results['errors'].append(f"Performance validation failed: {str(e)}")
        print(f"✗ Performance validation error: {e}")
    
    return results


def print_summary(config_results: Dict[str, Any], schema_results: Dict[str, Any], 
                 integrity_results: Dict[str, Any], performance_results: Dict[str, Any]) -> bool:
    """Print validation summary"""
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    
    all_valid = True
    total_errors = 0
    
    # Configuration
    config_valid = config_results['config_valid']
    config_errors = len(config_results['errors'])
    status = "✓" if config_valid else "✗"
    print(f"{status} Configuration: {'Valid' if config_valid else f'Invalid ({config_errors} errors)'}")
    
    if not config_valid:
        all_valid = False
        total_errors += config_errors
    
    # Schema
    schema_valid = schema_results['schema_valid']
    schema_errors = len(schema_results['errors'])
    status = "✓" if schema_valid else "✗"
    print(f"{status} Database Schema: {'Valid' if schema_valid else f'Invalid ({schema_errors} errors)'}")
    
    if not schema_valid:
        all_valid = False
        total_errors += schema_errors
    
    # Integrity
    integrity_valid = integrity_results['integrity_valid']
    integrity_errors = len(integrity_results['errors'])
    status = "✓" if integrity_valid else "✗"
    print(f"{status} Data Integrity: {'Valid' if integrity_valid else f'Invalid ({integrity_errors} errors)'}")
    
    if not integrity_valid:
        all_valid = False
        total_errors += integrity_errors
    
    # Performance
    performance_valid = performance_results['performance_valid']
    performance_errors = len(performance_results['errors'])
    status = "✓" if performance_valid else "✗"
    print(f"{status} Performance: {'Valid' if performance_valid else f'Invalid ({performance_errors} errors)'}")
    
    if not performance_valid:
        all_valid = False
        total_errors += performance_errors
    
    print(f"\nOverall Status: {'✓ PASS' if all_valid else f'✗ FAIL ({total_errors} total errors)'}")
    
    if not all_valid:
        print("\nErrors found:")
        for result in [config_results, schema_results, integrity_results, performance_results]:
            for error in result['errors']:
                print(f"  - {error}")
    
    return all_valid


def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description='Validate FOCUS billing system')
    parser.add_argument('--config-only', action='store_true', help='Only validate configuration')
    parser.add_argument('--schema-only', action='store_true', help='Only validate database schema')
    parser.add_argument('--integrity-only', action='store_true', help='Only validate data integrity')
    parser.add_argument('--performance-only', action='store_true', help='Only validate performance')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("FOCUS Billing System Validation")
        print("="*50)
    
    try:
        # Run validations based on arguments
        config_results = {'config_valid': True, 'errors': []}
        schema_results = {'schema_valid': True, 'errors': []}
        integrity_results = {'integrity_valid': True, 'errors': []}
        performance_results = {'performance_valid': True, 'errors': []}
        
        if args.config_only or not any([args.schema_only, args.integrity_only, args.performance_only]):
            config_results = validate_configuration()
        
        if args.schema_only or not any([args.config_only, args.integrity_only, args.performance_only]):
            schema_results = validate_database_schema()
        
        if args.integrity_only or not any([args.config_only, args.schema_only, args.performance_only]):
            integrity_results = validate_data_integrity()
        
        if args.performance_only or not any([args.config_only, args.schema_only, args.integrity_only]):
            performance_results = validate_performance()
        
        # Print summary
        if not args.quiet:
            all_valid = print_summary(config_results, schema_results, integrity_results, performance_results)
        else:
            all_valid = all([
                config_results['config_valid'],
                schema_results['schema_valid'],
                integrity_results['integrity_valid'],
                performance_results['performance_valid']
            ])
        
        # Exit with appropriate code
        sys.exit(0 if all_valid else 1)
        
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Validation failed with error: {e}")
        sys.exit(1)
    finally:
        # Clean up
        try:
            focus_observability.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()