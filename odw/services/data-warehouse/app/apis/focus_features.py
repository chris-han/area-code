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
def get_cost_comparison(request: CostComparisonRequest) -> List[CostComparisonRow]:
    """
    Compare cost columns to identify savings, amortization, and discounts.

    FOCUS Feature: Cost Comparison
    Reference: FOCUS_Spec/specification/supported_features/cost_comparison.md
    """
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
            WHERE billing_period_start >= {{{{ billing_period_start }}}}
                AND billing_period_end < {{{{ billing_period_end }}}}
                AND charge_class IS NULL
                {{{{ 'AND provider_name = ' + provider_name if provider_name else '' }}}}
                {{{{ 'AND service_name = ' + service_name if service_name else '' }}}}
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
    return []


# API 2: Effective Cost Analysis
def get_effective_cost_analysis(request: EffectiveCostAnalysisRequest) -> List[EffectiveCostAnalysisRow]:
    """
    Analyze costs after discounts and amortization of prepaid purchases.

    FOCUS Feature: Effective Cost Analysis
    Reference: FOCUS_Spec/specification/supported_features/effective_cost.md
    """
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
        WHERE billing_period_start >= {{{{ billing_period_start }}}}
            AND billing_period_end <= {{{{ billing_period_end }}}}
            {{{{ 'AND provider_name = ' + provider_name if provider_name else '' }}}}
            {{{{ 'AND service_category = ' + service_category if service_category else '' }}}}
            {{{{ 'AND region_name = ' + region_name if region_name else '' }}}}
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
    return []


# API 3: Commitment Discount Purchases
def get_commitment_discount_purchases(request: ChargeCategoryRequest) -> List[CommitmentDiscountPurchaseRow]:
    """
    Report on commitment discount purchases (reservations, savings plans).

    FOCUS Feature: Charge Categorization
    Reference: FOCUS_Spec/specification/supported_features/charge_categorization.md
    """
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
        WHERE charge_period_start >= {{{{ billing_period_start }}}}
            AND charge_period_end < {{{{ billing_period_end }}}}
            AND charge_category = 'Purchase'
            AND commitment_discount_id IS NOT NULL
            {{{{ 'AND provider_name = ' + provider_name if provider_name else '' }}}}
        GROUP BY
            provider_name,
            billing_account_id,
            commitment_discount_id,
            commitment_discount_type,
            commitment_discount_unit,
            commitment_discount_quantity,
            charge_frequency
    """
    return []


# API 4: Correction Charges
def get_correction_charges(request: ChargeCategoryRequest) -> List[CorrectionRow]:
    """
    Report on correction charges to identify billing adjustments.

    FOCUS Feature: Charge Categorization
    Reference: FOCUS_Spec/specification/supported_features/charge_categorization.md
    """
    query = f"""
        SELECT
            provider_name,
            billing_account_id,
            charge_category,
            service_category,
            service_name,
            SUM(billed_cost) AS total_billed_cost
        FROM FocusCostUsage_0_0
        WHERE billing_period_start >= {{{{ billing_period_start }}}}
            AND billing_period_end < {{{{ billing_period_end }}}}
            AND charge_class = 'Correction'
            {{{{ 'AND provider_name = ' + provider_name if provider_name else '' }}}}
        GROUP BY
            provider_name,
            billing_account_id,
            charge_category,
            service_category,
            service_name
    """
    return []


# API 5: Recurring Charges
def get_recurring_charges(request: ChargeCategoryRequest) -> List[RecurringChargeRow]:
    """
    Report on recurring charges for commitment discounts.

    FOCUS Feature: Charge Categorization
    Reference: FOCUS_Spec/specification/supported_features/charge_categorization.md
    """
    query = f"""
        SELECT
            billing_period_start,
            commitment_discount_id,
            commitment_discount_name,
            commitment_discount_type,
            charge_frequency,
            SUM(billed_cost) AS total_billed_cost
        FROM FocusCostUsage_0_0
        WHERE billing_period_start >= {{{{ billing_period_start }}}}
            AND billing_period_start < {{{{ billing_period_end }}}}
            AND charge_frequency = 'Recurring'
            AND commitment_discount_id IS NOT NULL
            {{{{ 'AND provider_name = ' + provider_name if provider_name else '' }}}}
        GROUP BY
            billing_period_start,
            commitment_discount_id,
            commitment_discount_name,
            commitment_discount_type,
            charge_frequency
    """
    return []


# Register Moose Consumption APIs
cost_comparison_api = ConsumptionApi[CostComparisonRequest, List[CostComparisonRow]](
    name="CostComparison",
    config=ConsumptionApiConfig(run=get_cost_comparison)
)

effective_cost_analysis_api = ConsumptionApi[EffectiveCostAnalysisRequest, List[EffectiveCostAnalysisRow]](
    name="EffectiveCostAnalysis",
    config=ConsumptionApiConfig(run=get_effective_cost_analysis)
)

commitment_discount_purchases_api = ConsumptionApi[ChargeCategoryRequest, List[CommitmentDiscountPurchaseRow]](
    name="CommitmentDiscountPurchases",
    config=ConsumptionApiConfig(run=get_commitment_discount_purchases)
)

correction_charges_api = ConsumptionApi[ChargeCategoryRequest, List[CorrectionRow]](
    name="CorrectionCharges",
    config=ConsumptionApiConfig(run=get_correction_charges)
)

recurring_charges_api = ConsumptionApi[ChargeCategoryRequest, List[RecurringChargeRow]](
    name="RecurringCharges",
    config=ConsumptionApiConfig(run=get_recurring_charges)
)
