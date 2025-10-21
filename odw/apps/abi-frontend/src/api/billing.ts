import { biaClient } from './client'
import { BillingData, BillingQueryRequest } from '@/types'

export const billingApi = {
  // Get FOCUS billing data
  getFocusBillingData: async (request: BillingQueryRequest): Promise<BillingData[]> => {
    const response = await biaClient.post<BillingData[]>('/api/v1/focus/billing-data', request)
    return response ?? []
  },

  // Get FOCUS aggregation
  getFocusAggregation: async (request: any): Promise<any> => {
    return biaClient.post<any>('/api/v1/focus/aggregation', request)
  },

  // Get cost trends
  getCostTrends: async (request: any): Promise<any> => {
    return biaClient.post<any>('/api/v1/billing/analytics/cost-trends', request)
  },

  // Get resource utilization
  getResourceUtilization: async (request: any): Promise<any> => {
    return biaClient.post<any>('/api/v1/billing/analytics/resource-utilization', request)
  },

  // Get cost optimization opportunities
  getCostOptimizationOpportunities: async (request: any): Promise<any> => {
    return biaClient.post<any>('/api/v1/billing/analytics/cost-optimization', request)
  },

  // Get service analysis
  getServiceAnalysis: async (request: any): Promise<any> => {
    return biaClient.post<any>('/api/v1/billing/analytics/service-analysis', request)
  }
}
