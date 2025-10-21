// Workflow Types
export interface WorkflowStatus {
  id: string
  name: string
  status: 'running' | 'completed' | 'failed' | 'cancelled' | 'scheduled'
  startTime: Date
  endTime?: Date
  progress?: number
  logs?: string[]
  error?: string
}

export interface WorkflowTriggerRequest {
  workflow_type: string
  parameters: Record<string, any>
  schedule?: string
}

// Billing Data Types
export interface BillingData {
  subscriptionId: string
  resourceGroup: string
  service: string
  cost: number
  date: Date
  currency: string
  region?: string
  resourceId?: string
}

export interface BillingQueryRequest {
  start_date: string
  end_date: string
  subscription_ids?: string[]
  resource_groups?: string[]
  services?: string[]
  limit?: number
}

// Plugin Types
export interface PluginMetadata {
  name: string
  version: string
  description: string
  author: string
  category: string
  tags: string[]
  iconUrl?: string
  documentationUrl?: string
  configSchema: Record<string, any>
  isInstalled: boolean
  isConfigured: boolean
  isActive: boolean
}

// Infrastructure Types
export interface InfrastructureService {
  name: string
  type: 'database' | 'messaging' | 'storage' | 'workflow' | 'cache' | 'unknown'
  status: 'healthy' | 'unhealthy' | 'unknown'
  url: string
  managementUrl?: string
  lastHealthCheck: Date
}

// API Response Types
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}
