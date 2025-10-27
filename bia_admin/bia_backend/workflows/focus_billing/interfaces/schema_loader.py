"""
Schema Loading Interfaces

Defines interfaces for loading FOCUS schema definitions and column metadata
from the FOCUS specification files.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..models import FocusColumn, FocusDataset


class IColumnMetadataLoader(ABC):
    """Interface for loading FOCUS column metadata from specification files"""
    
    @abstractmethod
    def load_column_metadata(self, dataset_name: str) -> List[FocusColumn]:
        """
        Load column metadata for a specific FOCUS dataset
        
        Args:
            dataset_name: Name of the dataset (e.g., 'cost_and_usage', 'contract_commitment')
            
        Returns:
            List of FocusColumn objects with metadata
        """
        pass
    
    @abstractmethod
    def get_clickhouse_type_mapping(self, focus_data_type: str, allows_nulls: bool) -> str:
        """
        Map FOCUS data type to ClickHouse type
        
        Args:
            focus_data_type: FOCUS data type from specification
            allows_nulls: Whether the column allows null values
            
        Returns:
            ClickHouse type string
        """
        pass


class ISchemaLoader(ABC):
    """Interface for loading complete FOCUS dataset schemas"""
    
    @abstractmethod
    def load_dataset_schema(self, dataset_name: str) -> FocusDataset:
        """
        Load complete schema for a FOCUS dataset
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            FocusDataset object with complete schema information
        """
        pass
    
    @abstractmethod
    def get_available_datasets(self) -> List[str]:
        """
        Get list of available FOCUS datasets
        
        Returns:
            List of dataset names
        """
        pass
    
    @abstractmethod
    def validate_schema_compatibility(self, dataset_name: str, parquet_schema: Dict[str, Any]) -> bool:
        """
        Validate that a Parquet file schema is compatible with FOCUS specification
        
        Args:
            dataset_name: Name of the FOCUS dataset
            parquet_schema: Schema from Parquet file
            
        Returns:
            True if compatible, False otherwise
        """
        pass