import { z } from 'zod'

const workflowTypeEnum = z.enum([
  'azure_billing_extraction',
  'focus_transformation',
  'data_validation',
  'azure_blob_ingest',
  'scheduled_report',
  'test_workflow',
  'focus_billing_ingest',
])

export const WORKFLOW_TYPE_OPTIONS: { value: WorkflowType; label: string }[] = [
  { value: 'azure_billing_extraction', label: 'Azure Billing Extraction' },
  { value: 'focus_transformation', label: 'FOCUS Transformation' },
  { value: 'data_validation', label: 'Data Quality Check' },
  { value: 'azure_blob_ingest', label: 'Azure Blob Ingest' },
  { value: 'scheduled_report', label: 'Scheduled Report' },
  { value: 'test_workflow', label: 'Test Workflow (Mock Ingest)' },
  { value: 'focus_billing_ingest', label: 'FOCUS Billing Ingest' },
]

export type WorkflowType = z.infer<typeof workflowTypeEnum>

export const workflowTriggerSchema = z.object({
  workflow_type: workflowTypeEnum,
  parameters: z.record(z.any()).optional().default({}),
  schedule: z.string().optional(),
})

export type WorkflowTriggerFormData = z.infer<typeof workflowTriggerSchema>

export const billingQuerySchema = z.object({
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  subscription_ids: z.array(z.string()).optional(),
  resource_groups: z.array(z.string()).optional(),
  services: z.array(z.string()).optional(),
  limit: z.number().positive().optional(),
})

export type BillingQueryFormData = z.infer<typeof billingQuerySchema>

export const pluginConfigSchema = z.object({
  plugin_name: z.string().min(1, 'Plugin name is required'),
  config: z.record(z.any()),
})

export type PluginConfigFormData = z.infer<typeof pluginConfigSchema>
