import { biaClient, consumptionClient } from './client'
import { WorkflowStatus, WorkflowTriggerRequest } from '@/types'

export const workflowsApi = {
  // Get all workflows
  getWorkflows: async (): Promise<WorkflowStatus[]> => {
    const response = await biaClient.post<{ workflows: WorkflowStatus[] }>('/api/v1/workflows/list', {})
    return response?.workflows ?? []
  },

  // Get workflow status by ID
  getWorkflowStatus: async (id: string): Promise<WorkflowStatus> => {
    return biaClient.post<WorkflowStatus>('/api/v1/workflows/status', { workflow_id: id })
  },

  // Get workflow metrics
  getWorkflowMetrics: async (id?: string): Promise<any> => {
    const params = id ? { workflow_id: id } : {}
    return biaClient.post<any>('/api/v1/workflows/metrics', params)
  },

  // Trigger a new workflow
  triggerWorkflow: async (request: WorkflowTriggerRequest): Promise<WorkflowStatus> => {
    return biaClient.post<WorkflowStatus>('/api/v1/workflows/trigger', request)
  },

  // Control a workflow (start, stop, pause, resume)
  controlWorkflow: async (id: string, action: 'start' | 'stop' | 'pause' | 'resume'): Promise<void> => {
    return biaClient.post<void>('/api/v1/workflows/control', { 
      workflow_id: id, 
      action 
    })
  },

  // Get workflow logs (using getLogs endpoint)
  getWorkflowLogs: async (id: string): Promise<string[]> => {
    return consumptionClient.get<string[]>('/getLogs', { workflow_id: id })
  }
}
