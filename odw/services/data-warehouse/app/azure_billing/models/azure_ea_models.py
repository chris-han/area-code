"""
Azure Enterprise Agreement Source Data Models

Data models for raw Azure EA API billing data before FOCUS transformation.
Provides extensible base classes for custom plugin data models.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from abc import ABC, abstractmethod

from moose_lib import Key
from pydantic import BaseModel, Field, validator


class BaseSourceModel(BaseModel, ABC):
    """
    Abstract base class for all source data models.
    
    Provides common functionality and validation for plugin data models.
    """
    
    # Common metadata fields
    id: Key[str] = Field(description="Unique identifier for the record")
    ingestion_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Data ingestion timestamp"
    )
    source_system: str = Field(description="Source system identifier")
    
    @abstractmethod
    def get_focus_mapping(self) -> Dict[str, str]:
        """
        Return field mapping to FOCUS model.
        
        Returns:
            Dictionary mapping source fields to FOCUS fields
        """
        pass
    
    @abstractmethod
    def validate_business_rules(self) -> List[str]:
        """
        Validate business rules specific to this source model.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        pass
    
    class Config:
        """Pydantic model configuration"""
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class AzureEABillingDetail(BaseSourceModel):
    """
    Azure Enterprise Agreement billing detail source model.
    
    This model represents the raw structure of Azure EA API billing data
    before transformation to FOCUS-compliant format.
    """
    
    # Azure EA API Fields
    account_owner_id: Optional[str] = Field(description="Account owner identifier")
    account_name: Optional[str] = Field(description="Account name")
    subscription_id: Optional[str] = Field(description="Azure subscription ID")
    subscription_guid: Optional[str] = Field(description="Azure subscription GUID")
    subscription_name: Optional[str] = Field(description="Azure subscription name")
    date: Optional[datetime] = Field(description="Usage date")
    product: Optional[str] = Field(description="Product name")
    meter_category: Optional[str] = Field(description="Meter category")
    meter_sub_category: Optional[str] = Field(description="Meter sub-category")
    meter_name: Optional[str] = Field(description="Meter name")
    meter_region: Optional[str] = Field(description="Meter region")
    unit_of_measure: Optional[str] = Field(description="Unit of measure")
    consumed_quantity: Optional[Decimal] = Field(description="Consumed quantity")
    resource_rate: Optional[Decimal] = Field(description="Resource rate")
    extended_cost: Optional[Decimal] = Field(description="Extended cost")
    resource_location: Optional[str] = Field(description="Resource location")
    consumed_service: Optional[str] = Field(description="Consumed service")
    instance_id: Optional[str] = Field(description="Instance ID")
    service_info_1: Optional[str] = Field(description="Service info 1")
    service_info_2: Optional[str] = Field(description="Service info 2")
    additional_info: Optional[str] = Field(description="Additional info")
    tags: Optional[str] = Field(description="Resource tags (JSON string)")
    store_service_identifier: Optional[str] = Field(
        description="Store service identifier"
    )
    department_name: Optional[str] = Field(description="Department name")
    cost_center: Optional[str] = Field(description="Cost center")
    unit_price: Optional[Decimal] = Field(description="Unit price")
    resource_group: Optional[str] = Field(description="Resource group")
    
    # Azure EA specific metadata
    source_file: Optional[str] = Field(
        description="Source file name if applicable"
    )
    api_version: Optional[str] = Field(
        description="Azure EA API version used"
    )
    enrollment_number: Optional[str] = Field(
        description="Azure EA enrollment number"
    )
    
    @validator('extended_cost', 'resource_rate', 'unit_price', 'consumed_quantity')
    def validate_numeric_fields(cls, v):
        """Validate numeric fields are not negative"""
        if v is not None and v < 0:
            raise ValueError('Numeric fields cannot be negative')
        return v
    
    @validator('subscription_id', 'subscription_guid')
    def validate_subscription_fields(cls, v):
        """Validate subscription identifiers"""
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Subscription fields cannot be empty strings')
        return v
    
    def get_focus_mapping(self) -> Dict[str, str]:
        """Return field mapping to FOCUS model"""
        return {
            "subscription_id": "billing_account_id",
            "subscription_name": "billing_account_name",
            "date": "usage_date",
            "extended_cost": "billed_cost",
            "unit_price": "list_unit_price",
            "consumed_quantity": "usage_quantity",
            "unit_of_measure": "usage_unit",
            "instance_id": "resource_id",
            "product": "resource_name",
            "meter_category": "service_category",
            "consumed_service": "service_name",
            "resource_location": "region",
            "meter_region": "availability_zone",
            "resource_rate": "effective_cost"
        }
    
    def validate_business_rules(self) -> List[str]:
        """Validate Azure EA specific business rules"""
        errors = []
        
        # Required fields for FOCUS transformation
        if not self.subscription_id:
            errors.append("subscription_id is required for FOCUS transformation")
        
        if not self.date:
            errors.append("date is required for FOCUS transformation")
        
        if self.extended_cost is None or self.extended_cost == 0:
            errors.append("extended_cost must be greater than 0")
        
        # Validate cost consistency
        if (self.consumed_quantity and self.resource_rate and 
            self.extended_cost and 
            abs(float(self.extended_cost) - 
                (float(self.consumed_quantity) * float(self.resource_rate))) > 0.01):
            errors.append("extended_cost does not match consumed_quantity * resource_rate")
        
        return errors


class AzureEAUsageDetail(BaseSourceModel):
    """
    Azure EA usage detail model for consumption-based resources.
    Enhanced with FOCUS mapping and validation.
    """
    
    # Usage-specific fields
    billing_account_id: Optional[str] = Field(description="Billing account ID")
    billing_account_name: Optional[str] = Field(description="Billing account name")
    billing_period_start_date: Optional[datetime] = Field(
        description="Billing period start"
    )
    billing_period_end_date: Optional[datetime] = Field(
        description="Billing period end"
    )
    billing_profile_id: Optional[str] = Field(description="Billing profile ID")
    billing_profile_name: Optional[str] = Field(description="Billing profile name")
    account_owner_id: Optional[str] = Field(description="Account owner ID")
    account_name: Optional[str] = Field(description="Account name")
    subscription_id: Optional[str] = Field(description="Subscription ID")
    subscription_name: Optional[str] = Field(description="Subscription name")
    date: Optional[datetime] = Field(description="Usage date")
    product: Optional[str] = Field(description="Product")
    part_number: Optional[str] = Field(description="Part number")
    meter_id: Optional[str] = Field(description="Meter ID")
    meter_details: Optional[str] = Field(description="Meter details (JSON)")
    quantity: Optional[Decimal] = Field(description="Usage quantity")
    effective_price: Optional[Decimal] = Field(description="Effective price")
    cost: Optional[Decimal] = Field(description="Cost")
    unit_price: Optional[Decimal] = Field(description="Unit price")
    billing_currency: Optional[str] = Field(description="Billing currency")
    resource_location: Optional[str] = Field(description="Resource location")
    availability_zone: Optional[str] = Field(description="Availability zone")
    consumed_service: Optional[str] = Field(description="Consumed service")
    resource_id: Optional[str] = Field(description="Resource ID")
    resource_name: Optional[str] = Field(description="Resource name")
    service_info_1: Optional[str] = Field(description="Service info 1")
    service_info_2: Optional[str] = Field(description="Service info 2")
    additional_info: Optional[str] = Field(description="Additional info")
    invoice_section_id: Optional[str] = Field(description="Invoice section ID")
    invoice_section_name: Optional[str] = Field(description="Invoice section name")
    cost_center: Optional[str] = Field(description="Cost center")
    resource_group: Optional[str] = Field(description="Resource group")
    reservation_id: Optional[str] = Field(description="Reservation ID")
    reservation_name: Optional[str] = Field(description="Reservation name")
    product_order_id: Optional[str] = Field(description="Product order ID")
    product_order_name: Optional[str] = Field(description="Product order name")
    offer_id: Optional[str] = Field(description="Offer ID")
    is_azure_credit_eligible: Optional[bool] = Field(
        description="Is Azure credit eligible"
    )
    term: Optional[str] = Field(description="Term")
    publisher_name: Optional[str] = Field(description="Publisher name")
    publisher_type: Optional[str] = Field(description="Publisher type")
    plan_name: Optional[str] = Field(description="Plan name")
    charge_type: Optional[str] = Field(description="Charge type")
    frequency: Optional[str] = Field(description="Frequency")
    
    @validator('cost', 'effective_price', 'unit_price', 'quantity')
    def validate_numeric_fields(cls, v):
        """Validate numeric fields are not negative"""
        if v is not None and v < 0:
            raise ValueError('Numeric fields cannot be negative')
        return v
    
    @validator('billing_currency')
    def validate_currency(cls, v):
        """Validate currency code format"""
        if v is not None and len(v) != 3:
            raise ValueError('Currency code must be 3 characters (ISO 4217)')
        return v
    
    def get_focus_mapping(self) -> Dict[str, str]:
        """Return field mapping to FOCUS model"""
        return {
            "billing_account_id": "billing_account_id",
            "billing_account_name": "billing_account_name",
            "date": "usage_date",
            "cost": "billed_cost",
            "effective_price": "list_unit_price",
            "quantity": "usage_quantity",
            "resource_id": "resource_id",
            "resource_name": "resource_name",
            "consumed_service": "service_name",
            "resource_location": "region",
            "availability_zone": "availability_zone",
            "billing_currency": "billing_currency"
        }
    
    def validate_business_rules(self) -> List[str]:
        """Validate Azure EA usage detail business rules"""
        errors = []
        
        # Required fields for FOCUS transformation
        if not self.billing_account_id and not self.subscription_id:
            errors.append(
                "Either billing_account_id or subscription_id is required"
            )
        
        if not self.date:
            errors.append("date is required for FOCUS transformation")
        
        if self.cost is None or self.cost == 0:
            errors.append("cost must be greater than 0")
        
        # Validate billing period consistency
        if (self.billing_period_start_date and self.billing_period_end_date and
            self.billing_period_start_date > self.billing_period_end_date):
            errors.append(
                "billing_period_start_date cannot be after billing_period_end_date"
            )
        
        return errors


class CustomPluginSourceModel(BaseSourceModel):
    """
    Generic source model for custom plugin data.
    
    Provides flexible structure for plugin-specific data sources
    while maintaining FOCUS transformation compatibility.
    """
    
    # Flexible data container
    raw_data: Dict[str, Any] = Field(
        description="Raw data from custom plugin source"
    )
    plugin_name: str = Field(description="Name of the plugin that provided the data")
    plugin_version: str = Field(description="Version of the plugin")
    schema_version: Optional[str] = Field(description="Data schema version")
    
    # Common billing fields (mapped from raw_data)
    account_identifier: Optional[str] = Field(
        description="Account identifier (plugin-specific)"
    )
    usage_date: Optional[datetime] = Field(description="Usage date")
    cost_amount: Optional[Decimal] = Field(description="Cost amount")
    currency_code: Optional[str] = Field(description="Currency code")
    service_identifier: Optional[str] = Field(
        description="Service identifier (plugin-specific)"
    )
    resource_identifier: Optional[str] = Field(
        description="Resource identifier (plugin-specific)"
    )
    
    def get_focus_mapping(self) -> Dict[str, str]:
        """Return field mapping to FOCUS model (customizable per plugin)"""
        return {
            "account_identifier": "billing_account_id",
            "usage_date": "usage_date",
            "cost_amount": "billed_cost",
            "currency_code": "billing_currency",
            "service_identifier": "service_name",
            "resource_identifier": "resource_id"
        }
    
    def validate_business_rules(self) -> List[str]:
        """Validate custom plugin business rules"""
        errors = []
        
        # Basic validation for FOCUS transformation
        if not self.account_identifier:
            errors.append("account_identifier is required for FOCUS transformation")
        
        if not self.usage_date:
            errors.append("usage_date is required for FOCUS transformation")
        
        if self.cost_amount is None or self.cost_amount <= 0:
            errors.append("cost_amount must be greater than 0")
        
        return errors