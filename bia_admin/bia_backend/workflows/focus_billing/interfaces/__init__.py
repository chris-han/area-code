"""
FOCUS Billing Interfaces

Core interfaces and abstract base classes for FOCUS billing integration.
"""

from .schema_loader import ISchemaLoader, IColumnMetadataLoader
from .query_loader import IQueryLoader
from .data_ingestion import IDataIngestionEngine
from .ddl_generator import IDDLGenerator

__all__ = [
    'ISchemaLoader',
    'IColumnMetadataLoader', 
    'IQueryLoader',
    'IDataIngestionEngine',
    'IDDLGenerator'
]