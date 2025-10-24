import { useQuery, useMutation } from '@tanstack/react-query'
import { billingApi } from '@/api/billing'
import { BillingQueryRequest } from '@/types'

export function useFocusBillingData(request: BillingQueryRequest) {
  return useQuery({
    queryKey: ['focus-billing-data', request],
    queryFn: () => billingApi.getFocusBillingData(request),
    enabled: !!(request.start_date && request.end_date),
  })
}

export function useFocusAggregation() {
  return useMutation({
    mutationFn: (request: any) => billingApi.getFocusAggregation(request),
  })
}

export function useCostTrends() {
  return useMutation({
    mutationFn: (request: any) => billingApi.getCostTrends(request),
  })
}

export function useResourceUtilization() {
  return useMutation({
    mutationFn: (request: any) => billingApi.getResourceUtilization(request),
  })
}

export function useCostOptimizationOpportunities() {
  return useMutation({
    mutationFn: (request: any) => billingApi.getCostOptimizationOpportunities(request),
  })
}

export function useServiceAnalysis() {
  return useMutation({
    mutationFn: (request: any) => billingApi.getServiceAnalysis(request),
  })
}