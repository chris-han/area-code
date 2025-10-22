'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { workflowTriggerSchema, WorkflowTriggerFormData, WORKFLOW_TYPE_OPTIONS } from '@/lib/schemas'
import { useTriggerWorkflow } from '@/hooks/useWorkflows'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AlertCircle, CheckCircle } from 'lucide-react'

export function WorkflowForm() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const triggerWorkflow = useTriggerWorkflow()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<WorkflowTriggerFormData>({
    resolver: zodResolver(workflowTriggerSchema),
  })

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
          <select
            id="workflow_type"
            {...register('workflow_type')}
            defaultValue=""
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            <option value="" disabled>
              Select a workflow type
            </option>
            {WORKFLOW_TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
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
          disabled={isSubmitting}
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
