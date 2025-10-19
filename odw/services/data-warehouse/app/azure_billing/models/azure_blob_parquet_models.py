"""
Azure Blob Storage Parquet Data Models for NCEI

Data models for FOCUS-compliant parquet files from Azure Blob Storage.
Replaces S3 CSV models with native parquet support for NCEI data source.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

from moose_lib import Key
from pydantic import BaseModel, Field, validator
from .azure_ea_models import BaseSourceModel


class ParquetCompressionType(str, Enum):
    """Supported parquet compression types"""
    SNAPPY = "snappy"
    GZIP = "gzip"
    LZ4 = "lz4"
    BROTLI = "brotli"
    UNCOMPRESSED = "uncompressed"


class AzureNCEIParquetModel(BaseSourceModel):
    """
    Azure NCEI Blob Storage parquet source model for FOCUS-compliant billing data.
    """
    
    # Blob metadata
    blob_path: str = Field(description="Azure Blob Storage path to the parquet file")
    blob_name: str = Field(description="Name of the parquet file")
    container_name: str = Field(description="Azure Blob Storage container name")
    secondary_container: Optional[str] = Field(description="Optional secondary container")
    account_url: str = Field(description="Azure Storage account URL")
    
    # File metadata
    file_size: Optional[int] = Field(description="File size in bytes")
    file_last_modified: Optional[datetime] = Field(description="File last modified timestamp")
    content_type: str = Field(default="application/parquet", description="File content type")
    compression_type: Optional[ParquetCompressionType] = Field(description="Parquet compression type")
    
    # Parquet schema metadata
    parquet_schema: Optional[Dict[str, Any]] = Field(description="Parquet file schema")
    column_names: List[str] = Field(description="Column names in parquet file")
    row_count: Optional[int] = Field(description="Total rows in the parquet file")
    row_group_count: Optional[int] = Field(description="Number of row groups")
    
    # FOCUS compliance metadata
    focus_version: Optional[str] = Field(description="FOCUS specification version")
    is_focus_compliant: Optional[bool] = Field(description="Whether file is FOCUS compliant")
    focus_validation_errors: Optional[List[str]] = Field(description="FOCUS validation errors")
    
    # Processing metadata
    processing_status: str = Field(default="pending", description="Processing status")
    validation_status: str = Field(default="pending", description="Validation status")
    transformation_required: bool = Field(default=False, description="Whether transformation is needed")
    
    # Data quality metrics
    null_column_percentages: Optional[Dict[str, float]] = Field(description="Null percentages per column")
    data_types: Optional[Dict[str, str]] = Field(description="Detected data types for each column")
    min_max_values: Optional[Dict[str, Dict[str, Any]]] = Field(description="Min/max values for numeric columns")

    @validator('blob_path')
    def validate_blob_path(cls, v):
        """Validate blob path format"""
        if not v or not v.strip():
            raise ValueError('Blob path cannot be empty')
        if not v.endswith('.parquet'):
            raise ValueError('Blob path must point to a parquet file')
        return v

    @validator('account_url')
    def validate_account_url(cls, v):
        """Validate Azure Storage account URL"""
        if not v.startswith('https://'):
            raise ValueError('Account URL must start with https://')
        if '.blob.core.' not in v:
            raise ValueError('Invalid Azure Blob Storage URL format')
        return v

    def get_focus_field_mapping(self) -> Dict[str, str]:
        """Return field mapping to FOCUS model based on detected schema."""
        if not self.column_names:
            return {}
        
        focus_mappings = {}
        
        for column in self.column_names:
            column_lower = column.lower().replace(' ', '_').replace('-', '_')
            
            # Direct FOCUS field mappings
            if column_lower in [
                'billing_account_id', 'billing_account_name', 'billing_currency',
                'billing_period_start_date', 'billing_period_end_date',
                'billed_cost', 'effective_cost', 'list_cost', 'list_unit_price',
                'usage_date', 'usage_quantity', 'usage_unit',
                'resource_id', 'resource_name', 'resource_type',
                'service_category', 'service_name',
                'availability_zone', 'region', 'provider'
            ]:
                focus_mappings[column] = column_lower
            
            # Common alternative field names
            elif column_lower in ['account_id', 'subscription_id']:
                focus_mappings[column] = 'billing_account_id'
            elif column_lower in ['account_name', 'subscription_name']:
                focus_mappings[column] = 'billing_account_name'
            elif column_lower in ['cost', 'total_cost', 'amount']:
                focus_mappings[column] = 'billed_cost'
            elif column_lower in ['currency', 'currency_code']:
                focus_mappings[column] = 'billing_currency'
            elif column_lower in ['date', 'billing_date']:
                focus_mappings[column] = 'usage_date'
        
        return focus_mappings

    def validate_business_rules(self) -> List[str]:
        """Validate NCEI parquet business rules"""
        errors = []
        
        # Check for required FOCUS fields
        focus_mapping = self.get_focus_field_mapping()
        required_fields = ['billing_account_id', 'usage_date', 'billed_cost']
        
        for required_field in required_fields:
            if required_field not in focus_mapping.values():
                errors.append(f"Missing required FOCUS field: {required_field}")
        
        return errors