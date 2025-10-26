import { useQuery, useMutation } from '@tanstack/react-query'
import { focusApi, type CostComparisonRequest, type EffectiveCostRequest, type CommitmentRequest, type ResourceUsageRequest, type ServiceCostRequest, type LocationCostRequest, type AccountCostRequest } from '@/api/focus'

export function useSupportedFeatures() {
  return useQuery({
    queryKey: ['focus', 'features'],
    queryFn: () => focusApi.listSupportedFeatures(),
  })
}

export function useSupportedFeature(featureId: string) {
  return useQuery({
    queryKey: ['focus', 'feature', featureId],
    queryFn: () => focusApi.getFeature(featureId),
    enabled: !!featureId,
  })
}

export function useCostComparison() {
  return useMutation({
    mutationFn: (params: CostComparisonRequest) => focusApi.costComparison(params),
  })
}

export function useEffectiveCostAnalysis() {
  return useMutation({
    mutationFn: (params: EffectiveCostRequest) => focusApi.effectiveCostAnalysis(params),
  })
}

export function useCommitmentDiscounts() {
  return useMutation({
    mutationFn: (params: CommitmentRequest) => focusApi.commitmentDiscounts(params),
  })
}

export function useResourceUsage() {
  return useMutation({
    mutationFn: (params: ResourceUsageRequest) => focusApi.resourceUsage(params),
  })
}

export function useServiceCosts() {
  return useMutation({
    mutationFn: (params: ServiceCostRequest) => focusApi.serviceCosts(params),
  })
}

export function useLocationCosts() {
  return useMutation({
    mutationFn: (params: LocationCostRequest) => focusApi.locationCosts(params),
  })
}

export function useAccountCosts() {
  return useMutation({
    mutationFn: (params: AccountCostRequest) => focusApi.accountCosts(params),
  })
}

export function useCommitmentUsage() {
  return useMutation({
    mutationFn: (params: import('@/api/focus').CommitmentUsageRequest) => focusApi.commitmentUsage(params),
  })
}

export function useMarketplacePurchases() {
  return useMutation({
    mutationFn: (params: import('@/api/focus').MarketplacePurchaseRequest) => focusApi.marketplacePurchases(params),
  })
}

export function useUnitPrices() {
  return useMutation({
    mutationFn: (params: import('@/api/focus').UnitPriceRequest) => focusApi.unitPrices(params),
  })
}

export function useInvoiceAlignment() {
  return useMutation({
    mutationFn: (params: import('@/api/focus').InvoiceAlignmentRequest) => focusApi.invoiceAlignment(params),
  })
}

export function useCostAttribution() {
  return useMutation({
    mutationFn: (params: import('@/api/focus').CostAttributionRequest) => focusApi.costAttribution(params),
  })
}

export function useCorrectionCharges() {
  return useMutation({
    mutationFn: (params: import('@/api/focus').CorrectionChargesRequest) => focusApi.correctionCharges(params),
  })
}

export function useRecurringCharges() {
  return useMutation({
    mutationFn: (params: import('@/api/focus').RecurringChargesRequest) => focusApi.recurringCharges(params),
  })
}
