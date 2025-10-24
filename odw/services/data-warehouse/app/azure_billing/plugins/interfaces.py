"""
Plugin Interfaces

Defines standard interfaces for different types of plugins
in the bia plugin system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from enum import Enum

from .manager import BasePlugin


class DataSourceType(Enum):
    """Data source types"""
    API = "api"
    FILE = "file"
    DATABASE = "database"
    STREAM = "stream"


class TransformationType(Enum):
    """Transformation types"""
    FIELD_MAPPING = "field_mapping"
    DATA_CLEANING = "data_cleaning"
    AGGREGATION = "aggregation"
    VALIDATION = "validation"


class OutputType(Enum):
    """Output types"""
    DATABASE = "database"
    FILE = "file"
    API = "api"
    STREAM = "stream"


class DataSourcePlugin(BasePlugin):
    """
    Abstract base class for data source plugins.
    
    Data source plugins extract data from various sources
    and provide it in a standardized format.
    """
    
    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        """Return the type of data source"""
        pass
    
    @abstractmethod
    async def extract_data(self, 
                          extraction_params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Extract data from the source.
        
        Args:
            extraction_params: Parameters for data extraction
            
        Yields:
            Data records
        """
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """
        Get the schema of the data source.
        
        Returns:
            Schema information
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to the data source.
        
        Returns:
            True if connection successful
        """
        pass
    
    async def get_extraction_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about data extraction.
        
        Returns:
            Extraction statistics
        """
        return {
            "total_records_extracted": 0,
            "extraction_rate_per_second": 0.0,
            "last_extraction_time": None,
            "error_count": 0
        }


class TransformationPlugin(BasePlugin):
    """
    Abstract base class for transformation plugins.
    
    Transformation plugins process and transform data
    between different formats and schemas.
    """
    
    @property
    @abstractmethod
    def transformation_type(self) -> TransformationType:
        """Return the type of transformation"""
        pass
    
    @abstractmethod
    async def transform_record(self, 
                             record: Dict[str, Any],
                             transformation_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Transform a single record.
        
        Args:
            record: Input record
            transformation_params: Optional transformation parameters
            
        Returns:
            Transformed record
        """
        pass
    
    @abstractmethod
    async def transform_batch(self, 
                            records: List[Dict[str, Any]],
                            transformation_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Transform a batch of records.
        
        Args:
            records: Input records
            transformation_params: Optional transformation parameters
            
        Returns:
            Transformed records
        """
        pass
    
    @abstractmethod
    async def validate_transformation(self, 
                                    input_record: Dict[str, Any],
                                    output_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate transformation result.
        
        Args:
            input_record: Original record
            output_record: Transformed record
            
        Returns:
            Validation result
        """
        pass
    
    async def get_transformation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about transformations.
        
        Returns:
            Transformation statistics
        """
        return {
            "total_records_transformed": 0,
            "transformation_rate_per_second": 0.0,
            "success_rate": 1.0,
            "error_count": 0,
            "last_transformation_time": None
        }


class OutputPlugin(BasePlugin):
    """
    Abstract base class for output plugins.
    
    Output plugins send transformed data to various destinations.
    """
    
    @property
    @abstractmethod
    def output_type(self) -> OutputType:
        """Return the type of output destination"""
        pass
    
    @abstractmethod
    async def send_record(self, 
                         record: Dict[str, Any],
                         output_params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a single record to the output destination.
        
        Args:
            record: Record to send
            output_params: Optional output parameters
            
        Returns:
            True if send successful
        """
        pass
    
    @abstractmethod
    async def send_batch(self, 
                        records: List[Dict[str, Any]],
                        output_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a batch of records to the output destination.
        
        Args:
            records: Records to send
            output_params: Optional output parameters
            
        Returns:
            Send result with statistics
        """
        pass
    
    @abstractmethod
    async def test_output_connection(self) -> bool:
        """
        Test connection to the output destination.
        
        Returns:
            True if connection successful
        """
        pass
    
    async def get_output_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about output operations.
        
        Returns:
            Output statistics
        """
        return {
            "total_records_sent": 0,
            "send_rate_per_second": 0.0,
            "success_rate": 1.0,
            "error_count": 0,
            "last_send_time": None
        }


class UtilityPlugin(BasePlugin):
    """
    Abstract base class for utility plugins.
    
    Utility plugins provide helper functions and tools
    for the bia system.
    """
    
    @abstractmethod
    async def execute_utility(self, 
                            utility_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the utility function.
        
        Args:
            utility_params: Parameters for utility execution
            
        Returns:
            Execution result
        """
        pass
    
    async def get_utility_info(self) -> Dict[str, Any]:
        """
        Get information about the utility.
        
        Returns:
            Utility information
        """
        return {
            "utility_type": "general",
            "supported_operations": [],
            "execution_count": 0,
            "last_execution_time": None
        }


class PluginFactory:
    """
    Factory class for creating plugin instances based on type.
    """
    
    @staticmethod
    def create_data_source_plugin(plugin_class: type, config: Dict[str, Any]) -> DataSourcePlugin:
        """Create a data source plugin instance"""
        if not issubclass(plugin_class, DataSourcePlugin):
            raise ValueError(f"Plugin class {plugin_class} is not a DataSourcePlugin")
        return plugin_class(config)
    
    @staticmethod
    def create_transformation_plugin(plugin_class: type, config: Dict[str, Any]) -> TransformationPlugin:
        """Create a transformation plugin instance"""
        if not issubclass(plugin_class, TransformationPlugin):
            raise ValueError(f"Plugin class {plugin_class} is not a TransformationPlugin")
        return plugin_class(config)
    
    @staticmethod
    def create_output_plugin(plugin_class: type, config: Dict[str, Any]) -> OutputPlugin:
        """Create an output plugin instance"""
        if not issubclass(plugin_class, OutputPlugin):
            raise ValueError(f"Plugin class {plugin_class} is not an OutputPlugin")
        return plugin_class(config)
    
    @staticmethod
    def create_utility_plugin(plugin_class: type, config: Dict[str, Any]) -> UtilityPlugin:
        """Create a utility plugin instance"""
        if not issubclass(plugin_class, UtilityPlugin):
            raise ValueError(f"Plugin class {plugin_class} is not a UtilityPlugin")
        return plugin_class(config)


class PluginCapabilities:
    """
    Defines standard capabilities that plugins can implement.
    """
    
    # Data source capabilities
    SUPPORTS_STREAMING = "supports_streaming"
    SUPPORTS_BATCH = "supports_batch"
    SUPPORTS_INCREMENTAL = "supports_incremental"
    SUPPORTS_SCHEMA_DETECTION = "supports_schema_detection"
    
    # Transformation capabilities
    SUPPORTS_FIELD_MAPPING = "supports_field_mapping"
    SUPPORTS_DATA_VALIDATION = "supports_data_validation"
    SUPPORTS_AGGREGATION = "supports_aggregation"
    SUPPORTS_FILTERING = "supports_filtering"
    
    # Output capabilities
    SUPPORTS_BULK_INSERT = "supports_bulk_insert"
    SUPPORTS_UPSERT = "supports_upsert"
    SUPPORTS_TRANSACTIONS = "supports_transactions"
    SUPPORTS_COMPRESSION = "supports_compression"
    
    # General capabilities
    SUPPORTS_MONITORING = "supports_monitoring"
    SUPPORTS_RETRY = "supports_retry"
    SUPPORTS_CACHING = "supports_caching"
    SUPPORTS_ENCRYPTION = "supports_encryption"


class PluginMetrics:
    """
    Standard metrics that plugins should track.
    """
    
    def __init__(self):
        self.metrics = {
            "execution_count": 0,
            "success_count": 0,
            "error_count": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "last_execution_time": None,
            "last_error_time": None,
            "last_error_message": None
        }
    
    def record_execution(self, execution_time: float, success: bool, error_message: Optional[str] = None):
        """Record plugin execution metrics"""
        self.metrics["execution_count"] += 1
        self.metrics["total_execution_time"] += execution_time
        self.metrics["average_execution_time"] = self.metrics["total_execution_time"] / self.metrics["execution_count"]
        self.metrics["last_execution_time"] = datetime.utcnow()
        
        if success:
            self.metrics["success_count"] += 1
        else:
            self.metrics["error_count"] += 1
            self.metrics["last_error_time"] = datetime.utcnow()
            self.metrics["last_error_message"] = error_message
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            "execution_count": 0,
            "success_count": 0,
            "error_count": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "last_execution_time": None,
            "last_error_time": None,
            "last_error_message": None
        }