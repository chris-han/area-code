import { useQuery } from '@tanstack/react-query'
import { systemApi } from '@/api/system'

export function useHealthStatus() {
  return useQuery({
    queryKey: ['health-status'],
    queryFn: systemApi.getHealthStatus,
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 2,
  })
}

export function useSystemLogs(params?: any) {
  return useQuery({
    queryKey: ['system-logs', params],
    queryFn: () => systemApi.getLogs(params),
    refetchInterval: 10000,
  })
}

export function useSystemEvents(params?: any) {
  return useQuery({
    queryKey: ['system-events', params],
    queryFn: () => systemApi.getEvents(params),
    refetchInterval: 15000,
  })
}

export function useBlobs(params?: any) {
  return useQuery({
    queryKey: ['blobs', params],
    queryFn: () => systemApi.getBlobs(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

export function useDailyPageViews(params?: any) {
  return useQuery({
    queryKey: ['daily-page-views', params],
    queryFn: () => systemApi.getDailyPageViews(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useUnstructuredData(params?: any) {
  return useQuery({
    queryKey: ['unstructured-data', params],
    queryFn: () => systemApi.getUnstructuredData(params),
    staleTime: 2 * 60 * 1000,
  })
}

export function useMedicalData(params?: any) {
  return useQuery({
    queryKey: ['medical-data', params],
    queryFn: () => systemApi.getMedical(params),
    staleTime: 5 * 60 * 1000,
  })
}