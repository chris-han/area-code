import { z } from 'zod'

// Dynamic workflow type validation - accepts any string
// Actual validation happens at the backend when workflows are registered
export const workflowTriggerSchema = z.object({
  workflow_type: z.string().min(1, 'Workflow type is required'),
  parameters: z.record(z.any()).optional().default({}),
  schedule: z.string().optional(),
})

export type WorkflowTriggerFormData = z.infer<typeof workflowTriggerSchema>
export type WorkflowType = string

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
