'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { WorkflowForm } from '@/components/workflow-form'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  ArrowLeft,
  Workflow,
  Clock,
  Database,
  Settings,
  Zap,
  Cloud,
  Loader2
} from 'lucide-react'
import Link from 'next/link'
import { useEffect, useState } from 'react'

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

export default function NewWorkflowPage() {
  const [workflowTypes, setWorkflowTypes] = useState<WorkflowType[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchWorkflowTypes()
  }, [])

  const fetchWorkflowTypes = async () => {
    try {
      setLoading(true)
      setError(null)

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
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const getIconForWorkflowType = (workflowType: string) => {
    if (workflowType.includes('ingest') || workflowType.includes('billing')) {
      return <Database className="h-6 w-6" />
    } else if (workflowType.includes('migration') || workflowType.includes('schema')) {
      return <Settings className="h-6 w-6" />
    } else if (workflowType.includes('transformation')) {
      return <Zap className="h-6 w-6" />
    } else if (workflowType.includes('blob') || workflowType.includes('cloud')) {
      return <Cloud className="h-6 w-6" />
    }
    return <Workflow className="h-6 w-6" />
  }

  const getComplexityForWorkflow = (estimatedDuration: string) => {
    // Parse estimated duration and determine complexity
    if (estimatedDuration.includes('5-') || estimatedDuration.startsWith('5')) {
      return 'Low'
    } else if (estimatedDuration.includes('10-20') || estimatedDuration.includes('15-')) {
      return 'Medium'
    }
    return 'High'
  }

  const getComplexityBadge = (complexity: string) => {
    switch (complexity) {
      case 'Low':
        return <Badge variant="success">{complexity}</Badge>
      case 'Medium':
        return <Badge variant="warning">{complexity}</Badge>
      case 'High':
        return <Badge variant="destructive">{complexity}</Badge>
      default:
        return <Badge variant="secondary">{complexity}</Badge>
    }
  }

  const getTagsForWorkflowType = (workflowType: string, displayName: string) => {
    const tags: string[] = []

    if (workflowType.includes('focus') || displayName.includes('FOCUS')) {
      tags.push('FOCUS')
    }
    if (workflowType.includes('billing')) {
      tags.push('Billing')
    }
    if (workflowType.includes('ingest')) {
      tags.push('Ingestion')
    }
    if (workflowType.includes('migration') || workflowType.includes('schema')) {
      tags.push('Migration')
    }
    if (workflowType.includes('transformation')) {
      tags.push('Transformation')
    }

    return tags.length > 0 ? tags : ['Workflow']
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" asChild>
          <Link href="/workflows">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Workflows
          </Link>
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Create New Workflow</h1>
          <p className="text-muted-foreground">
            Set up a new data processing workflow
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Workflow Types */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Choose Workflow Type</CardTitle>
              <CardDescription>
                Select the type of workflow you want to create (dynamically loaded from backend)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-muted-foreground">Loading workflow types...</span>
                </div>
              )}

              {error && (
                <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
                  <p className="font-medium">Failed to load workflow types</p>
                  <p className="text-sm mt-1">{error}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-3"
                    onClick={fetchWorkflowTypes}
                  >
                    Retry
                  </Button>
                </div>
              )}

              {!loading && !error && workflowTypes.length === 0 && (
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-muted-foreground">No workflow types available</p>
                </div>
              )}

              {!loading && !error && workflowTypes.length > 0 && (
                <div className="space-y-3">
                  {workflowTypes.map((type) => {
                    const complexity = getComplexityForWorkflow(type.estimated_duration)
                    const tags = getTagsForWorkflowType(type.workflow_type, type.display_name)

                    return (
                      <Card key={type.workflow_type} className="border hover:shadow-md transition-shadow cursor-pointer">
                        <CardContent className="p-4">
                          <div className="flex items-start gap-3">
                            <div className="p-2 bg-primary/10 rounded-lg text-primary">
                              {getIconForWorkflowType(type.workflow_type)}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="font-medium">{type.display_name}</h4>
                                {getComplexityBadge(complexity)}
                              </div>
                              <p className="text-sm text-muted-foreground mb-3">
                                {type.description}
                              </p>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                  <Clock className="h-3 w-3" />
                                  {type.estimated_duration}
                                </div>
                                <div className="flex gap-1">
                                  {tags.map((tag) => (
                                    <Badge key={tag} variant="outline" className="text-xs">
                                      {tag}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                              <div className="mt-2 text-xs text-muted-foreground">
                                Type: <code className="bg-muted px-1 py-0.5 rounded">{type.workflow_type}</code>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Prerequisites */}
          <Card>
            <CardHeader>
              <CardTitle>Prerequisites</CardTitle>
              <CardDescription>
                Make sure these requirements are met
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">ClickHouse database is connected</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Temporal workflow engine is running</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Data warehouse service is active</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">FOCUS data sources are configured</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Workflow Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Workflow Configuration</CardTitle>
            <CardDescription>
              Configure your workflow parameters
            </CardDescription>
          </CardHeader>
          <CardContent>
            <WorkflowForm />
          </CardContent>
        </Card>
      </div>

      {/* Recent Workflows */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Workflows</CardTitle>
          <CardDescription>
            Your recently created workflows for reference
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <Database className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h4 className="font-medium">FOCUS Billing Ingest - July 2025</h4>
                  <p className="text-sm text-muted-foreground">Created 1 hour ago • Completed successfully • 458K records</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="success">Completed</Badge>
                <Button variant="outline" size="sm">Clone</Button>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <Settings className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h4 className="font-medium">Schema Migration - FOCUS 1.2 Update</h4>
                  <p className="text-sm text-muted-foreground">Created 2 hours ago • Completed successfully • Schema version 0_1</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="success">Completed</Badge>
                <Button variant="outline" size="sm">Clone</Button>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <Database className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h4 className="font-medium">FOCUS Billing Ingest - June 2025</h4>
                  <p className="text-sm text-muted-foreground">Created yesterday • Completed successfully • 412K records</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="success">Completed</Badge>
                <Button variant="outline" size="sm">Clone</Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
