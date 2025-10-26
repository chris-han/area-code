'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { workflowTriggerSchema, WorkflowTriggerFormData } from '@/lib/schemas'
import { useTriggerWorkflow } from '@/hooks/useWorkflows'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react'

interface WorkflowType {
  workflow_type: string
  workflow_class: string
  display_name: string
  description: string
  estimated_duration: string
}

interface WorkflowTypesResponse {
  success: boolean
  workflows: WorkflowType[]
  total: number
  message: string
}

export function WorkflowForm() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [workflowTypes, setWorkflowTypes] = useState<WorkflowType[]>([])
  const [loadingTypes, setLoadingTypes] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const triggerWorkflow = useTriggerWorkflow()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<WorkflowTriggerFormData>({
    resolver: zodResolver(workflowTriggerSchema),
  })

  useEffect(() => {
    fetchWorkflowTypes()
  }, [])

  const fetchWorkflowTypes = async () => {
    try {
      setLoadingTypes(true)
      setLoadError(null)

      const response = await fetch('http://localhost:4300/api/v1/workflows/types')

      if (!response.ok) {
        throw new Error(`Failed to fetch workflow types: ${response.statusText}`)
      }

      const data: WorkflowTypesResponse = await response.json()

      if (data.success) {
        setWorkflowTypes(data.workflows)
      } else {
        throw new Error(data.message || 'Failed to fetch workflow types')
      }
    } catch (err) {
      console.error('Error fetching workflow types:', err)
      setLoadError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoadingTypes(false)
    }
  }

  const onSubmit = async (data: WorkflowTriggerFormData) => {
    try {
      setIsSubmitting(true)
      setSubmitStatus('idle')

      await triggerWorkflow.mutateAsync(data)

      setSubmitStatus('success')
      reset()

      // Reset success status after 3 seconds
      setTimeout(() => setSubmitStatus('idle'), 3000)
    } catch (error) {
      console.error('Failed to trigger workflow:', error)
      setSubmitStatus('error')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-md">
        <div className="space-y-2">
          <Label htmlFor="workflow_type">Workflow Type</Label>

          {loadingTypes ? (
            <div className="flex items-center gap-2 p-3 border rounded-md bg-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm text-muted-foreground">Loading workflow types...</span>
            </div>
          ) : loadError ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 p-3 border rounded-md bg-destructive/10 text-destructive">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm">Failed to load workflow types</span>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={fetchWorkflowTypes}
              >
                Retry
              </Button>
            </div>
          ) : (
            <select
              id="workflow_type"
              {...register('workflow_type')}
              defaultValue=""
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={workflowTypes.length === 0}
            >
              <option value="" disabled>
                {workflowTypes.length === 0
                  ? 'No workflow types available'
                  : 'Select a workflow type'}
              </option>
              {workflowTypes.map((workflow) => (
                <option key={workflow.workflow_type} value={workflow.workflow_type}>
                  {workflow.display_name} ({workflow.estimated_duration})
                </option>
              ))}
            </select>
          )}

          {errors.workflow_type && (
            <p className="text-sm text-destructive flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              {errors.workflow_type.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="schedule">Schedule (Optional)</Label>
          <Input
            id="schedule"
            type="text"
            placeholder="e.g., 0 2 * * * (daily at 2 AM)"
            {...register('schedule')}
          />
          <p className="text-xs text-muted-foreground">
            Use cron format for scheduling. Leave empty for immediate execution.
          </p>
          {errors.schedule && (
            <p className="text-sm text-destructive flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              {errors.schedule.message}
            </p>
          )}
        </div>

        <Button
          type="submit"
          disabled={isSubmitting || loadingTypes || workflowTypes.length === 0}
          className="w-full"
        >
          {isSubmitting ? 'Triggering...' : 'Trigger Workflow'}
        </Button>
      </form>

      {/* Status Messages */}
      {submitStatus === 'success' && (
        <div className="flex items-center gap-2 text-green-600 bg-green-50 p-3 rounded-md">
          <CheckCircle className="h-4 w-4" />
          <span>Workflow triggered successfully!</span>
        </div>
      )}

      {submitStatus === 'error' && (
        <div className="flex items-center gap-2 text-destructive bg-destructive/10 p-3 rounded-md">
          <AlertCircle className="h-4 w-4" />
          <span>Failed to trigger workflow. Please try again.</span>
        </div>
      )}
    </div>
  )
}
