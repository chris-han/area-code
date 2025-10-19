"""
FOCUS-Compliant Data Models

Implements the FinOps Open Cost and Usage Specification (FOCUS) data model
for standardized cloud billing analytics with ClickHouse optimization.
"""

from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from moose_lib import Key
from pydantic import BaseModel, Field


class FOCUSBillingData(BaseModel):
    """
    FOCUS-compliant billing data model for standardized cost analytics.
    
    This model implements the core FOCUS specification dimensions and measures
    for cloud billing data normalization and analytics with ClickHouse optimization.
    
    ClickHouse Table DDL:
    CREATE TABLE focus_billing_data (
        id String,
        billing_account_id String,
        billing_account_name Nullable(String),
        billing_currency String,
        billing_period_start_date Date,
        billing_period_end_date Date,
        billed_cost Decimal64(4),
        effective_cost Nullable(Decimal64(4)),
        list_cost Nullable(Decimal64(4)),
        list_unit_price Nullable(Decimal64(4)),
        usage_date Date,
        usage_quantity Nullable(Decimal64(4)),
        usage_unit Nullable(String),
        resource_id Nullable(String),
        resource_name Nullable(String),
        resource_type Nullable(String),
        service_category Nullable(String),
        service_name Nullable(String),
        availability_zone Nullable(String),
        region Nullable(String),
        provider String DEFAULT 'Azure',
        created_at DateTime64(3),
        updated_at DateTime64(3),
        source_system String
    ) ENGINE = MergeTree()
    PARTITION BY toYYYYMM(usage_date)
    ORDER BY (usage_date, billing_account_id, service_category, provider)
    SETTINGS index_granularity = 8192;
    """
    
    # Primary key
    id: Key[str] = Field(description="Unique identifier for the billing record")
    
    # FOCUS Required Dimensions
    billing_account_id: str = Field(
        description="Unique identifier for the billing account"
    )
    billing_account_name: Optional[str] = Field(
        description="Display name of the billing account"
    )
    billing_currency: str = Field(
        description="Currency code for billing amounts (ISO 4217)"
    )
    billing_period_start_date: date = Field(
        description="Start date of the billing period"
    )
    billing_period_end_date: date = Field(
        description="End date of the billing period"
    )
    
    # FOCUS Cost Dimensions
    billed_cost: Decimal = Field(
        description="The cost that was charged for this line item"
    )
    effective_cost: Optional[Decimal] = Field(
        description="The amortized cost after applying discounts"
    )
    list_cost: Optional[Decimal] = Field(
        description="The cost without any discounts applied"
    )
    list_unit_price: Optional[Decimal] = Field(
        description="The unit price without discounts"
    )
    
    # FOCUS Usage Dimensions
    usage_date: date = Field(
        description="The date when the resource usage occurred"
    )
    usage_quantity: Optional[Decimal] = Field(
        description="The quantity of the resource that was used"
    )
    usage_unit: Optional[str] = Field(
        description="The unit of measure for the usage quantity"
    )
    
    # FOCUS Resource Dimensions
    resource_id: Optional[str] = Field(
        description="Unique identifier for the resource"
    )
    resource_name: Optional[str] = Field(
        description="Display name of the resource"
    )
    resource_type: Optional[str] = Field(
        description="The type or category of the resource"
    )
    
    # FOCUS Service Dimensions
    service_category: Optional[str] = Field(
        description="High-level category of the service"
    )
    service_name: Optional[str] = Field(
        description="Name of the service that generated the cost"
    )
    
    # FOCUS Geographic Dimensions
    availability_zone: Optional[str] = Field(
        description="Availability zone where the resource is located"
    )
    region: Optional[str] = Field(
        description="Geographic region where the resource is located"
    )
    
    # FOCUS Provider Dimensions
    provider: str = Field(
        default="Azure", description="Cloud provider name"
    )
    
    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record last update timestamp"
    )
    source_system: str = Field(
        description="Source system that provided the data"
    )
    
    class Config:
        """Pydantic model configuration"""
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class FOCUSServiceCategory(BaseModel):
    """
    FOCUS service category dimension table.
    
    ClickHouse Table DDL:
    CREATE TABLE focus_service_category (
        id String,
        category_name String,
        category_description Nullable(String),
        provider String,
        created_at DateTime64(3)
    ) ENGINE = MergeTree()
    ORDER BY (provider, category_name)
    SETTINGS index_granularity = 8192;
    """
    
    id: Key[str] = Field(description="Unique identifier for the service category")
    category_name: str = Field(description="Name of the service category")
    category_description: Optional[str] = Field(
        description="Description of the service category"
    )
    provider: str = Field(description="Cloud provider name")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FOCUSResourceType(BaseModel):
    """
    FOCUS resource type dimension table.
    
    ClickHouse Table DDL:
    CREATE TABLE focus_resource_type (
        id String,
        resource_type_name String,
        resource_type_description Nullable(String),
        service_category_id String,
        provider String,
        created_at DateTime64(3)
    ) ENGINE = MergeTree()
    ORDER BY (provider, service_category_id, resource_type_name)
    SETTINGS index_granularity = 8192;
    """
    
    id: Key[str] = Field(description="Unique identifier for the resource type")
    resource_type_name: str = Field(description="Name of the resource type")
    resource_type_description: Optional[str] = Field(
        description="Description of the resource type"
    )
    service_category_id: str = Field(description="Reference to service category")
    provider: str = Field(description="Cloud provider name")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FOCUSGeography(BaseModel):
    """
    FOCUS geography dimension table.
    
    ClickHouse Table DDL:
    CREATE TABLE focus_geography (
        id String,
        region_name String,
        availability_zone Nullable(String),
        country Nullable(String),
        provider String,
        created_at DateTime64(3)
    ) ENGINE = MergeTree()
    ORDER BY (provider, country, region_name)
    SETTINGS index_granularity = 8192;
    """
    
    id: Key[str] = Field(description="Unique identifier for the geography")
    region_name: str = Field(description="Name of the region")
    availability_zone: Optional[str] = Field(
        description="Availability zone within the region"
    )
    country: Optional[str] = Field(
        description="Country where the region is located"
    )
    provider: str = Field(description="Cloud provider name")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FOCUSBillingAccount(BaseModel):
    """
    FOCUS billing account dimension table.
    
    ClickHouse Table DDL:
    CREATE TABLE focus_billing_account (
        id String,
        account_name String,
        account_type Nullable(String),
        parent_account_id Nullable(String),
        provider String,
        created_at DateTime64(3),
        updated_at DateTime64(3)
    ) ENGINE = MergeTree()
    ORDER BY (provider, id)
    SETTINGS index_granularity = 8192;
    """
    
    id: Key[str] = Field(description="Unique identifier for the billing account")
    account_name: str = Field(description="Display name of the billing account")
    account_type: Optional[str] = Field(
        description="Type of billing account (subscription, enrollment, etc.)"
    )
    parent_account_id: Optional[str] = Field(
        description="Parent account identifier for hierarchical accounts"
    )
    provider: str = Field(description="Cloud provider name")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)