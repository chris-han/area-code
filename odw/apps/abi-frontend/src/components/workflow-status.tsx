'use client'

import { useState, useEffect } from 'react'
import { useWorkflows } from '@/hooks/useWorkflows'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { formatDate } from '@/lib/utils'
import { AlertCircle, Clock, CheckCircle, XCircle, Pause, Play, ExternalLink } from 'lucide-react'

export function WorkflowStatus() {
  const [mounted, setMounted] = useState(false)
  const { data: workflows, isLoading, error } = useWorkflows()

  useEffect(() => {
    setMounted(true)
  }, [])

  const getTemporalUIUrl = (workflowId: string, runId?: string) => {
    if (!runId) return null
    return `http://localhost:8080/namespaces/default/workflows/${workflowId}/${runId}/history`
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Play className="h-3 w-3" />
      case 'completed':
        return <CheckCircle className="h-3 w-3" />
      case 'failed':
        return <XCircle className="h-3 w-3" />
      case 'cancelled':
        return <Pause className="h-3 w-3" />
      case 'scheduled':
        return <Clock className="h-3 w-3" />
      default:
        return <AlertCircle className="h-3 w-3" />
    }
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'running':
        return 'default'
      case 'completed':
        return 'success'
      case 'failed':
        return 'destructive'
      case 'cancelled':
      case 'terminated':
        return 'secondary'
      case 'scheduled':
      case 'timed_out':
        return 'warning'
      default:
        return 'outline'
    }
  }

  if (!mounted || isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-muted-foreground">Loading workflows...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="border border-destructive rounded-lg p-4">
        <div className="flex items-center gap-2 text-destructive">
          <AlertCircle className="h-4 w-4" />
          <span className="font-medium">Error loading workflows</span>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          {error.message}
        </p>
        <p className="text-xs text-muted-foreground mt-2">
          Make sure the API server is running and accessible.
        </p>
      </div>
    )
  }

  if (!workflows || workflows.length === 0) {
    return (
      <div className="text-center p-8">
        <div className="text-muted-foreground">
          No workflows found. Create your first workflow to get started.
        </div>
      </div>
    )
  }

  // Group workflows by status
  const groupedWorkflows = workflows.reduce((acc, workflow) => {
    const status = workflow.status
    if (!acc[status]) {
      acc[status] = []
    }
    acc[status].push(workflow)
    return acc
  }, {} as Record<string, typeof workflows>)

  // Status order for display
  const statusOrder = ['running', 'scheduled', 'completed', 'failed', 'cancelled', 'terminated', 'timed_out']

  const statusCounts = {
    running: groupedWorkflows.running?.length || 0,
    completed: groupedWorkflows.completed?.length || 0,
    failed: groupedWorkflows.failed?.length || 0,
    other: workflows.length - (groupedWorkflows.running?.length || 0) - (groupedWorkflows.completed?.length || 0) - (groupedWorkflows.failed?.length || 0)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Workflow Executions</h3>
        <div className="flex items-center gap-2">
          {statusCounts.running > 0 && (
            <Badge variant="default">{statusCounts.running} running</Badge>
          )}
          {statusCounts.completed > 0 && (
            <Badge variant="success">{statusCounts.completed} completed</Badge>
          )}
          {statusCounts.failed > 0 && (
            <Badge variant="destructive">{statusCounts.failed} failed</Badge>
          )}
          <Badge variant="outline">{workflows.length} total</Badge>
        </div>
      </div>

      <div className="space-y-4">
        {statusOrder.map(status => {
          const statusWorkflows = groupedWorkflows[status]
          if (!statusWorkflows || statusWorkflows.length === 0) return null

          return (
            <div key={status} className="space-y-2">
              <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                {status} ({statusWorkflows.length})
              </h4>
              <div className="space-y-2">
                {statusWorkflows.map((workflow) => (
                  <Card key={workflow.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium">{workflow.name}</h4>
                            <Badge variant={getStatusVariant(workflow.status) as any}>
                              {getStatusIcon(workflow.status)}
                              <span className="ml-1 capitalize">{workflow.status}</span>
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span>ID: {workflow.id}</span>
                            {workflow.startTime && (
                              <span>Started: {formatDate(workflow.startTime)}</span>
                            )}
                            {workflow.endTime && (
                              <span>Ended: {formatDate(workflow.endTime)}</span>
                            )}
                          </div>
                          {workflow.error && (
                            <p className="text-sm text-destructive">
                              Error: {workflow.error}
                            </p>
                          )}
                          {workflow.progress !== undefined && (
                            <div className="space-y-1">
                              <div className="text-xs text-muted-foreground">
                                Progress: {Math.round(workflow.progress * 100)}%
                              </div>
                              <div className="w-full bg-secondary rounded-full h-1.5">
                                <div
                                  className="bg-primary h-1.5 rounded-full transition-all duration-300"
                                  style={{ width: `${workflow.progress * 100}%` }}
                                />
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {workflow.runId ? (
                            <Button
                              variant="outline"
                              size="sm"
                              asChild
                            >
                              <a
                                href={getTemporalUIUrl(workflow.id, workflow.runId)!}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-1"
                              >
                                <ExternalLink className="h-3 w-3" />
                                Temporal UI
                              </a>
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              disabled
                              title="Run ID not available"
                            >
                              Details
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}