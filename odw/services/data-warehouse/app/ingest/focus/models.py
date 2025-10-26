"""
FOCUS 1.2 Cost and Usage data models for Moose ingestion.

Based on FOCUS specification: /FOCUS_Spec/specification/datasets/cost_and_usage/dataset.md
Parquet schema: Azure FOCUS 1.2 export with extended x_* columns
"""

from moose_lib import Key, IngestPipeline, IngestPipelineConfig
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class FocusCostUsage(BaseModel):
    """FOCUS 1.2 Cost and Usage dataset - snake_case for ClickHouse storage"""

    # Primary key - deterministic hash
    id: Key[str] = Field(
        description="Deterministic hash: billing_account_id + charge_period_start + resource_id + sku_meter"
    )

    # Mandatory dimensions (FOCUS spec)
    billing_account_id: str = Field(description="FOCUS: BillingAccountId (Mandatory)")
    billing_account_name: Optional[str] = Field(
        default=None, description="FOCUS: BillingAccountName (Mandatory, allows nulls)"
    )
    billing_account_type: Optional[str] = Field(
        default=None, description="FOCUS: BillingAccountType (Conditional)"
    )
    billing_currency: str = Field(description="FOCUS: BillingCurrency (Mandatory)")
    billing_period_start: datetime = Field(
        description="FOCUS: BillingPeriodStart (Mandatory)"
    )
    billing_period_end: datetime = Field(
        description="FOCUS: BillingPeriodEnd (Mandatory)"
    )
    charge_period_start: datetime = Field(
        description="FOCUS: ChargePeriodStart (Mandatory)"
    )
    charge_period_end: datetime = Field(description="FOCUS: ChargePeriodEnd (Mandatory)")
    charge_category: str = Field(description="FOCUS: ChargeCategory (Mandatory)")
    charge_class: Optional[str] = Field(
        default=None, description="FOCUS: ChargeClass (Mandatory, allows nulls)"
    )
    charge_description: Optional[str] = Field(
        default=None, description="FOCUS: ChargeDescription (Mandatory, allows nulls)"
    )
    charge_frequency: Optional[str] = Field(
        default=None, description="FOCUS: ChargeFrequency (Recommended)"
    )
    provider_name: str = Field(description="FOCUS: Provider (Mandatory)")
    publisher_name: str = Field(description="FOCUS: Publisher (Mandatory)")
    invoice_issuer_name: str = Field(description="FOCUS: InvoiceIssuer (Mandatory)")
    invoice_id: Optional[str] = Field(
        default=None, description="FOCUS: InvoiceId (Recommended)"
    )
    service_category: str = Field(description="FOCUS: ServiceCategory (Mandatory)")
    service_name: str = Field(description="FOCUS: ServiceName (Mandatory)")
    service_subcategory: Optional[str] = Field(
        default=None, description="FOCUS: ServiceSubcategory (Recommended)"
    )

    # Mandatory metrics (FOCUS spec)
    billed_cost: Decimal = Field(
        description="FOCUS: BilledCost (Mandatory, Decimal(38,18))"
    )
    contracted_cost: Decimal = Field(
        description="FOCUS: ContractedCost (Mandatory, Decimal(38,18))"
    )
    effective_cost: Decimal = Field(
        description="FOCUS: EffectiveCost (Mandatory, Decimal(38,18))"
    )
    list_cost: Decimal = Field(
        description="FOCUS: ListCost (Mandatory, Decimal(38,18))"
    )
    pricing_quantity: Optional[Decimal] = Field(
        default=None, description="FOCUS: PricingQuantity (Mandatory, allows nulls)"
    )
    pricing_unit: Optional[str] = Field(
        default=None, description="FOCUS: PricingUnit (Mandatory, allows nulls)"
    )

    # Conditional/Recommended dimensions (FOCUS spec - allows nulls)
    availability_zone: Optional[str] = Field(
        default=None, description="FOCUS: AvailabilityZone (Recommended)"
    )
    region_id: Optional[str] = Field(
        default=None, description="FOCUS: RegionId (Conditional)"
    )
    region_name: Optional[str] = Field(
        default=None, description="FOCUS: RegionName (Conditional)"
    )
    resource_id: Optional[str] = Field(
        default=None, description="FOCUS: ResourceId (Conditional)"
    )
    resource_name: Optional[str] = Field(
        default=None, description="FOCUS: ResourceName (Conditional)"
    )
    resource_type: Optional[str] = Field(
        default=None, description="FOCUS: ResourceType (Conditional)"
    )
    sku_id: Optional[str] = Field(default=None, description="FOCUS: SkuId (Conditional)")
    sku_meter: Optional[str] = Field(
        default=None, description="FOCUS: SkuMeter (Conditional)"
    )
    sku_price_id: Optional[str] = Field(
        default=None, description="FOCUS: SkuPriceId (Conditional)"
    )
    pricing_category: Optional[str] = Field(
        default=None, description="FOCUS: PricingCategory (Conditional)"
    )
    pricing_currency: Optional[str] = Field(
        default=None, description="FOCUS: PricingCurrency (Conditional)"
    )
    list_unit_price: Optional[Decimal] = Field(
        default=None, description="FOCUS: ListUnitPrice (Conditional)"
    )
    contracted_unit_price: Optional[Decimal] = Field(
        default=None, description="FOCUS: ContractedUnitPrice (Conditional)"
    )

    # Commitment/Discount fields
    capacity_reservation_id: Optional[str] = Field(
        default=None, description="FOCUS: CapacityReservationId (Conditional)"
    )
    capacity_reservation_status: Optional[str] = Field(
        default=None, description="FOCUS: CapacityReservationStatus (Conditional)"
    )
    commitment_discount_category: Optional[str] = Field(
        default=None, description="FOCUS: CommitmentDiscountCategory (Conditional)"
    )
    commitment_discount_id: Optional[str] = Field(
        default=None, description="FOCUS: CommitmentDiscountId (Conditional)"
    )
    commitment_discount_name: Optional[str] = Field(
        default=None, description="FOCUS: CommitmentDiscountName (Conditional)"
    )
    commitment_discount_quantity: Optional[Decimal] = Field(
        default=None, description="FOCUS: CommitmentDiscountQuantity (Conditional)"
    )
    commitment_discount_status: Optional[str] = Field(
        default=None, description="FOCUS: CommitmentDiscountStatus (Conditional)"
    )
    commitment_discount_type: Optional[str] = Field(
        default=None, description="FOCUS: CommitmentDiscountType (Conditional)"
    )
    commitment_discount_unit: Optional[str] = Field(
        default=None, description="FOCUS: CommitmentDiscountUnit (Conditional)"
    )

    # Consumption metrics
    consumed_quantity: Optional[Decimal] = Field(
        default=None, description="FOCUS: ConsumedQuantity (Conditional)"
    )
    consumed_unit: Optional[str] = Field(
        default=None, description="FOCUS: ConsumedUnit (Conditional)"
    )

    # Sub-account fields
    sub_account_id: Optional[str] = Field(
        default=None, description="FOCUS: SubAccountId (Conditional)"
    )
    sub_account_name: Optional[str] = Field(
        default=None, description="FOCUS: SubAccountName (Conditional)"
    )
    sub_account_type: Optional[str] = Field(
        default=None, description="FOCUS: SubAccountType (Conditional)"
    )

    # JSON fields (FOCUS spec)
    tags: Optional[str] = Field(
        default=None, description="FOCUS: Tags (Conditional, JSON as String)"
    )
    sku_price_details: Optional[str] = Field(
        default=None, description="FOCUS: SkuPriceDetails (Conditional, JSON as String)"
    )

    # Extended provider columns (x_* fields from Azure)
    x_account_id: Optional[str] = Field(
        default=None, description="Azure: Account ID"
    )
    x_account_name: Optional[str] = Field(
        default=None, description="Azure: Account Name"
    )
    x_account_owner_id: Optional[str] = Field(
        default=None, description="Azure: Account Owner ID"
    )
    x_amortization_class: Optional[str] = Field(
        default=None, description="Azure: Amortization Class"
    )
    x_billed_cost_in_usd: Optional[Decimal] = Field(
        default=None, description="Azure: Billed Cost in USD"
    )
    x_billed_unit_price: Optional[Decimal] = Field(
        default=None, description="Azure: Billed Unit Price"
    )
    x_billing_account_id: Optional[str] = Field(
        default=None, description="Azure: Billing Account ID (extended)"
    )
    x_billing_account_name: Optional[str] = Field(
        default=None, description="Azure: Billing Account Name (extended)"
    )
    x_billing_exchange_rate: Optional[str] = Field(
        default=None, description="Azure: Billing Exchange Rate"
    )
    x_billing_exchange_rate_date: Optional[datetime] = Field(
        default=None, description="Azure: Billing Exchange Rate Date"
    )
    x_billing_profile_id: Optional[str] = Field(
        default=None, description="Azure: Billing Profile ID"
    )
    x_billing_profile_name: Optional[str] = Field(
        default=None, description="Azure: Billing Profile Name"
    )
    x_contracted_cost_in_usd: Optional[Decimal] = Field(
        default=None, description="Azure: Contracted Cost in USD"
    )
    x_cost_allocation_rule_name: Optional[str] = Field(
        default=None, description="Azure: Cost Allocation Rule Name"
    )
    x_cost_center: Optional[str] = Field(
        default=None, description="Azure: Cost Center"
    )
    x_customer_id: Optional[str] = Field(
        default=None, description="Azure: Customer ID"
    )
    x_customer_name: Optional[str] = Field(
        default=None, description="Azure: Customer Name"
    )
    x_effective_cost_in_usd: Optional[Decimal] = Field(
        default=None, description="Azure: Effective Cost in USD"
    )
    x_effective_unit_price: Optional[Decimal] = Field(
        default=None, description="Azure: Effective Unit Price"
    )
    x_invoice_issuer_id: Optional[str] = Field(
        default=None, description="Azure: Invoice Issuer ID"
    )
    x_invoice_section_id: Optional[str] = Field(
        default=None, description="Azure: Invoice Section ID"
    )
    x_invoice_section_name: Optional[str] = Field(
        default=None, description="Azure: Invoice Section Name"
    )
    x_list_cost_in_usd: Optional[Decimal] = Field(
        default=None, description="Azure: List Cost in USD"
    )
    x_partner_credit_applied: Optional[str] = Field(
        default=None, description="Azure: Partner Credit Applied"
    )
    x_partner_credit_rate: Optional[Decimal] = Field(
        default=None, description="Azure: Partner Credit Rate"
    )
    x_pricing_block_size: Optional[Decimal] = Field(
        default=None, description="Azure: Pricing Block Size"
    )
    x_pricing_subcategory: Optional[str] = Field(
        default=None, description="Azure: Pricing Subcategory"
    )
    x_pricing_unit_description: Optional[str] = Field(
        default=None, description="Azure: Pricing Unit Description"
    )
    x_publisher_category: Optional[str] = Field(
        default=None, description="Azure: Publisher Category"
    )
    x_publisher_id: Optional[str] = Field(
        default=None, description="Azure: Publisher ID"
    )
    x_reseller_id: Optional[str] = Field(
        default=None, description="Azure: Reseller ID"
    )
    x_reseller_name: Optional[str] = Field(
        default=None, description="Azure: Reseller Name"
    )
    x_resource_group_name: Optional[str] = Field(
        default=None, description="Azure: Resource Group Name"
    )
    x_resource_type: Optional[str] = Field(
        default=None, description="Azure: Resource Type (extended)"
    )
    x_service_model: Optional[str] = Field(
        default=None, description="Azure: Service Model"
    )
    x_service_period_end: Optional[datetime] = Field(
        default=None, description="Azure: Service Period End"
    )
    x_service_period_start: Optional[datetime] = Field(
        default=None, description="Azure: Service Period Start"
    )
    x_sku_description: Optional[str] = Field(
        default=None, description="Azure: SKU Description"
    )
    x_sku_details: Optional[str] = Field(
        default=None, description="Azure: SKU Details (JSON)"
    )
    x_sku_is_credit_eligible: Optional[bool] = Field(
        default=None, description="Azure: SKU Is Credit Eligible"
    )
    x_sku_meter_category: Optional[str] = Field(
        default=None, description="Azure: SKU Meter Category"
    )
    x_sku_meter_id: Optional[str] = Field(
        default=None, description="Azure: SKU Meter ID"
    )
    x_sku_meter_subcategory: Optional[str] = Field(
        default=None, description="Azure: SKU Meter Subcategory"
    )
    x_sku_offer_id: Optional[str] = Field(
        default=None, description="Azure: SKU Offer ID"
    )
    x_sku_order_id: Optional[str] = Field(
        default=None, description="Azure: SKU Order ID"
    )
    x_sku_order_name: Optional[str] = Field(
        default=None, description="Azure: SKU Order Name"
    )
    x_sku_part_number: Optional[str] = Field(
        default=None, description="Azure: SKU Part Number"
    )
    x_sku_plan_name: Optional[str] = Field(
        default=None, description="Azure: SKU Plan Name"
    )
    x_sku_region: Optional[str] = Field(
        default=None, description="Azure: SKU Region"
    )
    x_sku_service_family: Optional[str] = Field(
        default=None, description="Azure: SKU Service Family"
    )
    x_sku_term: Optional[str] = Field(
        default=None, description="Azure: SKU Term"
    )
    x_sku_tier: Optional[str] = Field(
        default=None, description="Azure: SKU Tier"
    )

    # Audit fields
    source_system: str = Field(
        default="focus_parquet", description="Source system identifier"
    )
    ingested_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when record was ingested"
    )


# Create Moose IngestPipeline
focusCostUsageModel = IngestPipeline[FocusCostUsage](
    "FocusCostUsage",
    IngestPipelineConfig(
        ingest=True,  # Enable HTTP ingestion endpoint: POST /ingest/FocusCostUsage
        stream=True,  # Create Kafka/Redpanda topic
        table=True,  # Create ClickHouse table: FocusCostUsage_0_0
        dead_letter_queue=True,  # Enable DLQ for failed records
    ),
)
