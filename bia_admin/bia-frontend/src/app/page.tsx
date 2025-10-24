"use client"

import Link from 'next/link'
import { useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Activity, 
  Database, 
  Heart, 
  Plug, 
  Workflow, 
  BarChart3, 
  Settings,
  Plus,
  FileText
} from 'lucide-react'
import { useWorkflows } from '@/hooks/useWorkflows'

export default function HomePage() {
  const { data: workflows, isLoading, isError } = useWorkflows()

  const { activeCount, runningCount, scheduledCount } = useMemo(() => {
    const workflowList = workflows ?? []
    const active = workflowList.filter((wf) => wf.status === 'running' || wf.status === 'scheduled')
    const running = active.filter((wf) => wf.status === 'running').length
    const scheduled = active.filter((wf) => wf.status === 'scheduled').length

    return {
      activeCount: active.length,
      runningCount: running,
      scheduledCount: scheduled,
    }
  }, [workflows])

  const workflowSubtitle = useMemo(() => {
    if (isLoading) {
      return 'Loading workflow status...'
    }
    if (isError) {
      return 'Unable to load workflow status'
    }
    if (activeCount === 0) {
      return 'No active workflows'
    }
    const parts: string[] = []
    if (runningCount > 0) {
      parts.push(`${runningCount} running`)
    }
    if (scheduledCount > 0) {
      parts.push(`${scheduledCount} scheduled`)
    }
    if (parts.length === 0) {
      return 'No running or scheduled workflows'
    }
    return parts.join(', ')
  }, [activeCount, isError, isLoading, runningCount, scheduledCount])

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">
          Azure Billing Intelligence
        </h1>
        <p className="text-xl text-muted-foreground">
          Workflow orchestration and billing analytics platform
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Workflows</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? '—' : activeCount}
            </div>
            <p className="text-xs text-muted-foreground">
              {workflowSubtitle}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Data Sources</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2</div>
            <p className="text-xs text-muted-foreground">
              Azure EA, S3 Storage
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Heart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">Healthy</div>
            <p className="text-xs text-muted-foreground">
              All services operational
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Plugins</CardTitle>
            <Plug className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">5</div>
            <p className="text-xs text-muted-foreground">
              3 active, 2 available
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Action Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Workflow className="h-5 w-5 text-primary" />
              <CardTitle>Workflow Management</CardTitle>
            </div>
            <CardDescription>
              Create, schedule, and monitor ETL workflows
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button asChild className="w-full">
              <Link href="/workflows">
                Manage Workflows
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full">
              <Link href="/workflows/new">
                <Plus className="h-4 w-4 mr-2" />
                Create New Workflow
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              <CardTitle>Billing Analytics</CardTitle>
            </div>
            <CardDescription>
              Explore and analyze Azure billing data
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button asChild className="w-full">
              <Link href="/analytics">
                View Analytics
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full">
              <Link href="/analytics/reports">
                <FileText className="h-4 w-4 mr-2" />
                Generate Reports
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Settings className="h-5 w-5 text-primary" />
              <CardTitle>System Administration</CardTitle>
            </div>
            <CardDescription>
              Manage plugins, connections, and system settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button asChild className="w-full">
              <Link href="/admin">
                Admin Panel
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full">
              <Link href="/admin/plugins">
                <Plug className="h-4 w-4 mr-2" />
                Plugin Marketplace
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Status Section */}
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
          <CardDescription>
            Current status of all system components
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Badge variant="success">ClickHouse Connected</Badge>
            <Badge variant="success">Temporal Running</Badge>
            <Badge variant="success">Redis Active</Badge>
            <Badge variant="success">MinIO Available</Badge>
            <Badge variant="warning">Kafdrop Monitoring</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
