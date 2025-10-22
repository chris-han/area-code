import { biaClient, consumptionClient } from './client'
import { WorkflowStatus, WorkflowTriggerRequest } from '@/types'
import { WORKFLOW_TYPE_OPTIONS } from '@/lib/schemas'

const WORKFLOW_LABELS = WORKFLOW_TYPE_OPTIONS.reduce<Record<string, string>>((acc, option) => {
  acc[option.value] = option.label
  return acc
}, {})

const normalizeStatus = (status?: string): WorkflowStatus['status'] => {
  switch ((status ?? '').toLowerCase()) {
    case 'running':
      return 'running'
    case 'completed':
      return 'completed'
    case 'failed':
      return 'failed'
    case 'cancelled':
      return 'cancelled'
    case 'terminated':
      return 'terminated'
    case 'timed_out':
      return 'timed_out'
    case 'scheduled':
    case 'pending':
    default:
      return 'scheduled'
  }
}

const mapWorkflow = (workflow: any): WorkflowStatus => {
  if (!workflow) {
    return {
      id: '',
      name: 'Unknown Workflow',
      status: 'scheduled',
      startTime: null,
    }
  }

  const id = workflow.workflow_id ?? workflow.id ?? 'unknown'
  const type = workflow.workflow_type ?? 'unknown'

  return {
    id,
    name: WORKFLOW_LABELS[type] ?? String(type).replace(/[_-]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    status: normalizeStatus(workflow.status),
    startTime: workflow.start_time ? new Date(workflow.start_time) : null,
    endTime: workflow.end_time ? new Date(workflow.end_time) : undefined,
    progress: typeof workflow.progress === 'number' ? workflow.progress : undefined,
    logs: Array.isArray(workflow.result?.logs) ? workflow.result.logs : undefined,
    error: workflow.error_message ?? undefined,
  }
}

export const workflowsApi = {
  // Get all workflows
  getWorkflows: async (): Promise<WorkflowStatus[]> => {
    const response = await biaClient.post<{ workflows: any[] }>('/api/v1/workflows/list', {})
    return (response?.workflows ?? []).map(mapWorkflow)
  },

  // Get workflow status by ID
  getWorkflowStatus: async (id: string): Promise<WorkflowStatus> => {
    const response = await biaClient.post<{ workflow: any }>('/api/v1/workflows/status', { workflow_id: id })
    return mapWorkflow(response?.workflow ?? response)
  },

  // Get workflow metrics
  getWorkflowMetrics: async (id?: string): Promise<any> => {
    const params = id ? { workflow_id: id } : {}
    return biaClient.post<any>('/api/v1/workflows/metrics', params)
  },

  // Trigger a new workflow
  triggerWorkflow: async (request: WorkflowTriggerRequest): Promise<void> => {
    await biaClient.post('/api/v1/workflows/trigger', request)
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
