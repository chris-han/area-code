"""
Data Ingestion Interfaces

Defines interfaces for FOCUS data ingestion from Parquet files to ClickHouse.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
from pathlib import Path
from ..models import FocusIngestManifest


class IDataIngestionEngine(ABC):
    """Interface for FOCUS data ingestion engine"""
    
    @abstractmethod
    def discover_parquet_files(self, root_path: Path) -> List[Path]:
        """
        Discover Parquet files in the FOCUS data directory
        
        Args:
            root_path: Root path to search for Parquet files
            
        Returns:
            List of Parquet file paths
        """
        pass
    
    @abstractmethod
    def read_manifest_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Read manifest.json metadata for a Parquet file
        
        Args:
            file_path: Path to Parquet file
            
        Returns:
            Manifest metadata dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def is_file_processed(self, file_path: Path) -> bool:
        """
        Check if a file has already been processed
        
        Args:
            file_path: Path to Parquet file
            
        Returns:
            True if file has been processed, False otherwise
        """
        pass
    
    @abstractmethod
    def calculate_file_checksum(self, file_path: Path) -> str:
        """
        Calculate checksum for a file
        
        Args:
            file_path: Path to file
            
        Returns:
            File checksum string
        """
        pass
    
    @abstractmethod
    def transform_parquet_data(self, file_path: Path, dataset_type: str) -> Iterator[Dict[str, Any]]:
        """
        Transform Parquet data for ClickHouse insertion
        
        Args:
            file_path: Path to Parquet file
            dataset_type: Type of dataset (cost_usage or contract_commitment)
            
        Yields:
            Transformed data dictionaries
        """
        pass
    
    @abstractmethod
    def insert_batch_to_clickhouse(self, table_name: str, data_batch: List[Dict[str, Any]]) -> int:
        """
        Insert a batch of data to ClickHouse
        
        Args:
            table_name: Target table name
            data_batch: List of data dictionaries to insert
            
        Returns:
            Number of rows inserted
        """
        pass
    
    @abstractmethod
    def record_manifest_entry(self, manifest_entry: FocusIngestManifest) -> None:
        """
        Record a manifest entry for processed file
        
        Args:
            manifest_entry: Manifest entry to record
        """
        pass
    
    @abstractmethod
    def validate_referential_integrity(self) -> List[str]:
        """
        Validate referential integrity between datasets
        
        Returns:
            List of validation error messages (empty if valid)
        """
        pass