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
  Zap
} from 'lucide-react'
import Link from 'next/link'

export default function NewWorkflowPage() {
  const workflowTypes = [
    {
      id: 'azure-blob-ingestion',
      name: 'Azure Blob Storage Ingestion',
      description: 'Ingest FOCUS-compliant parquet files from Azure Blob Storage',
      icon: <Database className="h-6 w-6" />,
      estimatedTime: '10-25 min',
      complexity: 'Medium',
      tags: ['Azure', 'Blob', 'FOCUS', 'Parquet']
    },
    {
      id: 'focus-transformation',
      name: 'FOCUS 1.2 Transformation',
      description: 'Transform parquet files to Moose model FOCUS 1.2 data tables',
      icon: <Zap className="h-6 w-6" />,
      estimatedTime: '15-30 min',
      complexity: 'Medium',
      tags: ['FOCUS', 'Transform', '1.2', 'Moose']
    },
    {
      id: 'azure-to-clickhouse-pipeline',
      name: 'Azure Blob to ClickHouse Pipeline',
      description: 'Complete pipeline: Azure Blob → FOCUS Transform → ClickHouse Sink',
      icon: <Workflow className="h-6 w-6" />,
      estimatedTime: '25-45 min',
      complexity: 'High',
      tags: ['Pipeline', 'Azure', 'ClickHouse', 'End-to-End']
    },
    {
      id: 'azure-billing-extraction',
      name: 'Azure Billing Data Extraction',
      description: 'Extract billing data from Azure Enterprise Agreement',
      icon: <Database className="h-6 w-6" />,
      estimatedTime: '15-30 min',
      complexity: 'Medium',
      tags: ['Azure', 'Billing', 'EA']
    },
    {
      id: 'data-quality-check',
      name: 'Data Quality Check',
      description: 'Validate data integrity and completeness',
      icon: <Settings className="h-6 w-6" />,
      estimatedTime: '5-10 min',
      complexity: 'Low',
      tags: ['Quality', 'Validation', 'Check']
    },
    {
      id: 'cost-analysis',
      name: 'Cost Analysis Report',
      description: 'Generate comprehensive cost analysis and insights',
      icon: <Workflow className="h-6 w-6" />,
      estimatedTime: '20-45 min',
      complexity: 'High',
      tags: ['Analysis', 'Report', 'Insights']
    },
  ]

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
                Select the type of workflow you want to create
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {workflowTypes.map((type) => (
                  <Card key={type.id} className="border hover:shadow-md transition-shadow cursor-pointer">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                          {type.icon}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">{type.name}</h4>
                            {getComplexityBadge(type.complexity)}
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">
                            {type.description}
                          </p>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              {type.estimatedTime}
                            </div>
                            <div className="flex gap-1">
                              {type.tags.map((tag) => (
                                <Badge key={tag} variant="outline" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
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
                  <span className="text-sm">Azure Blob Storage Connector is configured</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">FOCUS 1.2 Transformer is active</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">ClickHouse Sink is configured</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-yellow-500 rounded-full"></div>
                  <span className="text-sm">Azure SAS token has valid permissions</span>
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
                <Workflow className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h4 className="font-medium">Azure to ClickHouse Pipeline - January Data</h4>
                  <p className="text-sm text-muted-foreground">Created 1 hour ago • Completed successfully • 1.2M records → ClickHouse</p>
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
                  <h4 className="font-medium">Azure Blob Ingestion - December FOCUS Data</h4>
                  <p className="text-sm text-muted-foreground">Created 2 hours ago • Completed successfully • 950K records</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="success">Completed</Badge>
                <Button variant="outline" size="sm">Clone</Button>
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <Zap className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h4 className="font-medium">FOCUS 1.2 Transform - Q4 Parquet Files</h4>
                  <p className="text-sm text-muted-foreground">Created yesterday • Completed successfully • 850K records transformed</p>
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
                  <h4 className="font-medium">Data Quality Check - December Billing</h4>
                  <p className="text-sm text-muted-foreground">Created 3 days ago • Completed successfully • 99.8% quality score</p>
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