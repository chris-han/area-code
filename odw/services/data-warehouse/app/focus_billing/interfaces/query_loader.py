"""
Query Loading Interfaces

Defines interfaces for loading and managing FOCUS queries from YAML files.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models import FocusQuery, FocusQueryParameter


class IQueryLoader(ABC):
    """Interface for loading FOCUS queries from YAML files"""
    
    @abstractmethod
    def load_queries(self) -> List[FocusQuery]:
        """
        Load all FOCUS queries from YAML files
        
        Returns:
            List of FocusQuery objects
        """
        pass
    
    @abstractmethod
    def get_query_by_slug(self, slug: str) -> Optional[FocusQuery]:
        """
        Get a specific query by its slug
        
        Args:
            slug: Query slug identifier
            
        Returns:
            FocusQuery object if found, None otherwise
        """
        pass
    
    @abstractmethod
    def validate_query_parameters(self, query: FocusQuery, parameters: Dict[str, Any]) -> List[str]:
        """
        Validate parameters for a query
        
        Args:
            query: FocusQuery object
            parameters: Parameters to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        pass
    
    @abstractmethod
    def prepare_query_sql(self, query: FocusQuery, parameters: Dict[str, Any]) -> str:
        """
        Prepare SQL query with parameter substitution
        
        Args:
            query: FocusQuery object
            parameters: Parameters for substitution
            
        Returns:
            SQL string with parameters substituted
        """
        pass
    
    @abstractmethod
    def extract_query_parameters(self, sql: str) -> List[str]:
        """
        Extract parameter names from SQL query
        
        Args:
            sql: SQL query string
            
        Returns:
            List of parameter names found in the query
        """
        pass