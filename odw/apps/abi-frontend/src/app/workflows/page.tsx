import { WorkflowForm } from '@/components/workflow-form'
import { WorkflowStatus } from '@/components/workflow-status'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function WorkflowsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Workflow Management</h1>
        <p className="text-muted-foreground">
          Create, schedule, and monitor ETL workflows
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Workflows</CardTitle>
          <CardDescription>
            Monitor all workflow executions - running, completed, failed, and scheduled
          </CardDescription>
        </CardHeader>
        <CardContent>
          <WorkflowStatus />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Create New Workflow</CardTitle>
          <CardDescription>
            Set up a new data processing workflow
          </CardDescription>
        </CardHeader>
        <CardContent>
          <WorkflowForm />
        </CardContent>
      </Card>
    </div>
  )
}