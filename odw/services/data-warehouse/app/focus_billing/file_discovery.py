"""
FOCUS Parquet File Discovery and Processing

Handles discovery of FOCUS Parquet files in the configured data directory,
reads manifest.json metadata, and tracks processed files to avoid duplicates.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .config import focus_config
from .models import FocusIngestManifest


@dataclass
class ParquetFileInfo:
    """Information about a discovered Parquet file"""
    file_path: Path
    relative_path: str
    manifest_path: Path
    manifest_data: Dict[str, Any]
    dataset_type: str
    period_folder: str
    export_timestamp: str
    run_id: str
    checksum: str
    row_count: int


class FocusFileDiscovery:
    """
    Discovers and processes FOCUS Parquet files from the configured data directory.
    
    Expected directory structure:
    FOCUS_DATA_ROOT/
    ├── 20250701-20250731/          # Period folder
    │   ├── 202507161527/           # Export timestamp
    │   │   └── cc47e41e-.../       # Run ID folder
    │   │       ├── manifest.json
    │   │       └── part_0_0001.snappy.parquet
    │   └── 202507170944/
    │       └── ...
    └── 20250801-20250831/
        └── ...
    """
    
    def __init__(self, data_root: Optional[str] = None):
        """Initialize file discovery with optional data root override"""
        self.data_root = Path(data_root or focus_config.focus_data_root)
        
    def discover_parquet_files(self) -> List[ParquetFileInfo]:
        """
        Discover all Parquet files in the FOCUS data directory.
        
        Returns:
            List of ParquetFileInfo objects for all discovered files
        """
        if not self.data_root.exists():
            raise FileNotFoundError(f"FOCUS data root does not exist: {self.data_root}")
            
        parquet_files = []
        
        # Walk through period folders (e.g., 20250701-20250731)
        for period_folder in self.data_root.iterdir():
            if not period_folder.is_dir():
                continue
                
            # Walk through export timestamp folders (e.g., 202507161527)
            for export_folder in period_folder.iterdir():
                if not export_folder.is_dir():
                    continue
                    
                # Walk through run ID folders (e.g., cc47e41e-a6ab-462e-9b26-fe7237024648)
                for run_folder in export_folder.iterdir():
                    if not run_folder.is_dir():
                        continue
                        
                    # Look for manifest.json and parquet files
                    manifest_path = run_folder / "manifest.json"
                    if not manifest_path.exists():
                        continue
                        
                    # Find parquet files in this run folder
                    parquet_paths = list(run_folder.glob("*.parquet"))
                    if not parquet_paths:
                        continue
                        
                    # Read manifest data
                    try:
                        manifest_data = self._read_manifest(manifest_path)
                    except Exception as e:
                        print(f"Warning: Failed to read manifest {manifest_path}: {e}")
                        continue
                        
                    # Process each parquet file
                    for parquet_path in parquet_paths:
                        try:
                            file_info = self._create_file_info(
                                parquet_path=parquet_path,
                                manifest_path=manifest_path,
                                manifest_data=manifest_data,
                                period_folder=period_folder.name,
                                export_timestamp=export_folder.name,
                                run_id=run_folder.name
                            )
                            parquet_files.append(file_info)
                        except Exception as e:
                            print(f"Warning: Failed to process {parquet_path}: {e}")
                            continue
                            
        return parquet_files
    
    def _read_manifest(self, manifest_path: Path) -> Dict[str, Any]:
        """Read and parse manifest.json file"""
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _create_file_info(
        self,
        parquet_path: Path,
        manifest_path: Path,
        manifest_data: Dict[str, Any],
        period_folder: str,
        export_timestamp: str,
        run_id: str
    ) -> ParquetFileInfo:
        """Create ParquetFileInfo from discovered file and manifest data"""
        
        # Calculate relative path from data root
        relative_path = str(parquet_path.relative_to(self.data_root))
        
        # Calculate file checksum
        checksum = self._calculate_file_checksum(parquet_path)
        
        # Determine dataset type from export config
        dataset_type = self._determine_dataset_type(manifest_data)
        
        # Get row count from manifest
        row_count = self._get_row_count_from_manifest(manifest_data, parquet_path.name)
        
        return ParquetFileInfo(
            file_path=parquet_path,
            relative_path=relative_path,
            manifest_path=manifest_path,
            manifest_data=manifest_data,
            dataset_type=dataset_type,
            period_folder=period_folder,
            export_timestamp=export_timestamp,
            run_id=run_id,
            checksum=checksum,
            row_count=row_count
        )
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file for change detection"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _determine_dataset_type(self, manifest_data: Dict[str, Any]) -> str:
        """
        Determine dataset type from manifest export config.
        
        Returns 'cost_usage' or 'contract_commitment' based on export type.
        """
        export_config = manifest_data.get('exportConfig', {})
        export_type = export_config.get('type', '').lower()
        
        if 'cost' in export_type:
            return 'cost_usage'
        elif 'commitment' in export_type or 'contract' in export_type:
            return 'contract_commitment'
        else:
            # Default to cost_usage for unknown types
            return 'cost_usage'
    
    def _get_row_count_from_manifest(self, manifest_data: Dict[str, Any], parquet_filename: str) -> int:
        """Get row count for specific parquet file from manifest blobs array"""
        blobs = manifest_data.get('blobs', [])
        
        # Try to find matching blob by filename
        for blob in blobs:
            blob_name = blob.get('blobName', '')
            if parquet_filename in blob_name:
                return blob.get('dataRowCount', 0)
        
        # Fallback to total row count if specific blob not found
        return manifest_data.get('dataRowCount', 0)


class ProcessedFileTracker:
    """
    Tracks processed files to avoid reprocessing.
    
    This class manages the manifest table to keep track of which files
    have already been processed, their status, and any errors encountered.
    """
    
    def __init__(self):
        self.manifest_table = focus_config.manifest_table_name
    
    def is_file_processed(self, file_info: ParquetFileInfo) -> bool:
        """
        Check if a file has already been processed successfully.
        
        Args:
            file_info: Information about the file to check
            
        Returns:
            True if file has been processed successfully, False otherwise
        """
        # This will be implemented when we have ClickHouse integration
        # For now, return False to process all files
        return False
    
    def mark_file_processing_started(self, file_info: ParquetFileInfo) -> str:
        """
        Mark a file as processing started and return manifest entry ID.
        
        Args:
            file_info: Information about the file being processed
            
        Returns:
            Manifest entry ID for tracking
        """
        manifest_id = self._generate_manifest_id(file_info)
        
        # This will create a manifest entry with status 'processing'
        # Implementation will be added when ClickHouse integration is ready
        
        return manifest_id
    
    def mark_file_processing_success(
        self,
        manifest_id: str,
        rows_processed: int,
        processing_duration: float
    ) -> None:
        """
        Mark a file as successfully processed.
        
        Args:
            manifest_id: Manifest entry ID
            rows_processed: Number of rows successfully processed
            processing_duration: Processing time in seconds
        """
        # Update manifest entry with success status
        # Implementation will be added when ClickHouse integration is ready
        pass
    
    def mark_file_processing_failed(
        self,
        manifest_id: str,
        error_message: str
    ) -> None:
        """
        Mark a file as failed to process.
        
        Args:
            manifest_id: Manifest entry ID
            error_message: Error message describing the failure
        """
        # Update manifest entry with failed status and error message
        # Implementation will be added when ClickHouse integration is ready
        pass
    
    def _generate_manifest_id(self, file_info: ParquetFileInfo) -> str:
        """Generate unique manifest entry ID from file info"""
        # Create deterministic ID from file path and checksum
        content = f"{file_info.relative_path}:{file_info.checksum}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_processing_stats(self) -> Dict[str, int]:
        """
        Get statistics about processed files.
        
        Returns:
            Dictionary with counts of processed, failed, and pending files
        """
        # This will query the manifest table for statistics
        # Implementation will be added when ClickHouse integration is ready
        return {
            'processed': 0,
            'failed': 0,
            'pending': 0,
            'total_files': 0
        }


def discover_focus_files(data_root: Optional[str] = None) -> Tuple[List[ParquetFileInfo], Dict[str, int]]:
    """
    Convenience function to discover FOCUS files and return processing statistics.
    
    Args:
        data_root: Optional override for FOCUS data root directory
        
    Returns:
        Tuple of (discovered files, processing statistics)
    """
    discovery = FocusFileDiscovery(data_root)
    tracker = ProcessedFileTracker()
    
    # Discover all files
    all_files = discovery.discover_parquet_files()
    
    # Filter out already processed files
    unprocessed_files = [
        file_info for file_info in all_files
        if not tracker.is_file_processed(file_info)
    ]
    
    # Get processing statistics
    stats = tracker.get_processing_stats()
    stats['total_files'] = len(all_files)
    stats['pending'] = len(unprocessed_files)
    
    return unprocessed_files, stats