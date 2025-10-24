"""
Integration Test for FOCUS Billing Workflow

Tests the workflow with actual FOCUS data files to verify end-to-end functionality.
"""

import os
from pathlib import Path

from .workflow import FocusBillingIngestParams, FocusBillingIngestWorkflow
from .file_discovery import discover_focus_files
from .config import focus_config


def test_file_discovery_integration():
    """Test file discovery with actual FOCUS data directory"""
    print("Testing file discovery with actual FOCUS data...")
    
    # Check if FOCUS data directory exists
    data_root = Path(focus_config.focus_data_root)
    if not data_root.exists():
        print(f"FOCUS data directory not found: {data_root}")
        print("Skipping integration test")
        return
    
    try:
        # Discover files
        files, stats = discover_focus_files()
        
        print(f"Discovery results:")
        print(f"  - Total files found: {len(files)}")
        print(f"  - Processing stats: {stats}")
        
        # Show breakdown by dataset type
        type_counts = {}
        for file_info in files:
            dataset_type = file_info.dataset_type
            type_counts[dataset_type] = type_counts.get(dataset_type, 0) + 1
        
        for dataset_type, count in type_counts.items():
            print(f"  - {dataset_type}: {count} files")
        
        # Show sample file info
        if files:
            sample_file = files[0]
            print(f"\nSample file info:")
            print(f"  - Path: {sample_file.relative_path}")
            print(f"  - Dataset type: {sample_file.dataset_type}")
            print(f"  - Period: {sample_file.period_folder}")
            print(f"  - Row count: {sample_file.row_count}")
            print(f"  - Checksum: {sample_file.checksum[:16]}...")
        
        return len(files) > 0
        
    except Exception as e:
        print(f"File discovery failed: {e}")
        return False


def test_workflow_dry_run_integration():
    """Test workflow execution in dry run mode with actual data"""
    print("\nTesting workflow dry run with actual data...")
    
    # Check if FOCUS data directory exists
    data_root = Path(focus_config.focus_data_root)
    if not data_root.exists():
        print(f"FOCUS data directory not found: {data_root}")
        print("Skipping workflow test")
        return
    
    try:
        # Create workflow parameters for dry run
        params = FocusBillingIngestParams(
            dry_run=True,
            max_files=3,  # Limit to first 3 files for testing
            continue_on_error=True
        )
        
        # Execute workflow
        workflow = FocusBillingIngestWorkflow(params)
        stats = workflow.execute()
        
        print(f"Workflow dry run results:")
        print(f"  - Files discovered: {stats.files_discovered}")
        print(f"  - Files processed: {stats.files_processed}")
        print(f"  - Files skipped: {stats.files_skipped}")
        print(f"  - Files failed: {stats.files_failed}")
        print(f"  - Total rows processed: {stats.total_rows_processed}")
        print(f"  - Processing time: {stats.total_processing_time:.2f}s")
        
        if stats.errors:
            print(f"  - Errors encountered: {len(stats.errors)}")
            for error in stats.errors[:3]:  # Show first 3 errors
                print(f"    - {error}")
        
        return stats.files_discovered > 0
        
    except Exception as e:
        print(f"Workflow execution failed: {e}")
        return False


def test_data_transformation_integration():
    """Test data transformation with actual Parquet file"""
    print("\nTesting data transformation with actual Parquet file...")
    
    try:
        # Discover files
        files, _ = discover_focus_files()
        
        if not files:
            print("No files found for transformation test")
            return False
        
        # Use first file for testing
        file_info = files[0]
        print(f"Testing transformation of: {file_info.relative_path}")
        
        # Import transformer
        from .data_transformer import transform_focus_data
        
        # Transform data
        result = transform_focus_data(file_info)
        
        print(f"Transformation results:")
        print(f"  - Success: {result.success}")
        print(f"  - Rows processed: {result.rows_processed}")
        
        if result.success and result.transformed_data is not None:
            df = result.transformed_data
            print(f"  - DataFrame shape: {df.shape}")
            print(f"  - Columns: {len(df.columns)}")
            print(f"  - Sample columns: {list(df.columns)[:5]}")
            
            # Check for required columns
            required_cols = ['id', 'source_system', 'created_at', 'updated_at']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"  - Missing required columns: {missing_cols}")
            else:
                print(f"  - All required columns present")
        
        if result.transformation_stats:
            stats = result.transformation_stats
            print(f"  - Memory usage: {stats.get('memory_usage_bytes', 0) / 1024 / 1024:.1f} MB")
        
        if not result.success:
            print(f"  - Error: {result.error_message}")
        
        return result.success
        
    except Exception as e:
        print(f"Data transformation test failed: {e}")
        return False


def main():
    """Run all integration tests"""
    print("Running FOCUS Billing Workflow Integration Tests")
    print("=" * 50)
    
    # Test file discovery
    discovery_success = test_file_discovery_integration()
    
    # Test workflow dry run
    workflow_success = test_workflow_dry_run_integration()
    
    # Test data transformation
    transformation_success = test_data_transformation_integration()
    
    print("\n" + "=" * 50)
    print("Integration Test Summary:")
    print(f"  - File Discovery: {'PASS' if discovery_success else 'FAIL'}")
    print(f"  - Workflow Dry Run: {'PASS' if workflow_success else 'FAIL'}")
    print(f"  - Data Transformation: {'PASS' if transformation_success else 'FAIL'}")
    
    all_passed = discovery_success and workflow_success and transformation_success
    print(f"\nOverall Result: {'PASS' if all_passed else 'FAIL'}")
    
    return all_passed


if __name__ == "__main__":
    main()