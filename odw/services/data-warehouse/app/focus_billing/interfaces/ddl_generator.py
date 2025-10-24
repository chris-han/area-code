"""
DDL Generation Interfaces

Defines interfaces for generating ClickHouse DDL statements from FOCUS specifications.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..models import FocusDataset


class IDDLGenerator(ABC):
    """Interface for generating ClickHouse DDL from FOCUS specifications"""
    
    @abstractmethod
    def generate_table_ddl(self, dataset: FocusDataset) -> str:
        """
        Generate CREATE TABLE DDL for a FOCUS dataset
        
        Args:
            dataset: FocusDataset with schema information
            
        Returns:
            CREATE TABLE DDL string
        """
        pass
    
    @abstractmethod
    def generate_view_ddl(self, dataset: FocusDataset) -> str:
        """
        Generate CREATE VIEW DDL for PascalCase column projection
        
        Args:
            dataset: FocusDataset with schema information
            
        Returns:
            CREATE VIEW DDL string
        """
        pass
    
    @abstractmethod
    def generate_indexes_ddl(self, dataset: FocusDataset) -> List[str]:
        """
        Generate index creation DDL statements
        
        Args:
            dataset: FocusDataset with schema information
            
        Returns:
            List of CREATE INDEX DDL strings
        """
        pass
    
    @abstractmethod
    def generate_drop_ddl(self, dataset: FocusDataset) -> List[str]:
        """
        Generate DROP statements for cleanup
        
        Args:
            dataset: FocusDataset with schema information
            
        Returns:
            List of DROP DDL strings
        """
        pass
    
    @abstractmethod
    def validate_ddl_syntax(self, ddl: str) -> bool:
        """
        Validate DDL syntax
        
        Args:
            ddl: DDL string to validate
            
        Returns:
            True if syntax is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def execute_ddl(self, ddl: str) -> bool:
        """
        Execute DDL against ClickHouse
        
        Args:
            ddl: DDL string to execute
            
        Returns:
            True if execution successful, False otherwise
        """
        pass