import { mooseClient } from './client'

export interface FocusSupportedFeature {
  id: string
  name: string
  description: string
  introduced_version: string
  dependent_columns: string[]
  supporting_columns: string[]
  example_sql?: string
}

export interface CostComparisonRequest {
  billing_period_start: string
  billing_period_end: string
  provider_name?: string
  billing_account_id?: string
}

export interface CostComparisonResponse {
  provider_name: string
  billing_account_id: string
  billing_account_name: string
  service_name: string
  total_effective_cost: number
  total_billed_cost: number
  total_contracted_cost: number
  total_list_cost: number
  contracted_discount: number
  effective_discount: number
}

export interface EffectiveCostRequest {
  billing_period_start: string
  billing_period_end: string
  provider_name?: string
}

export interface EffectiveCostResponse {
  provider_name: string
  billing_period_start: string
  billing_period_end: string
  service_category: string
  service_name: string
  region_id?: string
  region_name?: string
  pricing_unit?: string
  total_effective_cost: number
  total_pricing_quantity: number
}

export interface CommitmentRequest {
  billing_period_start: string
  billing_period_end: string
}

export interface CommitmentResponse {
  billing_account_id: string
  commitment_discount_id?: string
  commitment_discount_name?: string
  commitment_discount_type?: string
  total_purchased_quantity: number
  total_used_quantity: number
  total_unused_quantity: number
  utilization_rate: number
}

export interface ResourceUsageRequest {
  billing_period_start: string
  billing_period_end: string
  service_name?: string
}

export interface ResourceUsageResponse {
  service_name: string
  service_category: string
  resource_id?: string
  resource_name?: string
  resource_type?: string
  pricing_unit?: string
  total_pricing_quantity: number
  total_effective_cost: number
}

export interface ServiceCostRequest {
  billing_period_start: string
  billing_period_end: string
}

export interface ServiceCostResponse {
  service_category: string
  service_name: string
  total_effective_cost: number
  percentage_of_total: number
}

export interface LocationCostRequest {
  billing_period_start: string
  billing_period_end: string
}

export interface LocationCostResponse {
  region_id?: string
  region_name?: string
  availability_zone?: string
  total_effective_cost: number
  percentage_of_total: number
}

export interface AccountCostRequest {
  billing_period_start: string
  billing_period_end: string
}

export interface AccountCostResponse {
  billing_account_id: string
  billing_account_name?: string
  total_effective_cost: number
  total_billed_cost: number
}

export interface CommitmentUsageRequest {
  billing_period_start: string
  billing_period_end: string
  commitment_discount_status?: string
}

export interface CommitmentUsageResponse {
  provider_name: string
  billing_account_id: string
  commitment_discount_id?: string
  commitment_discount_type?: string
  commitment_discount_status?: string
  total_billed_cost: number
  total_effective_cost: number
}

export interface MarketplacePurchaseRequest {
  billing_period_start: string
  billing_period_end: string
  publisher_name?: string
}

export interface MarketplacePurchaseResponse {
  provider_name: string
  publisher_name: string
  service_name: string
  charge_category: string
  total_billed_cost: number
}

export interface UnitPriceRequest {
  billing_period_start: string
  billing_period_end: string
  service_name?: string
}

export interface UnitPriceResponse {
  service_name: string
  sku_id?: string
  pricing_unit?: string
  list_unit_price?: number
  contracted_unit_price?: number
  total_pricing_quantity?: number
}

export interface InvoiceAlignmentRequest {
  billing_period_start: string
  billing_period_end: string
  invoice_id?: string
}

export interface InvoiceAlignmentResponse {
  invoice_issuer_name: string
  billing_account_id: string
  billing_currency: string
  invoice_id?: string
  total_billed_cost: number
}

export interface CostAttributionRequest {
  billing_period_start: string
  billing_period_end: string
  tag_key?: string
}

export interface CostAttributionResponse {
  billing_account_id: string
  service_name: string
  resource_id?: string
  tags?: string
  total_billed_cost: number
}

export interface CorrectionChargesRequest {
  billing_period_start: string
  billing_period_end: string
  provider_name?: string
}

export interface CorrectionChargesResponse {
  provider_name: string
  billing_account_id: string
  charge_category: string
  service_category: string
  service_name: string
  total_billed_cost: number
}

export interface RecurringChargesRequest {
  billing_period_start: string
  billing_period_end: string
  provider_name?: string
}

export interface RecurringChargesResponse {
  billing_period_start: string
  commitment_discount_id?: string
  commitment_discount_name?: string
  commitment_discount_type?: string
  charge_frequency?: string
  total_billed_cost: number
}

export const focusApi = {
  listSupportedFeatures: () =>
    mooseClient.get<FocusSupportedFeature[]>('/focus/features'),

  getFeature: (featureId: string) =>
    mooseClient.get<FocusSupportedFeature>(`/focus/features/${featureId}`),

  costComparison: (params: CostComparisonRequest) =>
    mooseClient.post<CostComparisonResponse[]>('/consumption/CostComparison', params),

  effectiveCostAnalysis: (params: EffectiveCostRequest) =>
    mooseClient.post<EffectiveCostResponse[]>('/consumption/EffectiveCostAnalysis', params),

  commitmentDiscounts: (params: CommitmentRequest) =>
    mooseClient.post<CommitmentResponse[]>('/consumption/CommitmentDiscountPurchases', params),

  resourceUsage: (params: ResourceUsageRequest) =>
    mooseClient.post<ResourceUsageResponse[]>('/consumption/ResourceUsage', params),

  serviceCategorization: (params: ServiceCostRequest) =>
    mooseClient.post<ServiceCostResponse[]>('/consumption/ServiceCategorization', params),

  locationCosts: (params: LocationCostRequest) =>
    mooseClient.post<LocationCostResponse[]>('/consumption/LocationCosts', params),

  accountCosts: (params: AccountCostRequest) =>
    mooseClient.post<AccountCostResponse[]>('/consumption/AccountCosts', params),

  commitmentUsage: (params: CommitmentUsageRequest) =>
    mooseClient.post<CommitmentUsageResponse[]>('/consumption/CommitmentUsage', params),

  marketplacePurchases: (params: MarketplacePurchaseRequest) =>
    mooseClient.post<MarketplacePurchaseResponse[]>('/consumption/MarketplacePurchases', params),

  unitPrices: (params: UnitPriceRequest) =>
    mooseClient.post<UnitPriceResponse[]>('/consumption/UnitPrices', params),

  invoiceAlignment: (params: InvoiceAlignmentRequest) =>
    mooseClient.post<InvoiceAlignmentResponse[]>('/consumption/InvoiceAlignment', params),

  costAttribution: (params: CostAttributionRequest) =>
    mooseClient.post<CostAttributionResponse[]>('/consumption/CostAttribution', params),

  correctionCharges: (params: CorrectionChargesRequest) =>
    mooseClient.post<CorrectionChargesResponse[]>('/consumption/CorrectionCharges', params),

  recurringCharges: (params: RecurringChargesRequest) =>
    mooseClient.post<RecurringChargesResponse[]>('/consumption/RecurringCharges', params),
}
