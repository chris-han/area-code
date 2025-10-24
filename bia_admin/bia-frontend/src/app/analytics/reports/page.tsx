import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  FileText, 
  Download, 
  Calendar, 
  Clock,
  TrendingUp,
  DollarSign,
  BarChart3,
  PieChart,
  Plus
} from 'lucide-react'

export default function ReportsPage() {
  const recentReports = [
    {
      id: '1',
      name: 'Monthly Cost Analysis',
      type: 'Cost Analysis',
      createdAt: '2024-01-15T10:30:00Z',
      status: 'completed',
      size: '2.4 MB',
      format: 'PDF'
    },
    {
      id: '2',
      name: 'Resource Utilization Q4',
      type: 'Utilization',
      createdAt: '2024-01-14T15:45:00Z',
      status: 'completed',
      size: '1.8 MB',
      format: 'Excel'
    },
    {
      id: '3',
      name: 'Cost Optimization Opportunities',
      type: 'Optimization',
      createdAt: '2024-01-13T09:15:00Z',
      status: 'completed',
      size: '3.1 MB',
      format: 'PDF'
    },
    {
      id: '4',
      name: 'Service Breakdown Analysis',
      type: 'Service Analysis',
      createdAt: '2024-01-12T14:20:00Z',
      status: 'generating',
      size: '-',
      format: 'PDF'
    },
  ]

  const reportTemplates = [
    {
      name: 'Executive Summary',
      description: 'High-level cost overview for leadership',
      icon: <FileText className="h-6 w-6" />,
      frequency: 'Monthly',
      estimatedTime: '5 min'
    },
    {
      name: 'Detailed Cost Breakdown',
      description: 'Comprehensive analysis by service and resource',
      icon: <BarChart3 className="h-6 w-6" />,
      frequency: 'Weekly',
      estimatedTime: '10 min'
    },
    {
      name: 'Resource Utilization',
      description: 'Usage patterns and efficiency metrics',
      icon: <TrendingUp className="h-6 w-6" />,
      frequency: 'Daily',
      estimatedTime: '7 min'
    },
    {
      name: 'Cost Optimization',
      description: 'Recommendations for cost reduction',
      icon: <DollarSign className="h-6 w-6" />,
      frequency: 'Monthly',
      estimatedTime: '15 min'
    },
    {
      name: 'Service Analysis',
      description: 'Per-service cost and usage analysis',
      icon: <PieChart className="h-6 w-6" />,
      frequency: 'Weekly',
      estimatedTime: '8 min'
    },
    {
      name: 'Trend Analysis',
      description: 'Historical cost trends and forecasting',
      icon: <TrendingUp className="h-6 w-6" />,
      frequency: 'Monthly',
      estimatedTime: '12 min'
    },
  ]

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success">Completed</Badge>
      case 'generating':
        return <Badge variant="warning">Generating</Badge>
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>
      default:
        return <Badge variant="secondary">{status}</Badge>
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Reports</h1>
          <p className="text-muted-foreground">
            Generate and manage billing and cost analysis reports
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Create Report
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-muted-foreground">
              +3 this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled Reports</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8</div>
            <p className="text-xs text-muted-foreground">
              Auto-generated
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Generation Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8.5m</div>
            <p className="text-xs text-muted-foreground">
              -2m from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
            <Download className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">156 MB</div>
            <p className="text-xs text-muted-foreground">
              12% of quota
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Reports */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Reports</CardTitle>
          <CardDescription>
            Your recently generated reports
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentReports.map((report) => (
              <div key={report.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <h4 className="font-medium">{report.name}</h4>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span>{report.type}</span>
                      <span>•</span>
                      <span>{formatDate(report.createdAt)}</span>
                      <span>•</span>
                      <span>{report.size}</span>
                      <span>•</span>
                      <span>{report.format}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusBadge(report.status)}
                  {report.status === 'completed' && (
                    <Button variant="outline" size="sm">
                      <Download className="h-3 w-3 mr-1" />
                      Download
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Report Templates */}
      <Card>
        <CardHeader>
          <CardTitle>Report Templates</CardTitle>
          <CardDescription>
            Choose from pre-built report templates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {reportTemplates.map((template) => (
              <Card key={template.name} className="border hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-primary/10 rounded-lg text-primary">
                      {template.icon}
                    </div>
                    <div>
                      <h4 className="font-medium">{template.name}</h4>
                      <p className="text-xs text-muted-foreground">{template.frequency}</p>
                    </div>
                  </div>
                  
                  <p className="text-sm text-muted-foreground mb-3">
                    {template.description}
                  </p>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      Est. {template.estimatedTime}
                    </span>
                    <Button size="sm">Generate</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Scheduled Reports */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Scheduled Reports</CardTitle>
              <CardDescription>
                Automatically generated reports
              </CardDescription>
            </div>
            <Button variant="outline">
              <Calendar className="h-4 w-4 mr-2" />
              Manage Schedule
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h4 className="font-medium">Weekly Cost Summary</h4>
                  <p className="text-sm text-muted-foreground">Every Monday at 9:00 AM</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="success">Active</Badge>
                <Button variant="outline" size="sm">Edit</Button>
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h4 className="font-medium">Monthly Executive Report</h4>
                  <p className="text-sm text-muted-foreground">1st of every month at 8:00 AM</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="success">Active</Badge>
                <Button variant="outline" size="sm">Edit</Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}