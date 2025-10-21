import { biaClient, consumptionClient } from './client'
import { InfrastructureService } from '@/types'

const inferServiceType = (name: string): InfrastructureService['type'] => {
  const normalized = name.toLowerCase()
  if (normalized.includes('clickhouse')) return 'database'
  if (normalized.includes('temporal')) return 'workflow'
  if (normalized.includes('redis')) return 'cache'
  if (normalized.includes('minio') || normalized.includes('s3')) return 'storage'
  if (normalized.includes('redpanda') || normalized.includes('kafka')) return 'messaging'
  return 'unknown'
}

export const systemApi = {
  // Get system health status
  getHealthStatus: async (): Promise<{
    overall: 'healthy' | 'degraded' | 'unhealthy'
    services: InfrastructureService[]
    timestamp: string
  }> => {
    const response = await biaClient.get<any>('/api/v1/health')
    const services: InfrastructureService[] = (response?.services ?? []).map((service: any) => ({
      name: service?.name ?? 'Unknown Service',
      type: inferServiceType(service?.name ?? ''),
      status: (service?.status ?? 'unknown') as InfrastructureService['status'],
      url: service?.url ?? '',
      managementUrl: service?.management_url,
      lastHealthCheck: service?.last_check ? new Date(service.last_check) : new Date(),
    }))

    return {
      overall: (response?.status ?? 'unhealthy') as 'healthy' | 'degraded' | 'unhealthy',
      services,
      timestamp: response?.timestamp ?? new Date().toISOString(),
    }
  },

  // Get blobs (data storage info)
  getBlobs: async (params?: any): Promise<any[]> => {
    return consumptionClient.get<any[]>('/getBlobs', params)
  },

  // Get logs
  getLogs: async (params?: any): Promise<string[]> => {
    return consumptionClient.get<string[]>('/getLogs', params)
  },

  // Get events
  getEvents: async (params?: any): Promise<any[]> => {
    return consumptionClient.get<any[]>('/getEvents', params)
  },

  // Get daily page views
  getDailyPageViews: async (params?: any): Promise<any[]> => {
    return consumptionClient.get<any[]>('/getDailyPageViews', params)
  },

  // Get unstructured data
  getUnstructuredData: async (params?: any): Promise<any[]> => {
    return consumptionClient.get<any[]>('/getUnstructuredData', params)
  },

  // Get medical data
  getMedical: async (params?: any): Promise<any[]> => {
    return consumptionClient.get<any[]>('/getMedical', params)
  },

  // Extract blob data
  extractBlob: async (request: any): Promise<any> => {
    return consumptionClient.post<any>('/extract-blob', request)
  },

  // Extract logs
  extractLogs: async (request: any): Promise<any> => {
    return consumptionClient.post<any>('/extract-logs', request)
  },

  // Extract events
  extractEvents: async (request: any): Promise<any> => {
    return consumptionClient.post<any>('/extract-events', request)
  },

  // Extract unstructured data
  extractUnstructuredData: async (request: any): Promise<any> => {
    return consumptionClient.post<any>('/extract-unstructured-data', request)
  }
}
