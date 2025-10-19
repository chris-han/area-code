"""
S3 CSV Source Data Models

Data models for CSV-based billing data from S3-compatible storage.
Enhanced with schema detection and validation capabilities.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from moose_lib import Key
from pydantic import BaseModel, Field, validator
from .azure_ea_models import BaseSourceModel


class S3CSVSourceModel(BaseSourceModel):
    """
    Generic S3 CSV source model for file-based billing data.
    
    This model handles variable CSV schemas and provides a flexible
    structure for different CSV formats before FOCUS transformation.
    """
    
    # File metadata
    file_path: str = Field(description="S3 object key/path to the source file")
    file_name: str = Field(description="Name of the source CSV file")
    bucket_name: str = Field(description="S3 bucket name")
    file_size: Optional[int] = Field(description="File size in bytes")
    file_last_modified: Optional[datetime] = Field(
        description="File last modified timestamp"
    )
    
    # CSV structure metadata
    headers: List[str] = Field(description="CSV column headers")
    row_number: int = Field(description="Row number in the CSV file")
    total_rows: Optional[int] = Field(description="Total rows in the file")
    
    # Dynamic data content
    row_data: Dict[str, Any] = Field(description="Key-value pairs of CSV data")
    
    # Processing metadata
    schema_version: Optional[str] = Field(description="Detected schema version")
    validation_status: str = Field(default="pending", description="Validation status")
    validation_errors: Optional[List[str]] = Field(
        description="Validation error messages"
    )
    
    # Data quality metrics
    null_fields: Optional[List[str]] = Field(description="Fields with null values")
    data_types: Optional[Dict[str, str]] = Field(
        description="Detected data types for each field"
    )
    
    @validator('row_number')
    def validate_row_number(cls, v):
        """Validate row number is positive"""
        if v <= 0:
            raise ValueError('Row number must be positive')
        return v
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size is not negative"""
        if v is not None and v < 0:
            raise ValueError('File size cannot be negative')
        return v
    
    def get_focus_mapping(self) -> Dict[str, str]:
        """
        Return field mapping to FOCUS model.
        
        This is a generic mapping that should be customized based on
        the actual CSV schema detected.
        """
        # Common field mappings for typical billing CSV files
        common_mappings = {
            "account_id": "billing_account_id",
            "account_name": "billing_account_name",
            "usage_date": "usage_date",
            "cost": "billed_cost",
            "amount": "billed_cost",
            "charge": "billed_cost",
            "service": "service_name",
            "service_name": "service_name",
            "resource_id": "resource_id",
            "resource_name": "resource_name",
            "region": "region",
            "location": "region",
            "currency": "billing_currency"
        }
        
        # Map based on detected headers
        mapping = {}
        for header in self.headers:
            header_lower = header.lower().replace(' ', '_').replace('-', '_')
            if header_lower in common_mappings:
                mapping[header] = common_mappings[header_lower]
        
        return mapping
    
    def validate_business_rules(self) -> List[str]:
        """Validate S3 CSV business rules"""
        errors = []
        
        # Check for required data
        if not self.row_data:
            errors.append("row_data cannot be empty")
        
        # Check for minimum required fields for FOCUS transformation
        focus_mapping = self.get_focus_mapping()
        required_focus_fields = ["billing_account_id", "usage_date", "billed_cost"]
        
        for focus_field in required_focus_fields:
            if focus_field not in focus_mapping.values():
                errors.append(f"No mapping found for required FOCUS field: {focus_field}")
        
        # Validate data quality
        if self.null_fields and len(self.null_fields) > len(self.headers) * 0.5:
            errors.append("More than 50% of fields are null - data quality issue")
        
        return errors


class S3CSVBillingRecord(BaseSourceModel):
    """
    Structured billing record extracted from S3 CSV data.
    
    This model represents a normalized billing record after initial
    processing of CSV data but before FOCUS transformation.
    """
    
    # Common billing fields (mapped from CSV)
    account_id: Optional[str] = Field(description="Account identifier")
    account_name: Optional[str] = Field(description="Account name")
    subscription_id: Optional[str] = Field(description="Subscription identifier")
    subscription_name: Optional[str] = Field(description="Subscription name")
    usage_date: Optional[datetime] = Field(description="Usage date")
    service_name: Optional[str] = Field(description="Service name")
    service_category: Optional[str] = Field(description="Service category")
    resource_id: Optional[str] = Field(description="Resource identifier")
    resource_name: Optional[str] = Field(description="Resource name")
    resource_type: Optional[str] = Field(description="Resource type")
    resource_group: Optional[str] = Field(description="Resource group")
    location: Optional[str] = Field(description="Resource location")
    availability_zone: Optional[str] = Field(description="Availability zone")
    
    # Cost and usage fields
    usage_quantity: Optional[Decimal] = Field(description="Usage quantity")
    usage_unit: Optional[str] = Field(description="Usage unit")
    unit_price: Optional[Decimal] = Field(description="Unit price")
    cost: Optional[Decimal] = Field(description="Total cost")
    currency: Optional[str] = Field(description="Currency code")
    
    # Additional fields
    tags: Optional[Dict[str, str]] = Field(description="Resource tags")
    additional_properties: Optional[Dict[str, Any]] = Field(
        description="Additional CSV fields"
    )
    
    # Source metadata
    source_file_path: str = Field(description="Source CSV file path")
    source_row_number: int = Field(description="Source row number")
    
    @validator('cost', 'unit_price', 'usage_quantity')
    def validate_numeric_fields(cls, v):
        """Validate numeric fields are not negative"""
        if v is not None and v < 0:
            raise ValueError('Numeric fields cannot be negative')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code format"""
        if v is not None and len(v) != 3:
            raise ValueError('Currency code must be 3 characters (ISO 4217)')
        return v
    
    def get_focus_mapping(self) -> Dict[str, str]:
        """Return field mapping to FOCUS model"""
        return {
            "account_id": "billing_account_id",
            "account_name": "billing_account_name",
            "usage_date": "usage_date",
            "cost": "billed_cost",
            "unit_price": "list_unit_price",
            "usage_quantity": "usage_quantity",
            "usage_unit": "usage_unit",
            "resource_id": "resource_id",
            "resource_name": "resource_name",
            "service_name": "service_name",
            "service_category": "service_category",
            "location": "region",
            "availability_zone": "availability_zone",
            "currency": "billing_currency"
        }
    
    def validate_business_rules(self) -> List[str]:
        """Validate S3 CSV billing record business rules"""
        errors = []
        
        # Required fields for FOCUS transformation
        if not self.account_id:
            errors.append("account_id is required for FOCUS transformation")
        
        if not self.usage_date:
            errors.append("usage_date is required for FOCUS transformation")
        
        if self.cost is None or self.cost <= 0:
            errors.append("cost must be greater than 0")
        
        # Validate cost calculation consistency
        if (self.usage_quantity and self.unit_price and self.cost and
            abs(float(self.cost) - (float(self.usage_quantity) * float(self.unit_price))) > 0.01):
            errors.append("cost does not match usage_quantity * unit_price")
        
        return errors


class S3CSVSchemaMapping(BaseModel):
    """
    Schema mapping configuration for CSV to billing record transformation.
    Enhanced with validation and FOCUS compliance checking.
    """
    
    id: Key[str] = Field(description="Unique mapping identifier")
    
    # Mapping metadata
    mapping_name: str = Field(description="Name of the mapping configuration")
    source_schema_version: str = Field(description="Source CSV schema version")
    target_model: str = Field(description="Target model name")
    
    # Field mappings
    field_mappings: Dict[str, str] = Field(
        description="CSV column to model field mappings"
    )
    data_type_conversions: Dict[str, str] = Field(
        description="Data type conversion rules"
    )
    default_values: Optional[Dict[str, Any]] = Field(
        description="Default values for missing fields"
    )
    validation_rules: Optional[Dict[str, List[str]]] = Field(
        description="Field validation rules"
    )
    
    # Transformation rules
    date_format: Optional[str] = Field(description="Date format pattern")
    currency_field: Optional[str] = Field(description="Currency field name")
    cost_fields: List[str] = Field(description="Fields containing cost data")
    
    # FOCUS compliance
    focus_field_mappings: Optional[Dict[str, str]] = Field(
        description="Direct mappings to FOCUS fields"
    )
    required_focus_fields: List[str] = Field(
        default=["billing_account_id", "usage_date", "billed_cost"],
        description="Required FOCUS fields for compliance"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(description="Creator identifier")
    is_active: bool = Field(default=True, description="Is mapping active")
    
    @validator('field_mappings')
    def validate_field_mappings(cls, v):
        """Validate field mappings are not empty"""
        if not v:
            raise ValueError('field_mappings cannot be empty')
        return v
    
    @validator('cost_fields')
    def validate_cost_fields(cls, v):
        """Validate at least one cost field is specified"""
        if not v:
            raise ValueError('At least one cost field must be specified')
        return v
    
    def validate_focus_compliance(self) -> List[str]:
        """
        Validate that the mapping can produce FOCUS-compliant records.
        
        Returns:
            List of validation errors (empty if compliant)
        """
        errors = []
        
        # Check if all required FOCUS fields can be mapped
        available_mappings = set(self.field_mappings.values())
        if self.focus_field_mappings:
            available_mappings.update(self.focus_field_mappings.values())
        
        for required_field in self.required_focus_fields:
            if required_field not in available_mappings:
                errors.append(f"No mapping available for required FOCUS field: {required_field}")
        
        # Validate cost field mappings
        cost_mapped = False
        for cost_field in self.cost_fields:
            if cost_field in self.field_mappings:
                cost_mapped = True
                break
        
        if not cost_mapped:
            errors.append("No cost fields are properly mapped")
        
        return errors
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CSVSchemaDetector:
    """
    Utility class for detecting CSV schema and suggesting mappings.
    """
    
    @staticmethod
    def detect_schema(headers: List[str], sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect CSV schema from headers and sample data.
        
        Args:
            headers: CSV column headers
            sample_data: Sample rows of data
            
        Returns:
            Schema detection results
        """
        schema = {
            "headers": headers,
            "data_types": {},
            "suggested_mappings": {},
            "null_percentages": {},
            "sample_values": {}
        }
        
        # Analyze each column
        for header in headers:
            values = [row.get(header) for row in sample_data if row.get(header) is not None]
            
            if not values:
                schema["data_types"][header] = "unknown"
                schema["null_percentages"][header] = 100.0
                continue
            
            # Detect data type
            schema["data_types"][header] = CSVSchemaDetector._detect_data_type(values)
            
            # Calculate null percentage
            total_rows = len(sample_data)
            non_null_rows = len(values)
            schema["null_percentages"][header] = ((total_rows - non_null_rows) / total_rows) * 100
            
            # Store sample values
            schema["sample_values"][header] = values[:5]  # First 5 non-null values
            
            # Suggest FOCUS mapping
            suggested_focus_field = CSVSchemaDetector._suggest_focus_mapping(header)
            if suggested_focus_field:
                schema["suggested_mappings"][header] = suggested_focus_field
        
        return schema
    
    @staticmethod
    def _detect_data_type(values: List[Any]) -> str:
        """Detect data type from sample values"""
        if not values:
            return "unknown"
        
        # Try to detect numeric types
        numeric_count = 0
        date_count = 0
        
        for value in values:
            str_value = str(value).strip()
            
            # Check if numeric
            try:
                float(str_value.replace(',', '').replace('$', ''))
                numeric_count += 1
            except ValueError:
                pass
            
            # Check if date-like
            if any(char in str_value for char in ['-', '/', ':']):
                date_count += 1
        
        total_values = len(values)
        
        if numeric_count / total_values > 0.8:
            return "numeric"
        elif date_count / total_values > 0.8:
            return "date"
        else:
            return "string"
    
    @staticmethod
    def _suggest_focus_mapping(header: str) -> Optional[str]:
        """Suggest FOCUS field mapping based on header name"""
        header_lower = header.lower().replace(' ', '_').replace('-', '_')
        
        mapping_suggestions = {
            # Account mappings
            "account_id": "billing_account_id",
            "account_name": "billing_account_name",
            "subscription_id": "billing_account_id",
            "subscription_name": "billing_account_name",
            
            # Date mappings
            "date": "usage_date",
            "usage_date": "usage_date",
            "billing_date": "usage_date",
            
            # Cost mappings
            "cost": "billed_cost",
            "amount": "billed_cost",
            "charge": "billed_cost",
            "billed_cost": "billed_cost",
            "total_cost": "billed_cost",
            
            # Usage mappings
            "quantity": "usage_quantity",
            "usage_quantity": "usage_quantity",
            "consumed_quantity": "usage_quantity",
            "unit": "usage_unit",
            "usage_unit": "usage_unit",
            "unit_of_measure": "usage_unit",
            
            # Resource mappings
            "resource_id": "resource_id",
            "resource_name": "resource_name",
            "instance_id": "resource_id",
            
            # Service mappings
            "service": "service_name",
            "service_name": "service_name",
            "service_category": "service_category",
            
            # Geographic mappings
            "region": "region",
            "location": "region",
            "availability_zone": "availability_zone",
            "zone": "availability_zone",
            
            # Currency mappings
            "currency": "billing_currency",
            "currency_code": "billing_currency"
        }
        
        return mapping_suggestions.get(header_lower)