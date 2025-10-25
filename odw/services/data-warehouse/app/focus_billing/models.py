"""
FOCUS Billing Data Models

Defines Pydantic models for FOCUS datasets, queries, and metadata.
These models represent the core data structures used throughout the
FOCUS billing integration.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from enum import Enum


class FocusColumnType(str, Enum):
    """FOCUS column types from specification"""
    DIMENSION = "Dimension"
    METRIC = "Metric"


class FocusFeatureLevel(str, Enum):
    """FOCUS feature levels from specification"""
    MANDATORY = "Mandatory"
    RECOMMENDED = "Recommended" 
    CONDITIONAL = "Conditional"


class FocusDataType(str, Enum):
    """FOCUS data types from specification"""
    STRING = "String"
    DECIMAL = "Decimal"
    DATE = "Date"
    DATETIME = "DateTime"
    JSON = "JSON"
    BOOLEAN = "Boolean"


class FocusColumn(BaseModel):
    """Metadata for a FOCUS column from specification"""
    name: str
    snake_case_name: str
    column_type: FocusColumnType
    feature_level: FocusFeatureLevel
    data_type: FocusDataType
    allows_nulls: bool
    description: Optional[str] = None
    clickhouse_type: str


class FocusDataset(BaseModel):
    """Metadata for a FOCUS dataset"""
    name: str
    description: str
    columns: List[FocusColumn]
    table_name: str
    view_name: str


class FocusCostUsage(BaseModel):
    """
    FOCUS Cost & Usage dataset model
    
    Represents a single row from the FOCUS Cost & Usage dataset.
    Column names use snake_case for ClickHouse storage but maintain
    metadata for canonical FOCUS PascalCase naming.
    """
    
    # Core identification
    id: str = Field(description="Deterministic hash ID")
    
    # Mandatory dimensions
    billing_account_id: str = Field(description="Billing Account ID")
    usage_date: date = Field(description="Usage Date")
    
    # Mandatory metrics  
    billed_cost: Decimal = Field(description="Billed Cost")
    
    # Recommended dimensions
    billing_account_name: Optional[str] = Field(None, description="Billing Account Name")
    billing_currency: Optional[str] = Field(None, description="Billing Currency")
    billing_period_start: Optional[date] = Field(None, description="Billing Period Start")
    billing_period_end: Optional[date] = Field(None, description="Billing Period End")
    charge_category: Optional[str] = Field(None, description="Charge Category")
    charge_description: Optional[str] = Field(None, description="Charge Description")
    charge_frequency: Optional[str] = Field(None, description="Charge Frequency")
    charge_period_start: Optional[date] = Field(None, description="Charge Period Start")
    charge_period_end: Optional[date] = Field(None, description="Charge Period End")
    commitment_discount_category: Optional[str] = Field(None, description="Commitment Discount Category")
    commitment_discount_id: Optional[str] = Field(None, description="Commitment Discount ID")
    commitment_discount_name: Optional[str] = Field(None, description="Commitment Discount Name")
    commitment_discount_type: Optional[str] = Field(None, description="Commitment Discount Type")
    consumed_quantity: Optional[Decimal] = Field(None, description="Consumed Quantity")
    consumed_unit: Optional[str] = Field(None, description="Consumed Unit")
    contract_commitment_id: Optional[str] = Field(None, description="Contract Commitment ID")
    effective_cost: Optional[Decimal] = Field(None, description="Effective Cost")
    invoice_issuer_name: Optional[str] = Field(None, description="Invoice Issuer Name")
    list_cost: Optional[Decimal] = Field(None, description="List Cost")
    list_unit_price: Optional[Decimal] = Field(None, description="List Unit Price")
    pricing_category: Optional[str] = Field(None, description="Pricing Category")
    pricing_quantity: Optional[Decimal] = Field(None, description="Pricing Quantity")
    pricing_unit: Optional[str] = Field(None, description="Pricing Unit")
    provider_name: Optional[str] = Field(None, description="Provider Name")
    publisher_name: Optional[str] = Field(None, description="Publisher Name")
    region_id: Optional[str] = Field(None, description="Region ID")
    region_name: Optional[str] = Field(None, description="Region Name")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    resource_name: Optional[str] = Field(None, description="Resource Name")
    resource_type: Optional[str] = Field(None, description="Resource Type")
    service_category: Optional[str] = Field(None, description="Service Category")
    service_name: Optional[str] = Field(None, description="Service Name")
    sku_id: Optional[str] = Field(None, description="SKU ID")
    sku_meter: Optional[str] = Field(None, description="SKU Meter")
    sku_price_id: Optional[str] = Field(None, description="SKU Price ID")
    sub_account_id: Optional[str] = Field(None, description="Sub Account ID")
    sub_account_name: Optional[str] = Field(None, description="Sub Account Name")
    
    # JSON fields (stored as strings in ClickHouse for compatibility)
    tags: Optional[str] = Field(None, description="Tags JSON")
    sku_price_details: Optional[str] = Field(None, description="SKU Price Details JSON")
    
    # Extended provider columns (x_* fields)
    # These will be dynamically added based on the actual data
    extended_attributes: Optional[Dict[str, Any]] = Field(None, description="Extended provider attributes")
    
    # Audit fields
    source_system: str = Field(default="focus_parquet", description="Source system identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Record update timestamp")

    class Config:
        # Allow extra fields for extended provider columns
        extra = "allow"
        # Use enum values for serialization
        use_enum_values = True


class FocusContractCommitment(BaseModel):
    """
    FOCUS Contract Commitment dataset model
    
    Represents a single row from the FOCUS Contract Commitment dataset.
    """
    
    # Core identification
    id: str = Field(description="Deterministic hash ID")
    contract_commitment_id: str = Field(description="Contract Commitment ID")
    
    # Contract commitment fields based on FOCUS specification
    billing_account_id: Optional[str] = Field(None, description="Billing Account ID")
    billing_account_name: Optional[str] = Field(None, description="Billing Account Name")
    commitment_discount_category: Optional[str] = Field(None, description="Commitment Discount Category")
    commitment_discount_id: Optional[str] = Field(None, description="Commitment Discount ID")
    commitment_discount_name: Optional[str] = Field(None, description="Commitment Discount Name")
    commitment_discount_type: Optional[str] = Field(None, description="Commitment Discount Type")
    contract_commitment_description: Optional[str] = Field(None, description="Contract Commitment Description")
    contract_commitment_end_date: Optional[date] = Field(None, description="Contract Commitment End Date")
    contract_commitment_start_date: Optional[date] = Field(None, description="Contract Commitment Start Date")
    contract_commitment_status: Optional[str] = Field(None, description="Contract Commitment Status")
    contract_commitment_type: Optional[str] = Field(None, description="Contract Commitment Type")
    provider_name: Optional[str] = Field(None, description="Provider Name")
    region_id: Optional[str] = Field(None, description="Region ID")
    region_name: Optional[str] = Field(None, description="Region Name")
    service_category: Optional[str] = Field(None, description="Service Category")
    service_name: Optional[str] = Field(None, description="Service Name")
    sku_id: Optional[str] = Field(None, description="SKU ID")
    sku_meter: Optional[str] = Field(None, description="SKU Meter")
    
    # Commitment metrics
    committed_cost: Optional[Decimal] = Field(None, description="Committed Cost")
    committed_quantity: Optional[Decimal] = Field(None, description="Committed Quantity")
    committed_unit: Optional[str] = Field(None, description="Committed Unit")
    
    # Extended attributes
    extended_attributes: Optional[Dict[str, Any]] = Field(None, description="Extended provider attributes")
    
    # Audit fields
    source_system: str = Field(default="focus_parquet", description="Source system identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Record update timestamp")

    class Config:
        extra = "allow"
        use_enum_values = True


class FocusQuery(BaseModel):
    """
    FOCUS query definition from YAML files
    """
    slug: str = Field(description="Unique query identifier")
    name: str = Field(description="Human-readable query name")
    description: Optional[str] = Field(None, description="Query description")
    sql: str = Field(description="SQL query text")
    parameters: List[str] = Field(default_factory=list, description="Required parameters")
    category: Optional[str] = Field(None, description="Query category")
    tags: List[str] = Field(default_factory=list, description="Query tags")
    
    class Config:
        extra = "allow"


class FocusQueryParameter(BaseModel):
    """Parameter for FOCUS query execution"""
    name: str
    value: Any
    data_type: str


class FocusQueryRequest(BaseModel):
    """Request model for executing FOCUS queries"""
    query_slug: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    limit: Optional[int] = Field(None, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class FocusQueryResponse(BaseModel):
    """Response model for FOCUS query execution"""
    query_slug: str
    rows: List[Dict[str, Any]]
    total_rows: int
    execution_time_ms: float
    parameters_used: Dict[str, Any]


class FocusIngestManifest(BaseModel):
    """
    Manifest entry for tracking processed FOCUS files
    """
    id: str = Field(description="Unique manifest entry ID")
    file_path: str = Field(description="Relative path to processed file")
    file_checksum: str = Field(description="File checksum for change detection")
    dataset_type: str = Field(description="Dataset type (cost_usage or contract_commitment)")
    rows_processed: int = Field(description="Number of rows processed")
    processing_status: str = Field(description="Processing status (success, failed, skipped)")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")
    manifest_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata from manifest.json")

    class Config:
        extra = "allow"


class FocusSupportedFeature(BaseModel):
    """
    FOCUS supported feature metadata
    """
    name: str = Field(description="Feature name")
    title: str = Field(description="Feature title")
    description: str = Field(description="Feature description")
    feature_level: FocusFeatureLevel = Field(description="Feature level")
    content: str = Field(description="Feature content from markdown")
    
    class Config:
        use_enum_values = True