"""
FOCUS Supported Features - Moose Consumption APIs

Implements consumption APIs for FOCUS supported features based on specification.
All queries target the cost_and_usage dataset (FocusCostUsage_0_0 table).
"""

from moose_lib import ConsumptionApi, ConsumptionApiConfig
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal


# Request/Response models for Cost Comparison API
class CostComparisonRequest(BaseModel):
    """Request parameters for cost comparison analysis"""
    billing_period_start: date = Field(description="Start date for billing period")
    billing_period_end: date = Field(description="End date for billing period")
    provider_name: Optional[str] = Field(default=None, description="Filter by provider")
    service_name: Optional[str] = Field(default=None, description="Filter by service")


class CostComparisonRow(BaseModel):
    """Cost comparison result row"""
    provider_name: str
    billing_account_id: str
    billing_account_name: Optional[str]
    billing_currency: str
    service_name: str
    total_effective_cost: Decimal
    total_billed_cost: Decimal
    total_list_cost: Decimal
    contracted_discount: Optional[Decimal]
    effective_discount: Optional[Decimal]


# Request/Response models for Effective Cost Analysis API
class EffectiveCostAnalysisRequest(BaseModel):
    """Request parameters for effective cost analysis"""
    billing_period_start: date = Field(description="Start date for billing period")
    billing_period_end: date = Field(description="End date for billing period")
    provider_name: Optional[str] = Field(default=None, description="Filter by provider")
    service_category: Optional[str] = Field(default=None, description="Filter by service category")
    region_name: Optional[str] = Field(default=None, description="Filter by region")


class EffectiveCostAnalysisRow(BaseModel):
    """Effective cost analysis result row"""
    provider_name: str
    billing_period_start: date
    billing_period_end: date
    service_category: str
    service_name: str
    region_id: Optional[str]
    region_name: Optional[str]
    pricing_unit: Optional[str]
    total_effective_cost: Decimal
    total_pricing_quantity: Optional[Decimal]


# Request/Response models for Charge Categorization APIs
class ChargeCategoryRequest(BaseModel):
    """Request parameters for charge categorization queries"""
    billing_period_start: date = Field(description="Start date for billing period")
    billing_period_end: date = Field(description="End date for billing period")
    charge_category: Optional[str] = Field(default=None, description="Filter by charge category")
    charge_class: Optional[str] = Field(default=None, description="Filter by charge class")
    provider_name: Optional[str] = Field(default=None, description="Filter by provider")


class CommitmentDiscountPurchaseRow(BaseModel):
    """Commitment discount purchase result row"""
    charge_period_start: date
    charge_period_end: date
    provider_name: str
    billing_account_id: str
    commitment_discount_id: Optional[str]
    commitment_discount_type: Optional[str]
    commitment_discount_unit: Optional[str]
    commitment_discount_quantity: Optional[Decimal]
    charge_frequency: Optional[str]
    total_billed_cost: Decimal


class CorrectionRow(BaseModel):
    """Correction charges result row"""
    provider_name: str
    billing_account_id: str
    charge_category: str
    service_category: str
    service_name: str
    total_billed_cost: Decimal


class RecurringChargeRow(BaseModel):
    """Recurring charges result row"""
    billing_period_start: date
    commitment_discount_id: Optional[str]
    commitment_discount_name: Optional[str]
    commitment_discount_type: Optional[str]
    charge_frequency: Optional[str]
    total_billed_cost: Decimal


# API 1: Cost Comparison Analysis
def get_cost_comparison(client, request: CostComparisonRequest) -> List[CostComparisonRow]:
    """
    Compare cost columns to identify savings, amortization, and discounts.

    FOCUS Feature: Cost Comparison
    Reference: FOCUS_Spec/specification/supported_features/cost_comparison.md
    """
    provider_filter = f"AND provider_name = '{request.provider_name}'" if request.provider_name else ""
    service_filter = f"AND service_name = '{request.service_name}'" if request.service_name else ""

    query = f"""
        WITH AggregatedData AS (
            SELECT
                provider_name,
                billing_account_id,
                billing_account_name,
                billing_currency,
                service_name,
                SUM(effective_cost) AS total_effective_cost,
                SUM(billed_cost) AS total_billed_cost,
                SUM(CASE
                    WHEN charge_category = 'Usage' AND billed_cost = 0 AND effective_cost != 0
                    THEN 0
                    ELSE contracted_cost
                END) AS total_contracted_cost,
                SUM(CASE
                    WHEN charge_category = 'Usage' AND billed_cost = 0 AND effective_cost != 0
                    THEN 0
                    ELSE list_cost
                END) AS total_list_cost
            FROM FocusCostUsage_0_0
            WHERE billing_period_start >= '{request.billing_period_start}'
                AND billing_period_end < '{request.billing_period_end}'
                AND charge_class IS NULL
                {provider_filter}
                {service_filter}
            GROUP BY
                provider_name,
                billing_account_id,
                billing_account_name,
                billing_currency,
                service_name
        )
        SELECT
            provider_name,
            billing_account_id,
            billing_account_name,
            billing_currency,
            service_name,
            total_effective_cost,
            total_billed_cost,
            total_list_cost,
            (1 - (total_contracted_cost / NULLIF(total_list_cost, 0))) * 100 AS contracted_discount,
            (1 - (total_effective_cost / NULLIF(total_list_cost, 0))) * 100 AS effective_discount
        FROM AggregatedData
    """

    result = client.query(query)
    return [CostComparisonRow(**row) for row in result.named_results()]


# API 2: Effective Cost Analysis
def get_effective_cost_analysis(client, request: EffectiveCostAnalysisRequest) -> List[EffectiveCostAnalysisRow]:
    """
    Analyze costs after discounts and amortization of prepaid purchases.

    FOCUS Feature: Effective Cost Analysis
    Reference: FOCUS_Spec/specification/supported_features/effective_cost.md
    """
    provider_filter = f"AND provider_name = '{request.provider_name}'" if request.provider_name else ""
    category_filter = f"AND service_category = '{request.service_category}'" if request.service_category else ""
    region_filter = f"AND region_name = '{request.region_name}'" if request.region_name else ""

    query = f"""
        SELECT
            provider_name,
            billing_period_start,
            billing_period_end,
            service_category,
            service_name,
            region_id,
            region_name,
            pricing_unit,
            SUM(effective_cost) AS total_effective_cost,
            SUM(pricing_quantity) AS total_pricing_quantity
        FROM FocusCostUsage_0_0
        WHERE billing_period_start >= '{request.billing_period_start}'
            AND billing_period_end <= '{request.billing_period_end}'
            {provider_filter}
            {category_filter}
            {region_filter}
        GROUP BY
            provider_name,
            billing_period_start,
            billing_period_end,
            service_category,
            service_name,
            region_id,
            region_name,
            pricing_unit
    """

    result = client.query(query)
    return [EffectiveCostAnalysisRow(**row) for row in result.named_results()]


# API 3: Commitment Discount Purchases
def get_commitment_discount_purchases(client, request: ChargeCategoryRequest) -> List[CommitmentDiscountPurchaseRow]:
    """
    Report on commitment discount purchases (reservations, savings plans).

    FOCUS Feature: Charge Categorization
    Reference: FOCUS_Spec/specification/supported_features/charge_categorization.md
    """
    provider_filter = f"AND provider_name = '{request.provider_name}'" if request.provider_name else ""

    query = f"""
        SELECT
            MIN(charge_period_start) AS charge_period_start,
            MAX(charge_period_end) AS charge_period_end,
            provider_name,
            billing_account_id,
            commitment_discount_id,
            commitment_discount_type,
            commitment_discount_unit,
            commitment_discount_quantity,
            charge_frequency,
            SUM(billed_cost) AS total_billed_cost
        FROM FocusCostUsage_0_0
        WHERE charge_period_start >= '{request.billing_period_start}'
            AND charge_period_end < '{request.billing_period_end}'
            AND charge_category = 'Purchase'
            AND commitment_discount_id IS NOT NULL
            {provider_filter}
        GROUP BY
            provider_name,
            billing_account_id,
            commitment_discount_id,
            commitment_discount_type,
            commitment_discount_unit,
            commitment_discount_quantity,
            charge_frequency
    """

    result = client.query(query)
    return [CommitmentDiscountPurchaseRow(**row) for row in result.named_results()]


# API 4: Correction Charges
def get_correction_charges(client, request: ChargeCategoryRequest) -> List[CorrectionRow]:
    """
    Report on correction charges to identify billing adjustments.

    FOCUS Feature: Charge Categorization
    Reference: FOCUS_Spec/specification/supported_features/charge_categorization.md
    """
    provider_filter = f"AND provider_name = '{request.provider_name}'" if request.provider_name else ""

    query = f"""
        SELECT
            provider_name,
            billing_account_id,
            charge_category,
            service_category,
            service_name,
            SUM(billed_cost) AS total_billed_cost
        FROM FocusCostUsage_0_0
        WHERE billing_period_start >= '{request.billing_period_start}'
            AND billing_period_end < '{request.billing_period_end}'
            AND charge_class = 'Correction'
            {provider_filter}
        GROUP BY
            provider_name,
            billing_account_id,
            charge_category,
            service_category,
            service_name
    """

    result = client.query(query)
    return [CorrectionRow(**row) for row in result.named_results()]


# API 5: Recurring Charges
def get_recurring_charges(client, request: ChargeCategoryRequest) -> List[RecurringChargeRow]:
    """
    Report on recurring charges for commitment discounts.

    FOCUS Feature: Charge Categorization
    Reference: FOCUS_Spec/specification/supported_features/charge_categorization.md
    """
    provider_filter = f"AND provider_name = '{request.provider_name}'" if request.provider_name else ""

    query = f"""
        SELECT
            billing_period_start,
            commitment_discount_id,
            commitment_discount_name,
            commitment_discount_type,
            charge_frequency,
            SUM(billed_cost) AS total_billed_cost
        FROM FocusCostUsage_0_0
        WHERE billing_period_start >= '{request.billing_period_start}'
            AND billing_period_start < '{request.billing_period_end}'
            AND charge_frequency = 'Recurring'
            AND commitment_discount_id IS NOT NULL
            {provider_filter}
        GROUP BY
            billing_period_start,
            commitment_discount_id,
            commitment_discount_name,
            commitment_discount_type,
            charge_frequency
    """

    result = client.query(query)
    return [RecurringChargeRow(**row) for row in result.named_results()]


# Register Moose Consumption APIs
cost_comparison_api = ConsumptionApi[CostComparisonRequest, List[CostComparisonRow]](
    name="CostComparison",
    query_function=get_cost_comparison,
    config=ConsumptionApiConfig()
)

effective_cost_analysis_api = ConsumptionApi[EffectiveCostAnalysisRequest, List[EffectiveCostAnalysisRow]](
    name="EffectiveCostAnalysis",
    query_function=get_effective_cost_analysis,
    config=ConsumptionApiConfig()
)

commitment_discount_purchases_api = ConsumptionApi[ChargeCategoryRequest, List[CommitmentDiscountPurchaseRow]](
    name="CommitmentDiscountPurchases",
    query_function=get_commitment_discount_purchases,
    config=ConsumptionApiConfig()
)

correction_charges_api = ConsumptionApi[ChargeCategoryRequest, List[CorrectionRow]](
    name="CorrectionCharges",
    query_function=get_correction_charges,
    config=ConsumptionApiConfig()
)

recurring_charges_api = ConsumptionApi[ChargeCategoryRequest, List[RecurringChargeRow]](
    name="RecurringCharges",
    query_function=get_recurring_charges,
    config=ConsumptionApiConfig()
)


# Additional API Models

class ResourceUsageRequest(BaseModel):
    """Request parameters for resource usage tracking"""
    billing_period_start: date
    billing_period_end: date
    service_name: Optional[str] = None
    provider_name: Optional[str] = None


class ResourceUsageRow(BaseModel):
    """Resource usage result row"""
    provider_name: str
    service_name: str
    resource_id: Optional[str]
    sku_id: Optional[str]
    consumed_unit: Optional[str]
    total_quantity: Optional[Decimal]


class ServiceCategorizationRequest(BaseModel):
    """Request parameters for service categorization"""
    billing_period_start: date
    billing_period_end: date
    provider_name: Optional[str] = None
    service_category: Optional[str] = None


class ServiceCategorizationRow(BaseModel):
    """Service categorization result row"""
    billing_period_start: date
    billing_period_end: date
    provider_name: str
    service_category: str
    service_subcategory: Optional[str]
    service_name: str
    billing_currency: str
    total_billed_cost: Decimal


class LocationRequest(BaseModel):
    """Request parameters for location analysis"""
    billing_period_start: date
    billing_period_end: date
    region_name: Optional[str] = None


class LocationRow(BaseModel):
    """Location analysis result row"""
    region_id: Optional[str]
    region_name: Optional[str]
    availability_zone: Optional[str]
    total_billed_cost: Decimal


class AccountStructureRequest(BaseModel):
    """Request parameters for account structure analysis"""
    billing_period_start: date
    billing_period_end: date
    billing_account_id: Optional[str] = None


class AccountStructureRow(BaseModel):
    """Account structure result row"""
    billing_account_id: str
    billing_account_name: Optional[str]
    billing_account_type: Optional[str]
    sub_account_id: Optional[str]
    sub_account_name: Optional[str]
    sub_account_type: Optional[str]
    total_billed_cost: Decimal


class CommitmentUsageRequest(BaseModel):
    """Request parameters for commitment usage tracking"""
    billing_period_start: date
    billing_period_end: date
    commitment_discount_status: Optional[str] = None


class CommitmentUsageRow(BaseModel):
    """Commitment usage result row"""
    provider_name: str
    billing_account_id: str
    commitment_discount_id: Optional[str]
    commitment_discount_type: Optional[str]
    commitment_discount_status: Optional[str]
    total_billed_cost: Decimal
    total_effective_cost: Decimal


class MarketplacePurchaseRequest(BaseModel):
    """Request parameters for marketplace purchases"""
    billing_period_start: date
    billing_period_end: date
    publisher_name: Optional[str] = None


class MarketplacePurchaseRow(BaseModel):
    """Marketplace purchase result row"""
    provider_name: str
    publisher_name: str
    service_name: str
    charge_category: str
    total_billed_cost: Decimal


class UnitPriceRequest(BaseModel):
    """Request parameters for unit price analysis"""
    billing_period_start: date
    billing_period_end: date
    service_name: Optional[str] = None


class UnitPriceRow(BaseModel):
    """Unit price analysis result row"""
    service_name: str
    sku_id: Optional[str]
    pricing_unit: Optional[str]
    list_unit_price: Optional[Decimal]
    contracted_unit_price: Optional[Decimal]
    total_pricing_quantity: Optional[Decimal]


class InvoiceAlignmentRequest(BaseModel):
    """Request parameters for invoice alignment"""
    billing_period_start: date
    billing_period_end: date
    invoice_id: Optional[str] = None


class InvoiceAlignmentRow(BaseModel):
    """Invoice alignment result row"""
    invoice_issuer_name: str
    billing_account_id: str
    billing_currency: str
    invoice_id: Optional[str]
    total_billed_cost: Decimal


class CostAttributionRequest(BaseModel):
    """Request parameters for cost attribution via tags"""
    billing_period_start: date
    billing_period_end: date
    tag_key: Optional[str] = None


class CostAttributionRow(BaseModel):
    """Cost attribution result row"""
    billing_account_id: str
    service_name: str
    resource_id: Optional[str]
    tags: Optional[str]
    total_billed_cost: Decimal


# API 6: Resource Usage
def get_resource_usage(client, request: ResourceUsageRequest) -> List[ResourceUsageRow]:
    """
    Track resource consumption with quantities and units.

    FOCUS Feature: Resource Usage
    """
    service_filter = f"AND service_name = '{request.service_name}'" if request.service_name else ""
    provider_filter = f"AND provider_name = '{request.provider_name}'" if request.provider_name else ""

    query = f"""
        SELECT
            provider_name,
            service_name,
            resource_id,
            sku_id,
            consumed_unit,
            SUM(consumed_quantity) AS total_quantity
        FROM FocusCostUsage_0_0
        WHERE charge_category = 'Usage'
            AND charge_period_start >= '{request.billing_period_start}'
            AND charge_period_end <= '{request.billing_period_end}'
            {service_filter}
            {provider_filter}
        GROUP BY
            provider_name,
            service_name,
            resource_id,
            sku_id,
            consumed_unit
    """

    result = client.query(query)
    return [ResourceUsageRow(**row) for row in result.named_results()]


# API 7: Service Categorization
def get_service_categorization(client, request: ServiceCategorizationRequest) -> List[ServiceCategorizationRow]:
    """
    Organize costs by service categories and subcategories.

    FOCUS Feature: Service Categorization
    """
    provider_filter = f"AND provider_name = '{request.provider_name}'" if request.provider_name else ""
    category_filter = f"AND service_category = '{request.service_category}'" if request.service_category else ""

    query = f"""
        SELECT
            billing_period_start,
            billing_period_end,
            provider_name,
            service_category,
            service_subcategory,
            service_name,
            billing_currency,
            SUM(billed_cost) AS total_billed_cost
        FROM FocusCostUsage_0_0
        WHERE billing_period_start >= '{request.billing_period_start}'
            AND billing_period_end < '{request.billing_period_end}'
            {provider_filter}
            {category_filter}
        GROUP BY
            billing_period_start,
            billing_period_end,
            provider_name,
            service_category,
            service_subcategory,
            service_name,
            billing_currency
    """

    result = client.query(query)
    return [ServiceCategorizationRow(**row) for row in result.named_results()]


# API 8: Location Analysis
def get_location_costs(client, request: LocationRequest) -> List[LocationRow]:
    """
    Analyze costs by geographic location (region, availability zone).

    FOCUS Feature: Location
    """
    region_filter = f"AND region_name = '{request.region_name}'" if request.region_name else ""

    query = f"""
        SELECT
            region_id,
            region_name,
            availability_zone,
            SUM(billed_cost) AS total_billed_cost
        FROM FocusCostUsage_0_0
        WHERE charge_period_start >= '{request.billing_period_start}'
            AND charge_period_end <= '{request.billing_period_end}'
            {region_filter}
        GROUP BY
            region_id,
            region_name,
            availability_zone
    """

    result = client.query(query)
    return [LocationRow(**row) for row in result.named_results()]


# API 9: Account Structure
def get_account_costs(client, request: AccountStructureRequest) -> List[AccountStructureRow]:
    """
    Break down costs by billing accounts and sub-accounts.

    FOCUS Feature: Account Structures
    """
    account_filter = f"AND billing_account_id = '{request.billing_account_id}'" if request.billing_account_id else ""

    query = f"""
        SELECT
            billing_account_id,
            billing_account_name,
            billing_account_type,
            sub_account_id,
            sub_account_name,
            sub_account_type,
            SUM(billed_cost) AS total_billed_cost
        FROM FocusCostUsage_0_0
        WHERE billing_period_start >= '{request.billing_period_start}'
            AND billing_period_end < '{request.billing_period_end}'
            {account_filter}
        GROUP BY
            billing_account_id,
            billing_account_name,
            billing_account_type,
            sub_account_id,
            sub_account_name,
            sub_account_type
    """

    result = client.query(query)
    return [AccountStructureRow(**row) for row in result.named_results()]


# API 10: Commitment Usage and Under-usage
def get_commitment_usage(client, request: CommitmentUsageRequest) -> List[CommitmentUsageRow]:
    """
    Track commitment discount usage and identify under-utilized commitments.

    FOCUS Feature: Commit Usage and Under Usage
    """
    status_filter = f"AND commitment_discount_status = '{request.commitment_discount_status}'" if request.commitment_discount_status else ""

    query = f"""
        SELECT
            provider_name,
            billing_account_id,
            commitment_discount_id,
            commitment_discount_type,
            commitment_discount_status,
            SUM(billed_cost) AS total_billed_cost,
            SUM(effective_cost) AS total_effective_cost
        FROM FocusCostUsage_0_0
        WHERE charge_period_start >= '{request.billing_period_start}'
            AND charge_period_end < '{request.billing_period_end}'
            AND commitment_discount_id IS NOT NULL
            {status_filter}
        GROUP BY
            provider_name,
            billing_account_id,
            commitment_discount_id,
            commitment_discount_type,
            commitment_discount_status
    """

    result = client.query(query)
    return [CommitmentUsageRow(**row) for row in result.named_results()]


# API 11: Marketplace Purchases
def get_marketplace_purchases(client, request: MarketplacePurchaseRequest) -> List[MarketplacePurchaseRow]:
    """
    Report on third-party marketplace purchases.

    FOCUS Feature: Marketplace Purchases
    """
    publisher_filter = f"AND publisher_name = '{request.publisher_name}'" if request.publisher_name else ""

    query = f"""
        SELECT
            provider_name,
            publisher_name,
            service_name,
            charge_category,
            SUM(billed_cost) AS total_billed_cost
        FROM FocusCostUsage_0_0
        WHERE billing_period_start >= '{request.billing_period_start}'
            AND billing_period_end < '{request.billing_period_end}'
            AND publisher_name != provider_name
            {publisher_filter}
        GROUP BY
            provider_name,
            publisher_name,
            service_name,
            charge_category
    """

    result = client.query(query)
    return [MarketplacePurchaseRow(**row) for row in result.named_results()]


# API 12: Unit Price Verification
def get_unit_prices(client, request: UnitPriceRequest) -> List[UnitPriceRow]:
    """
    Verify, compare, and track unit prices over time.

    FOCUS Feature: Verify Compare Track Unit Prices
    """
    service_filter = f"AND service_name = '{request.service_name}'" if request.service_name else ""

    query = f"""
        SELECT
            service_name,
            sku_id,
            pricing_unit,
            AVG(list_unit_price) AS list_unit_price,
            AVG(contracted_unit_price) AS contracted_unit_price,
            SUM(pricing_quantity) AS total_pricing_quantity
        FROM FocusCostUsage_0_0
        WHERE billing_period_start >= '{request.billing_period_start}'
            AND billing_period_end < '{request.billing_period_end}'
            AND pricing_quantity IS NOT NULL
            {service_filter}
        GROUP BY
            service_name,
            sku_id,
            pricing_unit
    """

    result = client.query(query)
    return [UnitPriceRow(**row) for row in result.named_results()]


# API 13: Invoice Alignment
def get_invoice_alignment(client, request: InvoiceAlignmentRequest) -> List[InvoiceAlignmentRow]:
    """
    Reconcile billed costs with invoices.

    FOCUS Feature: Billed Cost and Invoice Alignment
    """
    invoice_filter = f"AND invoice_id = '{request.invoice_id}'" if request.invoice_id else ""

    query = f"""
        SELECT
            invoice_issuer_name,
            billing_account_id,
            billing_currency,
            invoice_id,
            SUM(billed_cost) AS total_billed_cost
        FROM FocusCostUsage_0_0
        WHERE billing_period_start >= '{request.billing_period_start}'
            AND billing_period_end < '{request.billing_period_end}'
            {invoice_filter}
        GROUP BY
            invoice_issuer_name,
            billing_account_id,
            billing_currency,
            invoice_id
    """

    result = client.query(query)
    return [InvoiceAlignmentRow(**row) for row in result.named_results()]


# API 14: Cost Attribution (Tag-based)
def get_cost_attribution(client, request: CostAttributionRequest) -> List[CostAttributionRow]:
    """
    Attribute costs using tags for chargeback/showback.

    FOCUS Feature: Cost and Usage Attribution
    """
    query = f"""
        SELECT
            billing_account_id,
            service_name,
            resource_id,
            tags,
            SUM(billed_cost) AS total_billed_cost
        FROM FocusCostUsage_0_0
        WHERE billing_period_start >= '{request.billing_period_start}'
            AND billing_period_end < '{request.billing_period_end}'
            AND tags IS NOT NULL
        GROUP BY
            billing_account_id,
            service_name,
            resource_id,
            tags
    """

    result = client.query(query)
    return [CostAttributionRow(**row) for row in result.named_results()]


# Register additional Moose Consumption APIs
resource_usage_api = ConsumptionApi[ResourceUsageRequest, List[ResourceUsageRow]](
    name="ResourceUsage",
    query_function=get_resource_usage,
    config=ConsumptionApiConfig()
)

service_categorization_api = ConsumptionApi[ServiceCategorizationRequest, List[ServiceCategorizationRow]](
    name="ServiceCategorization",
    query_function=get_service_categorization,
    config=ConsumptionApiConfig()
)

location_costs_api = ConsumptionApi[LocationRequest, List[LocationRow]](
    name="LocationCosts",
    query_function=get_location_costs,
    config=ConsumptionApiConfig()
)

account_costs_api = ConsumptionApi[AccountStructureRequest, List[AccountStructureRow]](
    name="AccountCosts",
    query_function=get_account_costs,
    config=ConsumptionApiConfig()
)

commitment_usage_api = ConsumptionApi[CommitmentUsageRequest, List[CommitmentUsageRow]](
    name="CommitmentUsage",
    query_function=get_commitment_usage,
    config=ConsumptionApiConfig()
)

marketplace_purchases_api = ConsumptionApi[MarketplacePurchaseRequest, List[MarketplacePurchaseRow]](
    name="MarketplacePurchases",
    query_function=get_marketplace_purchases,
    config=ConsumptionApiConfig()
)

unit_prices_api = ConsumptionApi[UnitPriceRequest, List[UnitPriceRow]](
    name="UnitPrices",
    query_function=get_unit_prices,
    config=ConsumptionApiConfig()
)

invoice_alignment_api = ConsumptionApi[InvoiceAlignmentRequest, List[InvoiceAlignmentRow]](
    name="InvoiceAlignment",
    query_function=get_invoice_alignment,
    config=ConsumptionApiConfig()
)

cost_attribution_api = ConsumptionApi[CostAttributionRequest, List[CostAttributionRow]](
    name="CostAttribution",
    query_function=get_cost_attribution,
    config=ConsumptionApiConfig()
)
