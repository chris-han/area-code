'use client'

import { useState, useEffect } from 'react'
import { useWorkflows } from '@/hooks/useWorkflows'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { formatDate } from '@/lib/utils'
import { AlertCircle, Clock, CheckCircle, XCircle, Pause, Play } from 'lucide-react'

export function WorkflowStatus() {
  const [mounted, setMounted] = useState(false)
  const { data: workflows, isLoading, error } = useWorkflows()

  useEffect(() => {
    setMounted(true)
  }, [])

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
        return 'secondary'
      case 'scheduled':
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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Active Workflows</h3>
        <Badge variant="outline">{workflows.length} total</Badge>
      </div>
      
      <div className="space-y-3">
        {workflows.map((workflow) => (
          <Card key={workflow.id}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium">{workflow.name}</h4>
                    <Badge variant={getStatusVariant(workflow.status) as any}>
                      {getStatusIcon(workflow.status)}
                      <span className="ml-1 capitalize">{workflow.status}</span>
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Started: {formatDate(workflow.startTime)}
                  </p>
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
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => alert(`Viewing details for workflow: ${workflow.name}`)}
                  >
                    Details
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}