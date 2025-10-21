import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workflowsApi } from '@/api/workflows'
import { WorkflowStatus, WorkflowTriggerRequest } from '@/types'

export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: workflowsApi.getWorkflows,
    refetchInterval: 10000, // Refetch every 10 seconds for live updates
    retry: 2,
  })
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: ['workflow', id],
    queryFn: () => workflowsApi.getWorkflowStatus(id),
    enabled: !!id,
    refetchInterval: 5000,
  })
}

export function useWorkflowMetrics(id?: string) {
  return useQuery({
    queryKey: ['workflow-metrics', id],
    queryFn: () => workflowsApi.getWorkflowMetrics(id),
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function useTriggerWorkflow() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: WorkflowTriggerRequest) => workflowsApi.triggerWorkflow(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      queryClient.invalidateQueries({ queryKey: ['workflow-metrics'] })
    },
  })
}

export function useControlWorkflow() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'start' | 'stop' | 'pause' | 'resume' }) => 
      workflowsApi.controlWorkflow(id, action),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      queryClient.invalidateQueries({ queryKey: ['workflow', variables.id] })
    },
  })
}

export function useWorkflowLogs(id: string) {
  return useQuery({
    queryKey: ['workflow-logs', id],
    queryFn: () => workflowsApi.getWorkflowLogs(id),
    enabled: !!id,
    refetchInterval: 5000,
  })
}